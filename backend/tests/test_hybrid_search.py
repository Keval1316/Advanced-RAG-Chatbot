import uuid
import pytest
from backend.app.rag.sparse import BM25Index, tokenize
from backend.app.rag.hybrid_search import ReciprocalRankFusion, hybrid_search_service
from backend.app.services.vector_service import vector_service
from backend.app.schemas.document import ChunkMetadata
from backend.app.schemas.rag import ScoredChunk


def test_bm25_tokenization_and_exact_match():
    chunks = [
        ChunkMetadata(
            chunk_id="c1",
            document_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            knowledge_base_id=uuid.uuid4(),
            filename="errors.txt",
            page_number=1,
            chunk_index=0,
            text="If you encounter ERR_AUTH_9901, refresh your session credentials immediately."
        ),
        ChunkMetadata(
            chunk_id="c2",
            document_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            knowledge_base_id=uuid.uuid4(),
            filename="general.txt",
            page_number=1,
            chunk_index=0,
            text="General information about user onboarding and password reset."
        )
    ]

    index = BM25Index()
    index.index(chunks)

    # Search for specific error code
    results = index.search("ERR_AUTH_9901", top_k=5)
    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert "ERR_AUTH_9901" in results[0].text
    assert results[0].retrieval_type == "sparse"


def test_reciprocal_rank_fusion():
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    dense_chunk_1 = ScoredChunk(
        chunk_id="chunk_A",
        document_id=doc_id,
        user_id=user_id,
        knowledge_base_id=kb_id,
        filename="doc.txt",
        page_number=1,
        chunk_index=0,
        text="Text A",
        score=0.95,
        retrieval_type="dense"
    )
    dense_chunk_2 = ScoredChunk(
        chunk_id="chunk_B",
        document_id=doc_id,
        user_id=user_id,
        knowledge_base_id=kb_id,
        filename="doc.txt",
        page_number=1,
        chunk_index=1,
        text="Text B",
        score=0.85,
        retrieval_type="dense"
    )

    sparse_chunk_1 = ScoredChunk(
        chunk_id="chunk_B",  # chunk_B appears first in sparse
        document_id=doc_id,
        user_id=user_id,
        knowledge_base_id=kb_id,
        filename="doc.txt",
        page_number=1,
        chunk_index=1,
        text="Text B",
        score=4.2,
        retrieval_type="sparse"
    )
    sparse_chunk_2 = ScoredChunk(
        chunk_id="chunk_C",
        document_id=doc_id,
        user_id=user_id,
        knowledge_base_id=kb_id,
        filename="doc.txt",
        page_number=1,
        chunk_index=2,
        text="Text C",
        score=2.1,
        retrieval_type="sparse"
    )

    # Fuse ranked lists
    fused = ReciprocalRankFusion.fuse(
        ranked_lists=[[dense_chunk_1, dense_chunk_2], [sparse_chunk_1, sparse_chunk_2]],
        k=60,
        top_k=3
    )

    assert len(fused) == 3
    # Chunk B appeared in both lists (rank 2 in dense, rank 1 in sparse) so should receive highest combined RRF score
    assert fused[0].chunk_id == "chunk_B"
    assert fused[0].retrieval_type == "hybrid"


def test_hybrid_search_end_to_end():
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    chunks = [
        ChunkMetadata(
            chunk_id=f"{doc_id}_p1_c0",
            document_id=doc_id,
            user_id=user_id,
            knowledge_base_id=kb_id,
            filename="hybrid_doc.txt",
            page_number=1,
            chunk_index=0,
            text="The cluster database uses PG_SHARD_ID_990 for distributed partition routing."
        ),
        ChunkMetadata(
            chunk_id=f"{doc_id}_p1_c1",
            document_id=doc_id,
            user_id=user_id,
            knowledge_base_id=kb_id,
            filename="hybrid_doc.txt",
            page_number=1,
            chunk_index=1,
            text="Instructions for resetting administrator authentication credentials."
        )
    ]

    vector_service.upsert_chunks(chunks)

    # Hybrid search for technical code
    result = hybrid_search_service.search(
        query="PG_SHARD_ID_990 partition routing",
        user_id=user_id,
        kb_id=kb_id,
        dense_top_k=5,
        sparse_top_k=5,
        fused_top_k=2
    )

    assert result.total_found > 0
    assert "PG_SHARD_ID_990" in result.chunks[0].text
    assert result.retrieval_type == "hybrid"
