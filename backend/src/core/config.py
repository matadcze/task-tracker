from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Default name used by health endpoint; tests expect this value
    app_name: str = "Project Name API"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str

    redis_url: str = "redis://localhost:6379/0"

    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    reminder_check_interval_minutes: int = 10

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    rate_limit_per_minute: int = 100

    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    upload_dir: Path = Path("./data/uploads")
    max_upload_size_mb: int = 10
    data_dir: Path = Path("./data")

    def model_post_init(self, __context):
        if not self.celery_broker_url:
            object.__setattr__(self, "celery_broker_url", self.redis_url)
        if not self.celery_result_backend:
            object.__setattr__(self, "celery_result_backend", self.redis_url)

        for directory in [self.data_dir, self.upload_dir]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
