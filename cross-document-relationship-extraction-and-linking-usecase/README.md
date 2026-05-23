# Cross-Document Relationship Extraction and Linking

A practical demonstration of the **chunk-boundary problem** in RAG systems and how RushDB's graph+vector architecture solves referential integrity across document boundaries.

## The Problem

When building RAG systems, documents are typically split into chunks for embedding and retrieval. This chunking destroys critical **cross-document relationships**:

1. A clause in Document A references a definition in Document B
2. A pricing term in Document C links to a rate card in Document D
3. A commitment in Document E triggers a condition described in Document F

Vector similarity search can find related chunks, but it **cannot preserve referential integrity**. When a user asks: "What are Acme Corp's total obligations under both the MSA and the SOW?" — vector-only retrieval fails because:
- It returns isolated chunks
- It loses the graph of relationships between documents
- Cross-references become dangling links

## The Solution

RushDB stores both **documents as nodes** and **relationships as edges**, with embeddings on both levels. This enables:
- **Graph traversal** to follow cross-document references
- **Vector search** to find semantically relevant content
- **Combined queries** that leverage both approaches

## What This Demo Shows

1. **The Chunk-Boundary Problem** — How splitting destroys cross-document relationships
2. **Vector Search Failure** — Why semantic similarity alone can't traverse relationships
3. **Graph Traversal** — Following edges across documents preserves referential integrity
4. **RushDB Implementation** — Complete working example with documents, nodes, and edges
5. **Benchmark Results** — Retrieval quality comparison on multi-hop questions

## Prerequisites

- Python 3.9+
- A RushDB account ([free tier available](https://rushdb.com/pricing))
- `sentence-transformers` for embeddings

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API key

# Generate mock legal documents and import them
python seed.py
```

## Running the Demo

```bash
python main.py
```

The script will:
1. Check if seed data exists (skip if already loaded)
2. Run vector-only retrieval benchmarks
3. Run graph+vector retrieval benchmarks
4. Compare results on multi-hop questions
5. Display benchmark summary

## Expected Output

```
=== Cross-Document Relationship Extraction Demo ===

--- Chunk Boundary Problem Illustration ---
Document "Master Service Agreement" contains reference to "Pricing Schedule" via "RATE_CARD" relationship
Document "Statement of Work" contains reference to "MSA" via "GOVERNS" relationship
Document "Pricing Schedule" contains rate information referenced by both MSA and SOW

--- Benchmark Results ---

Question: "What are the payment terms and how do they relate to the liability cap?"
  Pure Vector Search:
    - Retrieved 3 chunks (avg similarity: 0.72)
    - Cross-reference preserved: NO
    - Answerable: PARTIAL (missing connection)
  
  Graph + Vector Search:
    - Retrieved 5 records via graph traversal
    - Cross-reference preserved: YES
    - Answerable: COMPLETE

--- Benchmark Summary ---
Vector-only Precision: 0.45 | Recall: 0.38 | Cross-ref integrity: 0.12
Graph+Vector Precision: 0.82 | Recall: 0.89 | Cross-ref integrity: 0.95
```

## Project Structure

```
cross-document-relationship-extraction-and-linking-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Mock legal document generator
├── main.py             # Main demo with benchmarks
└── data/
    └── sample_documents.json  # Sample cross-document references
```

## Technical Details

### Data Model

Each legal document is stored as a `DOCUMENT` node with:
- `title`: Document name
- `body`: Full text content
- `doc_type`: Type (MSA, SOW, Pricing Schedule, etc.)
- `embedding`: Vector representation of body

Relationships between documents use typed edges:
- `REFERENCES` → Links clauses to their definitions
- `GOVERNS` → Links SOW to MSA
- `ATTACHED_TO` → Links schedules to main agreements
- `ESTABLISHES` → Links definitions to rates/terms

### Embedding Strategy

- Document-level embeddings capture the overall meaning
- Relationships preserve structural links that embeddings lose
- Combined queries use vector search for relevance + graph for traversal

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Repository](https://github.com/rush-db/examples/tree/main/cross-document-relationship-extraction-and-linking-usecase)
- [RushDB Pricing](https://rushdb.com/pricing)

## License

MIT License - See repository for details
