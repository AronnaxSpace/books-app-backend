import uuid

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.oidc import end_session_url, oauth
from app.auth.schemas import CurrentUser
from app.auth.sessions import create_session, destroy_session, load_session
from app.config import Settings
from app.database import get_db
from app.models import User

settings = Settings()

router = APIRouter(prefix="/auth", tags=["auth"], redirect_slashes=False)


@router.get("/login")
async def login(request: Request):
    return await oauth.aronnax.authorize_redirect(request, settings.oidc_redirect_uri)


@router.get("/callback")
async def callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.aronnax.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(status_code=400, detail=f"OAuth error: {exc.error}")

    claims = token.get("userinfo")
    if not claims:
        raise HTTPException(status_code=400, detail="ID token missing userinfo claims")

    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=400, detail="ID token missing 'sub' claim")
    email = claims.get("email") or ""
    nickname = email or sub

    stmt = (
        pg_insert(User)
        .values(sso_subject=sub, email=email, nickname=nickname)
        .on_conflict_do_update(
            index_elements=[User.sso_subject],
            set_={
                "email": email,
                "nickname": nickname,
                "updated_at": text("now()"),
            },
        )
        .returning(User)
    )
    result = await db.execute(stmt)
    user = result.scalar_one()
    await db.commit()

    session = await create_session(db, user, token)
    request.session.clear()
    request.session["sid"] = str(session.id)

    return RedirectResponse(url=settings.frontend_url, status_code=302)


@router.get("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    sid_raw = request.session.get("sid")
    id_token_hint: str | None = None
    if sid_raw:
        try:
            sid = uuid.UUID(sid_raw)
        except (TypeError, ValueError):
            sid = None
        if sid is not None:
            session = await load_session(db, sid)
            if session is not None:
                id_token_hint = session.id_token
                await destroy_session(db, sid)

    request.session.clear()
    url = await end_session_url(id_token_hint, settings.frontend_url)
    return RedirectResponse(url=url, status_code=302)


@router.get("/me", response_model=CurrentUser)
async def me(user: User = Depends(get_current_user)):
    return user
