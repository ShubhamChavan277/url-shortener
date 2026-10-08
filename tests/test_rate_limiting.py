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


def test_authenticated_url_creation_enforces_user_limit(
    authenticated_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.core.config.settings.url_create_ip_rate_limit_requests",
        10,
    )
    monkeypatch.setattr(
        "app.core.config.settings.url_create_user_rate_limit_requests",
        2,
    )

    first_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/1"},
    )

    second_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/2"},
    )

    third_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/3"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert third_response.status_code == 429
    assert "Retry-After" in third_response.headers
    assert third_response.json()["detail"] == (
        "Rate limit exceeded. Please try again later."
    )


def test_authenticated_url_creation_user_limits_are_independent(
    authenticated_client,
    second_authenticated_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.core.config.settings.url_create_ip_rate_limit_requests",
        10,
    )
    monkeypatch.setattr(
        "app.core.config.settings.url_create_user_rate_limit_requests",
        2,
    )

    first_user_response_1 = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/user1-1"},
    )
    first_user_response_2 = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/user1-2"},
    )

    second_user_response_1 = second_authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/user2-1"},
    )
    second_user_response_2 = second_authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/user2-2"},
    )

    assert first_user_response_1.status_code == 201
    assert first_user_response_2.status_code == 201
    assert second_user_response_1.status_code == 201
    assert second_user_response_2.status_code == 201


def test_authenticated_url_creation_enforces_shared_ip_limit(
    authenticated_client,
    second_authenticated_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.core.config.settings.url_create_ip_rate_limit_requests",
        3,
    )
    monkeypatch.setattr(
        "app.core.config.settings.url_create_user_rate_limit_requests",
        10,
    )

    first_user_response_1 = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/ip-1"},
    )
    first_user_response_2 = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/ip-2"},
    )
    second_user_response_1 = second_authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/ip-3"},
    )
    second_user_response_2 = second_authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/ip-4"},
    )

    assert first_user_response_1.status_code == 201
    assert first_user_response_2.status_code == 201
    assert second_user_response_1.status_code == 201
    assert second_user_response_2.status_code == 429
