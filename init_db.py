#!/usr/bin/env python3
"""
Database initialization script for StudyMate AI
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import Base, engine
from app.models.database import User, Course, Document, DocumentChunk, ChatSession, ChatMessage, Citation
from app.config.settings import settings

def init_database():
    """Initialize the database with all tables."""
    print("🔧 Initializing StudyMate AI database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Print table information
        print("\n📋 Created tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
        print(f"\n📍 Database location: {settings.database_url}")
        print("🎉 Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
