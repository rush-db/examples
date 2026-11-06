# From Retrieval to Reasoning: Graph-Structured Memory for AI Agents

This tutorial demonstrates how RushDB serves as a production-grade memory layer for AI agents, enabling multi-step reasoning through graph-structured context retrieval.

## What You'll Build

A simulation of an AI agent that:
1. **Retrieves** relevant context via semantic search
2. **Chains** reasoning steps as a graph of thought records
3. **Traverses** relationships to reconstruct decision paths
4. **Answers** complex queries requiring multi-hop reasoning

## Core Concepts Demonstrated

| Concept | Implementation |
|---------|----------------|
| **Memory Records** | `THOUGHT`, `OBSERVATION`, `ACTION`, `CONTEXT` labels |
| **Semantic Retrieval** | `db.ai.search()` for finding relevant context |
| **Graph Traversal** | Relationship filtering via `where` clauses |
| **Multi-step Reasoning** | Chained record creation with transaction support |
| **Context Windows** | Hierarchical memory with priority and recency |

## Prerequisites

- Python 3.9+
- RushDB account (free tier works)
- `rushdb>=2.0.0`

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API key

# Seed the memory store with demo data
python seed.py
```

## Running the Tutorial

```bash
python main.py
```

The script demonstrates three reasoning patterns:

1. **Single-hop retrieval** — Find relevant context for a query
2. **Multi-hop reasoning** — Trace a chain of thoughts leading to a conclusion
3. **Full decision reconstruction** — Replay an agent's reasoning from observations to actions

## Expected Output

```
=== AI Agent Memory System ===

[1] Semantic Search: "neural network optimization techniques"
   Found: 2 relevant context records
   - "Dropout as regularization" (score: 0.923)
   - "Learning rate scheduling strategies" (score: 0.891)

[2] Multi-hop Reasoning: Tracing decision path for "Model A"
   Step 1: OBSERVATION "Training loss decreasing slowly" → REASONED_ABOUT → THOUGHT "Investigate optimization"
   Step 2: THOUGHT "Investigate optimization" → LED_TO → ACTION "Apply learning rate decay"
   Conclusion: Decision path reconstructed in 2 hops

[3] Full Decision Reconstruction for "batch_size experiment"
   - OBSERVATION: "Current batch_size=16, GPU utilization low"
   - THOUGHT chain: ["Low GPU utilization indicates...", "Increasing batch may...", "Test batch_size=32"]
   - ACTION: "Set batch_size=32, monitor GPU utilization"
   Decision trace complete ✓
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent                              │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Reasoning  │───▶│   Memory     │◀───│    Action    │   │
│  │   Engine    │    │   (RushDB)   │    │   Executor   │   │
│  └─────────────┘    └──────────────┘    └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ THOUGHT  │   │ OBSERVATION│  │  ACTION  │
      │  (nodes) │   │   (nodes)  │   │  (nodes) │
      └─────┬────┘   └─────┬──────┘   └─────┬────┘
            │              │                │
            ▼              ▼                ▼
      REASONED_ABOUT   DERIVED_FROM     CAUSED_BY
            │              │                │
            └──────────────┴────────────────┘
```

## Key RushDB Patterns Used

- **Inline vector writes**: Embed context during record creation
- **Semantic search with filters**: `db.ai.search()` with `labels` and `where`
- **Relationship traversal**: Query by related record properties
- **Transaction support**: Atomic multi-step reasoning chains
- **Property indexing**: Fast filtering on metadata fields

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Memory Patterns](https://rushdb.com/docs)
- [AI Memory Layer Architecture](https://rushdb.com/docs)

## License

MIT