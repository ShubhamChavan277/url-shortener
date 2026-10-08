from datetime import datetime, timedelta, timezone

import redis

from app.models.url import URL
from app.services import url_cache


def test_active_short_url_redirects_and_records_click(
    authenticated_client,
    client,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/target"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://example.com/target"

    analytics_response = authenticated_client.get(
        f"/api/v1/urls/{short_code}/stats",
    )

    assert analytics_response.status_code == 200
    assert analytics_response.json() == {
        "short_code": short_code,
        "click_count": 1,
    }


def test_nonexistent_short_url_returns_404(
    client,
):
    response = client.get(
        "/doesnotexist",
        follow_redirects=False,
    )

    assert response.status_code == 404


def test_expired_short_url_returns_410_and_does_not_record_click(
    authenticated_client,
    client,
    db,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/expired"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    url = (
        db.query(URL)
        .filter(URL.short_code == short_code)
        .first()
    )

    assert url is not None

    url.expires_at = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    db.commit()

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 410

    analytics_response = authenticated_client.get(
        f"/api/v1/urls/{short_code}/stats",
    )

    assert analytics_response.status_code == 200
    assert analytics_response.json() == {
        "short_code": short_code,
        "click_count": 0,
    }


def test_cache_miss_populates_redis(
    authenticated_client,
    client,
    url_cache_redis,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/cache-miss"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    assert url_cache_redis.get(
        f"url_cache:{short_code}"
    ) is None

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307

    cached_value = url_cache_redis.get(
        f"url_cache:{short_code}"
    )

    assert cached_value is not None


def test_cache_hit_avoids_database_lookup(
    authenticated_client,
    client,
    monkeypatch,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/cache-hit"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    first_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert first_response.status_code == 307

    def fail_database_lookup(*args, **kwargs):
        raise AssertionError(
            "Database lookup should not occur on cache HIT."
        )

    monkeypatch.setattr(
        "app.api.redirect.get_url_by_short_code",
        fail_database_lookup,
    )

    second_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert second_response.status_code == 307
    assert second_response.headers["location"] == (
        "https://example.com/cache-hit"
    )


def test_redis_cache_failure_falls_back_to_database(
    authenticated_client,
    client,
    monkeypatch,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/cache-fallback"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    class FailingRedis:
        def get(self, key):
            raise redis.RedisError("Redis unavailable")

        def set(self, *args, **kwargs):
            raise redis.RedisError("Redis unavailable")

    monkeypatch.setattr(
        url_cache,
        "redis_client",
        FailingRedis(),
    )

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == (
        "https://example.com/cache-fallback"
    )


def test_deleted_url_invalidates_cache(
    authenticated_client,
    client,
    url_cache_redis,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/cache-delete"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307

    assert url_cache_redis.get(
        f"url_cache:{short_code}"
    ) is not None

    delete_response = authenticated_client.delete(
        f"/api/v1/urls/{short_code}",
    )

    assert delete_response.status_code == 204

    assert url_cache_redis.get(
        f"url_cache:{short_code}"
    ) is None

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 404


def test_expiring_url_is_not_cached_and_returns_410_after_expiration(
    authenticated_client,
    client,
    db,
    url_cache_redis,
):
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    ).isoformat()

    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={
            "original_url": "https://example.com/cache-expiring",
            "expires_at": expires_at,
        },
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    active_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert active_response.status_code == 307

    assert url_cache_redis.get(
        f"url_cache:{short_code}"
    ) is None

    url = (
        db.query(URL)
        .filter(URL.short_code == short_code)
        .first()
    )

    assert url is not None

    url.expires_at = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    )
    db.commit()

    expired_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert expired_response.status_code == 410


def test_redirect_rate_limit(
    authenticated_client,
    client,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/rate-limit"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    for _ in range(60):
        response = client.get(
            f"/{short_code}",
            follow_redirects=False,
        )

        assert response.status_code == 307

    limited_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert limited_response.status_code == 429
    assert "Retry-After" in limited_response.headers
