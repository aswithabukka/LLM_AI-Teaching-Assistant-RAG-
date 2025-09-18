#!/usr/bin/env python3
import subprocess
import time
import os
import sys
import signal

def run_command(cmd, cwd=None):
    """Run a command and return the process"""
    if cwd is None:
        cwd = os.getcwd()
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=cwd)

def main():
    try:
        # Get project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Activate virtual environment
        venv_path = os.path.join(project_dir, "venv", "bin", "activate")
        os.environ["PATH"] = f"{os.path.join(project_dir, 'venv', 'bin')}:{os.environ['PATH']}"
        
        # Start backend
        print("\n=== Starting FastAPI Backend ===")
        backend_cmd = [
            "python", "-m", "uvicorn", 
            "app.main:app", 
            "--host", "127.0.0.1",
            "--port", "25000"
        ]
        backend = run_command(backend_cmd, project_dir)
        print(f"Backend server started with PID: {backend.pid}")
        
        # Wait for backend to start
        print("Waiting for backend to initialize...")
        time.sleep(3)
        
        # Start Streamlit with very explicit configuration
        print("\n=== Starting Streamlit Frontend ===")
        frontend_cmd = [
            "python", "-m", "streamlit", "run", 
            "app/frontend/app.py",
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false", 
            "--server.address", "127.0.0.1",
            "--browser.serverAddress", "127.0.0.1",
            "--server.port", "25001"
        ]
        frontend = run_command(frontend_cmd, project_dir)
        print(f"Frontend server started with PID: {frontend.pid}")
        
        # Display access information
        print("\n" + "="*50)
        print("APPLICATION IS RUNNING")
        print("="*50)
        print("Backend API:       http://127.0.0.1:25000")
        print("API Documentation: http://127.0.0.1:25000/docs")
        print("Frontend UI:       http://127.0.0.1:25001")
        print("="*50)
        
        print("\nPress Ctrl+C to stop all services")
        
        # Wait for processes
        while backend.poll() is None and frontend.poll() is None:
            time.sleep(1)
        
        if backend.poll() is not None:
            print(f"Backend terminated unexpectedly with code: {backend.returncode}")
        
        if frontend.poll() is not None:
            print(f"Frontend terminated unexpectedly with code: {frontend.returncode}")
    
    except KeyboardInterrupt:
        print("\nStopping services...")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Clean up
        if 'backend' in locals() and backend.poll() is None:
            print("Terminating backend...")
            backend.terminate()
        
        if 'frontend' in locals() and frontend.poll() is None:
            print("Terminating frontend...")
            frontend.terminate()
        
        print("Services stopped.")

if __name__ == "__main__":
    main()
