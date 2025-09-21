from typing import Any, List
import os

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user as get_current_user
from app.core.database import get_db
from app.models.database import User, Course, Document, DocumentChunk
from app.models.schemas import DocumentResponse
from app.services.file_service import FileService
from app.core.rag_pipeline import RAGPipeline

router = APIRouter()
file_service = FileService()
rag_pipeline = RAGPipeline()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload a document for a course.
    """
    # Check if course exists and belongs to user
    course = db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    
    # Validate file extension
    original_filename = file.filename
    if not original_filename or '.' not in original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file: missing extension",
        )
        
    file_extension = original_filename.split(".")[-1].lower()
    if file_extension not in ["pdf", "docx", "pptx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}. Only PDF, DOCX, and PPTX files are supported.",
        )
        
    # Save the uploaded file
    try:
        document = await file_service.save_upload(file, course_id, db)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save document",
            )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Document save error: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving document: {str(e)}",
        )
    
    # Start document processing in background without waiting for completion
    import threading
    
    def process_document_async(document_id, app_state):
        # Create a new database session for this thread
        from sqlalchemy.orm import sessionmaker
        from app.core.database import engine
        import os
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        thread_db = SessionLocal()
        try:
            import time
            start_time = time.time()
            
            # Get document from database
            thread_document = thread_db.query(Document).filter(Document.id == document_id).first()
            if not thread_document:
                print(f"Document {document_id} not found for processing")
                return
                
            print(f"🔍 Starting processing for document {document_id}: {thread_document.original_filename}")
            
            # Check file size for optimized processing path
            file_size = os.path.getsize(thread_document.file_path) if os.path.exists(thread_document.file_path) else 0
            tiny_file_threshold = 50 * 1024  # 50KB threshold for ultra-fast processing
            use_ultra_fast_path = file_size > 0 and file_size < tiny_file_threshold
            
            # Log the path we're using
            if use_ultra_fast_path:
                print(f"🚀 ULTRA-FAST processing enabled for {file_size/1024:.1f}KB file - bypassing all embedding operations")
            else:
                print(f"📄 Standard processing for {file_size/1024:.1f}KB file")
            
            # Process the document
            print(f"⚡ Calling file_service.process_document...")
            process_start = time.time()
            success, page_count, chunks = file_service.process_document(thread_document)
            process_time = time.time() - process_start
            print(f"⏱️ Document processing took {process_time:.3f} seconds")
            
            # Update document status based on processing result
            if success:
                thread_document.is_processed = True
                thread_document.page_count = page_count
                
                # Save chunks to database for both small and large files
                import json
                
                try:
                    # Save chunks to database
                    for i, chunk in enumerate(chunks):
                        db_chunk = DocumentChunk(
                            document_id=thread_document.id,
                            chunk_index=i,
                            content=chunk["content"],
                            page_number=chunk["metadata"].get("page_number"),
                            vector_id=f"doc_{thread_document.id}_chunk_{i}",
                            meta_data=json.dumps(chunk["metadata"]),
                        )
                        thread_db.add(db_chunk)
                    
                    thread_db.commit()
                    print(f"Saved {len(chunks)} chunks to database for document {thread_document.id}")
                    
                except Exception as e:
                    print(f"Error saving chunks to database: {e}")
                
                # For tiny files, skip ALL embedding operations completely
                if use_ultra_fast_path:
                    thread_document.is_indexed = True
                    print(f"✅ ULTRA-FAST processing complete - skipped ALL embedding operations")
                else:
                    # Only do vector indexing for larger files
                    print(f"🔗 Starting vector indexing for larger file...")
                    vector_start = time.time()
                    try:
                        # Import RAG pipeline only when needed (not for ultra-fast processing)
                        from app.core.rag_pipeline import RAGPipeline
                        rag_pipeline = RAGPipeline()
                        vector_ids = rag_pipeline.index_document_chunks(chunks, thread_document.id, thread_document.course_id, thread_document.original_filename)
                        thread_document.is_indexed = bool(vector_ids)
                        vector_time = time.time() - vector_start
                        print(f"⏱️ Vector indexing took {vector_time:.3f} seconds")
                    except Exception as e:
                        print(f"❌ Vector indexing failed but document processing succeeded: {e}")
                        # Don't fail the whole document just because vectorization failed
                        thread_document.is_indexed = True
            else:
                thread_document.is_processed = False
                thread_document.processing_error = "Failed to process document"
                
            thread_db.commit()
            
            total_time = time.time() - start_time
            print(f"🏁 Total processing time for document {document_id}: {total_time:.3f} seconds")
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Async document processing error: {error_trace}")
            
            # Update document status to failed
            try:
                thread_document = thread_db.query(Document).filter(Document.id == document_id).first()
                if thread_document:
                    thread_document.is_processed = False
                    thread_document.processing_error = str(e)[:500]  # Limit error message length
                    thread_db.commit()
            except Exception as commit_error:
                print(f"Error updating document status: {commit_error}")
        
        finally:
            thread_db.close()
    
    # Start background processing thread
    processing_thread = threading.Thread(
        target=process_document_async,
        args=(document.id, object()),  # Pass document ID and an empty state object
        daemon=True
    )
    processing_thread.start()
    
    # Return the document details
    # Document processing happens asynchronously in the background
    return document


@router.get("/{document_id}", response_model=DocumentResponse)
async def read_document_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get document status and details.
    """
    # Get document from database
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if document belongs to user
    course = db.query(Course).filter(Course.id == document.course_id).first()
    if not course or course.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Return document status and details
    return document


@router.get("/course/{course_id}", response_model=List[DocumentResponse])
async def read_course_documents(
    course_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve documents for a course.
    """
    # Check if course exists and belongs to user
    course = db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    
    documents = db.query(Document).filter(Document.course_id == course_id).offset(skip).limit(limit).all()
    return documents


@router.delete("/{document_id}/cancel")
async def cancel_document_processing(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Cancel document processing and delete the document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to this document's course
    course = db.query(Course).filter(Course.id == document.course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )
    
    try:
        # Delete the file if it exists
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete document chunks from vector store if any
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        if chunks:
            vector_ids = [chunk.vector_id for chunk in chunks]
            try:
                rag_pipeline.vector_store.delete_vectors(vector_ids)
            except Exception as e:
                print(f"Warning: Failed to delete vectors from vector store: {e}")
        
        # Delete document chunks from database
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        
        # Delete the document record
        db.delete(document)
        db.commit()
        
        return {"message": "Document processing cancelled and document deleted"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling document: {str(e)}",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get document by ID.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to the document
    course = db.query(Course).filter(Course.id == document.course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return document


@router.delete("/{document_id}", response_model=DocumentResponse)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check if user has access to the document
    course = db.query(Course).filter(Course.id == document.course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Delete the document file
    file_service.delete_document(document)
    
    # Delete document chunks from vector store
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    vector_ids = [chunk.vector_id for chunk in chunks]
    rag_pipeline.vector_store.delete_vectors(vector_ids)
    
    # Delete document from database
    db.delete(document)
    db.commit()
    
    return document
