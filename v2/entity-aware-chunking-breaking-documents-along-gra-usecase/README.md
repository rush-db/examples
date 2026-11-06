# Entity-Aware Chunking: Breaking Documents Along Graph-Relationship Boundaries

## What This Demo Shows

Traditional RAG chunks documents at fixed token boundaries (512–1024 chars). This severs
cross-document references: when a function in `auth.py` calls a helper in `utils.py`,
the vector index returns two disconnected chunks. Questions like *"how does the auth
token flow from login to database?"* cannot be answered from a paragraph.

**Entity-aware chunking** breaks documents along semantic boundaries — functions, classes,
API endpoints, config keys — and explicitly records their relationships (calls, imports,
config dependencies, env var references). The graph preserves the traversal path that
naive chunking destroys.

This project demonstrates:
1. **Indexing** a mock code repository as typed entities + relationships in RushDB
2. **Graph traversal** answering multi-hop questions
3. **Vector-only search** failing the same questions (to show the contrast)
4. **Hybrid retrieval** combining both approaches

---

## Repository Structure

```
entity-aware-chunking-breaking-documents-along-gra-usecase/
├── seed.py           # Generate and load mock code base
├── main.py           # Run the full comparison demo
├── requirements.txt
└── .env.example
```

---

## Setup

```bash
# 1. Clone the examples repo
git clone https://github.com/rush-db/examples.git
cd examples/entity-aware-chunking-breaking-documents-along-gra-usecase

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate     # Linux/macOS
# venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure RushDB
cp .env.example .env
# Edit .env and set RUSHDB_API_KEY and RUSHDB_URL (if self-hosted)

# 5. Seed the database (generates ~30 entities + relationships)
python seed.py
```

---

## Running the Demo

```bash
python main.py
```

Expected output:
- Progress bars for each indexing phase
- Section-by-section comparison: graph vs vector for each query
- A final "why graph wins" summary

---

## Queries Demonstrated

| Query | Why Naive Chunking Fails | Why Graph Works |
|---|---|---|
| "authentication flow from login to DB" | Token chunks split `login_user()` from its `DBQuery` dependency | Relationship traversal follows CALLS edges |
| "how does JWT get validated" | A paragraph on JWT is detached from the config key that controls its algorithm | `TokenValidator` → CONFIGS → `JWT_ALGORITHM` path |
| "trace the environment variables" | ENV_REF edges only exist in the graph, not in any paragraph | `get_user_settings()` → ENV_REFS → `DATABASE_URL` |

---

## Prerequisites

- Python 3.10+
- RushDB account (free tier works) — https://rushdb.com
- `rushdb>=2.0.0` (see `requirements.txt`)
- `sentence-transformers` for embedding generation

---

## Embedding Model

We use `sentence-transformers/all-MiniLM-L6-v2` (384-dim) because it is:
- Fast enough for demo purposes (< 100ms per embed on CPU)
- Good general-purpose performance on code and technical text
- Publicly available with no API key required

For production, consider `nomic-ai/Nomic-embed-text-v1.5` or OpenAI `text-embedding-3-small`.
