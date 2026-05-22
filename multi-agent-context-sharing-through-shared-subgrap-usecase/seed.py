#!/usr/bin/env python3
"""
Seed script for multi-agent context sharing demo.

Creates a realistic e-commerce subgraph structure with:
- Users with preferences
- Order history
- Active sessions
- Agent result records

This data represents the "shared subgraph" that multiple agents will read/write.

Run: python seed.py
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB

# Load sample data
DATA_DIR = Path(__file__).parent / "data"
SAMPLE_USERS_PATH = DATA_DIR / "sample_users.json"

# Realistic order data for e-commerce
ORDER_ITEMS = [
    {"sku": "ELEC-001", "name": "Wireless Earbuds Pro", "price": 149.99},
    {"sku": "ELEC-002", "name": "Smart Watch Series 5", "price": 349.99},
    {"sku": "CLTH-001", "name": "Merino Wool Sweater", "price": 89.99},
    {"sku": "CLTH-002", "name": "Technical Running Jacket", "price": 129.99},
    {"sku": "HOME-001", "name": "Smart Thermostat Hub", "price": 199.99},
    {"sku": "HOME-002", "name": "Robot Vacuum Pro", "price": 449.99},
    {"sku": "BOOK-001", "name": "Design Patterns Guide", "price": 49.99},
    {"sku": "ACC-001", "name": "Leather Laptop Sleeve", "price": 59.99},
]

ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "completed", "cancelled"]


def load_sample_users():
    """Load sample user data from JSON file."""
    with open(SAMPLE_USERS_PATH, "r") as f:
        return json.load(f)


def generate_order_history(user_id: str, count: int = None):
    """Generate random order history for a user."""
    if count is None:
        count = random.randint(2, 8)
    
    orders = []
    base_date = datetime.now() - timedelta(days=random.randint(90, 365))
    
    for i in range(count):
        num_items = random.randint(1, 4)
        items = random.sample(ORDER_ITEMS, num_items)
        
        subtotal = sum(item["price"] for item in items)
        shipping = 0 if subtotal > 100 else 9.99
        tax = round(subtotal * 0.08, 2)
        total = round(subtotal + shipping + tax, 2)
        
        # Status weighted towards completed for older orders
        days_ago = (datetime.now() - base_date).days
        if days_ago > 60:
            status = "completed" if random.random() > 0.1 else "delivered"
        else:
            status = random.choice(ORDER_STATUSES[:4])
        
        order = {
            "user_id": user_id,
            "order_number": f"ORD-{random.randint(100000, 999999)}",
            "items": items,
            "item_count": num_items,
            "subtotal": subtotal,
            "shipping_cost": shipping,
            "tax": tax,
            "total": total,
            "status": status,
            "shipping_address": {
                "street": f"{random.randint(100, 9999)} Main St",
                "city": random.choice(["San Francisco", "New York", "Austin", "Seattle", "Denver"]),
                "state": random.choice(["CA", "NY", "TX", "WA", "CO"]),
                "zip": f"{random.randint(10000, 99999)}",
            },
            "created_at": (base_date + timedelta(days=i * random.randint(7, 21))).isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        orders.append(order)
    
    return orders


def seed_database():
    """Seed the database with user context subgraphs."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("❌ RUSHDB_API_KEY not found in environment")
        print("   Please copy .env.example to .env and add your API key")
        sys.exit(1)
    
    print("🚀 Connecting to RushDB...")
    db = RushDB(api_key)
    
    # Check for existing data
    existing = db.records.find({"labels": ["_SEED_MARKER"], "limit": 1})
    if existing.data:
        print("✅ Database already seeded (found marker record)")
        print("   To re-seed, delete existing records first")
        return
    
    print("📦 Loading sample user data...")
    sample_users = load_sample_users()
    
    print(f"\n{'='*60}")
    print("SEEDING USER CONTEXT SUBGRAPHS")
    print(f"{'='*60}\n")
    
    total_records = 0
    total_relationships = 0
    start_time = time.time()
    
    for idx, user_data in enumerate(sample_users, 1):
        print(f"\n[{idx}/{len(sample_users)}] Creating subgraph for: {user_data['name']}")
        
        # Generate order history
        orders = generate_order_history(user_data["id"])
        
        try:
            with db.transactions.begin() as tx:
                # 1. Create USER record
                user = db.records.create(
                    label="USER",
                    data={
                        "external_id": user_data["id"],
                        "name": user_data["name"],
                        "email": user_data["email"],
                        "age": user_data["age"],
                        "tier": user_data["tier"],
                        "account_status": user_data["account_status"],
                    },
                    transaction=tx,
                )
                print(f"   ✓ Created USER: {user.id}")
                
                # 2. Create PREFERENCES record
                prefs = db.records.create(
                    label="PREFERENCES",
                    data=user_data["preferences"],
                    transaction=tx,
                )
                print(f"   ✓ Created PREFERENCES: {prefs.id}")
                
                # 3. Link USER → PREFERENCES
                db.records.attach(
                    source=user,
                    target=prefs,
                    options={"type": "HAS_PREFERENCES"},
                    transaction=tx,
                )
                print(f"   ✓ Linked USER → HAS_PREFERENCES → PREFERENCES")
                total_relationships += 1
                
                # 4. Create SESSION record (current active session)
                session = db.records.create(
                    label="SESSION",
                    data={
                        "external_user_id": user_data["id"],
                        "started_at": datetime.now().isoformat(),
                        "status": "active",
                        "agent": "triage",
                        "intent": "pending",
                    },
                    transaction=tx,
                )
                print(f"   ✓ Created SESSION: {session.id}")
                
                # 5. Link USER → SESSION
                db.records.attach(
                    source=user,
                    target=session,
                    options={"type": "HAS_SESSION"},
                    transaction=tx,
                )
                print(f"   ✓ Linked USER → HAS_SESSION → SESSION")
                total_relationships += 1
                
                # 6. Create ORDER records and link them
                for order in orders:
                    order_record = db.records.create(
                        label="ORDER",
                        data=order,
                        transaction=tx,
                    )
                    total_records += 1
                    
                    # Link USER → ORDER
                    db.records.attach(
                        source=user,
                        target=order_record,
                        options={"type": "PLACED"},
                        transaction=tx,
                    )
                    total_relationships += 1
                
                print(f"   ✓ Created {len(orders)} ORDERS with relationships")
                total_records += len(orders) + 2  # +2 for USER and PREFERENCES
                
        except Exception as e:
            print(f"   ❌ Error creating subgraph: {e}")
            raise
        
        # Progress indicator
        if idx % 100 == 0:
            print(f"   ... {idx} users processed")
        
        total_records += 1  # SESSION
    
    # Create a marker record to indicate seeding is complete
    db.records.create(
        label="_SEED_MARKER",
        data={"seeded_at": datetime.now().isoformat(), "version": "1.0.0"},
    )
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("SEEDING COMPLETE")
    print(f"{'='*60}")
    print(f"   Records created:    {total_records}")
    print(f"   Relationships:      {total_relationships}")
    print(f"   Time elapsed:       {elapsed:.2f}s")
    print(f"\n   Users ready for multi-agent demo:")
    for user in sample_users:
        print(f"   - {user['name']} ({user['email']})")
    print()


if __name__ == "__main__":
    seed_database()
