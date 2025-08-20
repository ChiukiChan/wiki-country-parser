from datetime import UTC, datetime

import aiosqlite
from loguru import logger

from .settings import settings


def get_now_ts() -> int:
    return int(datetime.now(UTC).timestamp())


async def open_db():
    logger.info("Opening SQLite DB at {} with timeout={}", settings.DB_PATH, settings.DB_TIMEOUT)
    conn = await aiosqlite.connect(settings.DB_PATH, timeout=settings.DB_TIMEOUT)
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute(
        """
      CREATE TABLE IF NOT EXISTS capitals_cache(
        country TEXT NOT NULL,
        capital TEXT NOT NULL,
        description TEXT,
        updated_at INTEGER NOT NULL,
        PRIMARY KEY(country)
      )
    """
    )
    await conn.commit()
    logger.info("SQLite DB ready")
    return conn


async def get_cached(conn: aiosqlite.Connection, country: str, capital: str) -> str | None:
    async with conn.execute(
        "SELECT description, updated_at FROM capitals_cache WHERE country=? AND capital=?",
        (country, capital),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        logger.debug("Cache miss: {}/{}", country, capital)
        return None
    else:
        logger.debug("Cache hit: {}/{}", country, capital)
    desc, ts = row
    return desc if get_now_ts() - int(ts) < settings.CACHE_TTL_SECONDS else None


async def upsert(conn: aiosqlite.Connection, country: str, capital: str, description: str | None) -> None:
    ts = get_now_ts()
    await conn.execute(
        """
        INSERT INTO capitals_cache(country, capital, description, updated_at)
        VALUES(?,?,?,?)
        ON CONFLICT(country) DO UPDATE SET
          description=excluded.description,
          updated_at=excluded.updated_at
        """,
        (country, capital, description, ts),
    )
    await conn.commit()
    logger.debug("Cache upserted: {}/{} (len={}, ts={})", country, capital, len(description), ts)
