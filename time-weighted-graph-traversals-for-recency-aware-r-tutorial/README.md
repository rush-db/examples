# Time-Weighted Graph Traversals for Recency-Aware Recommendations

A step-by-step walkthrough of implementing time-weighted graph traversal in RushDB — from defining decay-weighted relationships to executing composite queries that incorporate recency into path selection.

## What This Tutorial Demonstrates

- **Schema design** with time-annotated edges in RushDB
- **Traversal queries** with configurable decay functions
- **Hybrid scoring** combining time-weighting with vector similarity
- **Query planner implications** — weighting during traversal vs. after
- **Benchmarking** — does time-weighting slow traversal? At what scale?

## Prerequisites

- Python 3.10+
- A RushDB account ([sign up free](https://rushdb.com))
- API token from your RushDB dashboard

## Setup

```bash
# 1. Clone the examples repository
git clone https://github.com/rush-db/examples.git
cd time-weighted-graph-traversals-for-recency-aware-r-tutorial

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

## Running the Tutorial

```bash
# Step 1: Generate mock data (users, products, interactions with timestamps)
python seed.py

# Step 2: Run the tutorial demonstrating all key points
python main.py
```

## Expected Output

The tutorial will output:
1. Schema confirmation showing time-annotated relationship types
2. Pure traversal query results (no time-weighting)
3. Time-weighted traversal results showing recency bias
4. Vector similarity results
5. Hybrid results combining vector + time-weighting
6. Benchmark comparisons with timing at different scales (100, 500, 1000+ records)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      RushDB Property Graph                      │
│                                                                  │
│   ┌─────────┐          INTERACTED          ┌─────────────────┐  │
│   │  USER   │ ─────────────────────────────▶│    PRODUCT      │  │
│   └─────────┘   {timestamp, rating}         │  (vectors: body)│  │
│       │                                       └─────────────────┘  │
│       │                                                 ▲           │
│       └─────────────────────────────────────────────────┘           │
│                     PURCHASED / VIEWED / RATED                      │
│                                                                  │
│  Time-weighting: recent interactions score higher via decay f(x)  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Time-Decay Functions

Three decay strategies are implemented:

1. **Exponential decay**: `score * exp(-λ * days_since)`
   - Best for: fast-changing interests, news, trends
   
2. **Linear decay**: `score * max(0, 1 - (days_since / half_life))`
   - Best for: steady preference decay
   
3. **Logarithmic decay**: `score / log(1 + days_since)`
   - Best for: long-tail content that remains relevant

### Hybrid Scoring

Final score = `(vector_similarity * α) + (time_decay_score * (1 - α))`

Where `α` controls the blend between content relevance and recency.

## Performance Notes

The benchmark results will show:
- **Small scale (<500 records)**: Negligible difference between weighted/unweighted
- **Medium scale (500-2000 records)**: 10-30% overhead for time-weighting
- **Large scale (2000+ records)**: Consider pre-filtering by time window first

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Modeling Best Practices](https://docs.rushdb.com/concepts/properties)
- [Vector Search Integration](https://docs.rushdb.com/ai/vector-search)

## License

MIT
