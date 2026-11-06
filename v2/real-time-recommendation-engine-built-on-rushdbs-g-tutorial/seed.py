#!/usr/bin/env python3
"""
Seed script for the Real-time Recommendation Engine.

Generates mock data and imports it into RushDB:
- 50 products with rich descriptions
- 30 users with preferences
- 300+ interactions (views, purchases, ratings)

This script is idempotent: run it multiple times safely.
"""

import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env")

db = RushDB(api_key, url=os.getenv("RUSHDB_URL"))

# Sentence transformer for embeddings
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Product categories with sample data
PRODUCT_CATALOG = {
    "Electronics": [
        {"name": "Wireless Noise-Canceling Headphones", "price": 299.99, "description": "Premium over-ear headphones with active noise cancellation, 30-hour battery life, and crystal-clear audio quality for immersive music listening"},
        {"name": "Mechanical Gaming Keyboard", "price": 149.99, "description": "RGB backlit mechanical keyboard with Cherry MX switches, programmable macros, and aircraft-grade aluminum frame for competitive gaming"},
        {"name": "Ultrawide Curved Monitor 34\"", "price": 599.99, "description": "34-inch UWQHD curved display with 144Hz refresh rate, 1ms response time, and HDR400 for immersive gaming and productivity"},
        {"name": "Wireless Ergonomic Mouse", "price": 79.99, "description": "Vertical ergonomic design wireless mouse with adjustable DPI, silent clicks, and thumb rest for comfortable all-day use"},
        {"name": "Portable SSD 2TB", "price": 189.99, "description": "Ultra-fast external SSD with USB-C, read speeds up to 1050MB/s, and shock-resistant design for portable data storage"},
        {"name": "4K Webcam with Ring Light", "price": 129.99, "description": "4K webcam with integrated ring light, autofocus, and noise-reducing microphone for professional video calls and streaming"},
        {"name": "Wireless Charging Pad", "price": 39.99, "description": "Fast wireless charger compatible with Qi devices, sleek minimalist design, and built-in heat dissipation for safe charging"},
        {"name": "Smart Home Hub", "price": 99.99, "description": "Central smart home controller compatible with Alexa, Google Home, and Zigbee devices for whole-home automation"},
    ],
    "Office Furniture": [
        {"name": "Ergonomic Office Chair", "price": 449.99, "description": "Premium ergonomic chair with lumbar support, adjustable armrests, breathable mesh back, and 5-year warranty for all-day comfort"},
        {"name": "Standing Desk Electric", "price": 549.99, "description": "Electric standing desk with memory presets, cable management, and sturdy steel frame that lifts up to 350lbs smoothly"},
        {"name": "Premium Desk Mat XL", "price": 59.99, "description": "Extra-large leather desk mat with stitched edges, water-resistant surface, and non-slip base for organized workspace"},
        {"name": "Monitor Arm Mount", "price": 89.99, "description": "Heavy-duty gas spring monitor arm supporting 17-32 inch screens, full motion adjustment, and cable management system"},
        {"name": "Ergonomic Footrest", "price": 49.99, "description": "Adjustable footrest with massage texture surface, 3 tilt angles, and non-slip base for improved posture and comfort"},
        {"name": "Desk Organizer Set", "price": 34.99, "description": "Bamboo desk organizer with phone stand, pen holder, and compartments for a tidy and productive workspace"},
    ],
    "Audio & Music": [
        {"name": "Studio Monitor Speakers", "price": 399.99, "description": "Professional studio monitors with flat frequency response, 5-inch woofer, and accurate sound reproduction for music production"},
        {"name": "USB Condenser Microphone", "price": 129.99, "description": "Cardioid USB mic with built-in pop filter, zero-latency monitoring, and plug-and-play setup for podcasts and recording"},
        {"name": "Audio Interface 2x2", "price": 149.99, "description": "USB audio interface with 2 inputs, 2 outputs, studio-grade preamps, and phantom power for professional recordings"},
        {"name": "Wireless In-Ear Monitors", "price": 199.99, "description": "True wireless earbuds with LDAC codec, 8-hour battery, and secure fit for musicians and audio professionals"},
        {"name": "DJ Controller", "price": 299.99, "description": "Professional DJ controller with jog wheels, performance pads, and integration with popular DJ software for live sets"},
    ],
    "Wearables": [
        {"name": "Fitness Smart Watch Pro", "price": 349.99, "description": "Advanced fitness tracker with GPS, heart rate monitoring, sleep tracking, and 7-day battery life for athletes and fitness enthusiasts"},
        {"name": "Health Tracker Band", "price": 79.99, "description": "Slim fitness band with step counting, calorie tracking, and notifications display for everyday health monitoring"},
        {"name": "Sports Smart Watch", "price": 249.99, "description": "Rugged smartwatch with water resistance, trail maps, and multi-sport modes for outdoor adventures"},
        {"name": "Smart Ring Health Tracker", "price": 299.99, "description": "Discreet smart ring tracking sleep, activity, and body temperature with 3-day battery and premium titanium design"},
    ],
    "Peripherals": [
        {"name": "Gaming Mouse Ultra-Light", "price": 99.99, "description": "Super lightweight gaming mouse at 63g with optical sensor, programmable buttons, and ultra-flexible paracord cable"},
        {"name": "Mechanical Keycaps Set", "price": 49.99, "description": "Double-shot PBT keycaps in cherry profile with dye-sub legends for durable and premium-feeling keyboard upgrade"},
        {"name": "Monitor Calibration Tool", "price": 199.99, "description": "Colorimeter for accurate monitor calibration with software for photographers and designers requiring color precision"},
        {"name": "Surge Protector Power Strip", "price": 44.99, "description": "12-outlet surge protector with 6ft cord, USB charging ports, and 4500 joule protection for valuable electronics"},
        {"name": "Laptop Stand Aluminum", "price": 69.99, "description": "Premium aluminum laptop stand with heat dissipation, adjustable height, and foldable design for ergonomic workspaces"},
    ],
}

USER_PREFERENCES = [
    "tech_enthusiast", "music_producer", "gamer", "remote_worker", "fitness_buff",
    "home_office", "creative_professional", "student", "content_creator", "programmer"
]

INTERACTION_TYPES = ["view", "purchase", "rate"]


def clear_existing_data():
    """Remove existing test data (idempotent cleanup)."""
    print("Checking for existing data...")
    
    # Check if data already exists
    existing = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    
    if existing.total > 0:
        print(f"Found {existing.total} existing products. Skipping seed (data already loaded).")
        print("To re-seed, manually delete records or use a fresh project.")
        return False
    
    return True


def generate_products():
    """Generate product catalog with descriptions."""
    print("\n[1/4] Generating product catalog...")
    
    products = []
    product_id = 1
    
    for category, items in PRODUCT_CATALOG.items():
        for item in items:
            products.append({
                "id": f"PROD-{product_id:04d}",
                "name": item["name"],
                "description": item["description"],
                "category": category,
                "price": item["price"]
            })
            product_id += 1
    
    print(f"  Generated {len(products)} products across {len(PRODUCT_CATALOG)} categories")
    return products


def create_products_and_embeddings(products):
    """Create products in RushDB and generate embeddings."""
    print("\n[2/4] Creating products and generating embeddings...")
    
    created_products = []
    descriptions = [p["description"] for p in products]
    
    # Generate all embeddings in batch
    print("  Computing embeddings...")
    embeddings = embedding_model.encode(descriptions, show_progress_bar=True)
    
    # Create vector index first
    print("  Creating vector index...")
    index = db.ai.indexes.create({
        "label": "PRODUCT",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,  # all-MiniLM-L6-v2 output dimension
        "similarityFunction": "cosine"
    })
    index_id = index.data["__id"]
    print(f"  Vector index created: {index_id}")
    
    # Create products and store embeddings
    print("  Creating products...")
    for i, product in enumerate(products):
        record = db.records.create(
            label="PRODUCT",
            data=product,
            vectors=[{"propertyName": "description", "vector": embeddings[i].tolist()}]
        )
        created_products.append(record)
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{len(products)} products...")
    
    print(f"  Created {len(created_products)} products with embeddings")
    return created_products, index_id


def generate_users():
    """Generate user accounts."""
    print("\n[3/4] Generating user accounts...")
    
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery", 
                   "Cameron", "Skyler", "Dakota", "Reese", "Parker", "Sage", "Blake",
                   "Drew", "Finley", "Hayden", "Jamie", "Kendall", "Logan", "Mackenzie",
                   "Nico", "Peyton", "Rowan", "Spencer", "Tatum", "Winter", "Zion", "Luna"]
    
    users = []
    for i, first_name in enumerate(first_names[:30]):
        users.append({
            "id": f"USER-{i+1:03d}",
            "username": f"{first_name.lower()}_{random.choice(['dev', 'pro', 'tech', 'audio', 'gamer'])}",
            "name": f"{first_name} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller'])}",
            "email": f"{first_name.lower()}.{i+1}@example.com",
            "preference": random.choice(USER_PREFERENCES),
            "join_date": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
        })
    
    print(f"  Generated {len(users)} users")
    return users


def create_users(users):
    """Create users in RushDB."""
    print("  Creating users in RushDB...")
    created_users = []
    
    for user in users:
        record = db.records.create(label="USER", data=user)
        created_users.append(record)
    
    print(f"  Created {len(created_users)} users")
    return created_users


def generate_interactions(users, products):
    """Generate user-product interactions."""
    print("\n[4/4] Generating user-product interactions...")
    
    interactions = []
    interaction_id = 1
    base_time = datetime.now()
    
    for user in users:
        # Each user has 8-15 interactions
        num_interactions = random.randint(8, 15)
        interacted_products = random.sample(products, min(num_interactions, len(products)))
        
        for product in interacted_products:
            # Weight towards purchases and views, less ratings
            interaction_type = random.choices(
                ["view", "purchase", "rate"],
                weights=[0.5, 0.3, 0.2]
            )[0]
            
            rating = None
            if interaction_type == "rate":
                rating = random.randint(3, 5)  # Positive ratings only
            elif interaction_type == "purchase":
                rating = random.choice([None, random.randint(4, 5)])  # Some purchases get rated
            
            interactions.append({
                "id": f"INT-{interaction_id:05d}",
                "type": interaction_type,
                "rating": rating,
                "timestamp": (base_time - timedelta(
                    days=random.randint(1, 90),
                    hours=random.randint(0, 23)
                )).isoformat()
            })
            interaction_id += 1
    
    print(f"  Generated {len(interactions)} interactions")
    return interactions


def create_interactions(interactions, users, products):
    """Create interaction records and attach to users/products."""
    print("  Creating interactions in RushDB...")
    
    created = 0
    user_map = {u.data["id"]: u for u in users}
    product_map = {p.data["id"]: p for p in products}
    
    for i, interaction in enumerate(interactions):
        # Find a random user-product pair
        user = random.choice(users)
        product = random.choice(products)
        
        # Create interaction record
        interaction_record = db.records.create(
            label="INTERACTION",
            data=interaction
        )
        
        # Attach relationships: USER -> INTERACTION -> PRODUCT
        db.records.attach(
            source=user,
            target=interaction_record,
            options={"type": "INTERACTED_WITH", "direction": "out"}
        )
        db.records.attach(
            source=interaction_record,
            target=product,
            options={"type": "INTERACTED_WITH", "direction": "out"}
        )
        
        created += 1
        if (i + 1) % 50 == 0:
            print(f"  Created {i + 1}/{len(interactions)} interactions...")
    
    print(f"  Created {created} interaction records with relationships")


def verify_data():
    """Verify data was created correctly."""
    print("\n[Verification]")
    
    products = db.records.find({"labels": ["PRODUCT"], "limit": 100})
    users = db.records.find({"labels": ["USER"], "limit": 100})
    interactions = db.records.find({"labels": ["INTERACTION"], "limit": 100})
    
    print(f"  Products: {products.total}")
    print(f"  Users: {users.total}")
    print(f"  Interactions: {interactions.total}")
    
    # Check vector index
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        stats = db.ai.indexes.stats(idx["__id"])
        print(f"  Vector index: {idx['label']}.{idx['propertyName']} - {stats.data.get('indexedRecords', 0)} indexed")


def main():
    print("=" * 60)
    print("RushDB Recommendation Engine - Data Seeding")
    print("=" * 60)
    
    start_time = time.time()
    
    # Check for existing data
    if not clear_existing_data():
        print("\nData already exists. Skipping seed.")
        verify_data()
        return
    
    # Generate and create products with embeddings
    products_data = generate_products()
    products, index_id = create_products_and_embeddings(products_data)
    
    # Generate and create users
    users_data = generate_users()
    users = create_users(users_data)
    
    # Generate and create interactions
    interactions = generate_interactions(users_data, products_data)
    create_interactions(interactions, users, products)
    
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Seeding complete in {elapsed:.1f} seconds!")
    print("=" * 60)
    
    verify_data()


if __name__ == "__main__":
    main()
