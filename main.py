from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.auth.router import router as auth_router
from app.config import Settings
from app.routers import authors, books

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    from app.database import engine

    await engine.dispose()


app = FastAPI(title="Books API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie=settings.session_cookie_name,
    https_only=settings.session_secure,
    same_site="lax",
    max_age=settings.session_max_age_seconds,
)

app.include_router(auth_router)
app.include_router(authors.router)
app.include_router(books.router)
