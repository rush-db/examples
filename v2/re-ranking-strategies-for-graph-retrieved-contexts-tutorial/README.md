# Re-ranking Strategies for Graph-Retrieved Contexts in LLM Pipelines

A practical tutorial demonstrating how to implement multiple re-ranking strategies using RushDB's graph-based retrieval capabilities for LLM context augmentation.

## What This Demonstrates

This project showcases a complete retrieval pipeline that:

1. **Stores structured knowledge** in RushDB as a property graph with documents, chunks, and semantic relationships
2. **Retrieves candidate contexts** using RushDB's vector search and graph traversal
3. **Applies multiple re-ranking strategies** to optimize context selection for LLM prompts:
   - BM25 keyword scoring
   - Vector similarity re-weighting
   - Graph centrality scoring
   - Hybrid ensemble scoring
   - Query-document relevance scoring

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Query    │────▶│  RushDB Graph    │────▶│  Re-ranking     │
│                 │     │  Retrieval       │     │  Strategies     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │  LLM Context    │
                                                │  (Augmented     │
                                                │   Prompt)       │
                                                └─────────────────┘
```

## Re-ranking Strategies Explained

### 1. BM25 Scoring
BM25 (Best Matching 25) is a probabilistic relevance ranking function. It improves on TF-IDF by:
- Saturating term frequency (diminishing returns for repeated terms)
- Document length normalization
- Term frequency saturation parameter (k1)

### 2. Vector Similarity Re-weighting
After initial semantic search, re-weight results based on:
- Exact embedding cosine similarity scores
- Cross-field semantic matches (title, metadata)

### 3. Graph Centrality Scoring
Leverage the graph structure to score documents by:
- Incoming relationship count (how many other docs reference this)
- Relationship type weights (hierarchy, citation, similarity)
- Neighbor document relevance scores

### 4. Hybrid Ensemble Scoring
Combine multiple signals with learned or tuned weights:
```
final_score = α·bm25 + β·vector_sim + γ·centrality + δ·recency
```

### 5. Query-Document Relevance (Cross-Encoder Style)
Compute relevance scores by analyzing:
- Query term coverage in document
- Semantic coherence between query intent and document topic
- Section importance weighting

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works: https://rushdb.com)
- OpenAI API key (for embeddings, or use sentence-transformers)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials:
#   RUSHDB_API_TOKEN=your_token_here
#   OPENAI_API_KEY=sk-... (optional, uses sentence-transformers if not set)
```

### 3. Get RushDB Credentials

1. Sign up at https://app.rushdb.com
2. Create a new project
3. Generate an API token
4. Find your project token in project settings

### 4. Seed the Knowledge Base

This creates the graph with documents, chunks, and relationships:

```bash
python seed.py
```

Expected output:
```
Seeding knowledge base...
✓ Created 12 document records
✓ Created 48 chunk records (4 per document)
✓ Created 52 relationships
✓ Created vector index
✓ Seeded vectors: 48 indexed
✅ Seed complete! 12 documents, 48 chunks ready.
```

## Running the Demo

```bash
python main.py
```

### What You'll See

The demo runs queries against the seeded knowledge base and demonstrates each re-ranking strategy:

```
╔══════════════════════════════════════════════════════════════════╗
║  RE-RANKING STRATEGIES FOR GRAPH-RETRIEVED CONTEXTS              ║
╚══════════════════════════════════════════════════════════════════╝

Query: "How do I implement authentication in a React application?"

────────────────────────────────────────────────────────────────────
Strategy 1: BM25 Keyword Scoring
────────────────────────────────────────────────────────────────────
  Rank 1: [0.72] React Authentication Patterns
  Rank 2: [0.68] OAuth 2.0 Implementation Guide
  Rank 3: [0.61] JWT Token Management
  ...

────────────────────────────────────────────────────────────────────
Strategy 2: Vector Similarity Re-weighting
────────────────────────────────────────────────────────────────────
  Rank 1: [0.89] React Authentication Patterns
  Rank 2: [0.85] Authentication Best Practices
  Rank 3: [0.82] OAuth 2.0 Implementation Guide
  ...

────────────────────────────────────────────────────────────────────
Strategy 3: Graph Centrality Scoring
────────────────────────────────────────────────────────────────────
  Rank 1: [0.94] Authentication Best Practices (cited by 8 docs)
  Rank 2: [0.86] OAuth 2.0 Implementation Guide (cited by 6 docs)
  Rank 3: [0.78] React Authentication Patterns (cited by 5 docs)
  ...

────────────────────────────────────────────────────────────────────
Strategy 4: Hybrid Ensemble Scoring
────────────────────────────────────────────────────────────────────
  Rank 1: [0.91] React Authentication Patterns
  Rank 2: [0.87] OAuth 2.0 Implementation Guide
  Rank 3: [0.85] Authentication Best Practices
  ...

────────────────────────────────────────────────────────────────────
Strategy 5: Query-Document Relevance Scoring
────────────────────────────────────────────────────────────────────
  Rank 1: [0.93] React Authentication Patterns
           ↑ Query coverage: 85%, Semantic coherence: High
  Rank 2: [0.88] OAuth 2.0 Implementation Guide
           ↑ Query coverage: 72%, Semantic coherence: High
  Rank 3: [0.82] JWT Token Management
           ↑ Query coverage: 68%, Semantic coherence: Medium
  ...

────────────────────────────────────────────────────────────────────
Final Selected Context (Top 3 by Hybrid Score):
────────────────────────────────────────────────────────────────────
  1. React Authentication Patterns (score: 0.91)
  2. OAuth 2.0 Implementation Guide (score: 0.87)
  3. Authentication Best Practices (score: 0.85)

✅ Demo complete!
```

## Project Structure

```
re-ranking-strategies-for-graph-retrieved-contexts-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generate and load mock knowledge base
├── main.py             # Main re-ranking demonstration
└── data/
    └── seed_data.json  # Seed data definitions
```

## Key Implementation Details

### RushDB Integration

This project uses RushDB's property graph capabilities to:

- **Store documents and chunks** as records with labels (`DOCUMENT`, `CHUNK`)
- **Create semantic relationships** between documents (`CITES`, `RELATED_TO`, `PART_OF`)
- **Enable vector search** on chunk content for semantic retrieval
- **Leverage graph traversal** for centrality-based re-ranking

### Embedding Strategy

The demo supports two embedding modes:

1. **OpenAI embeddings** (default if `OPENAI_API_KEY` is set):
   - Uses `text-embedding-3-small` for high quality
   - 1536 dimensions

2. **Local embeddings** (sentence-transformers):
   - Uses `all-MiniLM-L6-v2` for speed
   - 384 dimensions
   - No API costs

### Re-ranking Pipeline

```python
def rerank_with_strategy(strategy: str, candidates: list, query: str) -> list:
    # 1. Get initial candidates from RushDB (vector search)
    # 2. Compute strategy-specific scores
    # 3. Re-rank and return
```

## Extending This Project

### Add Your Own Data

Edit `data/seed_data.json` to add your documents:

```json
{
  "documents": [
    {
      "title": "Your Document Title",
      "content": "Document body...",
      "chunks": ["chunk1 content", "chunk2 content"],
      "related": ["other_doc_title"]
    }
  ]
}
```

### Custom Re-ranking Weights

Adjust weights in `main.py`:

```python
HYBRID_WEIGHTS = {
    "bm25": 0.25,
    "vector": 0.35,
    "centrality": 0.25,
    "recency": 0.15
}
```

### Integrate with Your LLM

Replace the mock prompt construction with your actual LLM call:

```python
def build_llm_prompt(query: str, contexts: list) -> str:
    context_text = "\n\n".join([c["content"] for c in contexts])
    return f"""Context:\n{context_text}\n\nQuestion: {query}\nAnswer:"""
```

## Understanding the Costs

RushDB pricing is based on Knowledge Units (KU):

| Operation | Cost |
|-----------|------|
| Record created | 0.5 KU |
| Property stored | 1 KU per property |
| Relationship | 0.25 KU per link |
| Embedding generated | 5 KU per record |
| Vector search | 5 KU per call |
| Standard reads | **Free** |

This demo uses approximately 500-1000 KU per full run.

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Cross-Encoder Reranking](https://www.sbert.net/examples/training/cross-encoder/)
- [Sentence Transformers](https://www.sbert.net/)

## License

MIT - See LICENSE file in rush-db/examples repository.
