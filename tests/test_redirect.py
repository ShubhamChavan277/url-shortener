from datetime import datetime, timedelta, timezone

from app.models.url import URL


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
