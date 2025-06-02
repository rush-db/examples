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

    print("🚀 Starting RushDB Simple RAG Application")
    print("=" * 50)

    # Test 1: Basic import test
    print("1. Testing imports...")
    try:
        sys.path.insert(0, str(project_dir / "src"))
        from rag_engine import SimpleRAG, DocumentProcessor
        from api import app
        from config import get_config
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return

    # Test 1.5: Check configuration
    print("\n1.5. Checking configuration...")
    config = get_config()
    if config['api_token']:
        print("✅ RushDB API token found in configuration")
    else:
        print("⚠️  No RushDB API token found")
        print("   Create .env file from .env.example and add your token")
        print("   You can still test the basic functionality")

    # Test 2: Document processor test
    print("\n2. Testing DocumentProcessor...")
    try:
        processor = DocumentProcessor()
        test_text = "This is a test document with multiple sentences. " * 10
        chunks = processor.chunk_text(test_text)
        embedding = processor.vectorize_text("test query")
        print(f"✅ Created {len(chunks)} chunks and {len(embedding)}-dimensional embedding")
    except Exception as e:
        print(f"❌ DocumentProcessor error: {e}")
        return

    # Test 3: Check test documents
    print("\n3. Checking test documents...")
    test_docs_dir = project_dir / "test_docs"
    if test_docs_dir.exists():
        md_files = list(test_docs_dir.glob("*.md"))
        print(f"✅ Found {len(md_files)} markdown files in test_docs/")
        for file in md_files:
            print(f"   - {file.name}")
    else:
        print("❌ No test_docs directory found")

    # Test 4: Start the API server
    print("\n4. Starting FastAPI server...")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("\nTo test the RAG system:")
    print("1. First initialize: POST /initialize with your RushDB API token")
    print("2. Ingest documents: POST /ingest/directory")
    print("3. Search: POST /search")
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
