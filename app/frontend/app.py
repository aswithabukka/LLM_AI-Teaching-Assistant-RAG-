import streamlit as st
import requests
import json
import os
import time
import re
from typing import Dict, List, Any, Optional

# Set page configuration
st.set_page_config(
    page_title="StudyMate AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API URL
API_URL = "http://127.0.0.1:8000"


# Frontend validation functions
def validate_email_frontend(email: str) -> bool:
    """Validate email format on frontend."""
    if not email or not isinstance(email, str):
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if len(email) > 254:
        return False
    
    if '..' in email or email.startswith('.') or email.endswith('.'):
        return False
    
    return bool(re.match(email_pattern, email))


def get_password_strength_frontend(password: str) -> Dict[str, Any]:
    """Calculate password strength on frontend."""
    if not password:
        return {"score": 0, "level": "Very Weak", "feedback": []}
    
    score = 0
    feedback = []
    
    # Length scoring
    length = len(password)
    if length >= 8:
        score += 25
    elif length >= 6:
        score += 15
        feedback.append("Consider using a longer password")
    else:
        feedback.append("Password is too short")
    
    # Character variety scoring
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))
    
    char_types = sum([has_lower, has_upper, has_digit, has_special])
    score += char_types * 15
    
    # Bonus for good practices
    if length >= 12:
        score += 10
        feedback.append("Great length!")
    
    if char_types >= 3:
        feedback.append("Good character variety!")
    
    # Penalties
    if re.search(r'(.)\1{2,}', password):
        score -= 10
        feedback.append("Avoid repeating characters")
    
    # Determine strength level
    if score >= 80:
        level = "Very Strong"
    elif score >= 60:
        level = "Strong"
    elif score >= 40:
        level = "Moderate"
    elif score >= 20:
        level = "Weak"
    else:
        level = "Very Weak"
    
    return {
        "score": max(0, min(100, score)),
        "level": level,
        "feedback": feedback
    }


def get_strength_color(level: str) -> str:
    """Get color for password strength level."""
    colors = {
        "Very Weak": "#ff4444",
        "Weak": "#ff8800",
        "Moderate": "#ffaa00",
        "Strong": "#88cc00",
        "Very Strong": "#00cc44"
    }
    return colors.get(level, "#cccccc")


# OAuth functions
def get_oauth_providers() -> List[Dict[str, Any]]:
    """Get available OAuth providers from backend."""
    try:
        response = requests.get(f"{API_URL}/api/oauth/providers")
        if response.status_code == 200:
            return response.json().get("providers", [])
        return []
    except Exception as e:
        print(f"Error getting OAuth providers: {e}")
        return []


def oauth_login(provider: str):
    """Initiate OAuth login flow."""
    try:
        # Get authorization URL from backend
        response = requests.get(f"{API_URL}/api/oauth/auth/{provider}")
        
        if response.status_code == 200:
            auth_data = response.json()
            auth_url = auth_data["authorization_url"]
            
            # Store provider info in session state for callback handling
            st.session_state.oauth_provider = provider
            st.session_state.oauth_redirect_uri = auth_data["redirect_uri"]
            
            # Use Streamlit's redirect functionality
            st.success(f"🔗 Redirecting to {provider.title()} for authentication...")
            st.info("💡 **Note:** You'll be redirected to complete the login process.")
            
            # Use JavaScript for immediate redirect
            st.markdown(f"""
            <meta http-equiv="refresh" content="0; url={auth_url}">
            <script>
                window.location.href = '{auth_url}';
            </script>
            """, unsafe_allow_html=True)
            
            # Also provide manual link as backup
            st.markdown(f"**[Click here if not redirected automatically]({auth_url})**")
            
        else:
            st.error(f"Failed to initiate {provider} login: {response.text}")
            
    except Exception as e:
        st.error(f"Error initiating OAuth login: {e}")


def handle_oauth_callback(provider: str, code: str):
    """Handle OAuth callback and login user."""
    try:
        # Exchange code for token
        response = requests.get(
            f"{API_URL}/api/oauth/callback/{provider}",
            params={"code": code}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Store token in session
            st.session_state.token = {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"]
            }
            
            # Clear OAuth session data
            if hasattr(st.session_state, "oauth_provider"):
                del st.session_state.oauth_provider
            if hasattr(st.session_state, "oauth_redirect_uri"):
                del st.session_state.oauth_redirect_uri
            
            st.success(f"✅ Successfully logged in with {provider.title()}!")
            st.rerun()
            
        else:
            st.error(f"OAuth login failed: {response.text}")
            
    except Exception as e:
        st.error(f"Error handling OAuth callback: {e}")




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


def delete_course(token: str, course_id: int) -> bool:
    """
    Delete a course.
    
    Args:
        token: Authentication token.
        course_id: ID of the course to delete.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        response = requests.delete(
            f"{API_URL}/api/courses/{course_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error deleting course: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error deleting course: {e}")
        return False


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


def delete_document(token: str, document_id: int) -> bool:
    """
    Delete a processed document and all its data.
    
    Args:
        token: Authentication token.
        document_id: Document ID to delete.
        
    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    try:
        response = requests.delete(
            f"{API_URL}/api/documents/{document_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"Failed to delete document: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error deleting document: {e}")
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
    # Check for OAuth callback parameters in URL
    query_params = st.query_params
    
    if "code" in query_params and hasattr(st.session_state, "oauth_provider"):
        # Handle OAuth callback
        code = query_params["code"]
        provider = st.session_state.oauth_provider
        
        st.info(f"Processing {provider.title()} login...")
        handle_oauth_callback(provider, code)
        return
    
    
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
    # Add some top spacing
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    
    # Create a centered container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Main title
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #2E86AB; margin-bottom: 10px; font-size: 32px;">
                📚 StudyMate AI
            </h1>
            <p style="color: #666; font-size: 16px; margin: 0;">
                Your AI-Powered Learning Assistant
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login/Register toggle
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #333; font-size: 24px; margin: 0;">
                Log in or sign up
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Create tabs for login and registration with custom styling
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        
        # Email input with validation
        email = st.text_input("Email", key="login_email", placeholder="Enter your email address")
        
        # Show email validation feedback
        if email and not validate_email_frontend(email):
            st.error("❌ Please enter a valid email address")
        
        # Password input
        password = st.text_input("Password", type="password", key="login_password", 
                               placeholder="Enter your password")
        
        # Login button
        if st.button("Login", type="primary"):
            # Client-side validation
            validation_errors = []
            
            if not email:
                validation_errors.append("Email is required")
            elif not validate_email_frontend(email):
                validation_errors.append("Please enter a valid email address")
            
            if not password:
                validation_errors.append("Password is required")
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            else:
                # Attempt login
                with st.spinner("Logging in..."):
                    token = login(email, password)
                    if token:
                        st.session_state.token = token
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password. Please check your credentials and try again.")
        
        # OAuth login options with modern styling
        st.markdown("<div style='text-align: center; margin: 20px 0;'><span style='color: #666; font-size: 14px;'>OR</span></div>", unsafe_allow_html=True)
        
        # Get available OAuth providers
        oauth_providers = get_oauth_providers()
        
        if oauth_providers:
            for provider in oauth_providers:
                if provider['name'] == 'google':
                    if st.button("🔍 Continue with Google", key="oauth_google", use_container_width=True, type="secondary"):
                        oauth_login('google')
                elif provider['name'] == 'github':
                    if st.button("🐙 Continue with GitHub", key="oauth_github", use_container_width=True, type="secondary"):
                        oauth_login('github')
        else:
            # Show OAuth buttons as enabled for demo purposes
            if st.button("🔍 Continue with Google", key="demo_google", use_container_width=True, type="secondary"):
                st.info("🔍 Google OAuth not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file.")
            
            if st.button("🐙 Continue with GitHub", key="demo_github", use_container_width=True, type="secondary"):
                st.info("🐙 GitHub OAuth not configured. Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to your .env file.")
            
            st.caption("💡 Add OAuth credentials to .env file to enable social login")
    
    with tab2:
        st.header("Register")
        
        # Email input with validation
        email = st.text_input("Email", key="register_email", placeholder="Enter your email address")
        
        # Email validation feedback
        if email:
            if validate_email_frontend(email):
                st.success("✅ Valid email format")
            else:
                st.error("❌ Please enter a valid email address")
        
        # Password input with real-time validation
        password = st.text_input("Password", type="password", key="register_password", 
                                placeholder="Enter a strong password")
        
        # Password strength indicator
        if password:
            strength_info = get_password_strength_frontend(password)
            
            # Display strength meter
            col1, col2 = st.columns([3, 1])
            with col1:
                progress_color = get_strength_color(strength_info["level"])
                st.progress(strength_info["score"] / 100)
            with col2:
                st.write(f"**{strength_info['level']}**")
            
            # Show requirements
            st.write("**Password Requirements:**")
            requirements = [
                ("At least 8 characters", len(password) >= 8),
                ("Contains uppercase letter", any(c.isupper() for c in password)),
                ("Contains lowercase letter", any(c.islower() for c in password)),
                ("Contains digit", any(c.isdigit() for c in password)),
                ("Contains special character", any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password))
            ]
            
            for req, met in requirements:
                if met:
                    st.success(f"✅ {req}")
                else:
                    st.error(f"❌ {req}")
            
            # Show feedback
            if strength_info["feedback"]:
                st.info("💡 " + "; ".join(strength_info["feedback"]))
        
        # Confirm password
        confirm_password = st.text_input("Confirm Password", type="password", 
                                       key="register_confirm_password",
                                       placeholder="Re-enter your password")
        
        # Password match validation
        if password and confirm_password:
            if password == confirm_password:
                st.success("✅ Passwords match")
            else:
                st.error("❌ Passwords do not match")
        
        # Register button
        if st.button("Register", type="primary"):
            # Client-side validation
            validation_errors = []
            
            if not email:
                validation_errors.append("Email is required")
            elif not validate_email_frontend(email):
                validation_errors.append("Please enter a valid email address")
            
            if not password:
                validation_errors.append("Password is required")
            elif len(password) < 8:
                validation_errors.append("Password must be at least 8 characters long")
            
            if not confirm_password:
                validation_errors.append("Please confirm your password")
            elif password != confirm_password:
                validation_errors.append("Passwords do not match")
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            else:
                # Attempt registration
                with st.spinner("Creating your account..."):
                    if register(email, password):
                        st.success("🎉 Registration successful! Please login with your new account.")
                        st.info("💡 You can now switch to the Login tab to access your account.")
                        # Note: We can't clear form fields after widgets are created in Streamlit
                        # The form will be cleared when the user refreshes or navigates away
                    else:
                        st.error("Registration failed. Please try again.")
        
        # OAuth registration options with modern styling
        st.markdown("<div style='text-align: center; margin: 20px 0;'><span style='color: #666; font-size: 14px;'>OR</span></div>", unsafe_allow_html=True)
        
        # Get available OAuth providers
        oauth_providers = get_oauth_providers()
        
        if oauth_providers:
            for provider in oauth_providers:
                if provider['name'] == 'google':
                    if st.button("🔍 Continue with Google", key="oauth_register_google", use_container_width=True, type="secondary"):
                        oauth_login('google')
                elif provider['name'] == 'github':
                    if st.button("🐙 Continue with GitHub", key="oauth_register_github", use_container_width=True, type="secondary"):
                        oauth_login('github')
        else:
            # Show disabled OAuth buttons with proper styling
            st.markdown("""
            <div class="oauth-button">
                <span class="oauth-icon">🔍</span>
                Continue with Google
            </div>
            <div class="oauth-button">
                <span class="oauth-icon">🐙</span>
                Continue with GitHub
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("💡 Add OAuth credentials to .env file to enable social login")


def show_main_app(user_info):
    """Show the main application interface."""
    # Enhanced sidebar header
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 10px;">
        <h2 style="color: #2E86AB; margin: 0;">
            📚 StudyMate AI
        </h2>
        <p style="color: #666; font-size: 12px; margin: 5px 0;">
            AI Learning Assistant
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    page = st.sidebar.radio(
        "Select Page",
        ["Courses", "Quiz", "Chat History"]
    )
    
    st.sidebar.divider()
    
    # Course management in sidebar
    st.sidebar.subheader("Select Course")
    courses = get_courses(st.session_state.token["access_token"])
    
    if courses:
        course_names = [course["title"] for course in courses]
        course_ids = [course["id"] for course in courses]
        
        selected_course_index = st.sidebar.selectbox(
            "Select Course",
            range(len(courses)),
            format_func=lambda i: course_names[i],
        )
        
        st.session_state.selected_course_id = course_ids[selected_course_index]
        st.session_state.selected_course_name = course_names[selected_course_index]
        
        # Add delete course button for selected course
        if st.sidebar.button("🗑️ Delete Selected Course", type="secondary"):
            # Use session state to track deletion confirmation
            if "confirm_delete_course" not in st.session_state:
                st.session_state.confirm_delete_course = True
                st.sidebar.warning(f"⚠️ Are you sure you want to delete '{st.session_state.selected_course_name}'?")
                st.sidebar.write("This action cannot be undone!")
            else:
                # User clicked delete again, proceed with deletion
                if delete_course(st.session_state.token["access_token"], st.session_state.selected_course_id):
                    st.success(f"Course '{st.session_state.selected_course_name}' deleted successfully!")
                    # Clear the confirmation state
                    if "confirm_delete_course" in st.session_state:
                        del st.session_state.confirm_delete_course
                    # Clear selected course
                    if "selected_course_id" in st.session_state:
                        del st.session_state.selected_course_id
                    if "selected_course_name" in st.session_state:
                        del st.session_state.selected_course_name
                    st.rerun()
                else:
                    # Clear the confirmation state on error
                    if "confirm_delete_course" in st.session_state:
                        del st.session_state.confirm_delete_course
        
        # Show confirmation dialog if needed
        if "confirm_delete_course" in st.session_state and st.session_state.confirm_delete_course:
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("✅ Confirm", key="confirm_delete_yes"):
                    if delete_course(st.session_state.token["access_token"], st.session_state.selected_course_id):
                        st.success(f"Course '{st.session_state.selected_course_name}' deleted successfully!")
                        # Clear states
                        del st.session_state.confirm_delete_course
                        if "selected_course_id" in st.session_state:
                            del st.session_state.selected_course_id
                        if "selected_course_name" in st.session_state:
                            del st.session_state.selected_course_name
                        st.rerun()
                    else:
                        del st.session_state.confirm_delete_course
            with col2:
                if st.button("❌ Cancel", key="confirm_delete_no"):
                    del st.session_state.confirm_delete_course
                    st.rerun()
    else:
        st.sidebar.info("No courses available. Create one below.")
    
    # Create new course in sidebar
    st.sidebar.divider()
    st.sidebar.subheader("Create New Course")
    new_course_title = st.sidebar.text_input("Course Title")
    new_course_description = st.sidebar.text_area("Course Description")
    
    if st.sidebar.button("Create Course"):
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
    
    # Chat History sidebar (only show when on Chat History page)
    if page == "Chat History":
        st.sidebar.divider()
        st.sidebar.subheader("Chat Sessions")
        # Get chat sessions
        chat_sessions = get_chat_sessions(st.session_state.token["access_token"])
        
        # Chat session selection
        if chat_sessions:
            chat_session_titles = [session["title"] for session in chat_sessions]
            chat_session_ids = [session["id"] for session in chat_sessions]
            
            selected_session_index = st.sidebar.selectbox(
                "Select Chat Session",
                range(len(chat_sessions)),
                format_func=lambda i: chat_session_titles[i],
            )
            
            st.session_state.selected_chat_session_id = chat_session_ids[selected_session_index]
        else:
            st.sidebar.info("No chat sessions found. Start a new conversation in the Courses page.")
    
    # Main content area
    st.write(f"Welcome, {user_info['email']}")
        
    if st.button("Logout"):
        st.session_state.pop("token", None)
        st.rerun()
    
    # Main content
    if page == "Courses":
        show_courses_page()
    elif page == "Quiz":
        show_quiz_page()
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
                    else:
                        # Show delete button for processed documents
                        if st.button("🗑️ Delete", key=f"delete_{document['id']}"):
                            if delete_document(st.session_state.token["access_token"], document["id"]):
                                st.success(f"Document '{document['original_filename']}' deleted successfully")
                                st.rerun()
                            else:
                                st.error("Failed to delete document")
                        
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
                                page_info = f", Page {citation['page_number']}" if citation.get('page_number') else ""
                                doc_name = citation.get('document_name', f"Document {citation['document_id']}")
                                with st.expander(f"📄 {doc_name}{page_info}"):
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
                            st.write("**📚 Sources:**")
                            for i, citation in enumerate(answer["citations"], 1):
                                page_info = f", Page {citation['page_number']}" if citation['page_number'] else ""
                                
                                # Try to get document name from the citation data, fallback to document ID
                                doc_name = citation.get('document_name', f"Document {citation['document_id']}")
                                print(f"🔍 Frontend citation: {citation}")
                                print(f"🔍 Frontend doc_name: {doc_name}")
                                
                                with st.expander(f"📄 {doc_name}{page_info}"):
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
                                page_info = f", Page {citation['page_number']}" if citation.get('page_number') else ""
                                doc_name = citation.get('document_name', f"Document {citation['document_id']}")
                                with st.expander(f"📄 {doc_name}{page_info}"):
                                    st.write(citation["quote"])
        else:
            st.info("No messages found for this chat session.")
    else:
        st.info("Please select a chat session from the sidebar.")


def show_quiz_page():
    """Show the quiz generation page."""
    st.title("📝 Quiz Generator")
    st.write("Generate quizzes based on your uploaded documents!")
    
    if not hasattr(st.session_state, "selected_course_id"):
        st.info("Please select a course from the sidebar first.")
        return
    
    # Show selected course name instead of ID
    course_name = getattr(st.session_state, 'selected_course_name', 'Unknown Course')
    st.info(f"Selected course: {course_name}")
    
    # Get documents for quiz generation
    try:
        response = requests.get(
            f"{API_URL}/api/quiz/documents/{st.session_state.selected_course_id}",
            headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
        )
        
        if response.status_code == 200:
            documents = response.json()
            st.success(f"Found {len(documents)} documents")  # Debug info
            
            if not documents:
                st.info("No processed documents available for quiz generation. Please upload and process documents first.")
                return
            
            # Document selection
            st.subheader("📄 Select Document")
            doc_options = {doc["id"]: f"{doc['filename']} ({doc['page_count']} pages)" for doc in documents}
            selected_doc_id = st.selectbox(
                "Choose a document to generate quiz from:",
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options[x]
            )
            
            # Quiz configuration
            st.subheader("⚙️ Quiz Settings")
            col1, col2 = st.columns(2)
            
            with col1:
                num_questions = st.slider("Number of questions:", 5, 20, 10)
            
            with col2:
                question_types = st.multiselect(
                    "Question types:",
                    ["mcq", "true_false"],
                    default=["mcq", "true_false"],
                    format_func=lambda x: "Multiple Choice" if x == "mcq" else "True/False"
                )
            
            if not question_types:
                st.error("Please select at least one question type.")
                return
            
            # Generate quiz button
            if st.button("🎯 Generate Quiz", type="primary"):
                with st.spinner("Generating quiz... This may take a moment."):
                    quiz_response = requests.post(
                        f"{API_URL}/api/quiz/generate",
                        headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"},
                        json={
                            "document_id": selected_doc_id,
                            "num_questions": num_questions,
                            "question_types": question_types
                        }
                    )
                    
                    if quiz_response.status_code == 200:
                        quiz_data = quiz_response.json()
                        st.session_state.current_quiz = quiz_data
                        st.session_state.quiz_answers = {}
                        st.session_state.show_answers = False
                        st.success(f"Quiz generated successfully! {quiz_data['total_questions']} questions created.")
                        st.rerun()
                    else:
                        st.error(f"Failed to generate quiz: {quiz_response.text}")
            
            # Display quiz if generated
            if hasattr(st.session_state, "current_quiz") and st.session_state.current_quiz:
                display_quiz()
                
        else:
            st.error(f"Failed to load documents for quiz generation. Status: {response.status_code}")
            st.error(f"Response: {response.text}")
            
    except Exception as e:
        st.error(f"Error loading quiz page: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")


def display_quiz():
    """Display the generated quiz."""
    quiz = st.session_state.current_quiz
    
    st.divider()
    st.subheader(f"📝 Quiz: {quiz['document_name']}")
    st.write(f"**Total Questions:** {quiz['total_questions']}")
    
    # Initialize answers if not exists
    if not hasattr(st.session_state, "quiz_answers"):
        st.session_state.quiz_answers = {}
    
    # Display questions
    for question in quiz["questions"]:
        st.write(f"**Question {question['id']}:** {question['question']}")
        
        if question["type"] == "mcq":
            # Multiple choice question
            answer_key = f"mcq_{question['id']}_{hash(str(question['question']))}"  # Unique key
            selected_option = st.radio(
                "Select your answer:",
                options=question["options"],
                key=answer_key,
                index=None
            )
            
            if selected_option:
                # Extract just the letter (A, B, C, D)
                st.session_state.quiz_answers[question['id']] = selected_option[0]
        
        elif question["type"] == "true_false":
            # True/False question
            answer_key = f"tf_{question['id']}_{hash(str(question['question']))}"  # Unique key
            selected_option = st.radio(
                "Select your answer:",
                options=["True", "False"],
                key=answer_key,
                index=None
            )
            
            if selected_option:
                st.session_state.quiz_answers[question['id']] = selected_option
        
        # Show answer if revealed
        if hasattr(st.session_state, "show_answers") and st.session_state.show_answers:
            user_answer = st.session_state.quiz_answers.get(question['id'], "Not answered")
            correct_answer = question['correct_answer']
            
            if user_answer == correct_answer:
                st.success(f"✅ Correct! Answer: {correct_answer}")
            else:
                st.error(f"❌ Incorrect. Your answer: {user_answer}, Correct answer: {correct_answer}")
            
            st.info(f"**Explanation:** {question['explanation']}")
        
        st.divider()
    
    # Quiz controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Show Answers"):
            st.session_state.show_answers = True
            st.rerun()
    
    with col2:
        if st.button("📊 Calculate Score"):
            if st.session_state.quiz_answers:
                correct_count = 0
                total_questions = len(quiz["questions"])
                
                for question in quiz["questions"]:
                    user_answer = st.session_state.quiz_answers.get(question['id'])
                    if user_answer == question['correct_answer']:
                        correct_count += 1
                
                score_percentage = (correct_count / total_questions) * 100
                st.success(f"Your Score: {correct_count}/{total_questions} ({score_percentage:.1f}%)")
            else:
                st.warning("Please answer some questions first!")
    
    with col3:
        if st.button("🔄 New Quiz"):
            if hasattr(st.session_state, "current_quiz"):
                del st.session_state.current_quiz
            if hasattr(st.session_state, "quiz_answers"):
                del st.session_state.quiz_answers
            if hasattr(st.session_state, "show_answers"):
                del st.session_state.show_answers
            st.rerun()


if __name__ == "__main__":
    main()
