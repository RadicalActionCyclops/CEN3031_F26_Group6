from functools import lru_cache
from typing import Literal
from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SwampSpace API"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./swampspace.db"
    secret_key: SecretStr | None = None

    local_auth_enabled: bool = True
    cors_origins: list[str] = ["http://localhost:5173"]

    session_cookie_name: str = "swampspace_session"
    csrf_cookie_name: str = "swampspace_csrf"
    session_lifetime_minutes: int = 60 * 24 * 7
    verification_token_lifetime_minutes: int = 30
    cookie_samesite: Literal["lax", "strict"] = "lax"

    email_delivery: Literal["console", "file"] = "console"
    email_outbox_path: str = "./development-email-outbox.jsonl"

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        secret_value = (
            self.secret_key.get_secret_value() if self.secret_key is not None else ""
        )
        if not secret_value:
            self.secret_key = None
        if self.environment == "production" and len(secret_value) < 32:
            raise ValueError(
                "SECRET_KEY must contain at least 32 characters in production"
            )
        return self

    @property
    def secure_cookies(self) -> bool:
        return self.environment == "production"

    @property
    def development_auth_available(self) -> bool:
        return self.environment != "production" and self.local_auth_enabled

@lru_cache
def get_settings() -> Settings:
    return Settings()
