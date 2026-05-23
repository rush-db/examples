"""
Mock data generation script for the belief revision tutorial.

Creates a knowledge base with facts about tech companies that will later
be contradicted to demonstrate belief revision patterns.
"""

import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Company data that will be stored as beliefs
INITIAL_BELIEFS = {
    "TechCorp": {
        "founding_date": "1999-03-15",
        "ceo": "John Smith",
        "headquarters": "San Francisco",
        "employees": 1500,
        "status": "active",
    },
    "DataInc": {
        "founding_date": "2010-07-22",
        "ceo": "Michael Chen",
        "headquarters": "New York",
        "employees": 800,
        "status": "active",
    },
    "CloudStartup": {
        "founding_date": "2018-01-10",
        "ceo": "Sarah Johnson",
        "headquarters": "Seattle",
        "employees": 50,
        "status": "active",
    },
    "LegacySystems": {
        "founding_date": "1985-11-05",
        "ceo": "Robert Williams",
        "headquarters": "Chicago",
        "employees": 300,
        "status": "active",
    },
}

# Beliefs that will later be revealed as incorrect
# These match the "contradicted" data in the main tutorial
UPCOMING_CONTRADICTIONS = {
    "TechCorp": {
        "founding_date": "2000-01-01",  # Old: 1999-03-15
        "ceo": "Jane Doe",              # Old: John Smith
    },
    "DataInc": {
        "headquarters": "Boston",      # Old: New York
    },
}


def check_already_seeded(db: RushDB) -> bool:
    """Check if data has already been seeded."""
    result = db.records.find({"labels": ["ENTITY"], "limit": 1})
    return len(result) > 0


def create_belief_record(
    db: RushDB,
    entity_name: str,
    property_name: str,
    value: str,
    source: str,
    confidence: float,
    timestamp: str,
) -> dict:
    """Create a single belief record."""
    belief = db.records.create(
        label="BELIEF",
        data={
            "property_name": property_name,
            "value": value,
            "source": source,
            "confidence": confidence,
            "retracted": False,
            "created_at": timestamp,
            "revised_at": None,
            "revision_note": None,
        }
    )

    # Attach belief to its entity
    entity = db.records.find({"labels": ["ENTITY"], "where": {"name": entity_name}})
    if entity:
        db.records.attach(
            source=belief,
            target=entity[0],
            options={"type": "BELIEF_ABOUT", "direction": "out"}
        )

    return belief


def seed_knowledge_base(db: RushDB) -> dict:
    """
    Seed the knowledge base with initial beliefs.
    Returns a dict mapping entity names to their belief IDs.
    """
    print("Seeding knowledge base...")

    entity_ids = {}
    belief_ids = {"TechCorp": [], "DataInc": [], "CloudStartup": [], "LegacySystems": []}

    # Create entity records
    for entity_name in INITIAL_BELIEFS:
        print(f"  Creating entity: {entity_name}")
        entity = db.records.create(
            label="ENTITY",
            data={
                "name": entity_name,
                "type": "company",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        entity_ids[entity_name] = entity.id

    # Create belief records for each property
    sources = ["annual_report", "press_release", "wiki", "direct_submission"]
    base_time = datetime.utcnow() - timedelta(days=365)

    for entity_name, properties in INITIAL_BELIEFS.items():
        for i, (prop_name, value) in enumerate(properties.items()):
            timestamp = (base_time + timedelta(days=i * 30)).isoformat()
            confidence = random.uniform(0.7, 1.0)
            source = random.choice(sources)

            belief = create_belief_record(
                db=db,
                entity_name=entity_name,
                property_name=prop_name,
                value=str(value),
                source=source,
                confidence=confidence,
                timestamp=timestamp,
            )
            belief_ids[entity_name].append(belief.id)

    print(f"  Created {len(entity_ids)} entities and {sum(len(v) for v in belief_ids.values())} beliefs")
    return {"entities": entity_ids, "beliefs": belief_ids}


def main():
    """Run the seeding process."""
    api_key = __import__("os").getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY environment variable not set")
        print("Copy .env.example to .env and add your API key")
        return

    db = RushDB(api_key)

    # Check if already seeded
    if check_already_seeded(db):
        print("Knowledge base already contains data. Skipping seed.")
        print("Delete existing records to reseed.")
        return

    # Seed the data
    result = seed_knowledge_base(db)
    print("\nSeeding complete!")
    print(f"  Entity IDs: {result['entities']}")


if __name__ == "__main__":
    main()
