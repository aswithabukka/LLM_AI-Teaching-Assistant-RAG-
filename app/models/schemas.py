from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    original_filename: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None


class DocumentCreate(DocumentBase):
    course_id: int
    filename: str
    file_path: str


class DocumentResponse(DocumentBase):
    id: int
    course_id: int
    filename: str
    is_processed: bool
    is_indexed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkBase(BaseModel):
    document_id: int
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunkCreate(DocumentChunkBase):
    vector_id: str


class DocumentChunkResponse(DocumentChunkBase):
    id: int
    vector_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    title: Optional[str] = None
    course_id: int


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionResponse(ChatSessionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    chat_session_id: int


class ChatMessageResponse(ChatMessageBase):
    id: int
    chat_session_id: int
    created_at: datetime
    citations: List["CitationResponse"] = []

    class Config:
        from_attributes = True


class CitationBase(BaseModel):
    document_id: int
    page_number: Optional[int] = None
    quote: Optional[str] = None
    relevance_score: Optional[float] = None


class CitationCreate(CitationBase):
    message_id: int
    chunk_id: Optional[int] = None


class CitationResponse(CitationBase):
    id: int
    message_id: int
    chunk_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Update forward references
ChatMessageResponse.update_forward_refs()


class QuestionRequest(BaseModel):
    question: str
    chat_session_id: Optional[int] = None
    course_id: int


class AnswerResponse(BaseModel):
    answer: str
    confidence: float
    citations: List[CitationResponse]
    chat_session_id: int
