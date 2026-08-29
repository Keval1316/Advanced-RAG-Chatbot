from typing import List, Tuple
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

    def _get_model(self):
        if self._model is None:
            try:
                from fastembed.rerank.cross_encoder import TextCrossEncoder
                logger.info("Loading lightweight ONNX Cross-Encoder reranker...")
                self._model = TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
            except Exception as e:
                logger.warning(f"Could not load FastEmbed CrossEncoder ({str(e)}), trying sentence-transformers fallback...")
                try:
                    from sentence_transformers import CrossEncoder
                    self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                except Exception as ex:
                    logger.error(f"All cross-encoder models failed to load: {str(ex)}")
                    self._model = None
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
            if model is None:
                return chunks[:top_k]

            candidate_pool = chunks[:8]
            texts = [chunk.text for chunk in candidate_pool]

            # FastEmbed TextCrossEncoder path
            if hasattr(model, "rerank"):
                scores = list(model.rerank(query, texts))
            else:
                # sentence-transformers predict path
                pairs = [[query, text] for text in texts]
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
        pass


reranker = CrossEncoderReranker()

