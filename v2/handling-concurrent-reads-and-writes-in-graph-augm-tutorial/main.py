"""
Handling Concurrent Reads and Writes in Graph-Augmented RAG

This tutorial demonstrates RushDB's handling of concurrent operations
in a graph-augmented RAG context. It covers edge cases that naive
implementations typically miss.
"""

import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Configuration
MAX_RETRIES = 3
BASE_BACKOFF_MS = 100


@dataclass
class WriteResult:
    """Result of a concurrent write operation."""
    success: bool
    record_id: Optional[str] = None
    attempts: int = 1
    error: Optional[str] = None


class ExponentialBackoff:
    """Simple exponential backoff implementation."""
    
    def __init__(self, base_ms: int = 100, max_ms: int = 2000, jitter: float = 0.1):
        self.base_ms = base_ms
        self.max_ms = max_ms
        self.jitter = jitter
        self.attempt = 0
    
    def wait_time(self) -> float:
        """Calculate wait time for current attempt."""
        self.attempt += 1
        exponential_wait = self.base_ms * (2 ** (self.attempt - 1))
        capped_wait = min(exponential_wait, self.max_ms)
        # Add jitter to prevent thundering herd
        jitter_range = capped_wait * self.jitter
        actual_wait = capped_wait + random.uniform(-jitter_range, jitter_range)
        return actual_wait / 1000.0  # Convert to seconds
    
    def reset(self):
        """Reset the backoff state."""
        self.attempt = 0


def initialize_db() -> RushDB:
    """Initialize RushDB connection with validation."""
    api_key = os.getenv("RUSHDB_API_KEY")
    url = os.getenv("RUSHDB_URL")
    
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not set. "
            "Copy .env.example to .env and add your API key."
        )
    
    if url:
        return RushDB(api_key, url=url)
    return RushDB(api_key)


def setup_vector_index(db: RushDB):
    """Ensure vector index exists for ARTICLE.body."""
    try:
        indexes = db.ai.indexes.find()
        existing_index = any(
            idx.get('label') == 'ARTICLE' and idx.get('propertyName') == 'body'
            for idx in (indexes.data if hasattr(indexes, 'data') else [])
        )
        
        if not existing_index:
            db.ai.indexes.create({
                "label": "ARTICLE",
                "propertyName": "body",
                "sourceType": "external",
                "dimensions": 384,
                "similarityFunction": "cosine"
            })
            print("✓ Created vector index for ARTICLE.body")
        else:
            print("✓ Vector index already exists")
    except Exception as e:
        print(f"Note: Index setup - {e}")


def demo_concurrent_writes(db: RushDB, model) -> list:
    """
    Demo 1: Setting up RushDB with concurrent write streams.
    
    Multiple writers from different sources write simultaneously.
    Each write includes a pre-computed vector embedding.
    """
    print("\n" + "=" * 60)
    print("DEMO 1: CONCURRENT WRITE STREAMS")
    print("=" * 60)
    
    sources = ["Source-A", "Source-B", "Source-C"]
    articles_per_source = 3
    created_records = []
    
    def write_from_source(source_name: str, index: int) -> WriteResult:
        """Simulate a single write from a source."""
        topic = random.choice([
            "distributed systems", "graph databases", "vector search",
            "microservices", "event sourcing"
        ])
        
        article_data = {
            "title": f"{topic.title()} - {source_name}-{index}",
            "body": f"A comprehensive guide to {topic} with practical examples.",
            "topic": topic,
            "source": source_name,
            "created_at": datetime.now().isoformat(),
        }
        
        # Compute embedding
        embedding = model.encode(article_data["body"]).tolist()
        
        backoff = ExponentialBackoff()
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Use upsert with deterministic merge to handle concurrent creates
                record = db.records.upsert(
                    label="DEMO_ARTICLE",
                    data=article_data,
                    options={"mergeBy": ["title"]},
                    vectors=[{"propertyName": "body", "vector": embedding}]
                )
                return WriteResult(success=True, record_id=record.id, attempts=attempt)
            except Exception as e:
                if attempt < MAX_RETRIES:
                    wait_time = backoff.wait_time()
                    print(f"  ⚠ {source_name}-{index}: Conflict (attempt {attempt}), waiting {wait_time:.3f}s")
                    time.sleep(wait_time)
                else:
                    return WriteResult(success=False, attempts=attempt, error=str(e))
        
        return WriteResult(success=False, attempts=MAX_RETRIES, error="Max retries exceeded")
    
    # Execute concurrent writes
    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        futures = {
            executor.submit(write_from_source, source, idx): (source, idx)
            for source in sources
            for idx in range(articles_per_source)
        }
        
        for future in as_completed(futures):
            source, idx = futures[future]
            result = future.result()
            
            if result.success:
                created_records.append(result.record_id)
                print(f"  ✓ {source}-{idx}: Created Article(id={result.record_id[:12]}...)")
            else:
                print(f"  ✗ {source}-{idx}: Failed after {result.attempts} attempts - {result.error}")
    
    print(f"\n✓ Concurrent writes complete: {len(created_records)} records created")
    return created_records


def demo_read_your_writes(db: RushDB, created_ids: list):
    """
    Demo 2: Read-Your-Writes Consistency.
    
    Demonstrates that writes are immediately visible on the same connection.
    This is critical for RAG applications where you write a document and
    immediately need to retrieve it for context.
    """
    print("\n" + "=" * 60)
    print("DEMO 2: READ-YOUR-WRITES CONSISTENCY")
    print("=" * 60)
    
    # Write a new record
    new_article = db.records.create(
        label="DEMO_ARTICLE",
        data={
            "title": "Read-Your-Writes Test",
            "body": "Testing immediate read visibility after write.",
            "verified": True
        }
    )
    print(f"  ✓ Wrote new article: {new_article.id}")
    
    # Immediately read it back on the SAME connection
    found = db.records.find_by_id(new_article.id)
    
    if found and found.id == new_article.id:
        print(f"  ✓ Read-after-write verified: Found '{found['title']}'")
    else:
        print(f"  ✗ Read-after-write failed: Record not found")
    
    # Verify consistency with transaction
    with db.transactions.begin() as tx:
        db.records.create(
            label="DEMO_ARTICLE",
            data={"title": "Transaction Test", "body": "Within transaction"},
            transaction=tx
        )
        # Read inside transaction - should see the write
        inside_records = db.records.find({
            "labels": ["DEMO_ARTICLE"],
            "where": {"title": "Transaction Test"},
            "transaction": tx
        })
        
        if inside_records.data:
            print(f"  ✓ Transaction consistency: {len(inside_records.data)} record(s) visible")
        else:
            print(f"  ⚠ Transaction reads may need fresh connection for visibility")
    
    # Verify all created records are findable
    all_found = 0
    for record_id in created_ids[:5]:
        try:
            record = db.records.find_by_id(record_id)
            if record:
                all_found += 1
        except Exception:
            pass
    
    print(f"  ✓ Consistency check: {all_found}/5 of our records are retrievable")


def demo_vector_staleness(db: RushDB, model):
    """
    Demo 3: Handling Vector Embedding Staleness.
    
    When a graph entity is updated, its vector embedding becomes stale.
    This demo shows how to detect and refresh stale embeddings.
    """
    print("\n" + "=" * 60)
    print("DEMO 3: VECTOR EMBEDDING STALENESS HANDLING")
    print("=" * 60)
    
    # Create an article with initial content
    original_body = "Introduction to graph databases and their applications in modern software."
    
    article = db.records.create(
        label="DEMO_ARTICLE",
        data={
            "title": "Staleness Test Article",
            "body": original_body,
            "version": 1,
            "embedding_stale": False
        },
        vectors=[{"propertyName": "body", "vector": model.encode(original_body).tolist()}]
    )
    print(f"  ✓ Created article with initial content: {article.id}")
    
    # Simulate content update (common in RAG when documents change)
    updated_body = "Advanced graph databases: A comprehensive look at Neo4j, RushDB, and relationship-centric data modeling in distributed systems."
    
    # Detect staleness: body content changed
    content_changed = original_body != updated_body
    
    if content_changed:
        print(f"  ✓ Detected content change: embedding is stale")
        
        # Re-compute the embedding with new content
        new_embedding = model.encode(updated_body).tolist()
        print(f"  ✓ Computed new embedding (dimension: {len(new_embedding)})")
        
        # Update the record with new content AND new embedding
        db.records.set(
            target=article,
            label="DEMO_ARTICLE",
            data={
                "title": "Staleness Test Article",
                "body": updated_body,
                "version": 2,
                "embedding_stale": False,
                "last_embedding_update": datetime.now().isoformat()
            },
            vectors=[{"propertyName": "body", "vector": new_embedding}]
        )
        
        print(f"  ✓ Refreshed record with new embedding (version 1 → 2)")
    
    # Verify the update
    updated_record = db.records.find_by_id(article.id)
    if updated_record and updated_record.get("version") == 2:
        print(f"  ✓ Verified: Record version is now {updated_record.get('version')}")
    
    # Demonstrate similarity search still works with updated content
    results = db.ai.search({
        "propertyName": "body",
        "query": "distributed systems data modeling",
        "labels": ["DEMO_ARTICLE"],
        "limit": 3
    })
    
    if results.data:
        print(f"  ✓ Semantic search works with updated content: {len(results.data)} results")
    else:
        print(f"  ⚠ No semantic search results (may need more articles for similarity)")


def demo_retry_with_backoff(db: RushDB, model):
    """
    Demo 4: Retry and Backoff Strategies.
    
    Demonstrates exponential backoff for handling transient conflicts.
    In production, network issues and contention cause occasional failures.
    """
    print("\n" + "=" * 60)
    print("DEMO 4: RETRY WITH EXPONENTIAL BACKOFF")
    print("=" * 60)
    
    backoff = ExponentialBackoff(base_ms=50, max_ms=500)
    
    def write_with_retry(title_suffix: int) -> WriteResult:
        """Write with exponential backoff retry logic."""
        article_data = {
            "title": f"Retry Test {title_suffix}",
            "body": f"Testing retry mechanism with backoff for article {title_suffix}."
        }
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Simulate occasional conflicts by using same title
                # In real scenarios, this happens due to contention
                record = db.records.upsert(
                    label="DEMO_RETRY",
                    data=article_data,
                    options={"mergeBy": ["title"]},
                    vectors=[{"propertyName": "body", "vector": model.encode(article_data["body"]).tolist()}]
                )
                return WriteResult(success=True, record_id=record.id, attempts=attempt)
            except Exception as e:
                if attempt < MAX_RETRIES:
                    wait_time = backoff.wait_time()
                    print(f"    Attempt {attempt} failed, waiting {wait_time:.3f}s...")
                    time.sleep(wait_time)
                else:
                    return WriteResult(success=False, attempts=attempt, error=str(e))
        
        backoff.reset()
        return WriteResult(success=False, attempts=MAX_RETRIES, error="All retries exhausted")
    
    print("  Simulating 5 concurrent writes with potential conflicts...")
    
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(write_with_retry, i) for i in range(5)]
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)
            
            if result.success:
                print(f"  ✓ Write {i+1}: Succeeded on attempt {result.attempts}")
            else:
                print(f"  ✗ Write {i+1}: Failed after {result.attempts} attempts")
    
    success_count = sum(1 for r in results if r.success)
    print(f"\n  ✓ Results: {success_count}/{len(results)} writes successful")
    
    # Demonstrate backoff pattern in detail
    print("\n  Backoff pattern demonstration:")
    for attempt in range(1, 5):
        wait = 50 * (2 ** (attempt - 1)) / 1000
        print(f"    Attempt {attempt}: wait {wait:.3f}s (exponential: 50ms * 2^{attempt-1})")


def demo_end_to_end(db: RushDB, model):
    """
    Demo 5: End-to-End Concurrent RAG Pipeline.
    
    Simulates a real-world scenario: multiple sources writing documents,
    immediate indexing, and semantic search for RAG context retrieval.
    """
    print("\n" + "=" * 60)
    print("DEMO 5: END-TO-END CONCURRENT RAG PIPELINE")
    print("=" * 60)
    
    # Simulate multiple document sources (like different microservices)
    sources = {
        "user-docs": ["User authentication guide", "API reference documentation", "SDK quickstart"],
        "product-docs": ["Product feature overview", "Pricing documentation", "Enterprise features"],
        "support-docs": ["Troubleshooting guide", "FAQ common issues", "Support contact info"]
    }
    
    print("\n  Writing documents from multiple sources...")
    written_docs = []
    
    for source_name, titles in sources.items():
        for title in titles:
            doc_data = {
                "title": title,
                "body": f"Comprehensive documentation for: {title}. Covers all aspects and best practices.",
                "source": source_name,
                "indexed_at": datetime.now().isoformat()
            }
            
            embedding = model.encode(doc_data["body"]).tolist()
            
            try:
                record = db.records.upsert(
                    label="RAG_DOCUMENT",
                    data=doc_data,
                    options={"mergeBy": ["title", "source"]},
                    vectors=[{"propertyName": "body", "vector": embedding}]
                )
                written_docs.append(record)
                print(f"    ✓ [{source_name}] {title}")
            except Exception as e:
                print(f"    ✗ [{source_name}] {title}: {e}")
    
    print(f"\n  ✓ Wrote {len(written_docs)} documents from {len(sources)} sources")
    
    # Now demonstrate RAG: semantic search for context
    print("\n  Performing semantic searches for RAG context...")
    
    queries = [
        "authentication and security",
        "pricing and enterprise features",
        "troubleshooting and support"
    ]
    
    for query in queries:
        print(f"\n  Query: '{query}'")
        
        results = db.ai.search({
            "propertyName": "body",
            "query": query,
            "labels": ["RAG_DOCUMENT"],
            "limit": 2
        })
        
        if results.data:
            for result in results.data:
                score = result.score if hasattr(result, 'score') else result.get('__score', 0)
                print(f"    → {result.get('title', 'Unknown')} (score: {score:.3f}, source: {result.get('source', 'N/A')})")
        else:
            print(f"    → No results (may need more documents for similarity)")
    
    print("\n  ✓ RAG pipeline demonstration complete")


def cleanup_demo_data(db: RushDB):
    """Clean up demo records (optional)."""
    try:
        # In production, you'd be more selective about cleanup
        # For demo purposes, we leave the data for inspection
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nDemo records remain in your RushDB project for inspection.")
        print("Labels used: DEMO_ARTICLE, DEMO_RETRY, RAG_DOCUMENT")
        print("\nTo clean up, use:")
        print("  db.records.delete({'labels': ['DEMO_ARTICLE'], 'where': {...}})")
    except Exception as e:
        print(f"Cleanup note: {e}")


def main():
    """Main entry point - runs all demonstrations."""
    print("\n" + "=" * 60)
    print("RUSHDB CONCURRENT READS AND WRITES TUTORIAL")
    print("Graph-Augmented RAG with Concurrent Operations")
    print("=" * 60)
    
    try:
        # Initialize connection
        db = initialize_db()
        print("\n✓ Connected to RushDB")
        
        # Setup vector index
        setup_vector_index(db)
        
        # Load embedding model
        print("\nLoading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Embedding model loaded (all-MiniLM-L6-v2)")
        
        # Run demonstrations
        created_ids = demo_concurrent_writes(db, model)
        demo_read_your_writes(db, created_ids)
        demo_vector_staleness(db, model)
        demo_retry_with_backoff(db, model)
        demo_end_to_end(db, model)
        
        # Cleanup and finish
        cleanup_demo_data(db)
        
        print("\n" + "=" * 60)
        print("All demonstrations completed successfully!")
        print("=" * 60 + "\n")
        
    except ValueError as e:
        print(f"\nConfiguration error: {e}")
        print("Make sure to copy .env.example to .env and add your RushDB API key.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Check your RushDB connection and try again.")
        raise


if __name__ == "__main__":
    main()
