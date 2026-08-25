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


def get_auth_token(email: str, username: str) -> str:
    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "password": "Password123!"
    })
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": email,
        "password": "Password123!"
    })
    return res.json()["data"]["access_token"]


def test_create_and_list_knowledge_bases():
    token = get_auth_token("user1@example.com", "user1")
    headers = {"Authorization": f"Bearer {token}"}

    # Create KB
    kb_payload = {
        "name": "Finance Documents",
        "description": "All financial quarterly reports"
    }
    create_res = client.post("/api/v1/knowledge-bases/", json=kb_payload, headers=headers)
    assert create_res.status_code == 201
    created_data = create_res.json()["data"]
    assert created_data["name"] == "Finance Documents"
    assert created_data["document_count"] == 0
    kb_id = created_data["id"]

    # List KBs
    list_res = client.get("/api/v1/knowledge-bases/", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert len(list_data) == 1
    assert list_data[0]["id"] == kb_id


def test_update_and_delete_knowledge_base():
    token = get_auth_token("user2@example.com", "user2")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post("/api/v1/knowledge-bases/", json={
        "name": "Old Name",
        "description": "Old Desc"
    }, headers=headers)
    kb_id = create_res.json()["data"]["id"]

    # Update
    update_res = client.put(f"/api/v1/knowledge-bases/{kb_id}", json={
        "name": "New Name",
        "description": "Updated Description"
    }, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["data"]["name"] == "New Name"

    # Delete
    delete_res = client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
    assert delete_res.status_code == 200

    # Verify deleted
    get_res = client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
    assert get_res.status_code == 404


def test_multi_tenant_isolation():
    token1 = get_auth_token("owner@example.com", "owner")
    token2 = get_auth_token("intruder@example.com", "intruder")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates KB
    create_res = client.post("/api/v1/knowledge-bases/", json={
        "name": "Secret Project X",
        "description": "Top secret information"
    }, headers=headers1)
    kb_id = create_res.json()["data"]["id"]

    # User 2 lists KBs -> Should be empty
    list_res = client.get("/api/v1/knowledge-bases/", headers=headers2)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 0

    # User 2 tries to read User 1's KB -> 403 Forbidden
    get_res = client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers2)
    assert get_res.status_code == 403

    # User 2 tries to update User 1's KB -> 403 Forbidden
    put_res = client.put(f"/api/v1/knowledge-bases/{kb_id}", json={"name": "Hacked"}, headers=headers2)
    assert put_res.status_code == 403

    # User 2 tries to delete User 1's KB -> 403 Forbidden
    del_res = client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=headers2)
    assert del_res.status_code == 403
