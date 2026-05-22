# Semantic Clustering: Grouping Related Memories with Vector Proximity

A practical tutorial demonstrating how to build a semantic memory clustering pipeline using RushDB's vector search capabilities combined with graph traversal.

## What This Demonstrates

This project walks through building a semantic clustering system that:

1. **Generates embeddings** for memory content using `sentence-transformers` (all-MiniLM-L6-v2)
2. **Stores vectors** alongside graph properties in RushDB
3. **Queries for semantically similar memories** using vector proximity
4. **Performs cluster analysis**: finds memory neighborhoods, identifies related groups, detects outliers
5. **Combines graph traversal + vector search** for richer clustering than either alone

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works great)
- `sentence-transformers` for embedding generation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `RUSHDB_API_KEY` — Your RushDB API key from the dashboard
- `RUSHDB_URL` — API URL (defaults to cloud: `https://api.rushdb.com/api/v1`)

### 3. Seed Mock Memory Data

The seed script generates 100+ realistic memory records with varied themes:

```bash
python seed.py
```

This creates:
- 100+ `MEMORY` records with titles, content, dates, and tags
- Pre-computed 384-dimensional embeddings for semantic search
- Relationships between related memories

## Running the Tutorial

```bash
python main.py
```

The main script demonstrates:

### 1. Vector Index Setup
Creates a vector index for semantic search on memory content.

### 2. Semantic Similarity Search
Find memories related to a query using cosine similarity:

```python
similar = db.ai.search({
    "propertyName": "content",
    "query": "childhood summer vacations",
    "labels": ["MEMORY"],
    "limit": 5
})
```

### 3. Memory Neighborhoods
Find the k-nearest neighbors of a specific memory to discover local clusters.

### 4. Cluster Analysis
- Group memories by semantic similarity
- Identify outlier memories (dissimilar from all clusters)
- Find memory themes/topics automatically

### 5. Graph + Vector Composition
Combine relationship queries with vector search:
- Find memories related to a specific memory that also share a tag
- Discover chains of semantically connected memories

## Expected Output

```
=== Semantic Memory Clustering Demo ===

1. Index Stats: 127 / 127 records indexed (100% coverage)

2. Semantic Search: "planning a trip to Japan"
   [0.892] Tokyo trip planning notes
   [0.847] Kyoto temples visit
   [0.812] Language learning journey
   [0.756] Japanese cuisine exploration
   [0.734] Cherry blossom season

3. Memory Neighborhood: Top 5 neighbors of memory #42
   [0.923] Related: Family reunion 2023
   [0.891] Related: Holiday traditions
   [0.867] Related: Childhood home memories
   [0.845] Related: Summer camp stories
   [0.812] Related: Birthday celebrations

4. Cluster Groups (3 clusters identified):
   Cluster A (family/home): 12 memories
   Cluster B (travel/adventure): 18 memories
   Cluster C (learning/growth): 15 memories

5. Outlier Memories (semantic outliers):
   - "Rare collector's item discovery" (avg similarity: 0.12)
   - "Unexpected career change" (avg similarity: 0.18)

6. Graph + Vector Composition:
   Memories connected to "Tokyo trip" that share a tag:
   - "Kyoto temples visit" (REL: CONNECTED_TO, tag: travel)
   - "Japanese cuisine exploration" (REL: CONNECTED_TO, tag: culture)
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ sentence-       │     │                  │     │                 │
│ transformers    │────▶│    RushDB        │◀────│  Cluster        │
│ (all-MiniLM)    │     │  ┌────────────┐  │     │  Analysis       │
│                 │     │  │ Neo4j      │  │     │                 │
│ 384-dim vectors │     │  │ + Vector   │  │     │  - Neighborhoods│
└─────────────────┘     │  │   Index    │  │     │  - Groups       │
                      │  └────────────┘  │     │  - Outliers     │
                      │                  │     │                 │
                      └──────────────────┘     └─────────────────┘
                              ▲
                              │
                      ┌───────┴───────┐
                      │ Graph Layer   │
                      │ (relationships│
                      │  + properties)│
                      └───────────────┘
```

## Embedding Model Choice

We use **all-MiniLM-L6-v2** from `sentence-transformers` because:
- Fast inference (suitable for real-time applications)
- 384 dimensions (compact, efficient storage)
- Strong performance on semantic similarity benchmarks
- No API costs (runs locally)

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Vector Search Guide](https://docs.rushdb.com/guides/vector-search)
- [GitHub Examples](https://github.com/rush-db/examples)
