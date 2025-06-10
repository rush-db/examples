import os
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file if it exists."""
    # Look for .env file in the project root (parent of src directory)
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def get_config():
    """Get configuration from environment variables."""
    load_env_file()

    return {
        'api_token': os.getenv('RUSHDB_API_TOKEN'),
        'base_url': os.getenv('RUSHDB_BASE_URL'),
        'api_host': os.getenv('API_HOST', '0.0.0.0'),
        'api_port': int(os.getenv('API_PORT', 8000))
    }
