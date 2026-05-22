"""
Seed script for the cross-document reference tutorial.

Creates a sample documentation system with:
- Authors (content creators)
- Articles (documents)
- Tags (categorization)
- Categories (organizational buckets)

All relationships are created to demonstrate cross-document referencing patterns.

This script is idempotent — safe to run multiple times.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

TOKEN = os.getenv("RUSHDB_TOKEN")
if not TOKEN:
    raise ValueError("RUSHDB_TOKEN not found in environment. Copy .env.example to .env")

db = RushDB(TOKEN)

# Sample data
AUTHORS = [
    {"name": "Alice Chen", "email": "alice@techcorp.io", "expertise": "backend", "years_exp": 8},
    {"name": "Bob Martinez", "email": "bob@techcorp.io", "expertise": "frontend", "years_exp": 5},
    {"name": "Carol Williams", "email": "carol@techcorp.io", "expertise": "devops", "years_exp": 10},
    {"name": "David Kim", "email": "david@techcorp.io", "expertise": "security", "years_exp": 6},
    {"name": "Eva Johnson", "email": "eva@techcorp.io", "expertise": "data", "years_exp": 7},
]

TAGS = [
    {"name": "python", "category": "language"},
    {"name": "typescript", "category": "language"},
    {"name": "async", "category": "concept"},
    {"name": "security", "category": "concept"},
    {"name": "performance", "category": "concept"},
    {"name": "testing", "category": "process"},
    {"name": "docker", "category": "tool"},
    {"name": "kubernetes", "category": "tool"},
]

CATEGORIES = [
    {"name": "Architecture", "description": "System design and architecture patterns"},
    {"name": "Development", "description": "Coding practices and patterns"},
    {"name": "Infrastructure", "description": "DevOps and deployment"},
    {"name": "Security", "description": "Security best practices"},
]

ARTICLES = [
    {
        "title": "Understanding Async/Await in Python",
        "slug": "understanding-async-await-python",
        "status": "published",
        "read_time": 12,
        "content": "A deep dive into asynchronous programming patterns...",
    },
    {
        "title": "Building REST APIs with FastAPI",
        "slug": "building-rest-apis-fastapi",
        "status": "published",
        "read_time": 18,
        "content": "Creating scalable web services with FastAPI...",
    },
    {
        "title": "Docker Best Practices for Production",
        "slug": "docker-best-practices-production",
        "status": "published",
        "read_time": 15,
        "content": "Containerization patterns for production environments...",
    },
    {
        "title": "Kubernetes Deployment Strategies",
        "slug": "kubernetes-deployment-strategies",
        "status": "published",
        "read_time": 20,
        "content": "Blue-green, canary, and rolling deployments...",
    },
    {
        "title": "TypeScript Generics Explained",
        "slug": "typescript-generics-explained",
        "status": "published",
        "read_time": 14,
        "content": "Mastering generic types in TypeScript...",
    },
    {
        "title": "Implementing Zero Trust Security",
        "slug": "implementing-zero-trust-security",
        "status": "published",
        "read_time": 22,
        "content": "A comprehensive guide to zero trust architecture...",
    },
    {
        "title": "React Performance Optimization",
        "slug": "react-performance-optimization",
        "status": "draft",
        "read_time": 16,
        "content": "Techniques for optimizing React applications...",
    },
    {
        "title": "Database Indexing Strategies",
        "slug": "database-indexing-strategies",
        "status": "published",
        "read_time": 19,
        "content": "Optimizing query performance with proper indexing...",
    },
    {
        "title": "GraphQL Schema Design",
        "slug": "graphql-schema-design",
        "status": "published",
        "read_time": 17,
        "content": "Designing effective GraphQL schemas...",
    },
    {
        "title": "Microservices Communication Patterns",
        "slug": "microservices-communication-patterns",
        "status": "published",
        "read_time": 21,
        "content": "Synchronous vs asynchronous communication...",
    },
    {
        "title": "Unit Testing Strategies",
        "slug": "unit-testing-strategies",
        "status": "draft",
        "read_time": 11,
        "content": "Writing maintainable and effective tests...",
    },
    {
        "title": "Caching Patterns for APIs",
        "slug": "caching-patterns-apis",
        "status": "published",
        "read_time": 13,
        "content": "Implementing efficient caching strategies...",
    },
]

# Cross-references: article_index -> [referenced_article_indices]
ARTICLE_REFERENCES = {
    0: [1, 4],      # Async article references FastAPI and TypeScript
    1: [0, 11],     # FastAPI references Async and Caching
    2: [3, 11],     # Docker references Kubernetes and Caching
    3: [2],         # Kubernetes references Docker
    4: [0],         # TypeScript references Async
    5: [2, 3],      # Security references Docker and Kubernetes
    7: [1],         # Indexing references FastAPI
    8: [1, 4],      # GraphQL references FastAPI and TypeScript
    9: [1, 2, 3],   # Microservices references FastAPI, Docker, Kubernetes
    11: [1],        # Caching references FastAPI
}


def clear_existing_data():
    """Remove all records with our tutorial labels to ensure clean seeding."""
    labels_to_clear = ["ARTICLE", "AUTHOR", "TAG", "CATEGORY"]
    for label in labels_to_clear:
        db.records.delete_many({"labels": [label], "where": {}})
    print("Cleared existing tutorial data.")


def seed_authors():
    """Create author records."""
    print("\n--- Seeding Authors ---")
    authors = []
    for author_data in AUTHORS:
        author = db.records.create(label="AUTHOR", data=author_data)
        authors.append(author)
        print(f"  Created author: {author['name']} ({author['email']})")
    return authors


def seed_categories():
    """Create category records."""
    print("\n--- Seeding Categories ---")
    categories = []
    for cat_data in CATEGORIES:
        category = db.records.create(label="CATEGORY", data=cat_data)
        categories.append(category)
        print(f"  Created category: {category['name']}")
    return categories


def seed_tags():
    """Create tag records."""
    print("\n--- Seeding Tags ---")
    tags = []
    for tag_data in TAGS:
        tag = db.records.create(label="TAG", data=tag_data)
        tags.append(tag)
        print(f"  Created tag: {tag['name']}")
    return tags


def seed_articles(authors, categories, tags):
    """Create article records and their relationships."""
    print("\n--- Seeding Articles ---")
    articles = []
    
    for i, article_data in enumerate(ARTICLES):
        # Assign articles to authors in round-robin fashion
        author = authors[i % len(authors)]
        
        # Assign to random category
        category = random.choice(categories)
        
        # Assign random tags (2-4 tags per article)
        article_tags = random.sample(tags, min(random.randint(2, 4), len(tags)))
        
        # Create the article
        article = db.records.create(label="ARTICLE", data=article_data)
        articles.append(article)
        
        # Create relationships
        # Author -> Article (WRITTEN_BY)
        db.records.attach(
            source=author,
            target=article,
            options={"type": "WRITTEN_BY", "direction": "out"}
        )
        
        # Article -> Category (BELONGS_TO)
        db.records.attach(
            source=article,
            target=category,
            options={"type": "BELONGS_TO", "direction": "out"}
        )
        
        # Article -> Tags (TAGGED_WITH)
        for tag in article_tags:
            db.records.attach(
                source=article,
                target=tag,
                options={"type": "TAGGED_WITH", "direction": "out"}
            )
        
        print(f"  Created article: '{article['title']}'")
        print(f"    ├── Author: {author['name']}")
        print(f"    ├── Category: {category['name']}")
        print(f"    └── Tags: {[t['name'] for t in article_tags]}")
    
    return articles


def seed_cross_references(articles):
    """Create cross-document references between articles."""
    print("\n--- Seeding Cross-Document References ---")
    
    for source_idx, target_indices in ARTICLE_REFERENCES.items():
        source_article = articles[source_idx]
        for target_idx in target_indices:
            if target_idx < len(articles):
                target_article = articles[target_idx]
                db.records.attach(
                    source=source_article,
                    target=target_article,
                    options={"type": "REFERENCES", "direction": "out"}
                )
                print(f"  {source_article['title']} -> REFERENCES -> {target_article['title']}")


def verify_seed():
    """Verify the seed data was created correctly."""
    print("\n--- Verifying Seed Data ---")
    
    for label in ["AUTHOR", "ARTICLE", "TAG", "CATEGORY"]:
        result = db.labels.find({"where": {}})
        label_counts = {lbl.name: lbl.count for lbl in result.data}
        count = label_counts.get(label, 0)
        print(f"  {label}: {count} records")
    
    # Count relationships
    all_articles = db.records.find({"labels": ["ARTICLE"], "limit": 100})
    print(f"  Total articles in system: {len(all_articles.data)}")


def main():
    """Run the complete seeding process."""
    print("=" * 60)
    print("RushDB Cross-Document Reference Tutorial - Seed Script")
    print("=" * 60)
    
    # Clear existing data for clean seeding
    clear_existing_data()
    
    # Seed entities
    authors = seed_authors()
    categories = seed_categories()
    tags = seed_tags()
    articles = seed_articles(authors, categories, tags)
    
    # Seed cross-document references
    seed_cross_references(articles)
    
    # Verify
    verify_seed()
    
    print("\n" + "=" * 60)
    print("Seeding complete! Run 'python main.py' to see the tutorial.")
    print("=" * 60)


if __name__ == "__main__":
    main()
