#!/usr/bin/env python3
"""
Real-time Stream Processing with Graph-Backed Vector Updates

This demo shows:
1. A stream processor that ingests events and updates the graph
2. Automatic vector synchronization on graph mutations
3. Combined graph traversal + vector similarity queries
4. Benchmarking of update and query latency
"""

import os
import sys
import time
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer


@dataclass
class BenchmarkResult:
    """Stores benchmark metrics."""
    name: str
    latencies_ms: List[float] = field(default_factory=list)
    total_operations: int = 0
    
    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0
    
    @property
    def p95_latency(self) -> float:
        if not self.latencies_ms:
            return 0
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def throughput(self) -> float:
        total_time = sum(self.latencies_ms)
        return (self.total_operations / total_time * 1000) if total_time > 0 else 0


class EmbeddingService:
    """Handles text embedding using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"\nInitializing embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_sentence_embedding_dimension()
        print(f"  Embedding dimensions: {self.dimensions}")
    
    def encode(self, text: str) -> List[float]:
        """Encode text to vector."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()


class StreamProcessor:
    """
    Simulates a stream processor that:
    - Consumes events from a stream
    - Updates the graph with each event
    - Automatically syncs vectors on mutations
    """
    
    def __init__(self, db: RushDB, embedding_service: EmbeddingService):
        self.db = db
        self.embedder = embedding_service
        self.event_buffer: List[Dict] = []
        self.processed_count = 0
    
    def generate_event(self, articles: List) -> Dict[str, Any]:
        """Generate a simulated stream event."""
        event_types = ["article.view", "article.like", "article.share", "article.comment"]
        article = random.choice(articles)
        
        return {
            "id": f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            "type": random.choice(event_types),
            "target_id": article.data.get("id"),
            "target_article_id": article.id,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "source": random.choice(["web", "mobile", "api"]),
                "session_id": f"sess_{random.randint(10000, 99999)}",
                "user_id": f"user_{random.randint(1, 1000)}"
            }
        }
    
    def process_event(self, event: Dict[str, Any]) -> tuple:
        """
        Process a single event:
        - Create/update the event record in the graph
        - Update the associated article's metrics
        - Sync the article's vector (simulating re-embedding on updates)
        
        Returns: (latency_ms, success)
        """
        start_time = time.perf_counter()
        
        try:
            # 1. Create the event record
            event_record = self.db.records.create(
                label="STREAM_EVENT",
                data={
                    "id": event["id"],
                    "type": event["type"],
                    "target_id": event["target_id"],
                    "timestamp": event["timestamp"],
                    "source": event["metadata"]["source"],
                    "session_id": event["metadata"]["session_id"],
                    "user_id": event["metadata"]["user_id"]
                }
            )
            
            # 2. Find the target article
            article = self.db.records.find_by_id(event["target_article_id"])
            if not article.exists:
                raise ValueError(f"Article not found: {event['target_article_id']}")
            
            # 3. Update article metrics (incremental update)
            view_count = article.data.get("view_count", 0)
            if event["type"] == "article.view":
                view_count += 1
            
            # 4. Update the article with new metrics + re-embed content
            # This demonstrates the vector sync on mutation pattern
            current_content = article.data.get("content", "")
            
            # Simulate content mutation based on event
            enhanced_content = current_content
            if event["type"] == "article.like":
                # Add trending indicator to content
                enhanced_content = f"[Trending] {current_content}"
            elif event["type"] == "article.share":
                enhanced_content = f"[Viral] {current_content}"
            
            # Generate new embedding for the updated content
            new_vector = self.embedder.encode(enhanced_content)
            
            # Upsert the article with the new vector (sync pattern)
            updated_article = self.db.records.upsert(
                label="ARTICLE",
                data={
                    "id": article.data.get("id"),
                    "title": article.data.get("title"),
                    "content": enhanced_content,
                    "summary": article.data.get("summary"),
                    "category": article.data.get("category"),
                    "tags": article.data.get("tags"),
                    "view_count": view_count,
                    "updated_at": datetime.now().isoformat()
                },
                options={"mergeBy": ["id"]},
                vectors=[{"propertyName": "content", "vector": new_vector}]
            )
            
            # 5. Link event to article in the graph
            self.db.records.attach(
                source=event_record,
                target=article,
                options={"type": "TRIGGERS_UPDATE", "direction": "out"}
            )
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return elapsed_ms, True
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            print(f"    Error processing event {event.get('id')}: {e}")
            return elapsed_ms, False


class GraphVectorQueryEngine:
    """
    Demonstrates combined graph traversal + vector similarity queries.
    """
    
    def __init__(self, db: RushDB, embedding_service: EmbeddingService):
        self.db = db
        self.embedder = embedding_service
    
    def search_by_graph_context_and_vector(
        self,
        author_domain: str,
        topic_query: str,
        limit: int = 5
    ) -> tuple:
        """
        Combined query pattern:
        1. First, traverse graph to find authors in a specific domain
        2. Then, search articles by vector similarity, filtered by those authors
        
        Returns: (results, latency_ms)
        """
        start_time = time.perf_counter()
        
        # Step 1: Graph traversal - find authors in the domain
        authors = self.db.records.find({
            "labels": ["AUTHOR"],
            "where": {"domain": author_domain}
        })
        
        author_ids = [a.id for a in authors.data] if authors.data else []
        
        if not author_ids:
            return [], (time.perf_counter() - start_time) * 1000
        
        # Step 2: Vector similarity search with graph-based filter
        query_vector = self.embedder.encode(topic_query)
        
        results = self.db.ai.search({
            "propertyName": "content",
            "queryVector": query_vector,
            "labels": ["ARTICLE"],
            "where": {
                "AUTHOR": {"$id": {"$in": author_ids}}
            },
            "limit": limit
        })
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        return results.data, latency_ms
    
    def find_related_articles(self, article_id: str, limit: int = 5) -> tuple:
        """
        Find articles related to a given article via graph traversal,
        then re-rank by vector similarity.
        
        Returns: (results, latency_ms)
        """
        start_time = time.perf_counter()
        
        # Get the source article
        source = self.db.records.find_by_id(article_id)
        if not source.exists:
            return [], 0
        
        # Get the author
        author_results = self.db.records.find({
            "labels": ["ARTICLE"],
            "where": {
                "AUTHOR": {"$id": {"$in": [source.id]}}
            }
        })
        
        if not author_results.data:
            return [], (time.perf_counter() - start_time) * 1000
        
        # Get author's other articles via graph
        author = self.db.records.find({
            "labels": ["AUTHOR"],
            "where": {
                "ARTICLE": {"$id": {"$in": [source.id]}}
            }
        })
        
        if not author.data:
            return [], (time.perf_counter() - start_time) * 1000
        
        author_id = author.data[0].id
        
        # Find other articles by this author
        other_articles = self.db.records.find({
            "labels": ["ARTICLE"],
            "where": {
                "AUTHOR": {"$id": {"$in": [author_id]}},
                "id": {"$ne": source.data.get("id")}
            },
            "limit": limit + 5
        })
        
        if not other_articles.data:
            return [], (time.perf_counter() - start_time) * 1000
        
        # Re-rank by vector similarity to source article
        source_vector = self.embedder.encode(source.data.get("content", ""))
        
        for article in other_articles.data:
            article_vector = self.embedder.encode(article.data.get("content", ""))
            similarity = self._cosine_similarity(source_vector, article_vector)
            article.score = similarity
        
        # Sort by similarity and return top results
        ranked = sorted(other_articles.data, key=lambda a: a.score or 0, reverse=True)[:limit]
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        return ranked, latency_ms
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude = lambda v: sum(x * x for x in v) ** 0.5
        return dot_product / (magnitude(vec1) * magnitude(vec2) + 1e-8)


def run_benchmarks(
    db: RushDB,
    processor: StreamProcessor,
    query_engine: GraphVectorQueryEngine,
    num_events: int = 100
) -> Dict[str, BenchmarkResult]:
    """Run comprehensive benchmarks."""
    
    print("\n" + "="*60)
    print("BENCHMARKING")
    print("="*60)
    
    results = {
        "event_processing": BenchmarkResult("Event Processing"),
        "article_upsert": BenchmarkResult("Article Upsert with Vector"),
        "graph_traversal": BenchmarkResult("Graph Traversal"),
        "vector_search": BenchmarkResult("Vector Search"),
        "combined_query": BenchmarkResult("Combined Graph+Vector Query")
    }
    
    # Get existing articles for event simulation
    articles = db.records.find({"labels": ["ARTICLE"], "limit": 50})
    if not articles.data:
        print("ERROR: No articles found. Please run seed.py first.")
        return results
    
    print(f"\nRunning benchmarks with {num_events} events...")
    
    # Benchmark 1: Event processing
    print("\n1. Event Processing Benchmark")
    print("-" * 40)
    
    batch_size = int(os.getenv("STREAM_BATCH_SIZE", "10"))
    delay_ms = float(os.getenv("STREAM_DELAY_MS", "100")) / 1000
    
    for i in range(num_events):
        event = processor.generate_event(articles.data)
        latency, success = processor.process_event(event)
        
        if success:
            results["event_processing"].latencies_ms.append(latency)
            results["event_processing"].total_operations += 1
        
        if (i + 1) % batch_size == 0:
            time.sleep(delay_ms)
        
        if (i + 1) % 25 == 0:
            print(f"  Processed {i+1}/{num_events} events")
    
    # Benchmark 2: Graph traversal
    print("\n2. Graph Traversal Benchmark")
    print("-" * 40)
    
    domains = ["technology", "science", "business", "health"]
    for _ in range(20):
        start_time = time.perf_counter()
        authors = db.records.find({
            "labels": ["AUTHOR"],
            "where": {"domain": random.choice(domains)}
        })
        latency = (time.perf_counter() - start_time) * 1000
        results["graph_traversal"].latencies_ms.append(latency)
        results["graph_traversal"].total_operations += 1
    
    print(f"  Completed {results['graph_traversal'].total_operations} traversals")
    
    # Benchmark 3: Vector search
    print("\n3. Vector Search Benchmark")
    print("-" * 40)
    
    queries = [
        "machine learning algorithms and applications",
        "cloud computing infrastructure best practices",
        "data science and analytics techniques",
        "cybersecurity and threat detection",
        "distributed systems architecture"
    ]
    
    embedder = processor.embedder
    
    for _ in range(20):
        query_vector = embedder.encode(random.choice(queries))
        
        start_time = time.perf_counter()
        results_vec = db.ai.search({
            "propertyName": "content",
            "queryVector": query_vector,
            "labels": ["ARTICLE"],
            "limit": 10
        })
        latency = (time.perf_counter() - start_time) * 1000
        results["vector_search"].latencies_ms.append(latency)
        results["vector_search"].total_operations += 1
    
    print(f"  Completed {results['vector_search'].total_operations} searches")
    
    # Benchmark 4: Combined queries
    print("\n4. Combined Graph + Vector Query Benchmark")
    print("-" * 40)
    
    for domain in random.sample(domains, k=5):
        for _ in range(4):
            query = random.choice(queries)
            _, latency = query_engine.search_by_graph_context_and_vector(
                author_domain=domain,
                topic_query=query,
                limit=5
            )
            results["combined_query"].latencies_ms.append(latency)
            results["combined_query"].total_operations += 1
    
    print(f"  Completed {results['combined_query'].total_operations} combined queries")
    
    return results


def print_benchmark_results(results: Dict[str, BenchmarkResult]):
    """Print formatted benchmark results."""
    
    print("\n" + "="*60)
    print("BENCHMARK RESULTS")
    print("="*60)
    print(f"\n{'Operation':<30} {'Avg (ms)':<12} {'P95 (ms)':<12} {'Throughput':<12}")
    print("-" * 66)
    
    for key, result in results.items():
        name = result.name
        avg = f"{result.avg_latency:.2f}"
        p95 = f"{result.p95_latency:.2f}"
        tput = f"{result.throughput:.2f}/s"
        print(f"{name:<30} {avg:<12} {p95:<12} {tput:<12}")
    
    print("-" * 66)


def demonstrate_queries(
    db: RushDB,
    query_engine: GraphVectorQueryEngine,
    embedder: EmbeddingService
):
    """Demonstrate various query patterns."""
    
    print("\n" + "="*60)
    print("QUERY DEMONSTRATIONS")
    print("="*60)
    
    # Demo 1: Combined graph + vector search
    print("\n1. Combined Graph Traversal + Vector Search")
    print("-" * 40)
    
    results, latency = query_engine.search_by_graph_context_and_vector(
        author_domain="technology",
        topic_query="artificial intelligence and machine learning advances",
        limit=5
    )
    
    print(f"   Query: 'artificial intelligence advances' filtered by tech authors")
    print(f"   Latency: {latency:.2f}ms")
    print(f"   Results: {len(results)} articles")
    
    for i, article in enumerate(results[:3], 1):
        title = article.data.get("title", "Untitled")[:50]
        score = article.score or 0
        print(f"   {i}. [{score:.3f}] {title}")
    
    # Demo 2: Find related articles
    print("\n2. Find Related Articles via Graph + Re-rank by Vector")
    print("-" * 40)
    
    articles = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    if articles.data:
        source_id = articles.data[0].id
        source_title = articles.data[0].data.get("title", "Untitled")[:50]
        
        print(f"   Source article: {source_title}")
        
        related, latency = query_engine.find_related_articles(source_id, limit=3)
        print(f"   Latency: {latency:.2f}ms")
        print(f"   Related articles: {len(related)}")
        
        for i, article in enumerate(related, 1):
            title = article.data.get("title", "Untitled")[:50]
            score = article.score or 0
            print(f"   {i}. [{score:.3f}] {title}")
    
    # Demo 3: Semantic search with graph filters
    print("\n3. Semantic Search with Graph-Based Filtering")
    print("-" * 40)
    
    query_vector = embedder.encode("cloud computing and distributed systems")
    
    # First, get authors with high followers
    popular_authors = db.records.find({
        "labels": ["AUTHOR"],
        "where": {"followers": {"$gte": 5000}},
        "limit": 10
    })
    
    popular_author_ids = [a.id for a in popular_authors.data]
    print(f"   Found {len(popular_author_ids)} authors with 5000+ followers")
    
    if popular_author_ids:
        results = db.ai.search({
            "propertyName": "content",
            "queryVector": query_vector,
            "labels": ["ARTICLE"],
            "where": {
                "AUTHOR": {"$id": {"$in": popular_author_ids}}
            },
            "limit": 5
        })
        
        print(f"   Vector search results from popular authors: {len(results.data)}")
        for i, article in enumerate(results.data[:3], 1):
            title = article.data.get("title", "Untitled")[:50]
            score = article.score or 0
            print(f"   {i}. [{score:.3f}] {title}")


def print_vector_index_stats(db: RushDB):
    """Print vector index statistics."""
    print("\n" + "="*60)
    print("VECTOR INDEX STATUS")
    print("="*60)
    
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        idx_id = idx.get("__id")
        label = idx.get("label")
        prop = idx.get("propertyName")
        
        stats = db.ai.indexes.stats(idx_id)
        indexed = stats.data.get("indexedRecords", 0)
        total = stats.data.get("totalRecords", 0)
        
        print(f"\n  {label}.{prop}")
        print(f"    Status: {idx.get('status', 'unknown')}")
        print(f"    Indexed: {indexed} / {total} records")


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("REAL-TIME STREAM PROCESSING WITH GRAPH-BACKED VECTORS")
    print("="*60)
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("Please copy .env.example to .env and add your API key")
        sys.exit(1)
    
    print("\nConnecting to RushDB...")
    db = RushDB(api_key)
    
    # Verify connection
    try:
        labels = db.labels.find()
        print(f"Connected. Found {len(labels.data)} labels.")
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)
    
    # Initialize embedding service
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedder = EmbeddingService(model_name)
    
    # Initialize components
    processor = StreamProcessor(db, embedder)
    query_engine = GraphVectorQueryEngine(db, embedder)
    
    # Print vector index stats
    print_vector_index_stats(db)
    
    # Get configuration
    num_events = int(os.getenv("STREAM_TOTAL_EVENTS", "100"))
    
    # Run benchmarks
    results = run_benchmarks(db, processor, query_engine, num_events)
    
    # Print results
    print_benchmark_results(results)
    
    # Demonstrate query patterns
    demonstrate_queries(db, query_engine, embedder)
    
    # Final stats
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    
    # Final database stats
    total_events = db.records.find({"labels": ["STREAM_EVENT"]})
    total_articles = db.records.find({"labels": ["ARTICLE"]})
    
    print(f"\n  Total STREAM_EVENT records: {len(total_events.data)}")
    print(f"  Total ARTICLE records: {len(total_articles.data)}")
    
    print_vector_index_stats(db)
    
    print("\n✅ All benchmarks and demonstrations completed!")
    print("\nKey takeaways:")
    print("  • Graph mutations can trigger automatic vector updates")
    print("  • Combined queries leverage both graph traversal and vector search")
    print("  • Latency can be benchmarked for both update and query paths")


if __name__ == "__main__":
    main()
