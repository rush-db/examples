# RushDB SDK Tutorial: Vector Search + Graph Query Integration

A practical guide to building an AI-powered knowledge base with RushDB, combining semantic vector search and graph traversal for powerful information retrieval.

## What This Tutorial Demonstrates

- **Vector Search**: Embed article content and perform semantic similarity searches
- **Graph Relationships**: Model articles, authors, and categories as a connected knowledge graph
- **Hybrid Queries**: Combine vector similarity with graph traversal (e.g., "find similar articles by the same author")
- **Transactions**: Atomic batch operations for data consistency
- **Full SDK Patterns**: Create, find, attach, search, upsert, and record manipulation

## Architecture

```
┌─────────────┐       WRITTEN_BY       ┌─────────────┐
│   ARTICLE   │────────────────────────│    AUTHOR   │
│  (vectors)  │                        └─────────────┘
└──────┬──────┘                              │
       │                                     │
   BELONGS_TO                                  │
       │                                     │
       ▼                                     ▼
┌─────────────┐                      ┌─────────────┐
│  CATEGORY   │                      │  EXPERTISE  │
└─────────────┘                      └─────────────┘
```

## Prerequisites

- Python 3.9+
- RushDB account (free tier: https://rushdb.com)
- `pip` package manager

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/rush-db/examples.git
cd examples/rushdb-sdk-tutorial
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env and add your RushDB API key
```

### 5. Seed the database (optional)

Run the seed script to populate RushDB with sample data:

```bash
python seed.py
```

This creates:
- 5 authors with expertise areas
- 4 categories (AI, Backend, Frontend, DevOps)
- 30 articles with realistic content and vector embeddings

## Running the Tutorial

```bash
python main.py
```

The script demonstrates:

1. **Setup** - Initialize RushDB client and check connection
2. **Data Model** - Create labels (AUTHOR, CATEGORY, ARTICLE)
3. **Batch Import** - Use transactions to create entities atomically
4. **Vector Embedding** - Generate embeddings for article content
5. **Relationship Building** - Connect articles to authors and categories
6. **Semantic Search** - Find articles by meaning, not keywords
7. **Graph Traversal** - Query across relationship boundaries
8. **Hybrid Queries** - Combine vector + graph filtering
9. **Upsert Patterns** - Update or create records idempotently

## Expected Output

```
=== RushDB SDK Tutorial: Vector Search + Graph Query ===

[1] Connection verified ✓
[2] Authors created: 5 records
[3] Categories created: 4 records
[4] Articles created with vectors: 30 records
[5] Relationships established: 90 edges

=== Semantic Search Demo ===
Query: "machine learning applications"
Top 3 results:
  [0.923] Intro to Machine Learning - AI - Alice Chen
  [0.891] Neural Networks Deep Dive - AI - Bob Smith
  [0.867] ML Model Deployment - Backend - Carol Davis

=== Graph Query Demo ===
Articles by authors specializing in AI:
  - Intro to Machine Learning (Alice Chen)
  - Neural Networks Deep Dive (Bob Smith)
  - Transformer Architecture Explained (Carol Davis)

=== Hybrid Query Demo ===
AI articles by expert authors (score > 0.85):
  - Intro to Machine Learning [relevance: 0.923]
  - Neural Networks Deep Dive [relevance: 0.891]

Tutorial complete!
```

## Project Structure

```
rushdb-sdk-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py           # Sample data generator
└── main.py           # Main tutorial code
```

## Key SDK Patterns Used

```sdk
# Create with inline vectors
article = db.records.create(
    label="ARTICLE",
    data={"title": "...", "content": "..."},
    vectors=[{"propertyName": "content", "vector": embedding}]
)

# Semantic search
results = db.ai.search({
    "propertyName": "content",
    "query": "query text",
    "labels": ["ARTICLE"],
    "limit": 5
})

# Graph traversal via related labels
articles = db.records.find({
    "labels": ["ARTICLE"],
    "where": {
        "AUTHOR": {"$relation": {"type": "WRITTEN_BY", "direction": "out"}},
        "CATEGORY": {"name": "AI"}
    }
})

# Transaction with context manager
with db.transactions.begin() as tx:
    db.records.create(label="X", data={...}, transaction=tx)
    # auto-commits on success, auto-rollbacks on exception
```

## Documentation

- SDK Reference: https://docs.rushdb.com
- Python SDK: https://pypi.org/project/rushdb/
- GitHub: https://github.com/rush-db/examples

## Pricing Note

RushDB charges by Knowledge Units (KU) for **writes only**. Reads and queries are always free.
See: https://rushdb.com/pricing
