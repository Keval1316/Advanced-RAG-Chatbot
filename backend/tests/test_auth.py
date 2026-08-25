import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.db.session import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


client = TestClient(app)


def test_register_user_success():
    payload = {
        "email": "alice@example.com",
        "username": "alice",
        "password": "strongpassword123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "alice@example.com"
    assert data["data"]["username"] == "alice"
    assert "hashed_password" not in data["data"]


def test_register_user_duplicate_email():
    payload = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "password123"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "email": "duplicate@example.com",
        "username": "user2",
        "password": "password123"
    }
    res2 = client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 400
    data = res2.json()
    assert data["success"] is False
    assert "already exists" in data["error"]["message"]


def test_login_success_and_get_profile():
    # Register
    reg_payload = {
        "email": "bob@example.com",
        "username": "bob",
        "password": "securepassword123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login with username
    login_payload = {
        "username_or_email": "bob",
        "password": "securepassword123"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Access /api/v1/users/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["email"] == "bob@example.com"
    assert me_data["username"] == "bob"


def test_login_invalid_password():
    reg_payload = {
        "email": "charlie@example.com",
        "username": "charlie",
        "password": "correctpassword123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "username_or_email": "charlie@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_get_current_user_unauthorized():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

    invalid_token_headers = {"Authorization": "Bearer invalid.jwt.token"}
    response_invalid = client.get("/api/v1/users/me", headers=invalid_token_headers)
    assert response_invalid.status_code == 401
