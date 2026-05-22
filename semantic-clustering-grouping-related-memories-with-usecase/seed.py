#!/usr/bin/env python3
"""
Seed script: Loads developer memory data into RushDB.

This script:
1. Creates records for tasks, decisions, bugs, learnings, and refactors
2. Establishes explicit relationships between them
3. Ensures idempotency (safe to run multiple times)

Usage: python seed.py
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("❌ Error: RUSHDB_API_KEY not found in environment")
    print("   Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(API_KEY)


def load_seed_data():
    """Load the seed memories from JSON file."""
    seed_path = Path(__file__).parent / "data" / "seed_memories.json"
    with open(seed_path, "r") as f:
        return json.load(f)


def find_existing_by_title(title: str) -> list:
    """Find records by title for idempotency check."""
    return db.records.find({
        "labels": ["TASK", "DECISION", "REFACTOR", "BUG", "LEARNING"],
        "where": {"title": title}
    })


def create_or_get(data: dict, label: str) -> object:
    """Create a record or return existing one (idempotent)."""
    existing = find_existing_by_title(data.get("title", ""))
    if existing:
        print(f"   Found existing: {data.get('title', 'unknown')[:50]}")
        return existing[0]
    
    record = db.records.create(label=label, data=data)
    print(f"   Created: {data.get('title', 'unknown')[:50]}")
    return record


def link_records(source: object, target: object, relation_type: str):
    """Create a relationship between two records."""
    try:
        db.records.attach(
            source=source,
            target=target,
            options={"type": relation_type, "direction": "out"}
        )
        print(f"      ├─ [{relation_type}] {target.data.get('title', target.id)[:40]}")
    except Exception as e:
        # Relationship might already exist - that's OK
        print(f"      ├─ [SKIP] {relation_type} (may already exist)")


def main():
    print("\n🚀 Seeding developer memory database\n")
    print("=" * 60)
    
    seed_data = load_seed_data()
    created_records = {}  # title -> record mapping
    
    # Phase 1: Create all records
    print("\n📝 Phase 1: Creating records...\n")
    
    for item in seed_data:
        label = item["label"]
        data = item["data"]
        title = data.get("title", "unknown")
        
        record = create_or_get(data, label)
        created_records[title] = record
    
    # Phase 2: Establish relationships
    print("\n🔗 Phase 2: Creating relationships...\n")
    
    for item in seed_data:
        source_title = item["data"].get("title", "")
        if source_title not in created_records:
            continue
            
        source = created_records[source_title]
        
        for relation in item.get("relations", []):
            target_title = relation.get("targetTitle", "")
            rel_type = relation.get("type", "")
            
            if target_title in created_records:
                target = created_records[target_title]
                link_records(source, target, rel_type)
    
    # Summary
    total_records = len(created_records)
    print("\n" + "=" * 60)
    print(f"\n✅ Seeding complete!")
    print(f"   Total records: {total_records}")
    print(f"   - Tasks: {sum(1 for item in seed_data if item['label'] == 'TASK')}")
    print(f"   - Decisions: {sum(1 for item in seed_data if item['label'] == 'DECISION')}")
    print(f"   - Refactors: {sum(1 for item in seed_data if item['label'] == 'REFACTOR')}")
    print(f"   - Bugs: {sum(1 for item in seed_data if item['label'] == 'BUG')}")
    print(f"   - Learnings: {sum(1 for item in seed_data if item['label'] == 'LEARNING')}")
    print(f"\n   Run 'python main.py' to query the memory cluster\n")


if __name__ == "__main__":
    main()
