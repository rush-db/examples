# Fine-tuning Retrieval Rankers Using Graph-Derived Signals

This tutorial demonstrates how to leverage RushDB's property graph structure to extract
meaningful signals for training and fine-tuning retrieval rankers. You'll learn how to
model document interactions, compute graph-based features, and use them as training
signals for a retrieval model.

## What You'll Learn

- **Graph-based signal extraction**: Derive features like co-occurrence patterns,
  user engagement graphs, and document similarity from RushDB's property graph
- **Training data construction**: Build labeled datasets from graph signals for
  supervised fine-tuning
- **Feature engineering**: Combine graph-derived features with content embeddings
- **Model training workflow**: End-to-end pipeline from graph to trained ranker

## Key Concepts

### Graph-Derived Signals

Graph-derived signals capture relational information that pure content similarity
misses:

| Signal | Description | Use Case |
|--------|-------------|----------|
| **Co-occurrence** | Documents accessed together | Collaborative filtering |
| **User engagement graph** | Click patterns by user | Implicit relevance judgments |
| **Document similarity graph** | Relationship strength between docs | Content reranking |
| **Query-document graph** | Query-session interactions | Session-aware retrieval |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RushDB                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Document   │  │    User     │  │    QueryInteraction    │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┼──────────────────────┘                │
│                          ▼                                       │
│              ┌─────────────────────┐                             │
│              │  Graph Relationships │                             │
│              │  CLICKED, VIEWED,    │                             │
│              │  QUERIED, SIMILAR    │                             │
│              └──────────┬──────────┘                             │
└────────────────────────┼────────────────────────────────────────┘
                         ▼
              ┌─────────────────────┐
              │  Signal Extraction  │
              │  - Co-occurrence    │
              │  - Centrality       │
              │  - Path features    │
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  Training Pipeline  │
              │  Fine-tune Ranker   │
              └─────────────────────┘
```

## Prerequisites

- Python 3.9+
- RushDB API key (get one at https://rushdb.com)
- `rushdb>=2.0.0`

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your RUSHDB_API_KEY
```

## Seed the Database

Run the seed script to create a realistic knowledge base with documents, users,
and interaction data:

```bash
python seed.py
```

This creates:
- 50 technology articles with embeddings
- 10 user profiles
- 200+ query-document interactions (views, clicks, ratings)

## Run the Tutorial

```bash
python main.py
```

Expected output:
1. **Graph signal extraction** — computed features from RushDB
2. **Training data preparation** — labeled pairs from graph signals
3. **Model fine-tuning** — training progress with validation metrics
4. **Evaluation** — ranker performance on held-out queries

## Project Structure

```
fine-tuning-retrieval-rankers-using-graph-derived--tutorial/
├── README.md
├── requirements.txt
├── .env.example
├── seed.py            # Generate mock knowledge base
└── main.py            # Core tutorial implementation
```

## How It Works

### 1. Data Modeling

We model documents, users, and interactions as RushDB records with relationships:

```sdk
# Create document
doc = db.records.create(
    label="DOCUMENT",
    data={"title": "Graph Neural Networks", "category": "ml", "content": "..."}
)

# Create user
user = db.records.create(label="USER", data={"user_id": "u123", "name": "Alice"})

# Record interaction
db.records.attach(
    source=user,
    target=doc,
    options={"type": "CLICKED", "properties": {"rating": 5, "timestamp": 1699900000}}
)
___SPLIT___
// TypeScript — demonstration only
const doc = await db.records.create({
    label: 'DOCUMENT',
    data: { title: 'Graph Neural Networks', category: 'ml', content: '...' }
})
```

### 2. Signal Extraction

From the graph, we extract training signals:

- **Positive signals**: Documents clicked/rated highly by users
- **Negative signals**: Documents viewed but not clicked, or low-rated
- **Graph proximity**: Documents related through multi-hop paths

### 3. Feature Construction

Each document-query pair gets graph-derived features:

- Co-occurrence score with positively labeled docs
- User engagement centrality in click graph
- Graph distance to relevant documents
- PageRank-style importance scores

### 4. Fine-tuning

We use a simple pointwise approach: given (query, document, graph_features),
predict the relevance score. The graph features supplement content embeddings,
allowing the ranker to learn patterns beyond pure semantic similarity.

## Customization

To adapt this for your use case:

1. **Extend the graph schema**: Add more relationship types (VIEWED, BOOKMARKED, SHARED)
2. **Add more signals**: Implement PageRank, community detection, or path-based features
3. **Scale the model**: Replace the simple MLP with a cross-encoder or transformer
4. **Use external embeddings**: Replace sentence-transformers with OpenAI/Cohere

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [Learning to Rank with Graph Signals](https://arxiv.org/abs/2103.14296)
- [Co-training for Retrieval](https://arxiv.org/abs/2004.12070)

---

View the full project at:
https://github.com/rush-db/examples/tree/main/fine-tuning-retrieval-rankers-using-graph-derived--tutorial
