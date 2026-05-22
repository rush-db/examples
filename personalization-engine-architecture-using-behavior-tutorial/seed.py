"""
Personalization Engine - Data Seeding Script

Generates synthetic behavioral data for the personalization engine tutorial.
Creates users, products, and behavioral events connected via RushDB property graph.
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Configuration
NUM_USERS = 50
NUM_PRODUCTS = 120
NUM_SESSIONS = 200
EVENTS_PER_SESSION = (3, 12)

# Behavior weights (for interest scoring)
BEHAVIOR_WEIGHTS = {
    "VIEW": 1.0,
    "CLICK": 2.5,
    "ADD_TO_CART": 5.0,
    "PURCHASE": 10.0,
}

# Product categories with realistic items
CATEGORIES = {
    "Electronics": [
        "Wireless Headphones", "Bluetooth Speaker", "USB-C Hub", "Mechanical Keyboard",
        "Gaming Mouse", "Webcam HD", "Monitor Stand", "Laptop Stand", "USB Cable",
        "Power Bank", "Wireless Charger", "Smart Watch", "Fitness Tracker",
        "Earbuds", "Portable SSD", "HDMI Cable", "Screen Protector", "Laptop Bag",
        "Wireless Mouse", "Desk Lamp",
    ],
    "Books": [
        "Python Programming Guide", "Data Science Handbook", "Machine Learning Basics",
        "System Design Interview", "Clean Code Principles", "Design Patterns",
        "Algorithms Cookbook", "Database Internals", "Cloud Architecture",
        "DevOps Handbook", "JavaScript Mastery", "React Performance",
        "Distributed Systems", "Microservices Guide", "Docker Deep Dive",
        "Kubernetes in Action", "GraphQL Essentials", "TypeScript Handbook",
        "Testing Strategies", "Technical Writing",
    ],
    "Home & Kitchen": [
        "Coffee Maker", "Air Fryer", "Instant Pot", "Blender Pro", "Toaster",
        "Electric Kettle", "Food Processor", "Knife Set", "Cutting Board", "Mixing Bowls",
        "Silicone Spatula Set", "Measuring Cups", "Kitchen Scale", "Colander",
        "Dish Rack", "Trash Can", "Storage Containers", "Pantry Organizer",
        "Spice Rack", "Oven Thermometer",
    ],
    "Sports & Outdoors": [
        "Yoga Mat", "Resistance Bands", "Dumbbells Set", "Jump Rope", "Foam Roller",
        "Running Shoes", "Hiking Boots", "Camping Tent", "Sleeping Bag", "Backpack",
        "Water Bottle", "Protein Shaker", "Workout Gloves", "Ankle Weights",
        "Exercise Ball", "Pull-up Bar", "Kettlebell", "Ab Wheel", "Bike Helmet",
        "Tennis Racket",
    ],
    "Fashion": [
        "Cotton T-Shirt", "Denim Jeans", "Wool Sweater", "Rain Jacket", "Running Shorts",
        "Leather Belt", "Canvas Sneakers", "Wool Socks", "Thermal Underwear",
        "Baseball Cap", "Beanie", "Scarf", "Leather Wallet", "Watch", "Sunglasses",
        "Backpack", "Messenger Bag", "Hiking Socks", "Fleece Jacket", "Dress Shirt",
    ],
    "Beauty & Health": [
        "Face Moisturizer", "Sunscreen SPF 50", "Shampoo", "Conditioner", "Body Wash",
        "Hair Serum", "Lip Balm", "Hand Cream", "Eye Cream", "Face Mask",
        "Vitamin D Supplements", "Omega-3 Capsules", "Probiotics", "Collagen Powder",
        "Essential Oil Set", "Beard Oil", "Hair Wax", "Face Wash", "Exfoliator",
        "Perfume",
    ],
}

# Price ranges per category
CATEGORY_PRICE_RANGES = {
    "Electronics": (29.99, 299.99),
    "Books": (14.99, 49.99),
    "Home & Kitchen": (19.99, 149.99),
    "Sports & Outdoors": (24.99, 199.99),
    "Fashion": (19.99, 129.99),
    "Beauty & Health": (12.99, 79.99),
}


def check_existing_data(db: RushDB) -> bool:
    """Check if data already exists."""
    result = db.records.find({"labels": ["USER"], "limit": 1})
    return len(result.data) > 0


def clear_existing_data(db: RushDB) -> None:
    """Clear all existing data for clean seeding."""
    print("Clearing existing data...")
    db.records.delete_many({"labels": ["BEHAVIOR_EVENT"]})
    db.records.delete_many({"labels": ["SESSION"]})
    db.records.delete_many({"labels": ["USER"]})
    db.records.delete_many({"labels": ["PRODUCT"]})
    print("Existing data cleared.")


def generate_users(db: RushDB) -> list:
    """Generate synthetic user profiles."""
    fake = Faker()
    print(f"\nGenerating {NUM_USERS} users...")

    users = []
    for i in range(NUM_USERS):
        user = db.records.create(
            label="USER",
            data={
                "user_id": f"user_{i:03d}",
                "name": fake.name(),
                "email": fake.email(),
                "age_group": random.choice(["18-24", "25-34", "35-44", "45-54", "55+"]),
                "location": random.choice(["North America", "Europe", "Asia", "Other"]),
                "signup_date": fake.date_between(start_date="-2y", end_date="today").isoformat(),
                "preference_categories": random.sample(list(CATEGORIES.keys()), k=random.randint(2, 4)),
            }
        )
        users.append(user)

        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{NUM_USERS} users")

    return users


def generate_products(db: RushDB) -> dict:
    """Generate synthetic product catalog."""
    print(f"\nGenerating {NUM_PRODUCTS} products...")

    products = {}
    product_id = 0

    for category, items in CATEGORIES.items():
        min_price, max_price = CATEGORY_PRICE_RANGES[category]

        for item in items:
            product = db.records.create(
                label="PRODUCT",
                data={
                    "product_id": f"prod_{product_id:04d}",
                    "name": item,
                    "category": category,
                    "price": round(random.uniform(min_price, max_price), 2),
                    "rating": round(random.uniform(3.5, 5.0), 1),
                    "review_count": random.randint(5, 500),
                    "in_stock": random.choice([True, True, True, False]),
                    "tags": random.sample(["bestseller", "new", "sale", "eco-friendly", "premium", "budget"], k=random.randint(1, 3)),
                }
            )
            products[f"prod_{product_id:04d}"] = product
            product_id += 1

            if product_id % 20 == 0:
                print(f"  Created {product_id}/{NUM_PRODUCTS} products")

    return products


def generate_sessions(db: RushDB, users: list, products: dict) -> list:
    """Generate user sessions with behavioral events."""
    print(f"\nGenerating {NUM_SESSIONS} sessions with behavioral events...")

    sessions = []
    product_list = list(products.values())

    for i in range(NUM_SESSIONS):
        user = random.choice(users)
        session_start = datetime.now() - timedelta(days=random.randint(0, 30))

        # Create session
        session = db.records.create(
            label="SESSION",
            data={
                "session_id": f"session_{i:04d}",
                "started_at": session_start.isoformat(),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "source": random.choice(["direct", "search", "social", "email", "referral"]),
            }
        )

        # Link session to user
        db.records.attach(
            source=session,
            target=user,
            options={"type": "BELONGS_TO"}
        )

        # Generate events for this session
        num_events = random.randint(*EVENTS_PER_SESSION)
        session_products = random.sample(product_list, k=min(num_events, len(product_list)))

        for j, product in enumerate(session_products):
            event_time = session_start + timedelta(minutes=random.randint(0, 120))

            # Determine behavior type with weighted probability
            behavior_roll = random.random()
            if behavior_roll < 0.50:
                behavior = "VIEW"
            elif behavior_roll < 0.75:
                behavior = "CLICK"
            elif behavior_roll < 0.90:
                behavior = "ADD_TO_CART"
            else:
                behavior = "PURCHASE"

            event = db.records.create(
                label="BEHAVIOR_EVENT",
                data={
                    "event_id": f"event_{i:04d}_{j:02d}",
                    "type": behavior,
                    "timestamp": event_time.isoformat(),
                    "duration_seconds": random.randint(5, 300) if behavior == "VIEW" else random.randint(10, 120),
                    "converted": behavior == "PURCHASE",
                }
            )

            # Link event to product
            db.records.attach(
                source=event,
                target=product,
                options={"type": "RELATES_TO"}
            )

            # Link event to session
            db.records.attach(
                source=event,
                target=session,
                options={"type": "PART_OF"}
            )

        sessions.append(session)

        if (i + 1) % 25 == 0:
            print(f"  Created {i + 1}/{NUM_SESSIONS} sessions")

    return sessions


def compute_interest_scores(db: RushDB, users: list, products: dict) -> None:
    """Derive user interest scores from behavioral data."""
    print("\nComputing user interest profiles...")

    for idx, user in enumerate(users):
        # Find all behavior events for this user
        events = db.records.find({
            "labels": ["BEHAVIOR_EVENT"],
            "where": {
                "SESSION": {
                    "$relation": {"type": "BELONGS_TO", "direction": "in"},
                    "$id": {"$in": [user.id]}
                }
            }
        })

        # Aggregate interest by category
        category_scores = {}
        for event in events.data:
            weight = BEHAVIOR_WEIGHTS.get(event.get("type", "VIEW"), 1.0)
            # Find the related product
            related_products = db.records.find({
                "labels": ["PRODUCT"],
                "where": {
                    "BEHAVIOR_EVENT": {
                        "$relation": {"type": "RELATES_TO", "direction": "in"},
                        "$id": {"$in": [event.get("__id") or event.get("id")]}
                    }
                }
            })
            if related_products.data:
                category = related_products.data[0].get("category", "Unknown")
                category_scores[category] = category_scores.get(category, 0) + weight

        # Update user profile with computed interests
        if category_scores:
            interests = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
            db.records.update(
                record_id=user.id,
                data={
                    "interest_profile": {"categories": dict(interests[:5])},
                    "total_events": len(events.data)
                }
            )

        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(users)} user profiles")


def main():
    """Main seeding function."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Please create a .env file with your RushDB API key")
        return

    print("=" * 60)
    print("Personalization Engine - Data Seeding")
    print("=" * 60)

    db = RushDB(api_key)

    # Check for existing data
    if check_existing_data(db):
        response = input("Existing data found. Clear and reseed? (y/n): ")
        if response.lower() == 'y':
            clear_existing_data(db)
        else:
            print("Seeding cancelled. Run main.py to use existing data.")
            return

    # Generate data
    print("\n[1/4] Generating user profiles...")
    users = generate_users(db)

    print("\n[2/4] Generating product catalog...")
    products = generate_products(db)

    print("\n[3/4] Generating behavioral events...")
    sessions = generate_sessions(db, users, products)

    print("\n[4/4] Computing interest profiles...")
    compute_interest_scores(db, users, products)

    print("\n" + "=" * 60)
    print("Seeding complete!")
    print(f"  Users: {len(users)}")
    print(f"  Products: {len(products)}")
    print(f"  Sessions: {len(sessions)}")
    print("=" * 60)
    print("\nRun 'python main.py' to execute the personalization engine")


if __name__ == "__main__":
    main()
