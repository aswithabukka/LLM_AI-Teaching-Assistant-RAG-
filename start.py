import subprocess
import time
import os
import signal
import sys

# Configuration
BACKEND_HOST = "localhost"
BACKEND_PORT = 8000
FRONTEND_PORT = 8501

def start_backend():
    """Start the FastAPI backend server"""
    print("Starting FastAPI backend server...")
    cmd = [
        "python", "-m", "uvicorn", "app.main:app",
        f"--host={BACKEND_HOST}", f"--port={BACKEND_PORT}"
    ]
    process = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    print(f"Backend server started with PID: {process.pid}")
    return process

def start_frontend():
    """Start the Streamlit frontend server"""
    print("Starting Streamlit frontend server...")
    cmd = [
        "python", "-m", "streamlit", "run", "app/frontend/app.py"
    ]
    process = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    print(f"Frontend server started with PID: {process.pid}")
    return process

def main():
    """Main function to start both servers"""
    try:
        # Start backend
        backend_process = start_backend()
        
        # Give the backend some time to start up
        print("Waiting for backend to initialize...")
        time.sleep(5)
        
        # Start frontend
        frontend_process = start_frontend()
        
        # Display server information
        print("\n" + "=" * 50)
        print("Course Notes Q&A Application")
        print("=" * 50)
        print(f"Backend API: http://{BACKEND_HOST}:{BACKEND_PORT}")
        print(f"API Documentation: http://{BACKEND_HOST}:{BACKEND_PORT}/docs")
        print(f"Frontend UI: http://{BACKEND_HOST}:{FRONTEND_PORT}")
        print("=" * 50)
        print("Press Ctrl+C to stop all services")
        
        # Wait for keyboard interrupt
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping services...")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Clean up
        if 'backend_process' in locals():
            backend_process.terminate()
        if 'frontend_process' in locals():
            frontend_process.terminate()
        print("Services stopped")

if __name__ == "__main__":
    main()
