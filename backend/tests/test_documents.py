import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.rag.chunker import RecursiveChunker
from backend.app.rag.parser import PageContent
import uuid

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


def test_recursive_chunker():
    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
    pages = [
        PageContent(
            page_number=1,
            text="First sentence of section one. Second sentence explaining the architecture. Third sentence detailing components."
        ),
        PageContent(
            page_number=2,
            text="Page two covers security guidelines and database tenant isolation policies."
        )
    ]
    chunks = chunker.chunk_pages(
        pages=pages,
        document_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        knowledge_base_id=uuid.uuid4(),
        filename="test_doc.txt"
    )

    assert len(chunks) >= 2
    for c in chunks:
        assert c.chunk_id is not None
        assert len(c.text) <= 120
        assert c.page_number in [1, 2]


def test_upload_and_manage_text_document():
    token = get_auth_token("doc_tester@example.com", "doctester")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create KB
    kb_res = client.post("/api/v1/knowledge-bases/", json={
        "name": "Architecture KB",
        "description": "System architecture files"
    }, headers=headers)
    kb_id = kb_res.json()["data"]["id"]

    # 2. Upload text document
    sample_text = (
        "Enterprise AI Knowledge Assistant Architecture.\n\n"
        "The system uses FastAPI for REST API routing and Groq for fast LLM inference.\n"
        "Qdrant vector database stores dense and sparse embeddings for hybrid retrieval.\n"
        "A cross-encoder reranks retrieved candidate chunks before generation."
    )
    file_bytes = io.BytesIO(sample_text.encode("utf-8"))
    upload_res = client.post(
        "/api/v1/documents/upload",
        data={"knowledge_base_id": kb_id},
        files={"file": ("architecture_overview.txt", file_bytes, "text/plain")},
        headers=headers
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()["data"]
    assert upload_data["status"] == "ready"
    assert upload_data["chunk_count"] > 0
    doc_id = upload_data["id"]

    # 3. List documents in KB
    list_res = client.get(f"/api/v1/documents/kb/{kb_id}", headers=headers)
    assert list_res.status_code == 200
    docs = list_res.json()["data"]
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id
    assert docs[0]["chunk_count"] == upload_data["chunk_count"]

    # 4. Get single document
    get_res = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["status"] == "ready"

    # 5. Delete document
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 200

    # 6. Verify deleted
    get_after_del = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_after_del.status_code == 404


def test_upload_invalid_file_format():
    token = get_auth_token("invalid_fmt@example.com", "invalidfmt")
    headers = {"Authorization": f"Bearer {token}"}

    kb_res = client.post("/api/v1/knowledge-bases/", json={
        "name": "Testing KB"
    }, headers=headers)
    kb_id = kb_res.json()["data"]["id"]

    fake_binary = io.BytesIO(b"MZ\x90\x00executable content")
    upload_res = client.post(
        "/api/v1/documents/upload",
        data={"knowledge_base_id": kb_id},
        files={"file": ("malicious.exe", fake_binary, "application/octet-stream")},
        headers=headers
    )
    assert upload_res.status_code == 500 or upload_res.status_code == 400
    assert upload_res.json()["success"] is False


def test_cross_tenant_document_protection():
    token_owner = get_auth_token("doc_owner@example.com", "docowner")
    token_stranger = get_auth_token("doc_stranger@example.com", "docstranger")

    headers_owner = {"Authorization": f"Bearer {token_owner}"}
    headers_stranger = {"Authorization": f"Bearer {token_stranger}"}

    # Owner creates KB and uploads doc
    kb_res = client.post("/api/v1/knowledge-bases/", json={"name": "Owner KB"}, headers=headers_owner)
    kb_id = kb_res.json()["data"]["id"]

    file_bytes = io.BytesIO(b"Private confidential roadmap text.")
    upload_res = client.post(
        "/api/v1/documents/upload",
        data={"knowledge_base_id": kb_id},
        files={"file": ("roadmap.txt", file_bytes, "text/plain")},
        headers=headers_owner
    )
    doc_id = upload_res.json()["data"]["id"]

    # Stranger tries to upload to Owner's KB -> 403
    stranger_file = io.BytesIO(b"Malicious file content")
    stranger_upload = client.post(
        "/api/v1/documents/upload",
        data={"knowledge_base_id": kb_id},
        files={"file": ("injected.txt", stranger_file, "text/plain")},
        headers=headers_stranger
    )
    assert stranger_upload.status_code == 403

    # Stranger tries to list Owner's docs -> 403
    stranger_list = client.get(f"/api/v1/documents/kb/{kb_id}", headers=headers_stranger)
    assert stranger_list.status_code == 403

    # Stranger tries to get Owner's doc -> 403
    stranger_get = client.get(f"/api/v1/documents/{doc_id}", headers=headers_stranger)
    assert stranger_get.status_code == 403

    # Stranger tries to delete Owner's doc -> 403
    stranger_del = client.delete(f"/api/v1/documents/{doc_id}", headers=headers_stranger)
    assert stranger_del.status_code == 403
