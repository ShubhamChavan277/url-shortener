def test_create_url_rejects_invalid_url(
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "not-a-valid-url"},
    )

    assert response.status_code == 422


def test_create_url_rejects_expiration_in_the_past(
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/v1/urls",
        json={
            "original_url": "https://example.com",
            "expires_at": "2020-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 400


def test_create_url_accepts_valid_url(
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/path"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["original_url"] == "https://example.com/path"
    assert len(data["short_code"]) == 8
    assert data["user_id"] is not None

def test_create_url_retries_after_short_code_collision(
    authenticated_client,
    monkeypatch,
):
    generated_codes = iter(
        [
            "collision",
            "unique123",
        ]
    )

    monkeypatch.setattr(
        "app.services.url_service.generate_short_code",
        lambda: next(generated_codes),
    )

    first_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/first"},
    )

    assert first_response.status_code == 201
    assert first_response.json()["short_code"] == "collision"

    second_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/second"},
    )

    assert second_response.status_code == 201
    assert second_response.json()["short_code"] == "unique123"


def test_create_url_fails_after_maximum_collision_attempts(
    authenticated_client,
    monkeypatch,
):
    existing_code = "collision"

    monkeypatch.setattr(
        "app.services.url_service.generate_short_code",
        lambda: existing_code,
    )

    first_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/first"},
    )

    assert first_response.status_code == 201
    assert first_response.json()["short_code"] == existing_code

    second_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/second"},
    )

    assert second_response.status_code == 500
    assert second_response.json()["detail"] == "Unable to create short URL."
