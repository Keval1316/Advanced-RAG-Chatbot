import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ScoredChunk(BaseModel):
    chunk_id: str
    document_id: uuid.UUID
    user_id: uuid.UUID
    knowledge_base_id: uuid.UUID
    filename: str
    page_number: int
    chunk_index: int
    text: str
    score: float
    retrieval_type: str = "dense"  # "dense", "sparse", "hybrid", "reranked"


class Citation(BaseModel):
    document_id: uuid.UUID
    document_name: str
    page_number: int
    chunk_id: str
    snippet: Optional[str] = None


class RetrievalResult(BaseModel):
    query: str
    chunks: List[ScoredChunk]
    total_found: int
    retrieval_type: str


class ChatRequest(BaseModel):
    knowledge_base_id: uuid.UUID
    message: str = Field(..., min_length=1)
    conversation_id: Optional[uuid.UUID] = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    answer: str
    citations: List[Citation]
    metadata: Dict[str, Any] = Field(default_factory=dict)
