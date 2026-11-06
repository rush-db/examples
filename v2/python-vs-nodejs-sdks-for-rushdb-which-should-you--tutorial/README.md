# Python vs Node.js SDKs for RushDB: Which Should You Choose?

A side-by-side comparison of RushDB's Python and TypeScript/Node.js SDKs, demonstrating feature parity, ergonomic differences, and the three most common usage patterns.

**Repository:** https://github.com/rush-db/examples/tree/main/python-vs-nodejs-sdks-for-rushdb-which-should-you--tutorial

---

## The Core Thesis

RushDB's Python and Node.js SDKs have **sufficient feature parity** that language choice should be driven by ecosystem familiarity — not capability. Both SDKs cover:

- ✅ Record CRUD (create, read, update, delete)
- ✅ Graph relationships (attach, detach, traverse)
- ✅ Vector similarity search (semantic search, vector indexing)
- ✅ Transactions (atomic writes with rollback)
- ✅ Batch operations (createMany, importCsv)

**But the SDKs have distinct ergonomic trade-offs worth understanding upfront.**

---

## Project Structure

```
.                       # Language-specific comparison
├── README.md            # This file
├── .env.example         # Environment variables template
├── python/              # Python SDK implementation
│   ├── requirements.txt
│   ├── seed.py          # Generate mock data
│   └── main.py          # All three patterns
└── typescript/          # TypeScript SDK implementation
    ├── package.json
    ├── seed.ts          # Generate mock data
    └── main.ts          # All three patterns
```

---

## Quick Start

### Prerequisites

- Node.js 18+ (for TypeScript)
- Python 3.10+ (for Python SDK)
- A RushDB account with an API key ([get one free](https://rushdb.com))

### Setup

**1. Clone and configure:**

```bash
# Clone the examples repo
git clone https://github.com/rush-db/examples.git
cd python-vs-nodejs-sdks-for-rushdb

# Copy and fill in environment variables
cp .env.example .env
```

**2. Run Python examples:**

```bash
cd python
pip install -r requirements.txt

# Seed mock data (optional — idempotent)
python seed.py

# Run the comparison
python main.py
```

**3. Run TypeScript examples:**

```bash
cd typescript
npm install

# Seed mock data (optional — idempotent)
npx tsx seed.ts

# Run the comparison
npx tsx main.ts
```

---

## What Each Pattern Demonstrates

### Pattern 1: CRUD Operations

Both SDKs create records, query with filters, update fields, and delete. The key difference is **synchronous (Python) vs asynchronous (TypeScript)**.

```sdk
# Python — synchronous, returns dict-like Record objects
movie = db.records.create(label="MOVIE", data={"title": "Inception", "rating": 8.8})
found = db.records.find({"labels": ["MOVIE"], "where": {"rating": {"$gte": 8}}})

# TypeScript — async/await, returns typed responses
const movie = await db.records.create({ label: "MOVIE", data: { title: "Inception", rating: 8.8 } })
const found = await db.records.find({ labels: ["MOVIE"], where: { rating: { $gte: 8 } } })
```

### Pattern 2: Graph Traversal

Create actors and movies, then traverse the relationship graph to find all actors in high-rated movies.

```sdk
# Python — synchronous, chain method calls
leads = db.records.find({
    "labels": ["ACTOR"],
    "where": {
        "MOVIE": {"$relation": {"type": "ACTED_IN", "direction": "out"}, "rating": {"$gte": 8}}
    }
})

# TypeScript — same structure, async/await
const leads = await db.records.find({
    labels: ["ACTOR"],
    where: {
        "MOVIE": { $relation: { type: "ACTED_IN", direction: "out" }, rating: { $gte: 8 } }
    }
})
```

### Pattern 3: Vector Similarity Search

Store article content with embeddings, then search semantically for relevant articles.

```sdk
# Python — dict responses, Python-first ecosystem alignment
db.records.create(
    label="ARTICLE",
    data={"title": "Understanding Transformers", "content": "..."},
    vectors=[{"propertyName": "content", "vector": [0.1, 0.2, ...]}]
)

results = db.ai.search({"propertyName": "content", "query": "neural network attention", "labels": ["ARTICLE"]})
for r in results.data:
    print(f"[{r.score:.3f}] {r.title}")

# TypeScript — typed responses, web framework alignment
await db.records.create({
    label: "ARTICLE",
    data: { title: "Understanding Transformers", content: "..." },
    vectors: [{ propertyName: "content", vector: [0.1, 0.2, ...] }]
})

const results = await db.ai.search({ propertyName: "content", query: "neural network attention", labels: ["ARTICLE"] })
results.data.forEach(r => console.log(`[${r.score?.toFixed(3)}] ${r.title}`))
```

---

## Ergonomic Trade-offs

| Aspect | Python SDK | TypeScript SDK |
|--------|-----------|----------------|
| **Response style** | Dict-like `Record` objects with `record.id`, `record.data`, `record.score` | Typed responses with `{ data: T[], total: number }` |
| **Async model** | Synchronous (blocking) — simpler for scripts | `async/await` — better for web servers |
| **ML/AI integration** | Native compatibility with sentence-transformers, LangChain, llama-index | Use via HTTP calls or external services |
| **Web framework integration** | Works with FastAPI/Flask but less idiomatic | Native with Next.js, Express, NestJS |
| **Type safety** | Duck-typed dicts | Full TypeScript type inference |
| **Transaction syntax** | Context manager (`with`) or manual `tx.commit()` | Always `await tx.commit()` |

---

## Why Python First?

The Python SDK is often preferred for:

- **Data pipelines** — ETL, batch processing, scheduled scripts
- **ML/AI workflows** — RAG, embeddings, model fine-tuning
- **Rapid prototyping** — faster iteration without async ceremony

Example: Using sentence-transformers with RushDB:

```python
from sentence_transformers import SentenceTransformer
from rushdb import RushDB

model = SentenceTransformer('all-MiniLM-L6-v2')
db = RushDB("API_KEY")

text = "A thriller about dreams within dreams"
embedding = model.encode(text).tolist()

db.records.create(
    label="ARTICLE",
    data={"title": "Inception Analysis", "content": text},
    vectors=[{"propertyName": "content", "vector": embedding}]
)
```

---

## Why TypeScript First?

The Node.js SDK is often preferred for:

- **Web APIs** — Next.js API routes, Express microservices
- **Real-time apps** — WebSocket integrations, live dashboards
- **Full-stack projects** — shared types between frontend/backend

Example: Next.js API route with RushDB:

```typescript
import RushDB from '@rushdb/javascript-sdk'
import { NextResponse } from 'next/server'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const query = searchParams.get('q') || ''

  const results = await db.ai.search({
    propertyName: 'content',
    query,
    labels: ['ARTICLE'],
    limit: 10
  })

  return NextResponse.json(results.data)
}
```

---

## Connection Pooling & Async Handling

Under high throughput, the SDKs behave differently:

- **Python SDK**: Synchronous — each call blocks until complete. Better for scripts with predictable, sequential operations.
- **Node.js SDK**: Async — non-blocking I/O. Better for web servers handling concurrent requests.

For typical use cases (< 100 req/s), both perform similarly. At higher loads, Node.js may have an edge due to event-loop parallelism.

---

## Environment Variables

```bash
# .env — Both Python and TypeScript use the same variable
RUSHDB_API_KEY=your_api_key_here
RUSHDB_URL=https://api.rushdb.com/api/v1  # optional, for self-hosted
```

---

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [TypeScript SDK Reference](https://docs.rushdb.com/sdk/typescript)
- [Pricing](https://rushdb.com/pricing)
