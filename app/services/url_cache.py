import json
import logging
from datetime import datetime

import redis

from app.core.config import settings


logger = logging.getLogger(__name__)


redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


CACHE_KEY_PREFIX = "url_cache:"


def _cache_key(short_code: str) -> str:
    return f"{CACHE_KEY_PREFIX}{short_code}"


def get_cached_url(short_code: str) -> dict | None:
    """Return cached URL data, or None when not cached."""

    try:
        cached_value = redis_client.get(_cache_key(short_code))

        if cached_value is None:
            logger.debug("URL cache MISS for %s", short_code)
            return None

        logger.debug("URL cache HIT for %s", short_code)
        return json.loads(cached_value)

    except (redis.RedisError, json.JSONDecodeError) as exc:
        logger.warning(
            "URL cache read failed for %s; falling back to database: %s",
            short_code,
            exc,
        )
        return None


def set_cached_url(
    short_code: str,
    url_id: int,
    original_url: str,
    expires_at: datetime | None,
) -> None:
    """Store non-expiring URL redirect data in Redis."""

    if expires_at is not None:
        return

    cache_data = {
        "id": url_id,
        "original_url": original_url,
        "expires_at": None,
    }

    try:
        redis_client.set(
            _cache_key(short_code),
            json.dumps(cache_data),
            ex=settings.url_cache_ttl_seconds,
        )
    except redis.RedisError as exc:
        logger.warning(
            "URL cache write failed for %s: %s",
            short_code,
            exc,
        )


def delete_cached_url(short_code: str) -> None:
    """Remove a URL from the Redis cache."""

    try:
        redis_client.delete(_cache_key(short_code))
    except redis.RedisError as exc:
        logger.warning(
            "URL cache deletion failed for %s: %s",
            short_code,
            exc,
        )
