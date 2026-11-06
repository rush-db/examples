# Dynamic Reranking Using Graph Relationship Signals

A tutorial demonstrating how to use RushDB's property graph model to store user-content interactions as typed relationships, extract behavioral signals from those edges, and dynamically rerank semantic search results using custom scoring.

## What This Demonstrates

- **Graph-native interaction storage**: Modeling views, saves, and shares as typed edges in RushDB
- **Relationship signal extraction**: Counting edge frequencies, recency weighting, and weight-based scoring
- **Dynamic score fusion**: Combining semantic similarity scores with relationship signals to rerank results
- **Transaction-safe writes**: Using RushDB transactions for atomic relationship creation

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://app.rushdb.com))
- `rushdb>=2.0.0` and `sentence-transformers` installed

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy env file and fill in your API key
cp .env.example .env
```

Open `.env` and set:

```env
RUSHDB_API_KEY=your_api_key_here
```

### Seed the Database

The `seed.py` script generates 20 articles across 5 topics and creates 5 users with diverse interaction histories (views, saves, shares). Run it once — it's idempotent.


```bash
python seed.py
```

Expected output:

```
🌱 Seeding articles...
  ✓ Created ARTICLE records
🌱 Seeding users...
  ✓ Created USER records
🌱 Creating interactions (views, saves, shares)...
  ✓ Linked interactions to articles
✅ Seed complete: 20 articles, 5 users, ~100 interaction edges
```

## How to Run

```bash
python main.py
```

The script runs the full pipeline:

1. **Semantic search** — queries the article body index using `"node.js performance"`
2. **Signal extraction** — counts `VIEWED`, `SAVED`, `SHARED` edges per article for a specific user
3. **Recency weighting** — applies exponential decay to edge timestamps
4. **Score fusion** — blends `(0.7 × semantic) + (0.3 × relationship_signal)` and reorders results
5. **Output** — prints ranked articles with a breakdown of their signal scores

## Expected Output

```
📊 Article Graph Signal Re-Ranking Demo
══════════════════════════════════════════════════════════

🔍 Initial semantic search for "node.js performance" (limit=8):
  1. [0.924] Node.js Performance: A Developer's Guide
  2. [0.901] JavaScript Performance Patterns in Production
  3. [0.891] Understanding the Node.js Event Loop
  4. [0.877] JavaScript Engine Internals: V8 Optimization
  5. [0.863] Choosing Between Node.js and Deno for API Backends
  6. [0.851] TypeScript Deep Dive: Advanced Type Patterns
  7. [0.841] Database Query Optimization Techniques
  8. [0.836] PostgreSQL vs MySQL: A Performance Comparison

🔗 Extracting relationship signals for user alex@example.com:
  article_0 (Node.js Performance: A Developer's Guide)
    VIEWED  2x  last: 2h ago   score: 0.667
    SAVED   1x  last: 3d ago   score: 0.135
    SHARED  0x  last: never     score: 0.000
    → combined signal: 0.802 / 1.000
  article_1 (JavaScript Performance Patterns in Production)
    VIEWED  3x  last: 1h ago   score: 1.000
    SAVED   2x  last: 5h ago   score: 0.500
    SHARED  1x  last: 1w ago   score: 0.083
    → combined signal: 1.583 / 1.000 (capped)
  ... (per article)

🏆 Re-ranked results (semantic × 0.7 + signals × 0.3):
  1. [★ 0.886] JavaScript Performance Patterns in Production
              ↳ semantic=0.901  signal=0.833
  2. [★ 0.875] Node.js Performance: A Developer's Guide
              ↳ semantic=0.924  signal=0.802
  3. [★ 0.817] Understanding the Node.js Event Loop
              ↳ semantic=0.891  signal=0.312
  4. [  0.796] TypeScript Deep Dive: Advanced Type Patterns
              ↳ semantic=0.851  signal=0.000
  5. [  0.780] JavaScript Engine Internals: V8 Optimization
              ↳ semantic=0.877  signal=0.104
  ...

📈 Impact: Article #1 moved up 1 position; Article #2 dropped 1 position
   Signal-aware ranking reflects actual user engagement patterns
```

## Project Structure

```
dynamic-reranking-using-graph-relationship-signals-tutorial/
├── README.md           ← you are here
├── requirements.txt    ← rushdb>=2.0.0, sentence-transformers
├── .env.example        ← RUSHDB_API_KEY template
├── seed.py             ← generates articles, users, and interaction graph
└── main.py             ← full reranking pipeline
```

## Key Concepts

### Graph Signal Model

Each user-content interaction becomes a typed directed edge:

```
(USER {email: "alex@..."}) ──[VIEWED]──> (ARTICLE {id: "..."})
(USER {email: "alex@..."}) ──[SAVED]──> (ARTICLE {id: "..."})
(USER {email: "alex@..."}) ──[SHARED]──> (ARTICLE {id: "..."})
```

Edge properties (`count`, `lastInteractionAt`) serve as behavioral signals.

### Signal Extraction Query

The tutorial uses RushDB's `db.relationships.find()` to fetch edges for a given user, grouped by article — demonstrating that RushDB treats relationships as first-class queryable entities:

```sdk
# Find all VIEWED edges from a specific user
db.relationships.find({
    "where": {
        "type": "VIEWED",
        "sourceLabel": "USER",
        "targetLabel": "ARTICLE",
        "source__id": user.id
    },
    "limit": 100
})
___SPLIT___
// TypeScript equivalent pattern (not called in this tutorial's main.py)
const viewed = await db.relationships.find({
    where: {
        type: 'VIEWED',
    },
    limit: 100,
})
```

### Score Fusion

```
final_score = (semantic_weight × semantic_score) + (signal_weight × relationship_signal_score)
```

Where `relationship_signal_score` is the capped weighted sum of all interaction types.

---

**Published**: [github.com/rush-db/examples](https://github.com/rush-db/examples/tree/main/dynamic-reranking-using-graph-relationship-signals-tutorial)

**Docs**: [docs.rushdb.com](https://docs.rushdb.com)
