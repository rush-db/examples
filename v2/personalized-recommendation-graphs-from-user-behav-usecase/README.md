# Personalized Recommendation Graphs from User Behavior Vector Streams

A session-based recommendation engine demonstrating graph+vector unification in RushDB.

## What This Project Demonstrates

- **Graph-first behavior modeling**: User sessions as nodes, clickstream events as edges
- **Vector similarity for collaborative filtering**: Finding users with similar click patterns
- **Hybrid recommendation pipeline**: Graph traversal → vector reranking → cold-start fallback
- **Architecture comparison**: Single RushDB query vs. stitched-together vector search + graph DB pipeline

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RushDB                                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────────┐                  │
│  │  USER   │───▶│ SESSION │───▶│ CLICK_EVENT │───▶│  ITEM   │  │
│  │(vector) │    │         │    │             │    │(vector) │  │
│  └─────────┘    └─────────┘    └─────────────┘    └─────────┘  │
│      │                                       │                  │
│      └──────────── graph traversal ──────────┘                  │
│                        + vector similarity                       │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (https://docs.rushdb.com)
- `pip` for dependencies

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### 3. Seed Mock Data

```bash
python seed.py
```

This generates:
- 50 users with embedding vectors (random 128-dim)
- 200 items across 5 categories with embedding vectors
- 300+ clickstream sessions with 3-10 events each

The seed script is **idempotent** — run it multiple times safely.

## Running the Demo

```bash
python main.py
```

### What Happens

1. **Warm user recommendation**: Find similar users via graph traversal → vector reranking → exclude already-viewed items
2. **Cold-start fallback**: For users with no history, traverse item-category graph
3. **Latency comparison**: Measures single RushDB query vs. separate vector+graph pipeline

## Expected Output

```
============================================================
Session-Based Recommendation Engine Demo
============================================================

[1/3] Loading users and items...
Found 50 users and 200 items

[2/3] Testing warm-start recommendation for user_0...
  - Found 12 similar users via click pattern traversal
  - Vector reranking returned 5 candidates
  - Recommendations: item_47, item_182, item_23, item_156, item_89

[3/3] Testing cold-start fallback for new_user_99...
  - No click history found (cold start)
  - Falling back to category traversal: Electronics > 5 items
  - Fallback recommendations: item_12, item_45, item_67, item_89, item_101

============================================================
Latency Comparison (100 iterations each)
============================================================
RushDB unified query:     12.4ms avg (σ=2.1ms)
Separated pipeline query:  34.7ms avg (σ=5.3ms)
Speedup: 2.8x

============================================================
End-to-End Recommendation Pipeline
============================================================

User: user_0
  Click history: 7 items (3 categories)
  Similar users found: 12
  Candidates from collaborative filtering: 5
  Final recommendations (vector-reranked):
    → item_47 (score: 0.92) - "Wireless Headphones"
    → item_182 (score: 0.89) - "Smart Watch Pro"
    → item_23 (score: 0.87) - "Bluetooth Speaker"
    → item_156 (score: 0.85) - "USB-C Hub"
    → item_89 (score: 0.82) - "Mechanical Keyboard"

Done.
```

## Project Structure

```
personalized-recommendation-graphs-from-user-behav-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── seed.py             # Generate mock clickstream data
└── main.py             # Recommendation engine implementation
```

## Key Code Patterns

### Vector-annotated Record Creation

```sdk
# Create item with embedding vector
item = db.records.create(
    label="ITEM",
    data={"itemId": "item_1", "name": "Wireless Headphones", "category": "Electronics"},
    vectors=[{"propertyName": "embedding", "vector": [0.123, ...]}]
)

# Attach user to session
db.records.attach(source=user, target=session, options={"type": "HAS_SESSION"})

# Click event links user → item
db.records.attach(source=click_event, target=item, options={"type": "REFERENCES"})
```

### Multi-hop Graph Traversal

```sdk
# Find users with similar click patterns via graph traversal
similar_users = db.records.find({
    "labels": ["USER"],
    "where": {
        "SESSION": {
            "$relation": {"type": "HAS_SESSION", "direction": "out"},
            "CLICK_EVENT": {
                "$relation": {"type": "BY_USER", "direction": "in"}
            }
        }
    }
})
```

### Vector Similarity Search (Reranking)

```sdk
# Rerank candidates by vector similarity to user's preference profile
recommendations = db.ai.search({
    "propertyName": "embedding",
    "queryVector": user_preference_vector,
    "labels": ["ITEM"],
    "where": {
        "itemId": {"$nin": already_viewed_ids}
    },
    "limit": 10
})
```

## Cold-Start Strategy

When a user has no click history:
1. Detect zero sessions via graph traversal
2. Fall back to category-based graph traversal
3. Return popular items from categories the user has shown interest in

## Benchmarking

The `benchmark()` function in `main.py` compares:
- **RushDB unified**: Single query traversing graph + filtering via vector similarity
- **Separated pipeline**: Vector search → external graph lookup → join (simulates separate systems)

This demonstrates the architectural advantage of unified graph+vector in one system.

---

Generated for [RushDB Examples](https://github.com/rush-db/examples/tree/main/personalized-recommendation-graphs-from-user-behav-usecase)
