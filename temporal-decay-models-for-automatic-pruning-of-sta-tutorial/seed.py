#!/usr/bin/env python3
"""
Seed script: Generates realistic agent memory data for decay model demonstration.

This script creates an agent with memories across different categories,
with varying ages and importance scores to demonstrate the decay model.

Run once before main.py to populate RushDB with test data.
Idempotent: safe to run multiple times.
"""

import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize Faker with reproducibility seed
fake = Faker()
Faker.seed(42)
random.seed(42)

# ============================================================================
# Configuration
# ============================================================================

# Decay parameters (must match main.py for consistent demo)
DECAY_LAMBDA = 0.05  # 5% decay per hour
RELEVANCE_THRESHOLD = 0.30

# Memory categories with their typical characteristics
MEMORY_CATEGORIES = {
    "fact": {
        "decay_rate": 0.01,  # Slow decay - facts persist
        "importance_range": (0.6, 0.9),
        "examples": [
            "User works as a software engineer at TechCorp",
            "Company Q4 deadline is March 15th",
            "Budget for project X is $50,000",
            "Primary stakeholders are finance and engineering teams",
            "Office location is in Building A, Floor 3",
        ],
    },
    "preference": {
        "decay_rate": 0.05,  # Medium decay
        "importance_range": (0.5, 0.85),
        "examples": [
            "User prefers dark mode in IDE",
            "Likes concise bullet-point responses",
            "Prefers morning meetings before 10am",
            "Usually works with TypeScript and Python",
            "Prefers async communication over meetings",
        ],
    },
    "context": {
        "decay_rate": 0.15,  # Fast decay - recent context fades quickly
        "importance_range": (0.4, 0.8),
        "examples": [
            "Currently debugging authentication module",
            "User mentioned upcoming product launch next week",
            "Discussing database migration strategy",
            "Working on API endpoint optimization",
            "Reviewing pull request #1234",
        ],
    },
    "skill": {
        "decay_rate": 0.005,  # Very slow decay - skills persist
        "importance_range": (0.7, 0.95),
        "examples": [
            "User is proficient in React and Node.js",
            "Has experience with PostgreSQL and Redis",
            "Certified in AWS Solutions Architect",
            "Strong background in distributed systems",
            "Experienced with CI/CD pipelines using GitHub Actions",
        ],
    },
}

# ============================================================================
# Utility Functions
# ============================================================================

def compute_relevance(initial_importance: float, created_at: datetime, decay_rate: float) -> float:
    """
    Compute current relevance using exponential decay.
    
    Formula: relevance = initial_importance × e^(-λ × age_hours)
    
    Args:
        initial_importance: Base importance score (0.0 - 1.0)
        created_at: When the memory was created
        decay_rate: Lambda parameter (higher = faster decay)
    
    Returns:
        Current relevance score (0.0 - 1.0)
    """
    age_hours = (datetime.now() - created_at).total_seconds() / 3600
    relevance = initial_importance * pow(2.71828, -decay_rate * age_hours)
    return max(0.0, min(1.0, relevance))  # Clamp to [0, 1]


def create_memory_record(
    db: RushDB,
    agent_id: str,
    category: str,
    content: str,
    created_at: datetime,
    access_count: int = 0,
) -> dict:
    """Create a memory record with metadata."""
    
    category_config = MEMORY_CATEGORIES[category]
    initial_importance = random.uniform(*category_config["importance_range"])
    
    # Create the memory record
    memory = db.records.create(
        label="MEMORY",
        data={
            "content": content,
            "category": category,
            "initialImportance": round(initial_importance, 3),
            "decayRate": category_config["decay_rate"],
            "createdAt": created_at.isoformat(),
            "lastAccessedAt": created_at.isoformat(),
            "accessCount": access_count,
            "agentId": agent_id,
        }
    )
    
    return memory


def check_existing_data(db: RushDB) -> tuple[bool, str | None]:
    """
    Check if demo data already exists.
    Returns (exists, agent_id).
    """
    try:
        agents = db.records.find({
            "labels": ["AGENT"],
            "where": {"type": "decay-demo-agent"},
            "limit": 1
        })
        
        if agents and len(agents) > 0:
            return True, agents[0].id
        return False, None
    except Exception:
        return False, None


def cleanup_existing_data(db: RushDB, agent_id: str) -> int:
    """
    Remove existing demo data for clean reseeding.
    Returns count of deleted memories.
    """
    # Find all memories for this agent
    memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {"agentId": agent_id}
    })
    
    count = 0
    for memory in memories:
        db.records.delete(record_id=memory.id)
        count += 1
    
    # Delete the agent itself
    db.records.delete(record_id=agent_id)
    
    return count


# ============================================================================
# Main Seeding Function
# ============================================================================

def seed_agent_memory_system():
    """
    Seed RushDB with a complete agent memory system.
    
    Creates:
    - 1 AGENT record (type: decay-demo-agent)
    - ~50 MEMORY records across 4 categories
    - 3 CONTEXT records (conversation sessions)
    - Appropriate relationships between records
    """
    
    print("=" * 60)
    print("Agent Memory System - Data Seeding")
    print("=" * 60)
    
    # Initialize RushDB
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("ERROR: RUSHDB_API_TOKEN not found in environment")
        print("Set it in .env or export it before running:")
        print("  export RUSHDB_API_TOKEN=your_token_here")
        sys.exit(1)
    
    db = RushDB(api_token)
    print(f"\n✓ Connected to RushDB")
    
    # Check for existing data
    existing_exists, existing_agent_id = check_existing_data(db)
    
    if existing_exists:
        print(f"\n⚠ Existing demo data found (Agent ID: {existing_agent_id})")
        response = input("Delete and reseed? [y/N]: ").strip().lower()
        
        if response == "y":
            deleted_count = cleanup_existing_data(db, existing_agent_id)
            print(f"✓ Deleted {deleted_count} existing memories")
        else:
            print("Aborted. Run main.py to use existing data.")
            sys.exit(0)
    
    # ========================================================================
    # Create Agent
    # ========================================================================
    
    print("\n📦 Creating agent record...")
    
    agent = db.records.create(
        label="AGENT",
        data={
            "name": "Demo Agent",
            "type": "decay-demo-agent",
            "description": "AI assistant demonstrating temporal decay memory management",
            "createdAt": datetime.now().isoformat(),
            "config": {
                "decayLambda": DECAY_LAMBDA,
                "relevanceThreshold": RELEVANCE_THRESHOLD,
                "reinforcementBoost": 0.20,
                "maxAccessReinforcement": 5,
            }
        }
    )
    
    print(f"  ✓ Agent created: {agent.id}")
    
    # ========================================================================
    # Create Memories with Varying Ages
    # ========================================================================
    
    print("\n📦 Creating memory records...")
    print("  (Memories with varying ages to demonstrate decay)")
    
    memories_created = 0
    total_target = 50
    
    # Time ranges for memories
    now = datetime.now()
    time_ranges = [
        ("very_recent", now - timedelta(hours=2), now - timedelta(minutes=30), 10),
        ("recent", now - timedelta(days=1), now - timedelta(hours=4), 15),
        ("moderate", now - timedelta(days=3), now - timedelta(days=1), 12),
        ("old", now - timedelta(days=7), now - timedelta(days=3), 8),
        ("very_old", now - timedelta(days=14), now - timedelta(days=7), 5),
    ]
    
    for time_range_name, start_time, end_time, count in time_ranges:
        for i in range(count):
            category = random.choice(list(MEMORY_CATEGORIES.keys()))
            category_examples = MEMORY_CATEGORIES[category]["examples"]
            
            # Use predefined examples or generate new ones
            if category_examples and random.random() > 0.3:
                content = random.choice(category_examples)
            else:
                # Generate contextual content
                if category == "fact":
                    content = f"User mentioned {fake.catch_phrase()} regarding {fake.bs()}"
                elif category == "preference":
                    content = f"{fake.catch_phrase()} about user preferences"
                elif category == "context":
                    content = f"Currently working on: {fake.catch_phrase()}"
                else:
                    content = f"Skill context: {fake.catch_phrase()}"
            
            # Random creation time within the range
            time_diff = (end_time - start_time).total_seconds()
            random_offset = random.uniform(0, time_diff)
            created_at = start_time + timedelta(seconds=random_offset)
            
            # Some memories have been accessed
            access_count = random.choices(
                [0, 1, 2, 3, 5, 10],
                weights=[0.4, 0.25, 0.15, 0.1, 0.07, 0.03]
            )[0]
            
            memory = create_memory_record(
                db=db,
                agent_id=agent.id,
                category=category,
                content=content,
                created_at=created_at,
                access_count=access_count,
            )
            
            # Attach memory to agent
            db.records.attach(
                source=agent,
                target=memory,
                options={"type": "HAS_MEMORY", "direction": "out"}
            )
            
            memories_created += 1
            
            if memories_created % 10 == 0:
                print(f"  ✓ Created {memories_created}/{total_target} memories...")
    
    # ========================================================================
    # Create Context Records
    # ========================================================================
    
    print("\n📦 Creating context records...")
    
    context_sessions = [
        {
            "name": "Morning Standup - Project Discussion",
            "startedAt": (now - timedelta(hours=3)).isoformat(),
            "endedAt": (now - timedelta(hours=2, minutes=30)).isoformat(),
            "topic": "Project status and blockers",
        },
        {
            "name": "Code Review Session",
            "startedAt": (now - timedelta(days=1, hours=2)).isoformat(),
            "endedAt": (now - timedelta(days=1)).isoformat(),
            "topic": "Reviewing PR #1234 authentication changes",
        },
        {
            "name": "Planning Meeting",
            "startedAt": (now - timedelta(days=2)).isoformat(),
            "endedAt": (now - timedelta(days=2, hours=-1)).isoformat(),
            "topic": "Q2 planning and resource allocation",
        },
    ]
    
    for ctx_data in context_sessions:
        context = db.records.create(
            label="CONTEXT",
            data={
                **ctx_data,
                "agentId": agent.id,
            }
        )
        
        db.records.attach(
            source=agent,
            target=context,
            options={"type": "OPERATES_IN", "direction": "out"}
        )
        
        print(f"  ✓ Context: {ctx_data['name']}")
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"\n✓ Agent: {agent.id}")
    print(f"✓ Memories created: {memories_created}")
    print(f"✓ Contexts created: {len(context_sessions)}")
    
    # Compute and show relevance distribution
    all_memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {"agentId": agent.id}
    })
    
    relevance_buckets = {"high (>0.7)": 0, "medium (0.4-0.7)": 0, "low (<0.4)": 0, "critical (<0.3)": 0}
    
    for memory in all_memories:
        created_at = datetime.fromisoformat(memory["createdAt"])
        relevance = compute_relevance(
            memory["initialImportance"],
            created_at,
            memory["decayRate"]
        )
        
        if relevance > 0.7:
            relevance_buckets["high (>0.7)"] += 1
        elif relevance > 0.4:
            relevance_buckets["medium (0.4-0.7)"] += 1
        elif relevance > 0.3:
            relevance_buckets["low (<0.4)"] += 1
        else:
            relevance_buckets["critical (<0.3)"] += 1
    
    print("\nCurrent relevance distribution:")
    for bucket, count in relevance_buckets.items():
        pct = (count / len(all_memories)) * 100 if all_memories else 0
        print(f"  {bucket}: {count} ({pct:.1f}%)")
    
    print("\n📋 Run `python main.py` to see the decay model in action!")


if __name__ == "__main__":
    seed_agent_memory_system()
