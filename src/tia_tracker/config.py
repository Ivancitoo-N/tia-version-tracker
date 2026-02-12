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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Convert relative paths to absolute paths based on project root
        import os
        from pathlib import Path
        
        # Assume config.py is in src/tia_tracker/
        # Project root is 2 levels up: src/tia_tracker/../../
        project_root = Path(__file__).parent.parent.parent.resolve()
        
        # Helper to make path absolute if not already
        def make_absolute(path_str):
            p = Path(path_str)
            if not p.is_absolute():
                return str(project_root / p)
            return path_str

        self.database_path = make_absolute(self.database_path)
        self.upload_folder = make_absolute(self.upload_folder)
        self.report_folder = make_absolute(self.report_folder)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# Global settings instance
settings = Settings()
