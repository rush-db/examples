#!/usr/bin/env python3
"""
Seed script: Initializes RushDB with product catalog and vector index.

This script is idempotent — running it multiple times is safe.
It checks for existing data before creating new records.
"""

import os
import sys
from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

API_TOKEN = os.getenv("RUSHDB_API_TOKEN")
if not API_TOKEN:
    print("ERROR: RUSHDB_API_TOKEN not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

# Product catalog — realistic electronics store items
PRODUCTS = [
    {
        "sku": "PHB15-2024",
        "name": "ProBook 15",
        "brand": "ProTech",
        "category": "laptop",
        "price": 1299.99,
        "specs": {
            "processor": "Intel Core i7-13700H",
            "ram": "16GB DDR5",
            "storage": "512GB NVMe SSD",
            "display": '15.6" 4K OLED',
            "gpu": "NVIDIA RTX 4060"
        },
        "stock": 4,
        "warranty_months": 24,
        "description": "Professional laptop optimized for video editing and 3D rendering. Features a powerful RTX 4060 GPU and stunning 4K OLED display perfect for color-accurate work."
    },
    {
        "sku": "AS14-ULTRA",
        "name": "AeroSlim 14",
        "brand": "AirCore",
        "category": "laptop",
        "price": 899.99,
        "specs": {
            "processor": "AMD Ryzen 7 7840U",
            "ram": "16GB LPDDR5",
            "storage": "256GB NVMe SSD",
            "display": '14" 2.8K IPS',
            "gpu": "Integrated Radeon 780M"
        },
        "stock": 12,
        "warranty_months": 12,
        "description": "Ultra-thin productivity laptop with excellent battery life. Ideal for office work and web development. Lightweight aluminum chassis weighs only 1.2kg."
    },
    {
        "sku": "PXB-GO-13",
        "name": "PixelBook Go",
        "brand": "ChromeWorks",
        "category": "laptop",
        "price": 649.99,
        "specs": {
            "processor": "Intel Core m3-8100Y",
            "ram": "8GB LPDDR3",
            "storage": "128GB eMMC",
            "display": '13.3" Full HD',
            "gpu": "Integrated UHD 615"
        },
        "stock": 8,
        "warranty_months": 12,
        "description": "Chromebook with premium design and quiet operation. Perfect for students and cloud-first workflows. Hush keyboard and 12-hour battery life."
    },
    {
        "sku": "WRK-ST-24",
        "name": "WorkStation Pro",
        "brand": "ProTech",
        "category": "desktop",
        "price": 2499.99,
        "specs": {
            "processor": "AMD Threadripper 7980X",
            "ram": "128GB DDR5 ECC",
            "storage": "2TB NVMe RAID 0",
            "gpu": "NVIDIA RTX 4090",
            "cooling": "Liquid cooling"
        },
        "stock": 2,
        "warranty_months": 36,
        "description": "High-end workstation for professionals. Handles 8K video editing, complex simulations, and machine learning workloads. Built for sustained heavy loads."
    }
]

# ============================================================================
# Main seeding logic
# ============================================================================

def check_existing_data(db):
    """Check if products already exist — enables idempotent seeding."""
    existing = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    return len(existing) > 0


def create_vector_index(db):
    """Create or verify vector index for product descriptions."""
    # Check for existing index
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        if idx["label"] == "PRODUCT" and idx["propertyName"] == "description":
            print(f"  ✓ Vector index already exists (status: {idx['status']})")
            return idx
    
    # Create new index (external source type — we provide our own embeddings)
    print("  Creating vector index for product descriptions...")
    index = db.ai.indexes.create({
        "label": "PRODUCT",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,  # sentence-transformers default
        "similarityFunction": "cosine"
    })
    print(f"  ✓ Vector index created: {index.data['__id']}")
    return index.data


def generate_embeddings(products):
    """Generate vector embeddings for product descriptions."""
    print("  Loading sentence-transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    embeddings = []
    for product in products:
        text = f"{product['name']}: {product['description']}"
        vector = model.encode(text).tolist()
        embeddings.append({
            "recordId": None,  # Will be set after record creation
            "vector": vector
        })
    
    return embeddings


def seed_products(db, product_index):
    """Create or update product records with embeddings."""
    print("\n[1] Syncing product catalog...")
    
    existing_products = {}
    existing = db.records.find({"labels": ["PRODUCT"], "limit": 100})
    for p in existing:
        existing_products[p["sku"]] = p
    
    embeddings = generate_embeddings(PRODUCTS)
    index_id = product_index["__id"]
    
    for i, product_data in enumerate(PRODUCTS):
        if product_data["sku"] in existing_products:
            print(f"  ✓ Already exists: {product_data['name']}")
            # Update embeddings for existing products
            existing_id = existing_products[product_data["sku"]].id
            embeddings[i]["recordId"] = existing_id
            continue
        
        # Create new product with inline vector
        product = db.records.create(
            label="PRODUCT",
            data=product_data,
            vectors=[{"propertyName": "description", "vector": embeddings[i]["vector"]}]
        )
        embeddings[i]["recordId"] = product.id
        print(f"  ✓ Created: {product_data['name']} (ID: {product.id[:16]}...)")
    
    # Upsert vectors to the index
    print("\n[2] Indexing embeddings...")
    db.ai.indexes.upsert_vectors(index_id, {"items": embeddings})
    print(f"  ✓ {len(embeddings)} vectors indexed")
    
    return {p["sku"]: p for p in PRODUCTS}


def create_sample_sessions(db, products):
    """Create sample conversation sessions for demonstration."""
    print("\n[3] Creating sample conversation sessions...")
    
    # Check for existing sessions
    existing = db.records.find({"labels": ["SESSION"], "limit": 1})
    if existing:
        print("  ✓ Sessions already exist, skipping...")
        return
    
    probook = next(p for p in db.records.find({"labels": ["PRODUCT"]}) 
                   if p["sku"] == "PHB15-2024")
    
    # Session 1: Initial inquiry
    session1 = db.records.create(
        label="SESSION",
        data={
            "user_id": "user_123",
            "started_at": "2024-01-15T10:30:00Z",
            "channel": "web_chat"
        }
    )
    
    message1 = db.records.create(
        label="MESSAGE",
        data={
            "role": "user",
            "content": "I need a laptop for video editing",
            "timestamp": "2024-01-15T10:30:15Z"
        }
    )
    db.records.attach(source=message1, target=session1, options={"type": "BELONGS_TO"})
    db.records.attach(source=message1, target=probook, options={"type": "REFERS_TO"})
    
    # Track entity reference
    ref1 = db.records.create(
        label="ENTITY_REFERENCE",
        data={
            "raw_text": "laptop for video editing",
            "resolution_strategy": "semantic_search",
            "confidence": 0.94
        }
    )
    db.records.attach(source=ref1, target=message1, options={"type": "TRACKS")})
    db.records.attach(source=ref1, target=probook, options={"type": "RESOLVED_TO"})
    
    print(f"  ✓ Created Session 1 with initial inquiry")
    
    # Session 2: Follow-up about same product
    session2 = db.records.create(
        label="SESSION",
        data={
            "user_id": "user_123",
            "started_at": "2024-01-16T14:00:00Z",
            "channel": "web_chat"
        }
    )
    
    message2 = db.records.create(
        label="MESSAGE",
        data={
            "role": "user",
            "content": "Is the laptop I looked at still available?",
            "timestamp": "2024-01-16T14:00:10Z"
        }
    )
    db.records.attach(source=message2, target=session2, options={"type": "BELONGS_TO"})
    db.records.attach(source=message2, target=probook, options={"type": "REFERS_TO"})
    
    ref2 = db.records.create(
        label="ENTITY_REFERENCE",
        data={
            "raw_text": "the laptop I looked at",
            "resolution_strategy": "session_history",
            "confidence": 1.0
        }
    )
    db.records.attach(source=ref2, target=message2, options={"type": "TRACKS"})
    db.records.attach(source=ref2, target=probook, options={"type": "RESOLVED_TO"})
    db.records.attach(source=session2, target=session1, options={"type": "CONTINUES"})
    
    print(f"  ✓ Created Session 2 with entity resolution via history")
    print(f"  ✓ Sessions linked via CONTINUES relationship")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RushDB Entity Tracking — Seed Script")
    print("=" * 60)
    
    # Initialize RushDB client
    db = RushDB(API_TOKEN)
    print(f"\n✓ Connected to RushDB")
    
    # Check for existing data
    if check_existing_data(db):
        print("\n⚠ Products already exist in database.")
        print("  Run with --force to re-seed (coming soon)")
        print("\nTo clear data, delete the project in the RushDB dashboard.")
        sys.exit(0)
    
    # Create vector index
    index = create_vector_index(db)
    
    # Seed products with embeddings
    products = seed_products(db, index)
    
    # Create sample sessions
    create_sample_sessions(db, products)
    
    print("\n" + "=" * 60)
    print("✓ Seeding complete!")
    print("=" * 60)
    print("\nRun 'python main.py' to execute the entity tracking demo.")


if __name__ == "__main__":
    main()
