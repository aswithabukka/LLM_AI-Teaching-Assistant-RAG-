"""
Quiz API Routes

Endpoints for generating and managing quizzes based on document content.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.database import User, Document
from app.services.quiz_service import QuizService


router = APIRouter(prefix="/quiz", tags=["quiz"])


class QuizGenerationRequest(BaseModel):
    """Request model for quiz generation."""
    document_id: int
    num_questions: int = 10
    question_types: List[str] = ["mcq", "true_false"]


class QuizQuestion(BaseModel):
    """Quiz question model."""
    id: int
    type: str  # "mcq" or "true_false"
    question: str
    options: Optional[List[str]] = None  # For MCQ questions
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    """Quiz response model."""
    document_id: int
    document_name: str
    total_questions: int
    question_types: List[str]
    questions: List[QuizQuestion]


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a quiz based on document content.
    
    Args:
        request: Quiz generation parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Generated quiz with questions and answers
    """
    # Verify document exists and user has access
    document = db.query(Document).filter(Document.id == request.document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access to the document (through course membership)
    # For now, we'll allow access if the document exists
    # TODO: Add proper course membership validation
    
    try:
        # Generate quiz using quiz service
        quiz_service = QuizService()
        quiz_result = quiz_service.generate_quiz(
            document_id=request.document_id,
            db=db,
            num_questions=request.num_questions,
            question_types=request.question_types
        )
        
        # Convert to response format
        questions = []
        for q in quiz_result["quiz_data"]["questions"]:
            question = QuizQuestion(
                id=q["id"],
                type=q["type"],
                question=q["question"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"]
            )
            
            if q["type"] == "mcq" and "options" in q:
                question.options = q["options"]
            
            questions.append(question)
        
        return QuizResponse(
            document_id=quiz_result["document_id"],
            document_name=quiz_result["document_name"],
            total_questions=quiz_result["total_questions"],
            question_types=quiz_result["question_types"],
            questions=questions
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error generating quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz"
        )


@router.get("/documents/{course_id}")
async def get_quiz_eligible_documents(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of documents that can be used for quiz generation.
    
    Args:
        course_id: Course ID to get documents from
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of documents eligible for quiz generation
    """
    # Get processed documents from the course
    documents = db.query(Document).filter(
        Document.course_id == course_id,
        Document.is_processed == True
    ).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.original_filename,
            "upload_date": doc.created_at,
            "page_count": doc.page_count
        }
        for doc in documents
    ]
