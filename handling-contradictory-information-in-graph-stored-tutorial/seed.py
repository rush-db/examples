"""
Seed script for the Contradictory Information tutorial.

Creates a realistic knowledge graph with contradictory claims across multiple domains.
This script is idempotent - safe to run multiple times.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
or api_key:
    raise ValueError("RUSHDB_API_KEY environment variable is not set")

db = RushDB(api_key)

# Clear existing test data (idempotent cleanup)
print("Cleaning up existing tutorial data...")
db.records.delete_many({"labels": ["FACT"], "where": {}})
db.records.delete_many({"labels": ["SOURCE"], "where": {}})
print("Cleanup complete.")

# Define knowledge sources
print("\nCreating sources...")
sources_data = [
    {
        "name": "Nature Journal",
        "type": "peer_reviewed",
        "url": "https://nature.com",
        "reliability_score": 0.95,
        "description": "Premier scientific journal with rigorous peer review"
    },
    {
        "name": "Wikipedia",
        "type": "crowdsourced",
        "url": "https://wikipedia.org",
        "reliability_score": 0.72,
        "description": "Collaboratively edited encyclopedia"
    },
    {
        "name": "CDC Health Reports",
        "type": "government",
        "url": "https://cdc.gov",
        "reliability_score": 0.93,
        "description": "Centers for Disease Control official health data"
    },
    {
        "name": "Historical Archives Online",
        "type": "archive",
        "url": "https://archives.example.gov",
        "reliability_score": 0.88,
        "description": "Digitized historical primary sources"
    },
    {
        "name": "Popular Science Monthly",
        "type": "magazine",
        "url": "https://popsci.com",
        "reliability_score": 0.78,
        "description": "General audience science publication"
    },
    {
        "name": "Ancient Texts Repository",
        "type": "archive",
        "url": "https://ancienttexts.example.org",
        "reliability_score": 0.65,
        "description": "Digital collection of ancient manuscripts"
    },
]

created_sources = {}
for src in sources_data:
    record = db.records.create(label="SOURCE", data=src)
    created_sources[src["name"]] = record
    print(f"  Created source: {src['name']}")

print(f"\nCreated {len(created_sources)} sources.")

# Define facts with contradictions
print("\nCreating facts and relationships...")

facts_data = [
    # Science domain - Vitamin D contradictions
    {
        "claim": "Adults should take 600 IU of vitamin D daily",
        "domain": "health",
        "claimed_date": "2020-05-15",
        "confidence_level": "high",
        "evidence_summary": "Based on IOM dietary reference intakes"
    },
    {
        "claim": "Adults need at least 2000 IU of vitamin D daily for optimal health",
        "domain": "health",
        "claimed_date": "2021-03-20",
        "confidence_level": "moderate",
        "evidence_summary": "Alternative research suggests higher thresholds"
    },
    
    # History domain - Alexander the Great
    {
        "claim": "Alexander the Great was born in Pella, Macedonia in 356 BCE",
        "domain": "history",
        "claimed_date": "2019-08-10",
        "confidence_level": "high",
        "evidence_summary": "Multiple ancient sources and archaeological evidence"
    },
    {
        "claim": "Alexander the Great was born in Pella, Macedonia in 356 BCE",
        "domain": "history",
        "claimed_date": "2020-01-05",
        "confidence_level": "high",
        "evidence_summary": "Widely accepted historical consensus"
    },
    {
        "claim": "Alexander the Great died of typhoid fever at age 32",
        "domain": "history",
        "claimed_date": "2018-11-20",
        "confidence_level": "moderate",
        "evidence_summary": "Medical analysis of historical accounts"
    },
    {
        "claim": "Alexander the Great died from acute pancreatitis at age 32",
        "domain": "history",
        "claimed_date": "2019-06-14",
        "confidence_level": "moderate",
        "evidence_summary": "Alternative medical theory based on symptoms described"
    },
    
    # Science domain - Dinosaur extinction
    {
        "claim": "Dinosaurs went extinct 66 million years ago due to asteroid impact",
        "domain": "science",
        "claimed_date": "2017-04-10",
        "confidence_level": "high",
        "evidence_summary": "Chicxulub crater evidence and iridium layer"
    },
    {
        "claim": "Dinosaurs were already declining before the asteroid impact",
        "domain": "science",
        "claimed_date": "2016-09-22",
        "confidence_level": "moderate",
        "evidence_summary": "Fossil record analysis suggests gradual decline"
    },
    {
        "claim": "Volcanic activity, not asteroids, was the primary cause of dinosaur extinction",
        "domain": "science",
        "claimed_date": "2020-02-18",
        "confidence_level": "moderate",
        "evidence_summary": "Deccan Traps volcanic evidence reanalysis"
    },
    
    # Health domain - Coffee consumption
    {
        "claim": "Drinking 3-4 cups of coffee daily is associated with reduced mortality risk",
        "domain": "health",
        "claimed_date": "2019-07-02",
        "confidence_level": "high",
        "evidence_summary": "Large-scale epidemiological studies"
    },
    {
        "claim": "Coffee consumption increases risk of cardiovascular disease",
        "domain": "health",
        "claimed_date": "2018-03-15",
        "confidence_level": "moderate",
        "evidence_summary": "Meta-analysis of earlier clinical trials"
    },
    
    # History domain - Great Wall construction
    {
        "claim": "The Great Wall of China was primarily built during the Ming Dynasty",
        "domain": "history",
        "claimed_date": "2019-10-05",
        "confidence_level": "high",
        "evidence_summary": "Archaeological dating of wall sections"
    },
    {
        "claim": "The Great Wall was originally constructed during the Qin Dynasty",
        "domain": "history",
        "claimed_date": "2018-05-20",
        "confidence_level": "high",
        "evidence_summary": "Historical records and earliest wall foundations"
    },
    
    # Science domain - Water on Mars
    {
        "claim": "Mars had liquid water on its surface 3-4 billion years ago",
        "domain": "science",
        "claimed_date": "2015-11-20",
        "confidence_level": "high",
        "evidence_summary": "NASA Curiosity rover findings"
    },
    {
        "claim": "Mars had flowing liquid water as recently as 2 billion years ago",
        "domain": "science",
        "claimed_date": "2021-03-10",
        "confidence_level": "moderate",
        "evidence_summary": "Recalibrated dating of geological features"
    },
    
    # Health domain - Sleep requirements
    {
        "claim": "Adults need 7-9 hours of sleep per night for optimal health",
        "domain": "health",
        "claimed_date": "2019-01-15",
        "confidence_level": "high",
        "evidence_summary": "NSF sleep duration recommendations"
    },
    {
        "claim": "Human adults can thrive on just 6 hours of sleep with proper training",
        "domain": "health",
        "claimed_date": "2020-08-12",
        "confidence_level": "low",
        "evidence_summary": "Small study group with adaptive sleep patterns"
    },
    
    # History domain - Library of Alexandria
    {
        "claim": "The Library of Alexandria was destroyed in a single catastrophic fire",
        "domain": "history",
        "claimed_date": "2017-06-30",
        "confidence_level": "low",
        "evidence_summary": "Popular culture narrative"
    },
    {
        "claim": "The Library of Alexandria declined gradually over several centuries",
        "domain": "history",
        "claimed_date": "2018-09-14",
        "confidence_level": "high",
        "evidence_summary": "Scholarly consensus based on multiple sources"
    },
    
    # Science domain - Honey properties
    {
        "claim": "Honey never spoils when properly stored",
        "domain": "science",
        "claimed_date": "2019-04-22",
        "confidence_level": "high",
        "evidence_summary": "Archaeological finds of edible ancient honey"
    },
    {
        "claim": "Honey can crystallize and degrade over very long periods",
        "domain": "science",
        "claimed_date": "2020-06-08",
        "confidence_level": "moderate",
        "evidence_summary": "Chemical analysis of aged honey samples"
    },
]

# Create facts
created_facts = []
for i, fact_data in enumerate(facts_data):
    fact = db.records.create(label="FACT", data=fact_data)
    created_facts.append(fact)
    if (i + 1) % 5 == 0:
        print(f"  Created {i + 1}/{len(facts_data)} facts...")

print(f"Created {len(created_facts)} facts.")

# Define source-fact assignments and contradictions
print("\nCreating relationships...")

# Assign each fact to sources (some facts have multiple sources)
source_assignments = [
    # Vitamin D claims
    (0, ["CDC Health Reports"]),
    (1, ["Popular Science Monthly"]),
    
    # Alexander birth (same fact, different sources)
    (2, ["Nature Journal", "Historical Archives Online"]),
    (3, ["Wikipedia"]),
    
    # Alexander death
    (4, ["Nature Journal"]),
    (5, ["Popular Science Monthly"]),
    
    # Dinosaur extinction
    (6, ["Nature Journal"]),
    (7, ["Wikipedia"]),
    (8, ["Popular Science Monthly"]),
    
    # Coffee
    (9, ["Nature Journal", "CDC Health Reports"]),
    (10, ["Popular Science Monthly"]),
    
    # Great Wall
    (11, ["Wikipedia", "Historical Archives Online"]),
    (12, ["Ancient Texts Repository"]),
    
    # Mars water
    (13, ["Nature Journal"]),
    (14, ["Popular Science Monthly"]),
    
    # Sleep
    (15, ["CDC Health Reports", "Nature Journal"]),
    (16, ["Popular Science Monthly"]),
    
    # Library of Alexandria
    (17, ["Wikipedia"]),
    (18, ["Historical Archives Online", "Nature Journal"]),
    
    # Honey
    (19, ["Wikipedia"]),
    (20, ["Nature Journal"]),
]

for fact_idx, source_names in source_assignments:
    fact = created_facts[fact_idx]
    for source_name in source_names:
        source = created_sources[source_name]
        db.records.attach(
            source=fact,
            target=source,
            options={"type": "ASSERTED_BY", "direction": "out"}
        )

print("  Attached facts to sources.")

# Define contradiction relationships
contradiction_pairs = [
    # Vitamin D
    (0, 1, "Daily vitamin D intake recommendations"),
    
    # Alexander death
    (4, 5, "Cause of Alexander the Great's death"),
    
    # Dinosaur extinction
    (6, 8, "Primary cause of dinosaur extinction"),
    (7, 8, "Timeline of dinosaur extinction"),
    
    # Coffee
    (9, 10, "Health effects of coffee consumption"),
    
    # Great Wall
    (11, 12, "Primary construction period of the Great Wall"),
    
    # Mars water
    (13, 14, "Timeline of liquid water on Mars"),
    
    # Sleep
    (15, 16, "Optimal sleep duration for adults"),
    
    # Library of Alexandria
    (17, 18, "Nature of the Library of Alexandria's destruction"),
    
    # Honey
    (19, 20, "Long-term storage properties of honey"),
]

for fact_a_idx, fact_b_idx, topic in contradiction_pairs:
    fact_a = created_facts[fact_a_idx]
    fact_b = created_facts[fact_b_idx]
    
    # Create bidirectional contradiction relationships
    db.records.attach(
        source=fact_a,
        target=fact_b,
        options={"type": "CONTRADICTS", "direction": "out"}
    )
    db.records.attach(
        source=fact_b,
        target=fact_a,
        options={"type": "CONTRADICTS", "direction": "out"}
    )
    
    # Add topic to both facts
    db.records.update(
        record_id=fact_a.id,
        data={"contradiction_topic": topic}
    )
    db.records.update(
        record_id=fact_b.id,
        data={"contradiction_topic": topic}
    )

print(f"  Created {len(contradiction_pairs)} contradiction pairs.")

# Final summary
print("\n" + "=" * 60)
print("SEEDING COMPLETE")
print("=" * 60)
print(f"\nCreated {len(created_sources)} sources")
print(f"Created {len(created_facts)} facts")
print(f"Created {len(contradiction_pairs)} contradiction pairs")
print(f"\nTotal relationships: {len(source_assignments)} ASSERTED_BY + {len(contradiction_pairs) * 2} CONTRADICTS")
print("\nRun 'python main.py' to explore the knowledge graph!")
