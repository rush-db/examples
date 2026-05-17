# Batch Processing Patterns for Bulk Node Ingestion

A practical tutorial demonstrating efficient batch processing strategies for ingesting large volumes of nodes into RushDB using the Python SDK.

## What This Tutorial Demonstrates

- **Chunked batch creation** — Processing large datasets in configurable chunks
- **Bulk upsert patterns** — Idempotent create-or-update with merge keys
- **Transaction batching** — Atomic batch operations with rollback support
- **Progress tracking** — Real-time ingestion progress monitoring
- **Error handling** — Graceful failure recovery and retry logic
- **Performance optimization** — Tuning batch sizes for throughput

## Prerequisites

- Python 3.9+
- RushDB account with API key ([get one free](https://app.rushdb.com))
- `rushdb>=2.0.0` Python package

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Tutorial

```bash
# Generate mock dataset (creates 1000 product records)
python seed.py

# Run all batch processing patterns
python main.py
```

## Project Structure

```
├── main.py           # Main tutorial demonstrating batch patterns
├── seed.py           # Mock data generator for 1000 products
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── README.md         # This file
```

## Expected Output

The tutorial runs four batch processing scenarios:

1. **Basic Batch Creation** — Creates 100 records via `create_many()`
2. **Chunked Processing** — Streams 1000 records in chunks of 50
3. **Transaction Batching** — Commits 100 records atomically with rollback
4. **Bulk Upsert** — Upserts 100 records with conflict resolution

Each pattern prints execution time, throughput (records/sec), and status.

## Key Concepts

### Batch Size Tuning

| Dataset Size | Recommended Chunk Size | Rationale |
|--------------|------------------------|----------|
| < 1,000      | 100-200                | Single batch optimal |
| 1,000-10,000  | 50-100                 | Balance memory/throughput |
| 10,000-100K  | 25-50                  | Avoid network timeouts |
| > 100K       | 10-25                  | Preserve stability under load |

### KU Cost Estimation

For budget planning, estimate:
- **0.5 KU** per record created
- **1 KU** per property stored
- **0.25 KU** per relationship

A 100-record batch with 10 properties each ≈ 1,050 KU (writes only; reads are free).

## References

- [RushDB Python SDK Documentation](https://docs.rushdb.com/sdk/python/)
- [Batch Operations Guide](https://docs.rushdb.com/guides/batch-operations/)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/batch-processing-patterns-for-bulk-node-ingestion-tutorial)
