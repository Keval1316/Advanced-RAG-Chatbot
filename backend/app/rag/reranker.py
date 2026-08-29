from typing import List, Tuple
from sentence_transformers import CrossEncoder
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.rag import ScoredChunk


class CrossEncoderReranker:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrossEncoderReranker, cls).__new__(cls)
        return cls._instance

    def _get_model(self) -> CrossEncoder:
        if self._model is None:
            logger.info(f"Loading Cross-Encoder model: {settings.RERANKER_MODEL}")
            self._model = CrossEncoder(settings.RERANKER_MODEL)
        return self._model

    def rerank(
        self,
        query: str,
        chunks: List[ScoredChunk],
        top_k: int = settings.RERANK_TOP_K
    ) -> List[ScoredChunk]:
        if not chunks:
            return []

        # Fast-path: If 1 or 0 chunks, no need to run cross-encoder inference
        if len(chunks) <= 1:
            return chunks[:top_k]

        try:
            model = self._get_model()
            # Only rerank top candidate pool (max 8) to keep CPU latency low (<150ms)
            candidate_pool = chunks[:8]
            pairs = [[query, chunk.text] for chunk in candidate_pool]
            scores = model.predict(pairs, batch_size=8, show_progress_bar=False)

            scored_chunks: List[Tuple[float, ScoredChunk]] = []
            for score, chunk in zip(scores, candidate_pool):
                reranked_chunk = ScoredChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    user_id=chunk.user_id,
                    knowledge_base_id=chunk.knowledge_base_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    score=float(score),
                    retrieval_type="reranked"
                )
                scored_chunks.append((float(score), reranked_chunk))

            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            top_results = [chunk for _, chunk in scored_chunks[:top_k]]

            logger.info(f"Reranked {len(candidate_pool)} candidates down to {len(top_results)} top passages.")
            return top_results

        except Exception as e:
            logger.error(f"Cross-Encoder reranking error: {str(e)}. Returning original candidates.")
            return chunks[:top_k]

    def warmup(self) -> None:
        try:
            model = self._get_model()
            model.predict([["warmup query", "warmup document text"]], show_progress_bar=False)
            logger.info("Cross-Encoder reranker warmed up successfully.")
        except Exception as e:
            logger.warning(f"Cross-Encoder warmup warning: {str(e)}")


reranker = CrossEncoderReranker()
