# Source Attribution and Grounded Generation Through Graph Provenance

**Project:** `source-attribution-and-grounded-generation-through-usecase`  
**RushDB SDK Reference:** [Python SDK](https://docs.rushdb.com/sdk/python) | [JavaScript SDK](https://docs.rushdb.com/sdk/javascript)

---

## What This Project Demonstrates

Building a **grounded, auditable AI research assistant** — where every generated answer carries a full citation lineage that can be verified, traced, and audited.

This project reveals where **pure vector stores break down** and why **graph + vector** (RushDB's dual-layer architecture) is the right tool for production-grounded AI:

| Capability | Pure Vector Store | RushDB (Graph + Vector) |
|------------|-------------------|-------------------------|
| Find relevant text | ✅ | ✅ |
| Trace claim back to source | ❌ | ✅ |
| Audit full evidence chain | ❌ | ✅ |
| Handle document updates | ❌ (stale embeddings) | ✅ (traverse current graph) |
| Verify downstream claims | ❌ | ✅ (query citation graph) |
| Explain why a claim was made | ❌ | ✅ (provenance trail) |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        RushDB Storage                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  Document     │───▶│   Passage    │───▶│    Claim     │       │
│  │  (source)     │    │  (chunked)   │    │  (extracted) │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│        │                   │                   │                │
│   CONTAINS              SUPPORTS             CITES               │
│        │                   │                   │                │
│        ▼                   ▼                   ▼                │
│  ─────────────────────────────────────────────────────────       │
│  Vector Index on Passage.content ── semantic search             │
└─────────────────────────────────────────────────────────────────┘

Query Path:
  User Question
       │
       ▼
  Semantic Search (vector retrieval)
       │
       ▼
  Candidate Passages ──▶ Graph Traversal ──▶ Supporting Claims
       │                                           │
       │                                           ▼
       │                                    Answer Assembly
       │                                    (with citation IDs)
       │
       ▼
  Provenance: "Claim X cites Passage Y from Document Z"
```

---

## Key RushDB Patterns Demonstrated

### 1. Inline Vector Writes on Record Creation

```sdk
db.records.create(
    label="Passage",
    data={"content": chunk_text, "source": doc_id},
    vectors=[{"propertyName": "content", "vector": embedding}]
)
```

### 2. Transactional Graph Building

```sdk
with db.transactions.begin() as tx:
    passage = db.records.create(label="Passage", data={...}, transaction=tx)
    claim = db.records.create(label="Claim", data={...}, transaction=tx)
    db.records.attach(source=claim, target=passage, options={"type": "CITES"}, transaction=tx)
```

### 3. Semantic Search with Graph Enrichment

```sdk
# Phase 1: Vector retrieval
candidates = db.ai.search({
    "propertyName": "content",
    "query": user_question,
    "labels": ["Passage"],
    "limit": 10
})

# Phase 2: Graph traversal to claims
for passage in candidates:
    claims = db.records.find({
        "labels": ["Claim"],
        "where": {
            "Passage": {"$relation": {"type": "CITES", "direction": "in"}, "$id": passage.id}
        }
    })
```

### 4. Provenance Verification Query

```sdk
# Audit trail: show all evidence for a specific claim
db.records.find({
    "labels": ["Claim"],
    "where": {
        "id": claim_id,
        "Passage": {
            "Document": {"title": "..."}
        }
    }
})
```

---

## Setup

### Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://app.rushdb.com))

### Installation

```bash
# Clone the examples repository
git clone https://github.com/rush-db/examples.git
cd source-attribution-and-grounded-generation-through-usecase

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### Getting Your RushDB API Key

1. Sign up at [https://app.rushdb.com](https://app.rushdb.com)
2. Create a new project
3. Navigate to Settings → API Keys
4. Copy your API key to `.env`

### Seed the Database

This project includes a seed script that creates realistic research paper data with claims:

```bash
python seed.py
```

Expected output:
```
🌱 Seeding RushDB with research documents...
✅ Created Document: 'Attention Is All You Need'
   └─ 3 passages chunked
   └─ 2 claims extracted
✅ Created Document: 'BERT: Pre-training...'
   └─ 3 passages chunked
   └─ 2 claims extracted
✅ Created Document: 'GPT-3: Language Models...'
   └─ 3 passages chunked
   └─ 2 claims extracted
✅ Created Document: 'Chain-of-Thought Prompting...'
   └─ 3 passages chunked
   └─ 2 claims extracted
✅ Created Document: 'Retrieval-Augmented Generation...'
   └─ 3 passages chunked
   └─ 2 claims extracted
✅ Seeded 5 documents, 15 passages, 10 claims
```

---

## Running the Example

```bash
python main.py
```

### What You'll See

1. **Database Status** — Shows vector index health and record counts
2. **Q&A with Provenance** — Three example questions with full citation chains
3. **Evidence Chain Demonstration** — Shows how RushDB reconstructs the full provenance
4. **Document Update Scenario** — Demonstrates how graph handles updates (vector stores break here)
5. **Downstream Verification** — Shows auditing capabilities unique to graph+vector

---

## Expected Output

```
================================================================================
GROUNDED AI RESEARCH ASSISTANT — Source Attribution Demo
================================================================================

📊 Database Status
  • Documents: 5
  • Passages: 15 (all vectorized)
  • Claims: 10
  • Vector Index: ACTIVE (15/15 passages indexed)

================================================================================
Q&A WITH FULL PROVENANCE
================================================================================

❓ Question: "How does retrieval improve language model performance?"

📄 Retrieved Passages (vector similarity):
  [1] "RAG combines retrieval and generation..." (score: 0.94)
  [2] "Pre-training data volume correlates with model capabilities..." (score: 0.89)
  [3] "Chain-of-thought prompting improves reasoning..." (score: 0.87)

🔗 Evidence Chain (graph traversal):
  Passage [1] "RAG combines retrieval..."
    └─── SUPPORTS ───▶ Claim: "Retrieval augments LMs with external knowledge"
         Document: "Retrieval-Augmented Generation..."
    
  Passage [2] "Pre-training data volume..."
    └─── SUPPORTS ───▶ Claim: "Model scale is a key factor in capabilities"
         Document: "GPT-3: Language Models..."

✅ Assembled Answer:
  "Retrieval-augmented generation (RAG) improves language model performance 
   by combining retrieval mechanisms with generation [Claim: RAG augments LMs 
   with external knowledge, citing Passage from 'Retrieval-Augmented Generation')
   alongside insights about model scale (citing 'GPT-3' paper)."

🔍 Citation Graph:
  Answer → CITES → Claim "RAG augments LMs with external knowledge"
    └─── CITES → Passage "RAG combines retrieval..."
         └─── FROM → Document "Retrieval-Augmented Generation..."

================================================================================
EVIDENCE CHAIN AUDIT
================================================================================

Claim: "Retrieval augments LMs with external knowledge"
  • Supported by: Passage from 'Retrieval-Augmented Generation...'
  • First-order citations: 1 passage
  • Verification status: ✅ VERIFIED

================================================================================
DOCUMENT UPDATE SCENARIO
...
```

---

## Why This Beats Pure Vector Stores

### The Document Update Problem

When a document is updated:

| Pure Vector Store | RushDB |
|-------------------|--------|
| Must re-embed entire document | Just update the record |
| Old chunks remain in index | Traverse to current citations only |
| "Stale evidence" problem | Full provenance at query time |
| No relationship updates | Edges follow data |

### The Auditing Problem

When a user asks "How did you arrive at that claim?":

| Pure Vector Store | RushDB |
|-------------------|--------|
| "It seemed similar" | "Claim X cites Passage Y from Document Z" |
| No verification possible | Full audit trail queryable |
| Black box | White box |

### The Comprehensiveness Problem

When evidence spans multiple documents:

| Pure Vector Store | RushDB |
|-------------------|--------|
| Top-K similar chunks | Graph traversal finds all connected claims |
| May miss related evidence | Follows relationships across documents |
| Flat similarity | Structured reasoning |

---

## Project Structure

```
source-attribution-and-grounded-generation-through-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── seed.py             # Database seeding script
└── main.py             # Main demonstration script
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `rushdb>=2.0.0` | RushDB Python SDK — graph + vector storage |
| `sentence-transformers` | Local embeddings (no API key required) |
| `python-dotenv` | Environment variable loading |

---

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Vector Search in RushDB](https://docs.rushdb.com/features/vector-search)
- [Graph Relationships](https://docs.rushdb.com/features/relationships)
- [Transactions API](https://docs.rushdb.com/sdk/python#transactions)
- [Source Attribution Pattern Guide](https://docs.rushdb.com/guides/source-attribution)

---

## License

MIT — See [LICENSE](https://github.com/rush-db/examples/blob/main/LICENSE) in the root repository.
