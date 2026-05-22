"""
Seed script for agent memory demonstration.

Generates realistic memory data for an AI agent:
- Users with profiles and preferences
- Tasks with status and priority
- Goals with progress tracking
- Past interactions with semantic embeddings

Run this script to populate RushDB with sample data.
Safe to run multiple times — checks for existing data before seeding.
"""

import os
import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

# Verify RushDB SDK
try:
    from rushdb import RushDB
except ImportError:
    print("ERROR: rushdb package not installed")
    print("Run: pip install rushdb>=2.0.0")
    sys.exit(1)

# Verify API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

# Initialize
fake = Faker()
Faker.seed(42)
random.seed(42)
db = RushDB(api_key)

# Embedding model (local, no API calls)
print("\nInitializing embedding model (sentence-transformers)...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("✓ Embedding model ready")


def get_embedding(text: str) -> list:
    """Generate embedding for text using local model."""
    return embedder.encode(text, normalize_embeddings=True).tolist()


def check_existing_data() -> bool:
    """Check if memory data already exists."""
    try:
        users = db.records.find({"labels": ["USER"], "limit": 1})
        return len(users.data) > 0
    except Exception:
        return False


def create_vector_index_if_needed():
    """Create vector index for INTERACTION descriptions."""
    try:
        indexes = db.ai.indexes.find()
        existing = [i for i in indexes.data if i.get('label') == 'INTERACTION' 
                     and i.get('propertyName') == 'description']
        if existing:
            return existing[0]
        
        index = db.ai.indexes.create({
            "label": "INTERACTION",
            "propertyName": "description",
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine"
        })
        print(f"✓ Created vector index: {index.data.get('__id')}")
        return index
    except Exception as e:
        print(f"Index creation note: {e}")
        return None


def seed_users():
    """Create sample users."""
    print("\nCreating users...")
    
    users_data = [
        {
            "name": "Alice Chen",
            "email": "alice@example.com",
            "role": "product_manager",
            "preferences": {"communication_style": "detailed_specs", "needs_timelines": True}
        },
        {
            "name": "Marcus Johnson",
            "email": "marcus@example.com",
            "role": "developer",
            "preferences": {"communication_style": "technical", "needs_code_examples": True}
        },
        {
            "name": "Sarah Williams",
            "email": "sarah@example.com",
            "role": "designer",
            "preferences": {"communication_style": "visual", "needs_mocks": True}
        }
    ]
    
    users = []
    for i, data in enumerate(users_data):
        user = db.records.create(label="USER", data=data)
        users.append(user)
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} users...")
    
    print(f"✓ Created {len(users)} users")
    return users


def seed_tasks(users):
    """Create sample tasks assigned to users."""
    print("\nCreating tasks...")
    
    task_templates = [
        ("Fix login validation bug", "urgent"),
        ("Implement user dashboard redesign", "medium"),
        ("Update API documentation", "low"),
        ("Review pull request #452", "medium"),
        ("Write unit tests for checkout flow", "high"),
        ("Optimize database queries", "high"),
        ("Add dark mode support", "low"),
        ("Conduct user research session", "medium"),
        ("Finalize Q1 product roadmap", "urgent"),
        ("Deploy staging environment", "high")
    ]
    
    statuses = ["pending", "in_progress", "completed"]
    
    tasks = []
    for i, (title, priority) in enumerate(task_templates):
        user = random.choice(users)
        status = random.choice(statuses)
        
        task = db.records.create(label="TASK", data={
            "title": title,
            "priority": priority,
            "status": status,
            "created_at": fake.date_time_between(start_date='-30d', end_date='now').isoformat()
        })
        
        # Attach task to user
        db.records.attach(
            source=task,
            target=user,
            options={"type": "ASSIGNED_TO", "direction": "in"}
        )
        
        tasks.append(task)
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} tasks...")
    
    print(f"✓ Created {len(tasks)} tasks")
    return tasks


def seed_goals(users):
    """Create goals for users."""
    print("\nCreating goals...")
    
    goal_templates = [
        ("Q1 Product Launch", 0.4, ["final review", "marketing materials", "staging tests"]),
        ("User Research Analysis", 0.6, ["synthesis report", "presentation"]),
        ("Technical Debt Reduction", 0.25, ["code cleanup", "documentation", "testing"]),
        ("Team Onboarding Program", 0.8, ["training materials", "mentorship matching"]),
        ("Performance Optimization Sprint", 0.15, ["profiling", "caching implementation"])
    ]
    
    goals = []
    for i, (title, progress, pending) in enumerate(goal_templates):
        user = random.choice(users)
        
        goal = db.records.create(label="GOAL", data={
            "title": title,
            "progress": progress,
            "pending_tasks": pending,
            "deadline": (datetime.now() + timedelta(days=random.randint(7, 90))).isoformat(),
            "created_at": fake.date_time_between(start_date='-60d', end_date='-30d').isoformat()
        })
        
        # Attach goal to user
        db.records.attach(
            source=user,
            target=goal,
            options={"type": "PURSUING", "direction": "out"}
        )
        
        goals.append(goal)
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} goals...")
    
    print(f"✓ Created {len(goals)} goals")
    return goals


def seed_interactions(users):
    """Create past interactions with embeddings."""
    print("\nCreating interactions (with embeddings)...")
    
    interaction_templates = [
        ("Customer reported checkout failing after updating payment method", 
         "Investigated and found payment gateway timeout issue. Escalated to payments team."),
        ("User couldn't complete purchase due to expired card",
         "Sent reminder email with link to update payment method. Issue resolved."),
        ("Checkout timeout issue on mobile devices",
         "Identified slow database query on cart summary. Optimized with caching."),
        ("Account locked after multiple login attempts",
         "Verified identity and unlocked account. Suggested implementing 2FA."),
        ("User asking how to export data",
         "Directed to settings > export page. Provided step-by-step guide."),
        ("Feature request: dark mode",
         "Logged request in product backlog. Prioritized for next sprint."),
        ("Performance issue on dashboard with large datasets",
         "Implemented pagination and virtual scrolling. Latency reduced by 70%."),
        ("Integration broken with third-party calendar app",
         "OAuth token refresh mechanism was failing. Fixed token refresh logic."),
        ("User confused about subscription tiers",
         "Provided comparison table. Offered upgrade consultation call."),
        ("Bug: notifications not appearing on iOS",
         "Traced to missing push certificate. Regenerated and redeployed."),
        ("User needs bulk import feature",
         "Directed to CSV import tool in admin panel. Helped with template."),
        ("Report: data not syncing between devices",
         "Identified conflict resolution issue. Implemented last-write-wins strategy."),
        ("Accessibility concern: screen reader not working",
         "Found missing ARIA labels. Fixed and tested with VoiceOver."),
        ("User requesting API access for automation",
         "Generated API keys. Provided documentation and rate limits."),
        ("Error 500 on user profile save",
         "Database constraint violation. Fixed schema and added validation."),
        ("User feedback: app loading too slowly",
         "Analyzed bundle size. Implemented code splitting. Load time improved."),
        ("Password reset email not received",
         "Email was in spam. Added SPF records and whitelist instructions."),
        ("Localization issue with date formats",
         "Implemented locale-aware date formatting library. Tested 12 locales."),
        ("User can't delete account",
         "Found GDPR compliance flow missing. Added account deletion wizard."),
        ("Dashboard showing wrong metrics after timezone change",
         "Server was caching user timezone. Implemented cache invalidation.")
    ]
    
    index = create_vector_index_if_needed()
    
    interactions = []
    for i, (description, resolution) in enumerate(interaction_templates):
        user = random.choice(users)
        
        # Generate embedding
        vector = get_embedding(description)
        
        interaction = db.records.create(
            label="INTERACTION",
            data={
                "description": description,
                "resolution": resolution,
                "outcome": random.choice(["resolved", "escalated", "pending"]),
                "created_at": fake.date_time_between(start_date='-90d', end_date='now').isoformat()
            },
            vectors=[{"propertyName": "description", "vector": vector}]
        )
        
        # Attach to user
        db.records.attach(
            source=interaction,
            target=user,
            options={"type": "HANDLED_BY", "direction": "in"}
        )
        
        interactions.append(interaction)
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1} interactions with embeddings...")
    
    # Upsert vectors to index
    if index:
        print("\nUpserting vectors to index...")
        items = [
            {"recordId": interaction.id, "vector": get_embedding(interaction.data.get("description", ""))}
            for interaction in interactions
        ]
        db.ai.indexes.upsert_vectors(index.data.get("__id"), {"items": items})
        print("✓ Vectors indexed")
    
    print(f"✓ Created {len(interactions)} interactions")
    return interactions


def main():
    """Main seeding function."""
    print("\n" + "=" * 70)
    print("RUSHDB AGENT MEMORY SEEDER")
    print("=" * 70)
    
    start_time = time.time()
    
    # Check for existing data
    if check_existing_data():
        print("\n⚠ Memory data already exists. Skipping seed.")
        print("To re-seed, delete existing records first.")
        return
    
    print("\nSeeding agent memory store...")
    
    try:
        # Create memory records
        users = seed_users()
        tasks = seed_tasks(users)
        goals = seed_goals(users)
        interactions = seed_interactions(users)
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("SEED COMPLETE")
        print("=" * 70)
        print(f"  Users:        {len(users)}")
        print(f"  Tasks:         {len(tasks)}")
        print(f"  Goals:         {len(goals)}")
        print(f"  Interactions:  {len(interactions)}")
        print(f"  Total time:   {elapsed:.2f}s")
        print("\nYour agent now has persistent memory.")
        print("Run 'python main.py' to see it in action.")
        
    except Exception as e:
        print(f"\n✗ Seeding failed: {e}")
        raise


if __name__ == "__main__":
    main()
