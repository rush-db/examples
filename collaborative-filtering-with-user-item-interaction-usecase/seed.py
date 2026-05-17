#!/usr/bin/env python3
"""
Seed script for collaborative filtering demo.

Generates mock users, items, and interactions, then imports them into RushDB.
Creates vector embeddings for item descriptions using sentence-transformers.

This script is IDEMPOTENT — safe to run multiple times.
It checks for existing data before creating new records.
"""

import os
import random
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from faker import Faker
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize Faker for realistic data generation
fake = Faker()
Faker.seed(42)
random.seed(42)

# Configuration
NUM_USERS = 30
NUM_ITEMS = 50
MIN_INTERACTIONS_PER_USER = 5
MAX_INTERACTIONS_PER_USER = 15
VECTOR_DIMENSIONS = 384  # all-MiniLM-L6-v2 output dimension

# Product categories for realistic item generation
PRODUCT_CATEGORIES = {
    "Electronics": {
        "items": [
            ("Wireless Bluetooth Headphones", "Premium noise-canceling wireless headphones with 30-hour battery life and crystal-clear audio quality"),
            ("Smart Watch Pro", "Advanced fitness tracking smartwatch with heart rate monitoring, GPS, and water resistance up to 50 meters"),
            ("Portable Power Bank", "20000mAh fast-charging portable charger with USB-C and wireless charging capabilities"),
            ("Mechanical Gaming Keyboard", "RGB backlit mechanical keyboard with Cherry MX switches and programmable macro keys"),
            ("4K Webcam", "Ultra HD webcam with autofocus, low-light correction, and built-in privacy shutter"),
            ("USB-C Hub 7-in-1", "Multi-port adapter with HDMI, USB-A, SD card reader, and ethernet connectivity"),
            ("Wireless Charging Pad", "Fast wireless charger compatible with all Qi-enabled devices and Apple Watch"),
            ("Noise Cancelling Earbuds", "True wireless earbuds with active noise cancellation and transparency mode"),
            ("Smart Home Speaker", "Voice-controlled smart speaker with premium sound and built-in assistant"),
            ("Portable SSD 1TB", "High-speed external solid-state drive with USB 3.2 and shock-resistant design"),
        ],
    },
    "Books": {
        "items": [
            ("The Art of Strategic Thinking", "Comprehensive guide to developing strategic thinking skills for business and personal growth"),
            ("Modern Python Cookbook", "Over 100 recipes for Python 3.9+ covering data structures, algorithms, and best practices"),
            ("The Neuroscience of Learning", "Understanding how the brain learns and retains information for effective education"),
            ("Startup Playbook", "Essential strategies for building and scaling a successful startup from zero to IPO"),
            ("Mindful Leadership", "A guide to leading with emotional intelligence, presence, and purpose"),
            ("Data Science Fundamentals", "Introduction to statistics, machine learning, and data visualization with Python"),
            ("The Productivity Blueprint", "Science-backed methods to maximize output while maintaining work-life balance"),
            ("Introduction to Philosophy", "Classic philosophical concepts and thinkers from ancient Greece to modern era"),
            ("The Creative Mind", "Exploring the psychology and neuroscience behind creativity and innovation"),
            ("Financial Freedom Guide", "Personal finance strategies for building wealth and achieving early retirement"),
        ],
    },
    "Home & Kitchen": {
        "items": [
            ("Instant Pot Duo Plus", "8-quart multi-use programmable pressure cooker with 15 built-in smart programs"),
            ("Robot Vacuum Cleaner", "Smart navigation robot vacuum with app control, mapping, and self-charging capability"),
            ("Espresso Machine", "Semi-automatic espresso maker with milk frother and built-in grinder"),
            ("Air Fryer XL", "Large capacity digital air fryer with 8 preset cooking programs and 360-degree circulation"),
            ("Smart Thermostat", "WiFi-enabled learning thermostat with energy reports and remote sensor support"),
            ("Stainless Steel Cookware Set", "10-piece premium cookware set with tri-ply construction and stay-cool handles"),
            (" countertop Ice Maker", "Portable ice maker producing 26 pounds of ice per day with self-cleaning function"),
            ("Bamboo Cutting Board Set", "Eco-friendly cutting boards with juice grooves and integrated storage"),
            ("Cast Iron Dutch Oven", "Enameled cast iron 6-quart dutch oven for slow cooking and baking"),
            ("High-Speed Blender", "Professional-grade blender with variable speed control and tamper for thick mixtures"),
        ],
    },
    "Sports & Outdoors": {
        "items": [
            ("Adjustable Dumbbell Set", "Space-saving adjustable dumbbells from 5 to 52.5 pounds with quick-change mechanism"),
            ("Yoga Mat Premium", "Extra-thick non-slip yoga mat with alignment lines and carrying strap"),
            ("Trail Running Shoes", "Lightweight breathable trail shoes with aggressive traction and rock plate protection"),
            ("Camping Hammock", "Ultralight parachute nylon hammock with tree straps and mosquito net"),
            ("Resistance Band Kit", "Complete set of resistance bands with handles, door anchor, and exercise guide"),
            ("Insulated Water Bottle", "32oz stainless steel water bottle keeping drinks cold 24 hours or hot 12 hours"),
            ("Foam Roller", "High-density muscle roller for self-myofascial release and recovery"),
            ("Trekking Poles", "Lightweight aluminum trekking poles with ergonomic cork grips and carbide tips"),
            ("Jump Rope Speed Rope", "Adjustable speed rope with ball bearings and memory wire for consistent rotation"),
            ("Pull-Up Bar Door Frame", "No-screw doorway pull-up bar with foam grips and multiple grip positions"),
        ],
    },
    "Clothing": {
        "items": [
            ("Merino Wool Base Layer", "Midweight thermal underwear top for hiking and cold weather activities"),
            ("Performance Running Shorts", "Lightweight running shorts with built-in liner and zippered pocket"),
            ("Cashmere Crew Sweater", "Luxury 100% cashmere sweater in classic fit with ribbed trim"),
            ("Waterproof Hiking Boots", "Full-grain leather hiking boots with Gore-Tex lining and Vibram soles"),
            ("Compression Socks", "Graduated compression socks for improved circulation and recovery"),
            ("Packable Down Jacket", "Ultra-lightweight 800-fill down jacket that compresses into its own pocket"),
            ("Moisture-Wicking T-Shirt", "Athletic performance tee with odor control and four-way stretch"),
            ("Fleece Zip Jacket", "Midlayer fleece jacket with zippered pockets and elastic hem"),
            ("Rain Pants", "Breathable waterproof hiking pants with articulated knees and ankle zippers"),
            ("Casual Canvas Sneakers", "Classic low-top sneakers in durable canvas with cushioned insole"),
        ],
    },
}

# Flatten all items
ALL_ITEMS = []
for category, data in PRODUCT_CATEGORIES.items():
    for name, description in data["items"]:
        ALL_ITEMS.append({
            "name": name,
            "description": description,
            "category": category,
        })


def check_existing_data(db: RushDB) -> dict:
    """Check if data already exists in the database."""
    existing = {
        "users": 0,
        "items": 0,
        "interactions": 0,
    }
    
    try:
        users_result = db.records.find({"labels": ["USER"], "limit": 1})
        existing["users"] = users_result.total
    except Exception:
        pass
    
    try:
        items_result = db.records.find({"labels": ["ITEM"], "limit": 1})
        existing["items"] = items_result.total
    except Exception:
        pass
    
    return existing


def generate_users(count: int) -> list[dict]:
    """Generate mock user data."""
    users = []
    for i in range(count):
        users.append({
            "userId": f"user_{i:04d}",
            "name": fake.name(),
            "email": fake.email(),
            "age_group": random.choice(["18-24", "25-34", "35-44", "45-54", "55+"]),
            "member_since": fake.date_between(start_date="-3y", end_date="today").isoformat(),
        })
    return users


def select_items_for_user() -> list[tuple[int, str, float]]:
    """
    Generate random item interactions for a user.
    Returns list of (item_index, interaction_type, weight) tuples.
    """
    interactions = []
    num_interactions = random.randint(MIN_INTERACTIONS_PER_USER, MAX_INTERACTIONS_PER_USER)
    
    # Select random items (with possible duplicates, but different interaction types)
    for _ in range(num_interactions):
        item_idx = random.randint(0, len(ALL_ITEMS) - 1)
        
        # Weight distribution: purchases are rare, ratings common, views most common
        roll = random.random()
        if roll < 0.1:  # 10% purchase
            interaction_type = "PURCHASED"
            weight = 3.0
        elif roll < 0.4:  # 30% rating
            interaction_type = "RATED"
            weight = random.uniform(1.0, 5.0)
        else:  # 60% view
            interaction_type = "VIEWED"
            weight = 0.5
        
        interactions.append((item_idx, interaction_type, weight))
    
    return interactions


def compute_embeddings(items: list[dict]) -> list[list[float]]:
    """Compute vector embeddings for item descriptions."""
    print("\n Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    descriptions = [item["description"] for item in items]
    print(f" Computing embeddings for {len(descriptions)} items...")
    
    embeddings = model.encode(descriptions, show_progress_bar=True)
    print(f" Generated {len(embeddings)} embeddings of dimension {VECTOR_DIMENSIONS}")
    
    return embeddings.tolist()


def create_vector_index(db: RushDB) -> str:
    """Create or get the vector index for item descriptions."""
    # Check if index already exists
    indexes = db.ai.indexes.find()
    for idx in indexes:
        if idx["label"] == "ITEM" and idx["propertyName"] == "description":
            print(f" Vector index already exists: {idx['__id']}")
            return idx["__id"]
    
    print(" Creating vector index for ITEM.description...")
    response = db.ai.indexes.create({
        "label": "ITEM",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": VECTOR_DIMENSIONS,
        "similarityFunction": "cosine",
    })
    
    index_id = response.data["__id"]
    print(f" Created vector index: {index_id}")
    return index_id


def seed_database(db: RushDB, force: bool = False) -> dict:
    """
    Seed the database with users, items, and interactions.
    
    Args:
        db: RushDB instance
        force: If True, skip check for existing data
    
    Returns:
        Dictionary with counts of created records
    """
    print("\n" + "="*60)
    print("RUSHDB COLLABORATIVE FILTERING - DATA SEEDING")
    print("="*60)
    
    # Check for existing data
    if not force:
        existing = check_existing_data(db)
        if existing["users"] > 0 or existing["items"] > 0:
            print(f"\n Data already exists: {existing['users']} users, {existing['items']} items")
            print(" Run with --force to re-seed, or continue to main.py")
            return {"skipped": True, **existing}
    
    # Generate data
    print(f"\n Generating {NUM_USERS} users...")
    users = generate_users(NUM_USERS)
    
    # Select items (we use all items but may not generate interactions for all)
    items = ALL_ITEMS[:NUM_ITEMS]
    
    # Compute embeddings
    embeddings = compute_embeddings(items)
    
    # Create vector index
    index_id = create_vector_index(db)
    
    # Import users in batches
    print(f"\n Creating {len(users)} users...")
    batch_size = 10
    created_users = []
    for i in range(0, len(users), batch_size):
        batch = users[i:i+batch_size]
        result = db.records.create_many(label="USER", data=batch)
        created_users.extend(result)
        print(f"  Created users {i+1}-{min(i+batch_size, len(users))}")
    
    # Import items with embeddings
    print(f"\n Creating {len(items)} items with vector embeddings...")
    batch_size = 10
    created_items = []
    for i in range(0, len(items), batch_size):
        batch_items = items[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]
        
        batch_data = []
        for item, embedding in zip(batch_items, batch_embeddings):
            batch_data.append({
                "itemId": f"item_{i + len(batch_data):04d}",
                **item,
            })
        
        vectors = [
            [{"propertyName": "description", "vector": emb}] 
            for emb in batch_embeddings
        ]
        
        result = db.records.create_many(
            label="ITEM", 
            data=batch_data,
            vectors=vectors
        )
        created_items.extend(result)
        print(f"  Created items {i+1}-{min(i+batch_size, len(items))}")
    
    # Create interactions
    print(f"\n Creating user-item interactions...")
    interaction_count = 0
    for user_idx, user_record in enumerate(created_users):
        interactions = select_items_for_user()
        
        for item_idx, interaction_type, weight in interactions:
            if item_idx < len(created_items):
                item_record = created_items[item_idx]
                
                db.records.attach(
                    source=user_record,
                    target=item_record,
                    options={
                        "type": interaction_type,
                        "direction": "out",
                        "data": {"weight": weight}
                    }
                )
                interaction_count += 1
        
        if (user_idx + 1) % 10 == 0:
            print(f"  Created interactions for {user_idx + 1}/{len(created_users)} users")
    
    # Upsert vectors to the index
    print(f"\n Indexing {len(created_items)} item vectors...")
    vector_items = [
        {"recordId": item.id, "vector": embedding}
        for item, embedding in zip(created_items, embeddings)
    ]
    
    batch_size = 25
    for i in range(0, len(vector_items), batch_size):
        batch = vector_items[i:i+batch_size]
        db.ai.indexes.upsert_vectors(index_id, {"items": batch})
        print(f"  Indexed vectors {i+1}-{min(i+batch_size, len(vector_items))}")
    
    print("\n" + "="*60)
    print("SEEDING COMPLETE")
    print("="*60)
    print(f"  Users: {len(created_users)}")
    print(f"  Items: {len(created_items)}")
    print(f"  Interactions: {interaction_count}")
    print(f"  Vector embeddings: {len(embeddings)}")
    
    return {
        "users": len(created_users),
        "items": len(created_items),
        "interactions": interaction_count,
        "index_id": index_id,
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed RushDB with collaborative filtering data")
    parser.add_argument("--force", action="store_true", help="Force re-seed (delete existing data first)")
    args = parser.parse_args()
    
    # Initialize RushDB
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        exit(1)
    
    url = os.environ.get("RUSHDB_URL")
    if url:
        db = RushDB(api_key, url=url)
    else:
        db = RushDB(api_key)
    
    result = seed_database(db, force=args.force)
    
    if not result.get("skipped"):
        # Print index stats
        index_id = result.get("index_id")
        if index_id:
            stats = db.ai.indexes.stats(index_id)
            print(f"\nVector Index Stats:")
            print(f"  Indexed: {stats.data.get('indexedRecords', 'N/A')} / {stats.data.get('totalRecords', 'N/A')} records")
