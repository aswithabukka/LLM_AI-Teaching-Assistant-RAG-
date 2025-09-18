from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.database import User, Course, ChatSession, ChatMessage
from app.models.schemas import QuestionRequest, AnswerResponse, ChatSessionResponse, ChatMessageResponse
from app.core.rag_pipeline import RAGPipeline

router = APIRouter()
rag_pipeline = RAGPipeline()


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    question_request: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Ask a question about course notes.
    """
    # Check if course exists and belongs to user
    course = db.query(Course).filter(Course.id == question_request.course_id, Course.owner_id == current_user.id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    
    # Process the question through the RAG pipeline
    answer = rag_pipeline.process_question(
        question=question_request.question,
        course_id=question_request.course_id,
        db=db,
        chat_session_id=question_request.chat_session_id,
        user_id=current_user.id
    )
    
    return answer


@router.get("/chat-sessions", response_model=List[ChatSessionResponse])
async def read_chat_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve chat sessions for the current user.
    """
    chat_sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).offset(skip).limit(limit).all()
    return chat_sessions


@router.get("/chat-sessions/{chat_session_id}", response_model=List[ChatMessageResponse])
async def read_chat_messages(
    chat_session_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve messages for a chat session.
    """
    # Check if chat session exists and belongs to user
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == chat_session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.chat_session_id == chat_session_id
    ).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()
    
    return messages


@router.delete("/chat-sessions/{chat_session_id}", response_model=ChatSessionResponse)
async def delete_chat_session(
    chat_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a chat session.
    """
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == chat_session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    
    db.delete(chat_session)
    db.commit()
    
    return chat_session
