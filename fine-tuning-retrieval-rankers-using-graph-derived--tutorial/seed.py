"""
Seed script for Fine-tuning Retrieval Rankers tutorial.

Creates a realistic knowledge base with:
- Technology articles (DOCUMENT records)
- User profiles (USER records)
- Query interactions (CLICKED, VIEWED, RATED relationships)

Run this once before executing main.py.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

from rushdb import RushDB

# Load environment variables
load_dotenv()
API_KEY = os.getenv("RUSHDB_API_KEY")
URL = os.getenv("RUSHDB_URL")

if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    exit(1)

db = RushDB(API_KEY, url=URL) if URL else RushDB(API_KEY)

# Sample documents covering technology topics
DOCUMENTS = [
    {"title": "Introduction to Graph Neural Networks", "category": "ml", 
     "content": "Graph Neural Networks extend deep learning to graph-structured data. "
                "They capture relational information through message passing between nodes."},
    {"title": "Transformer Architecture Deep Dive", "category": "nlp",
     "content": "Transformers use self-attention mechanisms to process sequential data. "
                "Key components include multi-head attention and positional encoding."},
    {"title": "Vector Databases for Semantic Search", "category": "databases",
     "content": "Vector databases store high-dimensional embeddings for similarity search. "
                "Popular options include Pinecone, Weaviate, and Qdrant."},
    {"title": "Fine-tuning Language Models", "category": "ml",
     "content": "Fine-tuning adapts pre-trained models to specific tasks. "
                "Techniques include LoRA, RLHF, and prompt tuning."},
    {"title": "RAG Architecture Patterns", "category": "ai",
     "content": "Retrieval-Augmented Generation combines vector search with LLM generation. "
                "Key components: chunking, embedding, retrieval, and synthesis."},
    {"title": "Neo4j Graph Database Basics", "category": "databases",
     "content": "Neo4j is a native graph database using the Cypher query language. "
                "It excels at traversing relationships and analyzing graph patterns."},
    {"title": "Python Async Programming", "category": "python",
     "content": "Async programming in Python uses asyncio for concurrent I/O operations. "
                "Key concepts: coroutines, event loops, and async/await syntax."},
    {"title": "React Server Components", "category": "frontend",
     "content": "React Server Components render on the server for improved performance. "
                "They reduce client-side JavaScript and enable direct database access."},
    {"title": "Kubernetes Deployment Patterns", "category": "devops",
     "content": "Kubernetes orchestrates containerized applications at scale. "
                "Key concepts: pods, services, deployments, and ingress controllers."},
    {"title": "Machine Learning Model Evaluation", "category": "ml",
     "content": "Evaluating ML models requires appropriate metrics and validation strategies. "
                "Common approaches: cross-validation, holdout sets, and A/B testing."},
    {"title": "REST API Design Best Practices", "category": "backend",
     "content": "Designing REST APIs involves resource modeling, versioning, and pagination. "
                "Consider HATEOAS for discoverability and GraphQL for flexible queries."},
    {"title": "PostgreSQL Performance Tuning", "category": "databases",
     "content": "Optimizing PostgreSQL involves indexing, query planning, and configuration. "
                "Key areas: connection pooling, caching, and materialized views."},
    {"title": "Docker Container Security", "category": "devops",
     "content": "Securing containers involves minimal base images, scanning, and runtime policies. "
                "Best practices: non-root users, read-only filesystems, and secrets management."},
    {"title": "TypeScript Type System Deep Dive", "category": "frontend",
     "content": "TypeScript's type system enables static analysis and IDE support. "
                "Advanced features: generics, conditional types, and mapped types."},
    {"title": "Event-Driven Architecture", "category": "backend",
     "content": "Event-driven systems use message brokers for decoupled communication. "
                "Patterns include CQRS, saga, and event sourcing."},
    {"title": "Redis Caching Strategies", "category": "databases",
     "content": "Redis provides in-memory data structures for caching and sessions. "
                "Patterns: cache-aside, write-through, and lazy expiration."},
    {"title": "GitOps with ArgoCD", "category": "devops",
     "content": "GitOps automates deployments through Git as the source of truth. "
                "ArgoCD implements GitOps with declarative application definitions."},
    {"title": "WebAssembly for High Performance", "category": "frontend",
     "content": "WebAssembly runs near-native code in browsers for performance-critical tasks. "
                "Use cases: video encoding, gaming, and scientific computing."},
    {"title": "Feature Flags and A/B Testing", "category": "devops",
     "content": "Feature flags enable controlled rollouts and experimentation. "
                "Tools: LaunchDarkly, Flagsmith, and custom solutions."},
    {"title": "Neural Information Retrieval", "category": "ml",
     "content": "Neural IR uses deep learning for relevance ranking. "
                "Models like BERT and ColBERT encode queries and documents for matching."},
    {"title": "GraphQL Schema Design", "category": "backend",
     "content": "GraphQL provides flexible data fetching with a type system. "
                "Schema design involves types, queries, mutations, and subscriptions."},
    {"title": "Monitoring with Prometheus and Grafana", "category": "devops",
     "content": "Prometheus collects metrics; Grafana visualizes them. "
                "Key concepts: exporters, alerting rules, and dashboard templates."},
    {"title": "Semantic Search Implementation", "category": "ai",
     "content": "Semantic search matches meaning rather than keywords. "
                "Implementation uses embeddings, vector indexes, and approximate nearest neighbors."},
    {"title": "Microservices Communication Patterns", "category": "backend",
     "content": "Microservices communicate via synchronous or asynchronous methods. "
                "Options: REST, gRPC, message queues, and service meshes."},
    {"title": "Python Memory Management", "category": "python",
     "content": "Python manages memory through reference counting and garbage collection. "
                "Understanding memory helps avoid leaks and optimize performance."},
    {"title": "CSS Grid Layout System", "category": "frontend",
     "content": "CSS Grid provides two-dimensional layout capabilities. "
                "Key features: grid-template areas, alignment, and responsive tracks."},
    {"title": "Kafka Stream Processing", "category": "databases",
     "content": "Apache Kafka handles real-time event streaming at scale. "
                "Streams can be processed with Kafka Streams or ksqlDB."},
    {"title": "CI/CD Pipeline Design", "category": "devops",
     "content": "CI/CD automates build, test, and deployment workflows. "
                "Best practices: trunk-based development, parallel testing, and canary releases."},
    {"title": "Attention Mechanisms Explained", "category": "nlp",
     "content": "Attention mechanisms allow models to focus on relevant input parts. "
                "Self-attention computes relationships within a sequence."},
    {"title": "Service Mesh with Istio", "category": "devops",
     "content": "Istio provides traffic management, security, and observability. "
                "Features include mTLS, traffic splitting, and circuit breakers."},
    {"title": "SQL Query Optimization", "category": "databases",
     "content": "Optimizing SQL involves indexes, join strategies, and query rewriting. "
                "Tools like EXPLAIN ANALYZE reveal execution plans."},
    {"title": "React Performance Optimization", "category": "frontend",
     "content": "Optimizing React involves memoization, code splitting, and virtualization. "
                "Tools: React DevTools Profiler, Lighthouse, and Web Vitals."},
    {"title": "Distributed Tracing with Jaeger", "category": "devops",
     "content": "Distributed tracing tracks requests across service boundaries. "
                "Jaeger provides visualization and latency analysis."},
    {"title": "Embeddings for Recommendation", "category": "ml",
     "content": "Embeddings represent items in dense vector space for recommendations. "
                "Techniques: collaborative filtering, content-based, and hybrid approaches."},
    {"title": "Python Decorators Tutorial", "category": "python",
     "content": "Decorators modify function behavior without changing their code. "
                "Common uses: logging, timing, caching, and authentication."},
    {"title": "WebSocket Real-time Communication", "category": "frontend",
     "content": "WebSockets enable bidirectional real-time communication. "
                "Use cases: chat, live updates, and collaborative editing."},
    {"title": "Database Normalization Principles", "category": "databases",
     "content": "Normalization reduces redundancy and improves data integrity. "
                "Forms: 1NF, 2NF, 3NF, BCNF for increasing normalization."},
    {"title": "Terraform Infrastructure as Code", "category": "devops",
     "content": "Terraform manages infrastructure declaratively across providers. "
                "Key concepts: state, providers, modules, and workspaces."},
    {"title": "Python Testing with pytest", "category": "python",
     "content": "pytest provides a mature testing framework for Python. "
                "Features: fixtures, parametrization, markers, and plugins."},
    {"title": "Vue 3 Composition API", "category": "frontend",
     "content": "Vue 3's Composition API offers flexible component logic reuse. "
                "Key features: ref, reactive, computed, and composables."},
    {"title": "Data Pipeline Architecture", "category": "databases",
     "content": "Data pipelines orchestrate movement and transformation of data. "
                "Tools: Airflow, Prefect, Dagster, and dbt."},
    {"title": "Zero Trust Security Model", "category": "devops",
     "content": "Zero trust assumes no implicit trust in network or users. "
                "Principles: verify explicitly, least privilege, assume breach."},
    {"title": "Python Type Hints Guide", "category": "python",
     "content": "Type hints document expected types and enable static analysis. "
                "Tools: mypy, pyright, and type checkers."},
    {"title": "Next.js App Router Features", "category": "frontend",
     "content": "Next.js 13+ App Router provides file-based routing and server components. "
                "Features: layouts, loading states, error boundaries, and streaming."},
    {"title": "Graph Database Query Patterns", "category": "databases",
     "content": "Graph queries traverse relationships efficiently. "
                "Use cases: recommendations, fraud detection, and knowledge graphs."},
    {"title": "Container Orchestration Best Practices", "category": "devops",
     "content": "Container orchestration requires health checks, resource limits, and scheduling. "
                "Patterns: sidecars, init containers, and affinity rules."},
    {"title": "AsyncIO Performance Patterns", "category": "python",
     "content": "AsyncIO enables high-concurrency I/O with minimal threads. "
                "Patterns: connection pooling, semaphores, and task groups."},
    {"title": "Web Performance Metrics", "category": "frontend",
     "content": "Core Web Vitals measure user experience: LCP, FID, CLS. "
                "Optimization targets: fast load, responsive interaction, stable layout."},
    {"title": "Vector Indexing Strategies", "category": "ai",
     "content": "Vector indexes accelerate similarity search at scale. "
                "Methods: HNSW, IVF, PQ compression, and hybrid search."},
    {"title": "Serverless Architecture Patterns", "category": "backend",
     "content": "Serverless abstracts infrastructure for event-driven workloads. "
                "Providers: AWS Lambda, Azure Functions, Google Cloud Functions."},
    {"title": "Python Concurrency Patterns", "category": "python",
     "content": "Python offers multiple concurrency models: threading, async, multiprocessing. "
                "Choosing the right model depends on workload characteristics."},
]

# Sample users
USERS = [
    {"user_id": "u001", "name": "Alice Chen", "expertise": "machine-learning"},
    {"user_id": "u002", "name": "Bob Martinez", "expertise": "backend"},
    {"user_id": "u003", "name": "Carol Johnson", "expertise": "frontend"},
    {"user_id": "u004", "name": "David Kim", "expertise": "devops"},
    {"user_id": "u005", "name": "Eva Williams", "expertise": "databases"},
    {"user_id": "u006", "name": "Frank Lee", "expertise": "python"},
    {"user_id": "u007", "name": "Grace Taylor", "expertise": "nlp"},
    {"user_id": "u008", "name": "Henry Brown", "expertise": "ai"},
    {"user_id": "u009", "name": "Iris Anderson", "expertise": "security"},
    {"user_id": "u010", "name": "Jack Thomas", "expertise": "architecture"},
]

# Simulated search queries with relevance to documents
QUERIES = [
    "graph neural networks machine learning",
    "transformer attention mechanism",
    "vector database semantic search",
    "fine-tune language model",
    "retrieval augmented generation",
    "python async programming",
    "react server components",
    "kubernetes deployment",
    "postgresql performance tuning",
    "docker security",
    "typescript types",
    "event driven architecture",
    "redis caching",
    "gitops argocd",
    "webassembly performance",
]


def clear_existing_data():
    """Remove existing records to ensure clean seed."""
    print("Clearing existing data...")
    labels_to_clear = ["SIGNAL", "TRAINING_PAIR", "QUERY_INTERACTION", "USER", "DOCUMENT"]
    for label in labels_to_clear:
        try:
            db.records.delete({"labels": [label], "where": {}})
        except Exception:
            pass
    print("  ✓ Cleared existing records")


def seed_documents():
    """Create document records with embeddings."""
    print("\nCreating documents...")
    documents = []
    
    for i, doc_data in enumerate(DOCUMENTS):
        doc = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc_data["title"],
                "category": doc_data["category"],
                "content": doc_data["content"],
                "slug": doc_data["title"].lower().replace(" ", "-").replace(",", ""),
            }
        )
        documents.append(doc)
        
        if (i + 1) % 10 == 0:
            print(f"  ✓ Created {i + 1} documents")
    
    print(f"  ✓ Created {len(documents)} documents total")
    return documents


def seed_users():
    """Create user records."""
    print("\nCreating users...")
    users = []
    
    for user_data in USERS:
        user = db.records.create(label="USER", data=user_data)
        users.append(user)
    
    print(f"  ✓ Created {len(users)} users")
    return users


def create_interactions(documents, users):
    """Create query-document interactions to simulate user engagement."""
    print("\nCreating query-document interactions...")
    
    # Query patterns with associated document categories
    query_patterns = [
        ("graph neural networks", ["ml", "databases"]),
        ("transformer language", ["nlp", "ml"]),
        ("vector search", ["databases", "ai"]),
        ("python async", ["python", "backend"]),
        ("kubernetes deployment", ["devops"]),
        ("react frontend", ["frontend"]),
        ("database performance", ["databases"]),
        ("api design", ["backend"]),
    ]
    
    interaction_count = 0
    base_time = datetime.now() - timedelta(days=30)
    
    # Each user interacts with documents based on their query
    for user in users:
        # Each user makes 5-15 queries
        num_queries = random.randint(5, 15)
        
        for q_idx in range(num_queries):
            # Select a random query pattern
            query, relevant_cats = random.choice(query_patterns)
            
            # Find documents in relevant categories
            relevant_docs = [d for d in documents if d["category"] in relevant_cats]
            
            if not relevant_docs:
                relevant_docs = documents[:5]
            
            # Create interactions with this query
            query_time = base_time + timedelta(
                hours=random.randint(0, 720),
                minutes=random.randint(0, 59)
            )
            
            # Click on 1-3 relevant documents (positive signals)
            num_clicks = random.randint(1, min(3, len(relevant_docs)))
            clicked_docs = random.sample(relevant_docs, num_clicks)
            
            for doc in clicked_docs:
                rating = random.randint(3, 5)  # Positive ratings
                
                db.records.attach(
                    source=user,
                    target=doc,
                    options={
                        "type": "CLICKED",
                        "properties": {
                            "query": query,
                            "rating": rating,
                            "timestamp": int(query_time.timestamp()),
                        }
                    }
                )
                interaction_count += 1
            
            # View but not click on 1-2 irrelevant documents (negative signals)
            irrelevant_docs = [d for d in documents if d not in clicked_docs][:2]
            for doc in irrelevant_docs:
                if random.random() < 0.3:  # 30% chance of a view
                    db.records.attach(
                        source=user,
                        target=doc,
                        options={
                            "type": "VIEWED",
                            "properties": {
                                "query": query,
                                "timestamp": int(query_time.timestamp()),
                            }
                        }
                    )
                    interaction_count += 1
    
    print(f"  ✓ Created {interaction_count} query-document interactions")
    return interaction_count


def create_document_similarity_graph(documents):
    """Create SIMILAR_TO relationships between documents."""
    print("\nCreating document similarity graph...")
    
    # Create similarity relationships based on category
    similarity_count = 0
    categories = set(d["category"] for d in DOCUMENTS)
    
    for cat in categories:
        cat_docs = [d for d in documents if d["category"] == cat]
        
        # Connect documents in same category
        for i, doc1 in enumerate(cat_docs):
            for doc2 in cat_docs[i+1:]:
                # 30% chance of being similar
                if random.random() < 0.3:
                    db.records.attach(
                        source=doc1,
                        target=doc2,
                        options={
                            "type": "SIMILAR_TO",
                            "properties": {
                                "strength": round(random.uniform(0.5, 1.0), 2),
                            }
                        }
                    )
                    similarity_count += 1
    
    print(f"  ✓ Created {similarity_count} document similarity relationships")
    return similarity_count


def main():
    print("=" * 60)
    print("Fine-tuning Retrieval Rankers - Data Seeding")
    print("=" * 60)
    
    try:
        # Clear existing data
        clear_existing_data()
        
        # Create records
        documents = seed_documents()
        users = seed_users()
        
        # Create interactions
        create_interactions(documents, users)
        
        # Create similarity graph
        create_document_similarity_graph(documents)
        
        print("\n" + "=" * 60)
        print("✓ Seeding complete!")
        print("=" * 60)
        print("\nYou can now run `python main.py` to execute the tutorial.")
        
    except Exception as e:
        print(f"\nError during seeding: {e}")
        raise


if __name__ == "__main__":
    main()
