import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.common import APIResponse
from backend.app.schemas.document import DocumentResponse, DocumentUploadResponse
from backend.app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=APIResponse[DocumentUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document into a knowledge base"
)
async def upload_document(
    knowledge_base_id: uuid.UUID = Form(..., description="Target knowledge base UUID"),
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, TXT)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[DocumentUploadResponse]:
    doc, chunks = document_service.upload_and_process(
        db=db,
        file=file,
        kb_id=knowledge_base_id,
        user_id=current_user.id
    )

    upload_data = DocumentUploadResponse(
        id=doc.id,
        filename=doc.original_filename,
        status=doc.status,
        message=f"Document successfully parsed and chunked into {len(chunks)} chunks.",
        chunk_count=len(chunks)
    )

    return APIResponse(
        success=True,
        message="Document uploaded and processed successfully.",
        data=upload_data
    )


@router.get(
    "/kb/{kb_id}",
    response_model=APIResponse[List[DocumentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all documents in a specific knowledge base"
)
def list_documents(
    kb_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[List[DocumentResponse]]:
    docs = document_service.list_by_kb(db=db, kb_id=kb_id, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Documents retrieved successfully.",
        data=[DocumentResponse.model_validate(d) for d in docs]
    )


@router.get(
    "/{doc_id}",
    response_model=APIResponse[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get status and details of a single document"
)
def get_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[DocumentResponse]:
    doc = document_service.get_by_id(db=db, doc_id=doc_id, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Document retrieved successfully.",
        data=DocumentResponse.model_validate(doc)
    )


@router.post(
    "/extract-text",
    summary="Directly extract text from an uploaded document (PDF, DOCX, TXT, MD)"
)
async def extract_document_text(
    file: UploadFile = File(..., description="Document file to extract text from")
):
    import tempfile
    from backend.app.rag.parser import document_parser

    # Save to temp file
    suffix = os.path.splitext(file.filename)[1].lower() or ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        pages = document_parser.parse_file(temp_path, file.filename)
        full_text = "\n\n".join(p.text for p in pages if p.text.strip())
        return {
            "success": True,
            "filename": file.filename,
            "page_count": len(pages),
            "text": full_text,
            "pages": [{"page_number": p.page_number, "text": p.text} for p in pages]
        }
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.delete(
    "/{doc_id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete document and remove its stored file"
)
def delete_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[dict]:
    document_service.delete(db=db, doc_id=doc_id, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Document deleted successfully.",
        data={"id": str(doc_id)}
    )

