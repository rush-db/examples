"""
Seed script for Knowledge Staleness Detection tutorial.

Creates sample knowledge articles with realistic metadata including:
- Publication and update timestamps
- View counts reflecting access patterns
- Category assignments
- Author information
- Dependency relationships for refresh chains

Run this script once before main.py to populate the database with test data.
"""

import os
import sys
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()


def get_db():
    """Initialize RushDB connection."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)
    return RushDB(api_key)


def clear_existing_data(db):
    """Remove any existing test data to ensure idempotency."""
    print("Clearing existing data...")
    
    # Delete relationships first
    db.records.delete_many({
        "labels": ["RefreshLink"],
        "where": {}
    })
    
    # Delete articles
    db.records.delete_many({
        "labels": ["Article"],
        "where": {}
    })
    
    # Delete categories
    db.records.delete_many({
        "labels": ["Category"],
        "where": {}
    })
    
    # Delete authors
    db.records.delete_many({
        "labels": ["Author"],
        "where": {}
    })
    
    print("✓ Cleared existing data")


def create_categories(db):
    """Create knowledge base categories."""
    categories_data = [
        {"name": "backend", "description": "Server-side development", "priority": "high"},
        {"name": "security", "description": "Security best practices", "priority": "critical"},
        {"name": "devops", "description": "DevOps and infrastructure", "priority": "medium"},
        {"name": "testing", "description": "Testing and quality assurance", "priority": "medium"},
    ]
    
    categories = {}
    for cat_data in categories_data:
        category = db.records.create(
            label="Category",
            data=cat_data
        )
        categories[cat_data["name"]] = category
        print(f"  ✓ Created category: {cat_data['name']}")
    
    return categories


def create_authors(db):
    """Create author records."""
    authors_data = [
        {"name": "Alice Chen", "email": "alice@example.com", "expertise": ["backend", "security"]},
        {"name": "Bob Martinez", "email": "bob@example.com", "expertise": ["devops", "testing"]},
        {"name": "Carol Williams", "email": "carol@example.com", "expertise": ["security", "backend"]},
        {"name": "David Kim", "email": "david@example.com", "expertise": ["devops", "backend"]},
    ]
    
    authors = {}
    for author_data in authors_data:
        author = db.records.create(
            label="Author",
            data=author_data
        )
        authors[author_data["name"]] = author
    
    return authors


def create_articles(db, categories, authors):
    """Create knowledge base articles with realistic metadata."""
    
    articles_data = [
        {
            "title": "Building REST APIs with FastAPI",
            "category": "backend",
            "author": "Alice Chen",
            "viewCount": 45,
            "daysSinceUpdate": 45,
            "content": "Complete guide to building REST APIs using FastAPI framework...",
            "editFrequency": 2,
        },
        {
            "title": "Database Design Patterns",
            "category": "backend",
            "author": "Carol Williams",
            "viewCount": 12,
            "daysSinceUpdate": 180,
            "content": "Essential database design patterns for scalable applications...",
            "editFrequency": 0.5,
        },
        {
            "title": "Microservices Communication",
            "category": "backend",
            "author": "Alice Chen",
            "viewCount": 89,
            "daysSinceUpdate": 60,
            "content": "Patterns for inter-service communication in microservices...",
            "editFrequency": 1,
        },
        {
            "title": "Authentication Best Practices",
            "category": "security",
            "author": "Carol Williams",
            "viewCount": 156,
            "daysSinceUpdate": 30,
            "content": "Implementing secure authentication in web applications...",
            "editFrequency": 3,
        },
        {
            "title": "Kubernetes Deployment Guide",
            "category": "devops",
            "author": "David Kim",
            "viewCount": 34,
            "daysSinceUpdate": 90,
            "content": "Step-by-step guide to deploying applications on Kubernetes...",
            "editFrequency": 1,
        },
        {
            "title": "Graph Database Fundamentals",
            "category": "backend",
            "author": "Alice Chen",
            "viewCount": 23,
            "daysSinceUpdate": 120,
            "content": "Introduction to graph databases and their use cases...",
            "editFrequency": 0.5,
        },
        {
            "title": "API Rate Limiting Strategies",
            "category": "backend",
            "author": "David Kim",
            "viewCount": 67,
            "daysSinceUpdate": 15,
            "content": "Implementing effective rate limiting for APIs...",
            "editFrequency": 2,
        },
        {
            "title": "Caching Layer Architecture",
            "category": "backend",
            "author": "Alice Chen",
            "viewCount": 41,
            "daysSinceUpdate": 25,
            "content": "Designing efficient caching layers for web applications...",
            "editFrequency": 1.5,
        },
        {
            "title": "Testing Best Practices",
            "category": "testing",
            "author": "Bob Martinez",
            "viewCount": 78,
            "daysSinceUpdate": 55,
            "content": "Comprehensive guide to testing methodologies...",
            "editFrequency": 2,
        },
        {
            "title": "Security Vulnerability Checklist",
            "category": "security",
            "author": "Carol Williams",
            "viewCount": 203,
            "daysSinceUpdate": 7,
            "content": "OWASP-based security vulnerability assessment checklist...",
            "editFrequency": 4,
        },
        {
            "title": "Performance Optimization Techniques",
            "category": "backend",
            "author": "David Kim",
            "viewCount": 95,
            "daysSinceUpdate": 40,
            "content": "Techniques for optimizing application performance...",
            "editFrequency": 1,
        },
        {
            "title": "CI/CD Pipeline Setup",
            "category": "devops",
            "author": "Bob Martinez",
            "viewCount": 52,
            "daysSinceUpdate": 35,
            "content": "Setting up continuous integration and deployment pipelines...",
            "editFrequency": 2.5,
        },
    ]
    
    articles = []
    
    for idx, article_data in enumerate(articles_data):
        # Calculate last updated date
        last_updated = datetime.now() - timedelta(days=article_data["daysSinceUpdate"])
        
        # Create article record
        article = db.records.create(
            label="Article",
            data={
                "title": article_data["title"],
                "category": article_data["category"],
                "viewCount": article_data["viewCount"],
                "lastUpdated": last_updated.isoformat(),
                "content": article_data["content"],
                "editFrequency": article_data["editFrequency"],
            }
        )
        
        # Attach to category
        category = categories[article_data["category"]]
        db.records.attach(
            source=article,
            target=category,
            options={"type": "BELONGS_TO"}
        )
        
        # Attach to author
        author = authors[article_data["author"]]
        db.records.attach(
            source=article,
            target=author,
            options={"type": "WRITTEN_BY"}
        )
        
        articles.append(article)
        
        if (idx + 1) % 4 == 0:
            print(f"  ... {idx + 1}/{len(articles_data)} articles created")
        print(f"  ✓ Created article: {article_data['title']}")
    
    return articles


def create_refresh_dependencies(db, articles):
    """Create refresh dependency relationships between articles."""
    
    # Build a map of articles by title for reference
    article_map = {}
    all_articles = db.records.find({"labels": ["Article"]})
    for art in all_articles.data:
        article_map[art["title"]] = art
    
    # Define refresh dependencies
    dependencies = [
        ("Authentication Best Practices", "Microservices Communication"),
        ("Authentication Best Practices", "Testing Best Practices"),
        ("Building REST APIs with FastAPI", "API Rate Limiting Strategies"),
        ("Building REST APIs with FastAPI", "Caching Layer Architecture"),
        ("Database Design Patterns", "Graph Database Fundamentals"),
        ("Kubernetes Deployment Guide", "CI/CD Pipeline Setup"),
        ("Performance Optimization Techniques", "Caching Layer Architecture"),
        ("Performance Optimization Techniques", "Database Design Patterns"),
    ]
    
    for source_title, target_title in dependencies:
        source = article_map.get(source_title)
        target = article_map.get(target_title)
        
        if source and target:
            db.records.create(
                label="RefreshLink",
                data={"type": "refresh_dependency", "priority": "high"}
            )
            
            # Get the RefreshLink we just created
            refresh_links = db.records.find({"labels": ["RefreshLink"]})
            refresh_link = refresh_links.data[-1] if refresh_links.data else None
            
            if refresh_link:
                # Attach source article to refresh link
                db.records.attach(
                    source=source,
                    target=refresh_link,
                    options={"type": "REQUIRES"}
                )
                # Attach target article to refresh link
                db.records.attach(
                    source=refresh_link,
                    target=target,
                    options={"type": "TRIGGERS"}
                )
                print(f"  ✓ Created refresh link: {source_title} → {target_title}")


def main():
    """Run the seed script."""
    print("\n" + "=" * 60)
    print("Knowledge Base Seeding Script")
    print("=" * 60 + "\n")
    
    db = get_db()
    
    # Clear existing test data
    clear_existing_data(db)
    
    # Create categories
    print("\nCreating categories...")
    categories = create_categories(db)
    
    # Create authors
    print("\nCreating authors...")
    authors = create_authors(db)
    
    # Create articles
    print("\nCreating articles...")
    articles = create_articles(db, categories, authors)
    
    # Create refresh dependencies
    print("\nCreating refresh dependencies...")
    create_refresh_dependencies(db, articles)
    
    # Summary
    all_articles = db.records.find({"labels": ["Article"]})
    all_categories = db.records.find({"labels": ["Category"]})
    all_authors = db.records.find({"labels": ["Author"]})
    refresh_links = db.records.find({"labels": ["RefreshLink"]})
    
    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"  ✓ Created {len(all_articles.data)} articles")
    print(f"  ✓ Created {len(all_categories.data)} categories")
    print(f"  ✓ Created {len(all_authors.data)} authors")
    print(f"  ✓ Created {len(refresh_links.data)} refresh links")
    print("\nRun 'python main.py' to analyze staleness and trigger refreshes.\n")


if __name__ == "__main__":
    main()
