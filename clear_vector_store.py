#!/usr/bin/env python3
"""
Clear vector store data for StudyMate AI

This script removes all vector embeddings from ChromaDB.
Use this when you want to start fresh or fix data isolation issues.
"""

import os
import shutil
import sys

def clear_vector_store():
    """Clear all vector store data."""
    vector_store_path = os.path.join(os.getcwd(), "data", "chromadb")
    
    if os.path.exists(vector_store_path):
        try:
            shutil.rmtree(vector_store_path)
            print("✅ Vector store cleared successfully!")
            print(f"📁 Removed: {vector_store_path}")
            print("\n💡 Note: You'll need to re-upload and process your documents.")
            return True
        except Exception as e:
            print(f"❌ Error clearing vector store: {e}")
            return False
    else:
        print("ℹ️  Vector store directory doesn't exist - nothing to clear.")
        return True

if __name__ == "__main__":
    print("🧹 StudyMate AI - Clear Vector Store")
    print("=" * 40)
    
    # Confirm with user
    response = input("Are you sure you want to clear all vector store data? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        success = clear_vector_store()
        sys.exit(0 if success else 1)
    else:
        print("Operation cancelled.")
        sys.exit(0)
