"""
Seed script for time-weighted graph traversal tutorial.

Generates realistic mock data:
- 50 users with browsing histories
- 200 products with descriptions (for vector search)
- 1000+ interactions (user-product edges with timestamps)

The data is designed to demonstrate recency-aware recommendations.
"""

import os
import random
import time
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB

# Initialize Faker for realistic data
fake = Faker()
Faker.seed(42)
random.seed(42)

# Product categories with realistic descriptions
PRODUCT_CATEGORIES = {
    "Electronics": {
        "items": [
            ("Wireless Bluetooth Headphones", "Premium noise-cancelling wireless headphones with 30-hour battery life and crystal-clear audio"),
            ("4K Ultra HD Smart TV", "55-inch 4K Smart TV with HDR support, built-in streaming apps, and voice control"),
            ("Mechanical Gaming Keyboard", "RGB backlit mechanical keyboard with Cherry MX switches and programmable macros"),
            ("Portable Power Bank", "20000mAh portable charger with fast charging support for all devices"),
            ("Smart Home Hub", "Central smart home controller compatible with Alexa, Google Home, and HomeKit"),
            ("Wireless Charging Pad", "Fast wireless charger compatible with Qi-enabled smartphones"),
            ("Laptop Stand", "Ergonomic aluminum laptop stand with adjustable height and cooling vents"),
            ("USB-C Hub Adapter", "7-in-1 USB-C hub with HDMI, USB-A, SD card reader, and ethernet"),
            ("Webcam HD 1080p", "Full HD webcam with auto-focus and built-in microphone for video calls"),
            ("Smart Watch Fitness Tracker", "Advanced fitness tracker with heart rate monitoring and GPS"),
        ],
        "base_price": (50, 500),
    },
    "Books": {
        "items": [
            ("The Art of Strategic Thinking", "Comprehensive guide to developing strategic thinking skills for business success"),
            ("Modern Python Cookbook", "Over 100 recipes for Python programming including async and type hints"),
            ("Data Science Fundamentals", "Introduction to data science, machine learning, and statistical analysis"),
            ("The Productivity Paradox", "Exploring why working harder doesn't always mean working smarter"),
            ("Creative Writing Masterclass", "Techniques from bestselling authors to unlock your creative potential"),
            ("History of the Digital Age", "How technology shaped society from the PC to the smartphone era"),
            ("Mindful Leadership", "Leading with emotional intelligence and presence in modern organizations"),
            ("The Startup Playbook", "Essential strategies for building and scaling a successful startup"),
            ("Psychology of Decision Making", "Understanding cognitive biases and improving judgment"),
            ("Introduction to Cloud Computing", "Cloud architecture, services, and deployment strategies explained"),
        ],
        "base_price": (10, 50),
    },
    "Sports": {
        "items": [
            ("Running Shoes Pro", "Lightweight running shoes with responsive cushioning for road running"),
            ("Yoga Mat Premium", "Extra-thick non-slip yoga mat with alignment lines for proper positioning"),
            ("Resistance Bands Set", "Set of 5 resistance bands with different tension levels for home workouts"),
            ("Fitness Tracker Watch", "Water-resistant fitness watch with step counter and sleep tracking"),
            ("Adjustable Dumbbells", "Space-saving adjustable dumbbells from 5 to 50 pounds"),
            ("Foam Roller Muscle", "High-density foam roller for muscle recovery and myofascial release"),
            ("Sports Water Bottle", "Insulated stainless steel water bottle keeps drinks cold for 24 hours"),
            ("Jump Rope Speed", "Professional speed jump rope with ball bearings for smooth rotation"),
            ("Exercise Ball Chair", "Ergonomic balance ball chair with air pump and stand"),
            ("Pull-Up Bar Door", "No-screw doorway pull-up bar with foam grips and multiple grip positions"),
        ],
        "base_price": (15, 150),
    },
    "Home": {
        "items": [
            ("Bamboo Cutting Board Set", "Set of 3 eco-friendly bamboo cutting boards with juice grooves"),
            ("Stainless Steel Cookware Set", "10-piece cookware set with tri-ply construction and oven-safe lids"),
            ("Memory Foam Pillow", "Ergonomic memory foam pillow with cooling gel technology"),
            ("LED Desk Lamp", "Adjustable LED desk lamp with wireless charging base and USB port"),
            ("Air Purifier HEPA", "True HEPA air purifier for rooms up to 500 sq ft with quiet mode"),
            ("Instant Pot Multi-Cooker", "7-in-1 electric pressure cooker, slow cooker, rice cooker, and more"),
            ("Robot Vacuum Cleaner", "Smart robot vacuum with app control, scheduling, and self-charging"),
            ("Scented Candle Collection", "Set of 6 natural soy candles in calming essential oil scents"),
            ("Blackout Curtains Pair", "Thermal insulated blackout curtains for better sleep and energy savings"),
            ("Indoor Plant Pot Set", "Set of 4 decorative ceramic pots with drainage and saucers"),
        ],
        "base_price": (20, 200),
    },
    "Music": {
        "items": [
            ("Acoustic Guitar Beginner", "Full-size acoustic guitar with nylon strings, ideal for beginners"),
            ("Portable Keyboard 61 Keys", "61-key portable keyboard with built-in sounds and lesson mode"),
            ("Studio Monitor Speakers", "Near-field studio monitors for accurate audio mixing"),
            ("XLR Microphone Bundle", "Professional condenser microphone with boom arm and pop filter"),
            ("Guitar Effects Pedal", "Multi-effects processor with amp modeling and USB audio interface"),
            ("Drum Practice Pad Set", "Electronic drum practice pads with adjustable sensitivity"),
            ("Violin Starter Kit", "Complete violin outfit for beginners with case, bow, and rosin"),
            ("Music Production DAW", "Digital audio workstation software for music production"),
            ("Guitar Cable 15ft", "Professional braided instrument cable with gold-plated connectors"),
            ("Metronome Digital", "Digital metronome with tempo tap and visual beat indicator"),
        ],
        "base_price": (25, 300),
    },
}


def generate_products(db: RushDB, count: int = 200) -> list:
    """Generate product records with descriptions."""
    print("\n📦 Generating products...")
    
    products = []
    
    # Flatten product list for random selection
    all_products = []
    for category, data in PRODUCT_CATEGORIES.items():
        for name, description in data["items"]:
            all_products.append((category, name, description, data["base_price"]))
    
    for i in range(count):
        category, name, description, (min_price, max_price) = random.choice(all_products)
        
        # Vary the product slightly to avoid exact duplicates
        variant = random.choice(["Pro", "Plus", "Elite", "Max", "Lite", "Ultra"])
        if random.random() > 0.7:
            full_name = f"{name} {variant}"
        else:
            full_name = name
        
        product_data = {
            "name": full_name,
            "description": description,
            "category": category,
            "price": round(random.uniform(min_price, max_price), 2),
            "sku": f"SKU-{category[:3].upper()}-{i:04d}",
        }
        
        product = db.records.create(label="PRODUCT", data=product_data)
        products.append(product)
        
        if (i + 1) % 50 == 0:
            print(f"  Created {i + 1}/{count} products")
    
    print(f"  ✓ Created {len(products)} products")
    return products


def generate_users(db: RushDB, count: int = 50) -> list:
    """Generate user records."""
    print("\n👤 Generating users...")
    
    users = []
    for i in range(count):
        user_data = {
            "username": f"user_{fake.user_name()}_{i}",
            "email": f"user_{i}_{fake.email()}",
            "member_since": (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat(),
            "preferred_category": random.choice(list(PRODUCT_CATEGORIES.keys())),
        }
        
        user = db.records.create(label="USER", data=user_data)
        users.append(user)
    
    print(f"  ✓ Created {len(users)} users")
    return users


def generate_interactions(db: RushDB, users: list, products: list) -> int:
    """Generate time-annotated user-product interactions."""
    print("\n🔗 Generating interactions (this may take a moment)...")
    
    interaction_types = ["VIEWED", "PURCHASED", "RATED", "ADDED_TO_CART"]
    
    # Generate interactions spanning the last 90 days
    now = datetime.now()
    total_interactions = 0
    
    with db.transactions.begin() as tx:
        for user in users:
            # Each user has 15-40 interactions
            num_interactions = random.randint(15, 40)
            
            for _ in range(num_interactions):
                product = random.choice(products)
                
                # Timestamp: weighted towards recent (more realistic)
                days_ago = random.expovariate(1/20)  # Exponential distribution favoring recent
                days_ago = min(days_ago, 90)  # Cap at 90 days
                timestamp = now - timedelta(days=days_ago)
                
                interaction_data = {
                    "timestamp": timestamp.isoformat(),
                    "interaction_type": random.choice(interaction_types),
                    "rating": random.randint(1, 5) if random.random() > 0.6 else None,
                    "session_id": fake.uuid4(),
                }
                
                interaction = db.records.create(
                    label="INTERACTION",
                    data=interaction_data,
                    transaction=tx
                )
                
                # Attach user -> interaction -> product
                db.records.attach(
                    source=user,
                    target=interaction,
                    options={"type": "MADE"},
                    transaction=tx
                )
                db.records.attach(
                    source=interaction,
                    target=product,
                    options={"type": "CONCERNS"},
                    transaction=tx
                )
                
                total_interactions += 1
                
                if total_interactions % 200 == 0:
                    print(f"  Created {total_interactions} interactions...")
        
        # Commit happens automatically when context manager exits
    
    print(f"  ✓ Created {total_interactions} interactions")
    return total_interactions


def check_existing_data(db: RushDB) -> bool:
    """Check if data already exists to avoid duplicate seeding."""
    try:
        result = db.records.find({"labels": ["PRODUCT"], "limit": 1})
        if result.data:
            return True
    except Exception:
        pass
    return False


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Time-Weighted Graph Traversal - Data Seeding")
    print("=" * 60)
    
    # Initialize RushDB
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        raise ValueError("RUSHDB_API_TOKEN not found in environment")
    
    db = RushDB(api_token)
    print("✓ Connected to RushDB")
    
    # Check for existing data
    if check_existing_data(db):
        print("\n⚠️  Data already exists. Skipping seed (idempotent).")
        print("   Delete existing records to re-seed.")
        return
    
    # Generate data
    products = generate_products(db, count=200)
    users = generate_users(db, count=50)
    interactions = generate_interactions(db, users, products)
    
    print("\n" + "=" * 60)
    print("✓ Seeding complete!")
    print(f"  • {len(users)} users")
    print(f"  • {len(products)} products")
    print(f"  • {interactions} interactions")
    print("=" * 60)
    print("\nRun `python main.py` to execute the tutorial.")


if __name__ == "__main__":
    main()
