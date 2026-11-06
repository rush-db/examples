# Zero-to-Knowledge-Graph: Ingesting Unstructured Documents with RushDB

A step-by-step tutorial demonstrating RushDB's zero-config document ingestion and immediate relationship querying. Get hands-on with RushDB in under 5 minutes — no schema definitions, no Cypher queries, just working code.

## What You'll Learn

1. **Prerequisites & Setup** — Get your environment ready in minutes
2. **Zero-Config Ingestion** — Ingest JSON documents without defining schemas
3. **Auto-Normalization** — See how RushDB transforms nested JSON into a property graph
4. **Semantic Search** — Find similar content using vector similarity
5. **Graph Traversal** — Query entity relationships across documents
6. **Chunking & Reindexing** — Adjust document chunking strategy without rebuilding

## Prerequisites

- **Python 3.9+**
- **RushDB Account** — [Sign up free](https://rushdb.com) (no credit card required)
- **API Key** — Get from your RushDB dashboard

## Setup (Under 5 Minutes)

```bash
# 1. Clone or navigate to this directory
cd zero-to-knowledge-graph-ingesting-unstructured-doc-tutorial

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY

# 5. Run the tutorial
python main.py
```

## Expected Output

```
🚀 ZERO-TO-KNOWLEDGE-GRAPH TUTORIAL
==================================================

📋 STEP 1: Environment Check
--------------------------------------------------
✅ RushDB SDK Version: 2.x.x
✅ API Key configured: Yes
✅ Connected to workspace: demo-workspace

📊 STEP 2: Initial Graph State
--------------------------------------------------
  • Graph nodes: 0
  • Graph relationships: 0
  • Labels: []

📄 STEP 3: Zero-Config Document Ingestion
--------------------------------------------------
Ingesting documents with NO schema definition required...

  ✓ Created: Understanding Neural Networks... (id: 01HX...)
  ✓ Created: Introduction to Graph Databases... (id: 01HX...)
  ✓ Created: Machine Learning Best Practices... (id: 01HX...)
  ✓ Created: The Rise of Vector Databases... (id: 01HX...)
  ✓ Created: Graph Neural Networks Explained... (id: 01HX...)

📊 STEP 4: Auto-Normalization - Graph Structure
--------------------------------------------------
Graph Structure Created:

  ARTICLE "Understanding Neural Networks..."
    ├── [WRITTEN_BY] → AUTHOR "Dr. Sarah Chen"
    ├── [TAGGED_WITH] → TAG "machine-learning"
    ├── [TAGGED_WITH] → TAG "neural-networks"
    └── [HAS_SECTION] → SECTION "Introduction"

  ... (4 more articles with similar structure)

  Total Nodes: 28
  Total Relationships: 32

🔍 STEP 5: Semantic Search
--------------------------------------------------
Query: "deep learning architectures"

Results:
  1. [0.892] Understanding Neural Networks
      "Neural networks are computing systems inspired..."
  
  2. [0.867] Graph Neural Networks Explained
      "Graph Neural Networks (GNNs) extend..."
  
  3. [0.734] Machine Learning Best Practices
      "Successfully deploying ML models requires..."

🔗 STEP 6: Graph Traversal Queries
--------------------------------------------------
Query: Articles by "Dr. Sarah Chen"

  • Understanding Neural Networks (machine-learning, neural-networks)
  • Graph Neural Networks Explained (deep-learning, gnns)

Query: Articles with tag "machine-learning"

  • Understanding Neural Networks
  • Machine Learning Best Practices

📦 STEP 7: Chunking Strategy & Reindexing
--------------------------------------------------
Current Index Stats:
  • Records indexed: 5 / 5

Reindexing with new chunking strategy (chunk_size=300, overlap=50)...

  Created 23 chunks from 5 documents
  Average chunks per document: 4.6

New Index Stats:
  • Records indexed: 28 / 28 (articles + chunks)

✨ TUTORIAL COMPLETE
==================================================
```

## Project Structure

```
zero-to-knowledge-graph-ingesting-unstructured-doc-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── main.py            # Main tutorial script
└── data/
    └── articles.json  # Sample knowledge base documents
```

## How It Works

### 1. Zero-Config Ingestion

RushDB ingests any JSON structure without schema definitions:

```sdk
db.records.create(label="ARTICLE", data={
    "title": "Understanding Neural Networks",
    "author": {"name": "Dr. Sarah Chen", "affiliation": "MIT"},
    "tags": ["machine-learning", "neural-networks"],
    "sections": [...]
})
___SPLIT___
await db.records.create({ label: 'ARTICLE', data: {
    title: 'Understanding Neural Networks',
    author: { name: 'Dr. Sarah Chen', affiliation: 'MIT' },
    tags: ['machine-learning', 'neural-networks'],
    sections: [...]
}})
```

### 2. Auto-Normalization

RushDB automatically transforms nested JSON into a property graph:

```
Nested JSON                          Property Graph
─────────────                        ─────────────
{                                    ARTICLE ──[WRITTEN_BY]──► AUTHOR
  "author": {                       ARTICLE ──[TAGGED_WITH]──► TAG
    "name": "Dr. Chen"              ARTICLE ──[HAS_SECTION]──► SECTION
  },
  "tags": ["ml", "ai"]             Each unique author/tag becomes
}                                    a separate node, shared across
                                     all articles that reference it
```

### 3. Semantic Search

Create a vector index and search by meaning:

```sdk
# Create index (server embeds automatically)
db.ai.indexes.create({"label": "ARTICLE", "propertyName": "content"})

# Search for semantically similar content
results = db.ai.search({
    "propertyName": "content",
    "query": "deep learning architectures",
    "labels": ["ARTICLE"],
    "limit": 5
})
___SPLIT___
// Create index (server embeds automatically)
await db.ai.indexes.create({ label: 'ARTICLE', propertyName: 'content' })

// Search for semantically similar content
const results = await db.ai.search({
    propertyName: 'content',
    query: 'deep learning architectures',
    labels: ['ARTICLE'],
    limit: 5
})
```

### 4. Graph Traversal

Query relationships across the graph:

```sdk
# Find articles by a specific author
db.records.find({
    "labels": ["ARTICLE"],
    "where": {
        "AUTHOR": {"$relation": {"type": "WRITTEN_BY", "direction": "out"}},
        "name": "Dr. Sarah Chen"
    }
})
___SPLIT___
// Find articles by a specific author
await db.records.find({
    labels: ['ARTICLE'],
    where: {
        AUTHOR: {
            $relation: { type: 'WRITTEN_BY', direction: 'out' },
            name: 'Dr. Sarah Chen'
        }
    }
})
```

## Cleaning Up

To remove all tutorial data:

```python
# In main.py, uncomment the cleanup section at the bottom
# or run:
python -c "from rushdb import RushDB; db = RushDB(); db.records.delete({'labels': ['ARTICLE']})"
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [Property Graph Model](https://docs.rushdb.com/concepts/property-graph)
- [Vector Search](https://docs.rushdb.com/features/vector-search)

## License

MIT — Use freely for learning and experimentation.
