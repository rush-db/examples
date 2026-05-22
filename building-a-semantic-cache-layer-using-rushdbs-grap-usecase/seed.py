#!/usr/bin/env python3
"""
Seed script for the semantic cache layer demo.

Generates mock cache entries (query/response pairs) with embeddings,
creates session nodes, links semantically similar queries via graph edges,
and creates data source nodes with invalidation relationships.

This script is idempotent — safe to run multiple times.
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

from rushdb import RushDB

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, 384-dim, great for demos
INDEX_LABEL = "CACHE_ENTRY"
INDEX_PROPERTY = "query"

# ─────────────────────────────────────────────────────────────────────────────
# Sample data — realistic LLM query/response pairs
# ─────────────────────────────────────────────────────────────────────────────

QUERIES = [
    # Programming questions
    ("how do I reverse a list in python", "Use list[::-1] or reversed(list). Example: nums[::-1] creates a new reversed list."),
    ("python list reverse function", "The list.reverse() method reverses in-place. For a new list, use reversed() or slicing: list[::-1]."),
    ("explain python list comprehension", "List comprehension: [expr for item in iterable if condition]. It's concise and faster than loops."),
    ("what is a list comprehension in python", "A list comprehension creates a list from iterables: [x*2 for x in range(10)]."),
    ("how to sort a dictionary by value in python", "Use sorted(d.items(), key=lambda x: x[1]) or dict(sorted(d.items(), key=lambda x: x[1]))."),
    ("python sort dictionary by value", "sorted(dict.items(), key=lambda kv: kv[1]) returns key-value pairs sorted by value."),
    
    # Data science
    ("what is machine learning", "Machine learning is a subset of AI where algorithms learn patterns from data to make predictions."),
    ("explain ml algorithms", "Common ML algorithms: Linear Regression (continuous), Logistic Regression (binary), Decision Trees, Random Forests, Neural Networks."),
    ("how does random forest work", "Random Forest builds multiple decision trees on bootstrapped data and averages predictions for robustness."),
    ("what is overfitting in ml", "Overfitting occurs when a model learns training data noise, performing poorly on new data. Solutions: regularization, cross-validation."),
    ("difference between supervised and unsupervised learning", "Supervised: labeled data (classification, regression). Unsupervised: no labels (clustering, dimensionality reduction)."),
    
    # Database questions
    ("how to optimize postgresql queries", "Use EXPLAIN ANALYZE, add indexes on WHERE/JOIN columns, avoid SELECT *, normalize schema."),
    ("postgres query optimization tips", "Key strategies: index frequently queried columns, use partial indexes, avoid functions on indexed columns in WHERE."),
    ("what is database indexing", "An index is a data structure that speeds up data retrieval, like a book index. Common types: B-tree, Hash, GIN."),
    
    # Web development
    ("how does react useeffect work", "useEffect runs after render. Use it for side effects: useEffect(() => { ... }, [deps]). Cleanup with return function."),
    ("react hooks explained", "React hooks let you use state and lifecycle in functional components: useState, useEffect, useContext, useMemo, useCallback."),
    ("explain async await in javascript", "async/await makes Promises readable. async functions return Promises. await pauses execution until Promise resolves."),
    ("javascript async await tutorial", "const data = await fetch(url); wraps the Promise. Wrap in try/catch for errors. Runs non-blocking."),
    
    # DevOps
    ("how to set up docker container", "Dockerfile: FROM, COPY, RUN, CMD. Build: docker build -t name . Run: docker run -p 8080:80 name."),
    ("docker container basics", "Containers package code + dependencies. Image is a template, container is a running instance. docker run starts from image."),
    ("what is kubernetes deployment", "Kubernetes orchestrates containers: pods (smallest unit), deployments (replica management), services (networking)."),
    
    # Product catalog queries (for invalidation demo)
    ("show me running shoes under 100", "Here are running shoes under $100: Nike Air Max 90 ($95), Adidas Ultraboost ($99)..."),
    ("cheapest wireless headphones", "Top cheap wireless headphones: Soundcore Anker ($35), JBL Tune ($49), Sony WH-CH510 ($50)."),
    ("laptop recommendations for students", "Best student laptops: MacBook Air M2 ($999), Dell XPS 13 ($899), Lenovo ThinkPad ($849)."),
    ("best gaming monitors 2024", "Top gaming monitors: ASUS ROG Swift 360Hz, LG 27GP950-B 4K 144Hz, Samsung Odyssey G7."),
    ("smartphone comparison iphone vs android", "iPhone: seamless ecosystem, long updates. Android: variety, customization, often better value."),
]

# Data sources that can invalidate cache entries
DATA_SOURCES = [
    {"name": "product_catalog", "entity_type": "products"},
    {"name": "pricing_service", "entity_type": "prices"},
    {"name": "user_preferences", "entity_type": "user_settings"},
]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def generate_sessions(num_sessions=5):
    """Generate mock session data."""
    sessions = []
    base_time = datetime.now() - timedelta(days=7)
    for i in range(num_sessions):
        sessions.append({
            "session_id": f"sess_{i:03d}",
            "user_id": f"user_{random.randint(1, 10):03d}",
            "created_at": (base_time + timedelta(hours=i * 12)).isoformat(),
            "is_active": i >= num_sessions - 2,  # Last 2 are active
        })
    return sessions


def generate_cache_entry_record(query: str, response: str):
    """Return the data dict for a cache entry record."""
    return {
        "query": query,
        "response": response,
        "created_at": datetime.now().isoformat(),
        "ttl_seconds": random.choice([3600, 7200, 14400, 86400]),  # 1h to 24h
        "hit_count": random.randint(0, 50),
    }


def compute_embeddings(texts: list[str], model) -> list[list[float]]:
    """Compute embeddings for a list of texts."""
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot / (norm_a * norm_b + 1e-8)


def find_similar_pairs(embeddings: list[list[float]], threshold: float = 0.75) -> list[tuple[int, int]]:
    """Find pairs of queries with cosine similarity above threshold."""
    pairs = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= threshold:
                pairs.append((i, j, sim))
    return pairs


def clear_existing_data(db: RushDB):
    """Remove existing cache data for a clean seed."""
    print("\nClearing existing cache data...")
    
    # Delete all cache entries
    result = db.records.delete({"labels": ["CACHE_ENTRY"], "where": {}})
    print(f"  Deleted {result.data.get('deletedCount', 0)} CACHE_ENTRY records")
    
    # Delete sessions
    result = db.records.delete({"labels": ["SESSION"], "where": {}})
    print(f"  Deleted {result.data.get('deletedCount', 0)} SESSION records")
    
    # Delete data sources
    result = db.records.delete({"labels": ["DATA_SOURCE"], "where": {}})
    print(f"  Deleted {result.data.get('deletedCount', 0)} DATA_SOURCE records")


# ─────────────────────────────────────────────────────────────────────────────
# Main seeding logic
# ─────────────────────────────────────────────────────────────────────────────

def seed():
    """Seed the database with cache entries, sessions, and relationships."""
    
    print("=" * 60)
    print("SEMANTIC CACHE SEEDER")
    print("=" * 60)
    
    # Initialize RushDB
    token = os.getenv("RUSHD_B_API_TOKEN")
    if not token:
        print("ERROR: RUSHD_B_API_TOKEN not set in environment")
        sys.exit(1)
    
    url = os.getenv("RUSHD_B_URL")
    db = RushDB(token, url=url) if url else RushDB(token)
    print(f"\nConnected to RushDB")
    
    # Clear existing data
    clear_existing_data(db)
    
    # ── Step 1: Compute embeddings ──────────────────────────────────────────
    print("\n[1/5] Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  Model: {MODEL_NAME} (384 dimensions)")
    
    print(f"\n[2/5] Computing embeddings for {len(QUERIES)} queries...")
    query_texts = [q for q, r in QUERIES]
    embeddings = compute_embeddings(query_texts, model)
    print(f"  Generated {len(embeddings)} embeddings")
    
    # ── Step 2: Find semantically similar pairs ─────────────────────────────
    print("\n[3/5] Finding semantically similar query pairs...")
    similar_pairs = find_similar_pairs(embeddings, threshold=0.75)
    print(f"  Found {len(similar_pairs)} pairs with similarity >= 0.75")
    
    # ── Step 3: Create data source nodes ───────────────────────────────────
    print("\n[4/5] Creating data source nodes...")
    data_source_records = []
    for ds in DATA_SOURCES:
        record = db.records.create(
            label="DATA_SOURCE",
            data={
                "name": ds["name"],
                "entity_type": ds["entity_type"],
                "last_updated": datetime.now().isoformat(),
            }
        )
        data_source_records.append(record)
        print(f"  Created DATA_SOURCE: {ds['name']}")
    
    # ── Step 4: Create cache entries with embeddings ────────────────────────
    print("\n[5/5] Creating cache entries with embeddings...")
    
    # First, ensure vector index exists
    print("  Ensuring vector index exists...")
    try:
        index = db.ai.indexes.create({
            "label": INDEX_LABEL,
            "propertyName": INDEX_PROPERTY,
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine",
        })
        print(f"  Created vector index: {index.data.get('__id', 'unknown')}")
    except Exception as e:
        # Index might already exist
        print(f"  Vector index already exists (or error: {e})")
    
    # Create cache entry records
    cache_records = []
    for i, (query, response) in enumerate(QUERIES):
        record = db.records.create(
            label=INDEX_LABEL,
            data=generate_cache_entry_record(query, response),
            vectors=[{"propertyName": INDEX_PROPERTY, "vector": embeddings[i]}],
        )
        cache_records.append(record)
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(QUERIES)} cache entries...")
    
    print(f"  Created {len(cache_records)} cache entries total")
    
    # ── Step 5: Create sessions and link cache entries ───────────────────────
    print("\n[6/6] Creating sessions and relationships...")
    
    sessions = generate_sessions(num_sessions=8)
    session_records = []
    
    for session in sessions:
        sess_record = db.records.create(
            label="SESSION",
            data={
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "created_at": session["created_at"],
                "is_active": session["is_active"],
            }
        )
        session_records.append(sess_record)
    
    print(f"  Created {len(session_records)} sessions")
    
    # Link cache entries to sessions (random assignment, some entries shared)
    print("  Creating FROM_SESSION relationships...")
    for i, cache_record in enumerate(cache_records):
        # Assign to a random session
        target_session = random.choice(session_records)
        db.records.attach(
            source=cache_record,
            target=target_session,
            options={"type": "FROM_SESSION", "direction": "out"},
        )
        
        if (i + 1) % 5 == 0:
            print(f"    Linked {i + 1}/{len(cache_records)} entries to sessions...")
    
    # Create SEMANTICALLY_SIMILAR edges between related cache entries
    print("  Creating SEMANTICALLY_SIMILAR relationships...")
    for i, j, sim in similar_pairs:
        db.records.attach(
            source=cache_records[i],
            target=cache_records[j],
            options={"type": "SEMANTICALLY_SIMILAR", "direction": "undirected"},
        )
    print(f"  Created {len(similar_pairs)} SEMANTICALLY_SIMILAR edges")
    
    # Link some cache entries to data sources (for invalidation demo)
    print("  Creating INVALIDATES relationships...")
    for i, cache_record in enumerate(cache_records[:10]):  # First 10 entries
        # Products-related entries get linked to product_catalog
        if any(kw in QUERIES[i][0].lower() for kw in ["shoe", "headphone", "laptop", "monitor", "phone", "product"]):
            db.records.attach(
                source=data_source_records[0],  # product_catalog
                target=cache_record,
                options={"type": "INVALIDATES", "direction": "out"},
            )
    
    # Save cache record IDs for the main demo
    cache_ids = [r.id for r in cache_records]
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "cache_ids.json", "w") as f:
        json.dump({"cache_ids": cache_ids}, f)
    
    print(f"\n{'=' * 60}")
    print("SEEDING COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Cache entries: {len(cache_records)}")
    print(f"  Sessions: {len(session_records)}")
    print(f"  Similarity edges: {len(similar_pairs)}")
    print(f"  Data sources: {len(data_source_records)}")
    print(f"\nRun 'python main.py' to test the semantic cache!")


if __name__ == "__main__":
    seed()
