# Handling Concurrent Reads and Writes in Graph-Augmented RAG

This tutorial demonstrates how to handle concurrent reads and writes in RushDB's graph+vector model for RAG (Retrieval-Augmented Generation) applications. It covers the edge cases that naive implementations miss.

## What This Tutorial Demonstrates

1. **Concurrent Write Streams** — Multiple writers simultaneously creating records with vectors
2. **Read-Your-Writes Consistency** — Ensuring writes are immediately visible on the same connection
3. **Vector Embedding Staleness** — Detecting and refreshing stale embeddings when graph entities change
4. **Retry with Exponential Backoff** — Handling transient conflicts gracefully
5. **End-to-End Concurrency** — Real-world multi-source write/read patterns

## Prerequisites

- Python 3.9+
- A RushDB account (free tier works)
- `sentence-transformers` for generating embeddings

## Setup

```bash
# Clone the repository
cd handling-concurrent-reads-and-writes-in-graph-augm-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API key
```

## Running the Tutorial

```bash
# First, seed the database with test data (creates 50 concurrent records)
python seed.py

# Run the main demonstration
python main.py
```

## Expected Output

```
=== Concurrent Writes Demo ===
✓ Writer A: Created Article(id=..., title="Microservices Architecture")
✓ Writer B: Created Article(id=..., title="Event Sourcing Pattern")
✓ Writer A: Created Article(id=..., title="GraphQL vs REST")
... (concurrent writes in progress)

=== Read-Your-Writes Consistency ===
✓ Read-after-write on same connection: Article found
✓ Transaction isolation verified: 3 articles visible

=== Vector Staleness Handling ===
✓ Detected stale embedding for Article(id=...)
✓ Refreshed embedding after content update

=== Retry with Backoff ===
✓ Conflict handled with backoff (attempt 1/3)
✓ Write succeeded after retry
```

## Project Structure

```
handling-concurrent-reads-and-writes-in-graph-augm-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py           # Data seeding script (50 concurrent records)
└── main.py           # Main demonstration script
```

## Key Concepts Explained

### Concurrent Write Streams

RushDB handles concurrent writes via optimistic locking. Each record has a version. When you update a record, if the version has changed since you read it, you get a conflict error. Use the `upsert` pattern with deterministic IDs to handle concurrent creates.

### Read-Your-Writes Consistency

Using the same RushDB connection, writes are immediately visible in subsequent reads. This is guaranteed because RushDB uses a single Neo4j instance and transactions provide ACID guarantees.

### Vector Embedding Staleness

When a record's content changes, its vector embedding becomes stale. The tutorial shows how to:
1. Detect that content has changed (version tracking)
2. Re-compute the embedding using sentence-transformers
3. Update the vector in the index

### Retry with Backoff

Network issues and transient conflicts are handled with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: Wait 100ms
- Attempt 3: Wait 200ms
- Attempt 4: Wait 400ms

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://github.com/rush-db/python-sdk)
- [Graph-Augmented RAG Tutorial](https://docs.rushdb.com/tutorials/graph-rag)

## License

MIT