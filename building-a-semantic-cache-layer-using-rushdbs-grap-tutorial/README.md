# Building a Semantic Cache Layer Using RushDB's Graph Storage

A complete, runnable tutorial demonstrating how to build a semantic cache from scratch with RushDB — covering embedding generation, node storage, graph edge creation, and retrieval-by-similarity with real code.

## What You'll Build

A production-ready semantic cache that:

- **Stores LLM query/response pairs** with semantic embeddings
- **Uses RushDB's graph** to link related cache entries by topic/context
- **Retrieves similar entries** via vector similarity search
- **Handles invalidation** via TTL (time-to-live) and contextual pruning

## Architecture Overview

```
┌──────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Incoming    │────▶│  Semantic   │────▶│   Cache Hit?    │
│  Query       │     │  Search     │     │                 │
└──────────────┘     └─────────────┘     └────────┬────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
                    ▼                             ▼                             ▼
            ┌───────────────┐             ┌───────────────┐             ┌───────────────┐
            │     YES       │             │      NO       │             │  No Match     │
            │  Return Cached │             │ Generate New  │             │  Generate New │
            │    Response   │             │  Embedding    │             │    + Link     │
            └───────────────┘             └───────────────┘             └───────────────┘
                    │                             │                             │
                    ▼                             ▼                             ▼
            ┌─────────────────────────────────────────────────────────────────────────┐
            │                      RushDB Graph Storage                               │
            │  ┌─────────┐      SEMANTICALLY_SIMILAR      ┌─────────┐                 │
            │  │CacheEntry│◀────────────────────────────▶│CacheEntry│                 │
            │  │  (query) │                              │  (query) │                 │
            │  └─────────┘                              └─────────┘                 │
            └─────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://rushdb.com))
- OpenAI API key (for embeddings) — or use local model alternative

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

### 3. Create the Vector Index

Before running, you need to create a vector index on RushDB for semantic search. Run:

```bash
python setup_index.py
```

### 4. Seed Mock Data (Optional)

```bash
python seed.py
```

This creates 20 sample cache entries representing common LLM queries about software development topics.

### 5. Run the Tutorial

```bash
python main.py
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── setup_index.py      # Creates the vector index on RushDB
├── seed.py             # Generates mock cache entries
├── main.py             # Main tutorial implementation
└── data/
    └── sample_queries.json  # Sample queries for seeding
```

## What the Code Demonstrates

### 1. Schema Definition

Cache entries use the `CacheEntry` label with these fields:

- `query_text`: The original user query (vectorized)
- `response_text`: The cached LLM response
- `created_at`: Timestamp for TTL validation
- `ttl_seconds`: Time-to-live for this entry
- `model`: Which LLM model generated the response
- `tokens_used`: Token count for cost tracking
- `context_tags`: Topic tags for filtering

### 2. Embedding Generation

```sdk
# Using OpenAI (set USE_OPENAI=True in main.py)
embedding = generate_embedding(query_text, openai_client)

# Or using local model (SentenceTransformers)
embedding = generate_embedding_local(query_text)
```

### 3. Storing Entries with Vectors

```sdk
# Create a cache entry with an inline vector
cache_entry = db.records.create(
    label="CacheEntry",
    data={
        "query_text": query_text,
        "response_text": response_text,
        "created_at": datetime.now().isoformat(),
        "ttl_seconds": 3600,
        "model": "gpt-4",
        "tokens_used": 500,
        "context_tags": ["python", "tutorial"]
    },
    vectors=[{"propertyName": "query_text", "vector": embedding}]
)
```

### 4. Graph Edge Creation

When storing a new entry, we link it to semantically similar existing entries:

```sdk
# Find similar entries
similar = db.ai.search({
    "propertyName": "query_text",
    "queryVector": embedding,
    "labels": ["CacheEntry"],
    "limit": 5
}).data

# Link new entry to each similar entry
for similar_entry in similar:
    if similar_entry.score >= similarity_threshold:
        db.records.attach(
            source=new_entry,
            target=similar_entry,
            options={"type": "SEMANTICALLY_SIMILAR"}
        )
```

### 5. Cache Hit Detection

```sdk
# Search for cached entry
results = db.ai.search({
    "propertyName": "query_text",
    "queryVector": embedding,
    "labels": ["CacheEntry"],
    "limit": 10
}).data

for result in results:
    if result.score >= 0.95:  # High confidence match
        # Check TTL
        ttl = int(result.data.get("ttl_seconds", 3600))
        created = datetime.fromisoformat(result.data["created_at"])
        if datetime.now() - created < timedelta(seconds=ttl):
            return result  # Cache hit!
```

### 6. Contextual Invalidation via Edge Pruning

```sdk
def invalidate_related_entries(source_entry, context_tag: str):
    """Remove edges to entries with different context tags."""
    related = db.records.find({
        "labels": ["CacheEntry"],
        "where": {
            "CacheEntry": {
                "$relation": {"type": "SEMANTICALLY_SIMILAR", "direction": "out"},
                "$id": source_entry.id
            }
        }
    })
    
    for related_entry in related:
        tags = related_entry.data.get("context_tags", [])
        if context_tag not in tags:
            # Prune the edge — entries are contextually incompatible
            db.records.detach(
                source=source_entry,
                target=related_entry,
                options={"type": "SEMANTICALLY_SIMILAR"}
            )
```

## Expected Output

```
╔══════════════════════════════════════════════════════════════╗
║     Building a Semantic Cache Layer with RushDB              ║
╚══════════════════════════════════════════════════════════════╝

--- Initializing Semantic Cache ---
[✓] RushDB connection established
[✓] Vector index ready
[✓] 20 existing cache entries found

--- Cache Lookup Demo ---

[1] Testing query: "How do I implement a Python decorator?"
    ↳ Searching for similar cached entries...
    ↳ Cache HIT! Found: "Explain Python decorators with examples"
       Similarity: 0.97
       Model: gpt-4 | Tokens: 350 | Age: 45 minutes

[2] Testing query: "What is the best way to handle async errors in Python?"
    ↳ Searching for similar cached entries...
    ↳ Cache MISS - No similar entry found
    ↳ Storing new cache entry...
    ↳ Linked to 2 semantically similar entries

[3] Testing query: "Help me debug this code: for i in range(10): print i"
    ↳ Searching for similar cached entries...
    ↳ Cache HIT! Found: "Fix Python 2 vs 3 print syntax issues"
       Similarity: 0.88
       Model: gpt-3.5-turbo | Tokens: 280 | Age: 2 hours

--- Invalidation Demo ---

[1] TTL Invalidation:
    ↳ Found 3 entries older than their TTL
    ↳ Removed: 'old_entry_1', 'old_entry_2'

[2] Context Pruning:
    ↳ After updating context_tag for entry 'python_async'...
    ↳ Pruned 4 invalid edges to contextually incompatible entries

--- Graph Statistics ---
Total CacheEntries: 21
Total SEMANTICALLY_SIMILAR edges: 42
Average similarity threshold: 0.85
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Vector Embedding** | Numeric representation of text capturing semantic meaning |
| **Semantic Search** | Finding entries by meaning, not exact keyword match |
| **Graph Edges** | Relationships between cache entries by topic similarity |
| **TTL** | Time-to-live; automatic expiry based on staleness |
| **Edge Pruning** | Removing invalid relationships based on context changes |

## Extension Ideas

1. **Cost Tracking**: Add token counting to estimate LLM cost savings
2. **Multi-model Support**: Cache responses from different models separately
3. **Warm-up Mode**: Pre-populate cache with common queries
4. **Adaptive TTL**: Longer TTL for stable topics, shorter for rapidly changing ones
5. **Contextual Clustering**: Group entries by conversation/session context

## Resources

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB SDK Reference](https://docs.rushdb.com/sdk/python)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-a-semantic-cache-layer-using-rushdbs-grap-tutorial)
