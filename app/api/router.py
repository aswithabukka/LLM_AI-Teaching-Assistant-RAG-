from fastapi import APIRouter
from app.api.routes import auth, courses, documents, questions, admin

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(questions.router, prefix="/questions", tags=["Questions"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
