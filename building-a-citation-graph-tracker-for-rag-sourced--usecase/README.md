# Building a Citation Graph Tracker for RAG-Sourced Answers

A production-ready prototype demonstrating how to track answer provenance in Retrieval-Augmented Generation (RAG) systems using RushDB's unique combination of graph traversal and vector similarity search.

## Why This Project Exists

RAG systems answer questions by retrieving relevant document chunks and passing them to an LLM. But when the LLM produces a response, how do you know exactly which source material it came from? Standard RAG pipelines lose this lineage information.

**This project solves that by building a citation graph** that tracks:
- Source documents and their chunked content
- Vector embeddings for semantic retrieval
- Retrieval events (which chunks were retrieved for which query)
- LLM responses and their associated citations
- Full provenance traversal from answer → citations → chunks → documents

This enables compliance auditing, answer debugging, and user trust through transparent source attribution.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  DOCUMENT   │────▶│   CHUNK     │────▶│ RETRIEVAL_EVENT  │────▶│  LLM_RESPONSE   │
└─────────────┘     └─────────────┘     └──────────────────┘     └─────────────────┘
      │                   │                     │                      │
      │                   │ vectors stored      │                      │
      │                   │ on chunks for       │                      │
      │                   │ semantic search      │                      │
      │                   ▼                     │                      │
      │            ┌─────────────┐               │                      │
      └───────────▶│  citations  │◀──────────────┘                      │
                   └─────────────┘                                       │
                   │                    full lineage traceback          │
                   ▼                                                        │
            ┌─────────────┐                                                │
            │  PROVENANCE │◀───────────────────────────────────────────────┘
            └─────────────┘
```

## Key Features

- **Document → Chunk Graph**: Documents are split into chunks, each linked to its parent
- **Vector Embeddings**: Chunks store semantic embeddings for similarity search
- **Retrieval Tracking**: Every semantic search creates a `RETRIEVAL_EVENT` record
- **Multi-Hop Support**: When chunks reference other chunks, the graph captures cross-references
- **Full Provenance**: Trace any answer back to its source documents with confidence scores

## Prerequisites

- Python 3.9+
- A RushDB account ([get free API key](https://app.rushdb.com))
- `sentence-transformers` for embeddings (all-MiniLM-L6-v2, 384 dimensions)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

### 3. Seed the Database

This creates sample documents about AI/ML topics with realistic chunking:

```bash
python seed.py
```

Expected output:
```
🌱 Seeding RushDB with sample documents...
✅ Created 3 documents with 12 total chunks
✅ Created vector index on CHUNK.body (384 dimensions)
✅ Upserted 12 chunk vectors
✅ Seeding complete!
```

### 4. Run the Citation Tracker

```bash
python main.py
```

This demonstrates:
1. Semantic search across document chunks
2. Creating a simulated LLM response with citations
3. Tracing provenance back through the graph

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── seed.py             # Database seeding script
├── main.py             # Citation graph tracker prototype
└── data/
    └── documents.json   # Sample documents about AI topics
```

## How It Works

### Data Model

| Label | Description |
|-------|-------------|
| `DOCUMENT` | Source documents with metadata |
| `CHUNK` | Document chunks with vector embeddings |
| `RETRIEVAL_EVENT` | Records a semantic search query and retrieved chunks |
| `LLM_RESPONSE` | Final generated response |
| `CITATION` | Links responses to retrieval events |

### Workflow

1. **Indexing Phase**: Documents → Chunks → Vector Embeddings → Stored in RushDB
2. **Query Phase**: Semantic Search → Retrieval Events → LLM Response + Citations
3. **Audit Phase**: Trace any response back to source documents

## Expected Output

```
╔══════════════════════════════════════════════════════════════╗
║   CITATION GRAPH TRACKER FOR RAG-SOURCED ANSWERS            ║
╚══════════════════════════════════════════════════════════════╝

📚 Query: "How does vector search work in databases?"
────────────────────────────────────────────────────────────────

🔍 Semantic Search Results:
  [1] "Vector databases use embedding..." (score: 0.847)
  [2] "Nearest neighbor search algorithms..." (score: 0.792)
  [3] "Embedding models convert text..." (score: 0.734)

🤖 Simulated LLM Response:
────────────────────────────────────────────────────────────────
"Vector databases store data as high-dimensional vectors and use
similarity search to find relevant items. They employ nearest neighbor
algorithms like HNSW or FAISS for efficient retrieval. Text is first
converted into vectors using embedding models before storage."

📎 Citations: 3 sources
────────────────────────────────────────────────────────────────

🔬 PROVENANCE TRACE
────────────────────────────────────────────────────────────────

Citation #1 → CHUNK (ID: chunk_abc123)
  Content: "Vector databases use embedding..."
  Score: 0.847
  Parent Document: "Introduction to Vector Databases"
    - Author: Dr. Sarah Chen
    - Published: 2024-01-15

Citation #2 → CHUNK (ID: chunk_def456)
  Content: "Nearest neighbor search algorithms..."
  Score: 0.792
  Parent Document: "ANN Algorithms Comparison"
    - Author: Prof. James Miller
    - Published: 2024-02-20

Citation #3 → CHUNK (ID: chunk_ghi789)
  Content: "Embedding models convert text..."
  Score: 0.734
  Parent Document: "Introduction to Vector Databases"
    - Author: Dr. Sarah Chen
    - Published: 2024-01-15

✅ Answer fully auditable: 3 documents traced
```

## Embedding Model

We use **all-MiniLM-L6-v2** from sentence-transformers:
- **384 dimensions**: Compact but effective for semantic similarity
- **Fast inference**: ~50ms per query on CPU
- **Well-balanced**: Strong performance on semantic search benchmarks

This model choice prioritizes tutorial clarity and speed. Production systems may use larger models like `text-embedding-ada-002` or domain-specific embeddings.

## Compliance & Audit Use Cases

This citation tracking system enables:

- **Regulatory Compliance**: Prove which source material informed each answer
- **Error Debugging**: Trace hallucinated facts back to their (mis)interpreted sources
- **User Trust**: Show users exactly where information comes from
- **Quality Metrics**: Track retrieval quality by analyzing citation patterns

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)
- [Vector Search Best Practices](https://docs.rushdb.com/ai-search)

## License

MIT License - Use freely for learning, prototyping, and production systems.
