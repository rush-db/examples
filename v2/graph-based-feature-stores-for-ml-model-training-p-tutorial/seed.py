"""
Mock data generation script for graph-based feature store tutorial.

Creates a realistic e-commerce dataset with users, products, purchases,
and view events to demonstrate feature engineering via graph traversal.

Run this once before main.py if you want fresh data.
The script is idempotent and skips seeding if data already exists.
"""

import random
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB

# Initialize
fake = Faker()
Faker.seed(42)
random.seed(42)

db = RushDB()

# Configuration
NUM_USERS = 150
NUM_PRODUCTS = 50
NUM_PURCHASES = 600
NUM_VIEWS = 2000

# Categories and price ranges
CATEGORIES = [
    ("electronics", 29.99, 999.99),
    ("clothing", 14.99, 299.99),
    ("home", 19.99, 499.99),
    ("sports", 24.99, 199.99),
    ("books", 9.99, 49.99),
]

SEGMENTS = ["standard", "premium", "enterprise"]


def check_data_exists():
    """Check if seed data already exists."""
    result = db.records.find({"labels": ["USER"], "limit": 1})
    return result.total > 0


def seed_segments():
    """Create segment records."""
    print("[1/5] Creating segments...")
    for segment_name in SEGMENTS:
        # Check if exists
        existing = db.records.find({
            "labels": ["SEGMENT"],
            "where": {"name": segment_name}
        })
        if existing.total > 0:
            print(f"  - Segment '{segment_name}' already exists, skipping")
            continue

        db.records.create(
            label="SEGMENT",
            data={
                "name": segment_name,
                "discount_rate": 0.0 if segment_name == "standard" else (0.1 if segment_name == "premium" else 0.15),
                "free_shipping_threshold": 99.99 if segment_name == "standard" else 49.99
            }
        )
        print(f"  - Created segment: {segment_name}")


def seed_categories():
    """Create category records."""
    print("[2/5] Creating categories...")
    for cat_name, _, _ in CATEGORIES:
        existing = db.records.find({
            "labels": ["CATEGORY"],
            "where": {"name": cat_name}
        })
        if existing.total > 0:
            print(f"  - Category '{cat_name}' already exists, skipping")
            continue

        db.records.create(
            label="CATEGORY",
            data={"name": cat_name}
        )
        print(f"  - Created category: {cat_name}")


def seed_users():
    """Create user records with profile features."""
    print(f"[3/5] Creating {NUM_USERS} users...")

    existing = db.records.find({"labels": ["USER"], "limit": 1})
    if existing.total > 0:
        print("  - Users already exist, skipping")
        return

    segments = db.records.find({"labels": ["SEGMENT"]}).data
    segment_map = {s.data["name"]: s for s in segments}

    users_created = 0
    for i in range(NUM_USERS):
        age = random.randint(18, 65)
        segment = random.choices(SEGMENTS, weights=[60, 30, 10])[0]
        registration_date = fake.date_between(
            start_date="-2y", end_date="-30d"
        )

        user = db.records.create(
            label="USER",
            data={
                "email": fake.email(),
                "name": fake.name(),
                "age": age,
                "city": fake.city(),
                "country": fake.country(),
                "registration_date": registration_date.isoformat(),
                "is_active": random.random() > 0.1,
                "preferred_categories": random.sample(
                    [c[0] for c in CATEGORIES], k=random.randint(1, 3)
                )
            }
        )

        # Attach to segment
        segment_record = segment_map[segment]
        db.records.attach(
            source=user,
            target=segment_record,
            options={"type": "BELONGS_TO", "direction": "out"}
        )

        users_created += 1
        if users_created % 50 == 0:
            print(f"  - Created {users_created}/{NUM_USERS} users...")

    print(f"  - Created {users_created} users")


def seed_products():
    """Create product records with attributes."""
    print(f"[4/5] Creating {NUM_PRODUCTS} products...")

    existing = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    if existing.total > 0:
        print("  - Products already exist, skipping")
        return

    categories = db.records.find({"labels": ["CATEGORY"]}).data
    category_map = {c["name"]: c for c in categories}

    products_created = 0
    for i in range(NUM_PRODUCTS):
        category_name, min_price, max_price = random.choice(CATEGORIES)
        category_record = category_map[category_name]

        product = db.records.create(
            label="PRODUCT",
            data={
                "sku": f"SKU-{i+1:05d}",
                "name": fake.catch_phrase(),
                "description": fake.sentence(nb_words=10),
                "price": round(random.uniform(min_price, max_price), 2),
                "stock": random.randint(0, 500),
                "rating": round(random.uniform(3.0, 5.0), 1),
                "review_count": random.randint(0, 500),
                "launch_date": fake.date_between(
                    start_date="-1y", end_date="-7d"
                ).isoformat()
            }
        )

        # Attach to category
        db.records.attach(
            source=product,
            target=category_record,
            options={"type": "BELONGS_TO", "direction": "out"}
        )

        products_created += 1
        if products_created % 25 == 0:
            print(f"  - Created {products_created}/{NUM_PRODUCTS} products...")

    print(f"  - Created {products_created} products")


def seed_purchases():
    """Create purchase records linking users to products."""
    print(f"[5/5] Creating {NUM_PURCHASES} purchases...")

    existing = db.records.find({"labels": ["PURCHASE"], "limit": 1})
    if existing.total > 0:
        print("  - Purchases already exist, skipping")
        return

    users = db.records.find({"labels": ["USER"]}).data
    products = db.records.find({"labels": ["PRODUCT"]}).data

    purchases_created = 0
    for i in range(NUM_PURCHASES):
        user = random.choice(users)
        product = random.choice(products)

        # Weighted by rating (better products slightly more likely)
        quantity = random.randint(1, 3)
        unit_price = product.data["price"]
        total = round(unit_price * quantity, 2)

        purchase_date = fake.date_time_between(
            start_date="-1y", end_date="now"
        )

        purchase = db.records.create(
            label="PURCHASE",
            data={
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total,
                "date": purchase_date.isoformat(),
                "payment_method": random.choice(["credit_card", "paypal", "bank_transfer"]),
                "status": random.choices(
                    ["completed", "pending", "refunded"],
                    weights=[85, 10, 5]
                )[0]
            }
        )

        # Link user to purchase
        db.records.attach(
            source=purchase,
            target=user,
            options={"type": "PLACED_BY", "direction": "in"}
        )

        # Link purchase to product
        db.records.attach(
            source=purchase,
            target=product,
            options={"type": "INCLUDES", "direction": "out"}
        )

        purchases_created += 1
        if purchases_created % 100 == 0:
            print(f"  - Created {purchases_created}/{NUM_PURCHASES} purchases...")

    print(f"  - Created {purchases_created} purchases")


def seed_views():
    """Create view events for behavioral features."""
    print(f"  Creating {NUM_VIEWS} view events...")

    existing = db.records.find({"labels": ["VIEW"], "limit": 1})
    if existing.total > 0:
        print("  - Views already exist, skipping")
        return

    users = db.records.find({"labels": ["USER"]}).data
    products = db.records.find({"labels": ["PRODUCT"]}).data

    views_created = 0
    for i in range(NUM_VIEWS):
        user = random.choice(users)
        product = random.choice(products)

        view = db.records.create(
            label="VIEW",
            data={
                "duration_seconds": random.randint(5, 300),
                "date": fake.date_time_between(
                    start_date="-6m", end_date="now"
                ).isoformat(),
                "source": random.choice(["search", "category", "recommendation", "direct"])
            }
        )

        # Link user to view
        db.records.attach(
            source=view,
            target=user,
            options={"type": "BY_USER", "direction": "in"}
        )

        # Link view to product
        db.records.attach(
            source=view,
            target=product,
            options={"type": "OF_PRODUCT", "direction": "out"}
        )

        views_created += 1
        if views_created % 500 == 0:
            print(f"  - Created {views_created}/{NUM_VIEWS} views...")

    print(f"  - Created {views_created} views")


def main():
    """Run the seeding process."""
    print("\n" + "=" * 50)
    print("Graph Feature Store - Data Seeding")
    print("=" * 50 + "\n")

    if check_data_exists():
        print("Seed data already exists. Skipping seeding.")
        print("Delete existing records or run 'python seed.py --force' to re-seed.")
        return

    # Seed in order (segments/categories first for foreign keys)
    seed_segments()
    seed_categories()
    seed_users()
    seed_products()
    seed_purchases()
    seed_views()

    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("Run 'python main.py' to start the tutorial.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("Force mode: cleaning existing data first...")
        # Note: In production, you'd want to be more careful about deletes
        # This is just for the tutorial
    main()
