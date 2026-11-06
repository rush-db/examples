"""
Seed script for Cross-Entity Link Prediction Tutorial.

Creates a realistic document cluster with authors, documents, topics, and tags
to demonstrate link prediction patterns. Uses transactions for atomicity.

Run this once before main.py to populate the database with sample data.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Verify token exists
token = os.getenv("RUSHDB_API_TOKEN")
if not token:
    print("Error: RUSHDB_API_TOKEN not found in environment")
    print("Copy .env.example to .env and add your token")
    sys.exit(1)

db = RushDB(token)

# Sample data
AUTHORS = [
    {"name": "Dr. Sarah Chen", "email": "s.chen@research.edu", "expertise": "machine_learning"},
    {"name": "Prof. James Miller", "email": "j.miller@university.edu", "expertise": "distributed_systems"},
    {"name": "Dr. Emily Watson", "email": "e.watson@ai-lab.org", "expertise": "natural_language_processing"},
    {"name": "Alex Rodriguez", "email": "a.rodriguez@tech.io", "expertise": "data_engineering"},
    {"name": "Dr. Michael Park", "email": "m.park@research.edu", "expertise": "computer_vision"},
    {"name": "Lisa Thompson", "email": "l.thompson@university.edu", "expertise": "reinforcement_learning"},
]

TOPICS = [
    {"name": "Machine Learning", "description": "Algorithms that improve through experience"},
    {"name": "Distributed Systems", "description": "Computing across multiple machines"},
    {"name": "Natural Language Processing", "description": "Understanding human language"},
    {"name": "Data Engineering", "description": "Building data pipelines and infrastructure"},
]

DOCUMENTS = [
    # Machine Learning documents
    {
        "title": "Deep Learning for Image Classification",
        "content": "Convolutional neural networks have revolutionized image classification. We present a novel architecture combining residual connections with attention mechanisms. Our approach achieves state-of-the-art results on ImageNet with 40% fewer parameters.",
        "topic": "Machine Learning",
        "tags": ["deep_learning", "computer_vision", "neural_networks"],
    },
    {
        "title": "Transfer Learning in NLP",
        "content": "Large language models pretrained on massive corpora can be fine-tuned for specific tasks with limited data. We explore techniques for efficient transfer learning including adapter methods and prompt tuning.",
        "topic": "Machine Learning",
        "tags": ["nlp", "transfer_learning", "transformers"],
    },
    {
        "title": "Reinforcement Learning from Human Feedback",
        "content": "Aligning AI systems with human values requires understanding preferences. We introduce a framework for learning reward models from comparative human feedback that scales to complex tasks.",
        "topic": "Machine Learning",
        "tags": ["reinforcement_learning", "alignment", "human_feedback"],
    },
    # Distributed Systems documents
    {
        "title": "Consensus Algorithms in Distributed Databases",
        "content": "Raft and Paxos remain fundamental for achieving consensus in distributed systems. We analyze their performance characteristics and propose optimizations for high-latency network conditions.",
        "topic": "Distributed Systems",
        "tags": ["distributed_systems", "consensus", "databases"],
    },
    {
        "title": "Microservices Communication Patterns",
        "content": "Service mesh architectures enable flexible inter-service communication. We examine patterns for implementing circuit breakers, retries, and observability in Kubernetes environments.",
        "topic": "Distributed Systems",
        "tags": ["microservices", "kubernetes", "distributed_systems"],
    },
    {
        "title": "Event-Driven Architecture at Scale",
        "content": "Apache Kafka has become the backbone of event streaming platforms. We share lessons learned from processing millions of events per second with exactly-once semantics.",
        "topic": "Distributed Systems",
        "tags": ["event_driven", "kafka", "streaming"],
    },
    # NLP documents
    {
        "title": "Retrieval-Augmented Generation",
        "content": "Combining retrieval systems with generative models improves factual accuracy. We propose a hybrid architecture that dynamically retrieves relevant documents to augment LLM responses.",
        "topic": "Natural Language Processing",
        "tags": ["rag", "nlp", "information_retrieval"],
    },
    {
        "title": "Multilingual Model Training",
        "content": "Cross-lingual transfer learning enables models trained on high-resource languages to generalize to low-resource languages. We investigate optimal vocabulary construction and alignment techniques.",
        "topic": "Natural Language Processing",
        "tags": ["multilingual", "nlp", "transfer_learning"],
    },
    {
        "title": "Semantic Search with Vector Embeddings",
        "content": "Dense vector representations capture semantic meaning beyond keyword matching. We compare different embedding models for enterprise search applications and propose a hybrid BM25-vector approach.",
        "topic": "Natural Language Processing",
        "tags": ["semantic_search", "embeddings", "information_retrieval"],
    },
    # Data Engineering documents
    {
        "title": "Data Lakehouse Architecture",
        "content": "Unifying data lake flexibility with data warehouse reliability requires careful schema design. We present patterns for implementing ACID transactions on object storage with schema evolution support.",
        "topic": "Data Engineering",
        "tags": ["data_lakehouse", "data_warehouse", "architecture"],
    },
    {
        "title": "Real-time Feature Engineering",
        "content": "ML models in production require low-latency feature computation. We describe a streaming architecture using Flink for computing sliding window aggregations and late-arriving data handling.",
        "topic": "Data Engineering",
        "tags": ["feature_store", "streaming", "ml_platforms"],
    },
    {
        "title": "Data Quality Monitoring at Scale",
        "content": "Maintaining data quality in large pipelines requires automated monitoring. We introduce a framework for defining data contracts and detecting anomalies using statistical methods and ML.",
        "topic": "Data Engineering",
        "tags": ["data_quality", "monitoring", "data_governance"],
    },
]

# Define tag IDs that will be created
TAG_IDS = {}


def check_and_clear_data():
    """Check if data already exists and clear if requested."""
    existing_docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    
    if existing_docs.data:
        response = input(
            "Database contains existing documents. Clear and reseed? (y/N): "
        )
        if response.lower() == 'y':
            print("Clearing existing data...")
            db.records.delete({"labels": ["DOCUMENT"]})
            db.records.delete({"labels": ["AUTHOR"]})
            db.records.delete({"labels": ["TOPIC"]})
            db.records.delete({"labels": ["TAG"]})
            print("Existing data cleared.")
        else:
            print("Keeping existing data. Some operations may fail.")
            return False
    return True


def create_tags(db):
    """Create all unique tags."""
    print("\n📋 Creating tags...")
    all_tags = set()
    for doc in DOCUMENTS:
        all_tags.update(doc["tags"])
    
    for i, tag_name in enumerate(sorted(all_tags)):
        tag = db.records.create(
            label="TAG",
            data={"name": tag_name, "category": "technical"}
        )
        TAG_IDS[tag_name] = tag.id
        if (i + 1) % 4 == 0:
            print(f"  Created {i + 1}/{len(all_tags)} tags...")
    
    print(f"  ✓ Created {len(all_tags)} tags")
    return TAG_IDS


def create_topics(db):
    """Create topics with a transaction."""
    print("\n📚 Creating topics...")
    
    with db.transactions.begin() as tx:
        topic_records = []
        for topic_data in TOPICS:
            topic = db.records.create(
                label="TOPIC",
                data=topic_data,
                transaction=tx
            )
            topic_records.append(topic)
        # Transaction auto-commits on clean exit
    
    print(f"  ✓ Created {len(TOPICS)} topics")
    return {t.data["name"]: t for t in topic_records}


def create_authors(db):
    """Create authors."""
    print("\n👥 Creating authors...")
    author_records = []
    
    for i, author_data in enumerate(AUTHORS):
        author = db.records.create(
            label="AUTHOR",
            data=author_data
        )
        author_records.append(author)
        if (i + 1) % 3 == 0:
            print(f"  Created {i + 1}/{len(AUTHORS)} authors...")
    
    print(f"  ✓ Created {len(AUTHORS)} authors")
    return author_records


def create_documents_with_relationships(db, authors, topics_by_name):
    """Create documents and link them to authors, topics, and tags."""
    print("\n📄 Creating documents with relationships...")
    
    # Assign authors to documents (round-robin with some overlap)
    author_indices = [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]
    
    for i, doc_data in enumerate(DOCUMENTS):
        author_idx = author_indices[i]
        author = authors[author_idx]
        topic = topics_by_name[doc_data["topic"]]
        
        with db.transactions.begin() as tx:
            # Create the document
            doc = db.records.create(
                label="DOCUMENT",
                data={
                    "title": doc_data["title"],
                    "content": doc_data["content"],
                    "created_at": f"2024-{1 + (i % 12):02d}-15",
                },
                transaction=tx
            )
            
            # Link to author
            db.records.attach(
                source=doc,
                target=author,
                options={"type": "AUTHORED_BY", "direction": "out"},
                transaction=tx
            )
            
            # Link to topic
            db.records.attach(
                source=doc,
                target=topic,
                options={"type": "BELONGS_TO", "direction": "out"},
                transaction=tx
            )
            
            # Link to tags
            for tag_name in doc_data["tags"]:
                tag_id = TAG_IDS.get(tag_name)
                if tag_id:
                    tag_record = db.records.find_by_id(tag_id)
                    db.records.attach(
                        source=doc,
                        target=tag_record,
                        options={"type": "TAGGED_WITH", "direction": "out"},
                        transaction=tx
                    )
        
        if (i + 1) % 4 == 0:
            print(f"  Created {i + 1}/{len(DOCUMENTS)} documents with relationships...")
    
    print(f"  ✓ Created {len(DOCUMENTS)} documents with relationships")


def create_cross_references(db):
    """
    Create some intentional cross-references to simulate a real corpus.
    These represent existing citations/references between documents.
    """
    print("\n🔗 Creating cross-document references...")
    
    # Find all documents
    docs = db.records.find({"labels": ["DOCUMENT"], "limit": 100})
    doc_list = docs.data
    
    if len(doc_list) < 4:
        print("  ⚠ Not enough documents to create cross-references")
        return
    
    # Create some intentional links
    cross_refs = [
        # DL for Image Classification cites RLHF (both ML topics)
        (0, 2),
        # Retrieval-Augmented Generation cites Semantic Search (both NLP)
        (6, 8),
        # Event-Driven cites Consensus (distributed systems)
        (5, 3),
        # Feature Engineering cites DL for Image Classification (ML ops)
        (9, 0),
    ]
    
    for source_idx, target_idx in cross_refs:
        if source_idx < len(doc_list) and target_idx < len(doc_list):
            db.records.attach(
                source=doc_list[source_idx],
                target=doc_list[target_idx],
                options={"type": "CITES", "direction": "out"}
            )
    
    print(f"  ✓ Created {len(cross_refs)} cross-document references")


def print_summary():
    """Print a summary of created data."""
    print("\n" + "=" * 50)
    print("📊 DATABASE SEED SUMMARY")
    print("=" * 50)
    
    labels_result = db.labels.find({})
    for label_info in labels_result.data:
        print(f"  • {label_info.name}: {label_info.count} records")
    
    print("\n✅ Database is ready for the link prediction tutorial!")
    print("   Run `python main.py` to see link prediction in action.")


def main():
    print("🚀 RushDB Link Prediction Tutorial - Data Seeder")
    print("=" * 50)
    
    # Check if we should proceed
    if not check_and_clear_data():
        print("\n⚠ Skipping seed - using existing data")
        print_summary()
        return
    
    # Create all data
    create_tags(db)
    topics = create_topics(db)
    authors = create_authors(db)
    create_documents_with_relationships(db, authors, topics)
    create_cross_references(db)
    
    print_summary()


if __name__ == "__main__":
    main()
