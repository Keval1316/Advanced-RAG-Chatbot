import uuid
import pytest
from backend.app.rag.embeddings import embedding_service
from backend.app.services.vector_service import vector_service
from backend.app.schemas.document import ChunkMetadata


def test_embedding_generation():
    text = "FastAPI and Groq make high performance AI systems."
    embedding = embedding_service.embed_query(text)
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)

    batch = embedding_service.embed_documents([
        "Document 1 text about PostgreSQL.",
        "Document 2 text about Qdrant vector database."
    ])
    assert len(batch) == 2
    assert len(batch[0]) == 384
    assert len(batch[1]) == 384


def test_vector_upsert_and_dense_search():
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    chunks = [
        ChunkMetadata(
            chunk_id=f"{doc_id}_p1_c0",
            document_id=doc_id,
            user_id=user_id,
            knowledge_base_id=kb_id,
            filename="auth_system.txt",
            page_number=1,
            chunk_index=0,
            text="Authentication uses JSON Web Tokens (JWT) with HS256 algorithm and bcrypt password hashing."
        ),
        ChunkMetadata(
            chunk_id=f"{doc_id}_p1_c1",
            document_id=doc_id,
            user_id=user_id,
            knowledge_base_id=kb_id,
            filename="auth_system.txt",
            page_number=1,
            chunk_index=1,
            text="Access tokens expire after 24 hours (1440 minutes) by default."
        ),
        ChunkMetadata(
            chunk_id=f"{doc_id}_p1_c2",
            document_id=doc_id,
            user_id=user_id,
            knowledge_base_id=kb_id,
            filename="auth_system.txt",
            page_number=1,
            chunk_index=2,
            text="PostgreSQL 16 is used as the relational database to store user and knowledge base metadata."
        )
    ]

    # 1. Upsert chunks
    upserted = vector_service.upsert_chunks(chunks)
    assert upserted == 3

    # 2. Search for token expiration
    results = vector_service.dense_search(
        query="How long do tokens last before expiring?",
        user_id=user_id,
        kb_id=kb_id,
        top_k=2
    )
    assert len(results) > 0
    assert "24 hours" in results[0].text
    assert results[0].filename == "auth_system.txt"
    assert results[0].retrieval_type == "dense"


def test_vector_store_multi_tenant_isolation():
    user1_id = uuid.uuid4()
    kb1_id = uuid.uuid4()
    doc1_id = uuid.uuid4()

    user2_id = uuid.uuid4()
    kb2_id = uuid.uuid4()

    chunk_user1 = [
        ChunkMetadata(
            chunk_id=f"{doc1_id}_p1_c0",
            document_id=doc1_id,
            user_id=user1_id,
            knowledge_base_id=kb1_id,
            filename="top_secret.txt",
            page_number=1,
            chunk_index=0,
            text="The project code name is Project Nebula and launch date is October 2026."
        )
    ]
    vector_service.upsert_chunks(chunk_user1)

    # User 1 searches -> Found
    user1_results = vector_service.dense_search(
        query="What is the launch date of Project Nebula?",
        user_id=user1_id,
        kb_id=kb1_id,
        top_k=5
    )
    assert len(user1_results) == 1
    assert "Project Nebula" in user1_results[0].text

    # User 2 searches with identical query in their KB -> Must return 0 results
    user2_results = vector_service.dense_search(
        query="What is the launch date of Project Nebula?",
        user_id=user2_id,
        kb_id=kb2_id,
        top_k=5
    )
    assert len(user2_results) == 0


def test_vector_deletion():
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    chunks = [
        ChunkMetadata(
            chunk_id=f"{doc_id}_p1_c0",
            document_id=doc_id,
            user_id=user_id,
            knowledge_base_id=kb_id,
            filename="deleteme.txt",
            page_number=1,
            chunk_index=0,
            text="This document will be deleted from Qdrant vector database."
        )
    ]
    vector_service.upsert_chunks(chunks)

    # Verify searchable before delete
    res_before = vector_service.dense_search("deleted from Qdrant", user_id=user_id, kb_id=kb_id)
    assert len(res_before) == 1

    # Delete by document
    vector_service.delete_by_document(doc_id=doc_id, user_id=user_id)

    # Verify not searchable after delete
    res_after = vector_service.dense_search("deleted from Qdrant", user_id=user_id, kb_id=kb_id)
    assert len(res_after) == 0
