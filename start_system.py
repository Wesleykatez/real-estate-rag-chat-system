#!/usr/bin/env python3
"""
Complete System Startup Script for Real Estate RAG Chat System
Handles database initialization, dependency installation, and service startup
"""

import os
import sys
import subprocess
import time
import requests
import platform
from pathlib import Path

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color=Colors.OKGREEN):
    """Print colored message"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message):
    """Print section header"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f"{message}", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)

def print_step(step, message):
    """Print step message"""
    print_colored(f"\n[Step {step}] {message}", Colors.OKBLUE)

def print_success(message):
    """Print success message"""
    print_colored(f"✅ {message}", Colors.OKGREEN)

def print_warning(message):
    """Print warning message"""
    print_colored(f"⚠️  {message}", Colors.WARNING)

def print_error(message):
    """Print error message"""
    print_colored(f"❌ {message}", Colors.FAIL)

def run_command(command, cwd=None, shell=True):
    """Run a command and return success status"""
    try:
        print_colored(f"Running: {command}", Colors.OKCYAN)
        result = subprocess.run(
            command, 
            shell=shell, 
            cwd=cwd, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print_success("Command completed successfully")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print_error(f"Command failed with return code {result.returncode}")
            if result.stderr.strip():
                print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Error running command: {str(e)}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python version...")
    
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_error("Python 3.8+ is required")
        return False
    
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} is compatible")
    return True

def check_nodejs():
    """Check if Node.js is installed"""
    print_step(2, "Checking Node.js installation...")
    
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Node.js version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print_error("Node.js is not installed")
    print_colored("Please install Node.js from https://nodejs.org/", Colors.WARNING)
    return False

def check_postgresql():
    """Check if PostgreSQL is accessible"""
    print_step(3, "Checking PostgreSQL connection...")
    
    try:
        import psycopg2
        
        # Try to connect to PostgreSQL
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password123@localhost:5432/real_estate_db")
        
        # Extract connection details
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/')
        )
        conn.close()
        
        print_success("PostgreSQL connection successful")
        return True
        
    except ImportError:
        print_warning("psycopg2 not installed - will install with backend dependencies")
        return True  # We'll install it later
    except Exception as e:
        print_error(f"PostgreSQL connection failed: {str(e)}")
        print_colored("Please ensure PostgreSQL is running and the database exists", Colors.WARNING)
        return False

def setup_backend():
    """Set up backend dependencies and initialize database"""
    print_step(4, "Setting up backend environment...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print_error("Backend directory not found")
        return False
    
    # Install Python dependencies
    print_colored("Installing Python dependencies...", Colors.OKCYAN)
    if not run_command("pip install -r requirements.txt", cwd=backend_dir):
        print_error("Failed to install Python dependencies")
        return False
    
    # Initialize database
    print_colored("Initializing database...", Colors.OKCYAN)
    if not run_command("python init_database.py", cwd=backend_dir):
        print_error("Failed to initialize database")
        return False
    
    print_success("Backend setup completed")
    return True

def setup_frontend():
    """Set up frontend dependencies"""
    print_step(5, "Setting up frontend environment...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_error("Frontend directory not found")
        return False
    
    # Install Node.js dependencies
    print_colored("Installing Node.js dependencies...", Colors.OKCYAN)
    if not run_command("npm install", cwd=frontend_dir):
        print_error("Failed to install Node.js dependencies")
        return False
    
    print_success("Frontend setup completed")
    return True

def start_backend_service():
    """Start the backend service"""
    print_step(6, "Starting backend service...")
    
    backend_dir = Path("backend")
    
    # Start the backend server in a separate process
    try:
        print_colored("Starting FastAPI server on http://localhost:8001", Colors.OKCYAN)
        backend_process = subprocess.Popen(
            ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
            cwd=backend_dir
        )
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Check if the server is running
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                print_success("Backend service started successfully")
                return backend_process
            else:
                print_error("Backend service health check failed")
                backend_process.terminate()
                return None
        except requests.RequestException:
            print_error("Backend service is not responding")
            backend_process.terminate()
            return None
            
    except Exception as e:
        print_error(f"Failed to start backend service: {str(e)}")
        return None

def start_frontend_service():
    """Start the frontend service"""
    print_step(7, "Starting frontend service...")
    
    frontend_dir = Path("frontend")
    
    # Start the frontend development server
    try:
        print_colored("Starting React development server on http://localhost:3000", Colors.OKCYAN)
        frontend_process = subprocess.Popen(
            ["npm", "start"],
            cwd=frontend_dir,
            env={**os.environ, "BROWSER": "none"}  # Prevent auto-opening browser
        )
        
        # Wait for the frontend to start
        time.sleep(10)
        
        print_success("Frontend service started successfully")
        return frontend_process
        
    except Exception as e:
        print_error(f"Failed to start frontend service: {str(e)}")
        return None

def print_startup_summary():
    """Print startup summary and URLs"""
    print_header("🚀 REAL ESTATE RAG CHAT SYSTEM READY!")
    
    print_colored("Services are now running:", Colors.OKGREEN)
    print_colored("📊 Backend API: http://localhost:8001", Colors.OKBLUE)
    print_colored("📚 API Documentation: http://localhost:8001/docs", Colors.OKBLUE)
    print_colored("🌐 Frontend Application: http://localhost:3000", Colors.OKBLUE)
    
    print_colored("\nSample Login Credentials:", Colors.WARNING)
    print_colored("👤 Client: demo.client@example.com / demo123", Colors.OKCYAN)
    print_colored("🏠 Agent: demo.agent@example.com / demo123", Colors.OKCYAN)
    print_colored("👨‍💼 Employee: demo.employee@example.com / demo123", Colors.OKCYAN)
    print_colored("⚙️ Admin: demo.admin@example.com / demo123", Colors.OKCYAN)
    
    print_colored("\nFeatures Available:", Colors.OKGREEN)
    print_colored("✨ Role-based AI Chat with personalized responses", Colors.OKBLUE)
    print_colored("🏠 Property Management with CRUD operations", Colors.OKBLUE)
    print_colored("📁 File Upload and AI Analysis", Colors.OKBLUE)
    print_colored("🔐 Secure Authentication with JWT", Colors.OKBLUE)
    print_colored("📊 Real-time Analytics and Insights", Colors.OKBLUE)
    print_colored("🎯 Milestone Detection and Celebrations", Colors.OKBLUE)
    
    print_colored("\nPress Ctrl+C to stop all services", Colors.WARNING)

def main():
    """Main startup function"""
    print_header("🏠 REAL ESTATE RAG CHAT SYSTEM - STARTUP")
    print_colored("Initializing the complete Real Estate AI Assistant...", Colors.OKBLUE)
    
    # Pre-flight checks
    if not check_python_version():
        return False
    
    if not check_nodejs():
        return False
    
    if not check_postgresql():
        print_warning("Continuing without PostgreSQL verification...")
    
    # Setup phase
    if not setup_backend():
        return False
    
    if not setup_frontend():
        return False
    
    # Service startup phase
    backend_process = start_backend_service()
    if not backend_process:
        return False
    
    frontend_process = start_frontend_service()
    if not frontend_process:
        backend_process.terminate()
        return False
    
    # Success!
    print_startup_summary()
    
    try:
        # Keep the script running and monitor processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print_error("Backend process has stopped")
                break
                
            if frontend_process.poll() is not None:
                print_error("Frontend process has stopped")
                break
                
    except KeyboardInterrupt:
        print_colored("\n\nShutting down services...", Colors.WARNING)
        
        # Gracefully terminate processes
        if frontend_process and frontend_process.poll() is None:
            frontend_process.terminate()
            frontend_process.wait()
            
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
            backend_process.wait()
            
        print_success("All services stopped successfully")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print_error(f"Startup failed: {str(e)}")
        exit(1)