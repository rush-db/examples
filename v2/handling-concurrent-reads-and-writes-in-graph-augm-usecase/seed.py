"""
Seed script for the concurrent RAG demo.
Creates research projects, documents, and relationships.

This script is idempotent — run it multiple times safely.
"""

import os
import sys
from datetime import datetime, timedelta
import random

from faker import Faker
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Verify RushDB is available
try:
    from rushdb import RushDB
except ImportError:
    print("Error: rushdb package not installed. Run: pip install rushdb")
    sys.exit(1)

fake = Faker()

# Research topics with realistic content snippets
RESEARCH_TOPICS = {
    "ai": {
        "keywords": ["neural network", "deep learning", "transformer", "attention mechanism", "gradient descent"],
        "sample_titles": [
            "Advances in Transformer Architecture Design",
            "Optimization Techniques for Neural Networks",
            "Understanding Attention Mechanisms in Modern LLMs",
            "Benchmarking Foundation Models on Reasoning Tasks",
            "Efficient Fine-Tuning Strategies for Domain Adaptation"
        ]
    },
    "blockchain": {
        "keywords": ["smart contract", "consensus", "decentralized", "token", "proof of stake"],
        "sample_titles": [
            "Layer 2 Scaling Solutions for Ethereum",
            "Formal Verification of Smart Contracts",
            "Cross-Chain Interoperability Protocols",
            "DeFi Liquidity Pool Dynamics",
            "Zero-Knowledge Proofs in Blockchain Privacy"
        ]
    },
    "quantum": {
        "keywords": ["qubit", "entanglement", "quantum gate", "error correction", "quantum supremacy"],
        "sample_titles": [
            "Topological Quantum Computing Approaches",
            "Quantum Error Correction with Surface Codes",
            "Quantum Machine Learning: Current State and Future",
            "Post-Quantum Cryptography Standards",
            "Practical Quantum Advantage in Optimization Problems"
        ]
    }
}


def get_embedding_model():
    """Initialize the embedding model (cached for reuse)."""
    return SentenceTransformer('all-MiniLM-L6-v2')


def generate_document_content(topic: str) -> tuple[str, list]:
    """Generate realistic research document content and its embedding."""
    topic_data = RESEARCH_TOPICS.get(topic, RESEARCH_TOPICS["ai"])
    
    # Build a coherent paragraph about the topic
    keyword = random.choice(topic_data["keywords"])
    content = f"""
{fake.paragraph(nb_sentences=8)} 

This research addresses the challenge of {keyword} in modern computational systems. 
We propose a novel approach that builds upon existing methods while introducing significant 
improvements in efficiency and scalability.

{fake.paragraph(nb_sentences=5)}

Our methodology involves {fake.sentence()} {fake.sentence()} {fake.sentence()}. 
The results demonstrate {random.randint(15, 40)}% improvement over baseline approaches.

{fake.paragraph(nb_sentences=3)}
    """.strip()
    
    # Generate embedding
    model = get_embedding_model()
    embedding = model.encode(content).tolist()
    
    return content, embedding


def check_existing_data(db: RushDB) -> bool:
    """Check if seed data already exists."""
    result = db.records.find({"labels": ["PROJECT"], "limit": 1})
    return len(result.data) > 0


def clear_existing_data(db: RushDB) -> None:
    """Clear any existing seed data for clean re-seeding."""
    print("Clearing existing data...")
    
    # Delete in order (respecting relationships)
    for label in ["DOCUMENT", "RESEARCHER", "PROJECT"]:
        db.records.delete_many({"labels": [label], "where": {}})


def seed(db: RushDB, force: bool = False) -> dict:
    """
    Seed the database with research assistant data.
    
    Returns dict with created record counts.
    """
    print("\n" + "=" * 60)
    print("  Research Assistant Seed Data Generator")
    print("=" * 60 + "\n")
    
    # Check for existing data
    if check_existing_data(db):
        if force:
            clear_existing_data(db)
        else:
            print("Seed data already exists. Run with --force to re-seed.")
            return {"skipped": True}
    
    print(f"Generating seed data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)\n")
    
    # Track created records
    created = {"projects": 0, "researchers": 0, "documents": 0}
    
    # Create projects
    print("Creating research projects...")
    projects = []
    for i, topic in enumerate(["AI Research", "Blockchain Systems", "Quantum Computing"]):
        project = db.records.create(
            label="PROJECT",
            data={
                "name": topic,
                "slug": topic.lower().replace(" ", "-"),
                "description": fake.sentence() + " " + fake.sentence(),
                "created_at": (datetime.now() - timedelta(days=random.randint(30, 180))).isoformat()
            }
        )
        projects.append(project)
        created["projects"] += 1
        print(f"  Created project: {project['name']}")
    
    # Create researchers
    print("\nCreating researchers...")
    researchers = []
    researcher_names = [
        ("Alice Chen", "alice@research.org"),
        ("Bob Martinez", "bob@research.org"),
        ("Carol Williams", "carol@research.org"),
        ("David Kim", "david@research.org"),
        ("Eva Thompson", "eva@research.org")
    ]
    
    for name, email in researcher_names:
        researcher = db.records.create(
            label="RESEARCHER",
            data={
                "name": name,
                "email": email,
                "institution": fake.company(),
                "expertise": random.choice(list(RESEARCH_TOPICS.keys())),
                "h_index": random.randint(5, 50)
            }
        )
        researchers.append(researcher)
        created["researchers"] += 1
        print(f"  Created researcher: {name}")
    
    # Create documents with embeddings
    print("\nCreating documents with embeddings...")
    print("  (This downloads the embedding model on first run)")
    
    topic_map = {
        "AI Research": "ai",
        "Blockchain Systems": "blockchain",
        "Quantum Computing": "quantum"
    }
    
    documents = []
    for project in tqdm(projects, desc="  Projects"):
        topic_key = topic_map.get(project['name'], "ai")
        topic_data = RESEARCH_TOPICS[topic_key]
        
        for title in topic_data["sample_titles"]:
            content, embedding = generate_document_content(topic_key)
            
            document = db.records.create(
                label="DOCUMENT",
                data={
                    "title": title,
                    "slug": title.lower().replace(" ", "-").replace(":", ""),
                    "content": content,
                    "topic": topic_key,
                    "word_count": len(content.split()),
                    "published_at": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                    "status": "published"
                },
                vectors=[{"propertyName": "content", "vector": embedding}]
            )
            documents.append(document)
            created["documents"] += 1
    
    # Create relationships
    print("\nCreating relationships...")
    
    # Assign researchers to projects and documents
    for i, researcher in enumerate(tqdm(researchers, desc="  Researchers")):
        # Assign to a project (cycle through)
        project = projects[i % len(projects)]
        db.records.attach(
            source=researcher,
            target=project,
            options={"type": "WORKS_ON", "direction": "out"}
        )
        
        # Assign to some documents
        assigned_docs = random.sample(documents, k=random.randint(3, 6))
        for doc in assigned_docs:
            db.records.attach(
                source=researcher,
                target=doc,
                options={"type": "AUTHORED", "direction": "out"}
            )
    
    print("\n" + "=" * 60)
    print("  Seed Complete!")
    print("=" * 60)
    print(f"  Projects:     {created['projects']}")
    print(f"  Researchers:  {created['researchers']}")
    print(f"  Documents:    {created['documents']}")
    print("=" * 60 + "\n")
    
    return created


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed research assistant data")
    parser.add_argument("--force", action="store_true", help="Clear existing data and re-seed")
    args = parser.parse_args()
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)
    
    db = RushDB(api_key)
    
    try:
        result = seed(db, force=args.force)
        if result.get("skipped"):
            print("Use --force to clear and re-seed")
    except Exception as e:
        print(f"Error seeding data: {e}")
        sys.exit(1)
