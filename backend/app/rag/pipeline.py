import uuid
import time
from typing import List, Dict, Optional, Any
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.guardrails import guardrails
from backend.app.schemas.rag import ScoredChunk, Citation, ChatResponse
from backend.app.rag.router import query_router, QueryRoute
from backend.app.rag.rewriter import query_rewriter
from backend.app.rag.hyde import hyde_generator
from backend.app.rag.hybrid_search import hybrid_search_service
from backend.app.rag.reranker import reranker
from backend.app.rag.corrective import corrective_rag
from backend.app.rag.generator import answer_generator


class AdvancedRAGPipeline:
    def execute(
        self,
        query: str,
        user_id: uuid.UUID,
        kb_id: uuid.UUID,
        conversation_id: uuid.UUID,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ChatResponse:
        start_time = time.time()
        history = conversation_history or []
        attempt = 1
        transformed_query = query.strip()

        # Step 0: Input Guardrails & Safety Filter
        is_safe, safety_response = guardrails.evaluate(query)
        if not is_safe:
            return ChatResponse(
                conversation_id=conversation_id,
                answer=safety_response,
                citations=[],
                metadata={
                    "guardrail_status": "BLOCKED",
                    "latency_seconds": round(time.time() - start_time, 4)
                }
            )

        # Step 1: Query Routing
        route = query_router.route(query=query, conversation_history=history)

        # Step 2: Query Transformation
        if route == QueryRoute.REWRITE:
            transformed_query = query_rewriter.rewrite(query=query, conversation_history=history)
            search_query = transformed_query
        elif route == QueryRoute.HYDE:
            # Generate hypothetical passage strictly for vector search
            hyde_passage = hyde_generator.generate_hypothetical_document(query=query)
            search_query = hyde_passage
        else:
            search_query = query

        # Step 3: Hybrid Search (Dense + Sparse with RRF)
        retrieval_result = hybrid_search_service.search(
            query=search_query,
            user_id=user_id,
            kb_id=kb_id,
            dense_top_k=settings.DENSE_TOP_K,
            sparse_top_k=settings.SPARSE_TOP_K,
            fused_top_k=settings.FUSED_TOP_K
        )
        candidate_chunks = retrieval_result.chunks

        # Step 4: Cross-Encoder Reranking
        top_chunks = reranker.rerank(
            query=query,
            chunks=candidate_chunks,
            top_k=settings.RERANK_TOP_K
        )

        # Step 5: Corrective RAG (CRAG) Evaluation
        crag_status, should_retry = corrective_rag.evaluate_context(
            query=query,
            chunks=top_chunks,
            attempt=attempt
        )

        # Handle CRAG Retry if context was poor
        if should_retry:
            attempt += 1
            logger.info(f"CRAG triggered retrieval retry #{attempt} with broadened query terms.")
            retry_query = f"{query} {transformed_query}"
            retry_retrieval = hybrid_search_service.search(
                query=retry_query,
                user_id=user_id,
                kb_id=kb_id,
                dense_top_k=settings.DENSE_TOP_K,
                sparse_top_k=settings.SPARSE_TOP_K,
                fused_top_k=settings.FUSED_TOP_K
            )
            top_chunks = reranker.rerank(
                query=query,
                chunks=retry_retrieval.chunks,
                top_k=settings.RERANK_TOP_K
            )
            crag_status, _ = corrective_rag.evaluate_context(
                query=query,
                chunks=top_chunks,
                attempt=attempt
            )

        insufficient_context = (crag_status == "INSUFFICIENT" and not top_chunks)

        # Step 6: Grounded Answer & Citations Generation
        answer, citations = answer_generator.generate_answer(
            query=query,
            chunks=top_chunks,
            conversation_history=history,
            insufficient_context=insufficient_context
        )

        elapsed = time.time() - start_time
        metadata = {
            "route": route.value,
            "transformed_query": transformed_query if route != QueryRoute.DIRECT_QA else None,
            "retrieval_attempts": attempt,
            "candidates_retrieved": len(candidate_chunks),
            "top_chunks_used": len(top_chunks),
            "crag_status": crag_status,
            "latency_seconds": round(elapsed, 4)
        }

        return ChatResponse(
            conversation_id=conversation_id,
            answer=answer,
            citations=citations,
            metadata=metadata
        )


rag_pipeline = AdvancedRAGPipeline()
