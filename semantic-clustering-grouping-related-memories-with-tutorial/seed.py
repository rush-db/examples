"""
Seed script: Generates 100+ realistic memory records with embeddings.

This script creates mock memory data with:
- Realistic titles and content about various life experiences
- Pre-computed 384-dimensional embeddings using sentence-transformers
- Relationships between semantically related memories

Run this once before main.py to populate the database.
"""

import os
import random
from datetime import datetime, timedelta
from typing import List

from dotenv import load_dotenv
from faker import Faker
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize Faker for realistic content
fake = Faker()
Faker.seed(42)
random.seed(42)

# Memory themes for realistic content generation
MEMORY_THEMES = {
    "travel": [
        "Tokyo trip planning notes",
        "Kyoto temples visit",
        "European backpacking adventure",
        "Beach vacation in Portugal",
        "Mountain hiking in Alps",
        "Road trip along Pacific coast",
        "Safari in Tanzania",
        "Exploring ancient Rome",
    ],
    "family": [
        "Family reunion 2023",
        "Holiday traditions",
        "Childhood home memories",
        "Summer camp stories",
        "Birthday celebrations",
        "Grandparents anniversary",
        "Cousins gathering",
        "New baby nephew arrival",
    ],
    "learning": [
        "Language learning journey",
        "First programming project",
        "University graduation day",
        "Online course completion",
        "Reading challenge success",
        "Music lessons experience",
        "Cooking class adventure",
        "Photography hobby start",
    ],
    "food": [
        "Japanese cuisine exploration",
        "Italian cooking class",
        "Street food tour in Bangkok",
        "Thanksgiving dinner preparation",
        "Wine tasting in Napa Valley",
        "Homemade pizza tradition",
        "Farmers market discovery",
    ],
    "nature": [
        "Cherry blossom season",
        "Northern lights observation",
        "Whale watching expedition",
        "Camping under stars",
        "Forest bathing experience",
        "Desert landscape visit",
        "Waterfall hiking trail",
    ],
    "milestones": [
        "First apartment move",
        "Career promotion celebration",
        "First marathon completion",
        "Buying first car",
        "Getting driver's license",
        "First international flight",
        "Owning a pet",
        "Learning to swim",
    ],
}

# Tags for categorization
ALL_TAGS = [
    "travel", "family", "learning", "food", "nature",
    "milestones", "friends", "work", "health", "creativity",
    "adventure", "tradition", "discovery", "growth", "celebration"
]


def generate_memory_content(theme: str, title: str) -> str:
    """Generate realistic memory content based on theme."""
    templates = {
        "travel": [
            f"Planning my trip to {fake.city()}. The anticipation is building as I research {fake.word()} attractions and local cuisine. Can't wait to explore the {fake.word()} streets and meet new people.",
            f"Finally visited {title}. The experience was transformative - from {fake.word()} architecture to the warm hospitality of locals. Will cherish these moments forever.",
        ],
        "family": [
            f"Spent quality time with family at {fake.word()} gathering. Stories were shared, laughs were had, and the {fake.word()} bond grew stronger.",
            f"Remembering {title}. Those precious moments with loved ones remind me what truly matters in life.",
        ],
        "learning": [
            f"Major milestone achieved with {title}. The journey was challenging but rewarding. Grateful for every lesson learned along the way.",
            f"Started exploring {fake.word()} and discovered a new passion. {title} opened doors I never knew existed.",
        ],
        "food": [
            f"Culinary adventure with {title}. Tasted incredible {fake.word()} flavors and learned traditional recipes from locals.",
            f"Cooking session that turned into a feast. {title} brought friends together around the table for an unforgettable evening.",
        ],
        "nature": [
            f"Witnessed breathtaking {title}. Standing amidst {fake.word()} landscapes reminded me of nature's incredible beauty and power.",
            f"Adventure in the wild: {title}. The sounds of {fake.word()} and fresh air were truly rejuvenating.",
        ],
        "milestones": [
            f"Celebrating {title} - a moment that marks new beginnings and opportunities. Life's journey continues with renewed energy.",
            f"{title} represents hard work paying off. This achievement will stay with me as a reminder of what dedication can accomplish.",
        ],
    }
    
    theme_templates = templates.get(theme, templates["milestones"])
    return random.choice(theme_templates)


def generate_memories(count: int = 100) -> List[dict]:
    """Generate a list of memory records with embeddings."""
    memories = []
    used_titles = set()
    
    # Collect all titles from themes
    all_titles = []
    for theme, titles in MEMORY_THEMES.items():
        for title in titles:
            all_titles.append((theme, title))
    
    # Generate additional random titles if needed
    while len(all_titles) < count:
        theme = random.choice(list(MEMORY_THEMES.keys()))
        title = fake.sentence(nb_words=4).rstrip('.')
        if title not in used_titles:
            all_titles.append((theme, title))
    
    # Shuffle and pick the required count
    random.shuffle(all_titles)
    selected = all_titles[:count]
    
    for theme, title in selected:
        used_titles.add(title)
        
        # Generate date within last 5 years
        days_ago = random.randint(0, 1825)
        memory_date = datetime.now() - timedelta(days=days_ago)
        
        # Select 1-3 random tags
        tags = random.sample(ALL_TAGS, k=random.randint(1, 3))
        if theme not in tags:
            tags.append(theme)
        
        content = generate_memory_content(theme, title)
        
        memories.append({
            "title": title,
            "content": content,
            "theme": theme,
            "tags": tags,
            "date": memory_date.isoformat(),
            "mood": random.choice(["happy", "nostalgic", "excited", "peaceful", "grateful"]),
            "importance": random.choice(["core", "significant", "minor"]),
        })
    
    return memories


def main():
    """Seed the database with memory records and embeddings."""
    print("=== Memory Seeding Script ===\n")
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("Please create a .env file with your API key")
        return
    
    db = RushDB(api_key, url=os.getenv("RUSHDB_URL"))
    
    # Check for existing memories
    existing = db.records.find({"labels": ["MEMORY"], "limit": 1})
    if existing.data:
        print("Memories already exist in the database. Skipping seed.")
        print("Delete existing MEMORY records or run with --force to reseed.")
        return
    
    # Initialize embedding model
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print(f"Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}\n")
    
    # Generate memory records
    print("Generating 100 memory records...")
    memories = generate_memories(count=100)
    
    # Create vector index for memory content
    print("\nCreating vector index for memory content...")
    try:
        index = db.ai.indexes.create({
            "label": "MEMORY",
            "propertyName": "content",
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine",
        })
        index_id = index.data["__id"]
        print(f"Vector index created: {index_id}")
    except Exception as e:
        print(f"Index may already exist: {e}")
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            if idx["label"] == "MEMORY" and idx["propertyName"] == "content":
                index_id = idx["__id"]
                break
    
    # Create memories with embeddings
    print("\nCreating memory records with embeddings...")
    batch_size = 20
    all_records = []
    
    for i in range(0, len(memories), batch_size):
        batch = memories[i:i + batch_size]
        
        # Generate embeddings for batch
        contents = [m["content"] for m in batch]
        embeddings = model.encode(contents, show_progress_bar=False)
        
        # Create records with inline vectors
        for memory, embedding in zip(batch, embeddings):
            try:
                record = db.records.create(
                    label="MEMORY",
                    data={
                        "title": memory["title"],
                        "content": memory["content"],
                        "theme": memory["theme"],
                        "tags": memory["tags"],
                        "date": memory["date"],
                        "mood": memory["mood"],
                        "importance": memory["importance"],
                    },
                    vectors=[{
                        "propertyName": "content",
                        "vector": embedding.tolist()
                    }]
                )
                all_records.append(record)
                
                if (i + len(batch)) % 20 == 0:
                    print(f"  Created {i + len(batch)} memories...")
                    
            except Exception as e:
                print(f"Error creating memory '{memory['title']}': {e}")
    
    print(f"\n✓ Created {len(all_records)} memory records with embeddings")
    
    # Create relationships between semantically similar memories
    print("\nCreating relationships between related memories...")
    related_count = 0
    
    for i, record in enumerate(all_records[:30]):  # Connect first 30 memories
        # Find 2-3 similar memories to connect
        similar = db.ai.search({
            "propertyName": "content",
            "queryVector": record["content"],  # Will use stored vector
            "labels": ["MEMORY"],
            "limit": 4
        })
        
        for other in similar.data[:2]:  # Connect to top 2
            if other.id != record.id:
                try:
                    db.records.attach(
                        source=record,
                        target=other,
                        options={"type": "CONNECTED_TO", "direction": "out"}
                    )
                    related_count += 1
                except Exception:
                    pass  # Relationship may already exist
    
    print(f"✓ Created {related_count} relationships between memories")
    
    # Create theme-based relationships
    print("\nCreating theme-based relationships...")
    theme_groups = {}
    for record in all_records:
        theme = record.data.get("theme")
        if theme not in theme_groups:
            theme_groups[theme] = []
        theme_groups[theme].append(record)
    
    for theme, records in theme_groups.items():
        for i, record in enumerate(records[:5]):  # Connect first 5 of each theme
            for other in records[i+1:3]:  # Connect to next 2
                try:
                    db.records.attach(
                        source=record,
                        target=other,
                        options={"type": "SAME_THEME_AS", "direction": "out"}
                    )
                except Exception:
                    pass
    
    print(f"✓ Created theme-based relationships")
    
    # Verify index coverage
    print("\nVerifying vector index...")
    stats = db.ai.indexes.stats(index_id)
    stats_data = stats.data
    print(f"✓ Index coverage: {stats_data['indexedRecords']} / {stats_data['totalRecords']} records")
    
    print("\n=== Seeding Complete ===")
    print(f"\nTotal memories: {len(all_records)}")
    print(f"Themes covered: {list(theme_groups.keys())}")
    print("\nRun 'python main.py' to explore semantic clustering!")


if __name__ == "__main__":
    main()
