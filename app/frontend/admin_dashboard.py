import streamlit as st
import requests
import pandas as pd
import json
import os
import time
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns

from app.utils.evaluation import RAGEvaluator

# Set page configuration
st.set_page_config(
    page_title="Course Notes Q&A - Admin Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API URL
API_URL = "http://localhost:8000/api"


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
        response = requests.post(
            f"{API_URL}/auth/token",
            data={"username": email, "password": password},
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        st.error(f"Error during login: {e}")
        return None


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
            f"{API_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error getting user info: {e}")
        return None


# Admin functions
def get_stats(token: str) -> Dict[str, Any]:
    """
    Get system statistics.
    
    Args:
        token: Authentication token.
        
    Returns:
        Dict[str, Any]: System statistics.
    """
    try:
        response = requests.get(
            f"{API_URL}/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error getting stats: {response.json().get('detail', 'Unknown error')}")
            return {}
    except Exception as e:
        st.error(f"Error getting stats: {e}")
        return {}


def get_users(token: str) -> List[Dict[str, Any]]:
    """
    Get all users.
    
    Args:
        token: Authentication token.
        
    Returns:
        List[Dict[str, Any]]: List of users.
    """
    try:
        response = requests.get(
            f"{API_URL}/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error getting users: {response.json().get('detail', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Error getting users: {e}")
        return []


def reindex_document(token: str, document_id: int) -> bool:
    """
    Reindex a document.
    
    Args:
        token: Authentication token.
        document_id: Document ID.
        
    Returns:
        bool: True if reindexing was successful, False otherwise.
    """
    try:
        response = requests.post(
            f"{API_URL}/admin/reindex/{document_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error reindexing document: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error reindexing document: {e}")
        return False


def toggle_user_status(token: str, user_id: int) -> bool:
    """
    Toggle user active status.
    
    Args:
        token: Authentication token.
        user_id: User ID.
        
    Returns:
        bool: True if toggling was successful, False otherwise.
    """
    try:
        response = requests.post(
            f"{API_URL}/admin/toggle-user-status/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error toggling user status: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error toggling user status: {e}")
        return False


# Evaluation functions
def run_evaluation(token: str, eval_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Run evaluation on the RAG pipeline.
    
    Args:
        token: Authentication token.
        eval_data: Evaluation data.
        
    Returns:
        Dict[str, float]: Evaluation results.
    """
    evaluator = RAGEvaluator()
    return evaluator.evaluate_from_qa_pairs(eval_data)


def generate_evaluation_report(results: Dict[str, float]) -> str:
    """
    Generate evaluation report.
    
    Args:
        results: Evaluation results.
        
    Returns:
        str: Evaluation report.
    """
    evaluator = RAGEvaluator()
    return evaluator.generate_evaluation_report(results)


# Main app
def main():
    # Check if user is logged in
    if "token" not in st.session_state:
        show_login_page()
    else:
        # Check if token is valid
        user_info = get_user_info(st.session_state.token["access_token"])
        if user_info and user_info.get("is_admin", False):
            show_admin_dashboard(user_info)
        elif user_info:
            st.error("You do not have admin privileges.")
            if st.button("Logout"):
                st.session_state.pop("token", None)
                st.experimental_rerun()
        else:
            # Token is invalid, show login page
            st.session_state.pop("token", None)
            show_login_page()


def show_login_page():
    """Show the login page."""
    st.title("Course Notes Q&A - Admin Dashboard")
    
    st.header("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        if email and password:
            token = login(email, password)
            if token:
                st.session_state.token = token
                st.experimental_rerun()
            else:
                st.error("Invalid email or password")
        else:
            st.error("Please enter email and password")


def show_admin_dashboard(user_info):
    """
    Show the admin dashboard.
    
    Args:
        user_info: User information.
    """
    # Sidebar
    with st.sidebar:
        st.title("Admin Dashboard")
        st.write(f"Welcome, {user_info['email']}")
        
        if st.button("Logout"):
            st.session_state.pop("token", None)
            st.experimental_rerun()
        
        st.divider()
        
        # Navigation
        page = st.radio("Navigation", ["System Stats", "User Management", "Evaluation", "Monitoring"])
    
    # Main content
    if page == "System Stats":
        show_system_stats_page()
    elif page == "User Management":
        show_user_management_page()
    elif page == "Evaluation":
        show_evaluation_page()
    elif page == "Monitoring":
        show_monitoring_page()


def show_system_stats_page():
    """Show the system stats page."""
    st.title("System Statistics")
    
    # Get stats
    stats = get_stats(st.session_state.token["access_token"])
    
    if stats:
        # Database stats
        st.header("Database Statistics")
        db_stats = stats.get("database_stats", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Users", db_stats.get("user_count", 0))
        with col2:
            st.metric("Courses", db_stats.get("course_count", 0))
        with col3:
            st.metric("Documents", db_stats.get("document_count", 0))
        
        # Vector store stats
        st.header("Vector Store Statistics")
        vector_stats = stats.get("vector_store_stats", {})
        
        if "namespaces" in vector_stats:
            namespaces = vector_stats["namespaces"]
            total_vectors = sum(ns.get("vector_count", 0) for ns in namespaces.values())
            st.metric("Total Vectors", total_vectors)
            
            # Display namespace stats
            if namespaces:
                st.subheader("Namespaces")
                namespace_data = []
                
                for ns_name, ns_stats in namespaces.items():
                    namespace_data.append({
                        "Namespace": ns_name,
                        "Vector Count": ns_stats.get("vector_count", 0)
                    })
                
                st.table(pd.DataFrame(namespace_data))
        else:
            st.info("No vector store statistics available.")
    else:
        st.info("No statistics available.")


def show_user_management_page():
    """Show the user management page."""
    st.title("User Management")
    
    # Get users
    users = get_users(st.session_state.token["access_token"])
    
    if users:
        # Display users
        st.header("Users")
        
        for user in users:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{user['email']}**")
            with col2:
                st.write(f"Admin: {'Yes' if user['is_admin'] else 'No'}")
            with col3:
                st.write(f"Status: {'Active' if user['is_active'] else 'Inactive'}")
            with col4:
                if st.button(f"{'Deactivate' if user['is_active'] else 'Activate'} #{user['id']}"):
                    if toggle_user_status(st.session_state.token["access_token"], user["id"]):
                        st.success(f"User status toggled successfully!")
                        st.experimental_rerun()
    else:
        st.info("No users found.")


def show_evaluation_page():
    """Show the evaluation page."""
    st.title("RAG Evaluation")
    
    # Create tabs for different evaluation methods
    tab1, tab2 = st.tabs(["Manual Evaluation", "Automated Evaluation"])
    
    with tab1:
        st.header("Manual Evaluation")
        
        # Load or create evaluation data
        if "eval_data" not in st.session_state:
            st.session_state.eval_data = []
        
        # Add new evaluation item
        st.subheader("Add Evaluation Item")
        
        question = st.text_input("Question")
        answer = st.text_area("Answer")
        contexts = st.text_area("Contexts (one per line)")
        ground_truth = st.text_area("Ground Truth (optional)")
        
        if st.button("Add Item"):
            if question and answer and contexts:
                context_list = [ctx.strip() for ctx in contexts.split("\n") if ctx.strip()]
                
                eval_item = {
                    "question": question,
                    "answer": answer,
                    "contexts": context_list,
                }
                
                if ground_truth:
                    eval_item["ground_truth"] = ground_truth
                
                st.session_state.eval_data.append(eval_item)
                st.success("Evaluation item added!")
        
        # Display evaluation data
        if st.session_state.eval_data:
            st.subheader("Evaluation Data")
            
            for i, item in enumerate(st.session_state.eval_data):
                with st.expander(f"Item {i+1}: {item['question'][:50]}..."):
                    st.write(f"**Question:** {item['question']}")
                    st.write(f"**Answer:** {item['answer']}")
                    st.write("**Contexts:**")
                    for ctx in item['contexts']:
                        st.write(f"- {ctx}")
                    if "ground_truth" in item:
                        st.write(f"**Ground Truth:** {item['ground_truth']}")
            
            # Run evaluation
            if st.button("Run Evaluation"):
                with st.spinner("Running evaluation..."):
                    results = run_evaluation(st.session_state.token["access_token"], st.session_state.eval_data)
                    
                    if results:
                        st.session_state.eval_results = results
                        st.success("Evaluation completed!")
                    else:
                        st.error("Evaluation failed.")
            
            # Clear evaluation data
            if st.button("Clear Evaluation Data"):
                st.session_state.eval_data = []
                st.success("Evaluation data cleared!")
        
        # Display evaluation results
        if "eval_results" in st.session_state:
            st.subheader("Evaluation Results")
            
            # Display metrics
            metrics_df = pd.DataFrame({
                "Metric": list(st.session_state.eval_results.keys()),
                "Score": list(st.session_state.eval_results.values())
            })
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.table(metrics_df)
            
            with col2:
                # Create bar chart
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x="Score", y="Metric", data=metrics_df, ax=ax)
                ax.set_xlim(0, 1)
                ax.set_title("RAG Evaluation Metrics")
                st.pyplot(fig)
            
            # Display report
            report = generate_evaluation_report(st.session_state.eval_results)
            st.markdown(report)
    
    with tab2:
        st.header("Automated Evaluation")
        st.info("Automated evaluation is not yet implemented.")


def show_monitoring_page():
    """Show the monitoring page."""
    st.title("System Monitoring")
    
    # Create tabs for different monitoring aspects
    tab1, tab2, tab3 = st.tabs(["Performance", "Usage", "Errors"])
    
    with tab1:
        st.header("Performance Monitoring")
        
        # Create sample performance data
        dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
        latency_data = pd.DataFrame({
            "Date": dates,
            "Latency (ms)": [100 + i * 5 + (i % 5) * 20 for i in range(30)]
        })
        
        # Plot latency over time
        st.subheader("Latency Over Time")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(x="Date", y="Latency (ms)", data=latency_data, ax=ax)
        ax.set_title("API Latency Over Time")
        st.pyplot(fig)
        
        # Create sample throughput data
        throughput_data = pd.DataFrame({
            "Date": dates,
            "Requests": [50 + i * 2 + (i % 7) * 10 for i in range(30)]
        })
        
        # Plot throughput over time
        st.subheader("Throughput Over Time")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(x="Date", y="Requests", data=throughput_data, ax=ax)
        ax.set_title("API Requests Over Time")
        st.pyplot(fig)
    
    with tab2:
        st.header("Usage Monitoring")
        
        # Create sample usage data
        usage_data = pd.DataFrame({
            "Resource": ["Documents", "Questions", "Vector DB Queries", "LLM Calls"],
            "Count": [120, 500, 1500, 600]
        })
        
        # Plot usage
        st.subheader("Resource Usage")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x="Count", y="Resource", data=usage_data, ax=ax)
        ax.set_title("Resource Usage")
        st.pyplot(fig)
        
        # Create sample user activity data
        user_activity = pd.DataFrame({
            "Date": dates,
            "Active Users": [10 + i + (i % 5) * 2 for i in range(30)]
        })
        
        # Plot user activity
        st.subheader("User Activity")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(x="Date", y="Active Users", data=user_activity, ax=ax)
        ax.set_title("Daily Active Users")
        st.pyplot(fig)
    
    with tab3:
        st.header("Error Monitoring")
        
        # Create sample error data
        error_data = pd.DataFrame({
            "Error Type": ["API Error", "Database Error", "Vector DB Error", "LLM Error", "File Processing Error"],
            "Count": [5, 3, 8, 2, 4]
        })
        
        # Plot errors
        st.subheader("Error Distribution")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x="Count", y="Error Type", data=error_data, ax=ax)
        ax.set_title("Error Distribution")
        st.pyplot(fig)
        
        # Create sample error rate data
        error_rate_data = pd.DataFrame({
            "Date": dates,
            "Error Rate (%)": [0.5 + (i % 10) * 0.2 for i in range(30)]
        })
        
        # Plot error rate
        st.subheader("Error Rate Over Time")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(x="Date", y="Error Rate (%)", data=error_rate_data, ax=ax)
        ax.set_title("Error Rate Over Time")
        st.pyplot(fig)


if __name__ == "__main__":
    main()
