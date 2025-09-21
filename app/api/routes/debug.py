from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.database import User, Course, Document
from app.core.rag_pipeline import RAGPipeline

router = APIRouter()
rag_pipeline = RAGPipeline()


@router.get("/vector-stats")
async def get_vector_stats(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get vector store statistics (for debugging).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return rag_pipeline.vector_store.get_stats()


@router.get("/document-vectors/{document_id}")
async def get_document_vectors(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    List vectors for a specific document (for debugging).
    """
    # Check if document exists and user has access
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user owns the course
    course = db.query(Course).filter(
        Course.id == document.course_id, 
        Course.owner_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    vectors = rag_pipeline.vector_store.list_vectors_by_document(document_id)
    
    return {
        "document_id": document_id,
        "document_name": document.filename,
        "course_id": document.course_id,
        "vectors_found": len(vectors),
        "vectors": vectors
    }
