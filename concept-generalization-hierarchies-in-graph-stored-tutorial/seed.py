"""
Seed script: Creates a concept generalization hierarchy with embeddings.

This script creates a multi-level IS_A hierarchy demonstrating:
- Root concepts (abstract)
- Mid-level categories
- Specific instances (leaf nodes)

All concepts include vector embeddings for semantic similarity search.
"""

import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env")

db = RushDB(api_key)

# Initialize embedding model
print("📦 Loading embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def get_embedding(text: str) -> list:
    """Generate embedding for text using the sentence transformer."""
    return embedder.encode(text).tolist()


# Define the concept hierarchy as nested structure
# Format: (name, definition, [children])
CONCEPT_HIERARCHY = [
    {
        "name": "Living Thing",
        "definition": "Any organism that exhibits the characteristics of life, including growth, reproduction, and metabolism",
        "children": [
            {
                "name": "Animal",
                "definition": "A multicellular organism that is heterotrophic and capable of voluntary movement",
                "children": [
                    {
                        "name": "Mammal",
                        "definition": "A warm-blooded vertebrate animal characterized by the presence of hair or fur and mammary glands",
                        "children": [
                            {
                                "name": "Dog",
                                "definition": "A domesticated carnivorous mammal known for loyalty and companionship",
                                "children": [
                                    {"name": "Golden Retriever", "definition": "A friendly, intelligent breed of dog developed for retrieving game"},
                                    {"name": "German Shepherd", "definition": "A large breed of working dog known for intelligence and versatility"},
                                    {"name": "Poodle", "definition": "An intelligent, active breed of dog known for its curly coat"},
                                ]
                            },
                            {
                                "name": "Cat",
                                "definition": "A small domesticated carnivorous mammal kept as a pet",
                                "children": [
                                    {"name": "Persian Cat", "definition": "A long-haired breed of cat known for its calm temperament"},
                                    {"name": "Siamese Cat", "definition": "A breed of cat known for its distinctive color points and vocal nature"},
                                ]
                            },
                            {"name": "Horse", "definition": "A large domesticated hoofed mammal used for riding and transportation"},
                            {"name": "Whale", "definition": "A large marine mammal with a streamlined body and flippers"},
                        ]
                    },
                    {
                        "name": "Bird",
                        "definition": "A warm-blooded vertebrate with feathers and wings",
                        "children": [
                            {"name": "Eagle", "definition": "A large bird of prey with broad wings and strong beak"},
                            {"name": "Penguin", "definition": "A flightless seabird adapted to aquatic life"},
                        ]
                    },
                    {"name": "Fish", "definition": "A cold-blooded aquatic vertebrate with gills and fins"},
                ]
            },
            {
                "name": "Plant",
                "definition": "A multicellular eukaryote that produces food through photosynthesis",
                "children": [
                    {"name": "Tree", "definition": "A perennial plant with a woody trunk and branches"},
                    {"name": "Flower", "definition": "The reproductive structure of a flowering plant"},
                    {"name": "Grass", "definition": "A plant with narrow leaves and jointed stems"},
                ]
            },
        ]
    },
    {
        "name": "Information",
        "definition": "Data that has been processed, organized, and structured to convey meaning",
        "children": [
            {
                "name": "Knowledge",
                "definition": "Information that has been internalized through experience or education",
                "children": [
                    {"name": "Scientific Knowledge", "definition": "Systematic knowledge obtained through the scientific method"},
                    {"name": "Practical Knowledge", "definition": "Skill or expertise gained through practice and application"},
                ]
            },
            {"name": "Data", "definition": "Raw facts and statistics collected for reference or analysis"},
            {"name": "Document", "definition": "A written or printed paper containing information"},
        ]
    },
    {
        "name": "Artifact",
        "definition": "An object made by humans, typically for a practical purpose",
        "children": [
            {
                "name": "Tool",
                "definition": "A device used to carry out a particular function",
                "children": [
                    {"name": "Hammer", "definition": "A hand tool with a heavy metal head used for driving nails"},
                    {"name": "Computer", "definition": "An electronic device for processing and storing data"},
                ]
            },
            {"name": "Vehicle", "definition": "A machine used to transport people or goods"},
        ]
    },
    {
        "name": "Abstract Concept",
        "definition": "An idea or notion that exists only as an abstraction without concrete physical existence",
        "children": [
            {"name": "Time", "definition": "The indefinite continued progress of existence and events"},
            {"name": "Space", "definition": "The boundless three-dimensional extent in which objects exist"},
            {"name": "Love", "definition": "An intense feeling of deep affection"},
        ]
    },
]


def count_concepts(hierarchy: list, level: int = 0) -> tuple:
    """Count total concepts and max depth in hierarchy."""
    count = len(hierarchy)
    max_level = level
    for item in hierarchy:
        if "children" in item and item["children"]:
            child_count, child_level = count_concepts(item["children"], level + 1)
            count += child_count
            max_level = max(max_level, child_level)
    return count, max_level


def create_concept_record(db: RushDB, concept_data: dict, level: int, parent_record=None) -> dict:
    """
    Create a single concept record with embedding and attach to parent.
    Returns the created record.
    """
    name = concept_data["name"]
    definition = concept_data["definition"]
    
    # Generate embedding from definition
    embedding = get_embedding(definition)
    
    # Create the record with inline vector
    record = db.records.create(
        label="CONCEPT",
        data={
            "name": name,
            "definition": definition,
            "level": level,
        },
        vectors=[{"propertyName": "definition", "vector": embedding}]
    )
    
    # Attach to parent if exists (IS_A relationship)
    if parent_record:
        db.records.attach(
            source=record,           # child
            target=parent_record,   # parent
            options={"type": "IS_A", "direction": "out"}
        )
    
    return record


def seed_hierarchy(db: RushDB, hierarchy: list, level: int = 0, parent: dict = None) -> list:
    """Recursively create all concepts in the hierarchy."""
    created = []
    
    for concept_data in hierarchy:
        record = create_concept_record(db, concept_data, level, parent)
        created.append(record)
        
        if "children" in concept_data and concept_data["children"]:
            children_created = seed_hierarchy(db, concept_data["children"], level + 1, record)
            created.extend(children_created)
    
    return created


def cleanup_existing():
    """Remove existing CONCEPT records for clean reseeding."""
    try:
        existing = db.records.find({"labels": ["CONCEPT"], "limit": 1000})
        if existing.data:
            for record in existing.data:
                db.records.delete(record_id=record.id)
            print(f"🗑️  Cleaned up {len(existing.data)} existing records")
    except Exception as e:
        print(f"Note: Cleanup encountered an issue (may be first run): {e}")


def create_vector_index():
    """Create or verify the vector index exists for CONCEPT.definition."""
    try:
        indexes = db.ai.indexes.find()
        concept_index = None
        for idx in indexes.data:
            if idx.get("label") == "CONCEPT" and idx.get("propertyName") == "definition":
                concept_index = idx
                break
        
        if not concept_index:
            print("📐 Creating vector index for CONCEPT.definition...")
            index = db.ai.indexes.create({
                "label": "CONCEPT",
                "propertyName": "definition",
                "sourceType": "external",
                "dimensions": EMBEDDING_DIM,
                "similarityFunction": "cosine"
            })
            print(f"   Index created with ID: {index.id}")
        else:
            print(f"📐 Using existing vector index: {concept_index.get('__id')}")
            
    except Exception as e:
        print(f"⚠️  Vector index creation note: {e}")


def main():
    print("🌱 Seeding concept hierarchy...\n")
    
    # Cleanup existing data for idempotent seeding
    cleanup_existing()
    
    # Create vector index
    create_vector_index()
    
    # Create the hierarchy
    created_records = seed_hierarchy(db, CONCEPT_HIERARCHY)
    print(f"\n✅ Created {len(created_records)} concept records")
    
    # Count relationships
    total_concepts = len(created_records)
    total_relationships = total_concepts - 3  # 3 root concepts have no parent
    print(f"✅ Created {total_relationships} IS_A relationships")
    
    # Count root concepts
    roots = [r for r in created_records if r.data.get("level") == 0]
    print(f"✅ Created {len(roots)} level-0 roots: {', '.join(r['name'] for r in roots)}")
    
    # Verify depth
    max_level = max(r.data.get("level", 0) for r in created_records)
    print(f"✅ Hierarchy depth: {max_level + 1} levels (0-{max_level})")
    
    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    main()
