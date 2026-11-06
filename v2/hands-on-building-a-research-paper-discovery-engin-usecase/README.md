# Research Paper Discovery Engine with RushDB

A hands-on demonstration of RushDB's combined graph and vector capabilities, building a research paper discovery engine that leverages both citation networks (graph) and semantic relevance (vectors).

## What This Demonstrates

This project showcases why RushDB is ideal for knowledge-intensive applications:

- **Graph traversal** — Navigate citation networks to find related work via citation chains
- **Semantic search** — Index paper abstracts with vectors to find conceptually related papers
- **Hybrid retrieval** — Combine graph and vector capabilities for intelligent paper discovery
- **"More like this"** — A unified endpoint returning both cited-by relations and semantically similar papers

## Why RushDB?

Traditional stacks require:
1. A graph database (Neo4j) for citation relationships
2. A vector database (Pinecone/Qdrant) for semantic search
3. Application-level orchestration to stitch them together

RushDB provides both capabilities natively, eliminating:
- **Latency** from multi-database round-trips
- **Consistency issues** from keeping two systems in sync
- **Operational overhead** of managing separate infrastructure

## Architecture

```
Papers (nodes) ────── CITES ──────> Papers (nodes)
     │                                        │
     └── Abstract (vector indexed)            └── Abstract (vector indexed)
              │                                        │
              └────── Semantic Search ─────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://rushdb.com))
- `sentence-transformers` for generating embeddings (local, no API key needed)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your RushDB credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
RUSHDB_TOKEN=your_api_key_here
```

Find your API key at [rushdb.com/settings](https://rushdb.com/settings).

### 3. Seed the Database

The seed script generates ~50 research papers with realistic metadata and citation relationships. It uses `sentence-transformers` (all-MiniLM-L6-v2) to generate embeddings locally.

```bash
python seed.py
```

**What the seed script does:**
- Creates papers across ML/AI research domains (NLP, Computer Vision, Reinforcement Learning, etc.)
- Establishes realistic citation relationships (newer papers cite foundational work)
- Generates abstract embeddings using a local transformer model
- Creates a vector index on the `abstract` property
- Prints progress every 10 papers

The script is **idempotent** — running it twice is safe. It checks for existing data before creating new records.

### 4. Run the Demo

```bash
python main.py
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generate and import mock research paper data
└── main.py             # Discovery engine demonstration
```

## Expected Output

The demo runs four scenarios:

1. **Citation Network Discovery** — Find all papers cited by and citing a specific paper
2. **Semantic Search** — Find papers conceptually related to a research interest
3. **Combined Discovery** — Filter recent papers via graph, rerank by semantic similarity
4. **"More Like This"** — Unified endpoint showing both citation relations and semantic similarity

## Embedding Model

We use `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions):
- Fast, lightweight model
- Excellent for sentence-level similarity
- Runs entirely locally — no API calls needed
- Industry standard for academic/scientific text similarity

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [Vector Search in RushDB](https://docs.rushdb.com/features/vector-search)
- [Graph Relationships in RushDB](https://docs.rushdb.com/features/graph-relationships)

## License

MIT — use freely for learning and building.
