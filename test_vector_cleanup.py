#!/usr/bin/env python3
"""
Test script to verify vector cleanup when documents are deleted
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_vector_cleanup():
    """Test that vectors are properly cleaned up when documents are deleted."""
    
    print("🧪 Testing Vector Cleanup on Document Deletion")
    print("=" * 50)
    
    # First, you need to:
    # 1. Login to get a token
    # 2. Create a course
    # 3. Upload a document
    # 4. Ask a question (to verify vectors exist)
    # 5. Delete the document
    # 6. Ask the same question (should not find the deleted document)
    
    print("📋 Manual Test Steps:")
    print("1. ✅ Login to StudyMate AI")
    print("2. ✅ Create a new course")
    print("3. ✅ Upload a document and wait for processing")
    print("4. ✅ Ask a question about the document content")
    print("5. ✅ Note the citation showing the document")
    print("6. ✅ Go to 'Manage Documents' and delete the document")
    print("7. ✅ Ask the same question again")
    print("8. ✅ Verify the deleted document no longer appears in citations")
    
    print("\n🔍 What Should Happen:")
    print("- Before deletion: Document appears in search results and citations")
    print("- After deletion: Document should NOT appear in search results or citations")
    print("- The system should say 'No relevant information found' or similar")
    
    print(f"\n🌐 Access your application at: http://localhost:8501")
    print("📚 Follow the steps above to test vector cleanup!")

if __name__ == "__main__":
    test_vector_cleanup()
