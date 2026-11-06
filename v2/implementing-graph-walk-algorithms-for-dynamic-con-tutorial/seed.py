#!/usr/bin/env python3
"""
Knowledge Graph Seeding Script

This script creates a sample knowledge graph representing a research knowledge base
with documents, concepts, authors, and their relationships. It demonstrates RushDB's
property graph capabilities for building interconnected knowledge structures.

The graph models:
- RESEARCHER nodes with expertise areas
- DOCUMENT nodes containing research papers
- CONCEPT nodes representing key topics
- Cites relationships between documents
- Contains relationships (documents contain concepts)
- Affiliated relationships (researchers work at institutions)
- Collaborates relationships (researcher co-authorship)
"""

import os
import random
from dotenv import load_dotenv
from faker import Faker
from rushdb import RushDB

# Initialize Faker for generating realistic names and text
fake = Faker()
Faker.seed(42)
random.seed(42)

# Knowledge base content - pre-defined concepts for domain realism
DOMAIN_CONCEPTS = [
    {"name": "Neural Networks", "description": "Computing systems inspired by biological neural networks"},
    {"name": "Deep Learning", "description": "Machine learning with multiple layers of neural networks"},
    {"name": "Transformer Architecture", "description": "Neural network architecture using self-attention mechanisms"},
    {"name": "Natural Language Processing", "description": "Computational techniques for analyzing textual data"},
    {"name": "Computer Vision", "description": "Enabling computers to derive information from images and videos"},
    {"name": "Reinforcement Learning", "description": "Learning through interaction with an environment"},
    {"name": "Graph Neural Networks", "description": "Neural networks operating on graph-structured data"},
    {"name": "Transfer Learning", "description": "Leveraging knowledge from one domain to another"},
    {"name": "Few-shot Learning", "description": "Learning from minimal labeled examples"},
    {"name": "Multimodal Learning", "description": "Processing information from multiple modalities"},
    {"name": "Knowledge Graphs", "description": "Structured representation of real-world entities"},
    {"name": "Attention Mechanisms", "description": "Focusing on relevant parts of input data"},
    {"name": "Embeddings", "description": "Dense vector representations of discrete variables"},
    {"name": "Prompt Engineering", "description": "Designing effective inputs for language models"},
    {"name": "Retrieval Augmented Generation", "description": "Enhancing LLM outputs with external knowledge"},
]

# Sample document titles for realism
DOCUMENT_TITLES = [
    "Attention Is All You Need: Revisiting Transformer Principles",
    "Graph-Based Context Assembly for Large Language Models",
    "Efficient Retrieval Strategies in Dense Knowledge Bases",
    "Dynamic Context Selection via Traversable Knowledge Graphs",
    "Neural Architecture Search in Resource-Constrained Environments",
    "Cross-Modal Alignment for Vision-Language Models",
    "Hierarchical Reinforcement Learning for Complex Tasks",
    "Federated Learning with Privacy-Preserving Aggregation",
    "Scaling Laws for Neural Language Models",
    "Emergent Abilities in Few-Shot Learning Scenarios",
    "Knowledge Graph Completion with Graph Neural Networks",
    "Zero-Shot Transfer Across Domain Boundaries",
    "Efficient Fine-Tuning of Pre-trained Language Models",
    "Contextual Embeddings for Semantic Search",
    "Multi-Hop Reasoning in Knowledge-Intensive Tasks",
    "Retrieval-Augmented Generation for Open-Domain QA",
    "Compositional Generalization in Neural Networks",
    "Continual Learning Without Catastrophic Forgetting",
    "Self-Supervised Learning for Visual Representations",
    "Towards Robust and Fair Machine Learning Systems",
]


def clear_existing_data(db: RushDB) -> None:
    """Remove any existing graph data to ensure clean state."""
    print("\n[1/5] Clearing existing data...")
    
    # Delete all records by label - in production, use more targeted cleanup
    labels_to_clear = ["RESEARCHER", "DOCUMENT", "CONCEPT", "INSTITUTION"]
    for label in labels_to_clear:
        try:
            result = db.records.delete_many({"labels": [label], "where": {}})
            print(f"  Cleared {result.data.get('deletedCount', 0)} {label} records")
        except Exception as e:
            print(f"  Note: {label} cleanup: {e}")


def create_concepts(db: RushDB) -> dict:
    """Create concept nodes representing key topics in the knowledge base."""
    print("\n[2/5] Creating concept nodes...")
    concepts = {}
    
    with db.transactions.begin() as tx:
        for i, concept_data in enumerate(DOMAIN_CONCEPTS):
            concept = db.records.create(
                label="CONCEPT",
                data={
                    "name": concept_data["name"],
                    "description": concept_data["description"],
                    "domain": "machine_learning",
                    "importance_score": random.uniform(0.5, 1.0),
                },
                transaction=tx,
            )
            concepts[concept_data["name"]] = concept
            
            if (i + 1) % 5 == 0:
                print(f"  Created {i + 1}/{len(DOMAIN_CONCEPTS)} concepts...")
    
    print(f"  Total: {len(concepts)} concepts created")
    return concepts


def create_institutions(db: RushDB) -> list:
    """Create institution nodes representing research organizations."""
    print("\n[3/5] Creating institution nodes...")
    
    institution_names = [
        "MIT Computer Science and AI Lab",
        "Stanford AI Lab",
        "DeepMind Research",
        "Google Brain",
        "Meta AI Research",
        "UC Berkeley AI Research",
        "Carnegie Mellon LTI",
        "ETH Zurich AI Center",
        "Oxford ML Group",
        "Max Planck Institute for Intelligent Systems",
    ]
    
    institutions = []
    with db.transactions.begin() as tx:
        for name in institution_names:
            institution = db.records.create(
                label="INSTITUTION",
                data={
                    "name": name,
                    "country": fake.country(),
                    "founded_year": random.randint(1950, 2015),
                },
                transaction=tx,
            )
            institutions.append(institution)
    
    print(f"  Created {len(institutions)} institutions")
    return institutions


def create_researchers(db: RushDB, institutions: list, concepts: dict) -> list:
    """Create researcher nodes with affiliations and expertise."""
    print("\n[4/5] Creating researcher nodes...")
    researchers = []
    
    # Generate 25 researchers
    num_researchers = 25
    
    with db.transactions.begin() as tx:
        for i in range(num_researchers):
            # Assign 2-4 random concepts as expertise areas
            expertise = random.sample(list(concepts.keys()), k=random.randint(2, 4))
            
            researcher = db.records.create(
                label="RESEARCHER",
                data={
                    "name": fake.name(),
                    "email": fake.email(),
                    "h_index": random.randint(10, 100),
                    "expertise": expertise,
                    "publication_count": random.randint(10, 200),
                },
                transaction=tx,
            )
            researchers.append(researcher)
            
            # Affirmate to random institution
            institution = random.choice(institutions)
            db.records.attach(
                source=researcher,
                target=institution,
                options={"type": "AFFILIATED_WITH", "direction": "out"},
                transaction=tx,
            )
            
            # Link expertise concepts to researcher
            for concept_name in expertise:
                db.records.attach(
                    source=researcher,
                    target=concepts[concept_name],
                    options={"type": "STUDIES", "direction": "out"},
                    transaction=tx,
                )
            
            if (i + 1) % 5 == 0:
                print(f"  Created {i + 1}/{num_researchers} researchers...")
    
    # Create collaboration relationships between researchers
    print("  Creating researcher collaborations...")
    with db.transactions.begin() as tx:
        collaborations = 0
        for researcher in researchers[:15]:  # First 15 researchers collaborate
            potential_collaborators = [r for r in researchers if r.id != researcher.id]
            collaborators = random.sample(potential_collaborators, k=random.randint(2, 4))
            
            for collaborator in collaborators:
                db.records.attach(
                    source=researcher,
                    target=collaborator,
                    options={"type": "COLLABORATES_WITH", "direction": "out"},
                    transaction=tx,
                )
                collaborations += 1
    
    print(f"  Created {len(researchers)} researchers with {collaborations} collaborations")
    return researchers


def create_documents(
    db: RushDB,
    researchers: list,
    concepts: dict
) -> list:
    """Create document nodes with citations and concept associations."""
    print("\n[5/5] Creating document nodes...")
    documents = []
    
    with db.transactions.begin() as tx:
        for i, title in enumerate(DOCUMENT_TITLES):
            # Assign 2-5 random concepts as document topics
            topics = random.sample(list(concepts.keys()), k=random.randint(2, 5))
            
            # Assign 1-3 random authors
            authors = random.sample(researchers, k=random.randint(1, 3))
            
            document = db.records.create(
                label="DOCUMENT",
                data={
                    "title": title,
                    "abstract": fake.paragraph(nb_sentences=5),
                    "year": random.randint(2018, 2024),
                    "citation_count": random.randint(5, 500),
                    "topics": topics,
                    "keywords": topics + random.sample(list(concepts.keys()), k=2),
                },
                transaction=tx,
            )
            documents.append(document)
            
            # Link to topics (concepts)
            for topic_name in topics:
                db.records.attach(
                    source=document,
                    target=concepts[topic_name],
                    options={"type": "DISCUSSES", "direction": "out"},
                    transaction=tx,
                )
            
            # Link to authors
            for author in authors:
                db.records.attach(
                    source=author,
                    target=document,
                    options={"type": "AUTHORED", "direction": "out"},
                    transaction=tx,
                )
            
            if (i + 1) % 5 == 0:
                print(f"  Created {i + 1}/{len(DOCUMENT_TITLES)} documents...")
    
    # Create citation relationships between documents
    print("  Creating document citations...")
    with db.transactions.begin() as tx:
        citations = 0
        for doc in documents:
            # Each document cites 1-4 other documents
            cited = random.sample([d for d in documents if d.id != doc.id], 
                                  k=random.randint(1, 4))
            for cited_doc in cited:
                db.records.attach(
                    source=doc,
                    target=cited_doc,
                    options={"type": "CITES", "direction": "out"},
                    transaction=tx,
                )
                citations += 1
    
    print(f"  Created {len(documents)} documents with {citations} citations")
    return documents


def verify_graph(db: RushDB) -> None:
    """Print graph statistics to verify successful creation."""
    print("\n" + "="*60)
    print("GRAPH CREATION COMPLETE - STATISTICS")
    print("="*60)
    
    labels = db.labels.find({})
    for label in labels:
        print(f"  {label.name}: {label.count} nodes")
    
    # Count relationships
    print("\nRelationships created:")
    rel_counts = {}
    sample_docs = db.records.find({"labels": ["DOCUMENT"], "limit": 3})
    if sample_docs.data:
        # Query relationship types via graph traversal
        for doc in sample_docs.data:
            related_docs = db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "DOCUMENT": {
                        "$relation": {"type": "CITES", "direction": "in"}
                    }
                },
                "limit": 100
            })
    
    print("\nKnowledge graph ready for graph walk algorithms!")


def main():
    """Main seeding function."""
    print("="*60)
    print("KNOWLEDGE GRAPH SEEDING SCRIPT")
    print("="*60)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("RUSHDB_API_KEY")
    
    if not api_key:
        print("\nERROR: RUSHDB_API_KEY not found in environment")
        print("Please create a .env file with your API key:")
        print("  cp .env.example .env")
        print("  # Then edit .env and add your API key")
        return
    
    # Initialize RushDB client
    db = RushDB(api_key)
    print(f"\nConnected to RushDB")
    
    # Execute seeding pipeline
    clear_existing_data(db)
    concepts = create_concepts(db)
    institutions = create_institutions(db)
    researchers = create_researchers(db, institutions, concepts)
    documents = create_documents(db, researchers, concepts)
    verify_graph(db)


if __name__ == "__main__":
    main()
