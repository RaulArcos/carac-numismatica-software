from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    default_baud_rate: int = Field(default=115200)
    default_timeout: float = Field(default=5.0)
    max_retries: int = Field(default=3)

    heartbeat_interval_ms: int = Field(default=5000)
    heartbeat_timeout_ms: int = Field(default=10000)
    firmware_version: str = Field(default="1.0.0")

    lighting_channels: list[str] = Field(default=["ring1", "ring2", "ring3", "ring4"])
    max_lighting_intensity: int = Field(default=255)

    window_width: int = Field(default=800)
    window_height: int = Field(default=600)
    theme: str = Field(default="light")

    log_level: str = Field(default="DEBUG")
    log_to_file: bool = Field(default=True)
    log_retention_days: int = Field(default=30)

    photo_sequence_delay: float = Field(default=1.0)
    photo_sequence_count: int = Field(default=5)

    @property
    def log_directory(self) -> Path:
        return self._get_user_directory("logs")

    @property
    def config_directory(self) -> Path:
        return self._get_user_directory("config")

    def _get_user_directory(self, subdirectory: str) -> Path:
        return Path.home() / ".carac" / subdirectory


settings = Settings()