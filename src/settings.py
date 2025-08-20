from pathlib import Path
from typing import Final

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_PATH: Path = Path("./capitals_cache.sqlite3")
    DB_TIMEOUT: float = 30
    CACHE_TTL_SECONDS: int = 3 * 24 * 60 * 60

    REQUEST_USER_AGENT: str = "Mozilla/5.0"
    REQUEST_TIMEOUT_SECONDS: int = 120

    MAX_CONCURRENT_REQUESTS: int = 8

    model_config = SettingsConfigDict(
        env_file=".env",
    )


settings: Final[Settings] = Settings()
