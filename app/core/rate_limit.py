import redis
from fastapi import HTTPException, Request, status

from app.core.config import settings


redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def enforce_rate_limit(
    request: Request,
    scope: str,
) -> None:
    """Enforce a Redis-backed fixed-window rate limit."""

    client_ip = request.client.host if request.client else "unknown"
    key = (
        f"rate_limit:{scope}:"
        f"{client_ip}"
    )

    try:
        request_count = redis_client.incr(key)

        if request_count == 1:
            redis_client.expire(
                key,
                settings.rate_limit_window_seconds,
            )

        if request_count > settings.rate_limit_requests:
            ttl = redis_client.ttl(key)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": str(max(ttl, 0)),
                },
            )

    except HTTPException:
        raise
    except redis.RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service is unavailable.",
        ) from exc
