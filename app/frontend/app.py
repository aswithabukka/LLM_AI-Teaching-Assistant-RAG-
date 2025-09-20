import streamlit as st
import requests
import json
import os
import time
from typing import Dict, List, Any, Optional

# Set page configuration
st.set_page_config(
    page_title="Course Notes Q&A",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API URL
API_URL = "http://127.0.0.1:25000"


# Authentication functions
def login(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Log in a user.
    
    Args:
        email: User email.
        password: User password.
        
    Returns:
        Optional[Dict[str, Any]]: User data if login successful, None otherwise.
    """
    try:
        # Print the URL being used for troubleshooting
        login_url = f"{API_URL}/api/auth/token"
        st.write(f"🔍 Attempting login at: {login_url}")
        st.write(f"📧 Email: {email}")
        
        # Set up request with proper headers and data
        response = requests.post(
            login_url,
            # Important: Don't set the Content-Type header manually with requests.post when using form data
            # Let the requests library handle the encoding and headers
            data={"username": email, "password": password},
            timeout=10
        )
        
        # Debug response
        st.write(f"📡 Response status: {response.status_code}")
        st.write(f"📄 Response text: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Login successful!")
            return data
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"❌ Login failed: {error_detail}")
            except:
                st.error(f"❌ Login failed with status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"💥 Error during login: {e}")
        return None


def register(email: str, password: str) -> bool:
    """
    Register a new user.
    
    Args:
        email: User email.
        password: User password.
        
    Returns:
        bool: True if registration successful, False otherwise.
    """
    try:
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json={"email": email, "password": password},
        )
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error during registration: {e}")
        return False


def get_user_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Get user information.
    
    Args:
        token: Authentication token.
        
    Returns:
        Optional[Dict[str, Any]]: User data if successful, None otherwise.
    """
    try:
        response = requests.get(
            f"{API_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error getting user info: {e}")
        return None


# Course functions
def get_courses(token: str) -> List[Dict[str, Any]]:
    """
    Get courses for the current user.
    
    Args:
        token: Authentication token.
        
    Returns:
        List[Dict[str, Any]]: List of courses.
    """
    try:
        response = requests.get(
            f"{API_URL}/api/courses/",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error getting courses: {response.json().get('detail', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Error getting courses: {e}")
        return []


def create_course(token: str, title: str, description: str) -> Optional[Dict[str, Any]]:
    """
    Create a new course.
    
    Args:
        token: Authentication token.
        title: Course title.
        description: Course description.
        
    Returns:
        Optional[Dict[str, Any]]: Course data if successful, None otherwise.
    """
    try:
        response = requests.post(
            f"{API_URL}/api/courses/",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": title, "description": description},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating course: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error creating course: {e}")
        return None


# Document functions
def get_document_status(token: str, document_id: int) -> Dict[str, Any]:
    """
    Check the processing status of a specific document.
    
    Args:
        token: Authentication token.
        document_id: Document ID.
        
    Returns:
        Dict[str, Any]: Document status information.
    """
    try:
        response = requests.get(
            f"{API_URL}/api/documents/{document_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting document status: {response.status_code}")
            return {"is_processed": False, "processing_error": "Failed to get status"}
    except Exception as e:
        print(f"Error checking document status: {e}")
        return {"is_processed": False, "processing_error": str(e)}


def cancel_document_processing(token: str, document_id: int) -> bool:
    """
    Cancel document processing and delete the document.
    
    Args:
        token: Authentication token.
        document_id: Document ID to cancel.
        
    Returns:
        bool: True if cancellation was successful, False otherwise.
    """
    try:
        response = requests.delete(
            f"{API_URL}/api/documents/{document_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"Error cancelling document: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error cancelling document: {e}")
        return False


def get_documents(token: str, course_id: int) -> List[Dict[str, Any]]:
    """
    Get documents for a course.
    
    Args:
        token: Authentication token.
        course_id: Course ID.
        
    Returns:
        List[Dict[str, Any]]: List of documents.
    """
    try:
        response = requests.get(
            f"{API_URL}/api/documents/course/{course_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error getting documents: {response.json().get('detail', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Error getting documents: {e}")
        return []


def upload_document(token: str, course_id: int, file) -> Optional[Dict[str, Any]]:
    """
    Upload a document.
    
    Args:
        token: Authentication token.
        course_id: Course ID.
        file: File to upload.
        
    Returns:
        Optional[Dict[str, Any]]: Document data if successful, None otherwise.
    """
    try:
        files = {"file": file}
        data = {"course_id": course_id}
        
        response = requests.post(
            f"{API_URL}/api/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data,
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error uploading document: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error uploading document: {e}")
        return None


# Question functions
def ask_question(token: str, question: str, course_id: int, chat_session_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Ask a question.
    
    Args:
        token: Authentication token.
        question: Question to ask.
        course_id: Course ID.
        chat_session_id: Optional chat session ID.
        
    Returns:
        Optional[Dict[str, Any]]: Answer data if successful, None otherwise.
    """
    try:
        data = {
            "question": question,
            "course_id": course_id,
            "chat_session_id": chat_session_id,
        }
        
        response = requests.post(
            f"{API_URL}/api/questions/ask",
            headers={"Authorization": f"Bearer {token}"},
            json=data,
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error asking question: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error asking question: {e}")
        return None


def get_chat_sessions(token: str) -> List[Dict[str, Any]]:
    """
    Get chat sessions for the current user.
    
    Args:
        token: Authentication token.
        
    Returns:
        List[Dict[str, Any]]: List of chat sessions.
    """
    try:
        response = requests.get(
            f"{API_URL}/api/questions/chat-sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error getting chat sessions: {response.json().get('detail', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Error getting chat sessions: {e}")
        return []


def get_chat_messages(token: str, chat_session_id: int) -> List[Dict[str, Any]]:
    """
    Get messages for a chat session.
    
    Args:
        token: Authentication token.
        chat_session_id: Chat session ID.
        
    Returns:
        List[Dict[str, Any]]: List of chat messages.
    """
    try:
        response = requests.get(
            f"{API_URL}/api/questions/chat-sessions/{chat_session_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error getting chat messages: {response.json().get('detail', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Error getting chat messages: {e}")
        return []


# Main app
def main():
    # Check if user is logged in
    if "token" not in st.session_state:
        show_login_page()
    else:
        # Check if token is valid
        user_info = get_user_info(st.session_state.token["access_token"])
        if user_info:
            show_main_app(user_info)
        else:
            # Token is invalid, show login page
            st.session_state.pop("token", None)
            show_login_page()


def show_login_page():
    """Show the login page."""
    st.title("Course Notes Q&A")
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if email and password:
                token = login(email, password)
                if token:
                    st.session_state.token = token
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            else:
                st.error("Please enter email and password")
    
    with tab2:
        st.header("Register")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        
        if st.button("Register"):
            if email and password and confirm_password:
                if password == confirm_password:
                    if register(email, password):
                        st.success("Registration successful! Please login.")
                else:
                    st.error("Passwords do not match")
            else:
                st.error("Please fill all fields")


def show_main_app(user_info):
    """
    Show the main application.
    
    Args:
        user_info: User information.
    """
    # Sidebar
    with st.sidebar:
        st.title("Course Notes Q&A")
        st.write(f"Welcome, {user_info['email']}")
        
        if st.button("Logout"):
            st.session_state.pop("token", None)
            st.rerun()
        
        st.divider()
        
        # Navigation
        page = st.radio("Navigation", ["Courses", "Chat History"])
        
        if page == "Courses":
            # Get courses
            courses = get_courses(st.session_state.token["access_token"])
            
            # Course selection
            if courses:
                course_names = [course["title"] for course in courses]
                course_ids = [course["id"] for course in courses]
                
                selected_course_index = st.selectbox(
                    "Select Course",
                    range(len(courses)),
                    format_func=lambda i: course_names[i],
                )
                
                st.session_state.selected_course_id = course_ids[selected_course_index]
                st.session_state.selected_course_name = course_names[selected_course_index]
            
            # Create new course
            st.divider()
            st.subheader("Create New Course")
            new_course_title = st.text_input("Course Title")
            new_course_description = st.text_area("Course Description")
            
            if st.button("Create Course"):
                if new_course_title:
                    course = create_course(
                        st.session_state.token["access_token"],
                        new_course_title,
                        new_course_description,
                    )
                    if course:
                        st.success(f"Course '{new_course_title}' created successfully!")
                        st.rerun()
                else:
                    st.error("Please enter a course title")
        
        elif page == "Chat History":
            # Get chat sessions
            chat_sessions = get_chat_sessions(st.session_state.token["access_token"])
            
            # Chat session selection
            if chat_sessions:
                chat_session_titles = [session["title"] for session in chat_sessions]
                chat_session_ids = [session["id"] for session in chat_sessions]
                
                selected_session_index = st.selectbox(
                    "Select Chat Session",
                    range(len(chat_sessions)),
                    format_func=lambda i: chat_session_titles[i],
                )
                
                st.session_state.selected_chat_session_id = chat_session_ids[selected_session_index]
            else:
                st.info("No chat sessions found. Start a new conversation in the Courses page.")
    
    # Main content
    if page == "Courses":
        show_courses_page()
    elif page == "Chat History":
        show_chat_history_page()


def show_courses_page():
    """Show the courses page."""
    if hasattr(st.session_state, "selected_course_id"):
        st.title(f"Course: {st.session_state.selected_course_name}")
        
        # Create tabs for documents and Q&A
        tab1, tab2 = st.tabs(["Documents", "Q&A"])
        
        with tab1:
            st.header("Documents")
            
            # Upload document
            st.subheader("Upload Document")
            uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "pptx"])
            
            if uploaded_file is not None:
                if st.button("Upload"):
                    with st.spinner("Uploading and processing document..."):
                        document = upload_document(
                            st.session_state.token["access_token"],
                            st.session_state.selected_course_id,
                            uploaded_file,
                        )
                        if document:
                            st.success(f"Document '{document['original_filename']}' uploaded successfully!")
            
            # Show documents with auto-refresh for processing status
            st.subheader("Course Documents")
            
            # Add a refresh button and auto-refresh for processing documents
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("🔄 Refresh"):
                    st.rerun()
                
            # Check if we need to auto-refresh for processing documents
            documents = get_documents(st.session_state.token["access_token"], st.session_state.selected_course_id)
            has_processing_docs = any(not doc["is_processed"] for doc in documents)
            
            # Display each document with status
            for document in documents:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(document["original_filename"])
                with col2:
                    st.write(f"Pages: {document['page_count'] or 'N/A'}")
                with col3:
                    if document["is_processed"]:
                        st.write("✅ Ready")
                    else:
                        st.write("⏳ Processing...") 
                with col4:
                    # Show cancel button for processing documents
                    if not document["is_processed"]:
                        if st.button("❌ Cancel", key=f"cancel_{document['id']}"):
                            if cancel_document_processing(st.session_state.token["access_token"], document["id"]):
                                st.success("Document processing cancelled")
                                st.rerun()
                            else:
                                st.error("Failed to cancel document processing")
                        
                # If there's an error, show it
                if document.get("processing_error"):
                    st.error(f"Error: {document['processing_error']}")
            
            # Auto-refresh if there are processing documents
            if has_processing_docs:
                time.sleep(3)  # Wait 3 seconds before refreshing
                st.rerun()
            
            if not documents:
                st.info("No documents found. Upload some documents to get started.")
        
        with tab2:
            st.header("Ask Questions")
            
            # Initialize chat history if not exists
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            # Initialize chat session ID if not exists
            if "current_chat_session_id" not in st.session_state:
                st.session_state.current_chat_session_id = None
            
            # Display chat history
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        
                        # Display citations if available
                        if "citations" in message and message["citations"]:
                            st.divider()
                            st.write("**Sources:**")
                            for citation in message["citations"]:
                                with st.expander(f"Source: {citation['source']}, Page: {citation['page']}"):
                                    st.write(citation["quote"])
            
            # Question input
            question = st.chat_input("Ask a question about your course notes")
            
            if question:
                # Add user message to chat history
                st.session_state.chat_history.append({"role": "user", "content": question})
                
                # Display user message
                st.chat_message("user").write(question)
                
                # Get answer
                with st.spinner("Thinking..."):
                    answer = ask_question(
                        st.session_state.token["access_token"],
                        question,
                        st.session_state.selected_course_id,
                        st.session_state.current_chat_session_id,
                    )
                
                if answer:
                    # Update chat session ID
                    st.session_state.current_chat_session_id = answer["chat_session_id"]
                    
                    # Display assistant message
                    with st.chat_message("assistant"):
                        st.write(answer["answer"])
                        
                        # Display confidence
                        st.progress(answer["confidence"])
                        st.caption(f"Confidence: {answer['confidence']:.2f}")
                        
                        # Display citations
                        if answer["citations"]:
                            st.divider()
                            st.write("**Sources:**")
                            for citation in answer["citations"]:
                                with st.expander(f"Source: {citation['source']}, Page: {citation['page']}"):
                                    st.write(citation["quote"])
                    
                    # Add assistant message to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer["answer"],
                        "citations": answer["citations"],
                        "confidence": answer["confidence"],
                    })
    else:
        st.info("Please select a course from the sidebar or create a new one.")


def show_chat_history_page():
    """Show the chat history page."""
    if hasattr(st.session_state, "selected_chat_session_id"):
        # Get chat messages
        messages = get_chat_messages(st.session_state.token["access_token"], st.session_state.selected_chat_session_id)
        
        if messages:
            st.title("Chat History")
            
            # Display messages
            for message in messages:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        
                        # Display citations if available
                        if "citations" in message and message["citations"]:
                            st.divider()
                            st.write("**Sources:**")
                            for citation in message["citations"]:
                                with st.expander(f"Source: {citation['source']}, Page: {citation['page']}"):
                                    st.write(citation["quote"])
        else:
            st.info("No messages found for this chat session.")
    else:
        st.info("Please select a chat session from the sidebar.")


if __name__ == "__main__":
    main()
