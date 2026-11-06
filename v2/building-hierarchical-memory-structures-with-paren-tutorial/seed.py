"""
Seed script for hierarchical memory structures tutorial.

Creates a realistic product category hierarchy with sample products.
Safe to run multiple times - uses upsert for idempotency.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)


def clear_existing_data():
    """Remove all existing records for clean seeding."""
    labels_to_clear = ["CATEGORY", "PRODUCT"]
    for label in labels_to_clear:
        db.records.delete_many({"labels": [label], "where": {}})
    print("Cleared existing records")


def create_category_hierarchy():
    """Create the product category tree."""
    categories = {
        "Electronics": {"description": "Electronic devices and gadgets"},
        "Computers": {"description": "Computing devices"},
        "Laptops": {"description": "Portable computers"},
        "Smartphones": {"description": "Mobile phones"},
        "Clothing": {"description": "Apparel and garments"},
        "Footwear": {"description": "Shoes and boots"},
        "Accessories": {"description": "General accessories"},
    }

    # Create all categories using upsert for idempotency
    category_records = {}
    for name, data in categories.items():
        record = db.records.upsert(
            label="CATEGORY",
            data={"name": name, **data},
            options={"mergeBy": ["name"]}
        )
        category_records[name] = record
        print(f"Created: {name}")

    # Define parent relationships
    parent_links = [
        ("Electronics", "Computers"),
        ("Computers", "Laptops"),
        ("Computers", "Smartphones"),
        ("Clothing", "Footwear"),
        ("Clothing", "Accessories"),
    ]

    # Create parent-child links
    for parent_name, child_name in parent_links:
        parent = category_records[parent_name]
        child = category_records[child_name]
        
        # Detach first to ensure clean state, then re-attach
        try:
            db.records.detach(source=parent, target=child, options={"type": "PARENT_OF"})
        except Exception:
            pass  # May not exist yet
        
        db.records.attach(source=parent, target=child, options={"type": "PARENT_OF"})
        print(f"Linked {child_name} → {parent_name} (PARENT_OF)")

    return category_records


def create_sample_products(categories):
    """Create sample products under each category."""
    products_by_category = {
        "Laptops": [
            {"name": "ProBook 15", "price": 1299.99, "brand": "TechCorp"},
            {"name": "UltraSlim 13", "price": 1599.99, "brand": "SlimTech"},
            {"name": "GamerPro X", "price": 1899.99, "brand": "GameGear"},
            {"name": "Business Elite", "price": 1499.99, "brand": "TechCorp"},
            {"name": "StudentMate", "price": 699.99, "brand": "EduDevices"},
            {"name": "CreatorStudio", "price": 2199.99, "brand": "ArtisticTech"},
            {"name": "DeveloperPro", "price": 1799.99, "brand": "CodeMasters"},
            {"name": "TravelLight", "price": 999.99, "brand": "SlimTech"},
        ],
        "Smartphones": [
            {"name": "Pixel Max", "price": 999.99, "brand": "GooSoft"},
            {"name": "Galaxy Pro", "price": 1099.99, "brand": "SamDroid"},
            {"name": "OnePlus Ultra", "price": 899.99, "brand": "OnePlus"},
            {"name": "iPhone Elite", "price": 1199.99, "brand": "FruitCo"},
        ],
        "Footwear": [
            {"name": "Running Elite", "price": 129.99, "brand": "SpeedFit"},
            {"name": "Casual Classic", "price": 89.99, "brand": "ComfortCo"},
            {"name": "Hiking Pro", "price": 159.99, "brand": "TrailMaster"},
        ],
    }

    total_created = 0

    for category_name, products in products_by_category.items():
        category = categories[category_name]
        
        for product_data in products:
            # Use upsert to avoid duplicates on re-runs
            product = db.records.upsert(
                label="PRODUCT",
                data=product_data,
                options={"mergeBy": ["name", "brand"]}
            )
            
            # Attach product to category
            try:
                db.records.detach(source=product, target=category, options={"type": "BELONGS_TO"})
            except Exception:
                pass
            
            db.records.attach(
                source=product,
                target=category,
                options={"type": "BELONGS_TO"}
            )
            total_created += 1

    return total_created


def main():
    """Run the seed script."""
    print("=== Seeding Hierarchical Data ===\n")
    
    print("Clearing existing data...")
    clear_existing_data()
    
    print("\nCreating category hierarchy...")
    categories = create_category_hierarchy()
    
    print("\nCreating sample products...")
    product_count = create_sample_products(categories)
    print(f"Created {product_count} products")
    
    print("\nSeeding complete!")
    print(f"\nRun `python main.py` to explore the hierarchy")


if __name__ == "__main__":
    main()
