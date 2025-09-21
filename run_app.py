#!/usr/bin/env python3
import subprocess
import time
import os
import sys
import signal

def start_backend():
    """Start the FastAPI backend"""
    print("\n[INFO] Starting FastAPI backend server...")
    cmd = [
        "python", "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0",  # Bind to all interfaces
        "--port", "8000"
    ]
    return subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

def start_frontend():
    """Start the Streamlit frontend"""
    print("\n[INFO] Starting Streamlit frontend...")
    cmd = [
        "python", "-m", "streamlit", 
        "run", "app/frontend/app.py",
        "--server.address", "0.0.0.0",  # Bind to all interfaces
        "--server.port", "8501"
    ]
    return subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        print("="*70)
        print("              🤖 STUDYMATE AI LAUNCHER")
        print("="*70)
        
        # Start backend
        backend_process = start_backend()
        print(f"[SUCCESS] Backend started with PID {backend_process.pid}")
        
        # Wait for backend to start
        print("\n[INFO] Waiting for backend to initialize (5 seconds)...")
        time.sleep(5)
        
        # Start frontend
        frontend_process = start_frontend()
        print(f"[SUCCESS] Frontend started with PID {frontend_process.pid}")
        
        # Display access information
        print("\n" + "="*70)
        print("APPLICATION RUNNING - ACCESS INFORMATION:")
        print("="*70)
        print("Backend API:       http://localhost:8000")
        print("API Documentation: http://localhost:8000/docs")
        print("Frontend UI:       http://localhost:8501")
        print("="*70)
        print("\nPress Ctrl+C to stop all services\n")
        
        # Keep the script running
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopping services...")
    
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
    
    finally:
        # Clean up processes
        if 'backend_process' in locals():
            print("[INFO] Stopping backend...")
            backend_process.terminate()
        
        if 'frontend_process' in locals():
            print("[INFO] Stopping frontend...")
            frontend_process.terminate()
        
        print("[SUCCESS] All services stopped")

if __name__ == "__main__":
    main()
