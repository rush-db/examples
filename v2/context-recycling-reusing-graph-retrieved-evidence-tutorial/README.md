# Context Recycling: Reusing Graph-Retrieved Evidence Across Related Queries

This project demonstrates how to implement **context recycling** in RushDB — a pattern where graph-retrieved evidence is cached with entity-based keys and reused across related queries in the same session.

## What is Context Recycling?

In multi-turn conversations or complex query pipelines, you often retrieve the same subgraph evidence repeatedly. Context recycling caches retrieved subgraphs as "evidence units" and reuses them when the same entity patterns appear in subsequent queries.

**Benefits:**
- Reduced graph traversal overhead
- Lower latency for related queries
- Consistent context within a session
- Partial cache hits for incremental updates

## What This Tutorial Demonstrates

1. **Setup**: A property graph schema modeling a software company domain
2. **Cache Pattern**: Storing retrieved subgraph evidence with entity-based keys
3. **Smart Retrieval**: Functions that check cache before traversing the graph
4. **Partial Hits**: Handling cases where some context is fresh but not all
5. **LLM Integration**: Passing recycled context as system prompt evidence
6. **Metrics**: Measuring query latency before and after recycling

## Domain Model

```
Company (root entity)
  └── Employees (MEMBER_OF)
        ├── Works on Projects (WORKS_ON)
        └── Authors Documents (AUTHORED)
  └── Projects (HAS)
        └── Contains Documents (HAS_DOC)
```

## Prerequisites

- Python 3.10+
- A RushDB account ([sign up free](https://rushdb.com))
- OpenAI API key (for LLM integration)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your RushDB API key and OpenAI key
```

### 3. Seed the Database

This creates the company graph with employees, projects, and documents:

```bash
python seed.py
```

Expected output:
```
🌱 Seeding RushDB with company knowledge graph...
✅ Created company: TechCorp (4 employees, 3 projects, 8 documents)
✅ Seeding complete! Ready for context recycling demo.
```

### 4. Run the Demo

```bash
python main.py
```

## Project Structure

```
context-recycling-reusing-graph-retrieved-evidence-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py            # Graph data seeder
└── main.py            # Context recycling implementation
```

## How It Works

### The Cache Key Pattern

Each cached evidence unit is keyed by the entity IDs it represents:

```python
cache_key = f"evidence:{entity_type}:{entity_id}:v{cache_version}"
```

### Retrieval Flow

```
Query arrives → Check cache →
  ├─ HIT: Return cached evidence (fast path)
  ├─ PARTIAL: Merge fresh + cached (hybrid)
  └─ MISS: Traverse graph → Cache result → Return
```

### Latency Metrics

The demo measures:
- **Cold retrieval**: Full graph traversal
- **Cached retrieval**: Instant cache lookup
- **Speedup factor**: Cold / Cached ratio

## Output Example

```
🚀 Context Recycling Demo
═══════════════════════════════════════════════════════════════════════

📊 Session 1: "Tell me about the AI Platform project"
   ├─ Cache status: MISS (first query)
   ├─ Graph traversals: 5
   ├─ Evidence items: 3
   └─ Latency: 145.23ms

📊 Session 2: "What team works on it?"
   ├─ Cache status: HIT (employee context reused)
   ├─ Graph traversals: 0
   ├─ Evidence items: 3 (reused)
   └─ Latency: 0.12ms (1206x faster!)

📊 Session 3: "Has the deadline changed?"
   ├─ Cache status: PARTIAL (project updated)
   ├─ Graph traversals: 1
   ├─ Evidence items: 2 fresh + 1 stale
   └─ Latency: 23.45ms
```

## Integrating with Your LLM

Pass recycled context as system prompt evidence:

```python
# Build context from cached evidence
context = build_context_from_cache(cached_evidence)

# Send to LLM
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": f"Evidence from knowledge graph:\n{context}"},
        {"role": "user", "content": user_query}
    ]
)
```

## Extending This Pattern

- **TTL-based invalidation**: Add time-to-live for cached evidence
- **Multi-level cache**: L1 (memory) + L2 (RushDB) for hybrid caching
- **Event-driven invalidation**: Webhooks to update cache on data changes
- **Session affinity**: Stick queries to the same cache instance

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)
- [Graph Patterns in RAG Systems](https://docs.rushdb.com/docs/rag-patterns)
