"""
Seed script for generating initial memory records in RushDB.

This script creates realistic AI agent memories including:
- Conversation summaries
- User preferences
- Learned facts
- Procedural memories (skills)

Run this once to populate the database with demo data.
"""

import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Check for API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    exit(1)

# Constants
MEMORY_COUNT = 100
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Realistic memory content templates
CONVERSATION_SUMMARIES = [
    "User asked about implementing authentication in Flask applications",
    "Discussed best practices for error handling in Python async code",
    "User wanted help debugging a memory leak in their Node.js application",
    "Explored different approaches to database query optimization",
    "User asked about implementing WebSocket connections for real-time updates",
    "Reviewed code for a REST API endpoint and suggested improvements",
    "User needed help with Docker container networking issues",
    "Discussed strategies for managing state in React applications",
    "User asked about implementing caching layer for API responses",
    "Explored options for migrating from REST to GraphQL",
    "User wanted to understand async/await patterns in Python",
    "Discussed proper logging practices for production applications",
    "User needed help with TypeScript type definitions",
    "Explored CI/CD pipeline configuration options",
    "User asked about securing API endpoints with JWT tokens",
    "Discussed rate limiting strategies for public APIs",
    "User wanted to implement file upload functionality",
    "Explored different approaches to data validation",
    "User asked about handling concurrent database operations",
    "Discussed strategies for monitoring application health",
]

USER_PREFERENCES = [
    "User prefers detailed explanations with code examples",
    "User likes to receive summaries at the start of conversations",
    "User prefers concise responses without unnecessary preamble",
    "User likes to see alternative approaches when available",
    "User prefers practical examples over theoretical discussions",
    "User likes step-by-step instructions for complex tasks",
    "User prefers to be asked clarifying questions before implementation",
    "User likes technical diagrams and architecture overviews",
    "User prefers to see performance benchmarks when discussing alternatives",
    "User likes to understand the 'why' before the 'how'",
    "User prefers receiving updates in the morning",
    "User likes to review code changes before final implementation",
    "User prefers asynchronous communication for long discussions",
    "User likes to have multiple options to choose from",
    "User prefers documentation alongside code examples",
]

LEARNED_FACTS = [
    "User works primarily with Python and JavaScript",
    "User's team uses Agile development methodology",
    "User prefers PostgreSQL over MySQL for complex queries",
    "User is familiar with Kubernetes and container orchestration",
    "User's codebase uses TypeScript for type safety",
    "User prefers VS Code as their primary code editor",
    "User's company has a CI/CD pipeline using GitHub Actions",
    "User works on a microservices architecture",
    "User prefers Redis for caching and session management",
    "User is experienced with Git version control workflows",
    "User's application uses React for the frontend",
    "User prefers REST over GraphQL for their current project",
    "User is working on a real-time collaboration feature",
    "User's team uses code review as part of their workflow",
    "User is familiar with serverless computing patterns",
]

SKILLS_AND_PROCEDURES = [
    "User knows how to implement JWT authentication in Express",
    "User is familiar with pytest for Python testing",
    "User knows how to configure Nginx as a reverse proxy",
    "User is experienced with Docker multi-stage builds",
    "User knows how to implement rate limiting with Redis",
    "User is familiar with React Hooks patterns",
    "User knows how to set up PostgreSQL connection pooling",
    "User is experienced with Git branching strategies",
    "User knows how to implement WebSocket keep-alive",
    "User is familiar with async iterators in Python",
    "User knows how to configure environment variables securely",
    "User is experienced with CSS Grid layout systems",
    "User knows how to implement request validation middleware",
    "User is familiar with database migration best practices",
    "User knows how to optimize React component re-renders",
]


def generate_timestamp(days_ago: int = None) -> str:
    """Generate ISO format timestamp."""
    if days_ago is None:
        days_ago = random.randint(0, 60)
    date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
    return date.isoformat() + "Z"


def create_vector_index(db: RushDB, label: str = "MEMORY", property_name: str = "content") -> str:
    """Create a vector index for semantic search."""
    print("Creating vector index for memory search...")
    
    # Check if index already exists
    try:
        indexes = db.ai.indexes.find()
        for idx in indexes:
            if idx.get("label") == label and idx.get("propertyName") == property_name:
                print(f"Vector index already exists: {label}.{property_name}")
                return idx.get("__id")
    except Exception:
        pass
    
    # Create new index (external mode since we provide our own embeddings)
    response = db.ai.indexes.create({
        "label": label,
        "propertyName": property_name,
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    
    index_id = response.data.get("__id")
    print(f"Created vector index: {index_id}")
    return index_id


def generate_memories(db: RushDB, embedder, index_id: str) -> dict:
    """Generate and store memory records."""
    
    all_content = CONVERSATION_SUMMARIES + USER_PREFERENCES + LEARNED_FACTS + SKILLS_AND_PROCEDURES
    types = {
        "conversation": CONVERSATION_SUMMARIES,
        "preference": USER_PREFERENCES,
        "fact": LEARNED_FACTS,
        "skill": SKILLS_AND_PROCEDURES,
    }
    
    stats = {"created": 0, "skipped": 0, "errors": 0}
    
    print(f"\nGenerating {MEMORY_COUNT} memory records...")
    print("(This uses local embeddings, no API calls needed)")
    
    # Check if data already exists
    existing = db.records.find({"labels": ["MEMORY"], "limit": 1})
    if existing:
        print("Memory records already exist. Skipping seed.")
        print("To re-seed, delete existing MEMORY records first.")
        return stats
    
    start_time = time.time()
    
    for i in range(MEMORY_COUNT):
        try:
            # Select random content and type
            memory_type = random.choice(list(types.keys()))
            content = random.choice(types[memory_type])
            
            # Add some variation to avoid duplicates
            if random.random() > 0.7:
                variations = [
                    " yesterday",
                    " last week",
                    " during our session",
                    " per user request",
                    " based on recent feedback",
                ]
                content = content + random.choice(variations)
            
            # Generate embedding
            embedding = embedder.encode(content).tolist()
            
            # Determine importance
            importance = round(random.uniform(0.3, 1.0), 2)
            
            # Create memory record with vector
            memory = db.records.create(
                label="MEMORY",
                data={
                    "content": content,
                    "type": memory_type,
                    "importance": importance,
                    "timestamp": generate_timestamp()
                },
                vectors=[{"propertyName": "content", "vector": embedding}]
            )
            
            stats["created"] += 1
            
            # Progress every 25 records
            if (i + 1) % 25 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"  Progress: {i + 1}/{MEMORY_COUNT} ({rate:.1f} records/sec)")
                
        except Exception as e:
            stats["errors"] += 1
            print(f"  Error creating memory {i}: {e}")
    
    return stats


def print_stats(stats: dict, elapsed: float):
    """Print seeding statistics."""
    print(f"\n{'='*50}")
    print("SEEDING COMPLETE")
    print(f"{'='*50}")
    print(f"Records created: {stats['created']}")
    print(f"Records skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    
    # Verify with a count query
    db = RushDB(api_key)
    count_result = db.records.find({"labels": ["MEMORY"], "limit": 0})
    print(f"\nTotal memories in database: {len(count_result)}")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("MEMORY DATABASE SEEDING")
    print("=" * 60)
    print(f"Target: {MEMORY_COUNT} memory records")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print()
    
    start_time = time.time()
    
    # Initialize RushDB
    print("Connecting to RushDB...")
    db = RushDB(api_key)
    print(f"Connected: {db}")
    print()
    
    # Load embedding model
    print(f"Loading embedding model ({EMBEDDING_MODEL})...")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    print("Embedding model loaded successfully\n")
    
    # Create vector index
    index_id = create_vector_index(db, "MEMORY", "content")
    
    # Generate memories
    stats = generate_memories(db, embedder, index_id)
    
    elapsed = time.time() - start_time
    print_stats(stats, elapsed)


if __name__ == "__main__":
    main()
