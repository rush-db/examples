"""
Cross-Modal Retrieval - Main Demonstration

Demonstrates how to use RushDB's hybrid graph+vector architecture
for cross-modal semantic search (images ↔ audio via graph bridges).

Query patterns:
1. Within-modality semantic search (pure vector similarity)
2. Cross-modal search (vector search + graph traversal)
3. Concept-centric retrieval (find all media by semantic relationship)
"""

import argparse
import os
from dotenv import load_dotenv

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")

if not api_key:
    print("ERROR: RUSHDB_API_KEY not set in .env")
    print("Copy .env.example to .env and add your API key.")
    exit(1)

db = RushDB(api_key, url=url) if url else RushDB(api_key)


def demo_within_modality_images():
    """Demo 1: Pure semantic search within images."""
    print("\n" + "─"*60)
    print("DEMO 1: Within-Modality Semantic Search (Images)")
    print("─"*60)
    
    query = "peaceful nature scene with water"
    print(f"Query: \"{query}\"")
    print()
    
    results = db.ai.search({
        "propertyName": "description",
        "query": query,
        "labels": ["IMAGE"],
        "limit": 5
    })
    
    print("Top matching images:")
    for i, record in enumerate(results.data, 1):
        score = record.score or 0
        desc = record.data.get("description", "")
        print(f"  {i}. [{score:.3f}] {desc[:70]}...")
    
    return results.data


def demo_within_modality_audio():
    """Demo 2: Pure semantic search within audio."""
    print("\n" + "─"*60)
    print("DEMO 2: Within-Modality Semantic Search (Audio)")
    print("─"*60)
    
    query = "upbeat celebration music with drums"
    print(f"Query: \"{query}\"")
    print()
    
    results = db.ai.search({
        "propertyName": "description",
        "query": query,
        "labels": ["AUDIO"],
        "limit": 5
    })
    
    print("Top matching audio clips:")
    for i, record in enumerate(results.data, 1):
        score = record.score or 0
        desc = record.data.get("description", "")
        print(f"  {i}. [{score:.3f}] {desc[:70]}...")
    
    return results.data


def demo_cross_modal_image_to_audio():
    """Demo 3: Cross-modal search - find audio matching an image's emotion."""
    print("\n" + "─"*60)
    print("DEMO 3: Cross-Modal Search (Image → Audio via Concepts)")
    print("─"*60)
    
    # Step 1: Find a target image using semantic search
    image_query = "sunset over calm ocean waves"
    print(f"Step 1: Finding image matching '{image_query}'...")
    
    images = db.ai.search({
        "propertyName": "description",
        "query": image_query,
        "labels": ["IMAGE"],
        "limit": 1
    })
    
    if not images.data:
        print("  No images found. Try seeding first: python seed.py")
        return
    
    target_image = images.data[0]
    print(f"  Found: {target_image.data.get('name')}")
    print(f"  Description: {target_image.data.get('description')}")
    print(f"  Emotion: {target_image.data.get('emotion')}")
    
    # Step 2: Find concepts this image represents
    print(f"\nStep 2: Finding concepts via graph traversal...")
    
    concepts = db.records.find({
        "labels": ["CONCEPT"],
        "where": {
            "IMAGE": {
                "$relation": {"type": "REPRESENTS", "direction": "in"},
                "id": target_image.id
            }
        },
        "limit": 5
    })
    
    concept_names = [c.data.get("name") for c in concepts.data]
    print(f"  Connected concepts: {concept_names}")
    
    if not concepts.data:
        print("  No concepts found. The image may not be linked to any concept.")
        print("  Continuing with direct audio search as fallback...")
        
        # Fallback: direct semantic search
        audio_results = db.ai.search({
            "propertyName": "description",
            "query": target_image.data.get("emotion", "peaceful"),
            "labels": ["AUDIO"],
            "limit": 5
        })
        print(f"\nFallback audio search for emotion '{target_image.data.get('emotion')}':")
    else:
        # Step 3: Find audio clips that express the same concepts
        print(f"\nStep 3: Finding audio clips via shared concepts...")
        
        concept_ids = [c.id for c in concepts.data]
        
        audio_results = db.records.find({
            "labels": ["AUDIO"],
            "where": {
                "CONCEPT": {
                    "$relation": {"type": "EXPRESSES", "direction": "out"},
                    "id": {"$in": concept_ids}
                }
            },
            "limit": 5
        })
        print(f"  Found {audio_results.total} audio clips via concept bridge")
    
    print("\nAudio clips matching the image's emotional tone:")
    for i, audio in enumerate(audio_results.data, 1):
        name = audio.data.get("name", "Unknown")
        desc = audio.data.get("description", "")
        emotion = audio.data.get("emotion", "unknown")
        print(f"  {i}. {name}")
        print(f"     [{emotion}] {desc[:60]}...")
    
    return audio_results.data


def demo_concept_centric():
    """Demo 4: Concept-centric retrieval - find all media by semantic relationship."""
    print("\n" + "─"*60)
    print("DEMO 4: Concept-Centric Retrieval")
    print("─"*60)
    
    target_concept = "serenity"
    print(f"Finding all media related to concept: '{target_concept}'")
    print()
    
    # Find the concept node
    concept_result = db.records.find({
        "labels": ["CONCEPT"],
        "where": {"name": target_concept}
    })
    
    if not concept_result.data:
        print(f"  Concept '{target_concept}' not found.")
        return
    
    concept = concept_result.data[0]
    print(f"  Concept: {concept.data.get('name')}")
    print(f"  Keywords: {concept.data.get('keywords')}")
    
    # Find images representing this concept
    images = db.records.find({
        "labels": ["IMAGE"],
        "where": {
            "CONCEPT": {
                "$relation": {"type": "REPRESENTS", "direction": "out"},
                "id": concept.id
            }
        },
        "limit": 10
    })
    
    # Find audio expressing this concept
    audio = db.records.find({
        "labels": ["AUDIO"],
        "where": {
            "CONCEPT": {
                "$relation": {"type": "EXPRESSES", "direction": "out"},
                "id": concept.id
            }
        },
        "limit": 10
    })
    
    print(f"\n  Images representing '{target_concept}' ({images.total}):")
    for img in images.data:
        print(f"    • {img.data.get('name')}")
    
    print(f"\n  Audio expressing '{target_concept}' ({audio.total}):")
    for aud in audio.data:
        print(f"    • {aud.data.get('name')}")
    
    print(f"\n  Cross-modal count: {images.total} images + {audio.total} audio = {images.total + audio.total} total")


def demo_graph_traversal():
    """Demo 5: Graph traversal to explore cross-modal relationships."""
    print("\n" + "─"*60)
    print("DEMO 5: Graph Traversal - Exploring Relationships")
    print("─"*60)
    
    # Get a sample image
    images = db.records.find({"labels": ["IMAGE"], "limit": 1})
    
    if not images.data:
        print("  No images found. Try seeding first: python seed.py")
        return
    
    sample_image = images.data[0]
    print(f"Sample image: {sample_image.data.get('name')}")
    print(f"  ID: {sample_image.id}")
    print(f"  Description: {sample_image.data.get('description')}")
    
    # Traverse: image → concepts → audio
    print("\nTraversing: IMAGE → CONCEPTS → AUDIO")
    
    # Get concepts for this image
    concepts = db.records.find({
        "labels": ["CONCEPT"],
        "where": {
            "IMAGE": {
                "$relation": {"type": "REPRESENTS", "direction": "in"},
                "id": sample_image.id
            }
        }
    })
    
    print(f"  Step 1: {len(concepts.data)} concepts via REPRESENTS relationship")
    for c in concepts.data:
        print(f"    → {c.data.get('name')}")
    
    if concepts.data:
        # Get audio for these concepts
        concept_ids = [c.id for c in concepts.data]
        audio = db.records.find({
            "labels": ["AUDIO"],
            "where": {
                "CONCEPT": {
                    "$relation": {"type": "EXPRESSES", "direction": "out"},
                    "id": {"$in": concept_ids}
                }
            },
            "limit": 5
        })
        
        print(f"  Step 2: {audio.total} audio clips via EXPRESSES relationship")
        for a in audio.data:
            print(f"    → {a.data.get('name')}")
        
        print("\n  ✓ Graph traversal complete: image bridged to audio via concepts")


def check_database_ready():
    """Check if database has been seeded."""
    images = db.records.find({"labels": ["IMAGE"], "limit": 1})
    return images.total > 0


def main():
    parser = argparse.ArgumentParser(description="Cross-Modal Retrieval Demo")
    parser.add_argument(
        "--mode",
        choices=["full", "demo", "check"],
        default="full",
        help="full: seed + demo (default), demo: demo only, check: verify data"
    )
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("CROSS-MODAL RETRIEVAL - RUSHDB DEMONSTRATION")
    print("="*60)
    
    if args.mode == "check":
        if check_database_ready():
            print("\n✓ Database is ready with cross-modal data.")
        else:
            print("\n✗ No data found. Run `python seed.py` first.")
        return
    
    if args.mode == "demo":
        if not check_database_ready():
            print("\n✗ No data found. Run `python seed.py` first.")
            return
    
    if args.mode == "full":
        if not check_database_ready():
            print("\n📦 No data found. Running seed.py first...")
            print("-"*60)
            import subprocess
            result = subprocess.run(["python", "seed.py"], capture_output=False)
            if result.returncode != 0:
                print("\n✗ Seeding failed. Check your API key and try again.")
                return
        else:
            print("\n✓ Data already exists. Skipping seeding.")
    
    print("\n" + "="*60)
    print("RUNNING DEMONSTRATIONS")
    print("="*60)
    
    try:
        # Run all demos
        demo_within_modality_images()
        demo_within_modality_audio()
        demo_cross_modal_image_to_audio()
        demo_concept_centric()
        demo_graph_traversal()
        
        print("\n" + "="*60)
        print("ALL DEMONSTRATIONS COMPLETE")
        print("="*60)
        print("\nKey Takeaways:")
        print("  • Vector search works within a modality (image→image, audio→audio)")
        print("  • Graph traversal bridges modalities (image→concepts→audio)")
        print("  • Concept anchor nodes enable semantic cross-modal queries")
        print("  • RushDB's hybrid architecture combines both approaches")
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify your API key in .env")
        print("  2. Run 'python seed.py' to populate data")
        print("  3. Check vector indexes exist: db.ai.indexes.find()")
        raise


if __name__ == "__main__":
    main()
