from typing import List
from fastembed import TextEmbedding
from backend.app.core.config import settings
from backend.app.core.logging import logger


class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def _get_model(self) -> TextEmbedding:
        if self._model is None:
            logger.info(f"Loading dense embedding model: {settings.EMBEDDING_MODEL}")
            self._model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        embeddings_gen = model.embed(texts, batch_size=64)
        return [[float(x) for x in vector] for vector in embeddings_gen]

    def embed_query(self, query: str) -> List[float]:
        model = self._get_model()
        query_text = f"Represent this sentence for searching relevant passages: {query}" if "bge" in settings.EMBEDDING_MODEL else query
        embeddings_gen = model.embed([query_text], batch_size=1)
        vector = next(embeddings_gen)
        return [float(x) for x in vector]

    def warmup(self) -> None:
        try:
            self.embed_query("warmup")
            logger.info("Dense embedding model warmed up successfully.")
        except Exception as e:
            logger.warning(f"Embedding warmup warning: {str(e)}")


embedding_service = EmbeddingService()
