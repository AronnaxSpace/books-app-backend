import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.oidc import refresh_access_token
from app.config import Settings
from app.models import User, UserSession

settings = Settings()

REFRESH_LEEWAY_SECONDS = 30


async def create_session(
    db: AsyncSession,
    user: User,
    token: dict,
) -> UserSession:
    now = datetime.now(UTC)
    expires_in = token.get("expires_in")
    access_expires_at = (
        now + timedelta(seconds=int(expires_in)) if expires_in else None
    )
    session = UserSession(
        user_id=user.id,
        access_token=token.get("access_token"),
        refresh_token=token.get("refresh_token"),
        id_token=token.get("id_token"),
        access_token_expires_at=access_expires_at,
        expires_at=now + timedelta(seconds=settings.session_max_age_seconds),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def load_session(db: AsyncSession, sid: uuid.UUID) -> UserSession | None:
    now = datetime.now(UTC)
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == sid,
            UserSession.expires_at > now,
        )
    )
    return result.scalar_one_or_none()


async def destroy_session(db: AsyncSession, sid: uuid.UUID) -> None:
    await db.execute(delete(UserSession).where(UserSession.id == sid))
    await db.commit()


async def ensure_fresh_access_token(
    db: AsyncSession, session: UserSession
) -> UserSession:
    if session.access_token_expires_at is None or session.refresh_token is None:
        return session
    now = datetime.now(UTC)
    if session.access_token_expires_at - now > timedelta(seconds=REFRESH_LEEWAY_SECONDS):
        return session

    new_token = await refresh_access_token(session.refresh_token)
    expires_in = new_token.get("expires_in")
    session.access_token = new_token.get("access_token", session.access_token)
    session.refresh_token = new_token.get("refresh_token", session.refresh_token)
    if expires_in:
        session.access_token_expires_at = now + timedelta(seconds=int(expires_in))
    if new_token.get("id_token"):
        session.id_token = new_token["id_token"]
    session.last_seen_at = now
    await db.commit()
    await db.refresh(session)
    return session
