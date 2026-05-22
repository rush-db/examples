#!/usr/bin/env python3
"""
Seed script: Generates mock memory records with temporal metadata.

This script creates a realistic dataset of memory records with:
- Timestamps spanning different time periods (recent, old, very old)
- Different importance levels
- Topic assignments via relationships
- Multiple memory types to demonstrate decay effects

Run this once before main.py. Safe to re-run (idempotent).
"""

import os
import random
import math
from datetime import datetime, timedelta
from dotenv import load_dotenv
from faker import Faker

# Initialize Faker for realistic content
fake = Faker()
Faker.seed(42)
random.seed(42)

# Load environment variables
load_dotenv()

# Import RushDB SDK
from rushdb import RushDB

# ============================================================================
# CONFIGURATION
# ============================================================================

# How many records to generate per memory type
RECORD_COUNTS = {
    "quick_note": 50,      # Short-term, ephemeral memories
    "project_doc": 30,     # Medium-term project documentation
    "knowledge_base": 25,  # Long-term knowledge storage
    "user_preference": 20, # User preferences and settings
}

# Topics for categorization (creates CONCEPT nodes and relationships)
TOPICS = [
    "machine_learning",
    "database_design",
    "api_development",
    "devops",
    "frontend",
    "security",
    "performance",
    "testing",
]

# Importance weights for different memory types
IMPORTANCE_WEIGHTS = {
    "quick_note": (1, 3),       # Low importance
    "project_doc": (4, 7),      # Medium importance
    "knowledge_base": (6, 10),  # High importance
    "user_preference": (5, 9),  # Medium-high importance
}

# Time decay half-lives in hours (how quickly importance decays)
HALFLIFE_HOURS = {
    "quick_note": 24,       # Decays fast - 24 hours half-life
    "project_doc": 168,     # Week half-life
    "knowledge_base": 720,  # Month half-life
    "user_preference": 336, # Two-week half-life
}


def get_exponential_decay_rate(half_life_hours: float) -> float:
    """Convert half-life to exponential decay rate (lambda)."""
    return math.log(2) / half_life_hours


def calculate_decay_score(
    base_importance: float,
    created_at: datetime,
    memory_type: str,
    decay_method: str = "halflife"
) -> float:
    """
    Calculate decayed importance score based on time elapsed.
    
    Args:
        base_importance: Original importance score (1-10)
        created_at: When the memory was created
        memory_type: Type of memory for half-life lookup
        decay_method: 'halflife', 'exponential', or 'logarithmic'
    
    Returns:
        Decayed score (0.0 to base_importance)
    """
    now = datetime.utcnow()
    hours_elapsed = (now - created_at).total_seconds() / 3600
    
    if hours_elapsed < 0:
        # Future timestamps treated as now
        hours_elapsed = 0
    
    if decay_method == "exponential":
        decay_rate = get_exponential_decay_rate(HALFLIFE_HOURS[memory_type])
        decayed = base_importance * math.exp(-decay_rate * hours_elapsed)
    elif decay_method == "logarithmic":
        # Prevent log(0) and keep score reasonable
        decayed = base_importance / (1 + math.log(1 + hours_elapsed))
    else:  # halflife (default)
        half_life = HALFLIFE_HOURS[memory_type]
        decayed = base_importance * math.pow(0.5, hours_elapsed / half_life)
    
    return max(0.0, min(base_importance, decayed))


def create_memory_content(memory_type: str) -> dict:
    """Generate realistic memory content based on type."""
    templates = {
        "quick_note": [
            f"Remember to check {fake.company()} PR",
            f"{fake.name()} mentioned {fake.catch_phrase()}",
            f"Fix the {fake.word()} issue in {fake.word()}",
            f"Meeting notes: {fake.sentence()}",
            f"TODO: Review {fake.catch_phrase()}",
        ],
        "project_doc": [
            f"Architecture decision: {fake.sentence()}",
            f"API endpoint /v1/{fake.word()}/{fake.word()} returns {fake.word()}",
            f"Database schema for {fake.word()} table includes {fake.word()} index",
            f"Deployment pipeline for {fake.word()} uses {fake.word()} cluster",
            f"Feature flag {fake.word()} controls {fake.word()} behavior",
        ],
        "knowledge_base": [
            f"Best practice: {fake.sentence(nb_words=15)}",
            f"Explanation of {fake.word()} pattern in distributed systems",
            f"When to use {fake.word()} vs {fake.word()} for {fake.word()} workloads",
            f"Performance optimization: {fake.sentence(nb_words=10)}",
            f"Security consideration: {fake.sentence(nb_words=12)}",
        ],
        "user_preference": [
            f"{fake.name()} prefers {fake.word()} theme",
            f"Enable {fake.word()} notifications for {fake.name()}",
            f"Default view: {fake.word()} sorted by {fake.word()}",
            f"{fake.name()} enabled {fake.word()} integration",
            f"Timezone preference: {fake.timezone()} for {fake.name()}",
        ],
    }
    
    content = random.choice(templates[memory_type])
    importance_range = IMPORTANCE_WEIGHTS[memory_type]
    
    return {
        "content": content,
        "importance": random.randint(*importance_range),
        "memory_type": memory_type,
        "topic": random.choice(TOPICS),
    }


def generate_timestamp(memory_type: str) -> datetime:
    """
    Generate a timestamp with bias toward the memory type's decay rate.
    
    Quick notes: mostly recent (last 48 hours)
    Project docs: distributed over last 2 weeks
    Knowledge base: can be very old (up to 6 months)
    User preferences: recent to medium age
    """
    now = datetime.utcnow()
    
    if memory_type == "quick_note":
        # 70% recent (0-48h), 30% older (48-168h)
        if random.random() < 0.7:
            hours_ago = random.uniform(0, 48)
        else:
            hours_ago = random.uniform(48, 168)
    elif memory_type == "project_doc":
        # Distributed over last 2 weeks
        hours_ago = random.uniform(0, 336)
    elif memory_type == "knowledge_base":
        # Can be up to 6 months old
        hours_ago = random.uniform(0, 4320)
    else:  # user_preference
        # Mostly recent with some medium-age
        hours_ago = random.uniform(0, 720)
    
    return now - timedelta(hours=hours_ago)


def seed_database(db: RushDB) -> dict:
    """
    Seed the database with memory records.
    
    Returns:
        Statistics about the seeded data.
    """
    print("\n" + "=" * 60)
    print("SEEDING DATABASE WITH TEMPORAL MEMORY RECORDS")
    print("=" * 60)
    
    stats = {"total": 0, "by_type": {}, "concepts": 0}
    
    # First, create CONCEPT nodes for topics
    print("\n[1/3] Creating concept nodes...")
    concepts = {}
    for i, topic in enumerate(TOPICS):
        if i % 20 == 0:
            print(f"  Creating concept nodes... ({i}/{len(TOPICS)})")
        
        concept = db.records.upsert(
            label="CONCEPT",
            data={"name": topic, "category": "topic"},
            options={"mergeBy": ["name"]}
        )
        concepts[topic] = concept
        stats["concepts"] += 1
    print(f"  Created {len(concepts)} concept nodes")
    
    # Create MEMORY records
    print("\n[2/3] Creating memory records...")
    memories_by_type = {}
    
    for memory_type, count in RECORD_COUNTS.items():
        print(f"\n  Creating {count} {memory_type} records...")
        memories_by_type[memory_type] = []
        stats["by_type"][memory_type] = 0
        
        for i in range(count):
            if i % 50 == 0 and i > 0:
                print(f"    Progress: {i}/{count} records created")
            
            # Generate temporal metadata
            created_at = generate_timestamp(memory_type)
            memory_data = create_memory_content(memory_type)
            
            # Add temporal fields (critical for decay queries)
            memory_data["created_at"] = created_at.isoformat()
            memory_data["updated_at"] = (created_at + timedelta(
                hours=random.uniform(0, 24)
            )).isoformat()
            memory_data["access_count"] = random.randint(0, 50)
            
            # Create the memory record
            memory = db.records.create(
                label="MEMORY",
                data=memory_data
            )
            memories_by_type[memory_type].append(memory)
            stats["total"] += 1
            stats["by_type"][memory_type] += 1
    
    print(f"\n  Total memories created: {stats['total']}")
    
    # Create relationships (MEMORY -> CONCEPT via ABOUT)
    print("\n[3/3] Creating memory-concept relationships...")
    total_rels = 0
    
    for memory_type, memories in memories_by_type.items():
        print(f"  Linking {memory_type} memories to concepts...")
        for i, memory in enumerate(memories):
            if i % 50 == 0 and i > 0:
                print(f"    Progress: {i}/{len(memories)} relationships created")
            
            topic = memory.data.get("topic")
            if topic and topic in concepts:
                db.records.attach(
                    source=memory,
                    target=concepts[topic],
                    options={"type": "ABOUT", "direction": "out"}
                )
                total_rels += 1
    
    print(f"\n  Total relationships created: {total_rels}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Total MEMORY records: {stats['total']}")
    for mtype, count in stats['by_type'].items():
        half_life = HALFLIFE_HOURS[mtype]
        print(f"    - {mtype}: {count} records (halflife: {half_life}h)")
    print(f"  - CONCEPT nodes: {stats['concepts']}")
    print(f"  - ABOUT relationships: {total_rels}")
    print("\nYou can now run `python main.py` to see decay scoring in action!")
    
    return stats


def check_existing_data(db: RushDB) -> bool:
    """Check if data already exists to avoid duplicate seeding."""
    result = db.records.find({
        "labels": ["MEMORY"],
        "limit": 1
    })
    return len(result.data) > 0


def main():
    """Main entry point for the seed script."""
    print("\n" + "=" * 60)
    print("RUSHDB TIME-DECAY SEEDING SCRIPT")
    print("=" * 60)
    
    # Initialize RushDB client
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("\nERROR: RUSHDB_API_TOKEN not found in environment!")
        print("Please copy .env.example to .env and add your API token.")
        return
    
    url = os.getenv("RUSHDB_URL")
    if url:
        db = RushDB(api_token, url=url)
    else:
        db = RushDB(api_token)
    
    print(f"\nConnected to RushDB: {db}")
    
    # Check for existing data
    if check_existing_data(db):
        print("\n⚠️  Existing MEMORY records found!")
        response = input("  Skip seeding to avoid duplicates? [Y/n]: ")
        if response.lower() != 'n':
            print("\nSkipping seed. To re-seed, delete existing MEMORY records first.")
            return
        print("\nProceeding with seeding (may create duplicates)...")
    
    # Run seeding
    seed_database(db)


if __name__ == "__main__":
    main()
