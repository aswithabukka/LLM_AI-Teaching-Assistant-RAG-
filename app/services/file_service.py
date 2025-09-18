import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.database import Document, Course
from app.utils.document_processor import DocumentProcessor


class FileService:
    """
    Service for handling file uploads, storage, and processing.
    """
    
    def __init__(self):
        """Initialize the file service."""
        self.upload_dir = settings.upload_dir
        self.processed_dir = settings.processed_dir
        self.temp_dir = settings.temp_dir
        
        # Ensure directories exist
        for directory in [self.upload_dir, self.processed_dir, self.temp_dir]:
            os.makedirs(directory, exist_ok=True)
    
    async def save_upload(self, file: UploadFile, course_id: int, db: Session) -> Optional[Document]:
        """
        Save an uploaded file and create a database record.
        
        Args:
            file: The uploaded file.
            course_id: ID of the course the file belongs to.
            db: Database session.
            
        Returns:
            Optional[Document]: The created document record, or None if failed.
        """
        try:
            # Check if course exists
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return None
            
            # Generate a unique filename
            original_filename = file.filename
            file_extension = original_filename.split(".")[-1].lower() if "." in original_filename else ""
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Create file path
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Create document record
            document = Document(
                filename=unique_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_type=file_extension,
                file_size=os.path.getsize(file_path),
                course_id=course_id,
                is_processed=False,
                is_indexed=False
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            return document
        
        except Exception as e:
            import traceback
            print(f"Error saving upload: {e}")
            print(f"Error details: {traceback.format_exc()}")
            return None
    
    def process_document(self, document: Document) -> Tuple[bool, int, list]:
        """
        Process a document to extract text and create chunks.
        
        Args:
            document: The document to process.
            
        Returns:
            Tuple[bool, int, list]: Success status, page count, and list of chunks.
        """
        try:
            # Check file size for ultra-fast processing
            import os
            file_size = os.path.getsize(document.file_path) if os.path.exists(document.file_path) else 0
            tiny_file_threshold = 15 * 1024  # 15KB threshold
            use_ultra_fast = file_size > 0 and file_size < tiny_file_threshold
            
            # Create document processor with ultra-fast flag
            processor = DocumentProcessor(document.file_path, document.file_type, use_ultra_fast_processing=use_ultra_fast)
            
            # Process the document
            success = processor.process()
            if not success:
                return False, 0, []
            
            # Get page count
            page_count = processor.get_page_count()
            
            # Create chunks
            chunks = processor.chunk_document()
            
            # Update document with page count
            document.page_count = page_count
            
            return True, page_count, chunks
        
        except Exception as e:
            import traceback
            print(f"Error processing document: {e}")
            print(f"Processing error details: {traceback.format_exc()}")
            return False, 0, []
    
    def get_document_path(self, document: Document) -> str:
        """
        Get the path to a document file.
        
        Args:
            document: The document.
            
        Returns:
            str: Path to the document file.
        """
        return document.file_path
    
    def delete_document(self, document: Document) -> bool:
        """
        Delete a document file and its record.
        
        Args:
            document: The document to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            # Delete the file
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            return True
        
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
