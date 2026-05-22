"""
Seed script for concurrent writes tutorial.

Generates 50 article records concurrently from multiple "sources"
to demonstrate RushDB's handling of concurrent write streams.

This script is idempotent - safe to run multiple times. It checks for
existing data before creating new records.
"""

import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Configuration
ARTICLE_COUNT = 50
MAX_WORKERS = 5  # Simulate 5 concurrent sources

# Article topics for realistic content generation
ARTICLE_TOPICS = [
    "microservices architecture", "event sourcing", "graph databases",
    "vector similarity search", "knowledge graphs", "rag systems",
    "neo4j best practices", "distributed tracing", "api design",
    "container orchestration", "kubernetes patterns", "service mesh",
    "event-driven architecture", "cqrs pattern", "domain-driven design",
    "clean architecture", "hexagonal architecture", "microservices patterns",
    "database indexing", "query optimization", "graph traversal",
    "embedding models", "semantic search", "information retrieval",
    "machine learning pipelines", "data engineering", "etl processes",
    "real-time analytics", "stream processing", "kafka patterns",
    "message queues", "async programming", "reactive systems",
    "cloud-native applications", "serverless architecture", "faas patterns",
    "devops practices", "ci/cd pipelines", "infrastructure as code",
    "observability", "monitoring", "logging strategies",
    "security patterns", "oauth2 implementation", "jwt authentication",
    "api gateways", "load balancing", "circuit breakers",
    "cache strategies", "redis patterns", "caching layers",
]

# Content templates for realistic articles
CONTENT_TEMPLATES = [
    "Comprehensive guide to {topic} covering fundamental concepts, practical implementations, and real-world examples from production systems.",
    "Deep dive into {topic} exploring advanced patterns, performance considerations, and integration strategies with modern stack components.",
    "Building scalable systems with {topic}: A practical tutorial covering architecture decisions, implementation details, and operational best practices.",
    "Advanced {topic} patterns for enterprise applications: Lessons learned from building high-traffic distributed systems.",
    "{topic} in practice: A hands-on guide with code examples, troubleshooting tips, and migration strategies from monolith to modern architecture.",
]


def get_embedding_model():
    """Load the sentence-transformer model for embeddings."""
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    return SentenceTransformer('all-MiniLM-L6-v2')


def generate_article_data(source_id: int, index: int) -> dict:
    """Generate realistic article data for seeding."""
    topic = random.choice(ARTICLE_TOPICS)
    template = random.choice(CONTENT_TEMPLATES)
    
    return {
        "title": f"{topic.title()} - Part {index % 5 + 1}",
        "body": template.format(topic=topic),
        "topic": topic,
        "source_id": source_id,
        "content_type": random.choice(["tutorial", "guide", "reference", "case-study"]),
        "difficulty": random.choice(["beginner", "intermediate", "advanced"]),
        "tags": random.sample([topic, "architecture", "backend", "database", "devops"], 3),
    }


def writer_task(db: RushDB, model, source_id: int, articles_per_source: int) -> list:
    """
    Simulate a writer from a specific source.
    
    Each source creates multiple articles with embeddings.
    Returns list of created article IDs.
    """
    created_ids = []
    
    for i in range(articles_per_source):
        # Generate article data
        article_data = generate_article_data(source_id, i)
        
        # Generate embedding for the body
        embedding = model.encode(article_data["body"]).tolist()
        
        # Create record with embedding using upsert (idempotent)
        record = db.records.upsert(
            label="ARTICLE",
            data=article_data,
            options={
                "mergeBy": ["title", "source_id"],  # Idempotent based on unique combo
            },
            vectors=[{"propertyName": "body", "vector": embedding}]
        )
        
        created_ids.append(record.id)
        
        # Small delay to simulate real-world write patterns
        time.sleep(random.uniform(0.01, 0.05))
    
    return created_ids


def check_existing_data(db: RushDB) -> int:
    """Check if data already exists and return count."""
    try:
        result = db.records.find({
            "labels": ["ARTICLE"],
            "limit": 1
        })
        return result.total if hasattr(result, 'total') else (len(result.data) if hasattr(result, 'data') else 0)
    except Exception:
        return 0


def seed_data():
    """Main seeding function with concurrent writes."""
    print("\n" + "=" * 60)
    print("RUSHDB CONCURRENT WRITES - DATA SEEDING")
    print("=" * 60 + "\n")
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    url = os.getenv("RUSHDB_URL")
    
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        return
    
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    
    # Check for existing data
    existing = check_existing_data(db)
    if existing > 0:
        print(f"Found {existing} existing articles. Skipping seed (idempotent)...")
        return
    
    # Create vector index if it doesn't exist
    try:
        indexes = db.ai.indexes.find()
        existing_index = any(
            idx.get('label') == 'ARTICLE' and idx.get('propertyName') == 'body'
            for idx in (indexes.data if hasattr(indexes, 'data') else [])
        )
        
        if not existing_index:
            print("Creating vector index for ARTICLE.body...")
            db.ai.indexes.create({
                "label": "ARTICLE",
                "propertyName": "body",
                "sourceType": "external",
                "dimensions": 384,  # all-MiniLM-L6-v2 produces 384-dim vectors
                "similarityFunction": "cosine"
            })
            print("Vector index created successfully")
    except Exception as e:
        print(f"Index creation note: {e}")
    
    # Load embedding model
    model = get_embedding_model()
    
    # Calculate articles per source
    articles_per_source = ARTICLE_COUNT // MAX_WORKERS
    
    print(f"\nSeeding {ARTICLE_COUNT} articles using {MAX_WORKERS} concurrent writers...")
    print(f"Each source will write {articles_per_source} articles\n")
    
    start_time = time.time()
    
    # Execute concurrent writes using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(writer_task, db, model, source_id, articles_per_source): source_id
            for source_id in range(MAX_WORKERS)
        }
        
        # Collect results with progress bar
        with tqdm(total=ARTICLE_COUNT, desc="Creating articles", unit="article") as pbar:
            for future in as_completed(futures):
                source_id = futures[future]
                try:
                    created_ids = future.result()
                    pbar.update(len(created_ids))
                    print(f"  Source {source_id}: Created {len(created_ids)} articles")
                except Exception as e:
                    print(f"  Source {source_id}: Error - {e}")
    
    elapsed = time.time() - start_time
    
    # Verify data
    final_count = check_existing_data(db)
    
    print(f"\n✓ Seeding complete in {elapsed:.2f}s")
    print(f"  Total articles: {final_count}")
    print(f"  Concurrent writers: {MAX_WORKERS}")
    print(f"  Throughput: {ARTICLE_COUNT / elapsed:.1f} writes/sec")


if __name__ == "__main__":
    seed_data()
