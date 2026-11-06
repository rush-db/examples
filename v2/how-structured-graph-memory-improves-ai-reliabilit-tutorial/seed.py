"""
Seed script for the Graph Memory Tutorial.

Creates a structured knowledge graph with:
- 5 users with beverage preferences
- 8 products across categories
- 20+ interactions (orders, views, reviews)
- Full relationship graph

Run this before main.py to populate the database with realistic mock data.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env and fill in your credentials.")

db = RushDB(API_KEY)

# Sample data
USERS = [
    {"name": "Alice Chen", "email": "alice@example.com", "loyalty_tier": "gold"},
    {"name": "Marcus Johnson", "email": "marcus@example.com", "loyalty_tier": "silver"},
    {"name": "Priya Patel", "email": "priya@example.com", "loyalty_tier": "bronze"},
    {"name": "Erik Svensson", "email": "erik@example.com", "loyalty_tier": "gold"},
    {"name": "Yuki Tanaka", "email": "yuki@example.com", "loyalty_tier": "silver"},
]

PREFERENCES = [
    {"type": "beverage_preference", "value": "dark_roast", "strength": 0.9},
    {"type": "beverage_preference", "value": "cold_brew", "strength": 0.7},
    {"type": "beverage_preference", "value": "oat_milk", "strength": 0.8},
    {"type": "beverage_preference", "value": "sweetened", "strength": 0.6},
    {"type": "flavor_preference", "value": "chocolate", "strength": 0.85},
    {"type": "flavor_preference", "value": "caramel", "strength": 0.75},
    {"type": "flavor_preference", "value": "vanilla", "strength": 0.65},
    {"type": "flavor_preference", "value": "fruity", "strength": 0.5},
]

PRODUCTS = [
    {"name": "Espresso", "category": "coffee", "price": 3.50, "tags": ["dark_roast", "strong", "classic"]},
    {"name": "Cold Brew", "category": "coffee", "price": 4.50, "tags": ["cold_brew", "smooth", "refreshing"]},
    {"name": "Cappuccino", "category": "coffee", "price": 4.00, "tags": ["balanced", "foam", "mild"]},
    {"name": "Matcha Latte", "category": "tea", "price": 4.75, "tags": ["green_tea", "smooth", "healthy"]},
    {"name": "Chai Latte", "category": "tea", "price": 4.25, "tags": ["spiced", "warm", "sweet"]},
    {"name": "Mocha", "category": "coffee", "price": 5.00, "tags": ["chocolate", "sweet", "indulgent"]},
    {"name": "Americano", "category": "coffee", "price": 3.00, "tags": ["dark_roast", "strong", "classic"]},
    {"name": "Oat Milk Latte", "category": "coffee", "price": 5.25, "tags": ["oat_milk", "smooth", "dairy_free"]},
]

CATEGORIES = [
    {"name": "coffee", "description": "Coffee-based beverages"},
    {"name": "tea", "description": "Tea-based beverages"},
    {"name": "smoothie", "description": "Fruit and vegetable smoothies"},
]

def seed():
    """Seed the database with structured graph data."""
    print("=" * 60)
    print("SEEDING GRAPH MEMORY DATABASE")
    print("=" * 60)
    
    # Check if data already exists
    existing_users = db.records.find({"labels": ["USER"], "limit": 1})
    if existing_users:
        print("\n⚠️  Database already contains records.")
        print("   Run with a fresh database or manually clear existing data.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Seeding cancelled.")
            return
    
    print("\n[1/5] Creating categories...")
    categories = {}
    for i, cat_data in enumerate(CATEGORIES):
        category = db.records.create(label="CATEGORY", data=cat_data)
        categories[cat_data["name"]] = category
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} categories...")
    print(f"  ✓ Created {len(CATEGORIES)} categories")
    
    print("\n[2/5] Creating products with category relationships...")
    products = {}
    for i, prod_data in enumerate(PRODUCTS):
        tags = prod_data.pop("tags")
        category_name = prod_data.pop("category")
        
        product = db.records.create(label="PRODUCT", data=prod_data)
        products[prod_data["name"]] = product
        
        # Link to category
        category = categories[category_name]
        db.records.attach(
            source=product,
            target=category,
            options={"type": "IN_CATEGORY", "direction": "out"}
        )
        
        # Create tag records and link
        for tag_name in tags:
            tag = db.records.create(label="TAG", data={"name": tag_name})
            db.records.attach(
                source=product,
                target=tag,
                options={"type": "HAS_TAG", "direction": "out"}
            )
        
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} products...")
    print(f"  ✓ Created {len(PRODUCTS)} products with tags and categories")
    
    print("\n[3/5] Creating users with preferences...")
    users = {}
    for i, user_data in enumerate(USERS):
        user = db.records.create(label="USER", data=user_data)
        users[user_data["name"]] = user
        
        # Assign random preferences
        user_prefs = random.sample(PREFERENCES, random.randint(1, 3))
        for pref_data in user_prefs:
            pref = db.records.create(label="PREFERENCE", data=pref_data)
            db.records.attach(
                source=user,
                target=pref,
                options={"type": "HAS_PREFERENCE", "direction": "out"}
            )
        
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} users...")
    print(f"  ✓ Created {len(USERS)} users with preferences")
    
    print("\n[4/5] Creating interactions (orders, views, reviews)...")
    interaction_types = ["ORDERED", "VIEWED", "REVIEWED"]
    all_interactions = []
    
    for i, (user_name, user) in enumerate(users.items()):
        # Each user has 3-5 interactions
        num_interactions = random.randint(3, 5)
        interacted_products = random.sample(list(products.keys()), min(num_interactions, len(products)))
        
        for prod_name in interacted_products:
            product = products[prod_name]
            interaction_type = random.choice(interaction_types)
            
            # Create interaction record
            interaction_data = {
                "type": interaction_type.lower(),
                "timestamp": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "rating": random.randint(3, 5) if interaction_type == "REVIEWED" else None,
                "quantity": random.randint(1, 3) if interaction_type == "ORDERED" else 1
            }
            if interaction_data["rating"]:
                interaction_data.pop("rating", None)
            
            interaction = db.records.create(label="INTERACTION", data=interaction_data)
            all_interactions.append(interaction)
            
            # Link user to interaction
            db.records.attach(
                source=user,
                target=interaction,
                options={"type": "MADE", "direction": "out"}
            )
            
            # Link interaction to product
            db.records.attach(
                source=interaction,
                target=product,
                options={"type": "REGARDING", "direction": "out"}
            )
        
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} users with interactions...")
    print(f"  ✓ Created {len(all_interactions)} interactions")
    
    print("\n[5/5] Establishing product preference relationships...")
    # Connect preferences to products based on preference values
    preference_to_tags = {
        "dark_roast": ["Espresso", "Americano"],
        "cold_brew": ["Cold Brew"],
        "oat_milk": ["Oat Milk Latte"],
        "chocolate": ["Mocha"],
        "sweetened": ["Chai Latte", "Mocha"],
    }
    
    for pref_value, matching_products in preference_to_tags.items():
        for user_name, user in users.items():
            # Check if user has this preference
            prefs = db.records.find({
                "labels": ["PREFERENCE"],
                "where": {
                    "USER": {"$relation": {"type": "HAS_PREFERENCE", "direction": "in"}},
                    "value": pref_value
                }
            })
            
            if prefs:
                for product_name in matching_products:
                    product = products[product_name]
                    # Create explicit preference link (not through interaction)
                    db.records.attach(
                        source=product,
                        target=user,
                        options={"type": "PREFERRED_BY", "direction": "out"}
                    )
    print(f"  ✓ Established preference relationships")
    
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - {len(USERS)} users")
    print(f"  - {len(CATEGORIES)} categories")
    print(f"  - {len(PRODUCTS)} products")
    print(f"  - {len(all_interactions)} interactions")
    print(f"  - {len(PREFERENCES)} preference types")
    print(f"\nRun `python main.py` to see the tutorial in action!")

if __name__ == "__main__":
    seed()
