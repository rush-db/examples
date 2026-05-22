#!/usr/bin/env python3
"""
Seed script: Creates a document corpus with chunks, embeddings, and graph edges.

This script builds a knowledge graph of tech articles with:
- 30 articles across 5 topics
- ~90 chunks (3-5 per article)
- Graph edges: citations, shared authors, shared topics
- Vector embeddings for semantic search

Run this once before main.py to populate the database.
"""

import os
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
db = RushDB(os.environ["RUSHDB_API_TOKEN"])

# Initialize embedding model (all-MiniLM-L6-v2 - fast, good quality)
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
EMBEDDING_DIM = 384


@dataclass
class Article:
    """Represents a source article."""
    title: str
    topic: str
    author: str
    content: str


@dataclass
class Chunk:
    """Represents a chunk extracted from an article."""
    article_title: str
    text: str
    position: int


# ============================================================================
# DOCUMENT CORPUS DEFINITION
# ============================================================================

TOPICS = ["AI/ML", "Web Development", "Security", "Cloud Computing", "Data Engineering"]

AUTHORS = ["Alice Chen", "Bob Martinez", "Carol Williams", "David Kim", "Eva Thompson"]

ARTICLES = [
    # AI/ML
    Article(
        title="Understanding Transformer Architecture",
        topic="AI/ML",
        author="Alice Chen",
        content="""Transformers revolutionized natural language processing by replacing recurrent networks with self-attention mechanisms. The core innovation is the attention mechanism that allows the model to weigh the importance of different parts of the input when processing each element.

The self-attention mechanism computes attention scores between all pairs of positions in the sequence. This parallel computation enables capturing long-range dependencies efficiently. Key components include Query, Key, and Value projections, as well as multi-head attention that allows the model to attend to different representation subspaces.

The feed-forward network in each transformer block processes each position independently, providing non-linear transformations. Layer normalization and residual connections stabilize training. Positional encodings inject sequence order information since self-attention is inherently order-invariant."""
    ),
    Article(
        title="Introduction to Large Language Models",
        topic="AI/ML",
        author="Alice Chen",
        content="""Large Language Models (LLMs) are transformer-based models trained on massive text corpora. GPT, BERT, and their variants represent the state of the art in natural language understanding and generation.

Pre-training involves predicting the next token (GPT) or masked tokens (BERT) on internet-scale data. This unsupervised learning creates rich representations of language, syntax, semantics, and even some world knowledge.

Fine-tuning adapts pre-trained models to specific tasks using supervised learning. Common techniques include instruction tuning and reinforcement learning from human feedback (RLHF). The emergent capabilities observed in larger models remain an active research area."""
    ),
    Article(
        title="Attention Mechanisms Explained",
        topic="AI/ML",
        author="Bob Martinez",
        content="""Attention mechanisms allow neural networks to focus on relevant parts of the input when producing output. The original attention mechanism was introduced for machine translation, where it helped models handle long sequences by dynamically aligning source and target tokens.

Self-attention extends this idea by relating different positions within the same sequence. The attention function can be described as mapping a query and key-value pairs to an output. The output is computed as a weighted sum of values, where weights are determined by the compatibility function between query and keys.

Multi-head attention runs several attention mechanisms in parallel, allowing the model to jointly attend to information from different representation subspaces at different positions. This diversity is crucial for capturing various types of relationships in the data."""
    ),
    Article(
        title="Training Deep Neural Networks",
        topic="AI/ML",
        author="Carol Williams",
        content="""Training deep neural networks involves optimizing millions or billions of parameters to minimize a loss function. Gradient descent and its variants (SGD, Adam, AdamW) form the foundation of modern training algorithms.

Backpropagation efficiently computes gradients through the computational graph using the chain rule. Modern frameworks like PyTorch and TensorFlow automate this process, allowing researchers to focus on model architecture rather than gradient engineering.

Challenges in training include vanishing and exploding gradients, which gradient clipping and proper initialization address. Modern architectures with normalization layers mitigate these issues, enabling much deeper networks."""
    ),
    Article(
        title="Neural Network Architectures Survey",
        topic="AI/ML",
        author="David Kim",
        content="""Neural network architectures have evolved from simple perceptrons to complex transformer-based models. Each architectural innovation addressed specific limitations in existing approaches.

Convolutional Neural Networks (CNNs) excel at processing grid-like data such as images. They leverage local connectivity and parameter sharing to efficiently capture spatial hierarchies. Residual connections and skip connections enabled training of very deep networks.

Recurrent Neural Networks (RNNs) naturally handle sequential data by maintaining hidden state. LSTMs and GRUs addressed gradient vanishing problems, but transformers eventually surpassed them for most sequence modeling tasks due to parallelization benefits."""
    ),
    Article(
        title="Natural Language Processing Fundamentals",
        topic="AI/ML",
        author="Eva Thompson",
        content="""Natural Language Processing (NLP) enables computers to understand, interpret, and generate human language. Traditional approaches relied on statistical methods and hand-crafted features, but deep learning has revolutionized the field.

Word embeddings like Word2Vec and GloVe represent words as dense vectors capturing semantic relationships. These static embeddings were later replaced by contextual embeddings from language models that capture polysemy and context-dependence.

Common NLP tasks include text classification, named entity recognition, sentiment analysis, machine translation, and question answering. Modern approaches use transfer learning, where pre-trained models are fine-tuned for specific tasks with relatively little data."""
    ),

    # Web Development
    Article(
        title="Building RESTful APIs with Node.js",
        topic="Web Development",
        author="Bob Martinez",
        content="""REST APIs are the backbone of modern web services, enabling communication between client and server applications. Node.js with Express provides a lightweight framework for building scalable RESTful services.

REST principles include stateless communication, resource-based URLs, and standard HTTP methods (GET, POST, PUT, DELETE). Response formats typically use JSON for data exchange. Proper status codes communicate the result of requests.

Middleware in Express handles cross-cutting concerns like authentication, logging, and error handling. Route parameters and query strings allow flexible request handling. Validation ensures data integrity before processing."""
    ),
    Article(
        title="React Component Patterns",
        topic="Web Development",
        author="Carol Williams",
        content="""React component patterns help developers build maintainable and reusable UI code. Understanding these patterns is essential for scaling React applications effectively.

Container and presenter components separate business logic from presentation. Higher-order components (HOCs) wrap existing components with additional functionality. Custom hooks encapsulate stateful logic for reuse across components.

The compound component pattern creates expressive APIs for related components. Render props pass rendering logic as a function prop. Each pattern has trade-offs; choosing the right pattern depends on the specific use case."""
    ),
    Article(
        title="TypeScript Best Practices",
        topic="Web Development",
        author="David Kim",
        content="""TypeScript adds static typing to JavaScript, catching errors at compile time and improving developer experience. Adopting best practices ensures type safety and maintainable code.

Strict mode enables all type-checking options, catching more potential errors. Discriminated unions model complex states safely. Type guards narrow union types in conditional branches.

Generic types enable reusable, type-safe abstractions. Utility types like Partial, Pick, and Omit simplify type transformations. Mapped types create new types by transforming existing ones. The satisfies operator validates types without widening."""
    ),
    Article(
        title="Modern CSS Techniques",
        topic="Web Development",
        author="Eva Thompson",
        content="""Modern CSS provides powerful tools for building responsive, maintainable designs. Flexbox and Grid revolutionized layout systems, replacing float-based approaches.

CSS custom properties (variables) enable theming and consistent design systems. They can be modified dynamically with JavaScript for runtime theming. The cascade layers specification provides explicit control over style precedence.

Container queries adapt components to their context rather than the viewport. The :has() selector enables parent selection, unlocking new layout possibilities. View transitions simplify creating smooth page animations."""
    ),
    Article(
        title="Web Performance Optimization",
        topic="Web Development",
        author="Alice Chen",
        content="""Web performance directly impacts user experience and business metrics. Core Web Vitals provide standardized metrics for measuring user-perceived performance.

Critical rendering path optimization ensures above-the-fold content loads quickly. Lazy loading defers loading non-essential resources. Code splitting and tree shaking reduce bundle sizes.

Caching strategies, including service workers and CDN usage, dramatically improve repeat visit performance. Image optimization, including modern formats like WebP and AVIF, reduces transfer sizes. Resource hints like preload and prefetch inform the browser about priority loading."""
    ),
    Article(
        title="Frontend Architecture Patterns",
        topic="Web Development",
        author="Bob Martinez",
        content="""Frontend architecture patterns organize code for large-scale applications. Choosing the right architecture affects maintainability, performance, and team productivity.

Monorepo architectures like Nx and Turborepo share code and tooling across projects. Micro-frontends decompose the frontend into independently deployable units, enabling team autonomy.

State management patterns like Redux, Zustand, and Jotai handle application state. Each has different trade-offs between boilerplate, performance, and developer experience. Server state management with React Query or SWR handles data fetching with caching and synchronization."""
    ),

    # Security
    Article(
        title="Web Application Security Fundamentals",
        topic="Security",
        author="Carol Williams",
        content="""Web application security protects against attacks that exploit application vulnerabilities. The OWASP Top 10 identifies the most critical security risks for web applications.

Cross-Site Scripting (XSS) injects malicious scripts into web pages. Content Security Policy and input sanitization prevent XSS attacks. Cross-Site Request Forgery (CSRF) tricks users into performing unintended actions; anti-CSRF tokens mitigate this.

SQL injection exploits insecure database queries. Parameterized queries and ORM usage prevent injection. Security headers like HSTS, CSP, and X-Frame-Options provide defense-in-depth against common attacks."""
    ),
    Article(
        title="Authentication and Authorization Patterns",
        topic="Security",
        author="David Kim",
        content="""Authentication verifies user identity, while authorization determines what authenticated users can access. Both are critical for application security.

Password-based authentication should use slow hashing algorithms like bcrypt or Argon2. Multi-factor authentication adds security through something you know, have, or are. OAuth 2.0 and OpenID Connect provide delegated authentication standards.

Role-based access control (RBAC) assigns permissions to roles rather than individuals. Attribute-based access control (ABAC) provides finer-grained control based on user attributes, resource attributes, and environmental conditions. The principle of least privilege grants minimum necessary permissions."""
    ),
    Article(
        title="Cryptography for Developers",
        topic="Security",
        author="Eva Thompson",
        content="""Cryptography protects data confidentiality, integrity, and authenticity. Developers should understand when and how to apply cryptographic primitives.

Symmetric encryption like AES encrypts and decrypts with the same key. Asymmetric encryption like RSA uses key pairs for encryption and signing. Hybrid encryption combines both for efficiency.

Hash functions like SHA-256 ensure data integrity. HMAC adds keyed authentication to hashes. Digital signatures provide non-repudiation. Key management, including secure storage and rotation, is often the hardest part of implementing cryptography."""
    ),
    Article(
        title="Network Security Essentials",
        topic="Security",
        author="Alice Chen",
        content="""Network security protects data as it travels across networks. Defense-in-depth uses multiple layers of security controls.

Firewalls filter traffic based on rules. Next-generation firewalls add deep packet inspection and application awareness. Network segmentation isolates sensitive systems.

TLS encrypts data in transit. Certificate authorities validate server identities. VPN creates secure tunnels over untrusted networks. Zero-trust architecture assumes no implicit trust based on network location."""
    ),
    Article(
        title="Secure Software Development Lifecycle",
        topic="Security",
        author="Bob Martinez",
        content="""The Secure Software Development Lifecycle (SSDLC) integrates security throughout development. Shifting security left catches vulnerabilities early when they're cheaper to fix.

Threat modeling identifies potential attacks during design. Secure coding standards prevent common vulnerabilities. Static analysis tools like SAST catch issues in code before runtime.

Dynamic analysis (DAST) tests running applications. Penetration testing simulates real attacks. Bug bounty programs leverage the broader security community. Incident response plans prepare organizations for security breaches."""
    ),
    Article(
        title="Incident Response and Forensics",
        topic="Security",
        author="Carol Williams",
        content="""Incident response handles security breaches systematically. Preparation, identification, containment, eradication, recovery, and lessons learned form the incident response lifecycle.

Detection systems like SIEM and EDR identify potential incidents. Alert triage prioritizes investigation efforts. Forensic analysis preserves evidence while investigating.

Containment isolates affected systems to prevent spread. Eradication removes the threat entirely. Recovery restores systems to normal operation. Post-incident review improves future response."""
    ),

    # Cloud Computing
    Article(
        title="Cloud Architecture Patterns",
        topic="Cloud Computing",
        author="David Kim",
        content="""Cloud architecture patterns provide proven solutions to recurring design problems. Understanding patterns helps architects make informed decisions.

Microservices decompose applications into independently deployable services. Service mesh infrastructure handles cross-cutting concerns like service discovery and retries.

Event-driven architecture decouples producers and consumers through asynchronous messaging. Saga pattern coordinates distributed transactions. Circuit breaker pattern prevents cascade failures."""
    ),
    Article(
        title="Kubernetes Deep Dive",
        topic="Cloud Computing",
        author="Eva Thompson",
        content="""Kubernetes orchestrates containerized applications across clusters of machines. Understanding its architecture is essential for cloud-native development.

Pods are the smallest deployable units, containing one or more containers. Services provide stable network endpoints for dynamic pod IPs. Deployments manage rolling updates and rollbacks.

ConfigMaps and Secrets decouple configuration from images. Persistent volumes preserve data across pod restarts. Horizontal pod autoscaling adjusts capacity based on metrics. Custom resource definitions extend Kubernetes functionality."""
    ),
    Article(
        title="Serverless Computing Explained",
        topic="Cloud Computing",
        author="Alice Chen",
        content="""Serverless computing abstracts server management entirely, allowing developers to focus on code. AWS Lambda, Azure Functions, and Cloud Functions are popular serverless platforms.

Functions scale automatically in response to events. Cold starts introduce latency on first invocation. Execution time limits affect long-running operations.

Serverless architectures excel at event-driven workloads and variable traffic patterns. Stateless functions encourage scalable design. Vendors provide managed services for databases, queues, and other infrastructure."""
    ),
    Article(
        title="Container Orchestration Strategies",
        topic="Cloud Computing",
        author="Bob Martinez",
        content="""Container orchestration manages containerized applications across infrastructure. Kubernetes dominates but alternatives like Docker Swarm and Nomad exist.

Scheduling places containers on appropriate nodes based on resource requirements and constraints. Affinity rules co-locate or spread related workloads. Taints and tolerations control node selection.

Resource quotas prevent resource exhaustion. Network policies control pod-to-pod communication. RBAC controls access to cluster resources. Multi-cluster strategies improve availability and isolation."""
    ),
    Article(
        title="Cloud Cost Optimization",
        topic="Cloud Computing",
        author="Carol Williams",
        content="""Cloud costs can spiral without proper management. Cost optimization balances performance and expense.

Right-sizing instances matches resources to actual needs. Reserved instances and savings plans offer discounts for committed usage. Spot instances provide cheap compute for fault-tolerant workloads.

Storage tiering moves data to appropriate storage classes based on access patterns. Auto-scaling adjusts capacity with demand. Cost allocation tags track expenses by team or project. FinOps practices bring finance and engineering together for cost management."""
    ),
    Article(
        title="DevOps and CI/CD Pipelines",
        topic="Cloud Computing",
        author="David Kim",
        content="""CI/CD pipelines automate software delivery from code commit to production. Fast, reliable pipelines enable frequent deployments.

Continuous integration merges code changes frequently, running automated tests to detect issues early. Continuous delivery automates release to staging environments. Continuous deployment automates production releases.

Infrastructure as Code treats infrastructure definitions like application code. GitOps uses Git as the source of truth for infrastructure. Progressive delivery techniques like canary releases reduce risk of new deployments."""
    ),

    # Data Engineering
    Article(
        title="Data Pipeline Architecture",
        topic="Data Engineering",
        author="Eva Thompson",
        content="""Data pipelines move data from sources to destinations, transforming it along the way. Well-designed pipelines are reliable, observable, and maintainable.

Batch processing handles large volumes at scheduled intervals. Stream processing handles data in real-time as events occur. Lambda architecture combines both for complete coverage.

Data quality checks validate data at pipeline stages. Idempotent operations enable safe retries. Schema evolution manages changing data structures. Backfilling handles historical data when requirements change."""
    ),
    Article(
        title="Apache Kafka Fundamentals",
        topic="Data Engineering",
        author="Alice Chen",
        content="""Apache Kafka is a distributed streaming platform for building real-time data pipelines. Its durability and scalability make it popular for event-driven architectures.

Topics are ordered, partitioned logs. Producers write messages to topics; consumers read from topics. Partitions enable parallel processing and scalability.

Consumer groups enable parallel consumption with exactly-once semantics. Replication ensures durability across broker failures. Retention policies manage storage. Schema registry validates message schemas."""
    ),
    Article(
        title="Data Warehouse Design Patterns",
        topic="Data Engineering",
        author="Bob Martinez",
        content="""Data warehouses store analytical data for business intelligence. Star and snowflake schemas organize data for query performance.

Fact tables store quantitative metrics like sales or orders. Dimension tables store descriptive attributes like products and customers. Slowly changing dimensions track historical changes.

ETL processes extract, transform, and load data from operational systems. ELT approaches load raw data first, then transform using warehouse compute. Data lakehouse architectures combine data lake flexibility with warehouse reliability."""
    ),
    Article(
        title="Real-time Analytics with Apache Flink",
        topic="Data Engineering",
        author="Carol Williams",
        content="""Apache Flink provides stateful stream processing for real-time analytics. Its exactly-once semantics and event-time processing make it powerful for complex event handling.

Stream processing handles unbounded data streams. Stateful operators maintain information across events. Windowing aggregates events over time periods.

Event time processing handles out-of-order events using watermarks. Checkpointing provides fault tolerance. CEP (Complex Event Processing) detects patterns across event sequences. Flink SQL provides declarative stream processing."""
    ),
    Article(
        title="Data Quality and Governance",
        topic="Data Engineering",
        author="David Kim",
        content="""Data quality ensures data is fit for its intended use. Governance establishes policies and processes for data management.

Data profiling analyzes data characteristics like completeness and uniqueness. Validation rules enforce quality requirements. Cleansing processes correct identified issues.

Data catalogs organize metadata for discovery. Lineage tracking traces data through transformations. Access controls protect sensitive data. Data contracts formalize agreements between data producers and consumers."""
    ),
    Article(
        title="ETL vs ELT Patterns",
        topic="Data Engineering",
        author="Eva Thompson",
        content="""ETL (Extract, Transform, Load) and ELT (Extract, Load, Transform) represent different approaches to data integration.

ETL transforms data before loading, reducing destination storage requirements. It works well when transformations are complex but data volumes are manageable. Legacy systems often use ETL.

ELT loads raw data first, then transforms in the destination system. Cloud data warehouses make ELT attractive by providing powerful, scalable transformation compute. Staging raw data enables reprocessing when requirements change."""
    ),
]


def chunk_article(article: Article, chunk_size: int = 3) -> list[Chunk]:
    """Split article into chunks of sentences."""
    sentences = [s.strip() for s in article.content.split(".") if s.strip()]
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk_text = ". ".join(sentences[i:i + chunk_size])
        if chunk_text:
            chunks.append(Chunk(
                article_title=article.title,
                text=chunk_text,
                position=i // chunk_size
            ))
    return chunks


def create_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for texts using sentence-transformers."""
    return EMBEDDING_MODEL.encode(texts, show_progress_bar=False).tolist()


def check_existing_data() -> bool:
    """Check if data already exists in the database."""
    try:
        result = db.records.find({"labels": ["ARTICLE"], "limit": 1})
        return len(result) > 0
    except Exception:
        return False


def seed_database():
    """Main seeding function."""
    print("=" * 60)
    print("RUSHDB PAGE RANK SEEDING SCRIPT")
    print("=" * 60)

    # Check for existing data
    if check_existing_data():
        print("\n⚠️  Data already exists! Skipping seed.")
        print("   To re-seed, delete existing records first.")
        return

    print("\n📚 Generating document corpus...")
    all_chunks = []
    for article in ARTICLES:
        chunks = chunk_article(article)
        all_chunks.append((article, chunks))
        print(f"  - {article.title} -> {len(chunks)} chunks")

    # Flatten all chunks for embedding
    print("\n🔢 Generating embeddings...")
    chunk_texts = [chunk.text for _, chunks in all_chunks for chunk in chunks]
    embeddings = create_embeddings(chunk_texts)

    print(f"  Generated {len(embeddings)} embeddings (dimension: {EMBEDDING_DIM})")

    # Create records in RushDB
    print("\n💾 Creating records in RushDB...")
    article_records = {}
    chunk_records = []
    tx = db.transactions.begin()

    try:
        # Create articles
        for i, article in enumerate(ARTICLES):
            article_rec = db.records.create(
                label="ARTICLE",
                data={
                    "title": article.title,
                    "topic": article.topic,
                    "author": article.author,
                },
                transaction=tx
            )
            article_records[article.title] = article_rec
            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/{len(ARTICLES)} articles...")

        print(f"  Created {len(article_records)} articles")

        # Create chunks with vectors
        for i, (article, chunks) in enumerate(all_chunks):
            for j, chunk in enumerate(chunks):
                chunk_rec = db.records.create(
                    label="CHUNK",
                    data={
                        "text": chunk.text,
                        "articleTitle": chunk.article_title,
                        "topic": article.topic,
                        "author": article.author,
                        "position": chunk.position,
                    },
                    vectors=[{"propertyName": "text", "vector": embeddings[len(chunk_records)]}],
                    transaction=tx
                )
                chunk_records.append(chunk_rec)

                # Link chunk to its article
                db.records.attach(
                    source=chunk_rec,
                    target=article_records[chunk.article_title],
                    options={"type": "FROM_ARTICLE"},
                    transaction=tx
                )

            if (i + 1) % 10 == 0:
                print(f"  Created chunks for {i + 1}/{len(all_chunks)} articles...")

        print(f"  Created {len(chunk_records)} chunks with vectors")

        tx.commit()
        print("\n✅ Records committed successfully")

    except Exception as e:
        tx.rollback()
        print(f"\n❌ Error creating records: {e}")
        raise

    # Create graph edges
    print("\n🔗 Creating graph edges...")
    tx = db.transactions.begin()

    try:
        # Group chunks by various dimensions for edge creation
        chunks_by_author = defaultdict(list)
        chunks_by_topic = defaultdict(list)
        chunks_by_article = defaultdict(list)

        for chunk_rec in chunk_records:
            author = chunk_rec.get("author")
            topic = chunk_rec.get("topic")
            article_title = chunk_rec.get("articleTitle")
            if author:
                chunks_by_author[author].append(chunk_rec)
            if topic:
                chunks_by_topic[topic].append(chunk_rec)
            if article_title:
                chunks_by_article[article_title].append(chunk_rec)

        edge_count = 0

        # Author edges (same author = topical coherence)
        for author, chunks in chunks_by_author.items():
            if len(chunks) > 1:
                for i in range(len(chunks) - 1):
                    db.records.attach(
                        source=chunks[i],
                        target=chunks[i + 1],
                        options={"type": "SHARES_AUTHOR"},
                        transaction=tx
                    )
                    edge_count += 1

        # Topic edges (sequential within topic)
        for topic, chunks in chunks_by_topic.items():
            for i in range(len(chunks) - 1):
                db.records.attach(
                    source=chunks[i],
                    target=chunks[i + 1],
                    options={"type": "SHARES_TOPIC"},
                    transaction=tx
                )
                edge_count += 1

        # Citation-like edges (next chunk cites previous within article)
        for article_title, chunks in chunks_by_article.items():
            # Sort by position
            chunks_sorted = sorted(chunks, key=lambda c: c.get("position", 0))
            for i in range(len(chunks_sorted) - 1):
                db.records.attach(
                    source=chunks_sorted[i + 1],
                    target=chunks_sorted[i],
                    options={"type": "CITES"},
                    transaction=tx
                )
                edge_count += 1

        tx.commit()
        print(f"  Created {edge_count} graph edges")
        print("\n✅ Graph edges committed successfully")

    except Exception as e:
        tx.rollback()
        print(f"\n❌ Error creating edges: {e}")
        raise

    # Create vector index
    print("\n📊 Creating vector index...")
    try:
        index = db.ai.indexes.create({
            "label": "CHUNK",
            "propertyName": "text",
            "sourceType": "external",
            "dimensions": EMBEDDING_DIM,
            "similarityFunction": "cosine"
        })
        print(f"  Index created: {index.id}")

        # Upsert vectors into the index
        print("  Upserting vectors...")
        items = [
            {"recordId": chunk_rec.id, "vector": embeddings[i]}
            for i, chunk_rec in enumerate(chunk_records)
        ]
        db.ai.indexes.upsert_vectors(index.id, {"items": items})
        print("  Vectors upserted successfully")

    except Exception as e:
        print(f"  Warning: Index creation failed: {e}")
        print("  You may need to create the index manually.")

    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - {len(article_records)} articles")
    print(f"  - {len(chunk_records)} chunks")
    print(f"  - {edge_count} graph edges")
    print(f"  - {len(embeddings)} vector embeddings")
    print("\nRun `python main.py` to see PageRank-style scoring in action!")


if __name__ == "__main__":
    seed_database()
