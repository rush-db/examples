# Entity-Aware Chunking with RushDB

**Demo repo:** https://github.com/rush-db/examples/tree/main/entity-aware-chunking-breaking-documents-along-gra-tutorial

A runnable comparison of two RAG retrieval strategies:

| Strategy | Unit of storage | Boundary logic |
|---|---|---|
| **Token-based** | Fixed-size window | Character/token count — splits mid-sentence |
| **Entity-aware** | Graph node + its edges | Semantic: a person, company, or event as one unit |

This tutorial shows how RushDB's property-graph model makes entity-aware chunking a natural
write pattern — no external NLP pipeline required. You define entity types via labels, write
documents as structured nodes, then query across entity boundaries via graph traversal.

---

## What it demonstrates

1. **Schema definition** — Entity labels (`COMPANY`, `PRODUCT`, `PERSON`) are just RushDB record
   labels. No migration, no schema registry.
2. **Document ingestion** — Raw article text stored as-is on one record. Simultaneously, named
   entities are extracted inline and written as separate linked nodes.
3. **Dual indexing** — Both the article body and each entity's description get a vector index.
4. **Side-by-side search** — Run the same semantic query against token-chunks and entity-chunks,
   print top results with similarity scores and a quality verdict.
5. **Graph traversal** — Show that entity nodes can be queried by their relationship to other
   entities (e.g., "all companies that produced a product mentioned in an article about X").

---

## Prerequisites

- Python 3.10+
- A RushDB account (Free tier works)
- `pip install -r requirements.txt`

---

## Setup

### 1. Copy env and fill in your credentials

```bash
cp .env.example .env
```

Edit `.env`:
```
RUSHDB_TOKEN=your_token_here
```

Get your token from https://app.rushdb.com → Settings → API Keys.

### 2. (Optional) Reset the project

If you want a clean slate, run:

```bash
python seed.py --reset
```

This deletes all `DOCUMENT`, `ENTITY`, `PERSON`, `COMPANY`, `PRODUCT`, `CHUNK` records
before re-seeding.

### 3. Seed mock data

```bash
python seed.py
```

Seeds 15 short tech news articles with inline entity extraction. Takes ~10–20 seconds.
Progress printed every 100 records.

### 4. Run the comparison

```bash
python main.py
```

Two indexed searches are executed:

- **Query 1** — `"What happened with AI chips and performance benchmarks?"`
- **Query 2** — `"Regulatory issues affecting big tech companies"`

For each, results from token-chunks and entity-chunks are printed side by side,
with score breakdown and a short human verdict.

---

## Project structure

```
entity-aware-chunking-breaking-documents-along-gra-tutorial/
├── README.md          ← you are here
├── requirements.txt
├── .env.example
├── seed.py            ← generates mock articles + entity extraction
├── main.py            ← dual search comparison + graph traversal demo
└── data/
    └── articles.json  ← 15 raw articles with inline entity metadata
```

---

## How entity-aware chunking works in RushDB

Traditional token chunking produces arbitrary splits:

```
[Article about AI chips... | ...company reports record...] ← broken mid-sentence
[...results...]                 ← lost context at boundary
```

RushDB stores entities as first-class nodes with relationships:

```
DOCUMENT ──HAS_ENTITY──► COMPANY "Nvidia"
DOCUMENT ──HAS_ENTITY──► PRODUCT "H100"
COMPANY "Nvidia" ──COMPETES_WITH──► COMPANY "AMD"
PRODUCT  "H100"  ──PRODUCED_BY──► COMPANY "Nvidia"
```

A semantic query against entity-chunks returns the COMPANY or PRODUCT node itself,
not a broken window. The document body is still available for context retrieval via
graph traversal (e.g., follow `HAS_ENTITY` → `PRODUCED_BY` → up to the source document).
