# Context Recycling: Reusing Graph-Retrieved Evidence Across Related Queries

This example demonstrates **context recycling** — a pattern that transforms expensive repeated graph traversals into single-query operations, enabling real-time relationship-aware AI responses without latency penalties.

## What is Context Recycling?

In graph-backed AI applications, a single user question often requires multiple related queries:

> "Tell me about Project Atlas — who works on it, what technologies does it use, and what are the dependencies?"

A naive approach triggers **3 separate graph traversals** (one per relationship type). With context recycling, you:

1. **Fetch the subgraph once** — all connected evidence in a single traversal
2. **Cache it keyed by entity ID** — evidence for "Project Atlas" is stored
3. **Reuse it** for any related query about Project Atlas (instant retrieval)

## What This Example Demonstrates

| Scenario | Description |
|----------|-------------|
| **Without Recycling** | 3 sequential graph traversals for 3 related queries |
| **With Recycling** | 1 traversal, cached, reused for all related queries |
| **Performance Delta** | Measured latency comparison at scale |
| **Freshness Tradeoffs** | TTL strategies, stale data risks, and when to invalidate |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WITHOUT RECYCLING                        │
├─────────────────────────────────────────────────────────────────┤
│  Query 1: "Project Atlas team"      → Graph Traversal (50ms)    │
│  Query 2: "Project Atlas tech"      → Graph Traversal (50ms)    │
│  Query 3: "Project Atlas deps"      → Graph Traversal (50ms)    │
│  ───────────────────────────────────────────────────────────    │
│  Total: 150ms, 3 traversals, redundant work                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          WITH RECYCLING                         │
├─────────────────────────────────────────────────────────────────┤
│  Query 1: Fetch subgraph                → Graph Traversal      │
│            └─→ Cache[atlas_001]         → 50ms + cache write    │
│                                                                 │
│  Query 2: Cache lookup[atlas_001]       → 0.1ms (cache hit)    │
│  Query 3: Cache lookup[atlas_001]       → 0.1ms (cache hit)     │
│  ───────────────────────────────────────────────────────────    │
│  Total: 50ms + 2 cache lookups, no redundant traversals        │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://rushdb.com))
- `rushdb>=2.0.0`

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

Get your API key from the [RushDB dashboard](https://app.rushdb.com).

### 3. Seed the Database

This creates a realistic knowledge graph with projects, team members, technologies, and dependencies:

```bash
python seed.py
```

The seed script:
- Creates 8 software projects with full metadata
- Links 12+ team members to projects
- Associates 15+ technologies with projects
- Establishes inter-project dependencies
- Is **idempotent** — safe to run multiple times

## Running the Example

```bash
python main.py
```

### Expected Output

```
============================================================
CONTEXT RECYCLING DEMONSTRATION
============================================================

SEEDING KNOWLEDGE GRAPH...
✓ Created 8 PROJECT records
✓ Created 12 TEAM_MEMBER records
✓ Created 15 TECHNOLOGY records
✓ Established 45+ relationships

------------------------------------------------------------
SCENARIO: "Tell me about Project Atlas"
  - Who works on it?
  - What technologies does it use?
  - What are its dependencies?
------------------------------------------------------------

WITHOUT RECYCLING (3 sequential traversals):
  Query "team":       12.4ms
  Query "technologies": 11.8ms
  Query "dependencies": 10.9ms
  ─────────────────────────────────
  Total: 35.1ms (3 traversals)

WITH RECYCLING (1 traversal, cached):
  First query (traverse): 13.2ms
  Cache stored: atlas_001 (45 evidence nodes)
  Second query (cache):    0.08ms  ✓
  Third query (cache):     0.06ms  ✓
  ─────────────────────────────────
  Total: 13.4ms (1 traversal + 2 cache hits)

SPEEDUP: 2.6x faster for related queries

------------------------------------------------------------
FRESHNESS TRADE-OFFS
------------------------------------------------------------

Staleness Examples:
  • Team member leaves → cache still shows them on project
  • New technology adopted → cache misses the update
  • Dependency removed → cache reflects removed relationship

TTL Strategy Analysis:
  • 5 minutes:  Good for real-time chat, may miss fast changes
  • 1 hour:    Safe for documentation, stale for active projects
  • 24 hours:  Batch processing only, inappropriate for AI apps

Cache Invalidation Triggers:
  ✓ Manual: User requests fresh data
  ✓ Event:  Webhook on PROJECT update → invalidate cache
  ✓ Time:   TTL expiration
  ✓ Scope:  Cascade invalidation to related entities

============================================================
CLEANUP COMPLETE
============================================================
```

## Project Structure

```
context-recycling-reusing-graph-retrieved-evidence-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Knowledge graph data generator
└── main.py             # Main demonstration
```

## Key Insights

### When Recycling Works Best

- **Same entity, multiple relationship queries** — ideal use case
- **High fan-out graphs** — more you traverse, more you save
- **Read-heavy workloads** — chat, Q&A, document generation

### When Recycling Breaks Down

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Stale data** | Deleted team members still appear | TTL + event-based invalidation |
| **Memory growth** | Unbounded cache size | LRU eviction, TTL-based cleanup |
| **Consistency lag** | Write/read divergence | Versioned caches, write-through |
| **Cold start** | First query is slow | Pre-warming on high-value entities |

### TTL Recommendations by Use Case

| Use Case | Recommended TTL | Rationale |
|----------|-----------------|----------|
| Real-time chat | 1-5 minutes | Freshness matters, queries are rapid |
| Document Q&A | 15-30 minutes | Stable context, reduced load |
| Batch processing | 1-24 hours | Consistency over performance |
| Static analysis | No expiry* | + manual invalidation |

*With careful cache invalidation on known write events.

## How RushDB Enables This Pattern

RushDB's property graph model makes context recycling efficient:

1. **Single traversal fetches all evidence** — `find()` with label filtering gets the subgraph in one call
2. **Relationships are first-class** — no JOINs needed, just traverse edges
3. **Schema-flexible** — evidence structure can evolve without migrations
4. **Free reads** — cache misses are cheap, no per-query cost anxiety

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Patterns in RAG](https://github.com/rush-db/examples)
- [RushDB GitHub Repository](https://github.com/rush-db/rush-db)
