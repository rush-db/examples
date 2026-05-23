# Detecting Hallucination Chains Using Graph Inconsistency Scoring

This tutorial demonstrates how to use RushDB's graph structure to detect hallucination chains in LLM-generated content. By modeling claims as nodes and their logical relationships as edges, we can identify contradictory information chains that indicate hallucination.

## What You'll Learn

- Modeling LLM-generated claims as a property graph in RushDB
- Creating relationship edges between claims (SUPPORTS, CONTRADICTS)
- Computing graph-based inconsistency scores through traversal
- Identifying hallucination chains (paths of contradictory claims)

## Prerequisites

- Python 3.10+
- RushDB API key (Free tier works)
- `rushdb>=2.0.0` and `sentence-transformers` packages

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Understanding the Approach

### The Hallucination Detection Problem

LLMs often generate claims that contradict each other, especially in long-form outputs. A single claim may not look suspicious in isolation, but chains of contradictions reveal hallucination patterns.

### Graph-Based Solution

1. **Claims as Nodes**: Each extracted claim becomes a Record with the `CLAIM` label
2. **Entities as Nodes**: Entities mentioned in claims become `ENTITY` records
3. **Relationships as Edges**: Semantic relationships link claims:
   - `CONTRADICTS` — claims with opposite truth values
   - `SUPPORTS` — claims that reinforce each other
   - `MENTIONS` — claim references an entity

### Inconsistency Scoring Algorithm

1. For a target entity, find all claims mentioning it
2. Build a subgraph of relationships between these claims
3. Count contradiction paths vs. support paths
4. Score = (contradiction edges) / (total edges) — higher = more likely hallucination

## How to Run

```bash
# First, seed the database with sample claims
python seed.py

# Then run the hallucination detection
python main.py
```

The output will show:
- Entity inconsistency scores
- Detected hallucination chains
- Visual representation of claim relationships

## Project Structure

```
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── seed.py             # Generate sample claims with contradictions
├── detector.py         # Hallucination detection engine
├── main.py             # Main execution script
└── .env                # Your API key (create from .env.example)
```

## Key RushDB Features Used

| Feature | Purpose |
|---------|---------|
| `db.records.create()` | Create CLAIM and ENTITY nodes |
| `db.records.attach()` | Link claims with CONTRADICTS/SUPPORTS edges |
| `db.records.find()` | Query claims by entity or label |
| `db.ai.search()` | Semantic search for similar claims |
| Transactions | Atomic creation of claim graphs |

## Expected Output

When run against the seeded data, you'll see:

```
=== Hallucination Detection Report ===

Entity: Apple Inc.
  Claims: 5
  Contradictions: 3
  Inconsistency Score: 0.60 (HIGH)
  Hallucination Chain: "Apple founded in 1976" → CONTRADICTS → "Apple founded in 1984"

Entity: Tesla
  Claims: 3
  Contradictions: 0
  Inconsistency Score: 0.00 (LOW)
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph-Based Knowledge Validation](https://rushdb.com/blog)
- [Property Graph Modeling Best Practices](https://docs.rushdb.com/concepts)
