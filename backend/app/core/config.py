from functools import lru_cache

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Proxy Gateway API"
    app_env: str = "development"
    api_v1_prefix: str = "/api"
    database_url: str = Field(
        default="postgresql+psycopg2://proxy_user:proxy_password@postgres:5432/proxy_gateway"
    )
    test_database_url: str = Field(
        default="postgresql+psycopg2://proxy_user:proxy_password@localhost:5432/proxy_gateway_test"
    )
    redis_url: str = Field(default="redis://redis:6379/0")
    secret_key: str = Field(default="change-me")
    access_token_expire_minutes: int = 60 * 24
    activation_key_length: int = 32
    activation_key_ttl_hours: int = 24
    smtp_host: str | None = None
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_sender: EmailStr = "noreply@example.com"
    use_console_email: bool = True
    ws_heartbeat_seconds: int = 10
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
