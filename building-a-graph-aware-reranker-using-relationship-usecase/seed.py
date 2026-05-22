#!/usr/bin/env python3
"""
Seed script: Creates a mock codebase dependency graph in RushDB.

This simulates a software project with modules that have:
- Natural language descriptions (for vector embedding/semantic search)
- Typed relationships (depends_on, conflicts_with, derives_from, implements)
- Stability status (stable, deprecated, experimental)

The graph encodes domain knowledge that pure semantic search would miss:
- deprecated-legacy conflicts with the current auth-module
- cache-invalidator depends_on cache-system
- email-service derives from logger
- etc.

Run this once to populate the graph, then run main.py to demonstrate
the graph-aware reranker.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

# Deterministic seed for reproducibility
random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# Mock Data: Codebase Module Graph
# ─────────────────────────────────────────────────────────────────────────────

MODULES = [
    {
        "slug": "auth-module",
        "name": "Authentication Module",
        "description": "Handles user login, session management, and JWT token validation for the application",
        "status": "stable",
    },
    {
        "slug": "deprecated-legacy",
        "name": "Legacy Auth Module",
        "description": "Old authentication system using session cookies and basic MD5 password hashing, kept for backwards compatibility",
        "status": "deprecated",
    },
    {
        "slug": "payment-gateway",
        "name": "Payment Gateway",
        "description": "Integrates with Stripe and PayPal APIs for processing online payments and handling refunds",
        "status": "stable",
    },
    {
        "slug": "cache-system",
        "name": "Cache System",
        "description": "Redis-based caching layer for improving API response times and reducing database load",
        "status": "stable",
    },
    {
        "slug": "email-service",
        "name": "Email Service",
        "description": "Sends transactional emails via SMTP and SendGrid integration with templating support",
        "status": "stable",
    },
    {
        "slug": "file-storage",
        "name": "File Storage",
        "description": "Manages file uploads to AWS S3 with presigned URLs and multipart upload support",
        "status": "stable",
    },
    {
        "slug": "logger",
        "name": "Logger",
        "description": "Structured logging library with Elasticsearch integration for search and analysis",
        "status": "stable",
    },
    {
        "slug": "validator",
        "name": "Input Validator",
        "description": "Validates and sanitizes user input to prevent SQL injection and XSS attacks",
        "status": "stable",
    },
    {
        "slug": "cache-invalidator",
        "name": "Cache Invalidator",
        "description": "Handles cache busting when underlying data changes, coordinates cache eviction across nodes",
        "status": "experimental",
    },
    {
        "slug": "stripe-adapter",
        "name": "Stripe Adapter",
        "description": "Stripe payment processing adapter with webhook handling and subscription billing support",
        "status": "stable",
    },
]

# Relationship definitions: (source_slug, target_slug, type, priority?)
RELATIONSHIPS = [
    # Standard dependencies
    ("cache-system", "logger", "depends_on", None),
    ("cache-system", "validator", "depends_on", None),
    ("payment-gateway", "logger", "depends_on", None),
    ("payment-gateway", "validator", "depends_on", None),
    ("payment-gateway", "auth-module", "depends_on", None),
    ("email-service", "logger", "depends_on", None),
    ("email-service", "auth-module", "derives_from", None),
    ("file-storage", "validator", "depends_on", None),
    ("file-storage", "auth-module", "depends_on", None),
    ("stripe-adapter", "payment-gateway", "depends_on", "high"),
    ("cache-invalidator", "cache-system", "depends_on", "high"),
    
    # Conflict: deprecated module vs current
    ("deprecated-legacy", "auth-module", "conflicts_with", None),
    
    # Interface implementation
    ("stripe-adapter", "payment-gateway", "implements", None),
]


def get_embedding(text: str, model) -> list:
    """Generate embedding vector using sentence-transformers."""
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def seed_graph():
    """Create the codebase dependency graph in RushDB."""
    load_dotenv()
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise RuntimeError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env")
    
    db = RushDB(api_key)
    
    # Check if data already exists
    existing = db.records.find({"labels": ["MODULE"], "limit": 1})
    if existing.data:
        print("✓ Graph data already exists (found MODULE records). Skipping seed.")
        print("  Run 'main.py' to see the graph-aware reranker in action.")
        return
    
    print("Seeding codebase dependency graph...")
    
    # Load sentence-transformers model for embeddings
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # ── Create vector index first ────────────────────────────────────────────
    index_response = db.ai.indexes.create({
        "label": "MODULE",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,  # all-MiniLM-L6-v2 produces 384-dim vectors
        "similarityFunction": "cosine",
    })
    index_id = index_response.data["__id"]
    print(f"  Created vector index: {index_id}")
    
    # ── Create MODULE records with embeddings ─────────────────────────────────
    module_records = []
    for i, module in enumerate(MODULES):
        # Create record
        record = db.records.create(
            label="MODULE",
            data={
                "slug": module["slug"],
                "name": module["name"],
                "description": module["description"],
                "status": module["status"],
            },
        )
        
        # Generate and store vector embedding
        vector = get_embedding(module["description"], model)
        db.ai.indexes.upsert_vectors(index_id, {
            "items": [{"recordId": record.id, "vector": vector}]
        })
        
        module_records.append((module["slug"], record))
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(MODULES)} modules...")
    
    # ── Create relationships ───────────────────────────────────────────────────
    slug_to_record = {slug: record for slug, record in module_records}
    
    for source_slug, target_slug, rel_type, priority in RELATIONSHIPS:
        source = slug_to_record.get(source_slug)
        target = slug_to_record.get(target_slug)
        
        if source and target:
            options = {"type": rel_type}
            if priority == "high":
                options["properties"] = {"priority": priority}
            
            db.records.attach(source=source, target=target, options=options)
    
    print(f"  Created {len(RELATIONSHIPS)} relationships")
    
    print("\n✓ Graph seeded successfully!")
    print(f"  - {len(MODULES)} modules with vector embeddings")
    print(f"  - {len(RELATIONSHIPS)} typed relationships")
    print("\nRun 'main.py' to demonstrate the graph-aware reranker.")


if __name__ == "__main__":
    seed_graph()
