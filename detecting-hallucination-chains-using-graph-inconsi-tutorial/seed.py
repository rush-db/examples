"""
Seed script for hallucination detection tutorial.
Creates a graph of claims with intentional contradictions to demonstrate detection.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)

# Sample entities with their factual information
ENTITIES_DATA = {
    "Apple Inc.": {
        "founded_year": 1976,
        "headquarters": "Cupertino, California",
        "ceo": "Tim Cook",
        "founded_by": ["Steve Jobs", "Steve Wozniak", "Ronald Wayne"]
    },
    "Tesla": {
        "founded_year": 2003,
        "headquarters": "Austin, Texas",
        "ceo": "Elon Musk",
        "founded_by": ["Martin Eberhard", "Marc Tarpenning"]
    },
    "Python Programming Language": {
        "created_year": 1991,
        "creator": "Guido van Rossum",
        "paradigm": ["interpreted", "dynamic", "object-oriented"]
    },
    "Moon Landing": {
        "year": 1969,
        "agency": "NASA",
        "crew": ["Armstrong", "Aldrin", "Collins"]
    }
}

# Claims with some correct and some incorrect (hallucinated) variations
CLAIMS_DATA = [
    # Apple Inc. claims - mix of fact and fiction
    {"entity": "Apple Inc.", "claim": "Apple Inc. was founded in 1976 by Steve Jobs and Steve Wozniak.", "factual": True},
    {"entity": "Apple Inc.", "claim": "Apple was founded in 1984 as a response to the IBM PC.", "factual": False},
    {"entity": "Apple Inc.", "claim": "Tim Cook became CEO of Apple in 2011 after Steve Jobs stepped down.", "factual": True},
    {"entity": "Apple Inc.", "claim": "Apple is headquartered in Seattle, Washington.", "factual": False},
    {"entity": "Apple Inc.", "claim": "The first Apple computer was called Apple I and released in 1976.", "factual": True},
    
    # Tesla claims - mostly factual with one hallucination
    {"entity": "Tesla", "claim": "Tesla was founded in 2003 by Martin Eberhard and Marc Tarpenning.", "factual": True},
    {"entity": "Tesla", "claim": "Elon Musk joined Tesla in 2008 as chairman and major investor.", "factual": True},
    {"entity": "Tesla", "claim": "Tesla's first car was the Roadster, released in 2008.", "factual": True},
    
    # Python claims - one fiction
    {"entity": "Python Programming Language", "claim": "Python was created by Guido van Rossum and first released in 1991.", "factual": True},
    {"entity": "Python Programming Language", "claim": "Python is named after the British comedy troupe Monty Python.", "factual": True},
    {"entity": "Python Programming Language", "claim": "Python was developed by Microsoft in the 1980s.", "factual": False},
    
    # Moon landing claims - mix
    {"entity": "Moon Landing", "claim": "Apollo 11 landed on the Moon on July 20, 1969.", "factual": True},
    {"entity": "Moon Landing", "claim": "Neil Armstrong was the first person to walk on the Moon.", "factual": True},
    {"entity": "Moon Landing", "claim": "The Moon landing was faked and filmed in a studio.", "factual": False},
    {"entity": "Moon Landing", "claim": "Apollo 11 returned safely to Earth on July 24, 1969.", "factual": True}
]

# Contradiction pairs - claims that logically oppose each other
CONTRADICTIONS = [
    # Apple founding year contradictions
    (0, 1),  # "founded 1976" vs "founded 1984"
    (3, None),  # "Seattle headquarters" contradicts (no specific counterpart in seeded claims)
    
    # Python origin contradictions
    (8, 11),  # "Guido van Rossum 1991" vs "Microsoft 1980s"
]

def seed_database():
    """Seed the database with claims and entities."""
    
    # Check if already seeded
    existing = db.records.find({"labels": ["ENTITY"], "limit": 1})
    if existing:
        print("Database already seeded. Skipping...")
        return
    
    print("Seeding database with claims and entities...")
    
    # First, create all entities
    entity_records = {}
    for entity_name in ENTITIES_DATA.keys():
        entity = db.records.create(
            label="ENTITY",
            data={
                "name": entity_name,
                "type": "organization" if entity_name in ["Apple Inc.", "Tesla"] else "concept"
            }
        )
        entity_records[entity_name] = entity
        print(f"  Created entity: {entity_name}")
    
    # Create all claims
    claim_records = []
    for i, claim_data in enumerate(CLAIMS_DATA):
        claim = db.records.create(
            label="CLAIM",
            data={
                "text": claim_data["claim"],
                "entity": claim_data["entity"],
                "factual": claim_data["factual"],
                "source": "tutorial_seed"
            }
        )
        claim_records.append(claim)
        
        # Attach claim to its entity
        entity = entity_records[claim_data["entity"]]
        db.records.attach(
            source=claim,
            target=entity,
            options={"type": "MENTIONS", "direction": "out"}
        )
        
        print(f"  Created claim {i+1}/{len(CLAIMS_DATA)}: {claim_data['claim'][:50]}...")
    
    # Now create CONTRADICTS and SUPPORTS relationships
    print("\nCreating semantic relationships...")
    
    # Create explicit contradictions based on entity conflicts
    contradiction_pairs = [
        (0, 1),  # Apple 1976 vs 1984
        (8, 11),  # Python 1991 vs Microsoft
    ]
    
    for idx_a, idx_b in contradiction_pairs:
        if idx_b is not None and idx_b < len(claim_records):
            db.records.attach(
                source=claim_records[idx_a],
                target=claim_records[idx_b],
                options={"type": "CONTRADICTS", "direction": "undirected"}
            )
            print(f"  CONTRADICTS: Claim {idx_a+1} <-> Claim {idx_b+1}")
    
    # Create support relationships (factual claims that agree)
    support_pairs = [
        (0, 4),   # Apple founding claims support each other
        (6, 7),   # Tesla timeline claims support each other
        (8, 9),   # Python origin claims support each other
        (12, 13), # Moon landing facts support each other
    ]
    
    for idx_a, idx_b in support_pairs:
        db.records.attach(
            source=claim_records[idx_a],
            target=claim_records[idx_b],
            options={"type": "SUPPORTS", "direction": "undirected"}
        )
        print(f"  SUPPORTS: Claim {idx_a+1} <-> Claim {idx_b+1}")
    
    print("\nSeeding complete!\n")

def show_stats():
    """Display current database statistics."""
    entities = db.records.find({"labels": ["ENTITY"]})
    claims = db.records.find({"labels": ["CLAIM"]})
    
    print("=== Database Statistics ===")
    print(f"Entities: {len(entities)}")
    print(f"Claims: {len(claims)}")
    
    for entity in entities:
        entity_claims = db.records.find({
            "labels": ["CLAIM"],
            "where": {"ENTITY": {"$id": entity.id}}
        })
        print(f"  - {entity['name']}: {len(entity_claims)} claims")

if __name__ == "__main__":
    seed_database()
    show_stats()
