import uuid
from typing import List, Dict, Optional
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.vector_service import vector_service
from backend.app.rag.sparse import BM25Index
from backend.app.schemas.document import ChunkMetadata
from backend.app.schemas.rag import ScoredChunk, RetrievalResult


class ReciprocalRankFusion:
    @staticmethod
    def fuse(
        ranked_lists: List[List[ScoredChunk]],
        k: int = 60,
        top_k: int = 20
    ) -> List[ScoredChunk]:
        """Combines multiple ranked lists using Reciprocal Rank Fusion (RRF).
        RRF_Score(d) = SUM_{m in M} (1 / (k + rank_m(d)))
        """
        chunk_map: Dict[str, ScoredChunk] = {}
        rrf_scores: Dict[str, float] = {}

        for rank_list in ranked_lists:
            for rank, chunk in enumerate(rank_list, start=1):
                chunk_id = chunk.chunk_id
                chunk_map[chunk_id] = chunk
                score_increment = 1.0 / (k + rank)
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score_increment

        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        fused_results: List[ScoredChunk] = []
        for cid in sorted_chunk_ids[:top_k]:
            original = chunk_map[cid]
            fused_results.append(
                ScoredChunk(
                    chunk_id=original.chunk_id,
                    document_id=original.document_id,
                    user_id=original.user_id,
                    knowledge_base_id=original.knowledge_base_id,
                    filename=original.filename,
                    page_number=original.page_number,
                    chunk_index=original.chunk_index,
                    text=original.text,
                    score=float(rrf_scores[cid]),
                    retrieval_type="hybrid"
                )
            )

        return fused_results


class HybridSearchService:
    def __init__(self):
        self.rrf = ReciprocalRankFusion()

    def _get_kb_chunks(self, user_id: uuid.UUID, kb_id: uuid.UUID) -> List[ChunkMetadata]:
        """Scrolls/fetches all chunks for a specific knowledge base to populate BM25 sparse index."""
        client = vector_service.get_client()
        col_name = settings.QDRANT_COLLECTION_NAME
        vector_service.ensure_collection_exists(col_name)

        tenant_filter = Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=str(user_id))),
                FieldCondition(key="knowledge_base_id", match=MatchValue(value=str(kb_id)))
            ]
        )

        chunks: List[ChunkMetadata] = []
        offset = None

        while True:
            scroll_result = client.scroll(
                collection_name=col_name,
                scroll_filter=tenant_filter,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            points, next_offset = scroll_result
            for p in points:
                payload = p.payload or {}
                chunks.append(
                    ChunkMetadata(
                        chunk_id=payload.get("chunk_id", ""),
                        document_id=uuid.UUID(payload.get("document_id")),
                        user_id=uuid.UUID(payload.get("user_id")),
                        knowledge_base_id=uuid.UUID(payload.get("knowledge_base_id")),
                        filename=payload.get("filename", ""),
                        page_number=payload.get("page_number", 1),
                        chunk_index=payload.get("chunk_index", 0),
                        text=payload.get("text", "")
                    )
                )

            if next_offset is None or len(points) == 0:
                break
            offset = next_offset

        return chunks

    def search(
        self,
        query: str,
        user_id: uuid.UUID,
        kb_id: uuid.UUID,
        dense_top_k: int = settings.DENSE_TOP_K,
        sparse_top_k: int = settings.SPARSE_TOP_K,
        fused_top_k: int = settings.FUSED_TOP_K
    ) -> RetrievalResult:
        # 1. Execute Dense Retrieval
        dense_results = vector_service.dense_search(
            query=query,
            user_id=user_id,
            kb_id=kb_id,
            top_k=dense_top_k
        )

        # 2. Execute Sparse Lexical Retrieval
        kb_chunks = self._get_kb_chunks(user_id=user_id, kb_id=kb_id)
        sparse_index = BM25Index()
        sparse_index.index(kb_chunks)
        sparse_results = sparse_index.search(query=query, top_k=sparse_top_k)

        # 3. Reciprocal Rank Fusion
        fused_chunks = self.rrf.fuse(
            ranked_lists=[dense_results, sparse_results],
            k=60,
            top_k=fused_top_k
        )

        logger.info(
            f"Hybrid search: {len(dense_results)} dense + {len(sparse_results)} sparse "
            f"fused into {len(fused_chunks)} candidates for query '{query[:35]}...'"
        )

        return RetrievalResult(
            query=query,
            chunks=fused_chunks,
            total_found=len(fused_chunks),
            retrieval_type="hybrid"
        )


hybrid_search_service = HybridSearchService()
