# Handling 10M+ Nodes: Scalability Patterns for RushDB Deployments

This tutorial demonstrates production-grade scalability patterns for RushDB when dealing with large-scale graph data (millions of nodes and relationships).

## What This Tutorial Covers

- **Batch Operations**: Efficient bulk creation and relationship linking
- **Pagination Patterns**: Memory-safe traversal of large result sets
- **Index Management**: Vector and property indexes for query performance
- **Transaction Batching**: ACID-compliant grouped writes
- **Concurrent Processing**: Thread pool patterns for parallel operations
- **Query Optimization**: Field projection and filtered searches

## Prerequisites

- Python 3.10+
- RushDB account (free tier available at https://rushdb.com)
- Neo4j-backed RushDB workspace

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

3. **Generate mock data** (optional - skips if data already exists):
   ```bash
   python seed.py
   ```

## How to Run

```bash
python main.py
```

The script will:
1. Initialize the RushDB connection
2. Seed mock data (products, brands, categories)
3. Demonstrate each scalability pattern in sequence
4. Print results and performance metrics

## Project Structure

```
handling-10m-nodes-scalability-patterns-for-rushdb-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Mock data generator
└── main.py            # Scalability patterns demonstration
```

## Key Patterns Demonstrated

### 1. Batch Creation (vs. Single Record)
```sdk
# ❌ Inefficient: N individual API calls
for product in products:
    db.records.create(label="PRODUCT", data=product)

# ✅ Efficient: Single batch API call
db.records.create_many(label="PRODUCT", data=products)
```

### 2. Pagination with Cursor-Based Navigation
```sdk
# Process 10M records in 1000-record chunks
offset = 0
BATCH_SIZE = 1000
while True:
    results = db.records.find({
        "labels": ["PRODUCT"],
        "skip": offset,
        "limit": BATCH_SIZE
    })
    if not results.data:
        break
    process_batch(results.data)
    offset += BATCH_SIZE
```

### 3. Transaction Batching
```sdk
with db.transactions.begin() as tx:
    for i in range(1000):
        db.records.create(label="PRODUCT", data={...}, transaction=tx)
    # Auto-commits on success, auto-rollbacks on exception
```

### 4. Query Projection (Reduce Data Transfer)
```sdk
# Only fetch needed fields, not full records
db.records.find({
    "labels": ["PRODUCT"],
    "select": ["name", "price", "brandId"],
    "limit": 100
})
```

### 5. Vector Index for Similarity Search at Scale
```sdk
# Pre-compute embeddings and store in index
index = db.ai.indexes.create({
    "label": "PRODUCT",
    "propertyName": "description",
    "sourceType": "external",
    "dimensions": 768
})

# Batch upsert vectors
db.ai.indexes.upsert_vectors(index_id, {
    "items": [{"recordId": r.id, "vector": r.embedding} for r in records]
})
```

## Performance Notes

| Pattern | Impact | Recommendation |
|---------|--------|----------------|
| `create_many` | 10-50x faster | Always batch when possible |
| Field projection | 3-10x less data | Always `select` specific fields |
| Vector index | O(log n) search | Create before bulk import |
| Transaction batching | Reduces API overhead | Group 100-1000 ops per tx |
| Connection pooling | 5-20x throughput | Use threaded patterns |

## Resources

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/handling-10m-nodes-scalability-patterns-for-rushdb-tutorial)
- [RushDB Pricing](https://rushdb.com/pricing)
