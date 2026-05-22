# RushDB Tutorial: Hybrid Vector + Graph Retrieval System

A production-ready demonstration of building a hybrid retrieval system with RushDB — combining semantic vector search with graph relationship traversal in under 100 lines of core logic.

## What This Project Demonstrates

- **Schema Design**: Define a unified data model supporting both vector embeddings and typed graph relationships
- **Data Ingestion**: Import structured knowledge with pre-computed embeddings, establishing entity nodes and connections
- **Hybrid Queries**: Execute combined vector similarity + graph traversal queries in a single, coherent API
- **Performance Benchmark**: Compare RushDB's unified approach against naive sequential calls (PostgreSQL + vector DB)
- **Production Readiness**: Clean architecture with single client, zero gymnastics

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      RushDB Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Neo4j     │  │   Vector    │  │   Relationship      │ │
│  │  (storage)  │  │   Index     │  │   Graph Engine      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────────┐
│                   Python SDK (rushdb)                       │
│   • Semantic search    • Graph traversal    • Transactions  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account and API key ([Sign up](https://rushdb.com) — Free tier available)
- `sentence-transformers` for generating embeddings

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

3. **Generate seed data** (optional — script detects existing data):
```bash
python seed.py
```

4. **Run the main demo**:
```bash
python main.py
```

## Project Structure

```
rushdb-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Data generation script
└── main.py            # Core demonstration
```

## Expected Output

The demo will show:
1. **Setup Phase**: Creating vector index and checking system status
2. **Hybrid Search**: Finding semantically similar articles, then traversing to authors and related topics
3. **Benchmark Results**: Comparing RushDB's latency against naive approach

Example benchmark output:
```
=== Hybrid Query Benchmark ===
RushDB (unified):      45ms
Naive (PG + Vec):      312ms
Speedup:               ~7x faster
```

## Use Cases

This pattern is ideal for:

| Use Case | Vector Query | Graph Traversal |
|----------|-------------|-----------------|
| **RAG Systems** | Find relevant document chunks | Follow knowledge graph to context |
| **Recommendation** | Similar items by embedding | Friends who bought X also bought Y |
| **Knowledge Graph** | Semantic entity search | Traverse relationships for reasoning |
| **Content Discovery** | Find similar articles | Explore author/topic connections |

## Documentation

- [RushDB SDK Reference](https://docs.rushdb.com)
- [Vector Search Guide](https://docs.rushdb.com/features/vector-search)
- [Graph Relationships](https://docs.rushdb.com/features/relationships)

## License

MIT — Use freely in personal and commercial projects.
