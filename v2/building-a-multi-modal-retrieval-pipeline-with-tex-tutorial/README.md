# Building a Multi-Modal Retrieval Pipeline with Text and Image Embeddings

A tutorial demonstrating how to build a production-ready multi-modal retrieval system using RushDB as the vector storage and similarity search backend.

## What This Tutorial Demonstrates

- **Multi-modal embeddings**: Generating and storing vectors for both text and images
- **Dual vector indexes**: Creating separate RushDB indexes for text and image embeddings
- **Hybrid retrieval**: Combining text and image similarity for richer search results
- **Property graph relationships**: Linking documents with their embeddings and collections

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Content    │────▶│  RushDB          │◀────│  Query      │
│  (text/img) │     │  ├─ Text Index    │     │  Pipeline   │
└─────────────┘     │  ├─ Image Index   │     └─────────────┘
                    │  └─ Relationships│
                    └──────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works)
- `sentence-transformers` for text embeddings

## Setup

1. **Clone the repository and navigate to this example:**
   ```bash
   git clone https://github.com/rush-db/examples.git
   cd building-a-multi-modal-retrieval-pipeline-with-tex-tutorial
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

5. **Generate seed data:**
   ```bash
   python seed.py
   ```

6. **Run the main demo:**
   ```bash
   python main.py
   ```

## Expected Output

The demo will:
1. Create two vector indexes (text and image embeddings)
2. Seed 30 sample product records with embedded vectors
3. Demonstrate pure text search
4. Demonstrate pure image search
5. Demonstrate hybrid search combining both modalities
6. Show relationship traversal for result enrichment

## Embedding Models Used

| Modality | Model | Dimensions | Reason |
|----------|-------|------------|--------|
| Text | `all-MiniLM-L6-v2` | 384 | Fast, good quality, lightweight |
| Image | Simulated CLIP embeddings | 512 | Tutorial uses synthetic vectors for reproducibility |

> **Note**: For production image embeddings, integrate a CLIP model like `openai/clip-vit-base-patch32`. This tutorial uses simulated vectors for reproducibility and to focus on the RushDB integration pattern.

## File Structure

```
.
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py           # Data generation and ingestion script
└── main.py           # Main demo showcasing retrieval patterns
```

## Key RushDB Patterns

```sdk
# Create a record with embedded vectors using the clean inline pattern
product = db.records.create(
    label="PRODUCT",
    data={"name": "Wireless Headphones", "description": "..."},
    vectors=[
        {"propertyName": "text_embedding", "vector": text_vec},
        {"propertyName": "image_embedding", "vector": image_vec}
    ]
)
___SPLIT___
// TypeScript — 2-space indentation for every nested level
const product = await db.records.create({
  label: 'PRODUCT',
  data: { name: 'Wireless Headphones', description: '...' },
  vectors: [
    { propertyName: 'text_embedding', vector: textVec },
    { propertyName: 'image_embedding', vector: imageVec }
  ]
})
```

```sdk
# Search across multiple modalities
results = db.ai.search({
    "propertyName": "image_embedding",
    "queryVector": image_query_vector,
    "labels": ["PRODUCT"],
    "limit": 10
}).data
___SPLIT___
// TypeScript — 2-space indentation for every nested level
const { data: results } = await db.ai.search({
  propertyName: 'image_embedding',
  queryVector: imageQueryVector,
  labels: ['PRODUCT'],
  limit: 10
})
```

## Pricing Note

RushDB's vector indexing is included in all plans. Writes (including embedding generation) are measured in KnowledgeUnits (KU), but standard reads and searches are **always free**. See [RushDB Pricing](https://rushdb.com/pricing) for details.
