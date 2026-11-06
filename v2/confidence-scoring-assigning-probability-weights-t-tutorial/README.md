# Confidence Scoring: Assigning Probability Weights to Graph-Retrieved Facts

A tutorial demonstrating how to use RushDB to store, query, and compute confidence scores for facts retrieved from a knowledge graph.

## What This Demonstrates

- **Record-level confidence scores**: Storing probability weights directly on fact records
- **Source reliability propagation**: Using source reliability to adjust fact confidence
- **Graph traversal for confidence aggregation**: Computing aggregate confidence through relationship traversal
- **Vector similarity as confidence**: Using `db.ai.search()` scores as probability indicators

## Prerequisites

- Python 3.9+
- A RushDB API key (get one at https://app.rushdb.com)
- `rushdb>=2.0.0` installed

## Setup

1. **Install dependencies**:

```bash
pip install -r requirements.txt
```

2. **Configure environment**:

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

3. **Seed the database** (optional — creates sample facts and sources):

```bash
python seed.py
```

## Running the Tutorial

```bash
python main.py
```

### Expected Output

The script demonstrates:
1. Creating facts with confidence scores
2. Creating sources with reliability ratings
3. Linking facts to supporting sources
4. Computing aggregate confidence through graph traversal
5. Querying facts filtered by confidence threshold
6. Using vector search results with similarity scores

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Core tutorial demonstrating confidence scoring patterns |
| `seed.py` | Generates mock facts, sources, and relationships |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

## Key Patterns

### Storing Confidence Scores

Facts are stored with explicit confidence values between 0.0 and 1.0:

```sdk
fact = db.records.create(
    label="FACT",
    data={
        "statement": "Climate change is primarily human-caused",
        "confidence": 0.95,
        "category": "science"
    }
)
___SPLIT___
const fact = await db.records.create({
  label: 'FACT',
  data: {
    statement: 'Climate change is primarily human-caused',
    confidence: 0.95,
    category: 'science'
  }
})
```

### Source Reliability Weighting

Sources have reliability scores that propagate to linked facts:

```sdk
source = db.records.create(
    label="SOURCE",
    data={
        "name": "Nature Journal",
        "reliability": 0.9,
        "type": "peer_reviewed"
    }
)
___SPLIT___
const source = await db.records.create({
  label: 'SOURCE',
  data: {
    name: 'Nature Journal',
    reliability: 0.9,
    type: 'peer_reviewed'
  }
})
```

### Computing Aggregate Confidence

When a fact has multiple supporting sources, aggregate confidence is computed as:

```
aggregate_confidence = base_confidence * (1 - (1 - s1) * (1 - s2) * ... * (1 - sn))
```

Where `s1, s2, ..., sn` are the reliability scores of supporting sources.

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB SDK Reference](https://docs.rushdb.com/sdk/python)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/confidence-scoring-assigning-probability-weights-t-tutorial)
