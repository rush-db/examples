#!/usr/bin/env python3
"""
Seed script for real-time stream processing demo.
Generates mock authors, articles, and initial stream events.
"""

import os
import sys
import time
import random
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB

fake = Faker()
Faker.seed(42)
random.seed(42)

# Categories and domains for realistic data
CATEGORIES = ["technology", "science", "business", "health", "entertainment"]
TAGS = ["ai", "machine-learning", "data-science", "cloud", "security", "startup", "research"]


def wait_for_rushdb(db, max_retries=30):
    """Wait for RushDB to be available."""
    print("Connecting to RushDB...")
    for i in range(max_retries):
        try:
            db.labels.find()
            print("Connected successfully!")
            return True
        except Exception as e:
            print(f"Attempt {i+1}/{max_retries}: {e}")
            time.sleep(2)
    return False


def create_vector_index(db, label, property_name, dimensions):
    """Create a vector index for a label's property."""
    print(f"\nCreating vector index for {label}.{property_name}...")
    try:
        response = db.ai.indexes.create({
            "label": label,
            "propertyName": property_name,
            "sourceType": "external",
            "dimensions": dimensions,
            "similarityFunction": "cosine"
        })
        print(f"  Index created: {response.data.get('__id', 'unknown')}")
        return response.data.get("__id")
    except Exception as e:
        # Index might already exist
        existing = db.ai.indexes.find()
        for idx in existing.data:
            if idx.get("label") == label and idx.get("propertyName") == property_name:
                print(f"  Index already exists: {idx.get('__id')}")
                return idx.get("__id")
        print(f"  Warning: {e}")
        return None


def seed_authors(db, count=50):
    """Seed author records."""
    print(f"\nSeeding {count} authors...")
    authors = []
    
    for i in range(count):
        author = db.records.create(
            label="AUTHOR",
            data={
                "id": f"author_{i+1:04d}",
                "name": fake.name(),
                "email": fake.email(),
                "bio": fake.text(max_nb_chars=150),
                "domain": random.choice(CATEGORIES),
                "followers": random.randint(100, 50000),
                "joined_at": fake.date_between(start_date="-5y", end_date="-1y").isoformat()
            }
        )
        authors.append(author)
        
        if (i + 1) % 25 == 0:
            print(f"  Created {i+1}/{count} authors")
    
    print(f"  Total: {len(authors)} authors")
    return authors


def seed_articles(db, authors, count=100):
    """Seed article records with content for vector embedding."""
    print(f"\nSeeding {count} articles...")
    articles = []
    
    # Content templates for realistic embeddings
    content_templates = [
        "Exploring the latest advances in {topic} and their implications for the industry. "
        "This comprehensive guide covers practical applications, best practices, and future trends. "
        "Learn how organizations are leveraging {topic} to drive innovation and efficiency.",
        
        "A deep dive into {topic} fundamentals and advanced concepts. "
        "We examine real-world case studies, compare different approaches, and provide actionable insights. "
        "Perfect for practitioners looking to stay ahead of the curve.",
        
        "Understanding {topic} from first principles. "
        "This article breaks down complex ideas into digestible explanations with hands-on examples. "
        "Includes code samples, architecture diagrams, and performance benchmarks.",
        
        "The future of {topic} and what it means for developers. "
        "Industry experts share their predictions, challenges, and opportunities ahead. "
        "Essential reading for anyone working in the {domain} space."
    ]
    
    topics = ["neural networks", "distributed systems", "data pipelines", "cloud architecture",
              "machine learning", "kubernetes", "microservices", "blockchain", "edge computing", "quantum computing"]
    
    for i in range(count):
        topic = random.choice(topics)
        domain = random.choice(CATEGORIES)
        template = random.choice(content_templates)
        content = template.format(topic=topic, domain=domain)
        
        author = random.choice(authors)
        published_at = fake.date_time_between(start_date="-30d", end_date="now")
        
        article = db.records.create(
            label="ARTICLE",
            data={
                "id": f"article_{i+1:04d}",
                "title": fake.catch_phrase(),
                "content": content,
                "summary": fake.sentence(nb_words=20),
                "category": domain,
                "tags": random.sample(TAGS, k=random.randint(2, 5)),
                "view_count": random.randint(100, 50000),
                "published_at": published_at.isoformat()
            }
        )
        
        # Link article to author
        db.records.attach(
            source=article,
            target=author,
            options={"type": "WRITTEN_BY", "direction": "out"}
        )
        
        articles.append(article)
        
        if (i + 1) % 25 == 0:
            print(f"  Created {i+1}/{count} articles")
    
    print(f"  Total: {len(articles)} articles")
    return articles


def seed_initial_events(db, articles, count=50):
    """Seed initial stream events."""
    print(f"\nSeeding {count} initial stream events...")
    events = []
    
    event_types = ["article.view", "article.like", "article.share", "article.comment"]
    
    for i in range(count):
        article = random.choice(articles)
        event_type = random.choice(event_types)
        timestamp = datetime.now() - timedelta(minutes=random.randint(1, 1440))
        
        event = db.records.create(
            label="STREAM_EVENT",
            data={
                "id": f"evt_init_{i+1:04d}",
                "type": event_type,
                "target_id": article.data.get("id"),
                "timestamp": timestamp.isoformat(),
                "source_ip": fake.ipv4(),
                "user_agent": fake.user_agent()
            }
        )
        
        # Link event to article
        db.records.attach(
            source=event,
            target=article,
            options={"type": "TRIGGERS_UPDATE", "direction": "out"}
        )
        
        events.append(event)
        
        if (i + 1) % 25 == 0:
            print(f"  Created {i+1}/{count} events")
    
    print(f"  Total: {len(events)} events")
    return events


def print_statistics(db):
    """Print current database statistics."""
    print("\n" + "="*50)
    print("DATABASE STATISTICS")
    print("="*50)
    
    labels = db.labels.find()
    print("\nLabels and record counts:")
    for label in labels.data:
        print(f"  {label['name']}: {label['count']} records")
    
    indexes = db.ai.indexes.find()
    print("\nVector indexes:")
    for idx in indexes.data:
        stats = db.ai.indexes.stats(idx["__id"])
        print(f"  {idx['label']}.{idx['propertyName']}: {stats.data.get('indexedRecords', 0)} indexed")
    
    print("\n" + "="*50)


def main():
    """Main seed function."""
    print("\n" + "="*60)
    print("RUSHDB STREAM PROCESSING DEMO - DATA SEEDING")
    print("="*60)
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("Please copy .env.example to .env and add your API key")
        sys.exit(1)
    
    db = RushDB(api_key)
    
    # Wait for RushDB to be ready
    if not wait_for_rushdb(db):
        print("ERROR: Could not connect to RushDB")
        sys.exit(1)
    
    # Check for existing data
    existing = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    if existing.data:
        print("\n⚠️  Data already exists in the database.")
        response = input("Do you want to clear existing data and reseed? (y/N): ")
        if response.lower() != 'y':
            print("Skipping seed operation.")
            print_statistics(db)
            return
        
        # Clear existing data
        print("\nClearing existing data...")
        for label in ["STREAM_EVENT", "ARTICLE", "AUTHOR"]:
            try:
                db.records.delete_many({"labels": [label]})
            except:
                pass
    
    # Create vector index for articles
    dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))
    article_index_id = create_vector_index(db, "ARTICLE", "content", dimensions)
    
    # Seed data
    authors = seed_authors(db, count=50)
    articles = seed_articles(db, authors, count=100)
    events = seed_initial_events(db, articles, count=50)
    
    # Print final statistics
    print_statistics(db)
    
    print("\n✅ Data seeding complete!")
    print("\nNext step: Run `python main.py` to start the stream processor")


if __name__ == "__main__":
    main()
