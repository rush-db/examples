"""
Seed script for personalization engine tutorial.

Creates a realistic e-commerce dataset with:
- 20 users with profiles
- 50 products across categories
- ~200 user-item interactions (views, purchases, ratings)
- Similarity relationships between items

This script is idempotent: running it multiple times produces the same result.
"""

import os
import random
from collections import defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
URL = os.getenv("RUSHDB_URL")

if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env and add your key.")

db = RushDB(API_KEY, url=URL) if URL else RushDB(API_KEY)

# Seed data
CATEGORIES = ["electronics", "clothing", "books", "home", "sports", "toys"]

USERS = [
    {"name": "Alice Chen", "email": "alice@example.com", "age_group": "25-34", "tier": "premium"},
    {"name": "Bob Martinez", "email": "bob@example.com", "age_group": "18-24", "tier": "standard"},
    {"name": "Carol Johnson", "email": "carol@example.com", "age_group": "35-44", "tier": "premium"},
    {"name": "David Kim", "email": "david@example.com", "age_group": "25-34", "tier": "standard"},
    {"name": "Emma Wilson", "email": "emma@example.com", "age_group": "45-54", "tier": "premium"},
    {"name": "Frank Brown", "email": "frank@example.com", "age_group": "25-34", "tier": "standard"},
    {"name": "Grace Lee", "email": "grace@example.com", "age_group": "18-24", "tier": "standard"},
    {"name": "Henry Davis", "email": "henry@example.com", "age_group": "35-44", "tier": "premium"},
    {"name": "Iris Taylor", "email": "iris@example.com", "age_group": "25-34", "tier": "standard"},
    {"name": "Jack Anderson", "email": "jack@example.com", "age_group": "45-54", "tier": "standard"},
    {"name": "Karen White", "email": "karen@example.com", "age_group": "18-24", "tier": "standard"},
    {"name": "Leo Garcia", "email": "leo@example.com", "age_group": "35-44", "tier": "premium"},
    {"name": "Mia Thompson", "email": "mia@example.com", "age_group": "25-34", "tier": "standard"},
    {"name": "Noah Robinson", "email": "noah@example.com", "age_group": "18-24", "tier": "standard"},
    {"name": "Olivia Clark", "email": "olivia@example.com", "age_group": "45-54", "tier": "premium"},
    {"name": "Paul Walker", "email": "paul@example.com", "age_group": "35-44", "tier": "standard"},
    {"name": "Quinn Harris", "email": "quinn@example.com", "age_group": "25-34", "tier": "standard"},
    {"name": "Rachel Young", "email": "rachel@example.com", "age_group": "18-24", "tier": "premium"},
    {"name": "Sam King", "email": "sam@example.com", "age_group": "35-44", "tier": "standard"},
    {"name": "Tina Wright", "email": "tina@example.com", "age_group": "25-34", "tier": "standard"},
]

ITEMS = [
    # Electronics (category_id: 0-9)
    {"name": "Wireless Headphones", "category": "electronics", "price": 79.99, "brand": "AudioMax"},
    {"name": "Smart Watch Pro", "category": "electronics", "price": 299.99, "brand": "TechTime"},
    {"name": "Bluetooth Speaker", "category": "electronics", "price": 49.99, "brand": "SoundWave"},
    {"name": "USB-C Hub", "category": "electronics", "price": 39.99, "brand": "ConnectPro"},
    {"name": "Mechanical Keyboard", "category": "electronics", "price": 129.99, "brand": "TypeMaster"},
    {"name": "Wireless Mouse", "category": "electronics", "price": 29.99, "brand": "ClickTech"},
    {"name": "Laptop Stand", "category": "electronics", "price": 44.99, "brand": "ErgoDesk"},
    {"name": "4K Monitor", "category": "electronics", "price": 399.99, "brand": "VisionPlus"},
    {"name": "Webcam HD", "category": "electronics", "price": 69.99, "brand": "ClearView"},
    {"name": "Portable Charger", "category": "electronics", "price": 34.99, "brand": "PowerBank"},
    # Clothing (category_id: 10-19)
    {"name": "Classic Denim Jacket", "category": "clothing", "price": 89.99, "brand": "DenimCo"},
    {"name": "Running Sneakers", "category": "clothing", "price": 119.99, "brand": "SpeedRun"},
    {"name": "Wool Sweater", "category": "clothing", "price": 79.99, "brand": "WarmWear"},
    {"name": "Casual T-Shirt", "category": "clothing", "price": 24.99, "brand": "BasicStyle"},
    {"name": "Cargo Pants", "category": "clothing", "price": 64.99, "brand": "UrbanFit"},
    {"name": "Leather Belt", "category": "clothing", "price": 45.99, "brand": "ClassicLeather"},
    {"name": "Winter Coat", "category": "clothing", "price": 159.99, "brand": "WarmWear"},
    {"name": "Hiking Boots", "category": "clothing", "price": 139.99, "brand": "TrailMaster"},
    {"name": "Baseball Cap", "category": "clothing", "price": 19.99, "brand": "SportStyle"},
    {"name": "Cotton Socks 6-Pack", "category": "clothing", "price": 18.99, "brand": "ComfortZone"},
    # Books (category_id: 20-29)
    {"name": "The Art of Programming", "category": "books", "price": 49.99, "brand": "CodePress"},
    {"name": "Modern Design Patterns", "category": "books", "price": 44.99, "brand": "DesignHub"},
    {"name": "Data Science Handbook", "category": "books", "price": 54.99, "brand": "DataWorks"},
    {"name": "Business Strategy 101", "category": "books", "price": 29.99, "brand": "BizBooks"},
    {"name": "Mindful Leadership", "category": "books", "price": 24.99, "brand": "GrowthMind"},
    {"name": "The Startup Guide", "category": "books", "price": 34.99, "brand": "EntrepreneurPub"},
    {"name": "Cloud Architecture", "category": "books", "price": 59.99, "brand": "CloudBooks"},
    {"name": "UX Design Fundamentals", "category": "books", "price": 39.99, "brand": "DesignHub"},
    {"name": "Machine Learning Basics", "category": "books", "price": 49.99, "brand": "DataWorks"},
    {"name": "Agile Methodologies", "category": "books", "price": 34.99, "brand": "CodePress"},
    # Home (category_id: 30-39)
    {"name": "Smart Light Bulbs", "category": "home", "price": 29.99, "brand": "BrightHome"},
    {"name": "Coffee Maker Pro", "category": "home", "price": 89.99, "brand": "BrewMaster"},
    {"name": "Plant Pot Set", "category": "home", "price": 34.99, "brand": "GreenLiving"},
    {"name": "Throw Blanket", "category": "home", "price": 44.99, "brand": "CozyHome"},
    {"name": "Wall Clock Minimal", "category": "home", "price": 24.99, "brand": "ModernHome"},
    {"name": "Storage Basket Set", "category": "home", "price": 39.99, "brand": "OrganizeIt"},
    {"name": "Scented Candles 4-Pack", "category": "home", "price": 28.99, "brand": "AromaCraft"},
    {"name": "Kitchen Timer", "category": "home", "price": 14.99, "brand": "ChefTools"},
    {"name": "Desk Organizer", "category": "home", "price": 22.99, "brand": "OrganizeIt"},
    {"name": "Indoor Plant Stand", "category": "home", "price": 49.99, "brand": "GreenLiving"},
    # Sports (category_id: 40-44)
    {"name": "Yoga Mat Premium", "category": "sports", "price": 39.99, "brand": "ZenFit"},
    {"name": "Resistance Bands Set", "category": "sports", "price": 24.99, "brand": "FitGear"},
    {"name": "Dumbbells 10kg Set", "category": "sports", "price": 79.99, "brand": "IronGym"},
    {"name": "Jump Rope Speed", "category": "sports", "price": 14.99, "brand": "FitGear"},
    {"name": "Foam Roller", "category": "sports", "price": 29.99, "brand": "ZenFit"},
    {"name": "Tennis Racket", "category": "sports", "price": 89.99, "brand": "SportPro"},
    {"name": "Basketball", "category": "sports", "price": 34.99, "brand": "BallSport"},
    {"name": "Swimming Goggles", "category": "sports", "price": 19.99, "brand": "AquaGear"},
    {"name": "Cycling Gloves", "category": "sports", "price": 22.99, "brand": "RideGear"},
    {"name": "Gym Bag", "category": "sports", "price": 44.99, "brand": "FitGear"},
    # Toys (category_id: 45-49)
    {"name": "Building Blocks Set", "category": "toys", "price": 39.99, "brand": "BuildFun"},
    {"name": "Board Game Collection", "category": "toys", "price": 34.99, "brand": "GameTime"},
    {"name": "Remote Control Car", "category": "toys", "price": 49.99, "brand": "SpeedToys"},
    {"name": "Puzzle 1000 Pieces", "category": "toys", "price": 19.99, "brand": "PuzzlePro"},
    {"name": "Art Supply Kit", "category": "toys", "price": 29.99, "brand": "CreativeKids"},
]


def clear_existing_data():
    """Remove existing seed data for clean re-seeding."""
    print("Clearing existing data...")
    
    # Delete all records with our labels
    db.records.delete_many({"labels": ["USER"], "where": {}})
    db.records.delete_many({"labels": ["ITEM"], "where": {}})
    
    print("Existing data cleared.")


def create_users():
    """Create user records."""
    print("\nCreating users...")
    users = []
    
    for i, user_data in enumerate(USERS):
        user = db.records.create(
            label="USER",
            data=user_data
        )
        users.append(user)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(USERS)} users")
    
    print(f"  Created {len(users)} users total")
    return users


def create_items():
    """Create item/product records."""
    print("\nCreating items...")
    items = []
    
    for i, item_data in enumerate(ITEMS):
        item = db.records.create(
            label="ITEM",
            data=item_data
        )
        items.append(item)
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{len(ITEMS)} items")
    
    print(f"  Created {len(items)} items total")
    return items


def create_interactions(users, items):
    """Create user-item interaction relationships."""
    print("\nCreating user-item interactions...")
    
    interaction_types = ["VIEWED", "PURCHASED", "RATED"]
    base_date = datetime.now() - timedelta(days=90)
    interactions_created = 0
    
    # Generate interactions with realistic patterns
    # Each user interacts with 8-15 items
    random.seed(42)  # Deterministic for idempotency
    
    for user in users:
        num_interactions = random.randint(8, 15)
        interacted_items = random.sample(items, num_interactions)
        
        with db.transactions.begin() as tx:
            for item in interacted_items:
                # Create at least one interaction type
                interaction = random.choice(interaction_types)
                
                # Attach the relationship
                db.records.attach(
                    source=user,
                    target=item,
                    options={"type": interaction, "direction": "out"},
                    transaction=tx
                )
                
                # Some users rate items
                if interaction == "RATED" or random.random() < 0.3:
                    rating = random.randint(3, 5)
                    # Create a rating node linked to the interaction
                    rating_record = db.records.create(
                        label="RATING",
                        data={
                            "score": rating,
                            "timestamp": (base_date + timedelta(days=random.randint(0, 90))).isoformat()
                        },
                        transaction=tx
                    )
                    # Link rating to both user and item
                    db.records.attach(source=user, target=rating_record, options={"type": "GAVE", "direction": "out"}, transaction=tx)
                    db.records.attach(source=rating_record, target=item, options={"type": "FOR", "direction": "out"}, transaction=tx)
                
                interactions_created += 1
        
        if (users.index(user) + 1) % 5 == 0:
            print(f"  Created interactions for {users.index(user) + 1}/{len(users)} users")
    
    print(f"  Created {interactions_created} interactions total")


def create_item_similarities(items):
    """Create SIMILAR_TO relationships between items in the same category."""
    print("\nCreating item similarities...")
    
    # Group items by category
    by_category = defaultdict(list)
    for item in items:
        category = item["category"]
        by_category[category].append(item)
    
    similarities_created = 0
    
    for category, category_items in by_category.items():
        # Create similarity links within each category
        for i, item_a in enumerate(category_items):
            for item_b in category_items[i+1:i+3]:  # Link to 2 similar items
                db.records.attach(
                    source=item_a,
                    target=item_b,
                    options={"type": "SIMILAR_TO", "direction": "out"}
                )
                similarities_created += 1
    
    print(f"  Created {similarities_created} item similarity links")


def verify_data():
    """Verify seed data was created correctly."""
    print("\n--- Verifying Seed Data ---")
    
    users = db.records.find({"labels": ["USER"], "limit": 100})
    items = db.records.find({"labels": ["ITEM"], "limit": 100})
    
    print(f"Users: {users.total}")
    print(f"Items: {items.total}")
    
    # Sample user preferences
    if users.data:
        sample_user = users.data[0]
        print(f"\nSample user: {sample_user['name']} ({sample_user['email']})")
    
    # Count by category
    for category in CATEGORIES:
        result = db.records.find({"labels": ["ITEM"], "where": {"category": category}})
        print(f"  {category}: {result.total} items")


def main():
    print("=" * 60)
    print("PERSONALIZATION ENGINE - DATA SEEDING")
    print("=" * 60)
    
    # Clear existing data first
    clear_existing_data()
    
    # Create new data
    users = create_users()
    items = create_items()
    create_interactions(users, items)
    create_item_similarities(items)
    
    # Verify
    verify_data()
    
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print("\nRun `python main.py` to see recommendation examples.")


if __name__ == "__main__":
    main()
