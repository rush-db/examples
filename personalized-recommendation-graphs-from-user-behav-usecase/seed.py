"""
Seed script for personalized recommendation demo.

Generates mock data:
- 50 users with embedding vectors
- 200 items across 5 categories with embedding vectors  
- 300+ clickstream sessions with 3-10 events each

This script is idempotent - safe to run multiple times.
"""

import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

import numpy as np
from faker import Faker

# Load environment
load_dotenv()

# Import RushDB
from rushdb import RushDB

# Initialize
fake = Faker()
random.seed(42)
np.random.seed(42)

# Configuration
NUM_USERS = 50
NUM_ITEMS = 200
NUM_SESSIONS = 100
VECTOR_DIM = 128
CATEGORIES = ["Electronics", "Clothing", "Books", "Home", "Sports"]

# Helper: Generate random embedding vector
def random_vector(dim: int = VECTOR_DIM) -> list:
    """Generate a random normalized vector."""
    vec = np.random.randn(dim)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()

# Helper: Get or create index, create if needed
def ensure_vector_index(db: RushDB, label: str, property_name: str = "embedding", dims: int = VECTOR_DIM):
    """Ensure vector index exists for a label/property combination."""
    try:
        existing = db.ai.indexes.find()
        for idx in existing.data if hasattr(existing, 'data') else []:
            if idx.get('label') == label and idx.get('propertyName') == property_name:
                return idx
        
        # Create new index
        index = db.ai.indexes.create({
            "label": label,
            "propertyName": property_name,
            "sourceType": "external",
            "dimensions": dims,
            "similarityFunction": "cosine"
        })
        print(f"  Created vector index for {label}.{property_name}")
        return index
    except Exception as e:
        print(f"  Index check/creation note: {e}")
        return None

def clear_existing_data(db: RushDB):
    """Clear all existing data for a fresh start."""
    print("Clearing existing data...")
    labels = ["USER", "ITEM", "SESSION", "CLICK_EVENT", "CATEGORY"]
    for label in labels:
        try:
            db.records.delete({"labels": [label], "where": {}})
        except Exception:
            pass
    time.sleep(1)  # Allow deletion to propagate

def seed_users(db: RushDB) -> list:
    """Create users with embedding vectors."""
    print(f"\nCreating {NUM_USERS} users with embedding vectors...")
    users = []
    
    for i in range(NUM_USERS):
        vector = random_vector()
        
        user = db.records.create(
            label="USER",
            data={
                "userId": f"user_{i}",
                "username": fake.user_name(),
                "email": fake.email(),
                "registeredAt": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
            },
            vectors=[{"propertyName": "embedding", "vector": vector}]
        )
        users.append(user)
        
        if (i + 1) % 50 == 0:
            print(f"  Created {i + 1}/{NUM_USERS} users")
    
    print(f"  Created {len(users)} users")
    return users

def seed_categories(db: RushDB) -> list:
    """Create category nodes."""
    print(f"\nCreating {len(CATEGORIES)} categories...")
    categories = []
    
    for category_name in CATEGORIES:
        category = db.records.create(
            label="CATEGORY",
            data={
                "name": category_name,
                "popularity": random.randint(50, 100)
            }
        )
        categories.append(category)
    
    return categories

def seed_items(db: RushDB, categories: list) -> list:
    """Create items with embedding vectors across categories."""
    print(f"\nCreating {NUM_ITEMS} items with embedding vectors...")
    items = []
    
    items_per_category = NUM_ITEMS // len(CATEGORIES)
    
    for cat_idx, category in enumerate(categories):
        for i in range(items_per_category):
            item_idx = cat_idx * items_per_category + i
            
            # Items in same category have similar embeddings (clustered)
            base_vector = np.random.randn(VECTOR_DIM)
            base_vector = base_vector / np.linalg.norm(base_vector)
            # Add category-specific bias
            category_offset = np.zeros(VECTOR_DIM)
            category_offset[cat_idx * (VECTOR_DIM // len(CATEGORIES)):][:20] = 0.5
            vector = (base_vector + category_offset)
            vector = vector / np.linalg.norm(vector)
            
            item = db.records.create(
                label="ITEM",
                data={
                    "itemId": f"item_{item_idx}",
                    "name": fake.catch_phrase(),
                    "category": category.data["name"],
                    "price": round(random.uniform(9.99, 299.99), 2),
                    "rating": round(random.uniform(3.5, 5.0), 1)
                },
                vectors=[{"propertyName": "embedding", "vector": vector.tolist()}]
            )
            
            # Link item to category
            db.records.attach(
                source=item,
                target=category,
                options={"type": "BELONGS_TO"}
            )
            
            items.append(item)
            
            if (item_idx + 1) % 50 == 0:
                print(f"  Created {item_idx + 1}/{NUM_ITEMS} items")
    
    print(f"  Created {len(items)} items")
    return items

def seed_sessions(db: RushDB, users: list, items: list):
    """Create sessions with clickstream events."""
    print(f"\nCreating {NUM_SESSIONS} sessions with clickstream events...")
    
    sessions_created = 0
    events_created = 0
    
    for user in users:
        # Each user has 1-5 sessions
        num_sessions = random.randint(1, 5)
        
        for _ in range(num_sessions):
            # Create session
            session = db.records.create(
                label="SESSION",
                data={
                    "sessionId": f"session_{user.data['userId']}_{sessions_created}",
                    "startedAt": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    "deviceType": random.choice(["desktop", "mobile", "tablet"])
                }
            )
            
            # Link user to session
            db.records.attach(
                source=user,
                target=session,
                options={"type": "HAS_SESSION"}
            )
            
            # Create click events (3-10 per session)
            num_clicks = random.randint(3, 10)
            clicked_items = random.sample(items, min(num_clicks, len(items)))
            
            for clicked_item in clicked_items:
                event = db.records.create(
                    label="CLICK_EVENT",
                    data={
                        "eventId": f"event_{events_created}",
                        "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 720))).isoformat(),
                        "durationMs": random.randint(500, 30000),
                        "action": random.choice(["view", "click", "add_to_cart"])
                    }
                )
                
                # Link session to click event
                db.records.attach(
                    source=session,
                    target=event,
                    options={"type": "CONTAINS"}
                )
                
                # Link click event to item
                db.records.attach(
                    source=event,
                    target=clicked_item,
                    options={"type": "REFERENCES"}
                )
                
                events_created += 1
            
            sessions_created += 1
            
            if sessions_created % 50 == 0:
                print(f"  Created {sessions_created} sessions, {events_created} click events")
    
    print(f"  Created {sessions_created} sessions, {events_created} click events")

def main():
    """Main seeding function."""
    print("=" * 60)
    print("Personalized Recommendation System - Data Seeding")
    print("=" * 60)
    
    # Get API key
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\nERROR: RUSHDB_API_KEY not found in environment.")
        print("Copy .env.example to .env and add your API key.")
        return
    
    # Connect to RushDB
    print("\nConnecting to RushDB...")
    db = RushDB(api_key)
    print("Connected successfully!")
    
    # Clear existing data for fresh start
    clear_existing_data(db)
    
    # Ensure vector indexes exist
    print("\nEnsuring vector indexes exist...")
    ensure_vector_index(db, "USER", "embedding")
    ensure_vector_index(db, "ITEM", "embedding")
    
    # Seed data
    print("\n" + "-" * 40)
    print("Starting data generation...")
    print("-" * 40)
    
    start_time = time.time()
    
    users = seed_users(db)
    categories = seed_categories(db)
    items = seed_items(db, categories)
    seed_sessions(db, users, items)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"Seeding complete in {elapsed:.1f}s")
    print(f"  - {len(users)} users")
    print(f"  - {len(categories)} categories")
    print(f"  - {len(items)} items")
    print("=" * 60)

if __name__ == "__main__":
    main()
