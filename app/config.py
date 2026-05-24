from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str

    # OIDC client
    oidc_issuer: str
    oidc_discovery_url: str
    oidc_client_id: str
    oidc_client_secret: str
    oidc_redirect_uri: str
    oidc_scopes: str = "openid email"

    # BFF session cookie
    session_secret_key: str
    session_cookie_name: str = "bff_session"
    session_max_age_seconds: int = 60 * 60 * 8
    session_secure: bool = True

    frontend_url: str

    # JWT validation knobs
    jwt_leeway_seconds: int = 60
    jwks_cache_ttl_seconds: int = 60 * 60
