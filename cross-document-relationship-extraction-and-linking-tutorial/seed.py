"""
Seed script for cross-document entity linking tutorial.

Generates mock academic paper data with authors, institutions, and citation relationships.
Safe to run multiple times (idempotent).
"""

import os
import json
import random
from datetime import datetime
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

# Configuration
API_KEY = os.getenv("RUSHDB_API_KEY")
or raise ValueError("RUSHDB_API_KEY not set. Copy .env.example to .env and fill in your key.")

# Mock academic data
PAPERS = [
    {
        "id": "paper_001",
        "title": "Neural Approaches to Entity Resolution in Knowledge Graphs",
        "abstract": "We present a novel neural architecture for resolving entity mentions across distributed knowledge graphs. Our approach combines graph attention mechanisms with contextual embeddings to achieve state-of-the-art performance.",
        "year": 2024,
        "authors": [
            {"name": "Dr. John Chen", "position": 1, "institution": "MIT"},
            {"name": "Dr. Sarah Kim", "position": 2, "institution": "MIT"},
            {"name": "Prof. Michael Torres", "position": 3, "institution": "Stanford"}
        ],
        "keywords": ["entity resolution", "knowledge graphs", "neural networks"]
    },
    {
        "id": "paper_002",
        "title": "Scalable Citation Graph Analysis for Research Intelligence",
        "abstract": "This paper introduces a scalable framework for analyzing citation networks to support research intelligence applications. We demonstrate how graph traversal patterns correlate with research impact.",
        "year": 2023,
        "authors": [
            {"name": "Prof. Michael Torres", "position": 1, "institution": "Stanford"},
            {"name": "Dr. Lisa Patel", "position": 2, "institution": "Oxford"}
        ],
        "keywords": ["citation analysis", "research intelligence", "graph analysis"]
    },
    {
        "id": "paper_003",
        "title": "Coreference Resolution Using Transformer-based Models",
        "abstract": "We propose a transformer-based approach to coreference resolution that leverages contextual embeddings from pre-trained language models. Our method achieves significant improvements on standard benchmarks.",
        "year": 2024,
        "authors": [
            {"name": "Dr. Lisa Patel", "position": 1, "institution": "Oxford"},
            {"name": "Dr. John Chen", "position": 2, "institution": "MIT"},
            {"name": "Dr. Emma Wilson", "position": 3, "institution": "Cambridge"}
        ],
        "keywords": ["coreference", "transformers", "NLP"]
    },
    {
        "id": "paper_004",
        "title": "Vector Similarity Search in Hybrid Database Systems",
        "abstract": "We investigate efficient methods for combining vector similarity search with traditional relational queries. Our hybrid indexing approach achieves sub-millisecond query times.",
        "year": 2023,
        "authors": [
            {"name": "Dr. Emma Wilson", "position": 1, "institution": "Cambridge"},
            {"name": "Dr. Sarah Kim", "position": 2, "institution": "MIT"}
        ],
        "keywords": ["vector search", "hybrid databases", "performance"]
    },
    {
        "id": "paper_005",
        "title": "Cross-Document Entity Linking via Semantic Similarity",
        "abstract": "We present a comprehensive study of cross-document entity linking, comparing graph-based and embedding-based approaches. Our analysis reveals that hybrid methods outperform both paradigms individually.",
        "year": 2024,
        "authors": [
            {"name": "Dr. Sarah Kim", "position": 1, "institution": "MIT"},
            {"name": "Dr. John Chen", "position": 2, "institution": "MIT"}
        ],
        "keywords": ["entity linking", "semantic similarity", "cross-document"]
    }
]

# Citation graph (who cites whom)
CITATIONS = [
    {"citing": "paper_001", "cited": "paper_003"},  # Chen et al. cite Patel & Chen
    {"citing": "paper_001", "cited": "paper_004"},  # Chen et al. cite Wilson & Kim
    {"citing": "paper_002", "cited": "paper_004"},  # Torres cites Wilson & Kim
    {"citing": "paper_003", "cited": "paper_005"},  # Patel cites Kim & Chen
    {"citing": "paper_004", "cited": "paper_002"},  # Wilson cites Torres
    {"citing": "paper_005", "cited": "paper_001"},  # Kim cites Chen et al.
    {"citing": "paper_005", "cited": "paper_002"},  # Kim cites Torres
]


def normalize_name(name: str) -> str:
    """Normalize a name for comparison (lowercase, remove titles)."""
    normalized = name.lower()
    titles = ["dr.", "dr", "prof.", "prof", "mr.", "mr", "ms.", "ms"]
    for title in titles:
        normalized = normalized.replace(title, "").strip()
    return " ".join(normalized.split())


def get_last_name(name: str) -> str:
    """Extract last name from full name."""
    parts = normalize_name(name).split()
    return parts[-1] if parts else name



def seed_database():
    """Seed the database with academic paper data."""
    print("\n=== Seeding Academic Paper Data ===\n")
    
    # Initialize RushDB client
    db = RushDB(API_KEY)
    
    # Check for existing data to make this idempotent
    existing_papers = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if existing_papers:
        print("✓ Data already seeded. Skipping...")
        print(f"  Found {len(existing_papers)} existing documents.")
        return
    
    print("[1/4] Creating institutions...")
    institutions = {}
    for paper in PAPERS:
        for author in paper["authors"]:
            inst = author["institution"]
            if inst not in institutions:
                institutions[inst] = db.records.create(
                    label="INSTITUTION",
                    data={
                        "name": inst,
                        "country": get_country_for_institution(inst)
                    }
                )
                print(f"  ✓ Created institution: {inst}")
    
    print("\n[2/4] Creating person entities...")
    persons = {}
    for paper in PAPERS:
        for author in paper["authors"]:
            name = author["name"]
            if name not in persons:
                inst = author["institution"]
                persons[name] = db.records.create(
                    label="PERSON",
                    data={
                        "name": name,
                        "canonicalName": get_last_name(name),
                        "institution": inst,
                        "embeddingContext": f"{name} from {inst}, research in machine learning and knowledge graphs"
                    }
                )
                print(f"  ✓ Created person: {name} ({inst})")
                
                # Link person to institution
                db.records.attach(
                    source=persons[name],
                    target=institutions[inst],
                    options={"type": "AFFILIATED_WITH", "direction": "out"}
                )
    
    print("\n[3/4] Creating documents and author relationships...")
    documents = {}
    for i, paper in enumerate(PAPERS):
        doc = db.records.create(
            label="DOCUMENT",
            data={
                "title": paper["title"],
                "abstract": paper["abstract"],
                "year": paper["year"],
                "keywords": paper["keywords"],
                "paperId": paper["id"]
            }
        )
        documents[paper["id"]] = doc
        print(f"  ✓ Created document: {paper['title'][:50]}...")
        
        # Link authors in order
        for author in paper["authors"]:
            person = persons[author["name"]]
            db.records.attach(
                source=doc,
                target=person,
                options={"type": "AUTHORED_BY", "direction": "out"}
            )
            
            # Track position
            db.records.set(
                target=doc,
                label="DOCUMENT",
                data={
                    "title": paper["title"],
                    "abstract": paper["abstract"],
                    "year": paper["year"],
                    "keywords": paper["keywords"],
                    "paperId": paper["id"],
                    f"author_{author['position']}_id": person.id
                }
            )
        
        if (i + 1) % 100 == 0:
            print(f"    Progress: {i + 1}/{len(PAPERS)} documents")
    
    print("\n[4/4] Creating citation relationships...")
    for citation in CITATIONS:
        citing_doc = documents[citation["citing"]]
        cited_doc = documents[citation["cited"]]
        db.records.attach(
            source=citing_doc,
            target=cited_doc,
            options={"type": "CITES", "direction": "out"}
        )
        print(f"  ✓ {citation['citing']} cites {citation['cited']}")
    
    print("\n=== Seeding Complete ===")
    print(f"  • {len(institutions)} institutions")
    print(f"  • {len(persons)} persons")
    print(f"  • {len(documents)} documents")
    print(f"  • {len(CITATIONS)} citations")


def get_country_for_institution(institution: str) -> str:
    """Map institution names to countries."""
    mapping = {
        "MIT": "USA",
        "Stanford": "USA",
        "Oxford": "UK",
        "Cambridge": "UK"
    }
    return mapping.get(institution, "Unknown")


if __name__ == "__main__":
    seed_database()
