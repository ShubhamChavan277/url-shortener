from datetime import datetime, timedelta, timezone

from app.models.url import URL


def test_register_login_create_redirect_and_analytics_flow(
    client,
):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "integration@example.com",
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "integration@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    create_response = client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/integration"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    client.headers.pop("Authorization")

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == (
        "https://example.com/integration"
    )

    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    analytics_response = client.get(
        f"/api/v1/urls/{short_code}/stats",
    )

    assert analytics_response.status_code == 200
    assert analytics_response.json() == {
        "short_code": short_code,
        "click_count": 1,
    }


def test_expiration_flow_redirects_before_expiration_and_returns_410_after(
    authenticated_client,
    client,
    db,
):
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    ).isoformat()

    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={
            "original_url": "https://example.com/expiring",
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


def test_deleted_url_is_no_longer_redirectable(
    authenticated_client,
    client,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/delete"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    delete_response = authenticated_client.delete(
        f"/api/v1/urls/{short_code}",
    )

    assert delete_response.status_code == 204

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 404
