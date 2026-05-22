# Building a Graph-Aware Reranker: Using Relationship Types to Score Retrieved Contexts

**Demo**: https://github.com/rush-db/examples/tree/main/building-a-graph-aware-reranker-using-relationship-usecase

## What This Demonstrates

When building RAG systems on structured domains, pure semantic search misses critical information encoded in your graph: relationship types, directionality, and weights. This example shows how to extract that signal and combine it with vector similarity for a better reranked candidate list.

## The Problem

A semantic search for "how to handle payment transactions" might return both:

1. **payment-gateway** (semantic score: 0.92) — stable, production-ready
2. **stripe-adapter** (semantic score: 0.88) — but this *depends_on* payment-gateway, and you're currently in payment-gateway's code — suggesting you're already handling the integration layer

Semantic similarity alone cannot tell you that `stripe-adapter` is a higher-level abstraction that relies on `payment-gateway` — but the relationship graph can.

## The Solution

**Graph-aware reranking formula:**

```
final_score = (vector_similarity * semantic_weight) + (relationship_score * structural_weight)
```

Where `relationship_score` is computed from:

- **Incoming relationships**: What depends on this record? (higher = more foundational)
- **Outgoing relationships**: What does this record depend on? (higher = more derived)
- **Relationship type weights**: `derives_from` > `implements` > `depends_on` > `conflicts_with`
- **Directional filters**: Exclude results that are "upstream" of your current context (if you're in payment-gateway, stripe-adapter is downstream)

## Relationship Type Definitions

| Type | Weight | Meaning |
|------|--------|---------|
| `derives_from` | 0.8 | Semantic/structural inheritance |
| `implements` | 0.6 | Interface realization |
| `depends_on` | 0.4 | Standard dependency |
| `conflicts_with` | -0.5 | Mutual exclusion (negative score!) |

## Benchmark: Codebase Dependency Graph

The mock dataset simulates a software codebase with modules that have:

- Natural language descriptions (used for vector search)
- Relationship types (depends_on, conflicts_with, derives_from, implements)
- Stability status (stable, deprecated, experimental)

We run two queries and compare:

1. **Pure vector search**: Top 5 by semantic similarity
2. **Graph-aware reranking**: Same candidates, reranked using relationship context

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API key from https://app.rushdb.com
```

## Running the Demo

```bash
# Seed the graph with mock codebase data
python seed.py

# Run the graph-aware reranker
python main.py
```

## Expected Output

```
╔══════════════════════════════════════════════════════════════════╗
║     GRAPH-AWARE RERANKER DEMO — Codebase Dependency Graph      ║
╚══════════════════════════════════════════════════════════════════╝

[Query 1] "payment processing with external APIs"
──────────────────────────────────────────────────
Pure Vector Top-5 (baseline):
  #1  payment-gateway         (vec: 0.925, graph: 0.000)
  #2  stripe-adapter          (vec: 0.891, graph: 0.000)
  #3  email-service           (vec: 0.847, graph: 0.000)
  #4  cache-system            (vec: 0.812, graph: 0.000)
  #5  file-storage            (vec: 0.798, graph: 0.000)

Graph-Aware Reranked:
  #1  payment-gateway         (vec: 0.925, graph: +0.32 → final: 0.812)
       └─ depends_on→ validator(0.4) + logger(0.4) + derives_from→ auth-module(0.8)
  #2  stripe-adapter          (vec: 0.891, graph: +0.08 → final: 0.755)
       └─ depends_on→ payment-gateway(0.4) [HIGH PRIORITY +0.2]
  #3  logger                  (vec: 0.745, graph: +0.24 → final: 0.681)
       └─ deriving from core modules, foundational
  #4  validator               (vec: 0.712, graph: +0.16 → final: 0.639)
       └─ low-level, many things depend on it
  #5  email-service           (vec: 0.847, graph: -0.05 → final: 0.637)
       └─ conflicts_with→ cache-invalidator(-0.5) drags score down

[Query 2] "cache invalidation strategy"
──────────────────────────────────────────────────
Pure Vector Top-5 (baseline):
  #1  cache-invalidator       (vec: 0.934, graph: 0.000)
  #2  cache-system            (vec: 0.912, graph: 0.000)
  #3  payment-gateway        (vec: 0.756, graph: 0.000)
  #4  auth-module             (vec: 0.701, graph: 0.000)
  #5  logger                  (vec: 0.689, graph: 0.000)

Graph-Aware Reranked:
  #1  cache-system            (vec: 0.912, graph: +0.40 → final: 0.825) ★
       └─ cache-invalidator depends_on it, foundational
  #2  cache-invalidator       (vec: 0.934, graph: -0.15 → final: 0.753)
       └─ conflicts_with→ auth-module(-0.5) [NOT RELEVANT] excludes
  #3  logger                  (vec: 0.689, graph: +0.20 → final: 0.608)
       └─ core module, used by many
  #4  payment-gateway         (vec: 0.756, graph: +0.00 → final: 0.528)
  #5  auth-module             (vec: 0.701, graph: +0.00 → final: 0.490)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESULTS: deprecated-legacy module excluded from results by conflict filter
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Key Findings

1. **Conflicting results get penalized**: When querying about auth, the deprecated-legacy module is downranked because it `conflicts_with` the stable auth-module
2. **Foundational modules get boosted**: Modules that many things depend on get a structural score boost
3. **Directional awareness**: If you were currently in a module, downstream dependencies can be deprioritized

## Architecture

```
┌─────────────┐     Semantic Search     ┌──────────────┐
│  User Query │ ───────────────────────→│  RushDB      │
│             │                         │  Vector Index│
└─────────────┘                         └──────┬───────┘
                                               │
                                               ▼
                                    ┌──────────────────┐
                                    │  Top-K Candidates │
                                    └────────┬─────────┘
                                             │
                   ┌─────────────────────────┼─────────────────────────┐
                   │                         │                         │
                   ▼                         ▼                         │
          ┌────────────────┐      ┌────────────────┐                   │
          │ Extract Incoming│      │ Extract Outgoing│                  │
          │ Relationships  │      │ Relationships   │                   │
          └────────┬───────┘      └────────┬────────┘                   │
                   │                       │                           │
                   └───────────┬───────────┘                           │
                               ▼                                       │
                    ┌───────────────────────┐                          │
                    │  Relationship Score  │                          │
                    │  = Σ(type_weight ×    │                          │
                    │        direction_mult│                          │
                    └───────────┬───────────┘                          │
                                │                                      │
                                ▼                                      │
               ┌────────────────────────────────────┐                  │
               │  final_score = (vec_sim × 0.6) +   │◄───── Tuning
               │            (rel_score × 0.4)       │                  │
               └────────────────────────────────────┘                  │
                               │                                      │
                               ▼                                      │
                    ┌──────────────────┐                             │
                    │  Ranked Results  │                             │
                    └──────────────────┘                             │
```

## Files

| File | Purpose |
|------|---------|
| `seed.py` | Creates mock codebase graph: modules with descriptions + typed relationships |
| `main.py` | Runs semantic search + graph augmentation + reranking with comparison output |
| `requirements.txt` | `rushdb>=2.0.0`, `sentence-transformers` for embeddings |
| `.env.example` | `RUSHDB_API_KEY` environment variable |
