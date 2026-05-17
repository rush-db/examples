# Building a Production RAG Pipeline with RushDB: A Complete Walkthrough

**Use Case:** Internal Policy Q&A — where multi-hop relationships determine the answer

## What This Demo Shows

This project demonstrates a real production challenge: building a RAG pipeline over internal company policies where the answer depends on **entity relationships**, not just document similarity.

**The problem:** A pure vector store can find relevant documents, but cannot answer:
> "What policies does the HR team handle, and how do they relate to the remote work policy?"

This requires traversing: `Policy → Author → Team → Related Policies`.

**RushDB's solution:** A single query that combines semantic search with graph traversal, returning answers in one round-trip.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RushDB (Neo4j-backed)                       │
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐ │
│  │ Policy  │───▶│ Author  │───▶│  Team   │◀───│ Related     │ │
│  │(vector) │    │         │    │         │    │ Policy      │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────────┘ │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────┐                                        │
│  │ Semantic Search │ ◀── Vector Index on 'body' field        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Scenario: Internal Policy Q&A

We model a small company's policy knowledge base:
- **5 policies** covering HR, IT, Finance topics
- **4 authors** with team affiliations
- **3 teams**: HR, Engineering, Finance
- **Cross-references** between related policies

### Sample Queries

| Query | What It Tests |
|-------|---------------|
| "remote work guidelines" | Pure semantic search (vector similarity) |
| "policies authored by the HR team" | Graph traversal + filtering |
| "policies related to the remote work policy authored by HR" | Multi-hop: Policy → Author → Team → Related Policy |

## Project Structure

```
building-a-production-rag-pipeline-with-rushdb-a-c-usecase/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   └── policies.json          # Seed data (policies, authors, teams)
├── seed.py                    # Load data into RushDB
└── main.py                    # RAG pipeline with queries + comparison
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `RUSHDB_API_KEY` — Your RushDB API key (get one at https://dash.rushdb.com)
- `RUSHDB_URL` — Your RushDB instance URL (optional, defaults to cloud)

### 3. Seed the Database

```bash
python seed.py
```

This will:
- Create 5 Policy records with embedded body text
- Create 4 Author records with names and roles
- Create 3 Team records
- Establish relationships: Policy → Author (WRITTEN_BY), Author → Team (MEMBER_OF)
- Link related policies via CROSS_REFERENCES relationships
- Create a vector index on the Policy `body` field for semantic search

Expected output:
```
✅ Seeding complete!
   - 5 Policies created
   - 4 Authors created
   - 3 Teams created
   - 9 Relationships established
   - Vector index created on Policy.body
```

### 4. Run the Demo

```bash
python main.py
```

## What You'll See

### Query 1: Pure Semantic Search

```
📌 Query: "remote work guidelines"

🎯 Results (vector similarity only):
   [0.923] Remote Work Policy — HR
   [0.784] IT Equipment Guidelines — IT
   [0.612] Travel Expense Policy — Finance

   ℹ️  Found the policy, but no context about author/team
```

### Query 2: Graph-Traversed Search

```
📌 Query: "policies authored by the HR team"

🎯 Results (graph traversal + vector search):
   ✅ Remote Work Policy — by Sarah Chen (HR Team)
   ✅ Performance Review Process — by Sarah Chen (HR Team)

   ℹ️  RushDB traversed Author → Team in a single query
```

### Query 3: Multi-Hop Retrieval (The Hard Part)

```
📌 Query: "policies related to remote work authored by HR"

🎯 Results (multi-hop graph traversal):
   ✅ Remote Work Policy (HR) — related to: [Performance Review Process, Equipment Policy]
   ✅ Performance Review Process (HR) — related to: [Remote Work Policy]

   ℹ️  RushDB handled 3 relationship hops in one query:
       Policy → Author → Team → Related Policy
```

## Latency Comparison

After the queries, the demo prints a comparison showing why RushDB's unified approach matters:

```
╔══════════════════════════════════════════════════════════════════════╗
║                     COMPLEXITY COMPARISON                           ║
╠══════════════════════════════════════════════════════════════════════╣
║  Query: "policies related to remote work authored by HR"             ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  PURE VECTOR STORE (Pinecone / Qdrant) + EXTERNAL GRAPH DB:            ║
║  ─────────────────────────────────────────────────────               ║
║  Step 1: Vector search → get policy IDs                        ~80ms  ║
║  Step 2: Query graph DB for authors                            ~60ms  ║
║  Step 3: Filter by team                                         ~40ms  ║
║  Step 4: Query graph DB for related policies                   ~60ms  ║
║  Step 5: Merge and deduplicate results                          ~20ms  ║
║  ─────────────────────────────────────────────────────               ║
║  TOTAL: 5 round-trips, ~260ms, complex client logic                      ║
║                                                                          ║
║  RUSHDB (UNIFIED GRAPH + VECTOR):                                      ║
║  ─────────────────────────────────────────────────────               ║
║  Single query with graph traversal + vector search             ~90ms  ║
║  ─────────────────────────────────────────────────────               ║
║  TOTAL: 1 round-trip, ~90ms, zero client-side graph logic             ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════╝
```

## How RushDB Handles Multi-Hop Queries

### The Secret: Relationship Filtering in `where`

RushDB lets you filter records by properties of related records using the **label as the key**:

```sdk
# Find all Policies where the Author belongs to the HR team
policies = db.records.find({
    "labels": ["POLICY"],
    "where": {
        "AUTHOR": {
            "$relation": {"type": "WRITTEN_BY", "direction": "in"},
            "TEAM": {"$relation": {"type": "MEMBER_OF", "direction": "in"},
            "name": "HR"
        }
    }
})
___SPLIT___
// Find all Policies where the Author belongs to the HR team
const policies = await db.records.find({
    labels: ['POLICY'],
    where: {
        AUTHOR: {
            $relation: { type: 'WRITTEN_BY', direction: 'in' },
            TEAM: {
                $relation: { type: 'MEMBER_OF', direction: 'in' },
                name: 'HR'
            }
        }
    }
})
```

This replaces what would be multiple Cypher queries or separate API calls in a traditional architecture.

## When to Use Graph+Vector RAG

| Use Case | Pure Vector | Graph+Vector (RushDB) |
|----------|-------------|----------------------|
| Unstructured docs (articles, books) | ✅ Best fit | Overkill |
| Q&A over structured KB (policies, SOPs) | ❌ Loses context | ✅ Optimal |
| Queries with "related to X" semantics | ❌ Requires app-layer logic | ✅ Native support |
| Entity-centric retrieval (authors, teams) | ❌ Loses relationships | ✅ First-class |

## Requirements

- Python 3.9+
- RushDB account (https://dash.rushdb.com)
- `rushdb>=2.0.0`
- `sentence-transformers` for embeddings (using `all-MiniLM-L6-v2`)
- `python-dotenv` for environment management

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdk/python)
- [Graph+Vector RAG Patterns](https://docs.rushdb.com/patterns)

## Related Examples

- [Semantic Search with RushDB](../semantic-search-rushdb/) — foundational vector search
- [Graph Analytics Walkthrough](../graph-analytics-with-rushdb/) — relationship traversal
- [Multi-Model Data Ingestion](../multi-model-data-ingestion/) — mixed data types
