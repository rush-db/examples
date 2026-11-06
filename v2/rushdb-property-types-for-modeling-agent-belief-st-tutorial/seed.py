#!/usr/bin/env python3
"""
Seed script for RushDB Property Types Tutorial

This script seeds the database with initial belief records.
It's idempotent - safe to run multiple times.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError(
        "RUSHDB_API_KEY not found in environment. "
        "Copy .env.example to .env and add your API key."
    )

db = RushDB(api_key)

def seed_beliefs():
    """Seed initial belief records into RushDB."""
    
    print("\n=== Seeding Belief Records ===\n")
    
    # Load belief data from JSON file
    data_file = Path(__file__).parent / "data" / "beliefs.json"
    with open(data_file, "r") as f:
        beliefs_data = json.load(f)
    
    # Check if we already have beliefs in the database
    existing = db.records.find({"labels": ["BELIEF"], "limit": 1})
    
    if existing.total > 0:
        print(f"Found {existing.total} existing BELIEF record(s). Skipping seed.")
        print("Run 'python main.py' to see the existing data in action.")
        return
    
    # Create beliefs in batches
    print(f"Creating {len(beliefs_data)} belief records...")
    
    created_count = 0
    for i, belief_data in enumerate(beliefs_data, 1):
        try:
            db.records.create(label="BELIEF", data=belief_data)
            created_count += 1
            
            if i % 100 == 0:
                print(f"  Created {i}/{len(beliefs_data)} records...")
                
        except Exception as e:
            print(f"  Warning: Failed to create belief at index {i}: {e}")
    
    print(f"\n✓ Successfully seeded {created_count} belief records\n")
    
    # Print summary
    all_beliefs = db.records.find({"labels": ["BELIEF"]})
    print(f"Total BELIEF records in database: {all_beliefs.total}")

def clear_beliefs():
    """Clear all belief records (for testing/reset)."""
    print("\n=== Clearing Belief Records ===\n")
    
    result = db.records.delete_many({
        "labels": ["BELIEF"],
        "where": {}
    })
    
    print(f"✓ Deleted all BELIEF records\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_beliefs()
    else:
        seed_beliefs()
