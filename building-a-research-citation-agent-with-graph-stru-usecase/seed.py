#!/usr/bin/env python3
"""
Seed script: Load research papers and their citation relationships into RushDB.

This script:
1. Creates a vector index for paper abstracts
2. Loads papers from data/papers.json
3. Embeds abstracts using sentence-transformers
4. Creates citation edges between papers

Run this once before main.py to populate the database.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
token = os.getenv("RUSHDB_TOKEN")
or url = os.getenv("RUSHDB_URL")

if not token:
    raise ValueError(
        "RUSHDB_TOKEN not found. Please create a .env file with your token.\n"
        "Get your token at: https://app.rushdb.com/settings/api-tokens"
    )

db = RushDB(token, url=url) if url else RushDB(token)

# Load the embedding model
print("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")
embedding_dim = 384  # Output dimension for all-MiniLM-L6-v2


def check_already_seeded():
    """Check if papers have already been loaded by looking for existing PAPER records."""
    result = db.records.find({"labels": ["PAPER"], "limit": 1})
    return len(result.data) > 0


def create_vector_index():
    """Create a vector index for paper abstracts if it doesn't exist."""
    # Check for existing indexes
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx.get("label") == "PAPER" and idx.get("propertyName") == "abstract":
            print(f"Vector index already exists: PAPER.abstract")
            return idx.get("__id")

    # Create new index
    print("Creating vector index for PAPER.abstract...")
    response = db.ai.indexes.create({
        "label": "PAPER",
        "propertyName": "abstract",
        "sourceType": "external",
        "dimensions": embedding_dim,
        "similarityFunction": "cosine"
    })
    index_id = response.data.get("__id") or response.data.get("id")
    print(f"Created vector index: {index_id}")
    return index_id


def load_papers():
    """Load paper data from JSON file."""
    data_path = Path(__file__).parent / "data" / "papers.json"
    with open(data_path, "r") as f:
        return json.load(f)


def embed_texts(texts):
    """Generate embeddings for a list of texts."""
    return model.encode(texts, show_progress_bar=True)


def seed_database():
    """Main seeding function."""
    # Check if already seeded
    if check_already_seeded():
        print("Database already contains PAPER records. Skipping seed.")
        print("To re-seed, delete existing PAPER records first.")
        return

    print("\n" + "=" * 60)
    print("SEEDING RESEARCH CITATION GRAPH")
    print("=" * 60 + "\n")

    # Create vector index
    index_id = create_vector_index()

    # Load papers
    papers_data = load_papers()
    print(f"\nLoading {len(papers_data)} papers from data/papers.json...")

    # Separate paper metadata from citation relationships
    paper_records = []
    citation_map = {}  # paper_id -> list of cited paper_ids

    for paper in papers_data:
        paper_id = paper["id"]
        citation_map[paper_id] = paper.get("citations", [])

        record = {
            "paperId": paper_id,
            "title": paper["title"],
            "authors": paper["authors"],
            "year": paper["year"],
            "abstract": paper["abstract"]
        }
        paper_records.append(record)

    # Generate embeddings for all abstracts
    abstracts = [p["abstract"] for p in paper_records]
    print("Generating embeddings for paper abstracts...")
    embeddings = embed_texts(abstracts)

    # Create papers with vectors using upsert (idempotent by paperId)
    print("\nCreating paper records with vectors...")
    created_papers = {}

    for i, record in enumerate(paper_records):
        paper = db.records.upsert(
            label="PAPER",
            data=record,
            options={"mergeBy": ["paperId"]},
            vectors=[{"propertyName": "abstract", "vector": embeddings[i].tolist()}]
        )
        created_papers[record["paperId"]] = paper

        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(paper_records)} papers...")

    print(f"Created {len(created_papers)} paper records")

    # Build citation graph - create CITES relationships
    print("\nBuilding citation graph...")
    edges_created = 0

    for paper_id, cited_ids in citation_map.items():
        if paper_id not in created_papers:
            continue

        citing_paper = created_papers[paper_id]

        for cited_id in cited_ids:
            if cited_id not in created_papers:
                continue

            cited_paper = created_papers[cited_id]

            # Create CITES edge: citing_paper --CITES--> cited_paper
            db.records.attach(
                source=citing_paper,
                target=cited_paper,
                options={"type": "CITES", "direction": "out"}
            )
            edges_created += 1

    print(f"Created {edges_created} citation edges")

    # Verify the index
    print("\nVerifying vector index...")
    try:
        stats = db.ai.indexes.stats(index_id)
        print(f"Index stats: {stats.data.get('indexedRecords', 'N/A')} records indexed")
    except Exception as e:
        print(f"Index stats check failed: {e}")

    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print("\nRun 'python main.py' to explore the citation graph.")


if __name__ == "__main__":
    seed_database()
