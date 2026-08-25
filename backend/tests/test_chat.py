import io
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


def test_chat_flow_end_to_end():
    token = get_auth_token("chat_tester@example.com", "chattester")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create KB
    kb_res = client.post("/api/v1/knowledge-bases/", json={
        "name": "DevOps Guide",
        "description": "DevOps runbooks and architecture"
    }, headers=headers)
    kb_id = kb_res.json()["data"]["id"]

    # 2. Upload document
    doc_content = (
        "DevOps Runbook: Continuous Deployment Pipeline.\n\n"
        "Deployment to staging triggers automatically upon merging to the main branch.\n"
        "Production deployments require dual administrator approvals in the dashboard.\n"
        "Rollbacks can be initiated by executing 'helm rollback release-prod 0'."
    )
    upload_res = client.post(
        "/api/v1/documents/upload",
        data={"knowledge_base_id": kb_id},
        files={"file": ("devops_runbook.txt", io.BytesIO(doc_content.encode("utf-8")), "text/plain")},
        headers=headers
    )
    assert upload_res.status_code == 201

    # 3. Send chat message
    chat_payload = {
        "knowledge_base_id": kb_id,
        "message": "What is required for production deployments?"
    }
    msg_res = client.post("/api/v1/chat/message", json=chat_payload, headers=headers)
    assert msg_res.status_code == 200
    msg_data = msg_res.json()["data"]

    assert msg_data["conversation_id"] is not None
    assert msg_data["answer"] is not None
    assert len(msg_data["citations"]) > 0
    assert msg_data["citations"][0]["document_name"] == "devops_runbook.txt"
    assert "metadata" in msg_data
    conv_id = msg_data["conversation_id"]

    # 4. Fetch conversation messages
    history_res = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=headers)
    assert history_res.status_code == 200
    messages = history_res.json()["data"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    # 5. List conversations
    conv_list_res = client.get(f"/api/v1/chat/conversations?kb_id={kb_id}", headers=headers)
    assert conv_list_res.status_code == 200
    assert len(conv_list_res.json()["data"]) == 1

    # 6. Delete conversation
    del_res = client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 200


def test_cross_tenant_chat_protection():
    token1 = get_auth_token("user1_chat@example.com", "user1chat")
    token2 = get_auth_token("user2_chat@example.com", "user2chat")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates KB and conversation
    kb_res = client.post("/api/v1/knowledge-bases/", json={"name": "Confidential KB"}, headers=headers1)
    kb_id = kb_res.json()["data"]["id"]

    conv_res = client.post("/api/v1/chat/conversations", json={
        "knowledge_base_id": kb_id,
        "title": "Confidential Discussion"
    }, headers=headers1)
    conv_id = conv_res.json()["data"]["id"]

    # User 2 tries to send message to User 1's KB -> 403
    send_res = client.post("/api/v1/chat/message", json={
        "knowledge_base_id": kb_id,
        "message": "Give me the secrets."
    }, headers=headers2)
    assert send_res.status_code == 403

    # User 2 tries to get User 1's conversation messages -> 403
    get_res = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=headers2)
    assert get_res.status_code == 403

    # User 2 tries to delete User 1's conversation -> 403
    del_res = client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers2)
    assert del_res.status_code == 403
