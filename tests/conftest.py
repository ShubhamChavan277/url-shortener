from collections.abc import Generator

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core import rate_limit
from app.db.session import get_db
from app.main import app
from app.models.url import URL
from app.models.url_click import URLClick
from app.models.user import User


TEST_DATABASE_URL = make_url(settings.database_url).set(
    database="url_shortener_test"
)

test_engine = create_engine(TEST_DATABASE_URL)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
def clean_test_database() -> Generator[None, None, None]:
    with TestSessionLocal() as db:
        db.execute(delete(URLClick))
        db.execute(delete(URL))
        db.execute(delete(User))
        db.commit()

    yield

    with TestSessionLocal() as db:
        db.execute(delete(URLClick))
        db.execute(delete(URL))
        db.execute(delete(User))
        db.commit()


@pytest.fixture(autouse=True)
def clean_test_redis(monkeypatch) -> Generator[None, None, None]:
    test_redis = redis.Redis.from_url(
        settings.redis_url,
        db=15,
        decode_responses=True,
    )

    test_redis.flushdb()
    monkeypatch.setattr(rate_limit, "redis_client", test_redis)

    yield

    test_redis.flushdb()
    test_redis.close()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _override_get_db() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user_payload() -> dict[str, str]:
    return {
        "email": "testuser@example.com",
        "password": "TestPassword123!",
    }


@pytest.fixture
def second_user_payload() -> dict[str, str]:
    return {
        "email": "seconduser@example.com",
        "password": "SecondPassword123!",
    }


@pytest.fixture
def registered_user(
    client: TestClient,
    user_payload: dict[str, str],
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json=user_payload,
    )

    assert response.status_code == 201
    return response.json()


@pytest.fixture
def authenticated_client(
    client: TestClient,
    user_payload: dict[str, str],
    registered_user: dict,
) -> TestClient:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user_payload["email"],
            "password": user_payload["password"],
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    return client


@pytest.fixture
def second_authenticated_client(
    second_user_payload: dict[str, str],
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/auth/register",
            json=second_user_payload,
        )

        assert response.status_code == 201

        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": second_user_payload["email"],
                "password": second_user_payload["password"],
            },
        )

        assert response.status_code == 200

        token = response.json()["access_token"]

        test_client.headers.update(
            {"Authorization": f"Bearer {token}"}
        )

        yield test_client

    app.dependency_overrides.clear()
