#!/usr/bin/env python3
"""
Seed script: Populates RushDB with a software architecture knowledge graph.

Creates nodes for: DOCUMENTATION, CONCEPT, DECISION, TRADEOFF
with typed edges forming the reasoning chain:
  DOCUMENTATION → CONTAINS → CONCEPT → LEADS_TO → DECISION → HAS_TRADEOFF → TRADEOFF

Run once before main.py. Idempotent — safe to run multiple times.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
db = RushDB(token=os.getenv("RUSHDB_TOKEN"))

# Sample data for the software architecture domain
SEED_DATA = {
    "documentation": [
        {
            "slug": "caching-guide",
            "title": "Distributed Systems Caching Guide",
            "body": "Caching is a fundamental technique in distributed systems for reducing latency and load. This guide covers cache placement strategies, invalidation approaches, and consistency models.",
            "domain": "distributed-systems"
        },
        {
            "slug": "microservices-patterns",
            "title": "Microservices Communication Patterns",
            "body": "Explore synchronous and asynchronous communication patterns in microservices. Learn about service discovery, load balancing, and fault tolerance mechanisms.",
            "domain": "microservices"
        },
        {
            "slug": "data-consistency",
            "title": "Data Consistency in Modern Applications",
            "body": "Understanding CAP theorem implications. Compare strong consistency, eventual consistency, and causal consistency models for distributed data stores.",
            "domain": "distributed-systems"
        }
    ],
    "concepts": [
        {
            "slug": "cache_coherency",
            "name": "Cache Coherency",
            "description": "The consistency of data shared between multiple caches and the main memory. Critical for systems requiring strong consistency guarantees.",
            "category": "caching"
        },
        {
            "slug": "eventual_consistency",
            "name": "Eventual Consistency",
            "description": "A consistency model where updates propagate to all replicas eventually, allowing stale reads during the propagation window.",
            "category": "consistency"
        },
        {
            "slug": "distributed_hash_table",
            "name": "Distributed Hash Table",
            "description": "A decentralized distributed system that provides lookup service similar to a hash table, used in peer-to-peer caching systems.",
            "category": "caching"
        },
        {
            "slug": "cache_invalidation",
            "name": "Cache Invalidation",
            "description": "Strategies for removing or updating stale cache entries, including time-based expiration, event-driven invalidation, and explicit invalidation.",
            "category": "caching"
        },
        {
            "slug": "circuit_breaker",
            "name": "Circuit Breaker Pattern",
            "description": "Prevents cascading failures by detecting failures and encapsulating logic to prevent a failure from constantly recurring.",
            "category": "resilience"
        }
    ],
    "decisions": [
        {
            "slug": "cache_placement_decision",
            "title": "Cache Placement Strategy",
            "context": "Choosing where to place cache layers in a distributed system",
            "recommendation": "Use a tiered approach: client-side cache for frequently read data, server-side cache for shared state, and CDN for static assets.",
            "domain": "caching"
        },
        {
            "slug": "invalidation_strategy_decision",
            "title": "Cache Invalidation Strategy",
            "context": "Determining when and how to invalidate cached entries",
            "recommendation": "Implement a hybrid approach: TTL-based expiration for general cases, event-driven invalidation for critical data, and manual purging for administrative actions.",
            "domain": "caching"
        },
        {
            "slug": "consistency_model_decision",
            "title": "Consistency Model Selection",
            "context": "Balancing consistency requirements with performance needs",
            "recommendation": "Default to eventual consistency for non-critical operations. Reserve strong consistency for financial transactions, inventory management, and user permissions.",
            "domain": "consistency"
        },
        {
            "slug": "service_discovery_decision",
            "title": "Service Discovery Approach",
            "context": "How services locate and communicate with each other",
            "recommendation": "Use DNS-based discovery with health checks for simple cases. Consider service mesh for complex microservice architectures requiring advanced traffic management.",
            "domain": "microservices"
        }
    ],
    "tradeoffs": [
        {
            "slug": "latency_vs_consistency",
            "dimension": "Latency vs Consistency",
            "pro": "Strong consistency provides predictable behavior but adds 10-50ms latency per operation due to coordination overhead.",
            "con": "Eventual consistency offers lower latency but risks stale reads during propagation windows.",
            "weight": "performance"
        },
        {
            "slug": "availability_vs_consistency",
            "dimension": "Availability vs Consistency",
            "pro": "Eventual consistency allows the system to remain available during network partitions.",
            "con": "Strong consistency may require sacrificing availability during split-brain scenarios.",
            "weight": "reliability"
        },
        {
            "slug": "cache_memory_vs_accuracy",
            "dimension": "Cache Memory vs Accuracy",
            "pro": "Larger caches reduce miss rates and improve hit ratio.",
            "con": "More cached data increases stale-read risk and memory costs.",
            "weight": "resource"
        },
        {
            "slug": "complexity_vs_flexibility",
            "dimension": "Implementation Complexity vs Flexibility",
            "pro": "Simple TTL-based invalidation is easy to implement and understand.",
            "con": "Event-driven invalidation provides fresher data but requires additional infrastructure.",
            "weight": "maintenance"
        }
    ]
}

# Relationships between concepts and decisions
CONCEPT_TO_DECISIONS = {
    "cache_coherency": ["cache_placement_decision", "consistency_model_decision"],
    "eventual_consistency": ["consistency_model_decision", "invalidation_strategy_decision"],
    "cache_invalidation": ["invalidation_strategy_decision"],
    "distributed_hash_table": ["cache_placement_decision"],
    "circuit_breaker": ["service_discovery_decision"]
}

# Relationships between decisions and tradeoffs
DECISION_TO_TRADEOFFS = {
    "cache_placement_decision": ["cache_memory_vs_accuracy", "complexity_vs_flexibility"],
    "invalidation_strategy_decision": ["latency_vs_consistency", "cache_memory_vs_accuracy"],
    "consistency_model_decision": ["latency_vs_consistency", "availability_vs_consistency"],
    "service_discovery_decision": ["complexity_vs_flexibility"]
}


def clear_existing_data():
    """Remove all seeded data to ensure idempotent re-seeding."""
    print("Clearing existing seeded data...")
    labels_to_delete = ["DOCUMENTATION", "CONCEPT", "DECISION", "TRADEOFF", "CONCLUSION"]
    for label in labels_to_delete:
        result = db.records.delete_many({"labels": [label], "where": {}})
        if result.data.get("deleted", 0) > 0:
            print(f"  Deleted {result.data['deleted']} {label} records")


def create_nodes():
    """Create all node types and establish relationships."""
    print("\nCreating DOCUMENTATION nodes...")
    docs = {}
    for doc_data in SEED_DATA["documentation"]:
        doc = db.records.upsert(
            label="DOCUMENTATION",
            data=doc_data,
            options={"mergeBy": ["slug"]}
        )
        docs[doc_data["slug"]] = doc
        print(f"  Created: {doc_data['title']}")

    print("\nCreating CONCEPT nodes...")
    concepts = {}
    for concept_data in SEED_DATA["concepts"]:
        concept = db.records.upsert(
            label="CONCEPT",
            data=concept_data,
            options={"mergeBy": ["slug"]}
        )
        concepts[concept_data["slug"]] = concept
        print(f"  Created: {concept_data['name']}")

    print("\nCreating DECISION nodes...")
    decisions = {}
    for decision_data in SEED_DATA["decisions"]:
        decision = db.records.upsert(
            label="DECISION",
            data=decision_data,
            options={"mergeBy": ["slug"]}
        )
        decisions[decision_data["slug"]] = decision
        print(f"  Created: {decision_data['title']}")

    print("\nCreating TRADEOFF nodes...")
    tradeoffs = {}
    for tradeoff_data in SEED_DATA["tradeoffs"]:
        tradeoff = db.records.upsert(
            label="TRADEOFF",
            data=tradeoff_data,
            options={"mergeBy": ["slug"]}
        )
        tradeoffs[tradeoff_data["slug"]] = tradeoff
        print(f"  Created: {tradeoff_data['dimension']}")

    return docs, concepts, decisions, tradeoffs


def create_relationships(concepts, decisions, tradeoffs):
    """Create typed edges between nodes."""
    print("\nCreating relationships...")
    
    # Link concepts to decisions
    print("  CONCEPT → LEADS_TO → DECISION")
    for concept_slug, decision_slugs in CONCEPT_TO_DECISIONS.items():
        concept = concepts[concept_slug]
        for decision_slug in decision_slugs:
            decision = decisions[decision_slug]
            db.records.attach(
                source=concept,
                target=decision,
                options={"type": "LEADS_TO", "direction": "out"}
            )

    # Link decisions to tradeoffs
    print("  DECISION → HAS_TRADEOFF → TRADEOFF")
    for decision_slug, tradeoff_slugs in DECISION_TO_TRADEOFFS.items():
        decision = decisions[decision_slug]
        for tradeoff_slug in tradeoff_slugs:
            tradeoff = tradeoffs[tradeoff_slug]
            db.records.attach(
                source=decision,
                target=tradeoff,
                options={"type": "HAS_TRADEOFF", "direction": "out"}
            )

    print("  All relationships created.")


def verify_graph():
    """Verify the graph structure by querying counts."""
    print("\n--- Graph Verification ---")
    labels_result = db.labels.find({})
    for label_info in labels_result.data:
        print(f"  {label_info.name}: {label_info.count} records")
    print()


def main():
    print("=== RushDB Graph Seeding ===\n")
    
    # Clear existing data for idempotent seeding
    clear_existing_data()
    
    # Create all nodes
    docs, concepts, decisions, tradeoffs = create_nodes()
    
    # Create relationships
    create_relationships(concepts, decisions, tradeoffs)
    
    # Verify the graph
    verify_graph()
    
    print("Seeding complete! Run main.py to execute the prompt chain.\n")


if __name__ == "__main__":
    main()
