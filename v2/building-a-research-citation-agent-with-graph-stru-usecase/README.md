# Building a Research Citation Agent with Graph-Structured References

This project demonstrates how to build a research citation agent using RushDB's unique dual-layer architecture: **graph traversal** for citation relationships and **vector similarity** for semantic discovery.

## The Problem

Research paper discovery has two complementary needs:

1. **Citation relationships** — "What papers does Paper X cite?" and "What papers cite Paper X?"
2. **Semantic similarity** — "What papers are conceptually related to this one, even without direct citation links?"

Most tools pick one. RushDB handles both natively in one store.

## What This Demo Shows

- **Schema design** — Papers as nodes, citation links as directed edges
- **Vector embedding** — Embedding paper abstracts using sentence-transformers
- **Semantic search** — Finding conceptually related papers regardless of citation
- **Graph traversal** — Following citation chains (papers that cite papers that cite X)
- **Co-citation analysis** — Discovering paper clusters via shared citations
- **Hybrid queries** — Combining graph traversal with vector filtering

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RushDB                                 │
│  ┌─────────────────┐    ┌──────────────────────────────┐  │
│  │   Graph Layer   │    │      Vector Index Layer      │  │
│  │                 │    │                              │  │
│  │  [Paper A] ───CITES──▶ [Paper B]                    │  │
│  │       │                 │                           │  │
│  │       │                 ▼                           │  │
│  │       │          [Paper C]                         │  │
│  │       │                 │                           │  │
│  │       ▼                 ▼                           │  │
│  │  [Paper D] ◀──CITES── [Paper E]                    │  │
│  │                 │                                     │  │
│  │  Traversal:    │  Similarity:                        │  │
│  │  find papers   │  embed(abstract) → vector search    │  │
│  │  N hops away   │  find conceptually similar         │  │
│  └─────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account ([get one free](https://app.rushdb.com))
- `sentence-transformers` for embedding generation

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_TOKEN

# Seed the database with sample papers
python seed.py

# Run the demonstration
python main.py
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── data/
│   └── papers.json     # Sample research papers with citations
├── seed.py             # Load papers and citations into RushDB
└── main.py             # Interactive demo of all features
```

## Output Examples

### Semantic Search
```
Searching for papers similar to: "attention mechanisms in neural networks"
────────────────────────────────────────────────────────────────────
[0.847] Transformer Attention Is All You Need (Vaswani et al.)
[0.812] Self-Attention and Long Dependencies (Huang et al.)
[0.789] Efficient Attention for Vision (Huang et al.)
```

### Citation Chain Traversal
```
Papers 2 hops away from "Attention Is All You Need":
────────────────────────────────────────────────────────────────────
BERT (Devlin et al.) - Cited by: Efficient Attention
GPT-3 (Brown et al.) - Cited by: BERT
Longformer (Beltagy et al.) - Cited by: Efficient Attention
```

### Co-Citation Analysis
```
Papers frequently cited together (co-citation clusters):
────────────────────────────────────────────────────────────────────
Cluster: Neural Architecture
  - Attention Is All You Need (cited 3 times with others)
  - BERT (cited 3 times with others)
  - GPT-3 (cited 2 times with others)
```

## Key Design Decisions

### Why `sentence-transformers`?
- Pre-trained on semantic similarity tasks
- Produces high-quality 384-dimensional embeddings
- Fast inference, no API calls needed
- Ideal for academic text (scientific phrasing, technical terms)

### Why Inline Vector Writes?
Using `vectors=[{"propertyName": "abstract", "vector": [...]}]` on `db.records.create()` keeps the paper and its embedding together in one write operation.

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Knowledge Graph Use Cases](https://docs.rushdb.com/use-cases/knowledge-graphs)
- [Vector Search in RushDB](https://docs.rushdb.com/features/ai-vector-search)

---

View on GitHub: https://github.com/rush-db/examples/tree/main/building-a-research-citation-agent-with-graph-stru-usecase
