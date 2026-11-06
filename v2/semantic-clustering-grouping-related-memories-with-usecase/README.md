# Semantic Clustering: Contextual Memory Assistant

A demonstration of RushDB's hybrid graph + vector search capabilities for building a developer memory system.

## What it demonstrates

When you're working on a task, you need more than just "the same thing happening before" — you need:

1. **Explicit relationships**: tasks that block this, decisions that informed this, parent work items
2. **Semantic similarity**: discussions about similar problems, past approaches to similar refactors
3. **Both combined**: the complete picture that neither graph traversal nor vector search provides alone

This example simulates a developer tool that, given a current task, surfaces:
- Related decisions from the graph
- Similar past work from vector search
- Bugs that were encountered during similar refactors
- The complete contextual memory cluster

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Memory System                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Current Task: "Refactor auth service"                      │
│       │                                                     │
│       ├── Graph Traversal                                   │
│       │   └── Find: blocking tasks, parent decisions,        │
│       │       related refactors in the relationship graph   │
│       │                                                     │
│       └── Vector Search                                      │
│           └── Find: semantically similar past memories,     │
│               discussions about auth patterns,              │
│               similar architectural changes                 │
│                                                              │
│       ┌──────────────────────────────────────────┐         │
│       │      Combined: Complete Context Cluster    │         │
│       │  ┌─────────────┐    ┌──────────────────┐  │         │
│       │  │ Graph Path │ +  │ Vector Proximity │  │         │
│       │  │ (explicit) │    │ (implicit)       │  │         │
│       │  └─────────────┘    └──────────────────┘  │         │
│       └──────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Project structure

```
semantic-clustering-grouping-related-memories-with-usecase/
├── data/
│   └── seed_memories.json     # Developer memory seed data
├── seed.py                    # Load seed memories into RushDB
├── main.py                    # Main query engine demonstration
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure RushDB

Copy `.env.example` to `.env` and add your RushDB credentials:

```bash
cp .env.example .env
```

Get your API key from https://app.rushdb.com/settings/api-keys

### 3. Seed the knowledge base

```bash
python seed.py
```

This creates ~50 developer memories about a fictional project with:
- Tasks, decisions, learnings, bugs, and refactor notes
- Explicit relationships (blocks, relates_to, informed_by, parent_of)
- Text content suitable for semantic clustering

The seeding is idempotent — run it multiple times safely.

## Running the demo

```bash
python main.py
```

Expected output:

```
╔══════════════════════════════════════════════════════════════════╗
║   SEMANTIC MEMORY CLUSTER: "Refactor auth service"              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  📊 GRAPH RELATIONSHIPS                                           ║
║  ─────────────────────────                                        ║
║  └─ [TASK] Auth Service Refactoring (ID: ...)                    ║
║       └─ [BLOCKS] Auth Service Tests (ID: ...)                   ║
║       └─ [INFORMED_BY] Migration to JWT tokens (ID: ...)          ║
║                                                                    ║
║  📐 VECTOR SIMILARITY                                             ║
║  ─────────────────────                                            ║
║  1. [0.943] Session token refactoring notes                      ║
║  2. [0.917] Cookie handling in auth middleware                   ║
║  3. [0.891] Refactored payment service auth pattern              ║\n║  4. [0.867] Auth middleware decision record                      ║
║  5. [0.842] User service auth changes                            ║
║                                                                    ║
║  🔗 COMPLETE CONTEXT CLUSTER                                      ║
║  ─────────────────────────────                                    ║
║  (Graph path) Auth Service Refactoring → Migration to JWT tokens  ║
║  (Graph path) Auth Service Refactoring → Auth Service Tests       ║
║  (Vector)   Session token refactoring notes [0.943]               ║
║  (Vector)   Cookie handling in auth middleware [0.917]            ║
║  (Graph path) Auth Service Tests → Bug: Token refresh race cond.  ║
╚══════════════════════════════════════════════════════════════════╝
```

## How it works

### 1. Graph traversal (explicit relationships)

```sdk
# Find all records directly related to the current task
related = db.records.find({
    "labels": ["TASK", "DECISION", "REFACTOR", "BUG", "LEARNING"],
    "where": {
        "$or": [
            {"TASK": {"$relation": {"type": "BLOCKS"}}, "title": {"$contains": "Auth"}},
            {"TASK": {"$relation": {"type": "INFORMED_BY"}}, "title": {"$contains": "auth"}}
        ]
    }
})
```

### 2. Vector search (semantic similarity)

```sdk
# Find semantically similar memories
similar = db.ai.search({
    "propertyName": "content",
    "query": "auth service refactoring jwt token migration",
    "labels": ["DECISION", "REFACTOR", "BUG", "LEARNING"],
    "limit": 5
})
```

### 3. Hybrid traversal with vector augmentation

```sdk
# Walk 2 hops from current task, then find similar content
# Uses graph structure to find first-hop neighbors,
# then vector search to find semantically related content
# the graph structure might miss
```

## Key insight

**Graph traversal finds explicit relationships, but misses implicit connections.**

Two refactors might not be connected in the graph, but if both discuss "migrating to JWT" and "handling token refresh", they're semantically related. Vector search catches this.

**Vector search finds similar content, but misses structural context.**

The fact that Task A blocks Task B is explicit in the graph, but a vector search might not surface that relationship. Graph traversal catches this.

**Combined = complete picture.**

## Cleaning up

To remove all seeded data:

```python
from rushdb import RushDB
import os

db = RushDB(os.getenv("RUSHDB_API_KEY"))
db.records.delete_many({"labels": ["TASK", "DECISION", "REFACTOR", "BUG", "LEARNING"]})
```

## Resources

- RushDB Documentation: https://docs.rushdb.com
- SDK Reference: https://docs.rushdb.com/sdk/python
- GitHub: https://github.com/rush-db/examples/tree/main/semantic-clustering-grouping-related-memories-with-usecase
