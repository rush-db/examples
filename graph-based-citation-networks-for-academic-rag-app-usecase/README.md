# Graph-Based Citation Networks for Academic RAG Applications

This project demonstrates how a **graph + vector architecture** solves the citation chain traversal problem that semantic-only retrieval cannot handle in academic RAG systems.

## The Problem

Traditional vector similarity search finds *relevant* papers but cannot answer:

> "Which papers in my literature review are *methodological ancestors* of the paper I'm evaluating?"

Semantic search tells you papers that *talk about* similar things. Citation graphs tell you which papers *inspired* or *validated* a method. A combined approach enables both **relevance** and **lineage**.

## What This Demo Shows

1. **Papers as nodes, citations as directed edges** — Citation relationships are first-class citizens, not implicit in vector space
2. **Multi-hop traversal** — Trace citation chains: paper → cites → which cites → which validates the original method
3. **Combined graph + vector queries** — Find semantically similar papers *and* their methodological ancestors in one workflow
4. **Claim provenance tracing** — Return not just similar papers, but papers that methodologically influenced the literature

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RushDB                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │   PAPERS     │◄───│   CITES      │───►│   PAPERS      │  │
│  │  (nodes)     │    │  (edges)     │    │  (nodes)      │  │
│  │              │    │              │    │               │  │
│  │ abstract_vec │    │ direction:   │    │ abstract_vec  │  │
│  │     +        │    │   outbound   │    │     +         │  │
│  │  metadata    │    │              │    │  metadata     │  │
│  └──────────────┘    └──────────────┘    └───────────────┘  │
│         │                                       │           │
│         └──────────┬────────────────────────────┘           │
│                    ▼                                        │
│         ┌─────────────────────┐                             │
│         │  Vector Index       │                             │
│         │  (on abstracts)     │                             │
│         └─────────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- A RushDB account ([sign up here](https://rushdb.com))
- API key from your RushDB workspace

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### 3. Seed the database (creates mock citation network)

```bash
python seed.py
```

This creates:
- 20 academic papers across NLP, CV, and ML domains
- Realistic citation relationships forming a citation graph
- Abstract vectors for semantic similarity search

### 4. Run the main demo

```bash
python main.py
```

## Expected Output

```
============================================================
GRAPH-BASED CITATION NETWORKS FOR ACADEMIC RAG
============================================================

--- DEMO 1: Semantic Search Only (Baseline) ---
Query: "neural network text classification"

Found 5 semantically similar papers:
  1. [0.892] BERT for Document Classification (2019)
  2. [0.847] Attention-Based Text Classification (2018)
  3. [0.834] LSTM Networks for Sequence Labeling (2017)
  4. [0.798] Transformer Architecture Survey (2020)
  5. [0.756] CNN for Text Analysis (2016)

Problem: These papers are RELEVANT but we don't know which
         VALIDATED or INSPIRED the user's research.


--- DEMO 2: Semantic Search + Citation Lineage ---
Query: "neural network text classification"

First, semantic search finds relevant papers...
Found 3 semantically similar papers:
  1. [0.892] BERT for Document Classification (2019)
  2. [0.847] Attention-Based Text Classification (2018)
  3. [0.834] LSTM Networks for Sequence Labeling (2017)

Now tracing citation lineage (methodological ancestors)...

For "BERT for Document Classification":
  This paper cites:
    • Attention Is All You Need (2017)
    • BERT: Pre-training of Deep Bidirectional Transformers (2018)

  These ancestors cite:
    • Attention Is All You Need cites:
      - Neural Machine Translation by Jointly Learning to Align (2014)
      - Sequence to Sequence Learning with Neural Networks (2014)

  METHODOLOGICAL LINEAGE (traced 2 hops):
    BERT for Document Classification (2019)
      ↓ CITES
    BERT: Pre-training of Deep Bidirectional Transformers (2018)
      ↓ CITES
    Attention Is All You Need (2017)
      ↓ CITES
    Neural Machine Translation by Jointly Learning to Align (2014)
      └── Found 2-hop ancestor!


--- DEMO 3: Find Papers That Validated/Influenced a Method ---

Query: "transformer architecture"

Relevant papers: 4 found

Tracing lineage for each to find methodological ancestors...

2-hop ancestors (key foundational papers):
  • Neural Machine Translation by Jointly Learning to Align (2014)
    [Found via: Attention Is All You Need → original attention work]
  
  • Sequence to Sequence Learning with Neural Networks (2014)
    [Found via: Attention Is All You Need → seq2seq foundations]

These papers represent the FOUNDATIONAL WORK that all
transformer papers ultimately build upon.


--- DEMO 4: Combined Query Result ---

User research: "I'm building a document classification system"

Query: "document classification neural network"

SEMANTIC RESULTS (top 3 by relevance):
  1. [0.912] BERT for Document Classification (2019)
  2. [0.856] Attention-Based Text Classification (2018)
  3. [0.823] LSTM Networks for Sequence Labeling (2017)

METHODOLOGICAL ANCESTORS (traced 2 hops):
  ┌─────────────────────────────────────────────────────┐
  │ Neural Machine Translation by Jointly Learning      │
  │ to Align and Translate (2014)                       │
  │                                                     │
  │ Why it matters: Introduced the attention mechanism   │
  │ that BERT and all transformer models build upon.     │
  └─────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────┐
  │ Word2Vec: Distributed Representations of Words       │
  │ and Phrases and their Compositionality (2013)       │
  │                                                     │
  │ Why it matters: Pioneered dense embeddings that     │
  │ enable pre-training strategies.                     │
  └─────────────────────────────────────────────────────┘

TOTAL: 3 semantic results + 2 key ancestors = 5 papers
        with proven methodological lineage

============================================================
KEY INSIGHT:
============================================================

Vector similarity alone returns RELEVANT papers.

Graph traversal alone returns INFLUENCED papers.

Combined graph+vector returns RELEVANT papers
THAT YOU CAN TRACE to their methodological roots.

This enables academic RAG that answers:
  "Show me papers like X, and trace back which
   foundational works they ultimately derive from."

============================================================

✅ All demos completed successfully!
```

## Project Structure

```
graph-based-citation-networks-for-academic-rag-app-usecase/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Generate mock citation network
└── main.py            # Main demo script
```

## How It Works

### Data Model

| Node/Edge | Properties |
|-----------|------------|
| **PAPER** | title, abstract, year, authors, venue |
| **CITES** | (directed edge from citing paper → cited paper) |

### Query Pattern

```python
# 1. Semantic search: find relevant papers
similar = db.ai.search({
    "propertyName": "abstract",
    "query": "neural network text classification",
    "labels": ["PAPER"],
    "limit": 5
})

# 2. For each relevant paper, traverse citation edges (outbound)
for paper in similar:
    citing = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "out"},
                "$id": paper.id
            }
        }
    })
    # ... continue tracing upstream
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdk/python)
- [Property Graphs for RAG](https://docs.rushdb.com)

## License

MIT