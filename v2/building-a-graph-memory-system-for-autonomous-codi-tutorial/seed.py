"""
Seed script for graph-memory tutorial.

Creates sample memory data including agents, tasks, files, observations,
and confirmed facts. Also sets up vector indexes for semantic search.

This script is idempotent — safe to run multiple times.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Check for API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)

# Initialize embedding model
print("Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def get_embedding(text: str) -> list:
    """Generate embedding for text using the model."""
    return model.encode(text).tolist()


def seed_data():
    """Seed the database with sample memory data."""
    print("\n=== Seeding Graph Memory ===\n")

    # Check if we already have data (idempotency)
    existing = db.records.find({"labels": ["Agent"], "limit": 1})
    if existing.data:
        print("Memory already seeded. Skipping...")
        return

    # Create Agent
    print("Creating agent record...")
    agent = db.records.create(
        label="Agent",
        data={
            "name": "Codi",
            "version": "1.0.0",
            "session_started": datetime.now().isoformat()
        },
        vectors=[{"propertyName": "description", "vector": get_embedding("Codi is an autonomous coding agent")}]
    )
    print(f"  Created: Agent '{agent['name']}'")

    # Create Tasks
    tasks_data = [
        {
            "title": "Implement user authentication",
            "description": "Add JWT-based authentication with refresh tokens",
            "status": "completed"
        },
        {
            "title": "Set up database migration system",
            "description": "Create automated migration scripts with rollback support",
            "status": "in_progress"
        },
        {
            "title": "Optimize API response times",
            "description": "Reduce average response time from 500ms to under 100ms",
            "status": "planned"
        }
    ]

    tasks = []
    for i, task_data in enumerate(tasks_data):
        print(f"Creating task {i+1}/{len(tasks_data)}...")
        task = db.records.create(
            label="Task",
            data={
                **task_data,
                "created_at": (datetime.now() - timedelta(days=3-i)).isoformat()
            },
            vectors=[{"propertyName": "description", "vector": get_embedding(task_data["description"])}]
        )
        tasks.append(task)
        
        # Link agent to task
        db.records.attach(
            source=agent,
            target=task,
            options={"type": "WORKING_ON"}
        )
        print(f"  Created: Task '{task['title']}'")

    # Create Files
    files_data = [
        {"path": "src/auth/jwt_handler.py", "type": "implementation", "language": "python"},
        {"path": "src/auth/refresh_token.py", "type": "implementation", "language": "python"},
        {"path": "src/db/migrations/001_initial.sql", "type": "migration", "language": "sql"},
        {"path": "src/api/users.py", "type": "endpoint", "language": "python"},
    ]

    for i, file_data in enumerate(files_data):
        print(f"Creating file {i+1}/{len(files_data)}...")
        file_record = db.records.create(
            label="File",
            data=file_data,
            vectors=[{"propertyName": "description", "vector": get_embedding(f"{file_data['path']} - {file_data['type']}")}]
        )
        
        # Link first two tasks to auth files
        if i < 2:
            db.records.attach(
                source=tasks[0],
                target=file_record,
                options={"type": "MODIFIES"}
            )
        elif i == 2:
            db.records.attach(
                source=tasks[1],
                target=file_record,
                options={"type": "MODIFIES"}
            )
        print(f"  Created: File '{file_record['path']}'")

    # Create Observations
    observations_data = [
        {
            "type": "hypothesis",
            "content": "User sessions should expire after 24 hours for security",
            "importance": 2,
            "status": "pending"
        },
        {
            "type": "finding",
            "content": "Database connection pooling reduces latency by ~40%",
            "importance": 2,
            "status": "pending"
        },
        {
            "type": "speculation",
            "content": "Could use Redis for caching to speed up auth checks",
            "importance": 1,
            "status": "pending"
        },
        {
            "type": "observation",
            "content": "The JWT secret should be at least 256 bits for HS256",
            "importance": 3,
            "status": "pending"
        }
    ]

    for i, obs_data in enumerate(observations_data):
        print(f"Creating observation {i+1}/{len(observations_data)}...")
        obs = db.records.create(
            label="Observation",
            data={
                **obs_data,
                "created_at": (datetime.now() - timedelta(days=2-i)).isoformat()
            },
            vectors=[{"propertyName": "content", "vector": get_embedding(obs_data["content"])}]
        )
        
        db.records.attach(
            source=agent,
            target=obs,
            options={"type": "CREATED"}
        )
        print(f"  Created: Observation about '{obs_data['type']}'")

    # Create Confirmed Facts
    confirmed_facts_data = [
        {
            "content": "Refresh tokens should be rotated on each use to prevent replay attacks",
            "source": "security_best_practices",
            "confirmed_at": (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            "content": "JWT tokens should not store sensitive user data in the payload",
            "source": "oauth2_specification",
            "confirmed_at": (datetime.now() - timedelta(days=2)).isoformat()
        }
    ]

    for i, fact_data in enumerate(confirmed_facts_data):
        print(f"Creating confirmed fact {i+1}/{len(confirmed_facts_data)}...")
        fact = db.records.create(
            label="ConfirmedFact",
            data=fact_data,
            vectors=[{"propertyName": "content", "vector": get_embedding(fact_data["content"])}]
        )
        print(f"  Created: ConfirmedFact")

    # Create Decisions
    decisions_data = [
        {
            "description": "Use RS256 for JWT signing to allow key rotation",
            "rationale": "RS256 is more secure than HS256 for multi-service architectures",
            "outcome": "implemented"
        },
        {
            "description": "Store refresh tokens in HTTP-only cookies",
            "rationale": "Prevents XSS attacks from stealing tokens",
            "outcome": "implemented"
        }
    ]

    for i, dec_data in enumerate(decisions_data):
        print(f"Creating decision {i+1}/{len(decisions_data)}...")
        decision = db.records.create(
            label="Decision",
            data={
                **dec_data,
                "decided_at": (datetime.now() - timedelta(days=2-i)).isoformat()
            },
            vectors=[{"propertyName": "rationale", "vector": get_embedding(dec_data["rationale"])}]
        )
        
        db.records.attach(
            source=agent,
            target=decision,
            options={"type": "MADE_DECISION"}
        )
        db.records.attach(
            source=decision,
            target=tasks[0],
            options={"type": "INFORMS"}
        )
        print(f"  Created: Decision '{dec_data['description'][:50]}...'")

    print("\n=== Seeding Complete ===")
    print(f"Created: 1 Agent, {len(tasks)} Tasks, {len(files_data)} Files, ")
    print(f"          {len(observations_data)} Observations, {len(confirmed_facts_data)} Confirmed Facts, ")
    print(f"          {len(decisions_data)} Decisions")


if __name__ == "__main__":
    seed_data()
