# Time-Weighted Graph Traversals for Recency-Aware Recommendations

## What This Example Demonstrates

A **news recommendation feed** that balances:

1. **Relevance** — vector similarity to user's reading history
2. **Recency** — time-decay scoring (newer articles rank higher)
3. **Social proximity** — articles from followed users

This example shows how RushDB's combined property graph + vector search model handles all three in a single logical traversal, where separate systems would require a multi-stage pipeline.

---

## The Data Model

```
┌─────────┐     FOLLOWS      ┌─────────┐
│  USER   │ ←─────────────── │  USER   │
│ (alice) │                  │  (bob)  │
└────┬────┘                  └────┬────┘
     │                           │
     │ PUBLISHED                 │ PUBLISHED
     ▼                           ▼
┌─────────┐     READ            ┌─────────┐
│ ARTICLE │ ←───────────────── │ ARTICLE │
│         │  (with timestamp)   │         │
└─────────┘                     └─────────┘
```

**Records**:
- `USER` — `{id, name, email}`
- `ARTICLE` — `{id, title, body, published_at}` with embedded vector on `body`
- Relationships carry timestamps: `FOLLOWS`, `PUBLISHED`, `READ`

---

## Why This Approach Outperforms a Pipeline

### The Naive Approach (3 Separate Systems)

```
[Graph DB]          [Vector DB]           [Ranker]
    │                    │                    │
    ├─ Traverse follows ─┼─ Semantic filter ──┼─ Combine scores
    │                    │                    │
    └────────────────────┴────────────────────┘
              Three hops, three round-trips
```

**Problems**:
1. Graph DB returns 1000 articles → Vector DB filters to 50 → Ranker combines (data volume mismatch)
2. No shared context between hops — recency and similarity computed independently
3. Two separate index lookups, two query languages, two failure modes
4. Social graph context lost in pure vector search

### RushDB's Single-Pass Approach

```
[RushDB — Single Graph + Vector Layer]
    │
    ├─ Traverse: User → FOLLOWS → Users → PUBLISHED → Articles
    │
    ├─ Vector search within the traversal context (same query, same session)
    │
    └─ Combine in one pass (Python-side scoring with full context)
```

**Advantages**:
1. One API call pattern, one authentication, one error handling path
2. Relationship traversal already filters to the social graph boundary
3. Vector search operates on the pre-filtered, contextually relevant set
4. Time-decay weighting combines naturally with similarity scores in Python

---

## Prerequisites

- Python 3.10+
- RushDB account (free tier at https://rushdb.com)
- `sentence-transformers` for local embeddings (no API key needed)

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set RUSHDB_API_TOKEN
```

### 3. Generate Mock Data

```bash
python seed.py
```

This will create:
- 20 users with follow relationships
- 50 articles with timestamps
- Reading history for each user (to compute interest vectors)

The seed script is **idempotent** — run it multiple times safely. It checks for existing data and skips if the workspace is already seeded.

### 4. Run the Recommendation Demo

```bash
python main.py
```

---

## Expected Output

```
╔══════════════════════════════════════════════════════════════════╗
║  RECENCY-AWARE NEWS RECOMMENDATION FEED                          ║
║  User: alice@example.com                                          ║
╠══════════════════════════════════════════════════════════════════╣
║  COMBINED FEED (recency × relevance)                             ║
╠══════════════════════════════════════════════════════════════════╣
║  #1 │ "OpenAI Releases GPT-5 with..."                            ║
║      │ by: bob_jenkins | 2h ago | score: 0.847                    ║
║                                                                  ║
║  #2 │ "Understanding Transformer..."                              ║
║      │ by: diana_ross | 5h ago | score: 0.823                    ║
║                                                                  ║
║  #3 │ "Rust 2.0 Announced with..."                                ║
║      │ by: carol_west | 1d ago | score: 0.791                    ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## How the Scoring Works

### Time-Decay Formula

```python
def time_decay(published_at: datetime, half_life_hours: int = 24) -> float:
    """Exponential decay: score halves every `half_life_hours`."""
    age_hours = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
    return math.exp(-0.693 * age_hours / half_life_hours)  # 0.693 = ln(2)
```

### Combined Score

```python
combined_score = time_decay_score * vector_similarity_score
```

This creates a **Pareto-optimal ranking**:
- Very recent + low similarity → still beats old + high similarity
- Very high similarity + old → may beat recent + low similarity
- Tunable via `half_life_hours` parameter

---

## Where It Breaks Down with Separate Systems

| Scenario | RushDB | Separate Pipeline |
|----------|--------|-------------------|
| User follows 1000 people | One traversal | Graph DB returns 10K articles → filtered down |
| Real-time ranking update | In-memory scoring | Needs re-query of both systems |
| Explainability | Full graph context | "Vector distance" — why? |
| Debugging | One query log | Correlate three systems |
| Schema changes | Property on relationship | Schema migration in two DBs |

---

## Files

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generate mock users, articles, interactions
└── main.py             # Run the recommendation feed demo
```

---

## References

- RushDB Documentation: https://docs.rushdb.com
- GitHub: https://github.com/rush-db/examples/tree/main/time-weighted-graph-traversals-for-recency-aware-r-usecase
