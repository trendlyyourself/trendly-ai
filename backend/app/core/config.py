from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Trendly AI", alias="APP_NAME")
    # Fail closed: deployments must explicitly opt into development mode.
    app_env: str = Field(default="production", alias="APP_ENV")
    frontend_url: str = Field(default="http://127.0.0.1:5173", alias="FRONTEND_URL")
    secret_key: str = Field(default="change-me-secret-key", alias="SECRET_KEY")
    encryption_key: str | None = Field(default=None, alias="ENCRYPTION_KEY")
    access_token_expire_minutes: int = Field(default=60 * 24 * 7, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    sqlite_path: str = Field(default="./trendly_ai.db", alias="SQLITE_PATH")

    @model_validator(mode="after")
    def validate_production_secret(self):
        if self.app_env.strip().lower() in {"production", "prod"}:
            secret = self.secret_key or ""
            if len(secret.encode("utf-8")) < 32 or secret.startswith("replace-with") or secret.startswith("change-me"):
                raise ValueError("SECRET_KEY must be a unique, non-placeholder value of at least 32 bytes in production")
            raise ValueError("This build uses SQLite only; production requires a managed database adapter and verified migration")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
