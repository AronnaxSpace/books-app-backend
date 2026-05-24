import uuid

from authlib.integrations.base_client.errors import OAuthError
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import destroy_session, ensure_fresh_access_token, load_session
from app.database import get_db
from app.models import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    sid_raw = request.session.get("sid")
    if not sid_raw:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        sid = uuid.UUID(sid_raw)
    except (TypeError, ValueError):
        request.session.clear()
        raise HTTPException(status_code=401, detail="Invalid session")

    session = await load_session(db, sid)
    if session is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session expired")

    try:
        session = await ensure_fresh_access_token(db, session)
    except OAuthError:
        await destroy_session(db, sid)
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session refresh failed")

    user = await db.get(User, session.user_id)
    if user is None:
        await destroy_session(db, sid)
        request.session.clear()
        raise HTTPException(status_code=401, detail="User not found")

    return user
