#!/usr/bin/env python3
"""
Seed script for the Subgraph-Aware Prompt Assembly demo.

Creates a realistic knowledge graph with technical concepts, documents,
topics, and code examples, demonstrating RushDB's relationship modeling.

This script is idempotent - safe to run multiple times.
"""

import os
import sys
import json
from pathlib import Path

# Ensure we're using the local rushdb package
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize RushDB client
API_KEY = os.environ.get("RUSHDB_API_KEY")
if not API_KEY:
    print("Error: RUSHDB_API_KEY environment variable not set")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(API_KEY)


def check_data_exists() -> bool:
    """Check if data has already been seeded by looking for TOPIC records."""
    result = db.records.find({"labels": ["TOPIC"], "limit": 1})
    return len(result) > 0


def create_or_get_label(db: RushDB, label: str) -> str:
    """Helper to get label name - creates by usage in records."""
    return label


def seed_knowledge_graph():
    """Seed the knowledge graph with sample data."""
    print("\n🌱 Seeding knowledge graph...\n")
    
    # Check if already seeded
    if check_data_exists():
        print("✓ Knowledge graph already exists, skipping seed")
        return
    
    print("Creating TOPIC nodes...")
    
    # Create Topics (categories)
    topics_data = [
        {"name": "security", "priority": 1, "description": "Authentication, authorization, and security best practices"},
        {"name": "performance", "priority": 2, "description": "Caching, optimization, and performance tuning"},
        {"name": "architecture", "priority": 1, "description": "System design and architectural patterns"},
        {"name": "api-design", "priority": 2, "description": "REST APIs, GraphQL, and API patterns"},
        {"name": "databases", "priority": 2, "description": "Database design, queries, and optimization"},
    ]
    
    topics = {}
    for i, topic_data in enumerate(topics_data):
        topic = db.records.create(label="TOPIC", data=topic_data)
        topics[topic_data["name"]] = topic
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} topics...")
    print(f"  ✓ Created {len(topics_data)} topics")
    
    print("\nCreating CONCEPT nodes...")
    
    # Create Concepts
    concepts_data = [
        # Security concepts
        {"name": "authentication", "domain": "security", "definition": "The process of verifying the identity of a user or system."},
        {"name": "authorization", "domain": "security", "definition": "The process of determining what actions an authenticated user is permitted to perform."},
        {"name": "jwt-tokens", "domain": "security", "definition": "JSON Web Tokens - a compact, URL-safe means of representing claims to be transferred between two parties."},
        {"name": "oauth2", "domain": "security", "definition": "An authorization framework that enables applications to obtain limited access to user accounts."},
        {"name": "password-hashing", "domain": "security", "definition": "The process of converting passwords into irreversible hashed values for secure storage."},
        
        # Performance concepts
        {"name": "caching", "domain": "performance", "definition": "Storing frequently accessed data in a fast-access storage layer."},
        {"name": "cdn", "domain": "performance", "definition": "Content Delivery Network - a distributed server system that delivers web content based on geographic location."},
        {"name": "lazy-loading", "domain": "performance", "definition": "A design pattern that defers initialization of an object until it is needed."},
        {"name": "query-optimization", "domain": "performance", "definition": "The process of improving query performance through indexes, query planning, and data modeling."},
        
        # Architecture concepts
        {"name": "microservices", "domain": "architecture", "definition": "An architectural style that structures an application as a collection of loosely coupled services."},
        {"name": "event-sourcing", "domain": "architecture", "definition": "A pattern where state changes are stored as a sequence of events rather than just current state."},
        {"name": "cqrs", "domain": "architecture", "definition": "Command Query Responsibility Segregation - separating read and write operations into different models."},
        {"name": "api-gateway", "domain": "architecture", "definition": "A server that acts as a single entry point for a defined group of microservices."},
        
        # API Design concepts
        {"name": "rest", "domain": "api-design", "definition": "Representational State Transfer - an architectural style for distributed hypermedia systems."},
        {"name": "rate-limiting", "domain": "api-design", "definition": "Controlling the rate of requests a client can make to an API."},
        {"name": "versioning", "domain": "api-design", "definition": "The practice of managing API changes to maintain backward compatibility."},
        
        # Database concepts
        {"name": "acid", "domain": "databases", "definition": "Atomicity, Consistency, Isolation, Durability - the four properties guaranteed by database transactions."},
        {"name": "normalization", "domain": "databases", "definition": "The process of organizing data to reduce redundancy and improve data integrity."},
        {"name": "indexing", "domain": "databases", "definition": "Creating data structures to improve the speed of data retrieval operations."},
    ]
    
    concepts = {}
    for i, concept_data in enumerate(concepts_data):
        concept = db.records.create(label="CONCEPT", data=concept_data)
        concepts[concept_data["name"]] = concept
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} concepts...")
    print(f"  ✓ Created {len(concepts_data)} concepts")
    
    print("\nCreating DOCUMENT nodes...")
    
    # Create Documents
    documents_data = [
        # Security documents
        {"title": "JWT Authentication Implementation Guide", "type": "tutorial", "content": "This guide covers implementing JWT-based authentication including token generation, validation, and refresh strategies."},
        {"title": "OAuth 2.0 Flow Explained", "type": "explanation", "content": "Deep dive into OAuth 2.0 authorization flows including Authorization Code, Client Credentials, and Refresh Token flows."},
        {"title": "Secure Password Storage Best Practices", "type": "best-practices", "content": "Recommendations for hashing algorithms (bcrypt, Argon2), salt handling, and password policy enforcement."},
        {"title": "API Security Checklist", "type": "checklist", "content": "Essential security measures for APIs: input validation, HTTPS enforcement, rate limiting, and audit logging."},
        
        # Performance documents
        {"title": "Redis Caching Patterns", "type": "tutorial", "content": "Common caching patterns including Cache-Aside, Write-Through, and Read-Through with Redis implementation examples."},
        {"title": "Frontend Performance Optimization", "type": "guide", "content": "Techniques for improving frontend performance including lazy loading, code splitting, and asset optimization."},
        {"title": "Database Query Optimization", "type": "tutorial", "content": "Strategies for optimizing database queries including index usage, query plans, and connection pooling."},
        
        # Architecture documents
        {"title": "Microservices Communication Patterns", "type": "guide", "content": "Synchronous vs asynchronous communication, service discovery, and circuit breaker patterns."},
        {"title": "Event Sourcing vs Traditional Persistence", "type": "comparison", "content": "Comparing event sourcing with traditional CRUD persistence including trade-offs and use cases."},
        {"title": "CQRS Implementation Patterns", "type": "tutorial", "content": "Implementing CQRS with separate read and write models, event handlers, and synchronization strategies."},
        
        # API Design documents
        {"title": "RESTful API Design Principles", "type": "guide", "content": "Core principles of REST API design including resource naming, HTTP methods, and status codes."},
        {"title": "API Versioning Strategies", "type": "tutorial", "content": "URL versioning, header versioning, and query parameter approaches with migration strategies."},
        {"title": "Rate Limiting Algorithms", "type": "explanation", "content": "Token bucket, leaky bucket, and sliding window algorithms for implementing rate limiting."},
        
        # Database documents
        {"title": "Database Normalization Forms", "type": "tutorial", "content": "1NF through BCNF normalization with practical examples and when denormalization is appropriate."},
        {"title": "Indexing Strategies for Performance", "type": "guide", "content": "Choosing appropriate indexes, composite indexes, and covering indexes for query optimization."},
        {"title": "ACID Compliance in Modern Databases", "type": "explanation", "content": "Understanding transaction properties and how different databases achieve ACID compliance."},
    ]
    
    documents = {}
    for i, doc_data in enumerate(documents_data):
        doc = db.records.create(label="DOCUMENT", data=doc_data)
        documents[doc_data["title"]] = doc
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} documents...")
    print(f"  ✓ Created {len(documents_data)} documents")
    
    print("\nCreating EXAMPLE nodes...")
    
    # Create Examples
    examples_data = [
        {"title": "JWT Generation Example", "language": "python", "code": "import jwt\n\ntoken = jwt.encode({'user_id': 123}, 'secret', algorithm='HS256')"},
        {"title": "Redis Cache Pattern", "language": "python", "code": "def get_user(user_id):\n    cache_key = f'user:{user_id}'\n    cached = redis.get(cache_key)\n    if cached:\n        return json.loads(cached)\n    user = db.query('SELECT * FROM users WHERE id = ?', user_id)\n    redis.setex(cache_key, 3600, json.dumps(user))\n    return user"},
        {"title": "Rate Limiter Implementation", "language": "typescript", "code": "const rateLimiter = new RateLimiter({ max: 100, duration: 60 });\napp.use(rateLimiter.middleware());"},
        {"title": "API Gateway Setup", "language": "yaml", "code": "routes:\n  - path: /api/users\n    upstream: user-service:3000\n  - path: /api/orders\n    upstream: order-service:3000"},
        {"title": "Database Index Example", "language": "sql", "code": "CREATE INDEX idx_users_email ON users(email);\nCREATE INDEX idx_orders_user_date ON orders(user_id, created_at);"},
    ]
    
    examples = {}
    for i, example_data in enumerate(examples_data):
        example = db.records.create(label="EXAMPLE", data=example_data)
        examples[example_data["title"]] = example
    print(f"  ✓ Created {len(examples_data)} examples")
    
    print("\nCreating relationships...")
    
    # Create relationships using transaction
    with db.transactions.begin() as tx:
        
        # Link concepts to topics (BELONGS_TO)
        concept_topic_map = {
            "authentication": "security",
            "authorization": "security",
            "jwt-tokens": "security",
            "oauth2": "security",
            "password-hashing": "security",
            "caching": "performance",
            "cdn": "performance",
            "lazy-loading": "performance",
            "query-optimization": "performance",
            "microservices": "architecture",
            "event-sourcing": "architecture",
            "cqrs": "architecture",
            "api-gateway": "architecture",
            "rest": "api-design",
            "rate-limiting": "api-design",
            "versioning": "api-design",
            "acid": "databases",
            "normalization": "databases",
            "indexing": "databases",
        }
        
        for concept_name, topic_name in concept_topic_map.items():
            db.records.attach(
                source=concepts[concept_name],
                target=topics[topic_name],
                options={"type": "BELONGS_TO", "direction": "out"},
                transaction=tx
            )
        print("  ✓ Created BELONGS_TO relationships")
        
        # Link concepts to defining documents (DEFINES)
        concept_doc_map = {
            "jwt-tokens": "JWT Authentication Implementation Guide",
            "oauth2": "OAuth 2.0 Flow Explained",
            "password-hashing": "Secure Password Storage Best Practices",
            "caching": "Redis Caching Patterns",
            "lazy-loading": "Frontend Performance Optimization",
            "query-optimization": "Database Query Optimization",
            "microservices": "Microservices Communication Patterns",
            "event-sourcing": "Event Sourcing vs Traditional Persistence",
            "cqrs": "CQRS Implementation Patterns",
            "rest": "RESTful API Design Principles",
            "versioning": "API Versioning Strategies",
            "rate-limiting": "Rate Limiting Algorithms",
            "normalization": "Database Normalization Forms",
            "indexing": "Indexing Strategies for Performance",
            "acid": "ACID Compliance in Modern Databases",
        }
        
        for concept_name, doc_title in concept_doc_map.items():
            db.records.attach(
                source=concepts[concept_name],
                target=documents[doc_title],
                options={"type": "DEFINES", "direction": "out"},
                transaction=tx
            )
        print("  ✓ Created DEFINES relationships")
        
        # Link concepts with RELATES_TO relationships
        relates = [
            ("authentication", "authorization"),
            ("jwt-tokens", "authentication"),
            ("oauth2", "authentication"),
            ("caching", "query-optimization"),
            ("microservices", "api-gateway"),
            ("event-sourcing", "cqrs"),
            ("rest", "versioning"),
            ("normalization", "indexing"),
            ("microservices", "event-sourcing"),
            ("authentication", "rate-limiting"),
        ]
        
        for source_name, target_name in relates:
            db.records.attach(
                source=concepts[source_name],
                target=concepts[target_name],
                options={"type": "RELATES_TO", "direction": "out"},
                transaction=tx
            )
        print("  ✓ Created RELATES_TO relationships")
        
        # Link examples to concepts (ILLUSTRATES)
        example_concept_map = {
            "JWT Generation Example": "jwt-tokens",
            "Redis Cache Pattern": "caching",
            "Rate Limiter Implementation": "rate-limiting",
            "API Gateway Setup": "api-gateway",
            "Database Index Example": "indexing",
        }
        
        for example_title, concept_name in example_concept_map.items():
            db.records.attach(
                source=examples[example_title],
                target=concepts[concept_name],
                options={"type": "ILLUSTRATES", "direction": "out"},
                transaction=tx
            )
        print("  ✓ Created ILLUSTRATES relationships")
        
        # Create DEPENDS_ON relationships
        dependencies = [
            ("authorization", "authentication"),  # Authorization depends on being authenticated
            ("cqrs", "event-sourcing"),
            ("microservices", "rest"),
        ]
        
        for source_name, target_name in dependencies:
            db.records.attach(
                source=concepts[source_name],
                target=concepts[target_name],
                options={"type": "DEPENDS_ON", "direction": "out"},
                transaction=tx
            )
        print("  ✓ Created DEPENDS_ON relationships")
    
    print("\n✅ Knowledge graph seeded successfully!")
    print(f"   - {len(topics)} topics")
    print(f"   - {len(concepts)} concepts")
    print(f"   - {len(documents)} documents")
    print(f"   - {len(examples)} examples")
    print(f"   - Multiple relationship types")


def save_schema():
    """Save the graph schema to data folder for reference."""
    schema = {
        "labels": [
            {
                "name": "TOPIC",
                "description": "Subject areas or categories",
                "properties": ["name", "priority", "description"]
            },
            {
                "name": "CONCEPT",
                "description": "Technical concepts or terms",
                "properties": ["name", "domain", "definition"]
            },
            {
                "name": "DOCUMENT",
                "description": "Articles, tutorials, guides",
                "properties": ["title", "type", "content"]
            },
            {
                "name": "EXAMPLE",
                "description": "Code examples or use cases",
                "properties": ["title", "language", "code"]
            }
        ],
        "relationship_types": [
            {"type": "BELONGS_TO", "from": "CONCEPT", "to": "TOPIC", "description": "Concept belongs to a topic"},
            {"type": "DEFINES", "from": "DOCUMENT", "to": "CONCEPT", "description": "Document defines/explains concept"},
            {"type": "RELATES_TO", "from": "*", "to": "*", "description": "General relationship between nodes"},
            {"type": "ILLUSTRATES", "from": "EXAMPLE", "to": "CONCEPT", "description": "Example demonstrates concept"},
            {"type": "DEPENDS_ON", "from": "CONCEPT", "to": "CONCEPT", "description": "Prerequisite dependency"}
        ]
    }
    
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "graph_schema.json", "w") as f:
        json.dump(schema, f, indent=2)
    
    print(f"\n📋 Schema saved to {data_dir / 'graph_schema.json'}")


if __name__ == "__main__":
    print("=" * 60)
    print("   Subgraph-Aware Prompt Assembly - Knowledge Graph Seeder")
    print("=" * 60)
    
    seed_knowledge_graph()
    save_schema()
    
    print("\n" + "=" * 60)
    print("   Seeding complete! Run 'python main.py' to test.")
    print("=" * 60)
