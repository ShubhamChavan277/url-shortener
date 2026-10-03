import redis


def test_rate_limit_allows_requests_within_limit(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.core.config.settings.rate_limit_requests",
        2,
    )

    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "limit1@example.com",
            "password": "TestPassword123!",
        },
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "limit2@example.com",
            "password": "TestPassword123!",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201


def test_rate_limit_returns_429_after_limit_is_exceeded(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.core.config.settings.rate_limit_requests",
        2,
    )

    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "limit1@example.com",
            "password": "TestPassword123!",
        },
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "limit2@example.com",
            "password": "TestPassword123!",
        },
    )

    third_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "limit3@example.com",
            "password": "TestPassword123!",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert third_response.status_code == 429
    assert "Retry-After" in third_response.headers
    assert third_response.json()["detail"] == (
        "Rate limit exceeded. Please try again later."
    )


def test_rate_limit_returns_503_when_redis_is_unavailable(
    client,
    monkeypatch,
):
    class FailingRedisClient:
        def incr(self, key):
            raise redis.RedisError("Redis unavailable")

    monkeypatch.setattr(
        "app.core.rate_limit.redis_client",
        FailingRedisClient(),
    )

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "redisfailure@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Rate limiting service is unavailable."
    )
