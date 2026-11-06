# Temporal Decay Models for Automatic Pruning of Stale Agent Memories

## Overview

This project demonstrates how to implement **temporal decay models** for automatically pruning stale memories in AI agent systems using RushDB as the memory layer.

### What are Temporal Decay Models?

Temporal decay models simulate how information relevance decreases over time. In AI agent memory systems:
- Fresh memories are highly relevant and easily accessible
- Older memories decay in importance unless reinforced through access
- Periodic pruning removes memories that fall below a relevance threshold

### Key Concepts Demonstrated

1. **Memory Lifecycle Management** — Track creation time, access patterns, and computed relevance scores
2. **Exponential Decay Function** — `relevance = initial_importance × e^(-λ × age_hours)`
3. **Access Reinforcement** — When a memory is accessed, boost its relevance (spaced repetition effect)
4. **Threshold-Based Pruning** — Automatically delete memories below relevance threshold
5. **Graph Relationships** — Connect memories to agents and contexts for traversal

### Why RushDB?

RushDB provides:
- Native graph relationships between memories, agents, and contexts
- Property indexing for efficient time-based queries
- Transaction support for atomic pruning operations
- Zero-schema flexibility for evolving memory structures

## Architecture

```
Agent
  └── HAS_MEMORY ──► Memory (content, timestamps, scores)
  └── OPERATES_IN ──► Context (conversation/session)
  └── PERFORMED ────► Action (tool calls, decisions)
```

Memory record schema:
- `content`: The actual memory content
- `initialImportance`: Base importance (0.0 - 1.0)
- `decayRate`: Lambda parameter for decay (higher = faster decay)
- `createdAt`: ISO timestamp
- `lastAccessedAt`: ISO timestamp
- `accessCount`: Number of times accessed
- `category`: Memory type (fact, preference, context, skill)

## Prerequisites

- Python 3.9+
- RushDB account (free tier available at https://rushdb.com)
- `rushdb>=2.0.0` Python package

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

Get your API token from the RushDB dashboard at https://dash.rushdb.com

### 3. Seed Mock Data (Optional)

The seed script generates realistic agent memory data demonstrating various decay scenarios:

```bash
python seed.py
```

This creates:
- 1 agent with memories across different categories
- ~50 memory records with varying ages and importance scores
- Context records linking related memories

## Running the Demo

### Main Script

```bash
python main.py
```

The script demonstrates:

1. **Initialize Agent Memory System** — Create agent and seed initial memories
2. **Compute Current Relevance** — Apply decay formula to all memories
3. **Access Memory with Reinforcement** — Simulate memory retrieval, boost relevance
4. **Prune Stale Memories** — Remove memories below threshold
5. **Memory Statistics** — Show before/after counts and category breakdown

### Output Interpretation

```
=== Agent Memory System Demo ===

Initial State:
  Total memories: 47
  Category breakdown: {...}

Relevance Scores (decay applied):
  Memory: "User prefers dark mode" | relevance: 0.78 | category: preference
  Memory: "Last week meeting notes" | relevance: 0.12 | category: context

After accessing "User prefers dark mode" (reinforcement):
  Memory: "User prefers dark mode" | relevance: 0.95

Pruning memories with relevance < 0.30:
  Deleted 8 stale memories
  Remaining: 39 memories

Final Statistics:
  By category: {...}
  Average relevance: 0.67
```

## Decay Model Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DECAY_LAMBDA` | 0.05 | Controls decay speed (0.05 = ~5% decay per hour) |
| `RELEVANCE_THRESHOLD` | 0.30 | Memories below this are pruned |
| `REINFORCEMENT_BOOST` | 0.20 | Relevance increase on access |
| `MAX_ACCESS_REINFORCEMENT` | 5 | Cap on access count multiplier |

## Extending the Model

### Custom Decay Functions

```python
def linear_decay(initial: float, hours: float, rate: float) -> float:
    """Linear decay: relevance = max(0, initial - rate * hours)"""
    return max(0.0, initial - rate * hours)

def step_decay(initial: float, hours: float, step_size: float = 24) -> float:
    """Step decay: relevance drops by 10% every 24 hours"""
    steps = int(hours / step_size)
    return max(0.0, initial * (0.9 ** steps))
```

### Category-Specific Decay

Different memory types decay at different rates:
- `fact`: Low decay (λ = 0.01) — factual knowledge persists
- `preference`: Medium decay (λ = 0.05) — preferences fade slowly
- `context`: High decay (λ = 0.15) — recent context decays fast
- `skill`: Very low decay (λ = 0.005) — skills are persistent

## Project Structure

```
temporal-decay-models-for-automatic-pruning-of-sta-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Mock data generation
└── main.py            # Main demo script
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Agent Memory Patterns](https://docs.rushdb.com/patterns)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)

## License

MIT
