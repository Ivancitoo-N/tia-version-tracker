"""Configuration management for TIA Version Tracker.

Uses pydantic-settings for type-safe configuration loading.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    project_name: str = "TIA Version Tracker"
    version: str = "0.1.0"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"

    # Server
    host: str = "0.0.0.0"
    port: int = 5000

    # Database
    database_path: str = "database/tia_tracker.db"

    # Upload
    upload_folder: str = "uploads"
    max_upload_size: int = 52428800  # 50MB
    allowed_extensions: set[str] = {"zap15", "zap20"}

    # Reports
    report_folder: str = "reports"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# Global settings instance
settings = Settings()
