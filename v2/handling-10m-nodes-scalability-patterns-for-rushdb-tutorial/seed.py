#!/usr/bin/env python3
"""
Seed Script: Generates mock product catalog data for scalability demonstrations.

This script creates a realistic e-commerce dataset:
- 10,000 PRODUCTS with descriptions, prices, and metadata
- 100 BRANDS with names and categories
- 50 CATEGORIES for product classification

The data demonstrates:
- Hierarchical relationships (Product -> Brand -> Category)
- Batch creation patterns
- Transaction batching

Run this once before main.py - it's idempotent and skips if data exists.
"""

import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rushdb import RushDB

# Initialize Faker for realistic data generation
fake = Faker()
Faker.seed(42)
random.seed(42)

# Configuration
BATCH_SIZE = 500  # Records per batch

# Sample data for realistic product generation
BRAND_PREFIXES = ["Pro", "Elite", "Ultra", "Max", "Prime", "Core", "Smart", "Flex"]
BRAND_SUFFIXES = ["Tech", "Gear", "Labs", "Works", "System", "Zone", "Hub", "Line"]

PRODUCT_TYPES = [
    "Wireless Headphones", "Mechanical Keyboard", "USB-C Hub", "4K Monitor",
    "Gaming Mouse", "Laptop Stand", "Webcam", "Microphone", "LED Strip",
    "Power Bank", "SSD Drive", "RAM Module", "Graphics Card", "CPU Cooler",
    "Smart Watch", "Fitness Tracker", "Portable Speaker", "E-Reader",
    "Tablet", "Drawing Tablet", "Network Switch", "Router", "NAS Drive"
]

CATEGORIES = [
    "Electronics", "Audio", "Computing", "Gaming", "Storage",
    "Accessories", "Networking", "Wearables", "Peripherals", "Components"
]


def load_env():
    """Load environment variables."""
    load_dotenv()
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError("RUSHDB_API_KEY environment variable is required")
    return api_key


def check_data_exists(db: RushDB) -> bool:
    """Check if seed data already exists."""
    result = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    return result.total > 0


def generate_brands(db: RushDB, count: int = 100) -> list[dict]:
    """Generate and create brand records in batches."""
    print(f"\nGenerating {count} brands...")
    
    brands = []
    used_names = set()
    
    for i in range(count):
        # Generate unique brand name
        name = None
        attempts = 0
        while name is None or name in used_names:
            prefix = random.choice(BRAND_PREFIXES)
            suffix = random.choice(BRAND_SUFFIXES)
            name = f"{prefix} {suffix}"
            if name in used_names:
                name = f"{prefix} {suffix} {fake.last_name()}"
            attempts += 1
            if attempts > 10:
                name = f"{prefix} {suffix} {i}"
        used_names.add(name)
        
        brand = {
            "name": name,
            "slug": fake.slug(),
            "category": random.choice(CATEGORIES),
            "founded": random.randint(1990, 2023),
            "country": fake.country_code(),
            "website": f"https://{fake.slug()}.com"
        }
        brands.append(brand)
    
    # Batch create brands
    db.records.create_many(label="BRAND", data=brands)
    print(f"Created {len(brands)} brands")
    
    return brands


def generate_categories(db: RushDB, count: int = 50) -> list[dict]:
    """Generate and create category records."""
    print(f"Generating {count} categories...")
    
    categories = []
    for i in range(count):
        category = {
            "name": fake.word().capitalize() + random.choice(["", "s", "Tech"]),
            "slug": fake.slug(),
            "description": fake.sentence(nb_words=10),
            "parentId": None  # Can be populated for hierarchy
        }
        categories.append(category)
    
    db.records.create_many(label="CATEGORY", data=categories)
    print(f"Created {len(categories)} categories")
    
    return categories


def generate_products(db: RushDB, brands: list[dict], categories: list[dict], count: int = 10000) -> list[dict]:
    """Generate product records in batches."""
    print(f"\nGenerating {count} products in batches of {BATCH_SIZE}...")
    
    products = []
    start_time = datetime.now()
    
    for i in range(count):
        product_type = random.choice(PRODUCT_TYPES)
        brand = random.choice(brands)
        category = random.choice(categories)
        
        product = {
            "name": f"{brand['name']} {product_type} {fake.numerify(text='Model-###')}",
            "slug": fake.slug(),
            "sku": f"SKU-{fake.numerify(text='######')}",
            "type": product_type,
            "brandName": brand['name'],
            "brandSlug": brand['slug'],
            "categoryName": category['name'],
            "price": round(random.uniform(19.99, 999.99), 2),
            "stock": random.randint(0, 1000),
            "rating": round(random.uniform(3.0, 5.0), 1),
            "reviewCount": random.randint(0, 500),
            "description": fake.paragraph(nb_sentences=3),
            "specs": {
                "weight": f"{random.randint(50, 5000)}g",
                "warranty": f"{random.choice([12, 24, 36])} months",
                "certification": random.choice(["CE", "FCC", "RoHS", "UL", None])
            },
            "tags": random.sample(["bestseller", "new", "sale", "eco-friendly", "premium", "budget"], k=random.randint(1, 3)),
            "createdAt": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
        }
        products.append(product)
        
        # Batch create every BATCH_SIZE products
        if len(products) >= BATCH_SIZE:
            db.records.create_many(label="PRODUCT", data=products)
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  Progress: {i + 1}/{count} products ({rate:.1f} records/sec)")
            products = []
    
    # Create remaining products
    if products:
        db.records.create_many(label="PRODUCT", data=products)
    
    total_time = (datetime.now() - start_time).total_seconds()
    print(f"Completed {count} products in {total_time:.1f}s ({count/total_time:.1f} records/sec)")



def create_relationships(db: RushDB, product_count: int = 10000):
    """Create relationships between products and brands/categories using batch operations."""
    print("\nCreating relationships (batch linking)...")
    
    # Fetch brands and categories
    brands = db.records.find({"labels": ["BRAND"], "limit": 1000})
    categories = db.records.find({"labels": ["CATEGORY"], "limit": 1000})
    
    print(f"  Found {brands.total} brands and {categories.total} categories")
    
    # For demonstration, we'll create sample relationships
    # In production, you'd iterate through products and link them
    
    # Create MANUFACTURED_BY relationships (sample)
    sample_count = min(100, product_count // 100)  # Link a sample for demonstration
    print(f"  Creating {sample_count} sample MANUFACTURED_BY relationships...")
    
    with db.transactions.begin() as tx:
        for i in range(sample_count):
            brand_idx = i % len(brands.data)
            product_result = db.records.find({
                "labels": ["PRODUCT"],
                "skip": i,
                "limit": 1
            })
            if product_result.data:
                product = product_result.data[0]
                brand = brands.data[brand_idx]
                
                # Link product to brand
                db.records.attach(
                    source=product,
                    target=brand,
                    options={"type": "MANUFACTURED_BY", "direction": "out"},
                    transaction=tx
                )
        # Auto-commit on success
    
    print(f"  Created {sample_count} relationships via transaction batching")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RushDB Scalability Demo - Data Seeding")
    print("=" * 60)
    
    # Load configuration
    api_key = load_env()
    
    # Initialize RushDB client
    db = RushDB(api_key)
    print(f"\nConnected to RushDB (API endpoint)")
    
    # Check if data already exists
    if check_data_exists(db):
        print("\n⚠️  Seed data already exists! Skipping seed.")
        print("   Run with --force to recreate data.")
        
        # Show current data stats
        products = db.records.find({"labels": ["PRODUCT"], "limit": 1})
        brands = db.records.find({"labels": ["BRAND"], "limit": 1})
        categories = db.records.find({"labels": ["CATEGORY"], "limit": 1})
        
        print(f"\nCurrent dataset:")
        print(f"  - Products: ~{products.total}")
        print(f"  - Brands: ~{brands.total}")
        print(f"  - Categories: ~{categories.total}")
        return
    
    # Generate data
    brands = generate_brands(db, count=100)
    categories = generate_categories(db, count=50)
    generate_products(db, brands, categories, count=10000)
    create_relationships(db, product_count=10000)
    
    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print("\nRun `python main.py` to execute scalability pattern demonstrations.")


if __name__ == "__main__":
    main()
