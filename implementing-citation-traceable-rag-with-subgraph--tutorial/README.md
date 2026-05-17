# Implementing Citation-Traceable RAG with Subgraph Provenance

A complete implementation demonstrating how to build a RAG pipeline where every generated answer carries a verifiable audit trail. This pattern is essential for compliance, debugging, and building user trust in AI-assisted responses.

## What This Demo Shows

| Capability | Description |
|---|---|
| **Schema Design** | Defining the provenance graph with Document → Chunk → Embedding → RetrievalEvent → Generation node types and their relationships |
| **Provenance Ingestion** | Storing chunks with vectors, parent references, and extraction context embedded during document processing |
| **Provenance-Aware Retrieval** | Semantic search that returns both relevant chunks AND their full provenance subgraph |
| **Citation Assembly** | Traversing from retrieved chunk → source document and from generation → informing chunks |
| **Trace Visualization** | Structured output showing the complete reasoning path from question to answer |

## Prerequisites

- Python 3.10+
- RushDB account (free tier works)
- `sentence-transformers` for embeddings (all-MiniLM-L6-v2, fast and lightweight)

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY

# Seed the knowledge base (creates ~10 documents, 40+ chunks)
python seed.py

# Run the provenance demonstration
python main.py
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generates and ingests sample knowledge base
└── main.py             # Full provenance-traceable RAG demo
```

## Environment Variables

| Variable | Description |
|---|---|
| `RUSHDB_API_KEY` | Your RushDB API key from the dashboard |

## How It Works

### 1. Provenance Graph Schema

The graph models the full RAG lifecycle:

```
DOCUMENT ──EXTRACTED_FROM──► CHUNK ──EMBEDDING_OF──► EMBEDDING
                                    │
                                    │ (vector similarity)
                                    ▼
                            RETRIEVAL_EVENT ◄──TRIGGERED_BY── GENERATION
                                    │
                                    │ (traces back to)
                                    ▼
                              SOURCES
```

Each node stores metadata about when and how it was created, enabling full auditability.

### 2. Ingestion Flow

1. **Document** → full source text, metadata, ingestion timestamp
2. **Chunk** → extracted segment, chunk index, context window (before/after text)
3. **Embedding** → vector representation with the embedding model used
4. **Relationships** → links parent document → chunk → embedding with typed edges

### 3. Retrieval Flow

1. Query embedding is generated
2. Semantic search finds top-k chunks
3. For each chunk, we traverse the provenance subgraph
4. A `RetrievalEvent` records the query, retrieved chunks, and timestamp
5. The event is linked to all retrieved chunks

### 4. Citation Assembly

Given a generated response:
- **Forward trace**: Generation → RetrievalEvent → Chunks → Documents
- **Backward trace**: Chunk → parent Document (for verifying sources)

### 5. Trace Output

The final output includes:
```json
{
  "answer": "...",
  "sources": [
    {
      "chunk": "...",
      "document": {
        "title": "...",
        "section": "..."
      },
      "relevance_score": 0.87,
      "provenance_path": ["Document", "Chunk", "RetrievalEvent"]
    }
  ],
  "audit_trail": {
    "query_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "retrieval_timestamp": "...",
    "total_chunks_evaluated": 40
  }
}
```

## Expected Output

Running `python main.py` produces:

1. **Schema inspection**: Shows all labels and relationships in the graph
2. **Document statistics**: Count of documents, chunks, and embeddings
3. **Query demonstration**: 3 sample queries with full provenance traces
4. **Citation output**: Each answer with cited sources and audit trail

## Cleaning Up

To reset the demo and start fresh:

```bash
# Delete all demo records
python -c "from rushdb import RushDB; db = RushDB(); db.records.delete({'labels': ['DOCUMENT', 'CHUNK', 'EMBEDDING', 'RETRIEVAL_EVENT', 'GENERATION']})"
```

Or simply re-run `seed.py` — it's idempotent and will re-populate from scratch.

## References

- RushDB Documentation: https://docs.rushdb.com
- GitHub Repository: https://github.com/rush-db/examples/tree/main/implementing-citation-traceable-rag-with-subgraph--tutorial
