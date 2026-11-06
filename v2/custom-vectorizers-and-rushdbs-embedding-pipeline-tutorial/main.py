#!/usr/bin/env python3
"""
Custom Vectorizers and RushDB's Embedding Pipeline Tutorial

This example demonstrates how to use RushDB with your own embedding model
(external vectorizer) instead of RushDB's managed embedding service.

Key concepts covered:
1. Creating an external vector index with custom dimensions
2. Generating embeddings locally with sentence-transformers
3. Associating pre-computed vectors with RushDB records
4. Performing semantic search using your custom vectors

This is the main tutorial file. Run `python seed.py` first to populate data,
or run this file directly to see the full pipeline including data creation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB
from sentence_transformers import SentenceTransformer
from data.books import BOOKS

# Load environment variables
load_dotenv()


def get_or_create_index(db: RushDB, model_dimensions: int):
    """
    Get existing index or create a new one.
    For clean demos, we delete and recreate.
    """
    INDEX_LABEL = "Book"
    INDEX_PROPERTY = "description"

    # Check for existing
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx["label"] == INDEX_LABEL and idx["propertyName"] == INDEX_PROPERTY:
            return idx["__id"]

    # Create new external index
    result = db.ai.indexes.create({
        "label": INDEX_LABEL,
        "propertyName": INDEX_PROPERTY,
        "sourceType": "external",
        "dimensions": model_dimensions,
        "similarityFunction": "cosine",
    })
    return result.data["__id"]


def cleanup(db: RushDB, index_id: str):
    """Clean up test data and index."""
    print("\n6. Cleanup: deleting test records and index...")
    
    # Delete all Book records
    books = db.records.find({"labels": ["Book"], "limit": 100})
    for book in books.data:
        db.records.delete(record_id=book.id)
    print(f"   ✓ Deleted {books.total} Book records")
    
    # Delete the index
    db.ai.indexes.delete(index_id)
    print("   ✓ Index deleted")


def main():
    # === Setup ===
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)

    db = RushDB(api_key)

    # Model configuration
    MODEL_NAME = "all-MiniLM-L6-v2"
    INDEX_LABEL = "Book"
    INDEX_PROPERTY = "description"

    print("=" * 60)
    print("Custom Vectorizers & RushDB Embedding Pipeline")
    print("=" * 60)

    # === Step 1: Create External Vector Index ===
    print("\n1. Creating external vector index for Book descriptions...")
    
    # Load model to get dimensions
    model = SentenceTransformer(MODEL_NAME)
    embedding_dimensions = model.get_sentence_embedding_dimension()
    print(f"   Model: {MODEL_NAME}")
    print(f"   Dimensions: {embedding_dimensions}")
    
    # Create external index (sourceType: "external" means YOU provide vectors)
    index = db.ai.indexes.create({
        "label": INDEX_LABEL,
        "propertyName": INDEX_PROPERTY,
        "sourceType": "external",
        "dimensions": embedding_dimensions,
        "similarityFunction": "cosine",
    })
    index_id = index.data["__id"]
    print(f"   Index created: {index_id}")
    print(f"   Status: {index.data['status']}")

    # === Step 2: Create Book Records ===
    print(f"\n2. Creating {len(BOOKS)} Book records...")
    
    created_records = []
    for book_data in BOOKS:
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
        created_records.append(record)
        print(f"   ✓ '{book_data['title'][:35]}...' created")

    # === Step 3: Generate Embeddings ===
    print(f"\n3. Generating embeddings for all books...")
    print(f"   Using model: {MODEL_NAME}")
    
    embeddings = []
    for book_data in BOOKS:
        # Generate embedding for the description
        vector = model.encode(book_data["description"]).tolist()
        embeddings.append(vector)
    
    # Simple progress visualization
    print(f"   [{'=' * 20}] 100% ({len(embeddings)}/{len(embeddings)})")

    # === Step 4: Upsert Vectors to Index ===
    print("\n4. Upserting vectors to index...")
    
    # Prepare vector items: recordId + vector pairs
    vector_items = [
        {
            "recordId": record.id,
            "vector": embeddings[i],
        }
        for i, record in enumerate(created_records)
    ]
    
    # Upsert all vectors at once
    db.ai.indexes.upsert_vectors(index_id, {"items": vector_items})
    print("   ✓ All vectors indexed successfully")

    # === Step 5: Semantic Search ===
    print("\n5. Running semantic searches...")
    
    # Define search queries
    queries = [
        "software engineering best practices",
        "algorithms and data structures",
    ]
    
    for query_text in queries:
        print(f"\n   Query: \"{query_text}\"")
        print("   " + "-" * 45)
        
        # Generate query vector locally
        query_vector = model.encode(query_text).tolist()
        
        # Search using the pre-computed query vector
        # Note: queryVector (not query) when using external index
        results = db.ai.search({
            "propertyName": INDEX_PROPERTY,
            "queryVector": query_vector,
            "labels": [INDEX_LABEL],
            "limit": 5,
        })
        
        # Display results
        for result in results.data:
            score = result.score if hasattr(result, 'score') else result.data.get("__score", 0)
            title = result["title"]
            author = result["author"]
            # Truncate long titles
            display_title = title[:35] + "..." if len(title) > 35 else title
            print(f"   [{score:.3f}] {display_title} ({author})")

    # === Step 6: Cleanup ===
    # Uncomment to clean up after demo:
    # cleanup(db, index_id)

    print("\n" + "=" * 60)
    print("Demo complete! Check RushDB dashboard for your indexed data.")
    print("=" * 60)


if __name__ == "__main__":
    main()
