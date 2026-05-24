from urllib.parse import urlencode

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth

from app.config import Settings

settings = Settings()

oauth = OAuth()
oauth.register(
    name="aronnax",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=settings.oidc_discovery_url,
    client_kwargs={
        "scope": settings.oidc_scopes,
        "code_challenge_method": "S256",
        "token_endpoint_auth_method": "client_secret_basic",
    },
)


async def end_session_url(
    id_token_hint: str | None,
    post_logout_redirect_uri: str,
) -> str:
    metadata = await oauth.aronnax.load_server_metadata()
    base = metadata.get("end_session_endpoint")
    if not base:
        return post_logout_redirect_uri
    params: dict[str, str] = {"post_logout_redirect_uri": post_logout_redirect_uri}
    if id_token_hint:
        params["id_token_hint"] = id_token_hint
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}{urlencode(params)}"


async def refresh_access_token(refresh_token: str) -> dict:
    metadata = await oauth.aronnax.load_server_metadata()
    token_endpoint = metadata["token_endpoint"]
    async with AsyncOAuth2Client(
        client_id=settings.oidc_client_id,
        client_secret=settings.oidc_client_secret,
        token_endpoint_auth_method="client_secret_basic",
    ) as client:
        return await client.refresh_token(
            token_endpoint,
            refresh_token=refresh_token,
        )
