def test_authenticated_client_can_access_protected_endpoint(
    authenticated_client,
):
    response = authenticated_client.get("/api/v1/urls")

    assert response.status_code == 200
    assert response.json() == []

def test_second_authenticated_client_can_access_protected_endpoint(
    second_authenticated_client,
):
    response = second_authenticated_client.get("/api/v1/urls")

    assert response.status_code == 200
    assert response.json() == []

def test_register_user_returns_public_user_data(
    client,
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email_returns_conflict(
    client,
):
    payload = {
        "email": "duplicate@example.com",
        "password": "TestPassword123!",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_register_invalid_email_returns_validation_error(
    client,
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 422


def test_register_short_password_returns_validation_error(
    client,
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpassword@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_login_invalid_password_returns_unauthorized(
    client,
    registered_user,
    user_payload,
):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user_payload["email"],
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_login_unknown_user_returns_unauthorized(
    client,
):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401


def test_protected_endpoint_without_token_returns_unauthorized(
    client,
):
    response = client.get("/api/v1/urls")

    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token_returns_unauthorized(
    client,
):
    client.headers.update(
        {"Authorization": "Bearer invalid-token"}
    )

    response = client.get("/api/v1/urls")

    assert response.status_code == 401
