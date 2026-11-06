#!/usr/bin/env python3
"""
Seed script for Subgraph Extraction Tutorial.

Creates a Software Architecture Knowledge Graph in RushDB with:
- CONCEPT nodes: Design patterns, architectural styles, principles
- TECHNOLOGY nodes: Languages, frameworks, tools
- PATTERN nodes: Implementation patterns and their contexts

The graph is designed to demonstrate various subgraph extraction
strategies for context-window optimization.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)

# =====================
# KNOWLEDGE BASE DATA
# =====================

CONCEPTS = [
    # Architectural Concepts
    {"name": "microservices", "description": "Architecture style breaking apps into small, independent services"},
    {"name": "event_driven", "description": "Pattern where system reactions are triggered by events"},
    {"name": "cqrs", "description": "Command Query Responsibility Segregation - separate read/write models"},
    {"name": "event_sourcing", "description": "Store state changes as sequence of events"},
    {"name": "domain_driven_design", "description": "Software design based on domain model"},
    {"name": "hexagonal_architecture", "description": "Ports and adapters pattern for separation of concerns"},
    {"name": "layered_architecture", "description": "Traditional n-tier architecture with distinct layers"},
    {"name": "service_mesh", "description": "Infrastructure layer for service-to-service communication"},
    {"name": "api_gateway", "description": "Single entry point for client requests to backend services"},
    {"name": "circuit_breaker", "description": "Pattern preventing cascading failures between services"},
    
    # Design Principles
    {"name": "solid_principles", "description": "Single responsibility, open-closed, liskov substitution, interface segregation, dependency inversion"},
    {"name": "dry", "description": "Don't Repeat Yourself - eliminate code duplication"},
    {"name": "kiss", "description": "Keep It Simple, Stupid - prefer simplicity"},
    {"name": "yagni", "description": "You Aren't Gonna Need It - avoid speculative code"},
    {"name": "fail_fast", "description": "Fail early in development cycle rather than at runtime"},
    
    # Quality Attributes
    {"name": "scalability", "description": "System's ability to handle growing load"},
    {"name": "availability", "description": "System uptime percentage over time"},
    {"name": "maintainability", "description": "Ease of modifying system without introducing defects"},
    {"name": "observability", "description": "Ability to understand internal system state from outputs"},
    {"name": "resilience", "description": "System's ability to recover from failures"},
]

TECHNOLOGIES = [
    # Languages
    {"name": "Python", "description": "High-level interpreted language with dynamic typing"},
    {"name": "TypeScript", "description": "JavaScript with static typing and compiled output"},
    {"name": "Go", "description": "Statically typed, compiled language designed at Google"},
    {"name": "Rust", "description": "Systems programming language focused on safety and performance"},
    {"name": "Java", "description": "Object-oriented language with strong typing and JVM"},
    
    # Frameworks
    {"name": "FastAPI", "description": "Modern Python web framework with async support"},
    {"name": "Spring Boot", "description": "Java-based framework for building production applications"},
    {"name": "Express", "description": "Minimalist Node.js web framework"},
    {"name": "NestJS", "description": "Progressive Node.js framework with TypeScript"},
    {"name": "gRPC", "description": "High-performance RPC framework using Protocol Buffers"},
    {"name": "GraphQL", "description": "Query language for APIs and runtime for executing queries"},
    {"name": "Django", "description": "Python web framework following MVC pattern"},
    
    # Infrastructure
    {"name": "Kubernetes", "description": "Container orchestration platform for automating deployment"},
    {"name": "Docker", "description": "Platform for containerizing applications"},
    {"name": "Redis", "description": "In-memory data structure store for caching/messaging"},
    {"name": "PostgreSQL", "description": "Object-relational database with advanced features"},
    {"name": "MongoDB", "description": "Document-oriented NoSQL database"},
    {"name": "RabbitMQ", "description": "Message broker implementing AMQP protocol"},
    {"name": "Prometheus", "description": "Systems monitoring and alerting toolkit"},
    {"name": "Nginx", "description": "Web server and reverse proxy server"},
]

PATTERNS = [
    {"name": "database_per_service", "description": "Each microservice owns its data store", "problem": "Distributed data management complexity", "solved_by": "event_sourcing,cqrs"},
    {"name": "sidecar_pattern", "description": "Deploy helper components alongside service containers", "problem": "Cross-cutting concerns in microservices", "solved_by": "hexagonal_architecture"},
    {"name": "strangler_fig", "description": "Incrementally migrate legacy system by replacing pieces", "problem": "Legacy system modernization", "solved_by": "layered_architecture"},
    {"name": "backends_for_frontends", "description": "Separate backend APIs per frontend experience", "problem": "Different client requirements conflict", "solved_by": "api_gateway"},
    {"name": " Saga_pattern", "description": "Manage distributed transactions across services", "problem": "ACID transactions across services", "solved_by": "event_driven"},
    {"name": "outbox_pattern", "description": "Reliable event publishing using transaction log table", "problem": "Dual writes causing inconsistency", "solved_by": "event_sourcing"},
    {"name": "bulkhead_pattern", "description": "Isolate resources per call type to prevent cascade failures", "problem": "Shared resource exhaustion", "solved_by": "circuit_breaker,service_mesh"},
    {"name": "materialized_view", "description": "Pre-computed query results for read optimization", "problem": "Complex joins hurting read performance", "solved_by": "cqrs"},
]

# Relationship definitions
RELATIONSHIPS = {
    "IMPLEMENTS": [
        # Technologies implement concepts
        ("FastAPI", "microservices"), ("FastAPI", "event_driven"), ("FastAPI", "api_gateway"),
        ("Spring Boot", "microservices"), ("Spring Boot", "domain_driven_design"),
        ("NestJS", "microservices"), ("NestJS", "solid_principles"),
        ("gRPC", "microservices"), ("gRPC", "circuit_breaker"),
        ("Kubernetes", "microservices"), ("Kubernetes", "service_mesh"),
        ("GraphQL", "api_gateway"), ("GraphQL", "cqrs"),
    ],
    "DEPENDS_ON": [
        # Technology dependencies
        ("FastAPI", "Python"), ("Django", "Python"),
        ("NestJS", "TypeScript"), ("Express", "TypeScript"),
        ("Spring Boot", "Java"),
        ("gRPC", "Go"),
        ("Kubernetes", "Docker"),
        ("Redis", "Docker"),
        ("Prometheus", "Kubernetes"),
        ("Nginx", "Kubernetes"),
    ],
    "USES": [
        # Technologies use concepts
        ("PostgreSQL", "database_per_service"),
        ("MongoDB", "database_per_service"),
        ("RabbitMQ", "event_driven"), ("RabbitMQ", "Saga_pattern"),
        ("Redis", "circuit_breaker"), ("Redis", "cache"),
        ("Prometheus", "observability"),
        ("Docker", "fail_fast"),
    ],
    "SOLVES": [
        # Patterns solve problems
        ("bulkhead_pattern", "availability"), ("bulkhead_pattern", "resilience"),
        ("database_per_service", "scalability"), ("database_per_service", "maintainability"),
        ("Saga_pattern", "maintainability"),
        ("circuit_breaker", "resilience"), ("circuit_breaker", "availability"),
        ("materialized_view", "scalability"),
    ],
    "ENABLES": [
        # Concepts enable other concepts
        ("microservices", "scalability"),
        ("microservices", "maintainability"),
        ("microservices", "availability"),
        ("event_driven", "resilience"),
        ("event_sourcing", "observability"),
        ("cqrs", "scalability"),
        ("service_mesh", "observability"),
        ("circuit_breaker", "fail_fast"),
    ],
    "FOLLOWS": [
        # Technologies follow principles
        ("Python", "kiss"), ("Python", "dry"),
        ("Go", "kiss"), ("Go", "fail_fast"),
        ("Rust", "solid_principles"),
        ("TypeScript", "solid_principles"),
    ],
}


def clear_existing_data():
    """Remove existing tutorial data to ensure clean state."""
    print("Clearing existing tutorial data...")
    for label in ["SEED_TUTORIAL_MARKER"]:
        try:
            db.records.delete_many({"labels": [label], "where": {}})
        except Exception:
            pass


def create_nodes():
    """Create all concept, technology, and pattern nodes."""
    print("\n--- Creating Nodes ---")
    
    concept_records = []
    for i, concept in enumerate(CONCEPTS):
        record = db.records.create(
            label="CONCEPT",
            data={
                "name": concept["name"],
                "description": concept["description"],
                "type": "architectural",
                "seed_marker": True
            }
        )
        concept_records.append((concept["name"], record))
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(CONCEPTS)} concepts...")
    
    tech_records = []
    for i, tech in enumerate(TECHNOLOGIES):
        record = db.records.create(
            label="TECHNOLOGY",
            data={
                "name": tech["name"],
                "description": tech["description"],
                "category": categorize_tech(tech["name"]),
                "seed_marker": True
            }
        )
        tech_records.append((tech["name"], record))
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(TECHNOLOGIES)} technologies...")
    
    pattern_records = []
    for i, pattern in enumerate(PATTERNS):
        record = db.records.create(
            label="PATTERN",
            data={
                "name": pattern["name"],
                "description": pattern["description"],
                "problem": pattern["problem"],
                "seed_marker": True
            }
        )
        pattern_records.append((pattern["name"], record))
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(PATTERNS)} patterns...")
    
    print(f"\n  Total nodes created: {len(concept_records) + len(tech_records) + len(pattern_records)}")
    return concept_records, tech_records, pattern_records


def categorize_tech(name: str) -> str:
    """Categorize technology by type."""
    languages = ["Python", "TypeScript", "Go", "Rust", "Java"]
    frameworks = ["FastAPI", "Spring Boot", "Express", "NestJS", "Django", "gRPC", "GraphQL"]
    infra = ["Kubernetes", "Docker", "Redis", "PostgreSQL", "MongoDB", "RabbitMQ", "Prometheus", "Nginx"]
    
    if name in languages:
        return "language"
    elif name in frameworks:
        return "framework"
    elif name in infra:
        return "infrastructure"
    return "other"


def create_relationships(concept_records, tech_records, pattern_records):
    """Create all relationships between nodes."""
    print("\n--- Creating Relationships ---")
    
    # Build lookup dictionaries
    concept_lookup = {name: record for name, record in concept_records}
    tech_lookup = {name: record for name, record in tech_records}
    pattern_lookup = {name: record for name, record in pattern_records}
    
    all_records = {**concept_lookup, **tech_lookup, **pattern_lookup}
    
    total_rels = sum(len(rels) for rels in RELATIONSHIPS.values())
    created = 0
    
    for rel_type, relationships in RELATIONSHIPS.items():
        for source_name, target_name in relationships:
            source = all_records.get(source_name)
            target = all_records.get(target_name)
            
            if source and target:
                db.records.attach(
                    source=source,
                    target=target,
                    options={"type": rel_type, "direction": "out"}
                )
                created += 1
                if created % 10 == 0:
                    print(f"  Created {created}/{total_rels} relationships...")
    
    print(f"\n  Total relationships created: {created}")


def verify_data():
    """Verify data was created correctly."""
    print("\n--- Verifying Data ---")
    
    labels = {}
    for label in ["CONCEPT", "TECHNOLOGY", "PATTERN"]:
        result = db.records.find({"labels": [label], "where": {}})
        labels[label] = result.total
        print(f"  {label}: {result.total} records")
    
    # Count relationships
    rel_types = list(RELATIONSHIPS.keys())
    for rel_type in rel_types:
        # Query relationships of this type
        result = db.records.find({
            "labels": ["CONCEPT", "TECHNOLOGY", "PATTERN"],
            "where": {}
        })
        
    total_rels = sum(len(rels) for rels in RELATIONSHIPS.values())
    print(f"  Total relationships: {total_rels}")
    print(f"  Total nodes: {sum(labels.values())}")
    
    return labels, total_rels


def main():
    print("=" * 50)
    print("SUBGRAPH EXTRACTION TUTORIAL - DATA SEEDING")
    print("=" * 50)
    
    print("\nThis will create a Software Architecture Knowledge Graph")
    print("for demonstrating subgraph extraction strategies.")
    
    # Check for existing data
    existing = db.records.find({"labels": ["CONCEPT"], "where": {}})
    if existing.total > 0:
        print(f"\nFound {existing.total} existing CONCEPT records.")
        response = input("Skip seeding? (y/n): ").strip().lower()
        if response == 'y':
            print("Skipping seed. Run 'python seed.py --force' to re-seed.")
            return
    
    clear_existing_data()
    concept_records, tech_records, pattern_records = create_nodes()
    create_relationships(concept_records, tech_records, pattern_records)
    labels, total_rels = verify_data()
    
    print("\n" + "=" * 50)
    print("SEEDING COMPLETE")
    print("=" * 50)
    print("\nRun 'python main.py' to explore subgraph extraction strategies.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        # Force clear and reseed
        print("Force mode enabled - clearing all data and reseeding")
        for label in ["CONCEPT", "TECHNOLOGY", "PATTERN"]:
            try:
                db.records.delete_many({"labels": [label], "where": {}})
            except Exception:
                pass
    
    main()
