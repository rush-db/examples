# Handling Concurrent Reads and Writes in Graph-Augmented RAG

A collaborative research assistant that maintains a shared knowledge graph with live embedding updates — demonstrating why graph-augmented RAG needs first-class concurrency support.

## What This Demonstrates

This project simulates a multi-user research environment where:

1. **Concurrent Writes**: Multiple researchers simultaneously create and update documents
2. **Live Vector Embeddings**: Every document update triggers a re-embedding for semantic search
3. **Consistent Reads**: RushDB's co-located graph+vector storage ensures reads see the latest state
4. **Workload Tradeoffs**: The code benchmarks write-heavy vs read-heavy scenarios

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Research Assistant                        │
├─────────────────────────────────────────────────────────────┤
│  Researcher A ──┐                                           │
│  Researcher B ──┼──▶ Concurrent Write Stream ──▶ RushDB     │
│  Researcher C ──┘                      │                    │
│                                         ▼                    │
│  Graph Layer ◄──────────────────── Neo4j                    │
│                                         │                    │
│  Vector Layer ◄────────────────────────┘                    │
│                                         │                    │
│  Semantic Search ──────────────────────▶ Current Embeddings  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account ([get one free](https://rushdb.com))
- `sentence-transformers` for embeddings (all-MiniLM-L6-v2, 384 dimensions)

## Setup

1. **Clone and install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Generate seed data**:
   ```bash
   python seed.py
   ```
   This creates:
   - 3 sample research projects
   - 15 research documents across topics (AI, blockchain, quantum computing)
   - Relationships between researchers, projects, and documents

## Running the Demo

```bash
python main.py
```

### What You'll See

The demo runs three sequential phases:

#### Phase 1: Concurrent Write Stream
- Spawns 5 simulated researchers, each making document edits
- All writes use transactions for atomicity
- Embeddings are updated inline with each write
- Demonstrates: write isolation, no data corruption

#### Phase 2: Consistent Read Verification
- While writes are happening in background, run semantic searches
- Shows that RushDB returns consistent results (no stale vectors)
- Confirms graph+vector co-location guarantees

#### Phase 3: Workload Benchmark
- **Write-heavy scenario**: 50 rapid updates, measure latency
- **Read-heavy scenario**: 100 concurrent searches, measure throughput
- Prints comparative metrics

## Expected Output

```
=== Phase 1: Concurrent Writes ===
[Researcher 1] Creating document: Neural Network Architectures
[Researcher 2] Creating document: Quantum Error Correction
[Researcher 1] Updating embeddings for document...
[Researcher 3] Creating document: DeFi Protocols
...
All 5 concurrent writes completed successfully ✓

=== Phase 2: Consistent Reads During Writes ===
Query: "machine learning optimization techniques"
  Found: [0.92] Optimizing Gradient Descent in Deep Networks
  Found: [0.87] Neural Architecture Search Methods
  Found: [0.81] Adaptive Learning Rate Algorithms
  Vector freshness verified: all embeddings < 2 seconds old ✓

=== Phase 3: Workload Benchmarks ===
Write-Heavy (50 updates):
  Total time: 3.24s
  Avg latency: 64.8ms
  Throughput: 15.4 writes/sec

Read-Heavy (100 searches):
  Total time: 1.87s
  Avg latency: 18.7ms
  Throughput: 53.5 searches/sec
```

## Key Design Decisions

### Why Transactions Matter for Graph + Vector Updates

When updating a document's content, you must update both:
1. The graph node (metadata, relationships)
2. The vector index (semantic embedding)

Using a transaction ensures these stay in sync. Without it:
- A read between write and embed update returns stale results
- Failed embeds leave orphaned state

### Inline Vector Writes vs Separate Index Updates

This project uses inline `vectors=` parameter on `create()`/`upsert()`:

```sdk
db.records.upsert(
    label="DOCUMENT",
    data={"title": "...", "content": "..."},
    options={"mergeBy": ["slug"]},
    vectors=[{"propertyName": "content", "vector": embedding}]
)
```

This is preferred over `db.ai.indexes.upsert_vectors()` for tutorial code because:
- Simpler, single-operation pattern
- Automatic transaction handling
- No manual index management

### Embedding Model Choice

We use **sentence-transformers/all-MiniLM-L6-v2** (384 dimensions):
- Fast inference (~10ms on CPU)
- High quality for research document retrieval
- Free, open-source (Apache 2.0)

## Files

| File | Purpose |
|------|---------|
| `seed.py` | Generates mock research documents and relationships |
| `main.py` | Main demo: concurrent writes, consistent reads, benchmarks |
| `utils.py` | Embedding helper, concurrent worker simulation |
| `requirements.txt` | Dependencies |
| `.env.example` | Environment variable template |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph-Augmented RAG Pattern](https://docs.rushdb.com/guides/graph-rag)
- [Transaction Semantics](https://docs.rushdb.com/api/transactions)

---

View on GitHub: https://github.com/rush-db/examples/tree/main/handling-concurrent-reads-and-writes-in-graph-augm-usecase
