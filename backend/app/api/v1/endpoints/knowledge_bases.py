import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.conversation import Conversation
from backend.app.schemas.common import APIResponse
from backend.app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse
)
from backend.app.services.kb_service import kb_service

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.post(
    "/",
    response_model=APIResponse[KnowledgeBaseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new isolated knowledge base"
)
def create_knowledge_base(
    kb_in: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[KnowledgeBaseResponse]:
    kb = kb_service.create(db, kb_in=kb_in, user_id=current_user.id)
    response_data = KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        user_id=kb.user_id,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
        document_count=0,
        conversation_count=0
    )
    return APIResponse(
        success=True,
        message="Knowledge base created successfully.",
        data=response_data
    )


@router.get(
    "/",
    response_model=APIResponse[List[KnowledgeBaseResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all knowledge bases owned by the authenticated user"
)
def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[List[KnowledgeBaseResponse]]:
    kbs = kb_service.list_by_user(db, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Knowledge bases retrieved successfully.",
        data=kbs
    )


@router.get(
    "/{kb_id}",
    response_model=APIResponse[KnowledgeBaseResponse],
    status_code=status.HTTP_200_OK,
    summary="Get details of a specific knowledge base"
)
def get_knowledge_base(
    kb_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[KnowledgeBaseResponse]:
    kb = kb_service.get_by_id(db, kb_id=kb_id, user_id=current_user.id)
    doc_count = db.query(Document).filter(Document.knowledge_base_id == kb.id).count()
    conv_count = db.query(Conversation).filter(Conversation.knowledge_base_id == kb.id).count()
    response_data = KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        user_id=kb.user_id,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
        document_count=doc_count,
        conversation_count=conv_count
    )
    return APIResponse(
        success=True,
        message="Knowledge base retrieved successfully.",
        data=response_data
    )


@router.put(
    "/{kb_id}",
    response_model=APIResponse[KnowledgeBaseResponse],
    status_code=status.HTTP_200_OK,
    summary="Update knowledge base metadata"
)
def update_knowledge_base(
    kb_id: uuid.UUID,
    kb_in: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[KnowledgeBaseResponse]:
    kb = kb_service.update(db, kb_id=kb_id, user_id=current_user.id, kb_in=kb_in)
    doc_count = db.query(Document).filter(Document.knowledge_base_id == kb.id).count()
    conv_count = db.query(Conversation).filter(Conversation.knowledge_base_id == kb.id).count()
    response_data = KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        user_id=kb.user_id,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
        document_count=doc_count,
        conversation_count=conv_count
    )
    return APIResponse(
        success=True,
        message="Knowledge base updated successfully.",
        data=response_data
    )


@router.delete(
    "/{kb_id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete knowledge base and all associated resources"
)
def delete_knowledge_base(
    kb_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[dict]:
    kb_service.delete(db, kb_id=kb_id, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Knowledge base deleted successfully.",
        data={"id": str(kb_id)}
    )
