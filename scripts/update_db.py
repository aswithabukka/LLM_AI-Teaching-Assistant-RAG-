import os
import sys
import sqlite3
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import settings

def update_database():
    """Update the database schema to add missing columns."""
    print(f"Using database at: {settings.database_url}")
    
    # Extract file path from SQLite URL
    db_path = settings.database_url.replace("sqlite:///", "")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if processing_error column exists in documents table
    cursor.execute("PRAGMA table_info(documents)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add processing_error column if it doesn't exist
    if 'processing_error' not in columns:
        print("Adding processing_error column to documents table...")
        cursor.execute("ALTER TABLE documents ADD COLUMN processing_error TEXT")
        conn.commit()
        print("Column added successfully.")
    else:
        print("processing_error column already exists.")
    
    # Close connection
    conn.close()
    return True

if __name__ == "__main__":
    update_database()
