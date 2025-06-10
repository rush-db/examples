#!/usr/bin/env python3
"""
Test runner for the RushDB Streamlit application
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    print("🚀 Starting RushDB Streamlit Application")
    print("=" * 50)

    # Test 1: Basic import test
    print("1. Testing imports...")
    try:
        sys.path.insert(0, str(project_dir / "src"))
        from streamlit_app import main as streamlit_main
        from rushdb_client import RushDBClient
        from data_processor import DataProcessor
        from chart_generator import ChartGenerator
        from config import get_config
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return

    # Test 2: Check configuration
    print("\n2. Checking configuration...")
    config = get_config()
    if config['api_token']:
        print("✅ RushDB API token found in configuration")
    else:
        print("⚠️  No RushDB API token found")
        print("   Create .env file from .env.example and add your token")
        print("   You can still test the basic functionality")

    # Test 3: Start the Streamlit application
    print("\n3. Starting Streamlit application...")
    print("🌐 Application will be available at: http://localhost:8501")
    print("\nTo test the application:")
    print("1. Configure your RushDB API token in .env file")
    print("2. Connect to RushDB using the sidebar")
    print("3. Generate sample data or load existing data")
    print("4. Explore the interactive visualizations")
    print("\nStarting Streamlit now...")

    try:
        # Use subprocess to start streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "src/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], cwd=project_dir)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Application error: {str(e)}")

if __name__ == "__main__":
    main()
