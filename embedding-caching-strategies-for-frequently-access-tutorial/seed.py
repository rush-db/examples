#!/usr/bin/env python3
"""
Seed script for RushDB Embedding Caching Tutorial

This script:
1. Cleans up existing data from previous runs
2. Creates sample article records with rich content
3. Creates an external vector index
4. Generates and stores embeddings for all articles

Run this once before running main.py
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Import RushDB
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("❌ Error: RUSHDB_API_KEY not found in environment")
    print("   Please copy .env.example to .env and add your API key")
    sys.exit(1)

# Configuration
ARTICLES_FILE = Path(__file__).parent / "data" / "articles.json"
INDEX_LABEL = "ARTICLE"
INDEX_PROPERTY = "content"
EMBEDDING_DIMENSIONS = 384  # Standard for all-MiniLM-L6-v2


def load_articles():
    """Load articles from JSON file."""
    with open(ARTICLES_FILE, "r") as f:
        return json.load(f)


def cleanup_existing_data(db):
    """Remove all existing articles and vector index for a fresh start."""
    print("\n[1] Cleaning up existing data...")
    
    # Delete existing articles
    existing = db.records.find({"labels": [INDEX_LABEL], "limit": 1000})
    if existing.data:
        ids_to_delete = [r.id for r in existing.data]
        for i in range(0, len(ids_to_delete), 50):
            batch = ids_to_delete[i:i+50]
            db.records.delete_many({"labels": [INDEX_LABEL], "where": {"__id": {"$in": batch}}})
        print(f"   ✓ Deleted {len(ids_to_delete)} existing articles")
    else:
        print("   ✓ No existing articles to clean up")
    
    # Delete existing vector index
    indexes = db.ai.indexes.find()
    for idx in indexes.data or []:
        if idx.get("label") == INDEX_LABEL:
            db.ai.indexes.delete(idx["__id"])
            print(f"   ✓ Deleted existing vector index")


def create_articles(db, articles_data):
    """Create article records in RushDB."""
    print("\n[2] Creating articles...")
    
    created_articles = []
    for i, article in enumerate(articles_data, 1):
        record = db.records.create(
            label=INDEX_LABEL,
            data={
                "title": article["title"],
                "content": article["content"],
                "category": article["category"],
                "tags": article["tags"]
            }
        )
        created_articles.append(record)
        
        if i % 5 == 0 or i == len(articles_data):
            print(f"   Created {i}/{len(articles_data)} articles...")
    
    print(f"   ✓ Created {len(created_articles)} articles")
    return created_articles


def create_vector_index(db):
    """Create external vector index for articles."""
    print("\n[3] Creating vector index...")
    
    # Check if index exists
    indexes = db.ai.indexes.find()
    for idx in indexes.data or []:
        if idx.get("label") == INDEX_LABEL and idx.get("propertyName") == INDEX_PROPERTY:
            print(f"   ✓ Vector index already exists: {idx['__id']}")
            return idx["__id"]
    
    # Create new index
    response = db.ai.indexes.create({
        "label": INDEX_LABEL,
        "propertyName": INDEX_PROPERTY,
        "sourceType": "external",
        "dimensions": EMBEDDING_DIMENSIONS,
        "similarityFunction": "cosine"
    })
    
    index_id = response.data["__id"]
    print(f"   ✓ Created vector index: {index_id}")
    return index_id


def generate_embeddings(articles, model_name="all-MiniLM-L6-v2"):
    """Generate embeddings for all article content using sentence-transformers."""
    print(f"\n[4] Loading embedding model ({model_name})...")
    start = time.time()
    model = SentenceTransformer(model_name)
    print(f"   ✓ Model loaded in {time.time() - start:.2f}s")
    
    print(f"\n[5] Generating embeddings for {len(articles)} articles...")
    embeddings = {}
    for i, article in enumerate(articles, 1):
        text = f"{article.data.get('title', '')} {article.data.get('content', '')}"
        vector = model.encode(text, normalize_embeddings=True).tolist()
        embeddings[article.id] = vector
        
        if i % 5 == 0 or i == len(articles):
            print(f"   Generated {i}/{len(articles)} embeddings...")
    
    print(f"   ✓ Generated {len(embeddings)} embeddings (dimension: {EMBEDDING_DIMENSIONS})")
    return embeddings


def upsert_vectors(db, index_id, embeddings):
    """Upload embeddings to RushDB vector index."""
    print("\n[6] Uploading vectors to RushDB...")
    
    items = [
        {"recordId": record_id, "vector": vector}
        for record_id, vector in embeddings.items()
    ]
    
    # Upsert in batches
    batch_size = 10
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        db.ai.indexes.upsert_vectors(index_id, {"items": batch})
        print(f"   Uploaded {min(i+batch_size, len(items))}/{len(items)} vectors...")
    
    print(f"   ✓ Uploaded {len(items)} vectors")


def verify_index(db, index_id, expected_count):
    """Verify that all vectors were indexed correctly."""
    print("\n[7] Verifying vector index...")
    
    stats = db.ai.indexes.stats(index_id)
    indexed = stats.data.get("indexedRecords", 0)
    total = stats.data.get("totalRecords", 0)
    
    print(f"   Indexed: {indexed}/{total} records")
    
    if indexed == expected_count:
        print(f"   ✓ All {expected_count} vectors successfully indexed")
    else:
        print(f"   ⚠ Warning: Expected {expected_count} vectors, got {indexed}")


def main():
    """Run the seeding process."""
    print("=" * 60)
    print("RushDB Embedding Caching Tutorial - Database Seeding")
    print("=" * 60)
    
    start_time = time.time()
    
    # Initialize RushDB
    print("\n[0] Connecting to RushDB...")
    db = RushDB(api_key)
    print(f"   ✓ Connected (endpoint: {db})")
    
    # Load articles
    articles_data = load_articles()
    print(f"   ✓ Loaded {len(articles_data)} articles from file")
    
    # Run seeding steps
    cleanup_existing_data(db)
    articles = create_articles(db, articles_data)
    index_id = create_vector_index(db)
    embeddings = generate_embeddings(articles)
    upsert_vectors(db, index_id, embeddings)
    verify_index(db, index_id, len(articles))
    
    # Save index ID for main.py
    index_info = {
        "index_id": index_id,
        "label": INDEX_LABEL,
        "property": INDEX_PROPERTY,
        "dimensions": EMBEDDING_DIMENSIONS
    }
    with open(".index_info.json", "w") as f:
        json.dump(index_info, f)
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"✓ Seeding complete in {elapsed:.1f}s")
    print("=" * 60)
    print("\nRun 'python main.py' to test the caching demo")


if __name__ == "__main__":
    main()
