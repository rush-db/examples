#!/usr/bin/env python3
"""
Seed script for contextual retrieval chains tutorial.
Creates a knowledge base of software engineering topics with rich relationships.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Relationship weights for scoring demonstration
RELATIONSHIP_WEIGHTS = {
    "CITES": 1.0,
    "AUTHORED_BY": 0.8,
    "RELATED_TO": 0.5,
    "REFERENCES": 0.3,
}

# Sample data
AUTHORS = [
    {"name": "Dr. Sarah Chen", "affiliation": "MIT CSAIL", "specialization": "distributed systems"},
    {"name": "Prof. James Miller", "affiliation": "Stanford NLP Group", "specialization": "machine learning"},
    {"name": "Elena Rodriguez", "affiliation": "Google Research", "specialization": "software engineering"},
    {"name": "Dr. Michael Park", "affiliation": "Berkeley RISE Lab", "specialization": "security"},
    {"name": "Dr. Aisha Patel", "affiliation": "Microsoft Research", "specialization": "databases"},
]

TOPICS = [
    {"name": "Microservices", "description": "Architectural style structuring apps as service suites"},
    {"name": "Event Sourcing", "description": "Capturing state changes as sequence of events"},
    {"name": "CQRS Pattern", "description": "Separating read and write operations for scaling"},
    {"name": "Distributed Tracing", "description": "Tracking requests across service boundaries"},
    {"name": "Service Mesh", "description": "Infrastructure layer for service communication"},
    {"name": "API Gateway", "description": "Single entry point for microservice architectures"},
    {"name": "Circuit Breaker", "description": "Preventing cascading failures in distributed systems"},
    {"name": "Event-Driven Architecture", "description": "Systems reacting to events produced by others"},
    {"name": "Saga Pattern", "description": "Managing distributed transactions across services"},
    {"name": "Kubernetes", "description": "Container orchestration for modern applications"},
    {"name": "GraphQL", "description": "Query language for APIs and runtime for fulfilling queries"},
    {"name": "gRPC", "description": "High-performance RPC framework"},
    {"name": "Observability", "description": "Understanding system internal state from external outputs"},
    {"name": "Chaos Engineering", "description": "Testing system resilience through experiments"},
    {"name": "Zero Trust Security", "description": "Security model eliminating implicit trust"},
]

DOCUMENTS = [
    {
        "title": "Introduction to Microservices Architecture",
        "body": "Microservices architecture structures an application as a collection of loosely coupled services, each implementing a specific business capability. This approach enables independent deployment, scaling, and technology diversity. Key characteristics include decentralized data management, infrastructure automation, and design for failure. Teams can own entire lifecycle from development to production, fostering ownership and accelerating delivery.",
        "tags": ["microservices", "architecture", "distributed systems"],
        "topic": "Microservices",
    },
    {
        "title": "Event Sourcing: A Paradigm Shift in State Management",
        "body": "Event sourcing stores state changes as a sequence of events rather than current state. This provides complete audit trail, enables temporal queries, and supports easy integration with event-driven systems. Event store acts as source of truth, with commands generating events that are persisted and processed by projectors. Advantages include ability to rebuild state at any point, replay for debugging, and sophisticated analytics. Challenges include event schema evolution and eventual consistency.",
        "tags": ["event sourcing", "cqrs", "event-driven"],
        "topic": "Event Sourcing",
    },
    {
        "title": "CQRS in Practice: Separating Command and Query Concerns",
        "body": "Command Query Responsibility Segregation (CQRS) separates read and write operations into distinct models. Write model handles commands and validation, while read model provides optimized projections for queries. This separation enables independent scaling of read and write workloads, different data models per view, and eventual consistency for complex aggregations. Implementation typically involves event bus between command and query sides, with read model updated asynchronously.",
        "tags": ["cqrs", "architecture", "scalability"],
        "topic": "CQRS Pattern",
    },
    {
        "title": "Distributed Tracing with OpenTelemetry",
        "body": "Distributed tracing tracks requests across multiple services, providing visibility into latency and error sources. OpenTelemetry provides vendor-neutral instrumentation APIs and SDKs. Traces consist of spans representing individual operations, with context propagation enabling end-to-end correlation. Implementation involves adding instrumentation to services, configuring exporters to collection backend, and establishing sampling strategies. Popular backends include Jaeger, Zipkin, and commercial solutions.",
        "tags": ["observability", "distributed tracing", "microservices"],
        "topic": "Distributed Tracing",
    },
    {
        "title": "Service Mesh Fundamentals: Istio and Linkerd",
        "body": "Service mesh provides transparent infrastructure layer handling service communication. It handles traffic management, security, and observability without requiring application changes. Data plane consists of sidecar proxies intercepting all network traffic. Control plane manages configuration and policy distribution. Key features include load balancing, circuit breaking, retries, mTLS between services, and traffic splitting for deployments. Istio provides rich feature set while Linkerd focuses on simplicity and performance.",
        "tags": ["service mesh", "kubernetes", "networking"],
        "topic": "Service Mesh",
    },
    {
        "title": "API Gateway Patterns for Microservices",
        "body": "API gateway provides single entry point for microservice architecture, handling cross-cutting concerns like authentication, rate limiting, and request routing. Patterns include Backend for Frontend (BFF) creating tailored APIs per client type, aggregation gateway combining multiple backend calls, and gateway routing directing requests to appropriate services. Implementation considerations include stateless design for horizontal scaling, circuit breaker integration, and caching strategies to reduce backend load.",
        "tags": ["api gateway", "microservices", "architecture"],
        "topic": "API Gateway",
    },
    {
        "title": "Implementing Circuit Breakers for Resilience",
        "body": "Circuit breaker pattern prevents cascading failures by detecting downstream failures and stopping requests to failing services. States include closed (normal operation), open (fast-fail), and half-open (testing recovery). Implementation involves monitoring failure rates, threshold configuration, and timeout strategies. Libraries like Hystrix, Resilience4j, and Polly provide ready implementations. Best practices include fallback strategies, bulkhead isolation, and proper health endpoint configuration.",
        "tags": ["circuit breaker", "resilience", "patterns"],
        "topic": "Circuit Breaker",
    },
    {
        "title": "Event-Driven Architecture with Apache Kafka",
        "body": "Event-driven architecture enables systems to react to events produced by others, achieving loose coupling and scalability. Apache Kafka provides distributed event streaming platform with durable storage, exactly-once semantics, and replay capability. Event schema registry manages evolution, while consumer groups enable parallel processing. Patterns include event sourcing, choreography versus orchestration saga, and CQRS. Kafka Streams and ksqlDB enable stream processing within Kafka ecosystem.",
        "tags": ["kafka", "event-driven", "streaming"],
        "topic": "Event-Driven Architecture",
    },
    {
        "title": "Saga Pattern for Distributed Transactions",
        "body": "Saga pattern manages distributed transactions across services without distributed locks. Choreography saga uses events between services, while orchestration saga uses centralized coordinator. Each saga step has compensating transaction for rollback. Implementation requires careful error handling, idempotency, and state management. Frameworks like Azure Saga Orchestration and AWS Step Functions provide infrastructure support. Design considerations include saga length impact on complexity and isolation level requirements.",
        "tags": ["saga", "distributed transactions", "patterns"],
        "topic": "Saga Pattern",
    },
    {
        "title": "Kubernetes Deep Dive: From Pods to Production",
        "body": "Kubernetes orchestrates containerized applications across clusters. Core concepts include Pods (smallest deployable units), Services (stable network endpoints), and Deployments (declarative updates). ReplicaSets ensure desired pod count, while Ingress provides external access. ConfigMaps and Secrets manage configuration and sensitive data. Advanced topics include custom controllers, operators, and cluster federation. Production considerations include resource limits, pod disruption budgets, and multi-zone distribution.",
        "tags": ["kubernetes", "containers", "orchestration"],
        "topic": "Kubernetes",
    },
    {
        "title": "GraphQL for Modern API Development",
        "body": "GraphQL provides flexible query language for APIs and runtime for fulfilling those queries with existing data. Clients specify exact data requirements, reducing over-fetching. Schema defines types and relationships, with resolvers implementing field logic. Subscriptions enable real-time updates. Implementation patterns include schema stitching for federated architectures, dataloader for N+1 problem, and persisted queries for production optimization. Security considerations include depth limiting, cost analysis, and field visibility.",
        "tags": ["graphql", "api", "backend"],
        "topic": "GraphQL",
    },
    {
        "title": "gRPC: High-Performance RPC Framework",
        "body": "gRPC is high-performance RPC framework using HTTP/2 for transport and Protocol Buffers for serialization. Advantages include binary protocol efficiency, bidirectional streaming, and strong typing through schema. Use cases include internal service communication, polyglot microservices, and mobile clients. Implementation involves defining .proto files, generating client/server code, and configuring channel options. Interceptors enable cross-cutting concerns like authentication and monitoring.",
        "tags": ["grpc", "protocol buffers", "microservices"],
        "topic": "gRPC",
    },
    {
        "title": "Building Observable Microservices",
        "body": "Observability enables understanding internal system state from external outputs. Three pillars include metrics (numerical measurements), logs (timestamped event records), and traces (request flow across components). Implementation requires instrumentation in application code, collection infrastructure, and visualization dashboards. OpenTelemetry provides vendor-neutral instrumentation, while Prometheus, Grafana, Jaeger, and ELK provide storage and visualization. SLO-based alerting ensures system reliability.",
        "tags": ["observability", "monitoring", "sre"],
        "topic": "Observability",
    },
    {
        "title": "Chaos Engineering: Testing Production Resilience",
        "body": "Chaos engineering proactively tests system resilience by injecting failures in controlled experiments. Principles include formulating hypothesis, injecting real-world failure, and measuring blast radius. Tools like Chaos Monkey, Gremlin, and Litmus enable chaos experiments. Common experiments include killing pods, introducing network latency, consuming resources, and simulating cloud service failures. Business impact measurement validates experiments value. Start with game days and mature toward continuous validation.",
        "tags": ["chaos engineering", "resilience", "testing"],
        "topic": "Chaos Engineering",
    },
    {
        "title": "Zero Trust Security for Cloud Native Applications",
        "body": "Zero trust security model eliminates implicit trust, requiring verification for every access request regardless of network location. Core principles include never trust always verify, least privilege access, and assume breach. Implementation involves strong identity verification, micro-segmentation, lateral movement prevention, and continuous monitoring. In cloud native context, this means service mesh mTLS, workload identity, secrets management, and network policies. Tools like SPIFFE/SPIRE provide workload identity foundation.",
        "tags": ["zero trust", "security", "cloud native"],
        "topic": "Zero Trust Security",
    },
    {
        "title": "Comparing Event Sourcing and CQRS: When to Use Each",
        "body": "Event sourcing and CQRS often appear together but serve different purposes. Event sourcing stores state changes as events, providing complete history and temporal queries. CQRS separates read and write models for independent optimization. Event sourcing works well when audit trail, replay capability, or temporal queries matter. CQRS shines when read/write workloads differ significantly or when multiple read views are needed. Combined approach maximizes benefits but adds complexity requiring careful consideration.",
        "tags": ["event sourcing", "cqrs", "architecture"],
        "topic": "Event Sourcing",
    },
    {
        "title": "Microservices Communication Patterns",
        "body": "Microservices communicate through synchronous (REST, gRPC) or asynchronous (messaging, events) patterns. Synchronous offers simplicity and immediate responses but creates temporal coupling. Asynchronous provides decoupling and resilience but adds complexity. Hybrid approaches combine both, using async for data flow and sync for commands. Service discovery enables dynamic addressing, while circuit breakers handle failures gracefully. API design principles ensure contracts remain stable across services.",
        "tags": ["microservices", "api", "communication"],
        "topic": "Microservices",
    },
    {
        "title": "Service Mesh vs API Gateway: Choosing the Right Tool",
        "body": "Service mesh and API gateway solve different problems at different layers. API gateway handles north-south traffic (external to cluster), providing rate limiting, authentication, and protocol translation. Service mesh manages east-west traffic (internal), handling service-to-service communication with mTLS, retries, and observability. Some solutions like Istio provide both capabilities. Decision factors include traffic direction, security perimeter, and operational complexity tolerance.",
        "tags": ["service mesh", "api gateway", "architecture"],
        "topic": "Service Mesh",
    },
    {
        "title": "Building Resilient APIs with Circuit Breakers",
        "body": "Resilient APIs protect backend services from cascading failures through circuit breakers. Implementation monitors error rates and trips circuit when threshold exceeded. Failed requests receive fallback response or fast failure. Recovery testing periodically allows requests to test service health. Configuration includes error threshold percentage, timeout duration, and volume threshold. Integration with API gateways adds protection at entry point. Monitoring circuit state helps identify problematic dependencies.",
        "tags": ["circuit breaker", "api", "resilience"],
        "topic": "Circuit Breaker",
    },
    {
        "title": "Saga Orchestration vs Choreography: Trade-offs",
        "body": "Saga orchestration uses centralized coordinator directing participants, while choreography uses participants reacting to events they receive. Orchestration offers visibility and simpler error handling but creates central point of failure. Choreography provides decentralization and simplicity but can lead to cyclic dependencies and hidden flows. Hybrid approaches use choreography for simple flows and orchestration for complex transactions. Decision factors include transaction complexity, team structure, and monitoring requirements.",
        "tags": ["saga", "orchestration", "patterns"],
        "topic": "Saga Pattern",
    },
]

# Relationship definitions between documents
DOCUMENT_RELATIONSHIPS = [
    {
        "source_idx": 0,  # Introduction to Microservices
        "target_idx": 7,  # Event-Driven Architecture
        "type": "RELATED_TO",
    },
    {
        "source_idx": 0,  # Introduction to Microservices
        "target_idx": 4,  # Service Mesh
        "type": "REFERENCES",
    },
    {
        "source_idx": 0,  # Introduction to Microservices
        "target_idx": 5,  # API Gateway
        "type": "RELATED_TO",
    },
    {
        "source_idx": 1,  # Event Sourcing
        "target_idx": 2,  # CQRS
        "type": "CITES",
    },
    {
        "source_idx": 2,  # CQRS in Practice
        "target_idx": 7,  # Event-Driven Architecture
        "type": "RELATED_TO",
    },
    {
        "source_idx": 7,  # Event-Driven Architecture
        "target_idx": 1,  # Event Sourcing
        "type": "AUTHORED_BY",
    },
    {
        "source_idx": 3,  # Distributed Tracing
        "target_idx": 12,  # Building Observable Microservices
        "type": "CITES",
    },
    {
        "source_idx": 4,  # Service Mesh
        "target_idx": 9,  # Kubernetes
        "type": "REFERENCES",
    },
    {
        "source_idx": 5,  # API Gateway
        "target_idx": 10,  # GraphQL
        "type": "RELATED_TO",
    },
    {
        "source_idx": 6,  # Circuit Breakers
        "target_idx": 12,  # Building Observable Microservices
        "type": "RELATED_TO",
    },
    {
        "source_idx": 8,  # Saga Pattern
        "target_idx": 2,  # CQRS
        "type": "REFERENCES",
    },
    {
        "source_idx": 9,  # Kubernetes
        "target_idx": 4,  # Service Mesh
        "type": "RELATED_TO",
    },
    {
        "source_idx": 9,  # Kubernetes
        "target_idx": 11,  # gRPC
        "type": "CITES",
    },
    {
        "source_idx": 10,  # GraphQL
        "target_idx": 11,  # gRPC
        "type": "REFERENCES",
    },
    {
        "source_idx": 12,  # Observability
        "target_idx": 3,  # Distributed Tracing
        "type": "AUTHORED_BY",
    },
    {
        "source_idx": 13,  # Chaos Engineering
        "target_idx": 12,  # Building Observable Microservices
        "type": "RELATED_TO",
    },
    {
        "source_idx": 14,  # Zero Trust Security
        "target_idx": 4,  # Service Mesh
        "type": "CITES",
    },
    {
        "source_idx": 15,  # Comparing Event Sourcing and CQRS
        "target_idx": 1,   # Event Sourcing
        "type": "CITES",
    },
    {
        "source_idx": 15,  # Comparing Event Sourcing and CQRS
        "target_idx": 2,   # CQRS
        "type": "CITES",
    },
    {
        "source_idx": 16,  # Microservices Communication
        "target_idx": 11,  # gRPC
        "type": "RELATED_TO",
    },
    {
        "source_idx": 17,  # Service Mesh vs API Gateway
        "target_idx": 4,   # Service Mesh
        "type": "CITES",
    },
    {
        "source_idx": 17,  # Service Mesh vs API Gateway
        "target_idx": 5,   # API Gateway
        "type": "CITES",
    },
    {
        "source_idx": 18,  # Building Resilient APIs
        "target_idx": 6,   # Circuit Breakers
        "type": "CITES",
    },
    {
        "source_idx": 19,  # Saga Orchestration vs Choreography
        "target_idx": 8,    # Saga Pattern
        "type": "CITES",
    },
]


def seed_data():
    """Main function to seed the database with test data."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Please copy .env.example to .env and add your API key")
        return False

    print("Connecting to RushDB...")
    db = RushDB(api_key)
    print("Connected successfully\n")

    # Check if data already exists
    existing_authors = db.records.find({"labels": ["AUTHOR"], "limit": 1})
    if existing_authors.data:
        print("Data already exists. Skipping seed.")
        print(f"Found {len(db.records.find({'labels': ['AUTHOR'], 'limit': 1000}).data)} authors")
        return True

    print("Seeding database with knowledge graph...")
    print("-" * 50)

    # Create authors
    print("Creating authors...")
    author_records = []
    for i, author in enumerate(AUTHORS):
        record = db.records.create(
            label="AUTHOR",
            data=author
        )
        author_records.append(record)
        print(f"  [{i+1}/{len(AUTHORS)}] Created author: {author['name']}")

    print()

    # Create topics
    print("Creating topics...")
    topic_records = {}
    for i, topic in enumerate(TOPICS):
        record = db.records.create(
            label="TOPIC",
            data=topic
        )
        topic_records[topic['name']] = record
        print(f"  [{i+1}/{len(TOPICS)}] Created topic: {topic['name']}")

    print()

    # Create documents with relationships to topics
    print("Creating documents...")
    doc_records = []
    for i, doc in enumerate(DOCUMENTS):
        # Assign random author
        author_record = random.choice(author_records)
        
        record = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc["title"],
                "body": doc["body"],
                "tags": doc["tags"],
            }
        )
        doc_records.append(record)

        # Attach to topic
        topic_record = topic_records.get(doc["topic"])
        if topic_record:
            db.records.attach(
                source=record,
                target=topic_record,
                options={"type": "DISCUSSES"}
            )

        # Attach to author
        db.records.attach(
            source=record,
            target=author_record,
            options={"type": "AUTHORED_BY"}
        )

        print(f"  [{i+1}/{len(DOCUMENTS)}] Created document: {doc['title'][:50]}...")

    print()

    # Create document-to-document relationships
    print("Creating document relationships...")
    for i, rel in enumerate(DOCUMENT_RELATIONSHIPS):
        source = doc_records[rel["source_idx"]]
        target = doc_records[rel["target_idx"]]
        db.records.attach(
            source=source,
            target=target,
            options={"type": rel["type"]}
        )
        print(f"  [{i+1}/{len(DOCUMENT_RELATIONSHIPS)}] {rel['type']}: {DOCUMENTS[rel['source_idx']]['title'][:40]}... -> {DOCUMENTS[rel['target_idx']]['title'][:40]}...")

    print()
    print("=" * 50)
    print("Seeding complete!")
    print(f"  - {len(AUTHORS)} authors")
    print(f"  - {len(TOPICS)} topics")
    print(f"  - {len(DOCUMENTS)} documents")
    print(f"  - {len(DOCUMENT_RELATIONSHIPS)} document relationships")

    # Create vector index for document body
    print("\nCreating vector index for document bodies...")
    try:
        index = db.ai.indexes.create({
            "label": "DOCUMENT",
            "propertyName": "body",
            "dimensions": 768,
            "sourceType": "external"
        })
        print(f"Index created: {index.id}")
    except Exception as e:
        print(f"Index creation may have failed (may already exist): {e}")

    return True


if __name__ == "__main__":
    seed_data()
