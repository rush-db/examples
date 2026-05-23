"""
Seed script for RAG Feedback Loop demo.

Creates sample documents across multiple categories with pre-computed embeddings.
Uses deterministic generation so the same data is created each time.

Run this once before main.py to populate the database with initial documents.
"""

import os
import random
from pathlib import Path

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()


# Pre-computed embeddings for demo (768-dimensional vectors simulating OpenAI ada-002)
# These are deterministic and represent semantically different content categories
def generate_embedding(seed: int) -> list:
    """Generate a deterministic pseudo-embedding based on a seed."""
    random.seed(seed)
    # Generate normalized random vector
    vec = [random.uniform(-1, 1) for _ in range(768)]
    # Normalize
    magnitude = sum(v * v for v in vec) ** 0.5
    return [v / magnitude for v in vec]


DOCUMENTS = [
    # Machine Learning category
    {"title": "Understanding RAG Systems", "content": "RAG combines retrieval with generation to enhance LLM outputs with relevant knowledge from external sources.", "category": "machine-learning", "tags": ["rag", "llm", "retrieval"]},
    {"title": "The Future of ML Optimization Techniques", "content": "Modern optimization techniques like AdamW, LAMB, and gradient clipping enable training larger models more efficiently.", "category": "machine-learning", "tags": ["optimization", "training", "deep-learning"]},
    {"title": "Advanced Deep Learning Strategies", "content": "Transfer learning, fine-tuning, and prompt engineering are key strategies for adapting pre-trained models to specific tasks.", "category": "machine-learning", "tags": ["deep-learning", "transfer-learning", "fine-tuning"]},
    {"title": "Machine Learning Model Training Best Practices", "content": "Best practices include proper data augmentation, regularization techniques, and validation strategies to prevent overfitting.", "category": "machine-learning", "tags": ["training", "best-practices", "overfitting"]},
    {"title": "Neural Network Optimization Methods", "content": "Various optimization methods like SGD, Adam, and RMSprop help neural networks converge faster and more reliably.", "category": "machine-learning", "tags": ["optimization", "neural-networks", "gradient-descent"]},
    {"title": "Gradient Descent and Backpropagation", "content": "Gradient descent with backpropagation forms the foundation of neural network training through gradient-based optimization.", "category": "machine-learning", "tags": ["gradient-descent", "backpropagation", "fundamentals"]},
    {"title": "Transformer Architecture Explained", "content": "Transformers use self-attention mechanisms to process sequential data without recurrence, enabling parallelization.", "category": "machine-learning", "tags": ["transformers", "attention", "architecture"]},
    {"title": "Tokenization Strategies for LLMs", "content": "Byte-pair encoding, WordPiece, and SentencePiece are common tokenization strategies for preparing text for language models.", "category": "machine-learning", "tags": ["tokenization", "nlp", "preprocessing"]},
    
    # Database category
    {"title": "Graph Databases vs Relational Databases", "content": "Graph databases excel at relationship-heavy queries while relational databases handle structured tabular data efficiently.", "category": "database", "tags": ["graph-database", "relational", "comparison"]},
    {"title": "Introduction to Neo4j and Cypher", "content": "Neo4j is a popular graph database using the Cypher query language for expressive pattern matching.", "category": "database", "tags": ["neo4j", "cypher", "graph-database"]},
    {"title": "Property Graphs in Modern Applications", "content": "Property graphs store both data and relationships as first-class entities, enabling rich semantic queries.", "category": "database", "tags": ["property-graphs", "data-model", "relationships"]},
    {"title": "Vector Indexes for Similarity Search", "content": "Vector indexes like HNSW and IVF enable efficient approximate nearest neighbor search in high-dimensional spaces.", "category": "database", "tags": ["vector-search", "similarity", "indexing"]},
    {"title": "ACID Transactions in Distributed Systems", "content": "Distributed transactions ensure data consistency across multiple nodes using consensus protocols.", "category": "database", "tags": ["transactions", "distributed-systems", "consistency"]},
    {"title": "Time-Series Database Optimization", "content": "Time-series databases use compression and downsampling to efficiently store and query high-frequency data points.", "category": "database", "tags": ["time-series", "optimization", "compression"]},
    {"title": "Database Indexing Strategies", "content": "B-trees, hash indexes, and bitmap indexes each offer different trade-offs for read vs write heavy workloads.", "category": "database", "tags": ["indexing", "performance", "b-tree"]},
    {"title": "Query Optimization Techniques", "content": "Query planners use statistics and cost models to choose optimal execution plans for complex queries.", "category": "database", "tags": ["query-optimization", "execution-plans", "performance"]},
    
    # Software Engineering category
    {"title": "Clean Code Principles for Python", "content": "Clean code principles include meaningful names, small functions, and proper error handling for maintainable software.", "category": "software-engineering", "tags": ["clean-code", "python", "best-practices"]},
    {"title": "Design Patterns in Modern Software", "content": "Creational, structural, and behavioral design patterns provide proven solutions to common software design problems.", "category": "software-engineering", "tags": ["design-patterns", "architecture", "oop"]},
    {"title": "Microservices Architecture Best Practices", "content": "Microservices should be loosely coupled, independently deployable, and organized around business capabilities.", "category": "software-engineering", "tags": ["microservices", "architecture", "distributed-systems"]},
    {"title": "API Design for Developer Experience", "content": "RESTful API design principles help create intuitive, consistent, and well-documented interfaces for developers.", "category": "software-engineering", "tags": ["api-design", "rest", "developer-experience"]},
    {"title": "Testing Strategies for Robust Applications", "content": "Comprehensive testing includes unit tests, integration tests, and end-to-end tests at different abstraction levels.", "category": "software-engineering", "tags": ["testing", "quality", "tdd"]},
    {"title": "CI/CD Pipeline Best Practices", "content": "Effective CI/CD pipelines automate builds, tests, and deployments to enable rapid and reliable software delivery.", "category": "software-engineering", "tags": ["cicd", "automation", "devops"]},
    {"title": "Container Orchestration with Kubernetes", "content": "Kubernetes provides automated deployment, scaling, and management of containerized applications in production.", "category": "software-engineering", "tags": ["kubernetes", "containers", "orchestration"]},
    {"title": "Observability and Monitoring Patterns", "content": "Observability combines metrics, logs, and traces to provide deep insight into system behavior and performance.", "category": "software-engineering", "tags": ["observability", "monitoring", "logging"]},
    
    # Data Engineering category
    {"title": "Building Scalable Data Pipelines", "content": "Scalable data pipelines handle increasing data volumes through partitioning, parallel processing, and fault tolerance.", "category": "data-engineering", "tags": ["data-pipelines", "scalability", "etl"]},
    {"title": "Apache Kafka for Event Streaming", "content": "Apache Kafka provides durable, scalable message streaming for real-time data processing and event-driven architectures.", "category": "data-engineering", "tags": ["kafka", "event-streaming", "messaging"]},
    {"title": "Data Lake Architecture Patterns", "content": "Modern data lakes use medallion architecture with bronze, silver, and gold layers for progressive data refinement.", "category": "data-engineering", "tags": ["data-lake", "architecture", "medallion"]},
    {"title": "ETL vs ELT Approaches", "content": "ETL transforms data before loading while ELT loads raw data first and transforms within the data warehouse.", "category": "data-engineering", "tags": ["etl", "elt", "data-warehouse"]},
    {"title": "Data Quality Management Strategies", "content": "Data quality management includes profiling, cleansing, validation, and continuous monitoring for reliable datasets.", "category": "data-engineering", "tags": ["data-quality", "validation", "cleansing"]},
    {"title": "Real-Time Analytics with Apache Spark", "content": "Apache Spark Structured Streaming enables real-time analytics on continuous data streams with familiar SQL interfaces.", "category": "data-engineering", "tags": ["spark", "real-time", "streaming"]},
    {"title": "Data Mesh Implementation Guide", "content": "Data mesh decentralizes data ownership to domain teams while maintaining global governance and interoperability.", "category": "data-engineering", "tags": ["data-mesh", "architecture", "governance"]},
    {"title": "Feature Engineering for ML Pipelines", "content": "Feature engineering transforms raw data into model-ready features through scaling, encoding, and selection techniques.", "category": "data-engineering", "tags": ["feature-engineering", "ml", "preprocessing"]},
    
    # AI/LLM category
    {"title": "Prompt Engineering Techniques", "content": "Effective prompts use clear instructions, context, examples, and formatting to guide LLM responses effectively.", "category": "ai-llm", "tags": ["prompt-engineering", "llm", "techniques"]},
    {"title": "Context Window Management Strategies", "content": "Managing limited context windows through summarization, retrieval, and prioritization maximizes LLM effectiveness.", "category": "ai-llm", "tags": ["context-window", "llm", "context-management"]},
    {"title": "Retrieval Augmented Generation Overview", "content": "RAG enhances LLM responses by retrieving relevant documents and incorporating them into the generation context.", "category": "ai-llm", "tags": ["rag", "retrieval", "generation"]},
    {"title": "Hallucination Mitigation Strategies", "content": "Mitigating hallucinations involves grounding responses in retrieved facts, confidence scoring, and factual verification.", "category": "ai-llm", "tags": ["hallucination", "reliability", "truthfulness"]},
    {"title": "Multi-Modal AI Systems", "content": "Multi-modal AI processes and relates information across text, images, audio, and video modalities.", "category": "ai-llm", "tags": ["multi-modal", "vision", "audio"]},
    {"title": "Fine-Tuning vs RAG Comparison", "content": "Fine-tuning adapts model weights for specific tasks while RAG provides dynamic knowledge retrieval without retraining.", "category": "ai-llm", "tags": ["fine-tuning", "rag", "comparison"]},
    {"title": "AI Safety and Alignment Principles", "content": "AI safety focuses on ensuring AI systems behave as intended and avoid harmful outcomes through alignment techniques.", "category": "ai-llm", "tags": ["ai-safety", "alignment", "ethics"]},
    {"title": "Evaluating LLM Performance", "content": "LLM evaluation uses benchmarks, human evaluation, and task-specific metrics to assess model capabilities and limitations.", "category": "ai-llm", "tags": ["evaluation", "benchmarks", "metrics"]},
    
    # Cloud/Infrastructure category
    {"title": "Serverless Architecture Patterns", "content": "Serverless architectures auto-scale based on demand, charging only for actual compute usage.", "category": "cloud", "tags": ["serverless", "architecture", "auto-scaling"]},
    {"title": "Multi-Cloud Strategy Considerations", "content": "Multi-cloud strategies provide redundancy, avoid vendor lock-in, and leverage best-of-breed services across providers.", "category": "cloud", "tags": ["multi-cloud", "strategy", "resilience"]},
    {"title": "Cloud Cost Optimization Techniques", "content": "Cloud cost optimization includes right-sizing resources, reserved instances, and automated scaling policies.", "category": "cloud", "tags": ["cost-optimization", "cloud", "budget"]},
    {"title": "Infrastructure as Code Best Practices", "content": "IaC treats infrastructure definitions as version-controlled code, enabling repeatable and auditable deployments.", "category": "cloud", "tags": ["iac", "infrastructure", "automation"]},
    {"title": "Edge Computing Use Cases", "content": "Edge computing processes data closer to the source, reducing latency for IoT, autonomous systems, and real-time applications.", "category": "cloud", "tags": ["edge-computing", "latency", "iot"]},
    {"title": "Disaster Recovery Planning", "content": "Disaster recovery plans define RTO and RPO targets, backup strategies, and failover procedures for critical systems.", "category": "cloud", "tags": ["disaster-recovery", "backup", "failover"]},
    {"title": "Network Security in Cloud Environments", "content": "Cloud network security combines VPCs, security groups, WAF, and encryption to protect data in transit and at rest.", "category": "cloud", "tags": ["security", "networking", "encryption"]},
    {"title": "Load Balancing and Traffic Management", "content": "Load balancers distribute traffic across resources using various algorithms while ensuring high availability.", "category": "cloud", "tags": ["load-balancing", "traffic", "availability"]},
    
    # Security category
    {"title": "Zero Trust Security Model", "content": "Zero trust assumes no implicit trust, requiring verification for every access request regardless of network location.", "category": "security", "tags": ["zero-trust", "security", "authentication"]},
    {"title": "API Security Best Practices", "content": "API security includes authentication, rate limiting, input validation, and encryption to protect services from attacks.", "category": "security", "tags": ["api-security", "authentication", "rate-limiting"]},
    {"title": "Secrets Management Solutions", "content": "Secrets management solutions securely store, rotate, and access sensitive credentials and API keys.", "category": "security", "tags": ["secrets-management", "credentials", "vault"]},
    {"title": "Incident Response Playbooks", "content": "Incident response playbooks define detection, containment, eradication, and recovery procedures for security events.", "category": "security", "tags": ["incident-response", "security", "playbooks"]},
    {"title": "Encryption Standards and Algorithms", "content": "Modern encryption uses AES-256, RSA, and elliptic curve cryptography with proper key management practices.", "category": "security", "tags": ["encryption", "cryptography", "standards"]},
    {"title": "OAuth 2.0 and OpenID Connect Flow", "content": "OAuth 2.0 and OIDC provide delegated authorization and authentication for modern application security.", "category": "security", "tags": ["oauth", "oidc", "authentication"]},
    {"title": "Penetration Testing Methodologies", "content": "Penetration testing follows structured methodologies like OWASP to identify and exploit security vulnerabilities.", "category": "security", "tags": ["penetration-testing", "owasp", "vulnerabilities"]},
    {"title": "Security Logging and SIEM Integration", "content": "Security logging captures events for analysis while SIEM solutions aggregate and correlate logs for threat detection.", "category": "security", "tags": ["logging", "siem", "monitoring"]},
]


def check_if_seeded(db: RushDB) -> bool:
    """Check if documents have already been seeded."""
    result = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    return len(result.data) > 0


def create_vector_index(db: RushDB) -> str:
    """Create vector index for document content if it doesn't exist."""
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        if idx["label"] == "DOCUMENT" and idx["propertyName"] == "content":
            return idx["__id"]
    
    # Create new external index
    index = db.ai.indexes.create({
        "label": "DOCUMENT",
        "propertyName": "content",
        "sourceType": "external",
        "dimensions": 768,
        "similarityFunction": "cosine"
    })
    return index.id


def seed_documents(db: RushDB):
    """Seed documents into RushDB with vector embeddings."""
    print("\n=== Seeding Documents ===\n")
    
    # Check if already seeded
    if check_if_seeded(db):
        print("Documents already seeded, skipping...")
        return
    
    # Create vector index
    print("Creating vector index for DOCUMENT.content...")
    index_id = create_vector_index(db)
    print(f"  Index ID: {index_id}")
    
    # Create documents with embeddings
    print("\nCreating documents with embeddings...")
    created = 0
    
    for i, doc_data in enumerate(DOCUMENTS):
        # Generate deterministic embedding based on document index
        vector = generate_embedding(i)
        
        doc = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc_data["title"],
                "content": doc_data["content"],
                "category": doc_data["category"],
                "tags": doc_data["tags"]
            },
            vectors=[{"propertyName": "content", "vector": vector}]
        )
        created += 1
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{len(DOCUMENTS)} documents...")
    
    # Upsert vectors to the index
    print("\nUpserting vectors to index...")
    all_docs = db.records.find({"labels": ["DOCUMENT"], "limit": len(DOCUMENTS)})
    
    items = []
    for doc in all_docs.data:
        # Find corresponding original data
        for j, orig in enumerate(DOCUMENTS):
            if orig["title"] == doc.get("title"):
                vector = generate_embedding(j)
                items.append({"recordId": doc["__id"], "vector": vector})
                break
    
    db.ai.indexes.upsert_vectors(index_id, {"items": items})
    print(f"  Indexed {len(items)} document vectors")
    
    # Get index stats
    stats = db.ai.indexes.stats(index_id)
    print(f"\nIndex stats: {stats.get('indexedRecords', 0)} records indexed")
    print("\n✓ Seeding complete!")


def main():
    """Main entry point for the seed script."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY environment variable not set")
        print("Please copy .env.example to .env and fill in your API key")
        return
    
    url = os.environ.get("RUSHDB_URL")
    if url:
        db = RushDB(api_key, url=url)
    else:
        db = RushDB(api_key)
    
    seed_documents(db)


if __name__ == "__main__":
    main()
