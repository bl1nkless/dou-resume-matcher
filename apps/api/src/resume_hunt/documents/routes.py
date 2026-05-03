from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from resume_hunt.auth.dependencies import get_current_user
from resume_hunt.db.models import User
from resume_hunt.db.session import get_db
from resume_hunt.documents.schemas import DocumentResponse, TextDocumentRequest
from resume_hunt.documents.service import create_text_document, persist_uploaded_file

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/resume", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_resume_text(
    payload: TextDocumentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> DocumentResponse:
    return create_text_document(
        session,
        user_id=current_user.id,
        document_type="resume",
        text=payload.text,
        source_url=payload.source_url,
    )


@router.post("/resume/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> DocumentResponse:
    supported_types = {
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if file.content_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Supported uploads for M1 are TXT, PDF, and DOCX. PDF/DOCX text extraction lands in M2.",
        )

    object_uri, text = await persist_uploaded_file(current_user.id, file)
    if file.content_type != "text/plain" or len(text.strip()) < 20:
        text = f"Uploaded file stored at {object_uri}. Text extraction will run in M2."

    return create_text_document(
        session,
        user_id=current_user.id,
        document_type="resume",
        text=text,
        object_storage_uri=object_uri,
    )
