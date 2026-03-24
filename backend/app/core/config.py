from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Trendly AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    frontend_url: str = Field(default="http://127.0.0.1:3000", alias="FRONTEND_URL")
    secret_key: str = Field(default="change-me-secret-key", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60 * 24 * 7, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    sqlite_path: str = Field(default="./trendly_ai.db", alias="SQLITE_PATH")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
