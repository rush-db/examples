"""
Seed script: Creates mock facts, sources, and relationships
for the confidence scoring tutorial.

This script is idempotent — safe to run multiple times.
"""
import os
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)

# Sample facts with varying confidence levels
FACTS = [
    {
        "statement": "The Earth orbits the Sun",
        "confidence": 0.9999,
        "category": "astronomy",
        "year": 1543
    },
    {
        "statement": "Water boils at 100°C at sea level",
        "confidence": 0.998,
        "category": "physics",
        "year": 1766
    },
    {
        "statement": "DNA carries genetic information",
        "confidence": 0.9995,
        "category": "biology",
        "year": 1953
    },
    {
        "statement": "Humans share a common ancestor with chimpanzees",
        "confidence": 0.97,
        "category": "evolution",
        "year": 1871
    },
    {
        "statement": "The universe is approximately 13.8 billion years old",
        "confidence": 0.94,
        "category": "cosmology",
        "year": 2013
    },
    {
        "statement": "Quantum entanglement allows faster-than-light communication",
        "confidence": 0.15,
        "category": "physics",
        "year": 1935
    },
    {
        "statement": "The Titanic sank on its maiden voyage in 1912",
        "confidence": 0.999,
        "category": "history",
        "year": 1912
    },
    {
        "statement": "Vaccines cause autism",
        "confidence": 0.001,
        "category": "health",
        "year": 1998
    },
    {
        "statement": "The Great Wall of China is visible from space",
        "confidence": 0.05,
        "category": "geography",
        "year": 1750
    },
    {
        "statement": "Penicillin was discovered in 1928",
        "confidence": 0.99,
        "category": "medicine",
        "year": 1928
    }
]

# Sample sources with reliability ratings (0.0 to 1.0)
SOURCES = [
    {"name": "Nature Journal", "reliability": 0.95, "type": "peer_reviewed"},
    {"name": "Science Magazine", "reliability": 0.93, "type": "peer_reviewed"},
    {"name": "Wikipedia", "reliability": 0.65, "type": "encyclopedia"},
    {"name": "New York Times", "reliability": 0.80, "type": "news"},
    {"name": "The Lancet", "reliability": 0.97, "type": "peer_reviewed"},
    {"name": "Twitter/X", "reliability": 0.30, "type": "social_media"},
    {"name": "Britannica", "reliability": 0.78, "type": "encyclopedia"},
    {"name": "Reuters", "reliability": 0.85, "type": "news"},
    {"name": "NASA Official", "reliability": 0.92, "type": "government"},
    {"name": "Anonymous Blog", "reliability": 0.20, "type": "blog"}
]


def check_already_seeded():
    """Check if data has already been seeded by looking for existing records."""
    existing_facts = db.records.find({"labels": ["FACT"], "limit": 1})
    return len(existing_facts.data) > 0


def clear_existing_data():
    """Remove existing tutorial data for clean reseed."""
    print("Clearing existing data...")
    db.records.delete_many({"labels": ["FACT"]})
    db.records.delete_many({"labels": ["SOURCE"]})
    print("Cleared.")


def seed_sources():
    """Create source records."""
    print("\nSeeding sources...")
    created_sources = []
    for i, source_data in enumerate(SOURCES):
        source = db.records.create(
            label="SOURCE",
            data=source_data
        )
        created_sources.append(source)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(SOURCES)} sources")
    print(f"Created {len(created_sources)} sources")
    return created_sources


def seed_facts():
    """Create fact records."""
    print("\nSeeding facts...")
    created_facts = []
    for i, fact_data in enumerate(FACTS):
        fact = db.records.create(
            label="FACT",
            data=fact_data
        )
        created_facts.append(fact)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(FACTS)} facts")
    print(f"Created {len(created_facts)} facts")
    return created_facts


def link_facts_to_sources(facts, sources):
    """Create relationships between facts and supporting sources."""
    print("\nLinking facts to sources...")
    
    # Link rules: higher confidence facts get more reliable sources
    # Low confidence facts might get unreliable sources
    links = [
        (0, [0, 1, 8]),    # Fact 0: Earth orbits Sun -> Nature, Science, NASA
        (1, [0, 1]),       # Fact 1: Water boils -> Nature, Science
        (2, [0, 1, 4]),    # Fact 2: DNA -> Nature, Science, Lancet
        (3, [0, 1, 6]),    # Fact 3: Chimp ancestor -> Nature, Science, Britannica
        (4, [0, 1, 8]),    # Fact 4: Universe age -> Nature, Science, NASA
        (5, [5, 9]),       # Fact 5: Quantum comm -> NYT, Anonymous Blog
        (6, [2, 7, 6]),    # Fact 6: Titanic -> Wikipedia, Reuters, Britannica
        (7, [5, 9]),       # Fact 7: Vaccines cause autism -> Twitter, Anonymous
        (8, [5]),          # Fact 8: Great Wall visible -> Twitter/X
        (9, [0, 1, 4]),    # Fact 9: Penicillin -> Nature, Science, Lancet
    ]
    
    for fact_idx, source_indices in links:
        for src_idx in source_indices:
            db.records.attach(
                source=facts[fact_idx],
                target=sources[src_idx],
                options={"type": "SUPPORTED_BY"}
            )
    print(f"Created {sum(len(l[1]) for l in links)} fact-source relationships")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RushDB Confidence Scoring Tutorial - Data Seeder")
    print("=" * 60)
    
    if check_already_seeded():
        print("\nData appears to already be seeded.")
        response = input("Clear and reseed? (y/N): ")
        if response.lower() == 'y':
            clear_existing_data()
        else:
            print("Skipping seed. Run main.py to see existing data.")
            return
    
    sources = seed_sources()
    facts = seed_facts()
    link_facts_to_sources(facts, sources)
    
    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("Run: python main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
