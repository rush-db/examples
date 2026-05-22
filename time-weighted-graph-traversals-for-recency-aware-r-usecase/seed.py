#!/usr/bin/env python3
"""
Seed script: Creates mock users, articles, and interaction data.

This script is IDEMPOTENT — it checks for existing data and skips
seeding if the workspace is already populated.
"""

import os
import sys
import math
import random
import datetime
from datetime import timezone, timedelta
from typing import Optional

from dotenv import load_dotenv
from faker import Faker
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize
fake = Faker()
Faker.seed(42)
random.seed(42)

# Embedding model (local, no API key needed)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

# Configuration
NUM_USERS = 20
NUM_ARTICLES = 50
ARTICLES_PER_USER_MIN = 1
ARTICLES_PER_USER_MAX = 5
READS_PER_USER_MIN = 5
READS_PER_USER_MAX = 15
FOLLOW_COUNT_MIN = 2
FOLLOW_COUNT_MAX = 8


def time_decay(published_at: datetime.datetime, half_life_hours: int = 24) -> float:
    """Exponential decay: score halves every `half_life_hours`."""
    age_hours = (datetime.datetime.now(timezone.utc) - published_at).total_seconds() / 3600
    return math.exp(-0.693 * age_hours / half_life_hours)


def check_already_seeded(db: RushDB) -> bool:
    """Check if data already exists in this workspace."""
    try:
        labels = db.labels.find({})
        label_names = [l.name for l in labels]
        if "USER" in label_names and "ARTICLE" in label_names:
            # Count records
            users = db.records.find({"labels": ["USER"], "limit": 1})
            if len(users) > 0:
                return True
        return False
    except Exception:
        return False


def create_users(db: RushDB, num_users: int) -> list:
    """Create user records."""
    print(f"\n{'='*60}")
    print(f"Creating {num_users} users...")
    print(f"{'='*60}")
    
    users = []
    
    # Create users in batches
    batch_size = 10
    for i in range(0, num_users, batch_size):
        batch_end = min(i + batch_size, num_users)
        batch_data = []
        
        for j in range(i, batch_end):
            name = fake.unique.name().lower().replace(" ", "_")
            batch_data.append({
                "id": f"user_{j:03d}",
                "name": name,
                "email": f"{name}@example.com"
            })
        
        with db.transactions.begin() as tx:
            for data in batch_data:
                user = db.records.create(
                    label="USER",
                    data=data,
                    transaction=tx
                )
                users.append(user)
        
        print(f"  Created users {i+1}-{batch_end}/{num_users}")
    
    return users


def create_follow_relationships(db: RushDB, users: list):
    """Create FOLLOWS relationships between users."""
    print(f"\n{'='*60}")
    print(f"Creating follow relationships...")
    print(f"{'='*60}")
    
    user_ids = [u.id for u in users]
    follow_count = 0
    
    for user in users:
        # Each user follows a random subset of other users
        num_follows = random.randint(FOLLOW_COUNT_MIN, FOLLOW_COUNT_MAX)
        potential_follows = [uid for uid in user_ids if uid != user.id]
        follows = random.sample(potential_follows, min(num_follows, len(potential_follows)))
        
        with db.transactions.begin() as tx:
            for target_id in follows:
                target = db.records.find_by_id(target_id)
                if target:
                    db.records.attach(
                        source=user,
                        target=target,
                        options={"type": "FOLLOWS"},
                        transaction=tx
                    )
                    follow_count += 1
    
    print(f"  Created {follow_count} follow relationships")


def create_articles(db: RushDB, users: list, model: SentenceTransformer) -> list:
    """Create article records with embedded vectors."""
    print(f"\n{'='*60}")
    print(f"Creating {NUM_ARTICLES} articles with vectors...")
    print(f"{'='*60}")
    
    # Article templates by category
    article_templates = [
        {
            "category": "AI/ML",
            "templates": [
                "Understanding Transformer Architecture: A Deep Dive into Attention Mechanisms",
                "GPT-5 Released: What New Capabilities Does It Bring to Developers?",
                "Building Production-Ready RAG Systems: Lessons from 100 Deployments",
                "Fine-Tuning vs RAG: When to Use Each Approach for AI Applications",
                "The Future of Code Generation: AI Tools Reshaping Software Development"
            ]
        },
        {
            "category": "Programming",
            "templates": [
                "Rust 2.0 Announced with Major Performance Improvements and New Features",
                "TypeScript 6.0: What's New and How to Migrate Your Codebase",
                "Building Microservices with Go: Best Practices for 2026",
                "The State of WebAssembly: From Browser Curiosity to Server Revolution",
                "Modern Python: Async/Await Patterns That Actually Improve Performance"
            ]
        },
        {
            "category": "Cloud/DevOps",
            "templates": [
                "Kubernetes 2.0: Simplified Orchestration for Edge Computing",
                "Zero-Trust Architecture: Implementing Security Without Compromising UX",
                "Terraform vs Pulumi: Infrastructure as Code in 2026",
                "Building Resilient Systems: Chaos Engineering Beyond Netflix",
                "GitOps Best Practices: Streamlining Deployments at Scale"
            ]
        },
        {
            "category": "Data Engineering",
            "templates": [
                "Apache Iceberg: The Table Format Revolutionizing Data Lakes",
                "Real-Time Analytics with Flink: Building Streaming Pipelines",
                "dbt 2.0: How Data Transformation Evolved in the Modern Stack",
                "Vector Databases Compared: Pinecone, Weaviate, and Chroma at Scale",
                "The Rise of the Data Mesh: Decentralizing Ownership in Enterprises"
            ]
        },
        {
            "category": "Startups/Tech",
            "templates": [
                "YC's 2026 Batch: The 20 Most Interesting AI Startups to Watch",
                "Remote Work 3.0: How Distributed Teams Are Building Culture",
                "The Great API Economy: How Companies Are Monetizing Data",
                "Sustainable Tech: How Startups Are Tackling Climate Change",
                "The Creator Economy Grows Up: Building Businesses on Social Platforms"
            ]
        }
    ]
    
    articles = []
    all_templates = []
    for cat in article_templates:
        all_templates.extend(cat["templates"])
    
    # Shuffle templates
    random.shuffle(all_templates)
    
    # Generate timestamps (spread over last 7 days)
    now = datetime.datetime.now(timezone.utc)
    
    batch_size = 10
    for i in range(0, NUM_ARTICLES, batch_size):
        batch_end = min(i + batch_size, NUM_ARTICLES)
        batch_articles = []
        batch_vectors = []
        
        for j in range(i, batch_end):
            template_idx = j % len(all_templates)
            title = all_templates[template_idx]
            
            # Generate body content
            body = fake.paragraph(nb_sentences=5) + " " + fake.paragraph(nb_sentences=5)
            
            # Timestamp: random point in last 7 days, more recent bias
            hours_ago = random.randint(1, 168) * random.random()  # 1-168 hours, weighted toward recent
            published_at = now - timedelta(hours=hours_ago)
            
            # Assign to a random author
            author = random.choice(users)
            
            article_data = {
                "id": f"article_{j:03d}",
                "title": title,
                "body": body,
                "published_at": published_at.isoformat(),
                "category": article_templates[template_idx % len(article_templates)]["category"]
            }
            
            batch_articles.append({
                "record": article_data,
                "author": author
            })
        
        # Compute embeddings for this batch
        texts = [item["record"]["body"] for item in batch_articles]
        embeddings = model.encode(texts, show_progress_bar=False)
        
        # Create records with vectors
        with db.transactions.begin() as tx:
            for k, item in enumerate(batch_articles):
                article = db.records.create(
                    label="ARTICLE",
                    data=item["record"],
                    vectors=[{"propertyName": "body", "vector": embeddings[k].tolist()}],
                    transaction=tx
                )
                
                # Attach author relationship
                db.records.attach(
                    source=item["author"],
                    target=article,
                    options={"type": "PUBLISHED"},
                    transaction=tx
                )
                
                articles.append(article)
        
        print(f"  Created articles {i+1}-{batch_end}/{NUM_ARTICLES}")
    
    return articles


def create_read_interactions(db: RushDB, users: list, articles: list):
    """Create READ relationships (user's reading history)."""
    print(f"\n{'='*60}")
    print(f"Creating reading history interactions...")
    print(f"{'='*60}")
    
    article_ids = [a.id for a in articles]
    total_reads = 0
    
    for i, user in enumerate(users):
        num_reads = random.randint(READS_PER_USER_MIN, READS_PER_USER_MAX)
        read_articles = random.sample(article_ids, min(num_reads, len(article_ids)))
        
        # Create reads with timestamps
        now = datetime.datetime.now(timezone.utc)
        
        with db.transactions.begin() as tx:
            for article_id in read_articles:
                article = db.records.find_by_id(article_id)
                if article:
                    read_time = now - timedelta(hours=random.randint(1, 72))
                    db.records.attach(
                        source=user,
                        target=article,
                        options={"type": "READ", "properties": {"read_at": read_time.isoformat()}},
                        transaction=tx
                    )
                    total_reads += 1
        
        if (i + 1) % 5 == 0:
            print(f"  Created reading history for {i+1}/{len(users)} users")
    
    print(f"  Created {total_reads} total read interactions")


def create_vector_index(db: RushDB):
    """Create a vector index for article body search."""
    print(f"\n{'='*60}")
    print(f"Creating vector index on ARTICLE.body...")
    print(f"{'='*60}")
    
    # Check if index already exists
    existing_indexes = db.ai.indexes.find({})
    for idx in existing_indexes.data:
        if idx["label"] == "ARTICLE" and idx["propertyName"] == "body":
            print(f"  Index already exists, skipping creation")
            return
    
    index = db.ai.indexes.create({
        "label": "ARTICLE",
        "propertyName": "body",
        "sourceType": "external",
        "dimensions": EMBEDDING_DIMENSIONS,
        "similarityFunction": "cosine"
    })
    
    print(f"  Created vector index: {index.data.get('__id')}")


def main():
    """Main seeding function."""
    print("\n" + "="*60)
    print("  RUSHDB SEED SCRIPT")
    print("  Time-Weighted Graph Traversal Demo Data")
    print("="*60)
    
    # Initialize RushDB
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("\n[ERROR] RUSHDB_API_TOKEN not found in environment")
        print("Please create a .env file with your RushDB API token")
        print("Get your token at: https://app.rushdb.com")
        sys.exit(1)
    
    db = RushDB(api_token)
    
    # Check if already seeded
    if check_already_seeded(db):
        print("\n[INFO] Workspace appears to already have data.")
        print("[INFO] Skipping seed to avoid duplicates.")
        print("[INFO] Delete existing USER and ARTICLE records to re-seed.")
        sys.exit(0)
    
    # Initialize embedding model
    print("\n[INFO] Loading embedding model (this may take a moment)...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"[INFO] Model loaded: {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS}d)")
    
    # Create data
    users = create_users(db, NUM_USERS)
    create_follow_relationships(db, users)
    articles = create_articles(db, users, model)
    create_read_interactions(db, users, articles)
    create_vector_index(db)
    
    # Summary
    print(f"\n{'='*60}")
    print("  SEEDING COMPLETE")
    print(f"{'='*60}")
    print(f"  Users created:        {NUM_USERS}")
    print(f"  Articles created:     {NUM_ARTICLES}")
    print(f"  Interactions created: ~{NUM_USERS * (READS_PER_USER_MIN + READS_PER_USER_MAX) // 2}")
    print(f"\n  Run 'python main.py' to see the recommendation demo.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
