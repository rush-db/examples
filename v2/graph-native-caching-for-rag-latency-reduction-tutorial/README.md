# Graph-Native Caching for RAG Latency Reduction

This tutorial demonstrates how to use RushDB's graph-native architecture to implement efficient caching for Retrieval Augmented Generation (RAG) systems, dramatically reducing query latency by leveraging relationship-aware context retrieval.

## Overview

Traditional RAG implementations suffer from repeated vector computations and lack of contextual awareness. By modeling your knowledge graph with explicit relationships, you can:

1. **Cache pre-computed embeddings** — Store vectors once, reuse across queries
2. **Model contextual relationships** — Parent-child chunks, topic clusters, temporal sequences
3. **Traverse related context** — Fetch related documents without redundant searches
4. **Reduce embedding generation costs** — RushDB's free reads mean cached results are instant

## Key Concepts Demonstrated

- **Semantic chunk caching** — Store document chunks with pre-computed vectors
- **Relationship-based context** — Link chunks to documents, topics, and related content
- **Graph-native retrieval** — Traverse relationships for context enrichment
- **Cache hit optimization** — Track and measure cache effectiveness
- **RAG context assembly** — Build context strings from graph traversals

## Prerequisites

- Python 3.9+
- RushDB account (Free tier works)
- `rushdb>=2.0.0` Python package
- Sentence Transformers for embeddings (or use external embeddings)

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

3. **Get your API key:**
   - Sign up at https://rushdb.com
   - Create a project and copy the API key

4. **Seed the database (optional — creates sample documents):**
```bash
python seed.py
```

## Running the Tutorial

```bash
python main.py
```

The script will:

1. Create a document and chunk index
2. Seed sample documents about technical topics
3. Demonstrate semantic search with cache simulation
4. Show graph traversal for context enrichment
5. Compare cached vs non-cached retrieval times

## Project Structure

```
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Generates sample documents
└── main.py            # Main demonstration script
```

## How It Works

### 1. Document Modeling

Documents are modeled as a graph:

```
DOCUMENT ──CONTAINS──> CHUNK ──RELATED_TO──> CHUNK
    │                     │
    └──HAS_TOPIC──> TOPIC
```

### 2. Caching Strategy

- **Vector cache** — Embeddings stored inline with records
- **Context cache** — Related records pre-linked via relationships
- **Query cache** — Track frequently accessed document combinations

### 3. Retrieval Flow

```
Query → Semantic Search → Find CHUNKs →
  → Traverse RELATES_TO → Fetch related chunks
  → Assemble context → Return to LLM
```

## Expected Output

```
=== Graph-Native RAG Caching Demo ===

[1] Creating indexes for DOCUMENT and CHUNK labels...
[2] Seeding sample documents (skipping if data exists)...
[3] Demonstrating semantic search with cache...
[4] Graph traversal for context enrichment...
[5] Performance comparison: cached vs fresh retrieval...

Cache Performance Summary:
- Total queries: 15
- Cache hits: 12 (80%)
- Avg latency cached: 2.3ms
- Avg latency fresh: 145.6ms
- Speed improvement: 63x
```

## Cost Efficiency

RushDB's pricing model makes caching particularly cost-effective:

| Operation | KU Cost | Notes |
|-----------|---------|-------|
| Semantic search | 5 KU | Server-side embedding |
| Read operations | **Free** | Cached results cost nothing |
| Record creation | 0.5 KU + 1 KU/property | One-time cache write |

By caching frequently accessed context, you pay KU only once per write, then serve reads for free.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Vector Search Guide](https://docs.rushdb.com/features/vector-search)
- [Property Graph Modeling](https://docs.rushdb.com/core-concepts/properties)

## Troubleshooting

**"Index not found" errors:**
- The script auto-creates indexes on first run
- Ensure your API key has sufficient permissions

**Slow initial run:**
- First run creates indexes and seeds data
- Subsequent runs use cached data and are much faster

**Embedding model errors:**
- Check that `sentence-transformers` is installed
- The script uses `all-MiniLM-L6-v2` (384 dimensions)
- If using external embeddings, update `EMBEDDING_SOURCE=external` in .env
