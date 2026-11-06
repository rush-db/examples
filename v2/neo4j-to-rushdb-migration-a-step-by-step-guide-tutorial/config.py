"""Configuration loader for RushDB migration project."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


def get_rushdb_token() -> str:
    """Get RushDB API token from environment."""
    token = os.getenv("RUSHDB_TOKEN", "")
    if not token:
        raise ValueError(
            "RUSHDB_TOKEN environment variable is not set. "
            "Please copy .env.example to .env and set your API token."
        )
    return token


def get_rushdb_url() -> str | None:
    """Get optional custom RushDB URL for self-hosted deployments."""
    url = os.getenv("RUSHDB_URL")
    if url:
        return url.rstrip("/")
    return None
