# Applying PageRank-Style Scoring to Order Retrieved Context

## Overview

This project demonstrates how to use **PageRank-style relevance propagation** to improve RAG context quality. Graph edges carry topical signal that cosine similarity alone misses, fixing semantic false positives and surfacing truly authoritative chunks.

## The Problem with Pure Similarity Search

Vector similarity search returns chunks that are *individually* similar to the query. But in a document corpus, the most relevant information might exist in a chunk with moderate similarity — if that chunk is cited by, elaborates on, or shares authorship with highly relevant chunks. Pure similarity ordering misses this *authority structure*.

## The Solution: Iterative Relevance Propagation

Inspired by PageRank, we:

1. **Seed**: Start with high-similarity chunks as initial authority scores
2. **Propagate**: Scores flow through graph edges (citations, shared authors, topic overlap)
3. **Iterate**: Reweight until convergence
4. **Rank**: Order chunks by final authority scores

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Document Corpus                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Doc A    │──│ Doc B    │──│ Doc C    │──│ Doc D    │    │
│  │ (vector) │  │ (vector) │  │ (vector) │  │ (vector) │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│        │              │              │              │       │
│        └──────────────┴──────────────┴──────────────┘       │
│                         Graph Edges                          │
│           (CITES, SHARES_AUTHOR, SHARES_TOPIC)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Iterative Relevance Propagation                │
│                                                             │
│   Chunk A (0.9 sim) ──┬──► Chunk B (propagated: 0.72)      │
│                       │                                     │
│   Chunk C (0.6 sim)───┼──► Chunk D (propagated: 0.45)      │
│                       │                                     │
│   Chunk E (0.4 sim)───┴──► Chunk F (propagated: 0.31)      │
│                                                             │
│   Final Rank: A > B > C > D > E > F                        │
└─────────────────────────────────────────────────────────────┘
```

## Setup

### Prerequisites

- Python 3.10+
- A RushDB account (Free tier works)

### Installation

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd applying-pagerank-style-scoring-to-order-retrieved-usecase

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

### Environment Variables

Create a `.env` file with:

```
RUSHDB_API_TOKEN=your_api_token_here
```

Get your API token from [RushDB Dashboard](https://app.rushdb.com).

## Running

### Step 1: Seed the Database

```bash
python seed.py
```

This creates:
- 30 articles across 5 tech topics (AI/ML, Web Dev, Security, Cloud, Data Engineering)
- ~90 chunks (3-5 per article)
- Graph edges: citations, shared authors, shared topics
- Vector embeddings for semantic search

### Step 2: Run the Demo

```bash
python main.py
```

## Expected Output

The demo queries **"How do transformers work in large language models?"** and compares:

1. **Naive Ordering**: Pure cosine similarity scores
2. **Propagation-Scored Ordering**: Authority scores after iterative propagation

You'll see how the propagation step:
- Fixes semantic false positives (chunks about ML that don't discuss transformers)
- Elevates authoritative chunks that are well-connected to highly-relevant content

## Project Structure

```
applying-pagerank-style-scoring-to-order-retrieved-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Data ingestion script
└── main.py             # PageRank scoring demonstration
```

## Key Code Patterns

### Creating Records with Vectors

```sdk
db.records.create(
    label="CHUNK",
    data={"text": chunk_text, "source": article_title},
    vectors=[{"propertyName": "text", "vector": embedding}]
)
___SPLIT___
// TypeScript equivalent pattern
await db.records.create({
    label: 'CHUNK',
    data: { text: chunkText, source: articleTitle },
    vectors: [{ propertyName: 'text', vector: embedding }]
})
```

### Attaching Graph Edges

```sdk
db.records.attach(
    source=chunk_a,
    target=chunk_b,
    options={"type": "CITES"}
)
```

### Semantic Search (Seed for Propagation)

```sdk
results = db.ai.search({
    "propertyName": "text",
    "query": "transformer architecture attention mechanism",
    "labels": ["CHUNK"],
    "limit": 20
})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub](https://github.com/rush-db/examples)
- [Property Graph Fundamentals in RushDB](https://docs.rushdb.com)
