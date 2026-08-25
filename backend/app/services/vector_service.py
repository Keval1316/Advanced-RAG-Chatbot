import uuid
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import VectorStoreException
from backend.app.rag.embeddings import embedding_service
from backend.app.schemas.document import ChunkMetadata
from backend.app.schemas.rag import ScoredChunk


class VectorService:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorService, cls).__new__(cls)
        return cls._instance

    def get_client(self) -> QdrantClient:
        if self._client is None:
            try:
                # Attempt remote connection if not explicit memory mode
                if settings.QDRANT_HOST and settings.QDRANT_HOST.lower() not in ["memory", "none"]:
                    if settings.QDRANT_HOST.startswith("http://") or settings.QDRANT_HOST.startswith("https://"):
                        client = QdrantClient(
                            url=settings.QDRANT_HOST,
                            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                            timeout=10.0,
                            check_compatibility=False
                        )
                    else:
                        client = QdrantClient(
                            host=settings.QDRANT_HOST,
                            port=settings.QDRANT_PORT,
                            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                            timeout=10.0,
                            check_compatibility=False
                        )
                    # Verify connectivity
                    client.get_collections()
                    self._client = client
                    logger.info(f"Connected to remote Qdrant at {settings.QDRANT_HOST}")
                else:
                    self._client = QdrantClient(location=":memory:")
                    logger.info("Using in-memory Qdrant instance.")
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant at {settings.QDRANT_HOST}: {str(e)}. Using in-memory Qdrant storage.")
                self._client = QdrantClient(location=":memory:")

            self.ensure_collection_exists()

        return self._client

    def ensure_collection_exists(self, collection_name: Optional[str] = None) -> None:
        col_name = collection_name or settings.QDRANT_COLLECTION_NAME
        client = self._client if self._client else self.get_client()
        try:
            collections = [c.name for c in client.get_collections().collections]
            if col_name not in collections:
                logger.info(f"Creating Qdrant collection '{col_name}' with {settings.EMBEDDING_DIMENSION} dimensions...")
                client.create_collection(
                    collection_name=col_name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{col_name}' created successfully.")

            # Ensure payload field indexes exist for multi-tenant payload filtering
            try:
                client.create_payload_index(
                    collection_name=col_name,
                    field_name="user_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                client.create_payload_index(
                    collection_name=col_name,
                    field_name="knowledge_base_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                client.create_payload_index(
                    collection_name=col_name,
                    field_name="document_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
            except Exception:
                pass  # Indexes may already exist

        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection '{col_name}' exists: {str(e)}")
            raise VectorStoreException(message=f"Vector collection initialization failed: {str(e)}")

    def upsert_chunks(
        self,
        chunks: List[ChunkMetadata],
        collection_name: Optional[str] = None
    ) -> int:
        if not chunks:
            return 0

        client = self.get_client()
        col_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.ensure_collection_exists(col_name)
        texts = [c.text for c in chunks]

        try:
            vectors = embedding_service.embed_documents(texts)
            points = []

            for chunk, vector in zip(chunks, vectors):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "document_id": str(chunk.document_id),
                    "user_id": str(chunk.user_id),
                    "knowledge_base_id": str(chunk.knowledge_base_id),
                    "filename": chunk.filename,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text
                }
                points.append(PointStruct(id=point_id, vector=vector, payload=payload))

            client.upsert(
                collection_name=col_name,
                points=points,
                wait=True
            )
            logger.info(f"Successfully upserted {len(points)} chunk vectors into Qdrant collection '{col_name}'.")
            return len(points)

        except Exception as e:
            logger.error(f"Error upserting vectors into Qdrant: {str(e)}")
            raise VectorStoreException(message=f"Failed to index document chunks: {str(e)}")

    def dense_search(
        self,
        query: str,
        user_id: uuid.UUID,
        kb_id: uuid.UUID,
        top_k: int = 20,
        collection_name: Optional[str] = None
    ) -> List[ScoredChunk]:
        client = self.get_client()
        col_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.ensure_collection_exists(col_name)

        try:
            query_vector = embedding_service.embed_query(query)

            # Enforce strict multi-tenant isolation
            tenant_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=str(user_id))
                    ),
                    FieldCondition(
                        key="knowledge_base_id",
                        match=MatchValue(value=str(kb_id))
                    )
                ]
            )

            # Query Qdrant with query_points
            query_response = client.query_points(
                collection_name=col_name,
                query=query_vector,
                query_filter=tenant_filter,
                limit=top_k,
                with_payload=True
            )

            scored_chunks = []
            for hit in query_response.points:
                payload = hit.payload or {}
                scored_chunks.append(
                    ScoredChunk(
                        chunk_id=payload.get("chunk_id", ""),
                        document_id=uuid.UUID(payload.get("document_id")),
                        user_id=uuid.UUID(payload.get("user_id")),
                        knowledge_base_id=uuid.UUID(payload.get("knowledge_base_id")),
                        filename=payload.get("filename", "unknown"),
                        page_number=payload.get("page_number", 1),
                        chunk_index=payload.get("chunk_index", 0),
                        text=payload.get("text", ""),
                        score=float(hit.score),
                        retrieval_type="dense"
                    )
                )

            logger.info(f"Dense search retrieved {len(scored_chunks)} candidate chunks for query '{query[:40]}...'.")
            return scored_chunks

        except Exception as e:
            logger.error(f"Error executing dense search in Qdrant: {str(e)}")
            raise VectorStoreException(message=f"Dense vector retrieval failed: {str(e)}")

    def delete_by_document(
        self,
        doc_id: uuid.UUID,
        user_id: uuid.UUID,
        collection_name: Optional[str] = None
    ) -> bool:
        client = self.get_client()
        col_name = collection_name or settings.QDRANT_COLLECTION_NAME

        try:
            client.delete(
                collection_name=col_name,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(key="document_id", match=MatchValue(value=str(doc_id))),
                            FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))
                        ]
                    )
                ),
                wait=True
            )
            logger.info(f"Deleted vectors for document {doc_id} from Qdrant.")
            return True
        except Exception as e:
            logger.error(f"Error deleting document vectors from Qdrant: {str(e)}")
            return False

    def delete_by_knowledge_base(
        self,
        kb_id: uuid.UUID,
        user_id: uuid.UUID,
        collection_name: Optional[str] = None
    ) -> bool:
        client = self.get_client()
        col_name = collection_name or settings.QDRANT_COLLECTION_NAME

        try:
            client.delete(
                collection_name=col_name,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(key="knowledge_base_id", match=MatchValue(value=str(kb_id))),
                            FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))
                        ]
                    )
                ),
                wait=True
            )
            logger.info(f"Deleted vectors for knowledge base {kb_id} from Qdrant.")
            return True
        except Exception as e:
            logger.error(f"Error deleting KB vectors from Qdrant: {str(e)}")
            return False


vector_service = VectorService()
