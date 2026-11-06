# Embedding Caching Strategies for Frequently Accessed Vectors

A practical tutorial demonstrating how to implement effective caching strategies for vector embeddings using RushDB. This project shows senior engineers how to optimize vector search performance and reduce embedding generation costs through intelligent caching.

## What This Project Demonstrates

- **LRU Cache** — In-memory cache for recently accessed vectors with configurable size limits
- **Batch Pre-computation** — Pre-generate embeddings for frequently queried items
- **Cache Warming** — Load popular vectors on startup to avoid cold starts
- **Hybrid Caching** — Combine RushDB's persistence with in-memory caching for best performance
- **Cache Statistics** — Monitor hit/miss rates and optimize cache parameters

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Client Query   │────▶│   Cache Layer    │────▶│  RushDB Search  │
│                 │     │  (LRU + Stats)   │     │  (Vector Index) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ Embedding Model  │
                    │ (sentence-trans) │
                    └──────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB API key (get one at https://app.rushdb.com)
- `sentence-transformers` for embedding generation

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Seed the database (creates vector index and sample articles):**
   ```bash
   python seed.py
   ```
   This will:
   - Create a `ARTICLE` vector index on the `content` property (384 dimensions)
   - Generate and store embeddings for 20 sample articles
   - Takes ~30 seconds depending on embedding model download time

4. **Run the caching demo:**
   ```bash
   python main.py
   ```

## Project Structure

```
embedding-caching-strategies/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── data/
│   └── articles.json   # Sample article data (20 articles)
├── seed.py            # Database seeding script
└── main.py            # Main caching demonstration
```

## How It Works

### 1. LRU Cache with Statistics

The `VectorCache` class wraps RushDB's vector search with an LRU cache:

```sdk
cache = VectorCache(
    db=db,
    index_id=index_id,
    max_size=100,      # Maximum cached vectors
    ttl_seconds=3600   # Time-to-live for cache entries
)

# First call - cache miss, generates embedding (5 KU)
result = cache.search("machine learning", limit=5)

# Second call - cache hit, no RushDB call needed
result = cache.search("machine learning", limit=5)
```

### 2. Batch Pre-computation

Pre-generate embeddings for known popular queries:

```sdk
popular_queries = [
    "machine learning",
    "neural networks",
    "data science"
]

cache.batch_precompute(popular_queries)
```

### 3. Cache Warming

Load frequently accessed vectors on application startup:

```sdk
# Warm cache with top 50 most-accessed articles
cache.warm(
    record_ids=[article.id for article in top_articles],
    embeddings=precomputed_embeddings
)
```

## Expected Output

```
=== RushDB Vector Caching Demo ===

[1] Creating fresh database state...
    ✓ Deleted existing articles
    ✓ Created 20 articles with content
    ✓ Created vector index (external, 384 dimensions)
    ✓ Generated embeddings for all articles

[2] Initializing LRU cache (max_size=50)...
    ✓ Cache ready

[3] Testing cache behavior...

    Query: "neural networks"
    Cache miss → generating embedding... done in 0.12s
    Searched 20 records, found 5 results
    
    Query: "neural networks" (again)
    Cache hit ✓ (0.0002s)
    
    Query: "machine learning"
    Cache miss → generating embedding... done in 0.11s
    Searched 20 records, found 5 results

[4] Running batch pre-computation...
    Pre-computing 10 popular queries...
    ✓ Done in 1.2s

[5] Cache statistics after warm-up:
    Hits: 7  |  Misses: 5  |  Hit Rate: 58.3%
    Storage: 17 vectors | Size: 6.5 KB

[6] Testing edge cases...
    ✓ Empty query handling
    ✓ Very long query truncation
    ✓ Invalid cache entry recovery

=== Demo Complete ===
```

## KU Costs (RushDB Pricing)

| Operation | Cost |
|-----------|------|
| Vector index creation | Free |
| Embedding generation (via search) | 5 KU/record |
| Vector search query | 5 KU/call |
| **Cache hit** | **Free** |

By caching frequently accessed vectors, you can significantly reduce KU consumption for high-traffic applications.

## Customization

### Adjust Cache Size
```python
cache = VectorCache(db, index_id, max_size=200)  # Larger cache
cache = VectorCache(db, index_id, max_size=10)   # Smaller cache
```

### Use Different Embedding Model
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # Smaller, faster
model = SentenceTransformer(' paraphrase-mpnet-base-v2')  # Larger, more accurate
```

### Add Custom Cache Eviction Logic
```python
class PriorityCache(VectorCache):
    def _evict(self):
        # Evict based on access frequency + recency
        # instead of simple LRU
        pass
```

## Further Reading

- [RushDB Vector Search Documentation](https://docs.rushdb.com/features/vector-search)
- [RushDB AI & Embedding Features](https://docs.rushdb.com/features/ai-embeddings)
- [Sentence Transformers Documentation](https://www.sbert.net/)

## License

MIT