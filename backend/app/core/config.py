from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application Settings
    APP_NAME: str = "Enterprise AI Knowledge Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "enterprise-super-secret-key-change-in-production-min-32-chars"
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:8501", "http://localhost:3000", "http://127.0.0.1:8501"]

    # Server Settings
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    API_BASE_URL: str = "http://localhost:8000/api/v1"

    # PostgreSQL Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "rag_knowledge_db"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/rag_knowledge_db"

    # JWT Authentication
    JWT_SECRET_KEY: str = "enterprise-super-secret-jwt-key-min-32-characters"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Groq LLM API (Multi-Key Pool)
    GROQ_API_KEY: str = ""
    GROQ_API_KEYS: Union[str, List[str]] = []
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"
    GROQ_THINK_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_ROUTER_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TEMPERATURE: float = 0.1
    GROQ_MAX_TOKENS: int = 2048

    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_COLLECTION_NAME: str = "enterprise_knowledge_base"
    QDRANT_API_KEY: str = ""

    # Document Ingestion & Chunking
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 25
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Retrieval & Hybrid Search
    DENSE_TOP_K: int = 20
    SPARSE_TOP_K: int = 20
    FUSED_TOP_K: int = 20
    RERANK_TOP_K: int = 8

    # Reranker Model
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Corrective RAG
    MAX_RETRIEVAL_ATTEMPTS: int = 2
    RELEVANCE_THRESHOLD: float = 0.6

    # Conversation Memory
    MAX_HISTORY_MESSAGES: int = 10

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        elif isinstance(v, list):
            return v
        return ["*"]


settings = Settings()
