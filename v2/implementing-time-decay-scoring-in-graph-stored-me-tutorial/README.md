# Implementing Time-Decay Scoring in Graph-Stored Memories

A step-by-step guide to implementing recency-aware retrieval in RushDB, covering decay algorithms, temporal metadata storage, and combining semantic search with time-weighted scoring.

## What This Tutorial Demonstrates

- **Choosing decay functions**: exponential, logarithmic, and custom halflife-based decay
- **Storing temporal metadata**: correct schema for efficient time-based queries
- **Combining semantic search + decay**: hybrid retrieval that respects both relevance and recency
- **Edge weight vs node property decay**: when to apply decay at different graph layers
- **Parameter tuning**: testing decay rates on a real dataset

## Prerequisites

- Python 3.9+
- A RushDB account ([get one free](https://rushdb.com))
- `rushdb>=2.0.0` Python package

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

## Quick Start

```bash
# 1. Seed the database with timestamped memory records
python seed.py

# 2. Run the main tutorial examples
python main.py
```

## Project Structure

```
implementing-time-decay-scoring-in-graph-stored-me-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py            # Generates mock memory data with timestamps
└── main.py            # Tutorial implementation
```

## Decay Functions Explained

### Exponential Decay
Best for: rapid information decay (social feeds, notifications)
```python
decayed_score = base_score * math.exp(-decay_rate * hours_elapsed)
```

### Logarithmic Decay
Best for: slow, diminishing decay (knowledge bases, long-term memory)
```python
decayed_score = base_score / (1 + math.log(1 + hours_elapsed))
```

### Halflife-Based Decay
Best for: tunable, predictable decay (spaced repetition, content curation)
```python
decayed_score = base_score * math.pow(0.5, hours_elapsed / half_life_hours)
```

## Expected Output

After running `main.py`, you'll see:
1. Raw vs. decayed scores for each memory type
2. Semantic search results with time-decay applied
3. Graph traversal with edge-weighted decay
4. Comparison of different decay functions

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [Graph-Based Memory Systems](https://rushdb.com/blog)

## License

MIT License - feel free to use this code in your own projects.
