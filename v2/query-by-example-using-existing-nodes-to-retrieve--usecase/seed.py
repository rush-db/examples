#!/usr/bin/env python3
"""
Seed script for Query-by-Example tutorial.

Creates a user behavior graph with:
- 50 users (mix of premium and regular)
- 20 products across 3 categories
- Purchase history forming graph relationships
- One high-value "target" user for QBE demonstration

This script is idempotent — safe to run multiple times.
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Initialize
fake = Faker()
Faker.seed(42)
random.seed(42)

# Product catalog
PRODUCT_CATALOG = [
    {"name": "MacBook Pro 14"", "price": 1999.99, "category": "Electronics"},
    {"name": "iPhone 15 Pro"", "price": 999.99, "category": "Electronics"},
    {"name": "Sony WH-1000XM5"", "price": 349.99, "category": "Electronics"},
    {"name": "Canon EOS R50"", "price": 679.99, "category": "Electronics"},
    {"name": "iPad Air"", "price": 599.99, "category": "Electronics"},
    {"name": "Apple Watch Ultra"", "price": 799.99, "category": "Electronics"},
    {"name": "Logitech MX Keys"", "price": 99.99, "category": "Accessories"},
    {"name": "Dell UltraSharp 27\"", "price": 549.99, "category": "Electronics"},
    {"name": "Logitech MX Master 3S"", "price": 99.99, "category": "Accessories"},
    {"name": "Sonos One SL"", "price": 219.99, "category": "Electronics"},
    {"name": "Logitech C920 Webcam"", "price": 79.99, "category": "Accessories"},
    {"name": "HP LaserJet Pro"", "price": 299.99, "category": "Electronics"},
    {"name": "ASUS RT-AX86U"", "price": 229.99, "category": "Electronics"},
    {"name": "Samsung 970 EVO 1TB"", "price": 89.99, "category": "Accessories"},
    {"name": "Corsair Vengeance 32GB"", "price": 109.99, "category": "Accessories"},
    {"name": "Anker 777 Charger"", "price": 49.99, "category": "Accessories"},
    {"name": "Anker USB-C Cable Pack"", "price": 19.99, "category": "Accessories"},
    {"name": "Rain Design mStack Stand"", "price": 69.99, "category": "Accessories"},
    {"name": "BenQ ScreenBar Plus"", "price": 199.99, "category": "Accessories"},
    {"name": "Autonomous SmartDesk Pro"", "price": 549.99, "category": "Office"},
]

# Premium product indices (for high-value users)
PREMIUM_PRODUCTS = [0, 1, 2, 3, 4, 5, 7, 9]  # Higher-priced items


def create_product_index(db: RushDB) -> dict:
    """Create or verify vector index for product embeddings."""
    # Check for existing index
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx["label"] == "PRODUCT" and idx["propertyName"] == "description_embedding":
            print("  ✓ Product embedding index already exists")
            return idx

    # Create new index (external type since we provide our own vectors)
    print("  Creating product embedding index...")
    index = db.ai.indexes.create({
        "label": "PRODUCT",
        "propertyName": "description_embedding",
        "sourceType": "external",
        "dimensions": 384,  # Using all-MiniLM-L6-v2 dimension
        "similarityFunction": "cosine"
    })
    return index


def create_user_index(db: RushDB) -> dict:
    """Create or verify vector index for user behavior profiles."""
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx["label"] == "USER" and idx["propertyName"] == "behavior_profile":
            print("  ✓ User behavior profile index already exists")
            return idx

    print("  Creating user behavior profile index...")
    index = db.ai.indexes.create({
        "label": "USER",
        "propertyName": "behavior_profile",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    return index


def generate_embedding(seed: int) -> list:
    """Generate a deterministic pseudo-embedding for demo purposes."""
    random.seed(seed)
    # Normalized random vector
    vec = [random.uniform(-1, 1) for _ in range(384)]
    magnitude = sum(x**2 for x in vec) ** 0.5
    return [x / magnitude for x in vec]


def main():
    print("\n=== RushDB QBE Tutorial: Data Seeding ===\n")

    # Check for API key
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment.")
        print("Please create a .env file with your API key (see .env.example)")
        return

    # Connect to RushDB
    print("Connecting to RushDB...")
    db = RushDB(api_key)
    print("  ✓ Connected\n")

    # Check existing data
    existing_users = db.records.find({"labels": ["USER"], "limit": 1})
    if existing_users.data:
        print("Data already exists. Skipping seed (idempotent behavior).")
        print(f"  Found {len(existing_users.data)} user(s) — seed skipped.\n")
        return

    # Setup vector indexes
    print("Setting up vector indexes...")
    product_index = create_product_index(db)
    user_index = create_user_index(db)
    print("  ✓ Vector indexes ready\n")

    # Create products
    print("Creating products...")
    products = []
    for i, prod_data in enumerate(PRODUCT_CATALOG):
        product = db.records.create(label="PRODUCT", data={
            "name": prod_data["name"],
            "price": prod_data["price"],
            "category": prod_data["category"],
            "description": f"{prod_data['name']} - {prod_data['category']} product",
        })
        products.append(product)
        
        # Add embedding vector
        db.ai.indexes.upsert_vectors(product_index.id, {
            "items": [{
                "recordId": product.id,
                "vector": generate_embedding(i + 100)
            }]
        })

    print(f"  ✓ Created {len(products)} products\n")

    # Create users with varying behavior patterns
    print("Creating users and purchase history...")
    target_user_created = False

    for user_num in range(50):
        # First few users are premium (for QBE demonstration)
        is_premium = user_num < 15
        
        # Determine join date (spread over last 2 years)
        days_ago = random.randint(0, 730)
        join_date = datetime.now() - timedelta(days=days_ago)

        # Create user
        user = db.records.create(label="USER", data={
            "name": fake.name(),
            "email": fake.email(),
            "join_date": join_date.isoformat(),
            "is_premium": is_premium,
            "account_age_days": days_ago,
        })

        # Generate behavior profile embedding based on user type
        if is_premium:
            profile_seed = 1  # Premium profile vector
        else:
            profile_seed = 2  # Regular profile vector

        behavior_vector = generate_embedding(profile_seed * 100 + user_num)

        # Add user to vector index
        db.ai.indexes.upsert_vectors(user_index.id, {
            "items": [{
                "recordId": user.id,
                "vector": behavior_vector
            }]
        })

        # Determine number of purchases (premium users buy more)
        if is_premium:
            num_purchases = random.randint(8, 15)
            product_pool = list(range(20))  # Can buy any product
        else:
            num_purchases = random.randint(1, 5)
            product_pool = [i for i in range(20) if i not in PREMIUM_PRODUCTS] + [6, 9]  # Fewer premium

        if not product_pool:
            product_pool = list(range(20))

        # Create purchases
        total_spent = 0.0
        purchase_count = 0
        purchase_dates = []

        for purchase_idx in range(num_purchases):
            product = random.choice(products)
            
            # Price varies slightly
            amount = round(product.data["price"] * random.uniform(0.85, 1.15), 2)
            
            # Purchase date spread over account lifetime
            purchase_days_ago = random.randint(0, min(days_ago, 365))
            purchase_date = datetime.now() - timedelta(days=purchase_days_ago)
            purchase_dates.append(purchase_date)

            # Create purchase within transaction
            with db.transactions.begin() as tx:
                purchase = db.records.create(label="PURCHASE", data={
                    "amount": amount,
                    "date": purchase_date.isoformat(),
                    "status": random.choices(
                        ["completed", "pending", "refunded"],
                        weights=[85, 10, 5]
                    )[0],
                }, transaction=tx)

                # Attach relationships
                db.records.attach(source=user, target=purchase, options={"type": "MADE"}, transaction=tx)
                db.records.attach(source=purchase, target=product, options={"type": "INCLUDES"}, transaction=tx)

            total_spent += amount
            purchase_count += 1

        # Update user with computed fields
        db.records.update(record_id=user.id, data={
            "lifetime_value": round(total_spent, 2),
            "purchase_count": purchase_count,
            "avg_order_value": round(total_spent / purchase_count, 2) if purchase_count > 0 else 0,
            "last_purchase_date": max(purchase_dates).isoformat() if purchase_dates else None,
        })

        # Mark first premium user as target (high-value demonstration)
        if is_premium and not target_user_created:
            db.records.update(record_id=user.id, data={
                "is_target": True,
                "notes": "High-value user for QBE demonstration"
            })
            target_user_created = True
            print(f"  ✓ Created TARGET user: {user.data['name']} (LTV: ${total_spent:.2f})")

        if (user_num + 1) % 10 == 0:
            print(f"  Created {user_num + 1}/50 users...")

    print(f"\n  ✓ Created 50 users with purchase history\n")

    # Create fraud pattern for anomaly detection demo
    print("Creating fraud pattern...")
    fraud_user = db.records.create(label="USER", data={
        "name": "Fraudulent Actor",
        "email": "fraud_detected@example.com",
        "account_age_days": 5,
        "prior_chargebacks": 3,
        "is_suspicious": True,
    })

    with db.transactions.begin() as tx:
        fraud_order = db.records.create(label="FRAUD_CASE", data={
            "amount": 2499.99,
            "date": datetime.now().isoformat(),
            "status": "confirmed",
            "risk_score": 0.95,
            "pattern_type": "high_value_new_account",
        }, transaction=tx)
        db.records.attach(source=fraud_user, target=fraud_order, options={"type": "COMMITTED"}, transaction=tx)

    print("  ✓ Fraud pattern created")

    # Create some similar suspicious orders
    for i in range(3):
        with db.transactions.begin() as tx:
            suspicious = db.records.create(label="PURCHASE", data={
                "amount": round(random.uniform(2200, 2600), 2),
                "date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "status": "pending",
                "risk_flags": ["new_account", "high_value", "rapid_sequence"],
            }, transaction=tx)

            # Create suspicious users for these orders
            sus_user = db.records.create(label="USER", data={
                "name": fake.name(),
                "email": fake.email(),
                "account_age_days": random.randint(3, 30),
                "prior_chargebacks": random.randint(1, 2),
            }, transaction=tx)

            db.records.attach(source=sus_user, target=suspicious, options={"type": "MADE"}, transaction=tx)

    print("  ✓ 3 suspicious transactions created")

    print("\n=== Seed Complete ===\n")
    print("Next: Run `python main.py` to execute the QBE demonstration.\n")


if __name__ == "__main__":
    main()
