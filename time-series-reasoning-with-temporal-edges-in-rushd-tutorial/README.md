# Time-Series Reasoning with Temporal Edges in RushDB

A practical tutorial demonstrating how to model, store, and query time-series events using RushDB's property graph with temporal relationships.

## What You'll Learn

- **Modeling time-series data** as connected event records with temporal edges
- **Creating temporal relationships** (BEFORE, AFTER, CAUSED, TRIGGERED_BY)
- **Querying temporal patterns** — find events by time ranges, sequences, and causal chains
- **Traversing temporal graphs** to reason about event sequences and dependencies

## The Approach

RushDB excels at representing **event sequences as a graph** rather than a flat table. Instead of storing timestamps and filtering with SQL, you model each event as a record and connect them with typed temporal relationships. This enables:

- **Sequence reasoning**: "Did event A always precede event B?"
- **Causal chains**: Trace back from an outcome to its root causes
- **Pattern detection**: Find recurring temporal patterns across the graph

## Prerequisites

- Python 3.9+
- RushDB account ([get started free](https://rushdb.com))
- `rushdb>=2.0.0`

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RUSHDB_API_KEY
```

## Running

```bash
# 1. Seed the database with time-series event data
python seed.py

# 2. Run the tutorial demonstrating temporal reasoning
python main.py
```

## Project Structure

| File | Purpose |
|------|---------|
| `seed.py` | Generates mock sensor/actuator events and creates temporal edges |
| `main.py` | Demonstrates temporal queries, traversal, and reasoning patterns |
| `data/events.json` | Sample event data used by seed script |

## Expected Output

The tutorial will demonstrate:

1. **Time-range queries** — Find events within a specific window
2. **Sequence detection** — Identify repeating event patterns
3. **Causal chain traversal** — Trace a fault back to root causes
4. **Aggregation over temporal edges** — Count events between two points

---

GitHub: [rush-db/examples](https://github.com/rush-db/examples/tree/main/time-series-reasoning-with-temporal-edges-in-rushd-tutorial)

RushDB Docs: [docs.rushdb.com](https://docs.rushdb.com)
