"""
seed.py — Initializes the e-commerce dataset with V1 schema.

Creates:
  - CATEGORY_V1, PRODUCT_V1, USER_V1, ORDER_V1 records
  - SCHEMA_VERSION registry record
  - Initial MIGRATION audit record

Idempotent: safe to run multiple times. Detects existing data
and skips re-seeding.
"""

import os
from datetime import datetime, timezone
import random

from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()
db = RushDB(os.environ["RUSHDB_API_KEY"])


def seed_categories():
    """Seed 4 top-level categories."""
    categories = [
        {"name": "Electronics", "slug": "electronics", "parent": None},
        {"name": "Clothing", "slug": "clothing", "parent": None},
        {"name": "Home & Garden", "slug": "home-garden", "parent": None},
        {"name": "Sports", "slug": "sports", "parent": None},
    ]
    created = []
    for cat_data in categories:
        cat = db.records.upsert(
            label="CATEGORY_V1",
            data={"version": "1.0", **cat_data},
            options={"mergeBy": ["slug"]},
        )
        created.append(cat)
    print(f"  [seed] CATEGORY_V1: {len(created)} records")
    return created


def seed_products(categories):
    """Seed 20 products across 4 categories."""
    products = [
        # Electronics
        {"sku": "ELEC-001", "name": "Wireless Headphones", "price": 79.99, "stock": 45, "weight_kg": 0.25, "tags": ["audio", "wireless"]},
        {"sku": "ELEC-002", "name": "USB-C Hub 7-port", "price": 49.99, "stock": 120, "weight_kg": 0.18, "tags": ["accessories", "connectivity"]},
        {"sku": "ELEC-003", "name": "Mechanical Keyboard", "price": 129.99, "stock": 30, "weight_kg": 0.85, "tags": ["peripherals", "gaming"]},
        {"sku": "ELEC-004", "name": "4K Webcam", "price": 89.99, "stock": 55, "weight_kg": 0.22, "tags": ["video", "streaming"]},
        {"sku": "ELEC-005", "name": "Portable SSD 1TB", "price": 109.99, "stock": 80, "weight_kg": 0.06, "tags": ["storage", "portable"]},
        # Clothing
        {"sku": "CLTH-001", "name": "Merino Wool Sweater", "price": 89.00, "stock": 25, "weight_kg": 0.40, "tags": ["wool", "winter"]},
        {"sku": "CLTH-002", "name": "Running Shorts", "price": 34.99, "stock": 60, "weight_kg": 0.15, "tags": ["sports", "running"]},
        {"sku": "CLTH-003", "name": "Waterproof Jacket", "price": 149.99, "stock": 40, "weight_kg": 0.55, "tags": ["outdoor", "waterproof"]},
        {"sku": "CLTH-004", "name": "Canvas Sneakers", "price": 59.99, "stock": 90, "weight_kg": 0.35, "tags": ["casual", "footwear"]},
        {"sku": "CLTH-005", "name": "Yoga Leggings", "price": 44.99, "stock": 75, "weight_kg": 0.20, "tags": ["yoga", "fitness"]},
        # Home & Garden
        {"sku": "HOME-001", "name": "Cast Iron Dutch Oven", "price": 119.99, "stock": 35, "weight_kg": 4.20, "tags": ["cookware", "cast-iron"]},
        {"sku": "HOME-002", "name": "Bamboo Cutting Board", "price": 29.99, "stock": 100, "weight_kg": 0.80, "tags": ["kitchen", "bamboo"]},
        {"sku": "HOME-003", "name": "LED Grow Light", "price": 69.99, "stock": 50, "weight_kg": 0.45, "tags": ["gardening", "grow"]},
        {"sku": "HOME-004", "name": "Stainless Cookware Set", "price": 199.99, "stock": 20, "weight_kg": 8.50, "tags": ["cookware", "stainless-steel"]},
        {"sku": "HOME-005", "name": "Smart Thermostat", "price": 159.99, "stock": 45, "weight_kg": 0.30, "tags": ["smart-home", "thermostat"]},
        # Sports
        {"sku": "SPRT-001", "name": "Carbon Fiber Road Bike", "price": 2499.00, "stock": 8, "weight_kg": 7.20, "tags": ["cycling", "road"]},
        {"sku": "SPRT-002", "name": "Foam Roller", "price": 24.99, "stock": 150, "weight_kg": 0.60, "tags": ["recovery", "mobility"]},
        {"sku": "SPRT-003", "name": "Adjustable Dumbbells", "price": 349.99, "stock": 15, "weight_kg": 25.00, "tags": ["strength", "home-gym"]},
        {"sku": "SPRT-004", "name": "Road Cycling Helmet", "price": 129.99, "stock": 35, "weight_kg": 0.28, "tags": ["safety", "cycling"]},
        {"sku": "SPRT-005", "name": "Resistance Bands Set", "price": 19.99, "stock": 200, "weight_kg": 0.35, "tags": ["strength", "portable"]},
    ]

    created = []
    for i, prod_data in enumerate(products):
        cat = random.choice(categories)
        record = db.records.upsert(
            label="PRODUCT_V1",
            data={
                "version": "1.0",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **prod_data,
                "category_id": cat.id,
            },
            options={"mergeBy": ["sku"]},
        )
        if i % 100 == 0:
            print(f"  [seed] PRODUCT_V1: {i}/{len(products)} records")

        # Attach to category
        db.records.attach(
            source=record,
            target=cat,
            options={"type": "BELONGS_TO", "direction": "out"},
        )
        created.append(record)

    print(f"  [seed] PRODUCT_V1: {len(created)} records created")
    return created


def seed_users():
    """Seed 50 users across the US."""
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
              "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer",
                   "Michael", "Linda", "William", "Barbara", "David", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez"]

    created = []
    for i in range(50):
        user = db.records.upsert(
            label="USER_V1",
            data={
                "version": "1.0",
                "email": f"user{i}@example.com",
                "full_name": f"{random.choice(first_names)} {random.choice(last_names)}",
                "city": random.choice(cities),
                "loyalty_tier": random.choice(["bronze", "silver", "gold", "platinum"]),
                "account_created": datetime.now(timezone.utc).isoformat(),
            },
            options={"mergeBy": ["email"]},
        )
        if i % 100 == 0:
            print(f"  [seed] USER_V1: {i}/50 records")
        created.append(user)

    print(f"  [seed] USER_V1: {len(created)} records")
    return created


def seed_orders(users, products):
    """Seed 40 orders with user-product relationships."""
    statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    created = []
    for i in range(40):
        order_products = random.sample(products, k=random.randint(1, 3))
        total = sum(p.data["price"] for p in order_products)

        order = db.records.upsert(
            label="ORDER_V1",
            data={
                "version": "1.0",
                "order_number": f"ORD-2024-{i+1:04d}",
                "status": random.choice(statuses),
                "total_usd": round(total + random.uniform(5, 15), 2),
                "item_count": len(order_products),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            options={"mergeBy": ["order_number"]},
        )

        # Attach to user
        user = random.choice(users)
        db.records.attach(
            source=order,
            target=user,
            options={"type": "PLACED_BY", "direction": "in"},
        )

        # Attach to each product
        for prod in order_products:
            db.records.attach(
                source=prod,
                target=order,
                options={"type": "ORDERED_IN", "direction": "out"},
            )

        created.append(order)

    print(f"  [seed] ORDER_V1: {len(created)} records")
    return created


def create_schema_registry():
    """Create or update the central SCHEMA_VERSION registry record."""
    registry = db.records.upsert(
        label="SCHEMA_VERSION",
        data={
            "schema_version": "1.0.0",
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "active_labels": {
                "PRODUCT": "PRODUCT_V1",
                "CATEGORY": "CATEGORY_V1",
                "USER": "USER_V1",
                "ORDER": "ORDER_V1",
            },
            "deprecated_labels": {},
            "migrations_applied": ["init_v1"],
        },
        options={"mergeBy": ["schema_version"]},
    )
    print(f"  [seed] SCHEMA_VERSION registry updated")
    return registry


def create_initial_migration():
    """Create the initial migration record as an audit trail entry."""
    migration = db.records.upsert(
        label="MIGRATION",
        data={
            "migration_id": "init_v1",
            "from_version": None,
            "to_version": "1.0.0",
            "description": "Initial schema deployment",
            "status": "completed",
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "affected_labels": ["PRODUCT_V1", "CATEGORY_V1", "USER_V1", "ORDER_V1"],
        },
        options={"mergeBy": ["migration_id"]},
    )
    print(f"  [seed] MIGRATION audit record created")
    return migration


def main():
    print("\n============================================================")
    print("  SEED: E-Commerce Dataset — Schema V1")
    print("============================================================\n")

    start = datetime.now(timezone.utc)

    categories = seed_categories()
    products = seed_products(categories)
    users = seed_users()
    orders = seed_orders(users, products)
    registry = create_schema_registry()
    migration = create_initial_migration()

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print(f"\n  ✓ Seed complete in {elapsed:.2f}s")
    print(f"  Created {len(products)} products, {len(users)} users, {len(orders)} orders")
    print(f"  Registry: schema_version=1.0.0")


if __name__ == "__main__":
    main()
