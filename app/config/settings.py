import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "")
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/app.db")
    
    # Application Settings
    app_name: str = os.getenv("APP_NAME", "StudyMate AI")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "supersecretkey")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Storage Settings
    storage_type: str = os.getenv("STORAGE_TYPE", "local")
    s3_bucket_name: Optional[str] = os.getenv("S3_BUCKET_NAME")
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: Optional[str] = os.getenv("AWS_REGION")
    
    # LLM Settings
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    
    # Application Paths
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
    processed_dir: Path = Path(os.getenv("PROCESSED_DIR", "data/processed"))
    temp_dir: Path = Path(os.getenv("TEMP_DIR", "data/temp"))
    
    # Vector DB Settings
    vector_db_name: str = os.getenv("VECTOR_DB_NAME", "course-notes-qa")
    vector_db_dimension: int = int(os.getenv("VECTOR_DB_DIMENSION", "1536"))  # OpenAI embedding dimension
    
    # RAG Settings
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    top_k_retrieval: int = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    
    # OAuth Settings
    google_client_id: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    github_client_id: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    github_client_secret: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET")
    facebook_client_id: Optional[str] = os.getenv("FACEBOOK_CLIENT_ID")
    facebook_client_secret: Optional[str] = os.getenv("FACEBOOK_CLIENT_SECRET")
    oauth_redirect_uri: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501/oauth/callback")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create a global settings object
settings = Settings()

# Ensure directories exist
for directory in [settings.upload_dir, settings.processed_dir, settings.temp_dir]:
    full_path = BASE_DIR / directory
    full_path.mkdir(parents=True, exist_ok=True)
