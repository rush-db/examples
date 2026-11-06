# Custom Vectorizers and RushDB's Embedding Pipeline

This tutorial demonstrates how to use RushDB with **custom vectorizers** — your own embedding models — by leveraging RushDB's **external vector index** mode.

## What You'll Learn

- How to create an external vector index in RushDB
- How to generate embeddings using your own model (sentence-transformers)
- How to associate pre-computed vectors with records
- How to perform semantic search using your custom embeddings

## Why Custom Vectorizers?

RushDB offers **managed embeddings** (server-side, using OpenAI or similar) and **external embeddings** (you generate them). External mode gives you:

- **Full control** over the embedding model (domain-specific, multilingual, etc.)
- **Cost savings** by using open-source models (sentence-transformers, E5, BGE)
- **Privacy** — text never leaves your infrastructure
- **Consistency** — same model every time, no API versioning issues

## Prerequisites

- Python 3.10+
- A RushDB account ([sign up free](https://rushdb.com))
- `RUSHDB_API_KEY` from your RushDB project settings

## Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Tutorial

### 1. Seed sample data (optional — already included inline)

```bash
python seed.py
```

### 2. Run the main demo

```bash
python main.py
```

## Expected Output

```
=== Custom Vectorizers & RushDB Embedding Pipeline ===

1. Creating external vector index for Book descriptions...
   Index created: index_id='xxx'
   Status: awaiting_vectors
   Dimensions: 384 (all-MiniLM-L6-v2)

2. Creating 8 Book records...
   ✓ 'The Pragmatic Programmer' created
   ✓ 'Clean Code' created
   ✓ 'Design Patterns' created
   ✓ 'Introduction to Algorithms' created
   ✓ 'Structure and Interpretation of Computer Programs' created
   ✓ 'The Mythical Man-Month' created
   ✓ 'Refactoring' created
   ✓ 'Code Complete' created

3. Generating embeddings for all books...
   [================================] 100% (8/8)

4. Upserting vectors to index...
   ✓ All 8 vectors indexed successfully

5. Running semantic searches...

   Query: "software engineering best practices"
   ────────────────────────────────────────────
   [0.892] Clean Code (Robert C. Martin)
   [0.847] Code Complete (Steve McConnell)
   [0.801] The Pragmatic Programmer (David Thomas)
   [0.734] Refactoring (Martin Fowler)
   [0.701] Design Patterns (Gang of Four)

   Query: "algorithms and data structures"
   ────────────────────────────────────────────
   [0.856] Introduction to Algorithms (Cormen et al.)
   [0.742] Structure and Interpretation... (Sussman)
   [0.698] Design Patterns (Gang of Four)
   [0.612] Code Complete (Steve McConnell)
   [0.587] Clean Code (Robert C. Martin)

6. Cleanup: deleting test records and index...
   ✓ Records deleted
   ✓ Index deleted

=== Demo complete ===
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐      ┌─────────────────────────────────┐ │
│  │ sentence-        │      │           RushDB                 │ │
│  │ transformers     │      │  ┌─────────────────────────────┐ │ │
│  │                  │      │  │   External Vector Index     │ │ │
│  │  [Book desc]     │      │  │                             │ │ │
│  │       │          │      │  │  ┌─────┐ ┌─────┐ ┌─────┐   │ │ │
│  │       ▼          │      │  │  │ 384 │ │ 384 │ │ 384 │   │ │ │
│  │  [0.1, -0.2, ...]│──────┼──┴─▶│ dim │ │ dim │ │ dim │   │ │ │
│  │                  │      │     └─────┘ └─────┘ └─────┘   │ │ │
│  └──────────────────┘      │  ┌───────────────────────────┐ │ │
│                             │  │   Neo4j (vector + graph)  │ │ │
│                             │  └───────────────────────────┘ │ │
│                             └─────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Code Patterns

### Creating an External Vector Index

```sdk
db.ai.indexes.create({
    "label": "Book",
    "propertyName": "description",
    "sourceType": "external",
    "dimensions": 384,
    "similarityFunction": "cosine",
})
___SPLIT___
await db.ai.indexes.create({
    label: 'Book',
    propertyName: 'description',
    sourceType: 'external',
    dimensions: 384,
    similarityFunction: 'cosine',
})
```

### Generating Embeddings with sentence-transformers

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
text = "The Pragmatic Programmer is your guide to..."
vector = model.encode(text).tolist()  # 384-dimensional
```

### Upserting Vectors

```sdk
db.ai.indexes.upsert_vectors(index_id, {
    "items": [
        {"recordId": book.id, "vector": embedding},
        # ... more items
    ]
})
___SPLIT___
await db.ai.indexes.upsertVectors(indexId, {
    items: [
        { recordId: book.id, vector: embedding },
        // ... more items
    ]
})
```

### Semantic Search with External Vectors

```sdk
# Generate query vector locally
query_vector = model.encode("software engineering best practices")

# Search using the pre-computed vector
results = db.ai.search({
    "propertyName": "description",
    "queryVector": query_vector.tolist(),
    "labels": ["Book"],
    "limit": 5
})
___SPLIT___
// Generate query vector locally
const queryVector = await model.encode("software engineering best practices")

// Search using the pre-computed vector
const { data: results } = await db.ai.search({
    propertyName: 'description',
    queryVector: queryVector.tolist(),
    labels: ['Book'],
    limit: 5
})
```

## Customization Options

| Use Case | Recommended Model | Dimensions |
|----------|-------------------|------------|
| General purpose (fast) | `all-MiniLM-L6-v2` | 384 |
| High quality (slower) | `all-mpnet-base-v2` | 768 |
| Multilingual | `paraphrase-multilingual-MiniLM-L12-v2` | 384 |
| Code-specific | `microsoft/codebert-base` | 768 |
| Scientific papers | `allenai/specter2` | 768 |

## Resources

- [RushDB Documentation](https://docs.rushdb.com)
- [sentence-transformers](https://www.sbert.net/)
- [Example Repository](https://github.com/rush-db/examples/tree/main/custom-vectorizers-and-rushdbs-embedding-pipeline-tutorial)
