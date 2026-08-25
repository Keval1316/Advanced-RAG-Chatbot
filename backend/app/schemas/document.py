import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: uuid.UUID
    user_id: uuid.UUID
    knowledge_base_id: uuid.UUID
    filename: str
    page_number: int
    chunk_index: int
    text: str


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int = 0
    knowledge_base_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    message: str
    chunk_count: int
