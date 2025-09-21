from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.database import User, Course, Document, DocumentChunk
from app.models.schemas import CourseCreate, CourseResponse
from app.core.rag_pipeline import RAGPipeline

router = APIRouter()
rag_pipeline = RAGPipeline()


@router.post("/", response_model=CourseResponse)
async def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new course.
    """
    course = Course(
        title=course_in.title,
        description=course_in.description,
        owner_id=current_user.id,
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return course


@router.get("/", response_model=List[CourseResponse])
async def read_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve courses.
    """
    courses = db.query(Course).filter(Course.owner_id == current_user.id).offset(skip).limit(limit).all()
    return courses


@router.get("/{course_id}", response_model=CourseResponse)
async def read_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get course by ID.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a course.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    
    # Update course attributes
    course.title = course_in.title
    course.description = course_in.description
    
    db.commit()
    db.refresh(course)
    
    return course


@router.delete("/{course_id}", response_model=CourseResponse)
async def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a course.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    
    # Delete all vectors associated with this course from vector store
    try:
        metadata_filter = {"course_id": {"$eq": course_id}}
        rag_pipeline.vector_store.delete_by_metadata(metadata_filter)
        print(f"Deleted vectors for course {course_id}")
    except Exception as e:
        print(f"Warning: Could not delete vectors for course {course_id}: {e}")
    
    # Delete all document chunks for this course (cascade will handle documents)
    documents = db.query(Document).filter(Document.course_id == course_id).all()
    for document in documents:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).all()
        for chunk in chunks:
            db.delete(chunk)
        db.delete(document)
    
    # Delete the course
    db.delete(course)
    db.commit()
    
    return course
