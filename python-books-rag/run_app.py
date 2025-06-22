#!/usr/bin/env python3
"""
Test runner for the RAG application
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    print("🚀 Starting RushDB Generic RAG API")
    print("=" * 50)

    # Test 1: Basic import test
    print("1. Testing imports...")
    try:
        sys.path.insert(0, str(project_dir / "src"))
        from rag_engine import RagService, TextProcessor
        from api import app
        from config import get_config
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return

    # Test 1.5: Check configuration
    print("\n1.5. Checking configuration...")
    config = get_config()
    if config['api_key']:
        print("✅ RushDB API token found in configuration")
    else:
        print("⚠️  No RushDB API token found")
        print("   Create .env file from .env.example and add your token")
        print("   You can still test the basic functionality")


    # Test 4: Start the API server
    print("\n3. Starting FastAPI server...")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("\nTo test the RAG system:")
    print("1. Index records: POST /index with search query and field")
    print("2. Search: POST /search with search query and query text")
    print("\nStarting server now...")

    try:
        # Use subprocess to start uvicorn
        result = subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], cwd=project_dir)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {str(e)}")

if __name__ == "__main__":
    main()
