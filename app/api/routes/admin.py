from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_admin_user
from app.core.database import get_db
from app.models.database import User, Course, Document
from app.models.schemas import UserResponse
from app.core.rag_pipeline import RAGPipeline

router = APIRouter()
rag_pipeline = RAGPipeline()


@router.get("/users", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Retrieve users.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/stats", response_model=Dict[str, Any])
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Get system statistics.
    """
    # Get database stats
    user_count = db.query(User).count()
    course_count = db.query(Course).count()
    document_count = db.query(Document).count()
    
    # Get vector store stats
    vector_stats = rag_pipeline.vector_store.get_stats()
    
    return {
        "database_stats": {
            "user_count": user_count,
            "course_count": course_count,
            "document_count": document_count,
        },
        "vector_store_stats": vector_stats,
    }


@router.post("/reindex/{document_id}", response_model=Dict[str, Any])
async def reindex_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Reindex a document in the vector store.
    """
    # Get the document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Delete existing chunks from vector store
    from app.models.database import DocumentChunk
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    vector_ids = [chunk.vector_id for chunk in chunks]
    rag_pipeline.vector_store.delete_vectors(vector_ids)
    
    # Delete existing chunks from database
    for chunk in chunks:
        db.delete(chunk)
    db.commit()
    
    # Process the document again
    from app.services.file_service import FileService
    file_service = FileService()
    success, page_count, new_chunks = file_service.process_document(document)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document",
        )
    
    # Index the new chunks
    new_vector_ids = rag_pipeline.index_document_chunks(new_chunks, document.id, document.course_id, document.original_filename)
    
    # Save new chunks to database
    for i, chunk in enumerate(new_chunks):
        vector_id = new_vector_ids[i] if i < len(new_vector_ids) else f"doc_{document.id}_chunk_{i}"
        db_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=i,
            content=chunk["content"],
            page_number=chunk["metadata"].get("page_number"),
            vector_id=vector_id,
            meta_data=str(chunk["metadata"])
        )
        db.add(db_chunk)
    
    db.commit()
    
    return {
        "success": True,
        "document_id": document_id,
        "chunks_count": len(new_chunks),
    }


@router.post("/toggle-user-status/{user_id}", response_model=UserResponse)
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Toggle user active status.
    """
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Toggle active status
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    return user
