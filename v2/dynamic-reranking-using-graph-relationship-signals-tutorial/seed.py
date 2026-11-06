"""
Seed script for the Dynamic Reranking tutorial.

Generates:
  - 20 ARTICLE records (5 topics × 4 articles)
  - 5 USER records
  - ~100 interaction edges: VIEWED, SAVED, SHARED between users and articles

Run once. Safe to re-run — checks for existing data before seeding.
"""

import os
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from faker import Faker
from rushdb import RushDB

load_dotenv()

db = RushDB(os.environ["RUSHDB_API_KEY"])
faker = Faker(seed=42)
random.seed(42)

# ─── Article seed data ─────────────────────────────────────────────────────────

ARTICLES = [
    # JavaScript / Node.js
    {
        "title": "Node.js Performance: A Developer's Guide",
        "topic": "JavaScript",
        "body": (
            "Node.js has become a dominant runtime for building fast, scalable server-side "
            "applications. This guide covers profiling tools, cluster mode, memory management, "
            "and the V8 garbage collector's impact on long-running services."
        ),
    },
    {
        "title": "Understanding the Node.js Event Loop",
        "topic": "JavaScript",
        "body": (
            "The event loop is the heart of Node.js asynchronous execution. "
            "Understanding the phases of the event loop, microtask queues, and when to "
            "prefer synchronous vs asynchronous code can dramatically improve application throughput."
        ),
    },
    {
        "title": "JavaScript Engine Internals: V8 Optimization",
        "topic": "JavaScript",
        "body": (
            "V8 uses hidden classes, inline caching, and deoptimization markers to run "
            "JavaScript at near-native speed. Learn how to write code that the JIT compiler "
            "loves and avoid patterns that trigger expensive bailouts."
        ),
    },
    {
        "title": "JavaScript Performance Patterns in Production",
        "topic": "JavaScript",
        "body": (
            "Real-world performance optimization goes beyond microbenchmarks. "
            "This article walks through lazy loading, code splitting, memoization, "
            "and profiling a live Node.js service with 10k concurrent connections."
        ),
    },
    # Python / ML
    {
        "title": "Building RAG Pipelines with LangChain and FAISS",
        "topic": "Python",
        "body": (
            "Retrieval-Augmented Generation combines the power of language models with "
            "external knowledge retrieval. This tutorial builds a production-grade RAG pipeline "
            "using LangChain, FAISS vector store, and OpenAI embeddings with evaluation metrics."
        ),
    },
    {
        "title": "PyTorch Lightning for Production ML Training",
        "topic": "Python",
        "body": (
            "PyTorch Lightning abstracts away boilerplate training loops while keeping "
            "full visibility into the data, model, and optimizer. We cover multi-GPU "
            "training, gradient checkpointing, early stopping, and experiment tracking with W&B."
        ),
    },
    {
        "title": "Asyncio Deep Dive: Python Concurrency Without the Threads",
        "topic": "Python",
        "body": (
            "Python's asyncio provides a single-threaded cooperative concurrency model "
            "ideal for I/O-bound workloads. We explore the event loop, Task/Future APIs, "
            "semaphores, and common async anti-patterns that lead to deadlocks."
        ),
    },
    {
        "title": "NumPy Internals: How Array Broadcasting Works",
        "topic": "Python",
        "body": (
            "NumPy's broadcasting rules let you write vectorized code without explicit loops. "
            "Understanding memory layout, stride tricks, and ufunc dispatch helps you write "
            "code that is both readable and orders of magnitude faster than pure Python."
        ),
    },
    # Databases
    {
        "title": "PostgreSQL Query Optimization Techniques",
        "topic": "Databases",
        "body": (
            "A slow query can cripple an otherwise well-architected system. This guide "
            "covers EXPLAIN ANALYZE, index selection, partial indexes, materialized views, "
            "connection pooling with PgBouncer, and the new incremental sort in PostgreSQL 16."
        ),
    },
    {
        "title": "PostgreSQL vs MySQL: A Performance Comparison",
        "topic": "Databases",
        "body": (
            "Both PostgreSQL and MySQL are production-grade relational databases, but "
            "they diverge in query planner sophistication, concurrency models, and indexing "
            "strategies. We benchmark identical workloads on both and analyze where each shines."
        ),
    },
    {
        "title": "Database Query Optimization Techniques",
        "topic": "Databases",
        "body": (
            "Generic techniques that apply across SQL databases: query rewriting, "
            "covering indexes, statistics maintenance, connection pooling, and caching "
            "with Redis. Includes before/after EXPLAIN plans for real-world slow queries."
        ),
    },
    {
        "title": "Neo4j Performance Tuning for Graph Queries",
        "topic": "Databases",
        "body": (
            "Graph databases excel at relationship-heavy queries, but poor index design "
            "defeats the purpose. This article covers node labels, relationship types, "
            "cypher query plans, the costs of cross-label scans, and profiling with APOC."
        ),
    },
    # React / Frontend
    {
        "title": "React Server Components: A Complete Guide",
        "topic": "Frontend",
        "body": (
            "React Server Components blur the boundary between server and client by "
            "executing components on the server and streaming HTML. We cover the mental "
            "model, data fetching patterns, caching strategies, and how RSC differs from SSR."
        ),
    },
    {
        "title": "TypeScript Advanced Types: Conditional, Mapped, and Template Literal",
        "topic": "Frontend",
        "body": (
            "TypeScript's advanced type system enables type-level programming that was "
            "previously only possible in languages with dependent types. This guide covers "
            "conditional types, infer keyword, mapped types, and template literal types."
        ),
    },
    {
        "title": "Next.js App Router: Migration and New Patterns",
        "topic": "Frontend",
        "body": (
            "The Next.js App Router introduces file-system routing, layouts, and server "
            "components. This article covers the migration path from Pages Router, "
            "metadata API, Server Actions, and how to incrementally adopt the new model."
        ),
    },
    {
        "title": "TypeScript Deep Dive: Advanced Type Patterns",
        "topic": "Frontend",
        "body": (
            "Going beyond basic interface definitions: recursive types, variadic tuple "
            "types, branded types for type-safe IDs, and the builder pattern implemented "
            "entirely through TypeScript's type system with zero runtime overhead."
        ),
    },
    # Backend / Architecture
    {
        "title": "Designing REST APIs That Scale to Millions of Users",
        "topic": "Backend",
        "body": (
            "A practical guide to API design at scale: versioning strategies, rate "
            "limiting, idempotency keys, cursor-based pagination, and error response "
            "conventions. We examine real-world APIs from Stripe and Twilio for reference."
        ),
    },
    {
        "title": "Choosing Between Node.js and Deno for API Backends",
        "topic": "Backend",
        "body": (
            "Both Node.js and Deno are JavaScript runtimes built for server-side use, "
            "but they differ in security model, module resolution, and TypeScript support. "
            "We benchmark HTTP throughput, cold start times, and developer experience."
        ),
    },
    {
        "title": "Microservices vs Monolith: A Pragmatic Guide",
        "topic": "Backend",
        "body": (
            "The microservices vs monolith debate has produced more heat than light. "
            "This article presents a decision framework based on team size, deployment "
            "frequency, data consistency requirements, and operational maturity."
        ),
    },
    {
        "title": "Event-Driven Architecture with Kafka and Node.js",
        "topic": "Backend",
        "body": (
            "Kafka enables durable, high-throughput event streaming for loosely coupled "
            "microservices. We cover producers, consumer groups, exactly-once semantics, "
            "schema registry with Avro, and integration patterns with Node.js services."
        ),
    },
]

# ─── Interaction weight configuration ────────────────────────────────────────
# Higher weight = more signal value per interaction edge
INTERACTION_WEIGHTS = {
    "VIEWED": 1.0,
    "SAVED":  3.0,
    "SHARED": 5.0,
}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def time_ago(hours: int) -> str:
    """Return an ISO timestamp for N hours ago."""
    return (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"


def is_seeded() -> bool:
    """Return True if data already exists in the workspace."""
    result = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    return result.total > 0


# ─── Main seed logic ───────────────────────────────────────────────────────────



def seed():
    if is_seeded():
        print("⚠️  Data already exists — skipping seed. Run main.py directly.")
        return

    print("\n🌱 Seeding articles...")
    articles = []
    for i, article_data in enumerate(ARTICLES):
        article = db.records.create(
            label="ARTICLE",
            data={
                "title":     article_data["title"],
                "topic":     article_data["topic"],
                "body":      article_data["body"],
                "slug":      f"article-{i}-{article_data['topic'].lower().replace(' ', '-')}",
            },
        )
        articles.append(article)
        if (i + 1) % 5 == 0:
            print(f"  ✓ {i + 1}/{len(ARTICLES)} articles created")

    print("  ✓ Created ARTICLE records")

    # ── Create vector index and embed article bodies ──────────────────────────
    print("\n📊 Creating vector index for ARTICLE.body...")
    from sentence_transformers import SentenceTransformer

    index = db.ai.indexes.create({
        "label":           "ARTICLE",
        "propertyName":    "body",
        "sourceType":      "external",
        "dimensions":      384,
        "similarityFunction": "cosine",
    })
    index_id = index.data["__id"]
    print(f"  ✓ Index created: {index_id}")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    vectors = []
    for article in articles:
        vec = model.encode(article["body"], normalize_embeddings=True)
        vectors.append({
            "recordId": article.id,
            "vector":   vec.tolist(),
        })

    db.ai.indexes.upsert_vectors(index_id, {"items": vectors})
    print(f"  ✓ {len(vectors)} vectors indexed")

    # ── Create users ──────────────────────────────────────────────────────────
    print("\n🌱 Seeding users...")
    USER_DATA = [
        {"name": "Alex Chen",        "email": "alex@example.com"},
        {"name": "Maria Santos",     "email": "maria@example.com"},
        {"name": "James Okonkwo",    "email": "james@example.com"},
        {"name": "Priya Kapoor",     "email": "priya@example.com"},
        {"name": "Sarah Thompson",    "email": "sarah@example.com"},
    ]
    users = []
    for u in USER_DATA:
        users.append(db.records.create(label="USER", data=u))
    print(f"  ✓ Created {len(users)} USER records")

    # ── Create interaction edges ──────────────────────────────────────────────
    print("\n🌱 Creating interactions (views, saves, shares)...")

    # Each user gets a unique random interaction profile
    # Some articles are hot (many interactions), some are cold
    interaction_configs = [
        # (user_index, article_indices, interaction_type, count, hours_ago_base)
        # User 0 — Alex: heavy JavaScript / Node.js interest
        (0, list(range(4)),           "VIEWED", 2, 24),
        (0, [0, 1],                  "SAVED",  1, 72),
        (0, [0, 3],                  "SHARED", 1, 168),
        # User 1 — Maria: Python + Databases
        (1, list(range(4, 8)),       "VIEWED", 3, 12),
        (1, [4, 5],                  "SAVED",  2, 48),
        (1, [4],                     "SHARED", 1, 120),
        (1, [8, 9, 10],              "VIEWED", 1, 36),
        (1, [8],                     "SAVED",  1, 96),
        # User 2 — James: Backend heavy
        (2, list(range(16, 20)),    "VIEWED", 4, 6),
        (2, [16, 18],                "SAVED",  2, 60),
        (2, [16],                    "SHARED", 1, 72),
        (2, list(range(4)),           "VIEWED", 2, 48),
        # User 3 — Priya: Frontend + Python
        (3, list(range(12, 16)),     "VIEWED", 3, 18),
        (3, [12, 14],                "SAVED",  2, 36),
        (3, [12],                    "SHARED", 1, 96),
        (3, list(range(4, 8)),       "VIEWED", 2, 72),
        # User 4 — Sarah: broad interests, light interactions
        (4, list(range(0, 20, 3)),   "VIEWED", 1, 96),
        (4, [0, 4, 8, 12, 16],       "SAVED",  1, 120),
    ]

    edge_count = 0
    with db.transactions.begin() as tx:
        for user_idx, article_indices, rel_type, count, base_hours in interaction_configs:
            user = users[user_idx]
            for art_idx in article_indices:
                article = articles[art_idx]
                for i in range(count):
                    hours_offset = base_hours + random.randint(0, 48)
                    db.records.attach(
                        source=user,
                        target=article,
                        options={
                            "type":      rel_type,
                            "direction": "out",
                            "properties": {
                                "count":               count,
                                "lastInteractionAt":  time_ago(hours_offset + i * random.randint(1, 12)),
                            },
                        },
                        transaction=tx,
                    )
                    edge_count += 1
                    if edge_count % 20 == 0:
                        print(f"  ✓ {edge_count} interaction edges created")
        # tx auto-commits on clean exit

    print(f"  ✓ Created {edge_count} interaction edges")
    print("\n✅ Seed complete! Run main.py to see reranking in action.")


if __name__ == "__main__":
    seed()
