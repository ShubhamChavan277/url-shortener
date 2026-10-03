def test_analytics_counts_multiple_clicks(
    authenticated_client,
    client,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/analytics"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    first_redirect = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )
    second_redirect = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )
    third_redirect = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert first_redirect.status_code == 307
    assert second_redirect.status_code == 307
    assert third_redirect.status_code == 307

    analytics_response = authenticated_client.get(
        f"/api/v1/urls/{short_code}/stats",
    )

    assert analytics_response.status_code == 200
    assert analytics_response.json() == {
        "short_code": short_code,
        "click_count": 3,
    }


def test_user_cannot_view_another_users_analytics(
    authenticated_client,
    second_authenticated_client,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/private"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    analytics_response = second_authenticated_client.get(
        f"/api/v1/urls/{short_code}/stats",
    )

    assert analytics_response.status_code == 404


def test_analytics_for_nonexistent_short_code_returns_404(
    authenticated_client,
):
    response = authenticated_client.get(
        "/api/v1/urls/doesnotexist/stats",
    )

    assert response.status_code == 404
