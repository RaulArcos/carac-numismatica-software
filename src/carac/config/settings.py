from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    default_baud_rate: int = Field(default=9600, description="Default baud rate for serial communication")
    default_timeout: float = Field(default=1.0, description="Default timeout for serial operations")
    max_retries: int = Field(default=3, description="Maximum number of retries for serial operations")
    
    lighting_channels: List[str] = Field(
        default=["axial", "ring", "backlight"],
        description="Available lighting channels"
    )
    max_lighting_intensity: int = Field(default=255, description="Maximum lighting intensity value")
    
    window_width: int = Field(default=800, description="Default window width")
    window_height: int = Field(default=600, description="Default window height")
    theme: str = Field(default="light", description="UI theme (light/dark)")
    
    log_level: str = Field(default="INFO", description="Logging level")
    log_to_file: bool = Field(default=True, description="Enable file logging")
    log_retention_days: int = Field(default=30, description="Log file retention in days")
    
    photo_sequence_delay: float = Field(default=1.0, description="Delay between photos in sequence")
    photo_sequence_count: int = Field(default=5, description="Number of photos in sequence")
    
    @property
    def log_directory(self) -> Path:
        return Path.home() / ".carac" / "logs"
    
    @property
    def config_directory(self) -> Path:
        return Path.home() / ".carac" / "config"


settings = Settings()
