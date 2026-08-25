import os
import uuid
import shutil
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import AppException, NotFoundException, ForbiddenException
from backend.app.core.logging import logger
from backend.app.models.document import Document
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.rag.parser import document_parser
from backend.app.rag.chunker import chunker
from backend.app.schemas.document import ChunkMetadata
from backend.app.services.vector_service import vector_service


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv"}


class DocumentService:
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise AppException(
                message=f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

    @staticmethod
    def _get_storage_path(user_id: uuid.UUID, kb_id: uuid.UUID) -> str:
        base_dir = os.path.abspath(settings.UPLOAD_DIR)
        kb_dir = os.path.join(base_dir, str(user_id), str(kb_id))
        os.makedirs(kb_dir, exist_ok=True)
        return kb_dir

    @classmethod
    def save_file(
        cls,
        file: UploadFile,
        user_id: uuid.UUID,
        kb_id: uuid.UUID,
        doc_id: uuid.UUID
    ) -> str:
        kb_dir = cls._get_storage_path(user_id, kb_id)
        clean_filename = f"{doc_id}_{file.filename}"
        dest_path = os.path.join(kb_dir, clean_filename)

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file size
        file_size_bytes = os.path.getsize(dest_path)
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size_bytes > max_bytes:
            os.remove(dest_path)
            raise AppException(
                message=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
            )

        return dest_path

    @classmethod
    def process_document(cls, db: Session, doc_id: uuid.UUID) -> List[ChunkMetadata]:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise NotFoundException(message=f"Document {doc_id} not found.")

        try:
            doc.status = "processing"
            db.commit()

            # 1. Parse pages
            pages = document_parser.parse_file(doc.file_path, doc.original_filename)

            # 2. Generate chunks
            chunks = chunker.chunk_pages(
                pages=pages,
                document_id=doc.id,
                user_id=doc.user_id,
                knowledge_base_id=doc.knowledge_base_id,
                filename=doc.original_filename
            )

            if not chunks:
                raise AppException(message="No chunks could be extracted from document.")

            # 3. Upsert chunks into Vector Database
            vector_service.upsert_chunks(chunks)

            doc.chunk_count = len(chunks)
            doc.status = "ready"
            doc.error_message = None
            db.commit()
            db.refresh(doc)
            logger.info(f"Document {doc.id} successfully processed and indexed into {len(chunks)} chunks.")
            return chunks

        except Exception as e:
            db.rollback()
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            logger.error(f"Failed to process document {doc_id}: {str(e)}")
            raise AppException(message=f"Document processing failed: {str(e)}")

    @classmethod
    def upload_and_process(
        cls,
        db: Session,
        file: UploadFile,
        kb_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> tuple[Document, List[ChunkMetadata]]:
        # 1. Validate file
        cls.validate_file(file)

        # 2. Check knowledge base ownership
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise NotFoundException(message=f"Knowledge base {kb_id} not found.")
        if kb.user_id != user_id:
            raise ForbiddenException(message="You do not have permission to upload to this knowledge base.")

        # 3. Create Document DB record
        doc_id = uuid.uuid4()
        file_path = cls.save_file(file, user_id, kb_id, doc_id)
        file_size = os.path.getsize(file_path)

        doc = Document(
            id=doc_id,
            filename=f"{doc_id}_{file.filename}",
            original_filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            file_size=file_size,
            file_path=file_path,
            status="uploaded",
            knowledge_base_id=kb_id,
            user_id=user_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 4. Ingest, chunk and index
        chunks = cls.process_document(db, doc.id)
        return doc, chunks

    @staticmethod
    def list_by_kb(db: Session, kb_id: uuid.UUID, user_id: uuid.UUID) -> List[Document]:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise NotFoundException(message=f"Knowledge base {kb_id} not found.")
        if kb.user_id != user_id:
            raise ForbiddenException(message="You do not have permission to access this knowledge base.")

        return db.query(Document).filter(
            Document.knowledge_base_id == kb_id,
            Document.user_id == user_id
        ).all()

    @staticmethod
    def get_by_id(db: Session, doc_id: uuid.UUID, user_id: uuid.UUID) -> Document:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise NotFoundException(message=f"Document {doc_id} not found.")
        if doc.user_id != user_id:
            raise ForbiddenException(message="You do not have permission to access this document.")
        return doc

    @classmethod
    def delete(cls, db: Session, doc_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        doc = cls.get_by_id(db, doc_id, user_id)
        
        # 1. Delete vectors from Qdrant
        vector_service.delete_by_document(doc_id=doc.id, user_id=user_id)

        # 2. Delete file from disk if it exists
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError as e:
                logger.warning(f"Could not remove file {doc.file_path}: {str(e)}")

        # 3. Delete database record
        db.delete(doc)
        db.commit()
        logger.info(f"Deleted Document {doc_id} and corresponding vectors for user {user_id}")
        return True


document_service = DocumentService()
