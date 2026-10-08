import redis
from fastapi import HTTPException, Request, status

from app.core.config import settings


redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def _check_rate_limit(
    key: str,
    limit: int,
) -> None:
    """Check and enforce a single Redis-backed fixed-window limit."""

    request_count = redis_client.incr(key)

    if request_count == 1:
        redis_client.expire(
            key,
            settings.rate_limit_window_seconds,
        )

    if request_count > limit:
        ttl = redis_client.ttl(key)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "Retry-After": str(max(ttl, 0)),
            },
        )


def enforce_rate_limit(
    request: Request,
    scope: str,
    *,
    user_id: int | None = None,
    ip_limit: int | None = None,
    user_limit: int | None = None,
) -> None:
    """Enforce IP-based and optional user-based rate limits."""

    client_ip = request.client.host if request.client else "unknown"

    effective_ip_limit = (
        ip_limit
        if ip_limit is not None
        else settings.rate_limit_requests
    )

    ip_key = (
        f"rate_limit:{scope}:ip:"
        f"{client_ip}"
    )

    try:
        _check_rate_limit(
            key=ip_key,
            limit=effective_ip_limit,
        )

        if user_id is not None:
            effective_user_limit = (
                user_limit
                if user_limit is not None
                else settings.url_create_user_rate_limit_requests
            )

            user_key = (
                f"rate_limit:{scope}:user:"
                f"{user_id}"
            )

            _check_rate_limit(
                key=user_key,
                limit=effective_user_limit,
            )

    except HTTPException:
        raise
    except redis.RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service is unavailable.",
        ) from exc
