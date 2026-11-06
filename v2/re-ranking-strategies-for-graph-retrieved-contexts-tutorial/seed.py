#!/usr/bin/env python3
"""
Seed script for the Re-ranking Strategies tutorial.

This script creates a knowledge base in RushDB with:
- Document records (12 technical articles)
- Chunk records (4 chunks per document)
- Relationships between related documents
- Vector embeddings for semantic search

Run this once before executing main.py.
"""

import json
import os
import sys
import time

import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for RushDB SDK
try:
    from rushdb import RushDB
except ImportError:
    print("❌ Error: rushdb package not found.")
    print("   Install with: pip install rushdb>=2.0.0")
    sys.exit(1)


def get_embeddings(texts: list, dimension: int = 384) -> list:
    """
    Generate embeddings for texts using sentence-transformers.
    Falls back to random vectors if transformer fails.
    """
    try:
        from sentence_transformers import SentenceTransformer
        print("   Loading sentence-transformers model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    except ImportError:
        print("   sentence-transformers not available, using random vectors")
        np.random.seed(42)
        return np.random.rand(len(texts), dimension).tolist()


def clear_existing_data(db: RushDB) -> bool:
    """Clear existing records to ensure clean seed state."""
    try:
        print("   Checking for existing data...")
        # Check for documents
        existing = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
        if existing.data:
            print("   Found existing data, clearing...")
            db.records.delete_many({"labels": ["CHUNK"], "where": {}})
            db.records.delete_many({"labels": ["DOCUMENT"], "where": {}})
            time.sleep(1)
            return True
        return False
    except Exception as e:
        print(f"   Note: {e}")
        return False


def create_vector_index(db: RushDB) -> str:
    """Create a vector index for chunk content search."""
    try:
        # Check for existing index
        existing = db.ai.indexes.find()
        for idx in existing.data:
            if idx.get("label") == "CHUNK" and idx.get("propertyName") == "content":
                return idx.get("__id")

        # Create new index
        print("   Creating vector index for CHUNK.content...")
        index = db.ai.indexes.create({
            "label": "CHUNK",
            "propertyName": "content",
            "dimensions": 384,
            "similarityFunction": "cosine",
            "sourceType": "external"
        })
        index_id = index.data.get("__id")
        print(f"   Created index: {index_id}")
        return index_id
    except Exception as e:
        print(f"   Warning creating index: {e}")
        return None


def main():
    print("\n" + "=" * 60)
    print("  SEEDING KNOWLEDGE BASE FOR RE-RANKING TUTORIAL")
    print("=" * 60 + "\n")

    # Initialize RushDB
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("❌ Error: RUSHDB_API_TOKEN not found in environment")
        print("   Copy .env.example to .env and add your RushDB API token")
        sys.exit(1)

    print(f"Connecting to RushDB...")
    db = RushDB(api_token)
    print("✓ Connected\n")

    # Clear existing data
    cleared = clear_existing_data(db)
    if cleared:
        print("✓ Cleared existing data\n")

    # Load seed data
    seed_file = os.path.join(os.path.dirname(__file__), "data", "seed_data.json")
    with open(seed_file, "r") as f:
        seed_data = json.load(f)

    documents_data = seed_data["documents"]
    print(f"Loaded {len(documents_data)} documents from seed data\n")

    # Phase 1: Create documents
    print("Phase 1: Creating document records...")
    doc_map = {}  # title -> record

    for i, doc in enumerate(documents_data):
        record = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc["title"],
                "category": doc["category"],
                "summary": doc["summary"],
                "chunkCount": len(doc["chunks"]),
                "createdAt": time.strftime("%Y-%m-%d")
            }
        )
        doc_map[doc["title"]] = record
        if (i + 1) % 4 == 0:
            print(f"  Created {i + 1}/{len(documents_data)} documents...")
        time.sleep(0.1)  # Rate limiting

    print(f"✓ Created {len(documents_data)} document records\n")

    # Phase 2: Create chunks with embeddings
    print("Phase 2: Creating chunk records with embeddings...")
    all_chunks = []
    chunk_to_doc = []  # Track which document each chunk belongs to

    for doc in documents_data:
        for chunk_text in doc["chunks"]:
            all_chunks.append(chunk_text)
            chunk_to_doc.append(doc_map[doc["title"]])

    # Generate embeddings for all chunks
    print("   Generating embeddings for all chunks...")
    embeddings = get_embeddings(all_chunks)

    # Create chunks in batches
    chunk_records = []
    chunk_vectors = []

    for i, (chunk_text, doc_record) in enumerate(zip(all_chunks, chunk_to_doc)):
        chunk_record = db.records.create(
            label="CHUNK",
            data={
                "content": chunk_text,
                "sourceDocId": doc_record.id,
                "sourceDocTitle": doc_record.data.get("title"),
                "chunkIndex": i % 4  # 0-3 for each document
            },
            vectors=[{"propertyName": "content", "vector": embeddings[i]}]
        )
        chunk_records.append(chunk_record)
        chunk_vectors.append({"recordId": chunk_record.id, "vector": embeddings[i]})

        if (i + 1) % 12 == 0:
            print(f"  Created {i + 1}/{len(all_chunks)} chunks...")
        time.sleep(0.05)

    print(f"✓ Created {len(chunk_records)} chunk records with embeddings\n")

    # Phase 3: Create relationships
    print("Phase 3: Creating document relationships...")
    rel_count = 0

    for doc in documents_data:
        source_doc = doc_map[doc["title"]]

        for related_title in doc.get("related", []):
            if related_title in doc_map:
                target_doc = doc_map[related_title]

                # Determine relationship type based on category
                if related_title in doc.get("related", [])[:2]:
                    rel_type = "CITES"
                else:
                    rel_type = "RELATED_TO"

                db.records.attach(
                    source=source_doc,
                    target=target_doc,
                    options={"type": rel_type, "direction": "out"}
                )
                rel_count += 1
                time.sleep(0.05)

    print(f"✓ Created {rel_count} relationships\n")

    # Phase 4: Create vector index and upsert vectors
    print("Phase 4: Setting up vector index...")
    index_id = create_vector_index(db)

    if index_id and chunk_vectors:
        print(f"   Upserting {len(chunk_vectors)} vectors to index...")
        db.ai.indexes.upsert_vectors(index_id, {"items": chunk_vectors})
        print(f"✓ Seeded vectors: {len(chunk_vectors)} indexed")
    else:
        print("⚠ Vector index skipped (not available in current environment)")

    # Summary
    print("\n" + "=" * 60)
    print("  SEED COMPLETE!")
    print("=" * 60)
    print(f"\n✅ {len(documents_data)} documents created")
    print(f"✅ {len(chunk_records)} chunks created")
    print(f"✅ {rel_count} relationships created")
    print(f"✅ {len(chunk_vectors)} vectors indexed")
    print(f"\nRun 'python main.py' to see the re-ranking demonstration.\n")


if __name__ == "__main__":
    main()
