"""
Mock data generator for batch processing tutorial.
Creates 1000 product records with realistic attributes.

Run this once to seed the database before running main.py.
The script is idempotent and safe to run multiple times.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
db = RushDB(api_key=os.getenv('RUSHDB_API_KEY'))

# Product data templates
CATEGORIES = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys']
BRANDS = ['TechCorp', 'StyleMax', 'HomePlus', 'SportElite', 'BookWorld', 'PlayFun']
CONDITIONS = ['new', 'refurbished', 'used']


def generate_product(index: int) -> dict:
    """Generate a single product record with realistic attributes."""
    return {
        'sku': f'SKU-{index:06d}',
        'name': f'Product {index}',
        'description': f'High-quality product with excellent features. SKU: SKU-{index:06d}',
        'price': round(random.uniform(9.99, 999.99), 2),
        'category': random.choice(CATEGORIES),
        'brand': random.choice(BRANDS),
        'condition': random.choice(CONDITIONS),
        'stock': random.randint(0, 500),
        'weight_kg': round(random.uniform(0.1, 20.0), 2),
        'tags': random.sample(['featured', 'bestseller', 'new', 'sale', 'limited'], k=random.randint(1, 3))
    }


def clear_existing_data():
    """Remove existing PRODUCT records for clean seeding."""
    print("Clearing existing product records...")
    db.records.delete_many({"labels": ["PRODUCT"], "where": {}})
    print("  ✓ Cleared existing data")


def seed_products(total: int = 1000, chunk_size: int = 100):
    """Seed database with product records in chunks."""
    print(f"\nSeeding {total} products in chunks of {chunk_size}...")
    
    created = 0
    for i in range(0, total, chunk_size):
        batch = [generate_product(j) for j in range(i + 1, min(i + chunk_size + 1, total + 1))]
        db.records.create_many(label="PRODUCT", data=batch)
        created += len(batch)
        
        if (i + chunk_size) % 500 == 0 or created == total:
            print(f"  ✓ Created {created}/{total} products")
    
    return created


def main():
    """Run the seeding process."""
    print("=" * 60)
    print("RushDB Batch Processing Tutorial - Data Seeding")
    print("=" * 60)
    
    # Check if data already exists
    existing = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    if existing.total > 0:
        response = input(f"\nFound {existing.total} existing products. Clear and reseed? (y/n): ")
        if response.lower() != 'y':
            print("Seeding cancelled. Existing data will be used.")
            return
        clear_existing_data()
    
    # Seed the data
    print("\nGenerating mock product data...")
    created = seed_products(total=1000, chunk_size=100)
    
    print(f"\n✓ Seeding complete! Created {created} product records.")
    print("\nYou can now run `python main.py` to see batch processing patterns.")


if __name__ == "__main__":
    main()
