import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.models.document import Document
from backend.app.models.conversation import Conversation
from backend.app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from backend.app.core.exceptions import NotFoundException, ForbiddenException
from backend.app.core.logging import logger
from backend.app.services.vector_service import vector_service


class KnowledgeBaseService:
    @staticmethod
    def create(db: Session, kb_in: KnowledgeBaseCreate, user_id: uuid.UUID) -> KnowledgeBase:
        kb = KnowledgeBase(
            name=kb_in.name.strip(),
            description=kb_in.description.strip() if kb_in.description else None,
            user_id=user_id
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        logger.info(f"Created KnowledgeBase '{kb.name}' ({kb.id}) for user {user_id}")
        return kb

    @staticmethod
    def get_by_id(db: Session, kb_id: uuid.UUID, user_id: uuid.UUID) -> KnowledgeBase:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise NotFoundException(message=f"Knowledge base {kb_id} not found.")
        if kb.user_id != user_id:
            raise ForbiddenException(message="You do not have permission to access this knowledge base.")
        return kb

    @staticmethod
    def list_by_user(db: Session, user_id: uuid.UUID) -> List[KnowledgeBaseResponse]:
        kbs = db.query(KnowledgeBase).filter(KnowledgeBase.user_id == user_id).all()
        results = []
        for kb in kbs:
            doc_count = db.query(Document).filter(Document.knowledge_base_id == kb.id).count()
            conv_count = db.query(Conversation).filter(Conversation.knowledge_base_id == kb.id).count()
            res = KnowledgeBaseResponse(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                user_id=kb.user_id,
                created_at=kb.created_at,
                updated_at=kb.updated_at,
                document_count=doc_count,
                conversation_count=conv_count
            )
            results.append(res)
        return results

    @staticmethod
    def update(
        db: Session,
        kb_id: uuid.UUID,
        user_id: uuid.UUID,
        kb_in: KnowledgeBaseUpdate
    ) -> KnowledgeBase:
        kb = KnowledgeBaseService.get_by_id(db, kb_id=kb_id, user_id=user_id)
        if kb_in.name is not None:
            kb.name = kb_in.name.strip()
        if kb_in.description is not None:
            kb.description = kb_in.description.strip() if kb_in.description else None

        db.commit()
        db.refresh(kb)
        logger.info(f"Updated KnowledgeBase '{kb.name}' ({kb.id}) for user {user_id}")
        return kb

    @staticmethod
    def delete(db: Session, kb_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        kb = KnowledgeBaseService.get_by_id(db, kb_id=kb_id, user_id=user_id)
        
        # Delete all vectors in Qdrant associated with this KB
        vector_service.delete_by_knowledge_base(kb_id=kb.id, user_id=user_id)

        db.delete(kb)
        db.commit()
        logger.info(f"Deleted KnowledgeBase ({kb_id}) and cleaned up vector index for user {user_id}")
        return True


kb_service = KnowledgeBaseService()
