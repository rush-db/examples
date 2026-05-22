# Real-Time Vector Index Updates Without Re-Embedding Overhead

This tutorial demonstrates how to update vector-indexed records in RushDB without incurring the cost and latency of re-computing embeddings from scratch.

## The Problem

When you update a record that has a vector embedding (e.g., a document's content), most vector databases require you to:
1. Delete the old vector
2. Re-compute the embedding from the updated text
3. Insert the new vector

This is expensive — it costs KU per embedding generation and adds latency on every update.

## The Solution

RushDB's `db.records.set()` method allows you to update both the data **and** the vector in a single operation, using a pre-computed vector you already have (from your own embedding model). You skip the embedding generation entirely on updates.

This pattern is ideal when you:
- Run your own embedding pipeline
- Batch-generate embeddings and want to update RushDB incrementally
- Need sub-second updates on high-volume content

## What This Demo Covers

1. **Initial embedding**: Create a vector index and populate records with embeddings (using RushDB's managed service for initial ingest)
2. **Pre-computed updates**: Demonstrate `db.records.set()` with pre-computed vectors — no re-embedding required
3. **Verification**: Run semantic search to confirm the updated vectors are correctly indexed and searchable
4. **Comparison**: Show the cost difference (managed re-embedding vs. pre-computed vector update)

## Prerequisites

- Python 3.9+
- RushDB account (free tier works)
- `RUSHDB_API_KEY` from your dashboard

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Demo

```bash
# 1. Seed the database with sample documents
python seed.py

# 2. Run the real-time update demo
python main.py
```

## Expected Output

```
=== SEEDING PHASE ===
✓ Created index: Document.body (external, 384 dimensions)
✓ Seeded 15 documents

=== INITIAL SEARCH ===
Query: "machine learning applications"
[0.892] Understanding Neural Networks in Production
[0.847] Deep Learning for Beginners
[0.801] Machine Learning Model Deployment

=== PRE-COMPUTED VECTOR UPDATE ===
✓ Updated doc-0 with pre-computed vector (no re-embedding)
✓ Updated doc-1 with pre-computed vector (no re-embedding)
✓ Updated doc-2 with pre-computed vector (no re-embedding)

=== POST-UPDATE SEARCH ===
Query: "transformers and attention mechanisms"
[0.918] Attention Is All You Need - Summary
[0.874] Transformer Architecture Explained
[0.842] BERT and Its Applications

=== COST COMPARISON ===
Managed re-embedding (3 updates): 15 KU
Pre-computed vector update (3 updates): 0 KU (embedding generation skipped)
```

## How It Works

### Initial Seeding

When you first create records, you generate embeddings using your preferred model:

```sdk
# Generate embedding externally
embedding = my_embedding_model.encode("Document content here")

# Store record with pre-computed vector
doc = db.records.create(
    label="Document",
    data={"body": "Document content here", "title": "My Doc"},
    vectors=[{"propertyName": "body", "vector": embedding.tolist()}]
)
___SPLIT___
// Generate embedding externally
const embedding = await myEmbeddingModel.encode("Document content here")

// Store record with pre-computed vector
const doc = await db.records.create({
    label: "Document",
    data: { body: "Document content here", title: "My Doc" },
    vectors: [{ propertyName: "body", vector: embedding.tolist() }]
})
```

### Real-Time Updates

When content changes, you update the vector along with the data — no re-embedding needed:

```sdk
# Re-compute embedding externally (one-time cost)
new_embedding = my_embedding_model.encode("Updated content here")

# Update both data and vector in one operation
db.records.set(
    target=doc,
    label="Document",
    data={"body": "Updated content here", "title": "My Updated Doc"},
    vectors=[{"propertyName": "body", "vector": new_embedding.tolist()}]
)
___SPLIT___
// Re-compute embedding externally (one-time cost)
const newEmbedding = await myEmbeddingModel.encode("Updated content here")

// Update both data and vector in one operation
await db.records.set({
    target: doc,
    label: "Document",
    data: { body: "Updated content here", title: "My Updated Doc" },
    vectors: [{ propertyName: "body", vector: newEmbedding.tolist() }]
})
```

### Key Insight

By using pre-computed vectors, you pay the embedding cost **once** during your pipeline, not on every update. RushDB stores and indexes the vector you provide without regenerating it.

## KU Cost Analysis

| Operation | KU Cost |
|-----------|--------|
| Record created | 0.5 KU |
| Property stored | 1 KU per property |
| Vector stored | Free (no KU for the vector itself) |
| Managed embedding generated | 5 KU per record |
| Pre-computed vector update | 0 KU (embedding generation) |

**Bottom line**: For high-frequency updates, pre-computed vectors save 5 KU per update compared to managed re-embedding.

## Repository

https://github.com/rush-db/examples/tree/main/real-time-vector-index-updates-without-re-embeddin-tutorial