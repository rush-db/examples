#!/usr/bin/env python3
"""
Seed script for RushDB SDK Tutorial.

Generates sample data: authors, categories, and articles with vector embeddings.
Safe to run multiple times — checks for existing data before seeding.

Usage:
    python seed.py
"""

import os
import sys
import time

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Configuration
BATCH_SIZE = 10
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality, 384 dimensions

# Sample data
AUTHORS = [
    {"name": "Alice Chen", "bio": "AI researcher specializing in NLP and transformer models", "expertise": ["AI", "NLP"]},
    {"name": "Bob Smith", "bio": "Senior backend engineer with focus on distributed systems", "expertise": ["Backend", "DevOps"]},
    {"name": "Carol Davis", "bio": "Full-stack developer and open source contributor", "expertise": ["Frontend", "Backend"]},
    {"name": "David Kim", "bio": "DevOps engineer and Kubernetes expert", "expertise": ["DevOps", "Backend"]},
    {"name": "Emma Wilson", "bio": "ML engineer focusing on production ML systems", "expertise": ["AI", "Backend"]},
]

CATEGORIES = [
    {"name": "AI", "description": "Artificial Intelligence and Machine Learning"},
    {"name": "Backend", "description": "Backend development and server-side technologies"},
    {"name": "Frontend", "description": "Frontend development and user interfaces"},
    {"name": "DevOps", "description": "DevOps, CI/CD, and infrastructure"},
]

ARTICLES = [
    # AI articles
    {"title": "Introduction to Machine Learning", "category": "AI",
     "content": "Machine learning is a subset of artificial intelligence that enables systems to learn from data and improve performance without being explicitly programmed. This tutorial covers supervised learning, unsupervised learning, and reinforcement learning fundamentals."},
    {"title": "Neural Networks Deep Dive", "category": "AI",
     "content": "Neural networks are computing systems inspired by biological neural networks. This article explores feedforward networks, backpropagation, activation functions, and the mathematics behind gradient descent optimization."},
    {"title": "Natural Language Processing with Transformers", "category": "AI",
     "content": "Transformers revolutionized NLP by introducing self-attention mechanisms. Learn about BERT, GPT, and how to fine-tune pretrained models for custom text classification and generation tasks."},
    {"title": "Reinforcement Learning Basics", "category": "AI",
     "content": "Reinforcement learning trains agents through reward signals. This guide covers Markov decision processes, Q-learning, policy gradients, and practical applications in robotics and game AI."},
    {"title": "Computer Vision with CNNs", "category": "AI",
     "content": "Convolutional neural networks excel at image recognition tasks. Explore convolutional layers, pooling operations,ResNet architectures, and techniques for object detection and semantic segmentation."},
    {"title": "Generative AI and Diffusion Models", "category": "AI",
     "content": "Diffusion models generate images by denoising random noise. This tutorial explains the forward and reverse diffusion processes, score-based generation, and applications in image synthesis."},
    # Backend articles
    {"title": "Building RESTful APIs with Python", "category": "Backend",
     "content": "REST APIs define how clients interact with servers. This guide covers HTTP methods, status codes, pagination, authentication with JWT tokens, and best practices for API design and documentation."},
    {"title": "Database Optimization Strategies", "category": "Backend",
     "content": "Slow queries kill application performance. Learn about indexing strategies, query optimization, connection pooling, and techniques for handling high-traffic workloads with PostgreSQL and Redis."},
    {"title": "Microservices Architecture Patterns", "category": "Backend",
     "content": "Microservices decompose applications into independent services. This article explores service discovery, API gateways, circuit breakers, event-driven communication, and deployment strategies."},
    {"title": "Authentication and Authorization Deep Dive", "category": "Backend",
     "content": "Security is paramount in modern applications. Understand OAuth 2.0, OpenID Connect, JWT validation, RBAC, and common vulnerabilities like injection attacks and session hijacking."},
    {"title": "Async Programming in Python", "category": "Backend",
     "content": "Async/await patterns enable high-concurrency servers without threads. Learn about event loops, coroutines, task scheduling, and when to use asyncio versus multiprocessing for I/O-bound work."},
    {"title": "Caching Strategies for Web Applications", "category": "Backend",
     "content": "Caching dramatically improves response times. Explore cache invalidation strategies, Redis patterns, CDN caching, HTTP caching headers, and techniques for maintaining consistency."},
    # Frontend articles
    {"title": "React Hooks Complete Guide", "category": "Frontend",
     "content": "Hooks revolutionized React development. Master useState, useEffect, useContext, and custom hooks to manage state, side effects, and share logic across components without class components."},
    {"title": "TypeScript for React Developers", "category": "Frontend",
     "content": "TypeScript adds static typing to JavaScript. Learn generics, discriminated unions, utility types, and how to build type-safe component APIs that catch errors at compile time."},
    {"title": "State Management with Redux Toolkit", "category": "Frontend",
     "content": "Redux Toolkit simplifies state management with createSlice and createAsyncThunk. This tutorial covers normalized state, selectors with reselect, and RTK Query for API caching."},
    {"title": "CSS Grid and Flexbox Layouts", "category": "Frontend",
     "content": "Modern CSS provides powerful layout systems. Master grid-template-areas, auto-fit, flex-shrink, and techniques for building responsive designs without media query spaghetti."},
    {"title": "Web Performance Optimization", "category": "Frontend",
     "content": "Fast websites rank higher and convert better. Learn about lazy loading, code splitting, tree shaking, Core Web Vitals, and techniques to reduce Largest Contentful Paint time."},
    {"title": "Testing React Applications", "category": "Frontend",
     "content": "Tests catch bugs before users do. This guide covers Jest, React Testing Library, mocking hooks, testing async operations, and strategies for achieving meaningful coverage."},
    # DevOps articles
    {"title": "Docker for Developers", "category": "DevOps",
     "content": "Containers package applications with dependencies. Learn Dockerfile syntax, multi-stage builds, docker-compose for local development, and best practices for production container security."},
    {"title": "Kubernetes Deployment Patterns", "category": "DevOps",
     "content": "Kubernetes orchestrates containerized applications at scale. Explore Deployments, Services, Ingress, ConfigMaps, and patterns for zero-downtime deployments and rollbacks."},
    {"title": "CI/CD Pipeline Construction", "category": "DevOps",
     "content": "Automated pipelines catch issues early. Learn about GitHub Actions, Jenkins pipelines, testing stages, artifact management, and deployment strategies like blue-green and canary releases."},
    {"title": "Infrastructure as Code with Terraform", "category": "DevOps",
     "content": "Terraform manages infrastructure through code. Master providers, resources, data sources, modules, state management, and techniques for managing multi-environment deployments."},
    {"title": "Monitoring and Observability", "category": "DevOps",
     "content": "Understand system behavior through metrics, logs, and traces. Explore Prometheus, Grafana, distributed tracing with Jaeger, and the three pillars of observability: logs, metrics, traces."},
    {"title": "Security Best Practices for Cloud Deployments", "category": "DevOps",
     "content": "Cloud security requires defense in depth. Learn about IAM policies, network segmentation, secret management, vulnerability scanning, and compliance frameworks for production workloads."},
    {"title": "Container Orchestration Strategies", "category": "DevOps",
     "content": "Scaling containers requires careful orchestration. Explore auto-scaling policies, pod disruption budgets, resource limits, and techniques for optimizing cluster utilization and cost."},
    {"title": "GitOps Implementation Guide", "category": "DevOps",
     "content": "GitOps uses Git as source of truth for infrastructure. Learn about ArgoCD, Flux, declarative configurations, and how to implement continuous deployment with audit trails."},
    {"title": "Database Backup and Recovery", "category": "DevOps",
     "content": "Data loss is catastrophic. Explore backup strategies, point-in-time recovery, replication configuration, and testing procedures to ensure business continuity during disasters."},
    {"title": "Service Mesh Architecture", "category": "DevOps",
     "content": "Service meshes handle cross-service communication. Learn about Istio, Linkerd, mTLS configuration, traffic splitting, and how to implement observability without code changes."},
    {"title": "Serverless Architecture Patterns", "category": "DevOps",
     "content": "Serverless abstracts servers entirely. Explore AWS Lambda, Azure Functions, cold start optimization, event-driven architectures, and when serverless makes sense versus containers."},
    {"title": "Network Security Fundamentals", "category": "DevOps",
     "content": "Network security protects data in transit. Learn about firewalls, VPNs, zero-trust architecture, network policies in Kubernetes, and techniques for securing service-to-service communication."},
]


def check_existing_data(db: RushDB) -> dict:
    """Check if data already exists to avoid duplicates."""
    result = {
        "has_data": False,
        "authors_count": 0,
        "categories_count": 0,
        "articles_count": 0,
    }
    
    authors = db.records.find({"labels": ["AUTHOR"], "limit": 1})
    categories = db.records.find({"labels": ["CATEGORY"], "limit": 1})
    articles = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    
    if authors.data:
        result["has_data"] = True
        result["authors_count"] = len(db.records.find({"labels": ["AUTHOR"]}).data)
        result["categories_count"] = len(db.records.find({"labels": ["CATEGORY"]}).data)
        result["articles_count"] = len(db.records.find({"labels": ["ARTICLE"]}).data)
    
    return result


def create_vector_index(db: RushDB) -> str:
    """Create vector index for article content if it doesn't exist."""
    try:
        # Check existing indexes
        existing = db.ai.indexes.find()
        for idx in existing.data:
            if idx.get("label") == "ARTICLE" and idx.get("propertyName") == "content":
                print(f"  Vector index already exists: {idx.get('__id')}")
                return idx.get("__id")
        
        # Create new index
        index = db.ai.indexes.create({
            "label": "ARTICLE",
            "propertyName": "content",
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine",
        })
        index_id = index.data["__id"]
        print(f"  Created vector index: {index_id}")
        return index_id
    except Exception as e:
        print(f"  Warning: Could not create vector index: {e}")
        return None


def generate_embeddings(model, texts: list) -> list:
    """Generate embeddings for a list of texts."""
    print(f"  Generating embeddings for {len(texts)} texts...")
    embeddings = model.encode(texts, show_progress_bar=False)
    return [emb.tolist() for emb in embeddings]


def seed_authors(db: RushDB) -> list:
    """Create author records."""
    print("\n[1/5] Creating authors...")
    authors = []
    
    for i, author_data in enumerate(AUTHORS):
        author = db.records.create(
            label="AUTHOR",
            data={
                "name": author_data["name"],
                "bio": author_data["bio"],
                "expertise": author_data["expertise"],
            }
        )
        authors.append(author)
        print(f"  Created: {author_data['name']} (expertise: {', '.join(author_data['expertise'])})")
    
    return authors


def seed_categories(db: RushDB) -> dict:
    """Create category records."""
    print("\n[2/5] Creating categories...")
    categories = {}
    
    for category_data in CATEGORIES:
        category = db.records.upsert(
            label="CATEGORY",
            data={
                "name": category_data["name"],
                "description": category_data["description"],
            },
            options={"mergeBy": ["name"]}
        )
        categories[category_data["name"]] = category
        print(f"  Created: {category_data['name']}")
    
    return categories


def seed_articles(db: RushDB, authors: list, categories: dict, model, index_id: str = None) -> list:
    """Create articles with vector embeddings."""
    print("\n[3/5] Creating articles with vector embeddings...")
    articles = []
    
    # Prepare content for embedding
    contents = [article["content"] for article in ARTICLES]
    embeddings = generate_embeddings(model, contents)
    
    # Create articles in batches
    for i, article_data in enumerate(ARTICLES):
        # Assign author round-robin
        author_idx = i % len(authors)
        author = authors[author_idx]
        
        # Create article with vector
        article = db.records.create(
            label="ARTICLE",
            data={
                "title": article_data["title"],
                "content": article_data["content"],
                "author_name": author.data.get("name", ""),
            },
            vectors=[{"propertyName": "content", "vector": embeddings[i]}]
        )
        articles.append(article)
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(ARTICLES)} articles...")
    
    print(f"  Total articles created: {len(articles)}")
    return articles


def create_relationships(db: RushDB, articles: list, authors: list, categories: dict):
    """Create relationships between articles, authors, and categories."""
    print("\n[4/5] Creating relationships...")
    
    for i, article in enumerate(articles):
        # Get author (round-robin assignment)
        author = authors[i % len(authors)]
        
        # Get category from article title
        article_data = ARTICLES[i]
        category_name = article_data["category"]
        category = categories.get(category_name)
        
        # Attach WRITTEN_BY relationship (article -> author)
        db.records.attach(
            source=article,
            target=author,
            options={"type": "WRITTEN_BY", "direction": "out"}
        )
        
        # Attach BELONGS_TO relationship (article -> category)
        if category:
            db.records.attach(
                source=article,
                target=category,
                options={"type": "BELONGS_TO", "direction": "out"}
            )
        
        # Attach EXPERTISE_IN relationship (author -> category)
        if category:
            db.records.attach(
                source=author,
                target=category,
                options={"type": "EXPERTISE_IN", "direction": "out"}
            )
        
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(articles)} article relationships...")
    
    print(f"  Total relationships created: {len(articles) * 3}")


def print_stats(db: RushDB):
    """Print current database statistics."""
    print("\n[5/5] Database statistics:")
    
    labels = db.labels.find()
    for label in labels:
        print(f"  - {label.name}: {label.count} records")
    
    # Get vector index stats
    try:
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            if idx.get("label") == "ARTICLE":
                stats = db.ai.indexes.stats(idx.get("__id"))
                if stats.data:
                    print(f"  - Vector index: {stats.data.get('indexedRecords', 0)} indexed")
    except Exception:
        pass


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RushDB SDK Tutorial - Data Seeder")
    print("=" * 60)
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)
    
    db = RushDB(api_key, url=os.getenv("RUSHDB_URL"))
    print("\n✓ Connected to RushDB")
    
    # Check existing data
    existing = check_existing_data(db)
    if existing["has_data"]:
        print(f"\n⚠ Data already exists in database:")
        print(f"  - Authors: {existing['authors_count']}")
        print(f"  - Categories: {existing['categories_count']}")
        print(f"  - Articles: {existing['articles_count']}")
        print("\nSkipping seed. Delete existing records to re-seed.")
        return
    
    # Load embedding model
    print("\nLoading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("✓ Model loaded")
    
    # Create vector index
    index_id = create_vector_index(db)
    
    # Seed data
    authors = seed_authors(db)
    categories = seed_categories(db)
    articles = seed_articles(db, authors, categories, model, index_id)
    create_relationships(db, articles, authors, categories)
    print_stats(db)
    
    print("\n" + "=" * 60)
    print("Seeding complete! Run 'python main.py' to start the tutorial.")
    print("=" * 60)


if __name__ == "__main__":
    main()
