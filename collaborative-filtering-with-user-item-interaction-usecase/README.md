# Collaborative Filtering with User-Item Interaction Graphs

A production-ready demonstration of real-time collaborative filtering using RushDB's native property graph and vector search capabilities.

## What This Demonstrates

This example shows how RushDB eliminates the infrastructure complexity of building recommendation systems by combining:

1. **Graph traversal** — Model users and items as nodes with typed interaction edges (RATED, PURCHASED, VIEWED)
2. **Vector similarity** — Layer semantic embeddings on items for content-based filtering
3. **Hybrid scoring** — Combine behavioral similarity (collaborative) with content similarity (semantic) in a single query

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     RushDB Instance                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐     RATED      ┌─────────┐                       │
│   │  USER   │◄──────────────►│  ITEM   │  (with vector embed)   │
│   │  Alice  │                │ Widget  │                        │
│   └────┬────┘                └─────────┘                        │
│        │                                                        │
│        │ PURCHASED                                              │
│        └──────────────►┌─────────┐                              │
│   ┌─────────┐           │  ITEM   │                              │
│   │  USER   │──────────►│ Gadget  │                              │
│   │   Bob   │  RATED    └─────────┘                              │
│   └─────────┘                                                     │
│                                                                  │
│   Vector Index on: ITEM.description ──► Semantic Search          │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- `sentence-transformers` for embeddings

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Get your API key:**
   - Sign up at [rushdb.com](https://rushdb.com)
   - Create a project
   - Copy the API key to `.env`

## How to Run

### Step 1: Seed the database

```bash
python seed.py
```

This generates:
- 30 users with random profiles
- 50 items (products) with descriptions
- ~500 interaction records (ratings, purchases, views)
- Vector embeddings for all item descriptions

The seed script is **idempotent** — run it multiple times safely. It checks for existing data before creating new records.

### Step 2: Run the collaborative filtering demo

```bash
python main.py
```

Output shows:
1. Target user profile and their interactions
2. Similar users found via graph traversal
3. Candidate items scored by interaction weight + vector proximity
4. Top 10 recommendations with explanations

## Key Code Patterns

### Creating Interaction Graphs

```sdk
# Create users and items
user = db.records.create(label="USER", data={"userId": "alice123", "name": "Alice"})
item = db.records.create(label="ITEM", data={"itemId": "prod456", "name": "Wireless Headphones"})

# Create typed interaction edges with weights
db.records.attach(
    source=user,
    target=item,
    options={"type": "RATED", "direction": "out"}
)
# Attach rating as a property on the relationship
db.records.attach(source=user, target=item, options={"type": "RATED", "data": {"score": 4.5, "weight": 1.0}})
```

### Graph-Based Similar User Finding

```sdk
# Find users who interacted with the same items as target user
similar_users = db.records.find({
    "labels": ["USER"],
    "where": {
        "ITEM": {  # Users who have items in common
            "RATED": {  # Through the RATED relationship
                "direction": "in"
            }
        }
    }
})
```

### Hybrid Scoring (Behavioral + Content)

```sdk
# 1. Get target user's interaction neighborhood
target_user = db.records.find_one({"labels": ["USER"], "where": {"userId": target_user_id}})

# 2. Find similar users via graph traversal
# 3. Aggregate their item preferences with weights
# 4. Combine with semantic similarity from vector search

semantic_matches = db.ai.search({
    "propertyName": "description",
    "query": target_user_preferences_summary,
    "labels": ["ITEM"],
    "limit": 20
})
```

## Production Considerations

### Real-Time vs. Batch Scoring

| Approach | Latency | Freshness | Use Case |
|----------|---------|-----------|----------|
| **Real-time** | <100ms | Always current | Homepage, checkout |
| **Pre-computed** | <5ms | Stale by hours | Email, notifications |

RushDB's graph traversal is fast enough for real-time recommendations with depth-2 traversals. For depth-3+, consider pre-computing user similarity matrices.

### Graph Depth vs. Latency Budget

```
Depth 1: User → Their Items                    (~5-15ms)
Depth 2: User → Items → Other Users            (~20-50ms)  ← Recommended max
Depth 3: User → Items → Users → Their Items    (~100-200ms)
```

### Cold Start Handling

1. **New Users**: Fall back to content-based filtering using demographics
2. **New Items**: Use vector similarity on item description (no interactions needed)
3. **Hybrid Approach**: Weight content-based higher for sparse interaction data

```sdk
# Cold start: find items similar to items the user HAS interacted with
similar_items = db.ai.search({
    "propertyName": "description",
    "query": "electronics gadget",
    "labels": ["ITEM"],
    "where": {
        "$not": {
            "__id": {"$in": user_interacted_item_ids}
        }
    },
    "limit": 10
})
```

## Project Structure

```
collaborative-filtering-with-user-item-interaction-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Data generation and import
└── main.py             # Collaborative filtering demo
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph-Based Recommendations](https://docs.rushdb.com/guides/recommendations)
- [Vector Search in RushDB](https://docs.rushdb.com/guides/vector-search)
