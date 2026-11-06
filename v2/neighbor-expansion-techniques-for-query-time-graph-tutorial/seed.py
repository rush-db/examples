"""
Seed script for the neighbor expansion tutorial.

Creates a product taxonomy with categories and products, establishing
relationships that enable multi-hop neighbor expansion queries.

This script is idempotent: it checks for existing data and skips seeding
if the data already exists. Safe to run multiple times.
"""

import json
import os
from pathlib import Path

from rushdb import RushDB


# Path to the sample data
DATA_DIR = Path(__file__).parent / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"

# Labels used in this tutorial
LABELS = {
    "category": "CATEGORY",
    "product": "PRODUCT",
}


def load_sample_data():
    """Load category and product data from JSON file."""
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)


def is_already_seeded(db: RushDB) -> bool:
    """Check if data has already been seeded by looking for a known category."""
    result = db.records.find({
        "labels": [LABELS["category"]],
        "where": {"slug": "category-electronics"},
        "limit": 1
    })
    return len(result) > 0


def create_vector_index_if_needed(db: RushDB):
    """Create the vector index for product descriptions if it doesn't exist."""
    # Check for existing indexes
    existing = db.ai.indexes.find()
    for idx in existing:
        if idx.get("label") == LABELS["product"] and idx.get("propertyName") == "description":
            print(f"  Vector index already exists: {idx['label']}.{idx['propertyName']}")
            return idx

    # Create new index for product descriptions
    print("  Creating vector index for PRODUCT.description...")
    index = db.ai.indexes.create({
        "label": LABELS["product"],
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 8,
        "similarityFunction": "cosine"
    })
    return index


def seed_categories(db: RushDB, categories_data: list) -> dict:
    """Create category records and return a mapping of slug to record."""
    print(f"  Creating {len(categories_data)} categories...")
    created = {}

    for i, cat in enumerate(categories_data):
        # Upsert category (idempotent)
        record = db.records.upsert(
            label=LABELS["category"],
            data={
                "name": cat["name"],
                "slug": cat["slug"],
                "parentSlug": cat["parentSlug"],
            },
            options={"mergeBy": ["slug"]}
        )
        created[cat["slug"]] = record

        if (i + 1) % 4 == 0:
            print(f"    {i + 1}/{len(categories_data)} categories created...")

    return created


def establish_category_hierarchy(db: RushDB, categories_data: list, category_records: dict):
    """Create PARENT_OF relationships to form the category taxonomy."""
    print("  Establishing category hierarchy...")
    link_count = 0

    for cat in categories_data:
        if cat["parentSlug"] and cat["parentSlug"] in category_records:
            child_record = category_records[cat["slug"]]
            parent_record = category_records[cat["parentSlug"]]

            # Attach child to parent with PARENT_OF relationship
            db.records.attach(
                source=parent_record,
                target=child_record,
                options={"type": "PARENT_OF", "direction": "out"}
            )
            link_count += 1

    print(f"    {link_count} PARENT_OF relationships created")


def seed_products(db: RushDB, products_data: list, category_records: dict):
    """Create product records and link them to categories."""
    print(f"  Creating {len(products_data)} products...")

    for i, prod in enumerate(products_data):
        # Create product with vector embedding
        product = db.records.upsert(
            label=LABELS["product"],
            data={
                "name": prod["name"],
                "slug": prod["slug"],
                "description": prod["description"],
                "price": prod["price"],
                "categorySlug": prod["categorySlug"],
            },
            options={"mergeBy": ["slug"]},
            vectors=[{
                "propertyName": "description",
                "vector": prod["vector"]
            }]
        )

        # Link product to its category
        if prod["categorySlug"] in category_records:
            category = category_records[prod["categorySlug"]]
            db.records.attach(
                source=product,
                target=category,
                options={"type": "BELONGS_TO", "direction": "out"}
            )

        if (i + 1) % 5 == 0:
            print(f"    {i + 1}/{len(products_data)} products created...")



def seed_database(db: RushDB):
    """
    Seed the database with sample product taxonomy data.

    Creates:
    - 8 category records arranged in a 3-level hierarchy
    - 15 product records with vector embeddings
    - BELONGS_TO relationships (product → category)
    - PARENT_OF relationships (category → parent category)
    """
    print("\n--- Seeding Database ---")

    # Check if already seeded
    if is_already_seeded(db):
        print("  Data already exists, skipping seed.")
        create_vector_index_if_needed(db)
        return

    # Load sample data
    data = load_sample_data()
    categories_data = data["categories"]
    products_data = data["products"]

    print(f"  Loaded {len(categories_data)} categories and {len(products_data)} products")

    # Create vector index first
    create_vector_index_if_needed(db)

    # Create categories
    category_records = seed_categories(db, categories_data)

    # Establish hierarchy
    establish_category_hierarchy(db, categories_data, category_records)

    # Create products
    seed_products(db, products_data, category_records)

    print("  Seeding complete!")


if __name__ == "__main__":
    # Initialize RushDB
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY environment variable is not set.")
        print("See .env.example for configuration instructions.")
        exit(1)

    db = RushDB(api_key)
    seed_database(db)
