from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CRM AI Analytics"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = Field(
        default="postgresql+asyncpg://crm:crm@localhost:5432/crm_analytics",
        validation_alias="DATABASE_URL",
    )
    enable_openai_insights: bool = Field(default=False, validation_alias="ENABLE_OPENAI_INSIGHTS")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    cache_ttl_seconds: int = Field(default=300, validation_alias="CACHE_TTL_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

