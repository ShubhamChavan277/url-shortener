def test_user_can_create_and_list_own_url(
    authenticated_client,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com"},
    )

    assert create_response.status_code == 201

    list_response = authenticated_client.get("/api/v1/urls")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["short_code"] == create_response.json()["short_code"]


def test_user_cannot_delete_another_users_url(
    authenticated_client,
    second_authenticated_client,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    delete_response = second_authenticated_client.delete(
        f"/api/v1/urls/{short_code}",
    )

    assert delete_response.status_code == 404

    owner_list_response = authenticated_client.get("/api/v1/urls")

    assert owner_list_response.status_code == 200
    assert len(owner_list_response.json()) == 1


def test_user_can_delete_own_url(
    authenticated_client,
):
    create_response = authenticated_client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com"},
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    delete_response = authenticated_client.delete(
        f"/api/v1/urls/{short_code}",
    )

    assert delete_response.status_code == 204

    list_response = authenticated_client.get("/api/v1/urls")

    assert list_response.status_code == 200
    assert list_response.json() == []
