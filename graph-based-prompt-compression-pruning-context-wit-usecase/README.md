# Graph-Based Prompt Compression: Pruning Context Without Losing Meaning

A production-ready RAG pipeline demonstrating how structural graph traversal reduces prompt tokens while maintaining answer quality. Built with RushDB's native graph+vector combination.

[![GitHub](https://img.shields.io/badge/GitHub-rush--db%2Fexamples-blue?style=flat-square)](https://github.com/rush-db/examples/tree/main/graph-based-prompt-compression-pruning-context-wit-usecase)
[![Docs](https://img.shields.io/badge/Docs-rushdb.com-blue?style=flat-square)](https://docs.rushdb.com)

## What This Demonstrates

This project shows how to build a RAG pipeline that:

1. **Ingests documents** and chunks them semantically
2. **Builds a knowledge graph** connecting related concepts across chunks
3. **Performs graph-aware retrieval** that finds the minimal connected subgraph
4. **Prunes irrelevant context** while preserving structural relationships
5. **Measures the impact** — token reduction, quality retention, latency tradeoffs

The key insight: naive vector similarity returns the k-most-similar chunks individually, but ignores cross-chunk relationships. Graph traversal ensures we get semantically coherent context that maintains discourse structure.

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Document   │────▶│   Chunk     │────▶│  Vector Index    │
│  Ingestion  │     │  Extraction │     │  (embeddings)    │
└─────────────┘     └──────┬──────┘     └──────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Concept    │
                    │  Extraction  │
                    └──────┬───────┘
                           │
                           ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Query     │────▶│ Graph        │────▶│ Minimal Subgraph │
│   Time      │     │ Traversal    │     │ Pruning          │
└─────────────┘     └──────┬───────┘     └────────┬─────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────────────────────┐
                    │    Compressed Context +      │
                    │    Metrics Comparison         │
                    └──────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account and API key ([get one free](https://app.rushdb.com))
- 8GB RAM minimum for embedding model

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your RUSHDB_API_KEY
```

### 3. Seed the Database

This creates synthetic research paper chunks with graph relationships:

```bash
python seed.py
```

Expected output:
```
Seeding database with research paper data...
[1/100] Created chunk: Attention Is All You Need (chunk 1/8)
[50/100] Linked concepts: transformer → attention mechanism
[100/100] Seeding complete: 25 documents, 75 chunks, 50+ concept links
```

### 4. Run the Pipeline

```bash
python main.py
```

This executes both naive and graph-based retrieval for comparison:

```bash
$ python main.py

=== Graph-Based Prompt Compression Demo ===

[1/3] Query: "How do self-attention mechanisms work?"
  Naive (top-3 chunks): 847 tokens | Graph-pruned: 412 tokens | Reduction: 51.4%

[2/3] Query: "What is retrieval-augmented generation?"
  Naive (top-3 chunks): 923 tokens | Graph-pruned: 398 tokens | Reduction: 56.9%

[3/3] Query: "Explain the transformer architecture"
  Naive (top-3 chunks): 1024 tokens | Graph-pruned: 521 tokens | Reduction: 49.1%

=== Summary ===
Average token reduction: 52.5%
Average retrieval latency (naive): 45ms
Average retrieval latency (graph): 78ms
Quality preserved: 94.2% concept overlap with reference
```

## Project Structure

```
graph-based-prompt-compression-pruning-context-wit-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Database seeding script
├── main.py             # Main pipeline with metrics
└── data/
    └── benchmark.json  # Query benchmark set (optional)
```

## How It Works

### 1. Document Ingestion & Chunking

Documents are split into overlapping semantic chunks (~200-400 tokens each). Each chunk is:
- Stored as a `CHUNK` record in RushDB
- Embedded using sentence-transformers
- Linked to its parent `DOCUMENT`

### 2. Concept Graph Construction

For each chunk, NLP extraction identifies key concepts (named entities, technical terms). These create:
- `CONCEPT` nodes in RushDB
- `MENTIONS` relationships: `CHUNK` → `CONCEPT`
- `RELATED_TO` relationships: `CONCEPT` ↔ `CONCEPT` (cross-references)

### 3. Query-Time Retrieval

**Naive approach** (baseline):
```
1. Semantic search → top-k chunks by similarity
2. Return chunks as-is
```

**Graph-pruned approach**:
```
1. Semantic search → candidate chunks (k=20)
2. Traverse graph → collect connected concepts
3. Score each chunk by: relevance × graph_connectivity
4. Prune → keep chunks above threshold
5. Return pruned subgraph
```

### 4. The Graph Traversal Algorithm

```python
def prune_with_graph(candidate_chunks, relevance_threshold=0.6):
    """
    Find minimal connected subgraph containing relevant chunks.
    
    RushDB query pattern:
    1. Start from high-relevance seed chunks
    2. Traverse CONCEPT neighbors
    3. Include chunks that share concepts
    4. Score and filter by threshold
    """
    
    # Step 1: Find seed chunks above relevance threshold
    seed_chunks = [c for c in candidate_chunks 
                   if c.score >= relevance_threshold]
    
    # Step 2: Traverse to connected concepts
    concept_ids = set()
    for chunk in seed_chunks:
        # RushDB: traverse MENTIONS relationships
        related_concepts = db.records.find({
            "labels": ["CONCEPT"],
            "where": {"CHUNK": {"$relation": {"type": "MENTIONS", "direction": "in"}}}
        })
        concept_ids.update(c.id for c in related_concepts)
    
    # Step 3: Expand to chunks sharing these concepts
    relevant_chunks = []
    for concept_id in concept_ids:
        connected_chunks = db.records.find({
            "labels": ["CHUNK"],
            "where": {"CONCEPT": {"$id": concept_id}}
        })
        relevant_chunks.extend(connected_chunks)
    
    # Step 4: Deduplicate and rank by cumulative relevance
    return deduplicate_and_rank(relevant_chunks)
```

## Metrics Explained

| Metric | Description |
|--------|-------------|
| **Token Reduction** | `(naive_tokens - pruned_tokens) / naive_tokens × 100` |
| **Concept Overlap** | % of reference concepts found in pruned context |
| **Retrieval Latency** | Time to fetch and prune (ms) |
| **Subgraph Size** | Number of chunks in final pruned context |

## Production Considerations

### Graph Update Frequency

The concept graph should be updated:
- **On document update**: Re-extract concepts and update relationships
- **Nightly batch**: Full graph consistency check
- **On-demand**: For real-time applications, lazy-update on query

```python
# Example: Incremental graph update
def update_document_graph(document_id, new_chunks):
    for chunk in new_chunks:
        concepts = extract_concepts(chunk.body)
        for concept in concepts:
            # Create or find concept
            concept_record = find_or_create_concept(concept)
            # Link chunk to concept
            db.records.attach(
                source=chunk, 
                target=concept_record,
                options={"type": "MENTIONS"}
            )
```

### Vector Sync Strategy

Vectors must stay synchronized with text:
- Use external vector index for control
- Re-embed on document update
- Batch sync for bulk updates

```python
# Re-index after document update
def sync_vectors(document_id):
    chunks = get_document_chunks(document_id)
    vectors = [embed(chunk.body) for chunk in chunks]
    
    db.ai.indexes.upsert_vectors(index_id, {
        "items": [
            {"recordId": c.id, "vector": v}
            for c, v in zip(chunks, vectors)
        ]
    })
```

### Pruning Threshold Tuning

| Use Case | Threshold | Rationale |
|----------|-----------|-----------|
| Code generation | 0.7 | High accuracy required |
| General Q&A | 0.5 | Balance speed/quality |
| Creative writing | 0.3 | More context helps |
| Legal/compliance | 0.8 | Minimize hallucinations |

Tune by running your benchmark set and plotting precision-recall curves.

## API Reference

This project uses these RushDB SDK methods:

```sdk
# Create chunks with vectors
db.records.create(
    label="CHUNK",
    data={"body": chunk_text, "position": i},
    vectors=[{"propertyName": "body", "vector": embedding}]
)
___SPLIT___
// Create chunks with vectors
await db.records.create({
    label: "CHUNK",
    data: { body: chunkText, position: i },
    vectors: [{ propertyName: "body", vector: embedding }]
})
```

```sdk
# Semantic search for candidate chunks
db.ai.search({
    "propertyName": "body",
    "query": query_text,
    "labels": ["CHUNK"],
    "limit": 20
})
___SPLIT___
// Semantic search for candidate chunks
await db.ai.search({
    propertyName: "body",
    query: queryText,
    labels: ["CHUNK"],
    limit: 20
})
```

```sdk
# Traverse to related concepts
db.records.find({
    "labels": ["CONCEPT"],
    "where": {
        "CHUNK": {"$relation": {"type": "MENTIONS", "direction": "in"}}
    }
})
___SPLIT___
// Traverse to related concepts
await db.records.find({
    labels: ["CONCEPT"],
    where: {
        CHUNK: { $relation: { type: "MENTIONS", direction: "in" }}
    }
})
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RAG Optimization Techniques](https://docs.rushdb.com/guides/rag)
- [Graph-Based Retrieval in Production](https://docs.rushdb.com/guides/knowledge-graphs)

## License

MIT - See [GitHub repository](https://github.com/rush-db/examples) for details.
