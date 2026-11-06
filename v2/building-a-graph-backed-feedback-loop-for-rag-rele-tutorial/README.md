# Building a Graph-Backed Feedback Loop for RAG Relevance Tuning

## Overview

This project demonstrates how to build a **feedback loop for RAG relevance tuning** using RushDB's property graph capabilities. The feedback loop pattern helps you continuously improve retrieval quality by tracking which documents help answer which queries.

## What This Demonstrates

1. **Document Ingestion with Embeddings** — Store documents with their vector embeddings for semantic search
2. **Semantic Retrieval** — Query the vector index to find relevant documents
3. **Feedback Collection** — Record user feedback (helpful/not helpful) on retrieved documents
4. **Graph-Based Feedback Storage** — Link feedback to both documents and queries using relationships
5. **Feedback-Weighted Retrieval** — Use stored feedback to boost/highlight documents in future queries
6. **Traverse Feedback Patterns** — Query the graph to understand retrieval quality over time

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Feedback Loop                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  Query   │───▶│  Find    │───▶│  Return  │             │
│  │  Record  │    │  Vectors │    │  Results │             │
│  └─────┬────┘    └──────────┘    └────┬────┘             │
│        │                              │                    │
│        │         ┌───────────────────┘                    │
│        │         ▼                                        │
│        │    ┌──────────┐                                  │
│        │    │ Feedback │◀──── User Rates Results          │
│        │    │  Record  │                                  │
│        │    └────┬─────┘                                  │
│        │         │                                        │
│        └─────────┼────────────────────────────────────────┘
│                  │
│     ┌────────────┼────────────┐
│     ▼            ▼            ▼
│ ┌────────┐ ┌──────────┐ ┌──────────┐
│ │ QUERY  │ │ DOCUMENT │ │ DOCUMENT │
│ └────────┘ └────┬─────┘ └────┬─────┘
│                 │            │
│                 ▼            ▼
│          ┌──────────┐ ┌──────────┐
│          │ FEEDBACK │ │ FEEDBACK │
│          └──────────┘ └──────────┘
│                                                             │
│  Next query: Boost docs with positive feedback history      │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- RushDB account (free tier available at [rushdb.com](https://rushdb.com))
- `rushdb>=2.0.0` Python package

## Setup

### 1. Install Dependencies


```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### 3. Seed the Database

Run the seed script to populate initial document data:

```bash
python seed.py
```

This will create ~50 sample documents across multiple categories with pre-computed embeddings.

## Running the Demo

```bash
python main.py
```

The demo walks through the complete feedback loop:


1. **Ingest Documents** — Creates document records with embeddings
2. **Semantic Search** — Runs a query against the vector index
3. **Collect Feedback** — Simulates user feedback on retrieved results
4. **Store Feedback as Graph** — Creates linked feedback records
5. **Analyze Feedback** — Traverses the graph to understand patterns
6. **Boost Future Retrieval** — Uses feedback to weight results

## Key Code Patterns

### Creating Documents with Embeddings

```sdk
from rushdb import RushDB

db = RushDB("your-api-key")

# Create document with inline vector embedding
doc = db.records.create(
    label="DOCUMENT",
    data={
        "title": "Understanding RAG Systems",
        "content": "RAG combines retrieval with generation...",
        "category": "ai"
    },
    vectors=[{"propertyName": "content", "vector": [0.123, 0.456, ...]}]
)
```

### Storing Feedback as Graph Relationships

```sdk
# Link feedback to both query and document
with db.transactions.begin() as tx:
    feedback = db.records.create(
        label="FEEDBACK",
        data={"rating": "helpful", "query_text": query},
        transaction=tx
    )
    db.records.attach(source=feedback, target=doc, options={"type": "RATES"}, transaction=tx)
    db.records.attach(source=feedback, target=query_record, options={"type": "FOR_QUERY"}, transaction=tx)
```

### Querying Feedback Patterns

```sdk
# Find all documents rated helpful for a specific query
helpful_docs = db.records.find({
    "labels": ["DOCUMENT"],
    "where": {
        "FEEDBACK": {
            "$relation": {"type": "RATES", "direction": "in"},
            "rating": "helpful"
        }
    }
})
```

## Project Structure

```
building-a-graph-backed-feedback-loop-for-rag-rele-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variable template
├── seed.py           # Generates mock document data
└── main.py           # Main feedback loop demonstration
```

## Expected Output

```
=== RAG Feedback Loop Demo ===

[1/6] Creating sample documents...
  ✓ Created 50 documents with embeddings

[2/6] Running semantic search for 'machine learning optimization'...
  ✓ Found 5 relevant documents
     [0.892] The Future of ML Optimization Techniques
     [0.876] Advanced Deep Learning Strategies
     [0.854] Machine Learning Model Training Best Practices
     [0.823] Neural Network Optimization Methods
     [0.801] Gradient Descent and Backpropagation

[3/6] Simulating user feedback on results...
  ✓ Collected 5 feedback entries
     • Document 'The Future of ML Optimization Techniques': helpful ✓
     • Document 'Advanced Deep Learning Strategies': helpful ✓
     • Document 'Machine Learning Model Training Best Practices': helpful ✓
     • Document 'Neural Network Optimization Methods': helpful ✓
     • Document 'Gradient Descent and Backpropagation': helpful ✓

[4/6] Storing feedback as graph relationships...
  ✓ Created 5 FEEDBACK records with RATES and FOR_QUERY links

[5/6] Analyzing feedback patterns...
  ✓ Feedback pattern analysis:
     Total feedback: 5
     Helpful: 5 (100%)
     Not helpful: 0 (0%)

[6/6] Feedback-weighted retrieval...
  ✓ Documents with feedback history boosted
     [Boosted by +0.05] The Future of ML Optimization Techniques
     [Boosted by +0.05] Advanced Deep Learning Strategies
     [Boosted by +0.05] Machine Learning Model Training Best Practices
     [Boosted by +0.05] Neural Network Optimization Methods
     [Boosted by +0.05] Gradient Descent and Backpropagation

=== Demo Complete ===
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub](https://github.com/rush-db/examples)
- [RushDB Pricing](https://rushdb.com/pricing)
