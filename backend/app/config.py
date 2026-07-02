from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project: str = "巨龙出击"
    name: str = "dragon-strike-gold-mt4"
    version: str = "0.1.0"
    stage: str = "development_skeleton"
    env: str = "development"
    log_level: str = "INFO"
    default_symbol: str = Field(
        default="XAUUSD",
        validation_alias=AliasChoices("DEFAULT_SYMBOL", "APP_DEFAULT_SYMBOL"),
    )
    data_source: str = Field(
        default="mock",
        validation_alias=AliasChoices("DATA_SOURCE", "APP_DATA_SOURCE"),
    )
    mock_initial_price: float = Field(
        default=2030.00,
        validation_alias=AliasChoices("MOCK_INITIAL_PRICE", "APP_MOCK_INITIAL_PRICE"),
    )
    mock_spread: float = Field(
        default=0.30,
        validation_alias=AliasChoices("MOCK_SPREAD", "APP_MOCK_SPREAD"),
    )
    mock_digits: int = Field(
        default=2,
        validation_alias=AliasChoices("MOCK_DIGITS", "APP_MOCK_DIGITS"),
    )
    signal_log_dir: str = Field(
        default="data/signals",
        validation_alias=AliasChoices("SIGNAL_LOG_DIR", "APP_SIGNAL_LOG_DIR"),
    )
    placeholder_signal_log_file: str = Field(
        default="placeholder_signals.jsonl",
        validation_alias=AliasChoices(
            "PLACEHOLDER_SIGNAL_LOG_FILE",
            "APP_PLACEHOLDER_SIGNAL_LOG_FILE",
        ),
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_prefix="APP_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
