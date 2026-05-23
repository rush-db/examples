"""
Seed script for the multi-hop question answerer tutorial.

Creates a knowledge graph with:
- 6 Person records with descriptions
- 5 Organization records with descriptions
- 5 Location records with descriptions
- 14 relationship edges (WORKS_AT, LOCATED_IN, KNOWS, VISITED)

All descriptions are embedded for semantic search via RushDB's vector indexing.
"""

import os
import sys
from datetime import datetime, timedelta
from random import choice, randint, seed

from dotenv import load_dotenv
from rushdb import RushDB

# Import embedding utilities
from main import generate_embeddings, create_vector_index

# Load environment
load_dotenv()

# Seed for deterministic data generation
seed(42)

# ============================================================================
# DATA DEFINITIONS
# ============================================================================

PERSONS = [
    {
        "name": "Dr. Sarah Chen",
        "description": "Dr. Sarah Chen is a senior AI researcher at MIT specializing in natural language processing and machine learning.",
        "expertise": "AI, NLP, Machine Learning",
        "collaboration_date": (datetime.now() - timedelta(days=30)).isoformat(),
    },
    {
        "name": "Michael Rodriguez",
        "description": "Michael Rodriguez works at Google as a machine learning engineer focusing on large language models and AI safety research.",
        "expertise": "ML Engineering, LLM, AI Safety",
        "collaboration_date": (datetime.now() - timedelta(days=45)).isoformat(),
    },
    {
        "name": "Emma Wilson",
        "description": "Emma Wilson is a data scientist at Stanford University conducting research on graph neural networks and knowledge graphs.",
        "expertise": "Data Science, Graph Neural Networks",
        "collaboration_date": (datetime.now() - timedelta(days=60)).isoformat(),
    },
    {
        "name": "David Kim",
        "description": "David Kim is a software engineer at Microsoft working on cloud infrastructure and distributed systems.",
        "expertise": "Cloud Computing, Distributed Systems",
        "collaboration_date": (datetime.now() - timedelta(days=90)).isoformat(),
    },
    {
        "name": "Lisa Zhang",
        "description": "Lisa Zhang is a research scientist at DeepMind focusing on reinforcement learning and AI alignment.",
        "expertise": "Reinforcement Learning, AI Alignment",
        "collaboration_date": (datetime.now() - timedelta(days=15)).isoformat(),
    },
    {
        "name": "James O'Brien",
        "description": "James O'Brien is a tech entrepreneur and consultant advising startups on AI implementation strategies.",
        "expertise": "Entrepreneurship, AI Strategy",
        "collaboration_date": (datetime.now() - timedelta(days=120)).isoformat(),
    },
]

ORGANIZATIONS = [
    {
        "name": "MIT",
        "description": "Massachusetts Institute of Technology is a world-renowned research university and technology hub.",
        "industry": "Education/Research",
        "founded": "1861",
    },
    {
        "name": "Google",
        "description": "Google is a global technology company leading in AI research, search engines, and cloud computing.",
        "industry": "Technology",
        "founded": "1998",
    },
    {
        "name": "Stanford University",
        "description": "Stanford University is a leading research institution known for innovation in AI and computer science.",
        "industry": "Education/Research",
        "founded": "1885",
    },
    {
        "name": "Microsoft",
        "description": "Microsoft Corporation is a technology corporation developing software, cloud services, and AI solutions.",
        "industry": "Technology",
        "founded": "1975",
    },
    {
        "name": "DeepMind",
        "description": "DeepMind is an AI research company pushing the boundaries of artificial intelligence through deep learning.",
        "industry": "AI Research",
        "founded": "2010",
    },
]

LOCATIONS = [
    {
        "city": "Cambridge, MA",
        "description": "Cambridge, Massachusetts is a hub for higher education and technology research, home to MIT and Harvard.",
        "population": "118,000",
    },
    {
        "city": "Mountain View, CA",
        "description": "Mountain View, California is the headquarters of Google and a center of Silicon Valley innovation.",
        "population": "82,000",
    },
    {
        "city": "Stanford, CA",
        "description": "Stanford, California is home to Stanford University and Silicon Valley's tech ecosystem.",
        "population": "35,000",
    },
    {
        "city": "Seattle, WA",
        "description": "Seattle, Washington is a major tech hub with strong presence from Microsoft and Amazon.",
        "population": "749,000",
    },
    {
        "city": "London, UK",
        "description": "London, UK is a leading financial and tech center with a growing AI research community.",
        "population": "9,000,000",
    },
]

# Relationship mappings: (person_index, relationship_type, target_label, target_index)
RELATIONSHIPS = [
    # WORKS_AT relationships
    (0, "WORKS_AT", "ORGANIZATION", 0),  # Dr. Sarah Chen -> MIT
    (1, "WORKS_AT", "ORGANIZATION", 1),  # Michael Rodriguez -> Google
    (2, "WORKS_AT", "ORGANIZATION", 2),  # Emma Wilson -> Stanford
    (3, "WORKS_AT", "ORGANIZATION", 3),  # David Kim -> Microsoft
    (4, "WORKS_AT", "ORGANIZATION", 4),  # Lisa Zhang -> DeepMind
    (5, "WORKS_AT", "ORGANIZATION", 1),  # James O'Brien -> Google (consultant)
    # LOCATED_IN relationships
    (0, "LOCATED_IN", "LOCATION", 0),  # Dr. Sarah Chen -> Cambridge
    (1, "LOCATED_IN", "LOCATION", 1),  # Michael Rodriguez -> Mountain View
    (2, "LOCATED_IN", "LOCATION", 2),  # Emma Wilson -> Stanford
    (3, "LOCATED_IN", "LOCATION", 3),  # David Kim -> Seattle
    (4, "LOCATED_IN", "LOCATION", 4),  # Lisa Zhang -> London
    # ORGANIZATION located in
    (0, "LOCATED_IN", "LOCATION", 0),  # MIT -> Cambridge
    (1, "LOCATED_IN", "LOCATION", 1),  # Google -> Mountain View
    (2, "LOCATED_IN", "LOCATION", 2),  # Stanford -> Stanford
    (3, "LOCATED_IN", "LOCATION", 3),  # Microsoft -> Seattle
    (4, "LOCATED_IN", "LOCATION", 4),  # DeepMind -> London
    # KNOWS relationships (person to person)
    (0, "KNOWS", "PERSON", 1),  # Sarah knows Michael
    (0, "KNOWS", "PERSON", 2),  # Sarah knows Emma
    (1, "KNOWS", "PERSON", 4),  # Michael knows Lisa
    (2, "KNOWS", "PERSON", 0),  # Emma knows Sarah
    (4, "KNOWS", "PERSON", 1),  # Lisa knows Michael
]


def clear_existing_data(db):
    """Remove all existing records with our labels."""
    print("Clearing existing data...")
    labels = ["PERSON", "ORGANIZATION", "LOCATION"]
    for label in labels:
        result = db.records.find({"labels": [label], "limit": 1})
        if result.data:
            db.records.delete({"labels": [label], "where": {}})
    print("  ✓ Cleared existing records")

    # Delete vector indexes
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        db.ai.indexes.delete(idx['__id'])
    print("  ✓ Cleared vector indexes")


def seed_knowledge_graph(db):
    """Create all records and relationships."""
    print("\nSeeding knowledge graph with 22 records and 18 relationships...")

    # Generate embeddings for all descriptions
    all_descriptions = []
    for person in PERSONS:
        all_descriptions.append(person["description"])
    for org in ORGANIZATIONS:
        all_descriptions.append(org["description"])
    for loc in LOCATIONS:
        all_descriptions.append(loc["description"])

    embeddings = generate_embeddings(all_descriptions)

    # Create Person records
    print("\n✓ Seeding 6 Person records")
    person_records = []
    for i, person in enumerate(PERSONS):
        vec = embeddings[i]
        record = db.records.create(
            label="PERSON",
            data=person,
            vectors=[{"propertyName": "description", "vector": vec.tolist()}]
        )
        person_records.append(record)
        print(f"  - {person['name']}")

    # Create Organization records
    print("\n✓ Seeding 5 Organization records")
    org_records = []
    for i, org in enumerate(ORGANIZATIONS):
        vec = embeddings[len(PERSONS) + i]
        record = db.records.create(
            label="ORGANIZATION",
            data=org,
            vectors=[{"propertyName": "description", "vector": vec.tolist()}]
        )
        org_records.append(record)
        print(f"  - {org['name']}")

    # Create Location records
    print("\n✓ Seeding 5 Location records")
    loc_records = []
    for i, loc in enumerate(LOCATIONS):
        vec = embeddings[len(PERSONS) + len(ORGANIZATIONS) + i]
        record = db.records.create(
            label="LOCATION",
            data=loc,
            vectors=[{"propertyName": "description", "vector": vec.tolist()}]
        )
        loc_records.append(record)
        print(f"  - {loc['city']}")

    # Create relationships
    print("\n✓ Creating relationship edges...")
    rel_count = 0
    for source_idx, rel_type, target_label, target_idx in RELATIONSHIPS:
        if target_label == "PERSON":
            source = person_records[source_idx]
            target = person_records[target_idx]
        elif target_label == "ORGANIZATION":
            source = person_records[source_idx]
            target = org_records[target_idx]
        else:  # LOCATION
            # Check if source is a person or organization
            if source_idx < len(PERSONS):
                source = person_records[source_idx]
            else:
                source = org_records[source_idx - len(PERSONS)]
            target = loc_records[target_idx]

        db.records.attach(
            source=source,
            target=target,
            options={"type": rel_type}
        )
        rel_count += 1

    print(f"  - Created {rel_count} relationship edges")

    return {
        "persons": person_records,
        "organizations": org_records,
        "locations": loc_records,
    }


def create_indexes(db):
    """Create vector indexes for semantic search."""
    print("\n✓ Indexing records for vector search...")

    # Create index for PERSON description
    index_person = db.ai.indexes.create({
        "label": "PERSON",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,
    })

    # Create index for ORGANIZATION description
    index_org = db.ai.indexes.create({
        "label": "ORGANIZATION",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,
    })

    # Create index for LOCATION description
    index_loc = db.ai.indexes.create({
        "label": "LOCATION",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,
    })

    print("  - Created indexes for PERSON, ORGANIZATION, LOCATION")
    print(f"\nKnowledge graph seeded successfully!\n")


def main():
    """Main seeding function."""
    api_key = os.getenv("RUSHD_API_KEY")
    if not api_key:
        print("ERROR: RUSHD_API_KEY environment variable not set.")
        print("Copy .env.example to .env and add your API key.")
        sys.exit(1)

    db = RushDB(api_key)

    print("=" * 60)
    print("RushDB Multi-Hop Q&A Knowledge Graph Seeder")
    print("=" * 60)

    # Check for existing data
    existing = db.records.find({"labels": ["PERSON"], "limit": 1})
    if existing.data:
        response = input("\nExisting data found. Clear and reseed? (y/N): ")
        if response.lower() == 'y':
            clear_existing_data(db)
        else:
            print("Skipping seed - existing data preserved.")
            return

    # Seed the data
    seed_knowledge_graph(db)

    # Create vector indexes
    create_indexes(db)

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("  - 6 Person records (AI researchers, engineers)")
    print("  - 5 Organization records (MIT, Google, etc.)")
    print("  - 5 Location records (Cambridge, Mountain View, etc.)")
    print("  - 18 relationship edges")
    print("=" * 60)


if __name__ == "__main__":
    main()
