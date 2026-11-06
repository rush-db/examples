# Zero-to-Knowledge-Graph: Ingesting Unstructured Documents with RushDB

A complete walkthrough of ingesting a messy document corpus — PDFs, nested JSON, unstructured notes — and immediately querying it with both semantic similarity and multi-hop graph traversal.

## What This Demo Proves

RushDB is purpose-built for the document-to-knowledge-graph pipeline:
- **No second database** — records, vectors, and graph edges all live in RushDB
- **No custom relationship mapping layer** — `attach()` wires entities together
- **No Cypher required** — use `find()` with relationship filtering instead
- **Inline vector writes** — embed vectors at create/upsert time, no separate index step

## Project Structure

```
zero-to-knowledge-graph-ingesting-unstructured-doc-usecase/
├── seed.py          # Generates the mock document corpus
├── main.py          # End-to-end ingestion + querying pipeline
├── requirements.txt # Python dependencies
└── .env.example     # Environment variable template
```

## Prerequisites

- Python 3.10+
- A RushDB account ([get free API key](https://app.rushdb.com))
- `sentence-transformers` for local embeddings (no OpenAI key needed)

## Setup

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd zero-to-knowledge-graph-ingesting-unstructured-doc-usecase

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running

**Step 1: Seed the document corpus**

```bash
python seed.py
```

This generates 12 realistic documents across 3 types (technical articles, meeting notes, data specs) and loads them into RushDB. Safe to run multiple times — checks for existing data before seeding.

**Step 2: Run the full pipeline**

```bash
python main.py
```

The script executes in 5 phases:

| Phase | What It Does |
|-------|-------------|
| 1. Ingest | Loads documents, chunks them, creates entities, wires relationships |
| 2. Vector Index | Creates a managed index on `DOCUMENT.content` |
| 3. Semantic Search | Finds contextually similar document chunks |
| 4. Graph Traversal | Follows entity relationships across documents |
| 5. Reindex Demo | Updates a chunk's content + vectors in-place |

## Expected Output

```
=== PHASE 1: Ingesting Document Corpus ===
  ✓ Created SOURCE: 'research-papers-2024'
  ✓ Created SOURCE: 'team-meetings'
  ✓ Created SOURCE: 'data-specs'
  ✓ Created 12 DOCUMENT records (4 articles, 4 notes, 4 specs)
  ✓ Created 9 ENTITY records (3 people, 3 companies, 3 topics)
  ✓ Created 21 RELATIONSHIP edges

=== PHASE 2: Vector Index ===
  ✓ Created managed index on DOCUMENT.content (model: rushdb-embed-768)
  ✓ Waiting for initial indexing (10s)...
  ✓ Index stats: 12/12 records indexed

=== PHASE 3: Semantic Search ===
Query: "distributed systems consensus"
  [0.94] DOC-7: "...Paxos consensus algorithm forms the backbone..."
  [0.89] DOC-3: "...Raft was designed as a more understandable alternative..."
  [0.82] DOC-11: "...Chubby lock service uses Paxos internally..."

=== PHASE 4: Graph Traversal ===
Starting from ENTITY 'Dr. Sarah Chen':
  AUTHORED → DOC-1 (chunk 1)
    MENTIONS → Ent: Machine Learning Systems Inc.
    MENTIONS → Ent: transformer architectures
  AUTHORED → DOC-1 (chunk 2)
    MENTIONS → Ent: NLP research trends

=== PHASE 5: Reindex Demo ===
  Before: "Paxos is a family of protocols..."
  ✓ Updated DOC-7 with new content and fresh vectors
  After: "Paxos is a family of protocols for value agreement..."

=== ALL PHASES COMPLETE ===
```

## Key API Patterns Demonstrated

### Inline Vector Writes

```sdk
db.records.create(
    label="DOCUMENT",
    data={"content": "...", "source": "research-papers-2024"},
    vectors=[{"propertyName": "content", "vector": embedding}]
)
___SPLIT___
// Not directly supported in TS; use managed indexes instead
```

### Semantic Search

```sdk
results = db.ai.search({
    "propertyName": "content",
    "query": "distributed systems consensus",
    "labels": ["DOCUMENT"],
    "limit": 5
})
___SPLIT___
const { data: results } = await db.ai.search({
    propertyName: 'content',
    query: 'distributed systems consensus',
    labels: ['DOCUMENT'],
    limit: 5
})
```

### Graph Traversal via Relationship Filtering

```sdk
db.records.find({
    "labels": ["DOCUMENT"],
    "where": {
        "ENTITY": {"$relation": {"type": "AUTHORED", "direction": "in"}},
        "AUTHORED_BY": {"name": "Dr. Sarah Chen"}
    }
})
___SPLIT___
// TypeScript equivalent uses same query structure
const { data } = await db.records.find({
    labels: ['DOCUMENT'],
    where: {
        'ENTITY': {
            $relation: { type: 'AUTHORED', direction: 'in' }
        },
        'AUTHORED_BY': { name: 'Dr. Sarah Chen' }
    }
})
```

## Why This Matters

Traditional document pipelines require:
1. A document store (S3, MongoDB, etc.)
2. A vector database (Pinecone, Weaviate, etc.)
3. A graph database (Neo4j, etc.)
4. Custom sync logic between all three

**RushDB eliminates all four** — you get documents, vectors, and graph traversal in a single API call, with zero schema setup.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [Semantic Search Guide](https://docs.rushdb.com/features/vector-search)
- [Graph Relationships](https://docs.rushdb.com/features/relationships)
