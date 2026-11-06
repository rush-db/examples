# Real-time Stream Processing with Graph-Backed Vector Updates

This project demonstrates a working implementation of a stream processor that mutates a RushDB graph and automatically updates associated vectors.

## What It Demonstrates

1. **Schema Setup**: Define a RushDB schema with vector-enabled node properties
2. **Stream Processor**: Simulates consuming events from a stream and writing graph mutations
3. **Vector Sync Mechanism**: Automatic vector updates triggered by graph changes
4. **Combined Query**: Graph traversal → vector similarity filter → results
5. **Benchmarking**: Latency measurement for updates and queries under load

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Stream Events  │───▶│ Stream Processor │───▶│   RushDB Graph  │
│  (simulated)    │    │  + Vector Sync   │    │  + Vector Index │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                     │
                                                     ▼
                              ┌──────────────────────────────────┐
                              │  Graph Traversal + Vector Query  │
                              │  (combined search pattern)       │
                              └──────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- RushDB account (https://rushdb.com)
- API key from RushDB dashboard

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Generate Mock Data

```bash
# Generate and seed test data (100 articles, 50 authors, 500 events)
python seed.py
```

## Run the Demo

```bash
# Run the complete demonstration
python main.py
```

Expected output:
- Schema creation confirmation
- Stream processing simulation (100 events)
- Vector index statistics
- Latency benchmarks (update and query)
- Combined graph + vector query results

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── seed.py              # Mock data generation script
└── main.py              # Main demonstration
```

## Benchmark Results Interpretation

| Metric | Description |
|--------|-------------|
| **Update Latency** | Time to ingest event + update graph + sync vector |
| **Query Latency** | Time to traverse graph + filter by vector similarity |
| **Throughput** | Events processed per second |

## Key Patterns

### Vector Sync Pattern
```python
# On graph mutation, automatically sync vectors
db.records.upsert(
    label="ARTICLE",
    data=article_data,
    options={"mergeBy": ["id"]},
    vectors=[{"propertyName": "content", "vector": embedding}]
)
```

### Combined Graph + Vector Query
```python
# First, traverse graph to get relevant context
authors = db.records.find({"labels": ["AUTHOR"], "where": {"domain": "tech"}})

# Then, filter by vector similarity
results = db.ai.search({
    "propertyName": "content",
    "queryVector": query_vector,
    "labels": ["ARTICLE"],
    "where": {"AUTHOR": {"$id": {"$in": [a.id for a in authors]}}},
    "limit": 5
})
```

## Troubleshooting

- **Authentication Error**: Ensure `RUSHDB_API_KEY` is set in `.env`
- **No Vector Index**: Run `seed.py` first to create indexes
- **Rate Limits**: The demo includes 0.1s delays between events; adjust as needed

## See Also

- [RushDB Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [Vector Search Guide](https://docs.rushdb.com/features/vector-search)
