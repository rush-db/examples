#!/usr/bin/env python3
"""
Seed script for the custom vectorizers tutorial.

This script:
1. Creates a vector index for Book records
2. Generates embeddings for book descriptions
3. Creates Book records with associated vectors

Run this once to populate your RushDB project with test data.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB
from data.books import BOOKS

# Load environment variables
load_dotenv()


def main():
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)

    db = RushDB(api_key)

    # Use a fixed index name to make this idempotent
    INDEX_LABEL = "Book"
    INDEX_PROPERTY = "description"
    MODEL_NAME = "all-MiniLM-L6-v2"

    print("=" * 60)
    print("Seeding RushDB with Book records and embeddings")
    print("=" * 60)

    # Step 1: Check for existing index and clean up if present
    print("\n1. Checking for existing index...")
    existing_indexes = db.ai.indexes.find()
    for idx in existing_indexes.data:
        if idx["label"] == INDEX_LABEL and idx["propertyName"] == INDEX_PROPERTY:
            print(f"   Found existing index, deleting: {idx['__id']}")
            db.ai.indexes.delete(idx["__id"])

    # Step 2: Clean up existing books
    print("2. Cleaning up existing Book records...")
    existing_books = db.records.find({"labels": [INDEX_LABEL], "limit": 100})
    if existing_books.total > 0:
        for book in existing_books.data:
            db.records.delete(record_id=book.id)
        print(f"   Deleted {existing_books.total} existing books")

    # Step 3: Create external vector index
    print("3. Creating external vector index...")
    print(f"   Model: {MODEL_NAME} (384 dimensions)")
    index = db.ai.indexes.create({
        "label": INDEX_LABEL,
        "propertyName": INDEX_PROPERTY,
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine",
    })
    index_id = index.data["__id"]
    print(f"   Index created: {index_id}")

    # Step 4: Load embedding model
    print("4. Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"   Model loaded: {MODEL_NAME}")

    # Step 5: Create books and generate embeddings
    print("5. Creating Book records with embeddings...")
    records_created = []

    for i, book_data in enumerate(BOOKS):
        # Create the record
        record = db.records.create(
            label=INDEX_LABEL,
            data={
                "title": book_data["title"],
                "author": book_data["author"],
                "genre": book_data["genre"],
                "year": book_data["year"],
                "description": book_data["description"],
            }
        )
        records_created.append(record)

        # Generate embedding
        embedding = model.encode(book_data["description"]).tolist()

        # Print progress
        print(f"   [{i + 1}/{len(BOOKS)}] {book_data['title'][:40]:<40} ✓")

    # Step 6: Upsert all vectors
    print("\n6. Upserting vectors to index...")
    vector_items = [
        {"recordId": record.id, "vector": model.encode(BOOKS[i]["description"]).tolist()}
        for i, record in enumerate(records_created)
    ]
    db.ai.indexes.upsert_vectors(index_id, {"items": vector_items})
    print("   All vectors indexed successfully")

    # Step 7: Verify
    print("\n7. Verification:")
    stats = db.ai.indexes.stats(index_id)
    print(f"   Indexed records: {stats.data['indexedRecords']}")
    print(f"   Total records:   {stats.data['totalRecords']}")

    print("\n" + "=" * 60)
    print("Seeding complete! Run `python main.py` to test semantic search.")
    print("=" * 60)


if __name__ == "__main__":
    main()
