from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project: str = "巨龙出击"
    name: str = "dragon-strike-gold-mt4"
    version: str = "0.1.0"
    stage: str = "development_skeleton"
    env: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_prefix="APP_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
