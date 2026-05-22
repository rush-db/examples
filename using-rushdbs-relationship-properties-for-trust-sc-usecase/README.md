# Trust-Scored Retrieval with RushDB

**Project**: [using-rushdbs-relationship-properties-for-trust-sc-usecase](https://github.com/rush-db/examples/tree/main/using-rushdbs-relationship-properties-for-trust-sc-usecase)

This project demonstrates how RushDB's combination of graph relationships with embedded properties and vector similarity enables **trust-weighted retrieval** — a pattern that is significantly more complex to implement in a traditional Postgres + separate vector database architecture.

## The Problem

Content moderation, fraud detection, and recommendation systems often need to rank results by both:
1. **Semantic similarity** — how closely content matches the query
2. **Source trust** — how much we trust the publisher/verifier

Neither pure vector databases nor pure graph databases handle this elegantly:
- **Vector DBs** excel at similarity but have no concept of relationship properties
- **Graph DBs** model relationships well but don't support semantic search natively
- **Postgres + Vector DB** requires complex application-layer logic to combine scores from two separate systems

## The RushDB Solution

RushDB stores both the graph structure and vector embeddings in a single Neo4j backend, enabling:
- Relationship edges with **first-class properties** (trust scores on VERIFIED_BY edges)
- Vector indexes on record properties
- **Single-query traversal** that combines similarity search with trust-weighted ranking

## What This Demo Shows

1. **Graph model** — Users verify content with trust scores stored on relationship edges
2. **Vector indexing** — Article bodies indexed for semantic search
3. **Trust-weighted retrieval** — Query that combines content similarity with publisher trust
4. **Comparison** — Why achieving this requires custom weighting logic across two systems in Postgres + vector DB

---

## Prerequisites

- Python 3.9+
- RushDB account ([get one free](https://rushdb.com))
- `rushdb>=2.0.0` Python package

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your RUSHD_API_TOKEN
```

### 3. Seed the database

The seed script creates a realistic content moderation scenario:
- 5 verified users with varying trust scores (0.7–0.99)
- 20 articles across tech/health/politics topics
- Trust relationships (VERIFIED_BY) between users and articles they verified

```bash
python seed.py
```

The script is **idempotent** — safe to run twice. It checks for existing data before creating.

### 4. Run the demo

```bash
python main.py
```

Expected output:
- A query for "machine learning applications" retrieves relevant articles
- Results are ranked by **combined score**: semantic similarity × publisher trust
- High-trust verified content appears higher than similar but unverified content

---

## Architecture Overview

### Data Model

```
USER ──VERIFIED_BY(trust_score: 0.95)──► ARTICLE
     └─VERIFIED_BY(trust_score: 0.72)──► ARTICLE

ARTICLE has vector index on `body` property
```

### Trust Score Logic

When a user verifies an article, the relationship edge carries a `trust_score` property (0.0–1.0):
- **0.95–1.0**: Trusted expert or verified journalist
- **0.80–0.94**: Established contributor
- **0.70–0.79**: New contributor, needs verification
- **<0.70**: Untrusted, flagged for review

### Retrieval Query

1. **Semantic search** — Find articles with similar body content
2. **Graph traversal** — For each article, find verification trust scores
3. **Weighted ranking** — `final_score = semantic_similarity * max(trust_scores)`

---

## Why This Matters

### Postgres + Vector DB (Traditional Approach)

```sql
-- PostgreSQL stores users, articles, verification relationships
SELECT a.*, v.trust_score
FROM articles a
JOIN verifications v ON v.article_id = a.id
JOIN users u ON u.id = v.user_id
WHERE ...;

-- Separate vector DB query
SELECT * FROM articles_vector_index
WHERE embedding MATCHES query_embedding;
```

**Problems:**
- Two separate systems require application-level score merging
- No native way to traverse edges while filtering by vector similarity
- Trust scores live in PostgreSQL, vectors in a separate DB
- Complex pagination and ordering across systems

### RushDB (This Approach)

```sdk
# Single query: vector similarity filtered by trust-weighted verification
results = db.ai.search({
    "propertyName": "body",
    "query": "machine learning",
    "labels": ["ARTICLE"],
    "where": {
        "$relationship": {
            "type": "VERIFIED_BY",
            "direction": "in",
            "targetLabel": "USER"
        }
    }
})
# Results include both similarity score and trust metadata
```

**Benefits:**
- Single backend, single query
- Relationship properties are first-class citizens
- Vector search and graph traversal unified
- Trust-weighted ranking happens at the database level

---

## Files

| File | Description |
|-------|-------------|
| `seed.py` | Generates mock users, articles, and trust relationships |
| `main.py` | Demonstrates trust-weighted semantic retrieval |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Pricing](https://rushdb.com/pricing)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
