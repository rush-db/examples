# Hands-on: Building a Research Paper Discovery Engine with RushDB

A step-by-step tutorial demonstrating how to combine **graph traversal** and **vector similarity search** in a unified system — something that would traditionally require two separate databases.

## What You'll Build

A discovery engine for research papers that can answer questions like:

1. **"Which papers cite the seminal work on attention mechanisms, directly or indirectly?"** — Graph traversal (citation depth)
2. **"Find papers semantically similar to this abstract about transformers."** — Vector similarity search
3. **"Which semantically similar papers are cited by papers in the neural architecture citation subtree?"** — The best of both worlds

## Prerequisites

- Python 3.9+\n- A RushDB account ([sign up free](https://rushdb.com))
- `sentence-transformers` for generating embeddings (CPU-friendly model)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your RushDB API key:

```
RUSHDB_API_KEY=your_api_key_here
```

Find your API key at [rushdb.com/settings](https://rushdb.com/settings).

### 3. Generate and Ingest Data

The `seed.py` script generates 50 mock research papers with:
- Realistic ML/AI titles and abstracts
- Citation relationships forming a graph structure
- Pre-computed embeddings for each abstract

```bash
python seed.py
```

This is **idempotent** — safe to run multiple times. It checks for existing data and skips re-ingestion.

## Running the Tutorial

```bash
python main.py
```

The script demonstrates:

1. **Schema Setup** — Creating the Paper label with metadata fields
2. **Data Ingestion** — Creating records with inline vector embeddings
3. **Citation Depth Query** — Find papers 2-3 hops from a seminal paper
4. **Semantic Similarity Query** — Vector search for papers similar to a query
5. **Combined Query** — Semantically similar papers within a citation subtree

## Expected Output

```
=== Tutorial: Research Paper Discovery Engine ===

[1] Papers ingested: 50
[2] Citation relationships created: ~150
[3] Vector index ready for search

--- Query 1: Citation Depth ---
Papers 2-3 hops away from 'Attention Is All You Need':
  - "Scaling Laws for Neural Language Models" (3 hops)
  - "Layer Normalization" (2 hops)

--- Query 2: Semantic Similarity ---
Papers similar to "transformer architecture attention mechanism":
  [0.923] "Attention Is All You Need"
  [0.891] "BERT: Pre-training of Deep Bidirectional Transformers"
  [0.867] "The Illustrated Transformer"

--- Query 3: Combined Query ---
Semantically similar papers within the NLP citation subtree:
  [0.912] "GPT-3: Language Models are Few-Shot Learners"
  [0.889] "T5: Text-to-Text Transfer Transformer"
```

## Architecture

This project demonstrates RushDB's dual-layer storage:

| Capability | RushDB Component |
|------------|------------------|
| Paper metadata storage | Neo4j nodes |
| Citation graph traversal | Neo4j relationships |
| Semantic search | Neo4j vector index |
| Unified queries | Single SDK |

## Why This Approach?

Traditional systems would require:
- A **graph database** (Neo4j) for citation traversal
- A **vector database** (Pinecone, Weaviate) for semantic search
- Complex synchronization between systems

RushDB provides both capabilities in a single API, enabling queries like "find papers similar to X that cite papers that cite Y" — impossible to express in either system alone.

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)
- [Vector Search Guide](https://docs.rushdb.com/guides/vector-search)
- [Graph Relationships Guide](https://docs.rushdb.com/guides/relationships)
