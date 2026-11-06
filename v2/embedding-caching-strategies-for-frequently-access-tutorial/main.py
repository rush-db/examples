#!/usr/bin/env python3
"""
RushDB Embedding Caching Strategies Demo

This script demonstrates various caching strategies for vector embeddings:
1. LRU cache with configurable size and TTL
2. Batch pre-computation for popular queries
3. Cache warming on startup
4. Statistics tracking for cache optimization

Each strategy reduces embedding generation costs and improves search latency.
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from cachetools import LRUCache

# Import RushDB
from rushdb import RushDB

# Load environment variables
load_dotenv()


@dataclass
class CacheStats:
    """Tracks cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_query_time: float = 0.0
    cache_storage_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": f"{self.hit_rate:.1f}%",
            "avg_query_ms": (self.total_query_time / (self.hits + self.misses) * 1000) if (self.hits + self.misses) > 0 else 0,
            "storage_kb": self.cache_storage_bytes / 1024
        }


@dataclass
class CacheEntry:
    """Represents a cached vector with metadata."""
    vector: List[float]
    created_at: float
    last_accessed: float
    access_count: int = 0
    query_hash: str = ""
    
    def touch(self):
        """Update access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1


class VectorCache:
    """
    LRU cache wrapper for RushDB vector search.
    
    This cache stores computed query embeddings to avoid re-computation
    on repeated searches. It's designed to reduce latency and API costs
    for frequently-accessed vectors.
    """
    
    def __init__(
        self,
        db: RushDB,
        index_id: str,
        max_size: int = 100,
        ttl_seconds: Optional[float] = None
    ):
        self.db = db
        self.index_id = index_id
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
        # LRU cache for vectors
        self._cache: Dict[str, CacheEntry] = {}
        
        # Statistics
        self.stats = CacheStats()
        
        # Embedding model for cache misses
        self._model = None
        
        # Pre-warmed items
        self._pre_warmed: int = 0
    
    @property
    def model(self):
        """Lazy-load the embedding model."""
        if self._model is None:
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model
    
    def _compute_hash(self, query: str) -> str:
        """Generate a deterministic hash for a query."""
        normalized = query.lower().strip()[:500]
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        return time.time() - entry.created_at > self.ttl_seconds
    
    def _evict(self) -> None:
        """Remove least recently used entries when cache is full."""
        while len(self._cache) >= self.max_size:
            # Find LRU entry
            lru_key = None
            lru_time = float('inf')
            
            for key, entry in self._cache.items():
                if entry.last_accessed < lru_time:
                    lru_time = entry.last_accessed
                    lru_key = key
            
            if lru_key:
                del self._cache[lru_key]
                self.stats.evictions += 1
    
    def _generate_embedding(self, query: str) -> List[float]:
        """Generate embedding for a query string."""
        return self.model.encode(
            query,
            normalize_embeddings=True
        ).tolist()
    
    def get_or_compute(self, query: str) -> List[float]:
        """
        Get cached vector or compute and store a new one.
        
        Args:
            query: The search query string
            
        Returns:
            The embedding vector
        """
        query_hash = self._compute_hash(query)
        
        # Check cache
        if query_hash in self._cache:
            entry = self._cache[query_hash]
            
            # Check expiration
            if self._is_expired(entry):
                del self._cache[query_hash]
            else:
                entry.touch()
                self.stats.hits += 1
                self.stats.cache_storage_bytes = sum(
                    len(str(e.vector)) for e in self._cache.values()
                )
                return entry.vector
        
        # Cache miss - compute embedding
        self.stats.misses += 1
        vector = self._generate_embedding(query)
        
        # Store in cache
        self._evict()
        self._cache[query_hash] = CacheEntry(
            vector=vector,
            created_at=time.time(),
            last_accessed=time.time(),
            query_hash=query_hash
        )
        
        return vector
    
    def search(
        self,
        query: str,
        labels: Optional[List[str]] = None,
        where: Optional[Dict] = None,
        limit: int = 5
    ) -> List:
        """
        Perform a vector search with caching.
        
        Args:
            query: The search query
            labels: Optional label filter
            where: Optional property filter
            limit: Maximum results to return
            
        Returns:
            List of matching records with similarity scores
        """
        start = time.time()
        
        # Get embedding (from cache or computed)
        vector = self.get_or_compute(query)
        
        # Perform search in RushDB
        search_params = {
            "propertyName": "content",
            "queryVector": vector,
            "limit": limit
        }
        if labels:
            search_params["labels"] = labels
        if where:
            search_params["where"] = where
        
        results = self.db.ai.search(search_params)
        
        self.stats.total_query_time += time.time() - start
        
        return results.data
    
    def batch_precompute(self, queries: List[str]) -> None:
        """
        Pre-compute embeddings for a batch of queries.
        
        This is useful for warming the cache with known popular queries
        before they're needed in production.
        
        Args:
            queries: List of query strings to pre-compute
        """
        print(f"   Pre-computing {len(queries)} embeddings...")
        start = time.time()
        
        for query in queries:
            self.get_or_compute(query)
        
        elapsed = time.time() - start
        print(f"   ✓ Done in {elapsed:.2f}s")
    
    def warm_from_records(self, records: List, get_text_fn) -> None:
        """
        Warm cache by pre-computing embeddings for specific records.
        
        Args:
            records: List of record objects
            get_text_fn: Function to extract text content from a record
        """
        print(f"   Warming cache with {len(records)} records...")
        for record in records:
            text = get_text_fn(record)
            if text:
                self.get_or_compute(text)
        self._pre_warmed = len(records)


def print_cache_stats(cache: VectorCache):
    """Print formatted cache statistics."""
    stats = cache.stats.to_dict()
    print(f"   Hits: {stats['hits']} | Misses: {stats['misses']} | Evictions: {stats['evictions']}")
    print(f"   Hit Rate: {stats['hit_rate']}")
    print(f"   Avg Query: {stats['avg_query_ms']:.2f}ms")
    print(f"   Cache Size: {len(cache._cache)}/{cache.max_size} entries")


def load_index_info() -> Dict:
    """Load the vector index info from seed.py output."""
    path = Path(".index_info.json")
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def demo_basic_caching(db: RushDB, index_id: str):
    """Demonstrate basic LRU caching with cache hits and misses."""
    print("\n" + "─" * 50)
    print("[DEMO 1] Basic LRU Caching")
    print("─" * 50)
    
    # Create cache with small size to demonstrate eviction
    cache = VectorCache(db, index_id, max_size=10, ttl_seconds=300)
    
    queries = [
        "neural networks",
        "machine learning",
        "data science basics",
        "computer vision applications"
    ]
    
    print("\nExecuting searches with empty cache:")
    for i, query in enumerate(queries, 1):
        start = time.time()
        results = cache.search(query, labels=["ARTICLE"], limit=3)
        elapsed = time.time() - start
        
        print(f"\n   Query {i}: \"{query}\"")
        print(f"   Cache MISS - computed embedding in {elapsed:.3f}s")
        print(f"   Found {len(results)} results")
        if results:
            print(f"   Top result: {results[0].data.get('title', 'N/A')}")
    
    print("\n\nRepeating queries (should hit cache):")
    for query in queries[:2]:
        start = time.time()
        results = cache.search(query, labels=["ARTICLE"], limit=3)
        elapsed = time.time() - start
        
        print(f"\n   Query: \"{query}\"")
        print(f"   Cache HIT ✓ ({elapsed*1000:.2f}ms)")
    
    print("\n\nCache statistics after demo 1:")
    print_cache_stats(cache)
    
    return cache


def demo_batch_precomputation(db: RushDB, cache: VectorCache):
    """Demonstrate batch pre-computation for popular queries."""
    print("\n" + "─" * 50)
    print("[DEMO 2] Batch Pre-computation")
    print("─" * 50)
    
    # Clear cache for clean demo
    cache._cache.clear()
    cache.stats = CacheStats()
    
    popular_queries = [
        "machine learning algorithms",
        "deep neural networks",
        "natural language processing",
        "data visualization techniques",
        "cloud computing infrastructure",
        "microservices architecture patterns",
        "API authentication methods",
        "database optimization strategies"
    ]
    
    print(f"\nPre-computing {len(popular_queries)} popular query embeddings...")
    cache.batch_precompute(popular_queries)
    
    print("\nNow querying pre-computed embeddings:")
    for query in popular_queries[:4]:
        start = time.time()
        results = cache.search(query, labels=["ARTICLE"], limit=3)
        elapsed = time.time() - start
        
        print(f"\n   \"{query}\"")
        print(f"   ✓ Cache hit ({elapsed*1000:.2f}ms) - {len(results)} results")
    
    print("\n\nCache statistics after demo 2:")
    print_cache_stats(cache)


def demo_cache_warming(db: RushDB, index_id: str):
    """Demonstrate cache warming from existing database records."""
    print("\n" + "─" * 50)
    print("[DEMO 3] Cache Warming from Database")
    print("─" * 50)
    
    cache = VectorCache(db, index_id, max_size=50)
    
    # Fetch popular articles from database
    print("\nFetching articles to warm cache with...")
    articles = db.records.find({"labels": ["ARTICLE"], "limit": 15})
    print(f"   Found {len(articles.data)} articles")
    
    # Warm cache with article content
    def get_article_text(article):
        title = article.data.get("title", "")
        content = article.data.get("content", "")
        return f"{title} {content}"
    
    cache.warm_from_records(articles.data, get_article_text)
    
    # Now perform searches - should be cache hits
    print("\n\nSearching with warmed cache:")
    test_queries = [
        "machine learning introduction",
        "neural networks deep dive",
        "data science overview"
    ]
    
    for query in test_queries:
        start = time.time()
        results = cache.search(query, labels=["ARTICLE"], limit=3)
        elapsed = time.time() - start
        
        print(f"\n   \"{query}\"")
        print(f"   ✓ ({elapsed*1000:.2f}ms) - {len(results)} results")
    
    print("\n\nCache statistics after warm-up:")
    print_cache_stats(cache)


def demo_cache_eviction(db: RushDB, index_id: str):
    """Demonstrate LRU eviction behavior with small cache."""
    print("\n" + "─" * 50)
    print("[DEMO 4] LRU Eviction Behavior")
    print("─" * 50)
    
    # Very small cache to trigger eviction
    cache = VectorCache(db, index_id, max_size=5)
    
    queries = [
        "query one", "query two", "query three",
        "query four", "query five", "query six"
    ]
    
    print(f"\nCache size: {cache.max_size} entries")
    print(f"\nExecuting {len(queries)} queries to trigger eviction:")
    
    for i, query in enumerate(queries, 1):
        results = cache.search(query, labels=["ARTICLE"], limit=1)
        print(f"   Query {i}: \"{query}\" → Cache size: {len(cache._cache)}")
    
    print(f"\n   After {len(queries)} queries: {cache.stats.evictions} evictions occurred")
    print("   First 2 queries were evicted to make room for newer ones")
    
    print("\n\nRepeating first query (should trigger re-computation):")
    start = time.time()
    results = cache.search("query one", labels=["ARTICLE"], limit=1)
    elapsed = time.time() - start
    print(f"   \"query one\" - Cache MISS after eviction ({elapsed*1000:.2f}ms)")
    print(f"   Total evictions: {cache.stats.evictions}")


def demo_ttl_expiration(db: RushDB, index_id: str):
    """Demonstrate TTL-based cache expiration."""
    print("\n" + "─" * 50)
    print("[DEMO 5] TTL-based Expiration")
    print("─" * 50)
    
    # Very short TTL for demo purposes
    cache = VectorCache(db, index_id, max_size=10, ttl_seconds=0.5)
    
    print("\nCache TTL: 0.5 seconds")
    
    # First query
    print("\nExecuting first query...")
    results = cache.search("artificial intelligence", labels=["ARTICLE"], limit=1)
    print(f"   ✓ Cached (TTL: 0.5s)")
    
    # Immediate repeat - should hit
    print("\nRepeating immediately (should hit):")
    start = time.time()
    results = cache.search("artificial intelligence", labels=["ARTICLE"], limit=1)
    elapsed = time.time() - start
    print(f"   ✓ Cache hit ({elapsed*1000:.2f}ms)")
    
    # Wait for TTL
    print("\nWaiting 0.6 seconds for TTL to expire...")
    time.sleep(0.6)
    
    # Repeat - should miss
    print("Repeating after expiry (should miss):")
    start = time.time()
    results = cache.search("artificial intelligence", labels=["ARTICLE"], limit=1)
    elapsed = time.time() - start
    print(f"   ✓ Cache miss - re-computed ({elapsed*1000:.2f}ms)")


def demo_cache_stats_and_monitoring(db: RushDB, index_id: str):
    """Demonstrate cache statistics and monitoring capabilities."""
    print("\n" + "─" * 50)
    print("[DEMO 6] Cache Statistics & Monitoring")
    print("─" * 50)
    
    cache = VectorCache(db, index_id, max_size=50)
    
    # Run various queries
    queries = [
        "machine learning", "machine learning",  # Duplicate to boost hit rate
        "neural networks",
        "data science", "data science",  # Duplicate
        "python programming",
        "API design",
        "database optimization",
        "machine learning",  # Again
        "cloud computing"
    ]
    
    print("\nRunning 10 queries (some duplicates)...")
    for query in queries:
        cache.search(query, labels=["ARTICLE"], limit=3)
    
    # Display comprehensive stats
    print("\n📊 Cache Performance Report")
    print("─" * 35)
    stats = cache.stats
    
    print(f"   Total Queries:    {stats.hits + stats.misses}")
    print(f"   Cache Hits:       {stats.hits}")
    print(f"   Cache Misses:     {stats.misses}")
    print(f"   Hit Rate:         {stats.hit_rate:.1f}%")
    print(f"   Evictions:        {stats.evictions}")
    print(f"   Current Size:     {len(cache._cache)}/{cache.max_size}")
    
    # Show most accessed entries (by access count)
    print("\n📈 Most Accessed Queries:")
    sorted_entries = sorted(
        cache._cache.values(),
        key=lambda e: e.access_count,
        reverse=True
    )[:5]
    
    for entry in sorted_entries:
        print(f"   Hash: {entry.query_hash} | Accesses: {entry.access_count}")


def main():
    """Run the embedding caching demonstration."""
    print("=" * 60)
    print("RushDB Embedding Caching Strategies Demo")
    print("=" * 60)
    
    # Load index info from seed.py
    index_info = load_index_info()
    if not index_info:
        print("\n❌ Error: index_info.json not found.")
        print("   Please run 'python seed.py' first to set up the database.")
        sys.exit(1)
    
    index_id = index_info["index_id"]
    print(f"\n✓ Loaded index: {index_id}")
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\n❌ Error: RUSHDB_API_KEY not found in environment")
        sys.exit(1)
    
    db = RushDB(api_key)
    print("✓ Connected to RushDB")
    
    # Verify index exists
    try:
        stats = db.ai.indexes.stats(index_id)
        print(f"✓ Index ready: {stats.data.get('indexedRecords', 0)} records indexed")
    except Exception as e:
        print(f"\n❌ Error: Could not access index: {e}")
        print("   Please re-run 'python seed.py' to recreate the index.")
        sys.exit(1)
    
    # Run demonstrations
    cache = demo_basic_caching(db, index_id)
    demo_batch_precomputation(db, cache)
    demo_cache_warming(db, index_id)
    demo_cache_eviction(db, index_id)
    demo_ttl_expiration(db, index_id)
    demo_cache_stats_and_monitoring(db, index_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("""
Key Takeaways:

1. LRU Cache reduces embedding computation by caching query vectors
2. Batch pre-computation warms the cache for known popular queries
3. Cache warming from database avoids cold-start penalties
4. TTL helps balance freshness vs. performance
5. Monitor hit rates to optimize cache size parameters

For production use:
- Set max_size based on expected unique queries
- Adjust TTL based on data freshness requirements
- Consider using Redis for distributed caching across instances
- Track cache metrics in your monitoring system
""")


if __name__ == "__main__":
    main()
