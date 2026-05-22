# Building a Semantic Cache Layer Using RushDB's Graph Storage

## What This Project Demonstrates

This project shows how to build a **semantic cache layer** that combines graph traversal with vector similarity search — a pattern where RushDB's dual-layer architecture genuinely shines.

When you're running LLM-powered applications, naive vector caches hit a wall: they're great at finding "similar" queries, but they can't tell you whether those queries are still valid, whether they belong to the same user session, or whether a downstream data source change has invalidated them.

RushDB solves this by letting you model cache entries as **full graph nodes** with:
- Embedded vectors for semantic similarity search
- Typed relationships to model session affinity, topic clusters, and invalidation chains
- Property filtering for exact-match staleness checks

## Key Concepts Demonstrated

1. **Cache entry modeling** — Query/response pairs stored as typed records with inline vectors
2. **Semantic clustering** — Related queries linked via graph edges (`SEMANTICALLY_SIMILAR`)
3. **Session-aware caching** — User/session relationships for affinity-based retrieval
4. **Invalidation via graph topology** — Using edge traversal to determine staleness boundaries
5. **Pure vector vs. graph-backed comparison** — Side-by-side benchmark showing hit rate and false-positive differences

## Prerequisites

- Python 3.9+
- A RushDB account ([get one free](https://rushdb.com))
- `sentence-transformers` for embedding generation (CPU-friendly, no API key needed)

## Setup

```bash
# Clone the examples repo
git clone https://github.com/rush-db/examples
cd building-a-semantic-cache-layer-using-rushdbs-grap-usecase

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHD_B_API_TOKEN
```

## Quick Start

```bash
# 1. Seed mock cache data (queries, responses, embeddings, relationships)
python seed.py

# 2. Run the full demo (cache lookup, comparison, invalidation demo)
python main.py
```

## Project Structure

```
building-a-semantic-cache-layer-using-rushdbs-grap-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .env                # Your API token (gitignored)
├── seed.py             # Generate mock cache data
├── main.py             # Core semantic cache implementation
└── data/
    └── queries.json    # Seeded query/response pairs
```

## Expected Output

Running `python main.py` will show:

```
=== Semantic Cache Demo ===

1. CACHE LOOKUP: "what is machine learning"
   Found: what is ml (score: 0.847)
   → Cache HIT (semantic match, same session)

2. CACHE LOOKUP: "tell me about python basics"
   No close match found
   → Cache MISS → would recompute

3. TOPOLOGY-BASED INVALIDATION
   Data source 'product_catalog' updated
   → Following SUPERSET_OF edges...
   → Invalidated 3 cache entries

4. COMPARISON: Pure Vector vs Graph-Backed Cache
   +----------------------+-------------+-------------+
   | Metric               | Pure Vector | Graph-Backed|
   +----------------------+-------------+-------------+
   | Total lookups        | 50          | 50          |
   | Hits                 | 18          | 18          |
   | False positives      | 7           | 1           |
   | Invalidated hits     | 3           | 0           |
   | Effective hits       | 15          | 17          |
   +----------------------+-------------+-------------+
```

## Why This Architecture Works

### The Problem with Pure Vector Caches

A pure vector cache stores (query_embedding, response) pairs. To retrieve:
1. Embed the incoming query
2. Find the nearest embedding by cosine similarity
3. Return the associated response

This works — until you encounter:

- **False positives**: "How do I reset my password?" and "How do I create a new password?" score high but have different answers
- **Staleness**: The cache can't know if the underlying data changed
- **No session affinity**: A query from session A shouldn't share hits with session B

### The Graph-Backed Solution

By modeling cache entries as nodes with typed edges, you gain:

| Problem | Graph Solution |
|---------|----------------|
| False positives | Require `SEMANTICALLY_SIMILAR` edge AND same session edge |
| Staleness | `INVALIDATED_BY` edges from data source nodes |
| No affinity | `FROM_SESSION` edges filter by active session |
| No grouping | `PART_OF_TOPIC` edges cluster related queries |

## Data Model

```
┌─────────────────┐          ┌─────────────────────┐
│  CACHE_ENTRY    │          │  DATA_SOURCE        │
│  query: str     │          │  name: str          │
│  response: str  │          │  last_updated: date │
│  embedding: vec │          └──────────┬──────────┘
└────────┬────────┘                     │
         │ SUPERSET_OF                  │ INVALIDATES
         │                              │
    ┌────┴────┐                         │
    │CACHE_EN │◄────────────────────────┘
    │TRY      │
    └────┬────┘
         │ FROM_SESSION
         │
    ┌────┴────┐
    │ SESSION │
    │ user_id │
    └─────────┘
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Vector Search in RushDB](https://docs.rushdb.com/ai-search)
- [Graph Relationships in RushDB](https://docs.rushdb.com/relationships)

## License

MIT — see the [rush-db/examples](https://github.com/rush-db/examples) repository.
