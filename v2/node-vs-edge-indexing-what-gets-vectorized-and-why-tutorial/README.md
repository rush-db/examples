# Node vs Edge Indexing: What Gets Vectorized and Why It Matters

A deep-dive tutorial demonstrating how RushDB handles vectorization differently for **nodes** vs **edges**, and when to use each approach.

## What This Tutorial Covers

| Concept | Description |
|---------|-------------|
| **Node vectorization** | Creating embeddings from node properties (e.g., document content, article body) |
| **Edge vectorization** | Creating embeddings from relationship properties (e.g., citation excerpts, comment text) |
| **Storage implications** | How vectors are indexed and stored for each entity type |
| **Search patterns** | When to search across nodes vs traverse edges with embedded context |

## Why This Matters

When building AI-powered applications, you often need semantic search across different types of content:

- **Node search**: "Find documents similar to this query" — search across document bodies
- **Edge search**: "Find relevant citations within document relationships" — search across citation excerpts

RushDB lets you index both nodes AND edges, enabling powerful graph-aware semantic search patterns.

## Prerequisites

- Python 3.9+
- RushDB account (free tier works)
- API key from https://app.rushdb.com

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API_KEY and optional self-hosted URL
```

## Running the Tutorial

```bash
# Generate sample data (idempotent — safe to run multiple times)
python seed.py

# Run the main tutorial demonstrating node vs edge indexing
python main.py
```

## Expected Output

The tutorial will:
1. Create a knowledge graph with papers, authors, and citation relationships
2. Create a vector index on node property `Document.content`
3. Create a vector index on edge property `CITES.excerpt`
4. Perform semantic search on nodes (find similar papers by content)
5. Perform semantic search on edges (find relevant citations by excerpt similarity)
6. Show how combining both enables powerful hybrid search

## Project Structure

```
node-vs-edge-indexing-what-gets-vectorized-and-why-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generates mock research papers and citations
└── main.py             # Tutorial demonstrating node vs edge vectorization
```

## Key Concepts Demonstrated

### Node Indexing

Nodes store content directly. Indexing a node property creates an embedding for each record:

```sdk
# Create a vector index on a node property
index = db.ai.indexes.create({
    "label": "Document",
    "propertyName": "content"
})
___SPLIT___
// TypeScript
const index = await db.ai.indexes.create({
  label: 'Document',
  propertyName: 'content'
})
```

### Edge Indexing

Relationships can also have properties with vector embeddings. This enables searching within the graph structure:

```sdk
# Create a vector index on an edge property
index = db.ai.indexes.create({
    "label": "CITES",
    "propertyName": "excerpt"
})
___SPLIT___
// TypeScript
const index = await db.ai.indexes.create({
  label: 'CITES',
  propertyName: 'excerpt'
})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Vector Search Guide](https://docs.rushdb.com/features/vector-search)
- [Graph Relationships](https://docs.rushdb.com/features/relationships)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/node-vs-edge-indexing-what-gets-vectorized-and-why-tutorial)
