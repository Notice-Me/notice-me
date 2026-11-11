from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOTICE_", env_file=".env", extra="ignore")

    db_path: Path = Path("data/notice_me.db")
    data_mode: Literal["mock", "live", "mixed"] = "mock"
    http_timeout_seconds: float = Field(default=10, gt=0, le=60)
    news_read_timeout_seconds: float = Field(default=20, gt=0, le=60)
    news_max_retries: int = Field(default=1, ge=0, le=1)
    news_request_budget: int = Field(default=20, ge=1, le=100)
    freenews_api_key: SecretStr = SecretStr("")
    thenewsapi_token: SecretStr = SecretStr("")
    gnews_api_key: SecretStr = SecretStr("")
    seoul_api_key: SecretStr = SecretStr("sample")
    tour_api_key: SecretStr = SecretStr("")
    its_api_key: SecretStr = SecretStr("")
    manual_events_path: Path | None = None

    @field_validator("manual_events_path", mode="before")
    @classmethod
    def empty_path_is_disabled(cls, value):
        return None if value == "" else value

    def provider_status(self) -> dict[str, bool | str]:
        return {
            "freenews": bool(self.freenews_api_key.get_secret_value()),
            "thenewsapi": bool(self.thenewsapi_token.get_secret_value()),
            "gnews": bool(self.gnews_api_key.get_secret_value()),
            "seoul": "sample"
            if self.seoul_api_key.get_secret_value() == "sample"
            else bool(self.seoul_api_key.get_secret_value()),
            "tourapi": bool(self.tour_api_key.get_secret_value()),
            "its": bool(self.its_api_key.get_secret_value()),
            "llm": "DETERMINISTIC_MOCK",
            "routing": "UNVERIFIED",
        }
