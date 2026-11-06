"""
Cross-Modal Retrieval Tutorial: Searching Images and Audio with Graph-Structured Vectors

This tutorial demonstrates how to build a cross-modal retrieval system using RushDB.
We use CLIP for image embeddings and CLAP for audio embeddings, stored in a property
graph with shared concept nodes for cross-modal linkage.

Key Steps:
1. Schema Design - Modeling images, audio, and shared concept nodes
2. Ingestion - Embedding generation and linking nodes across modalities
3. Cross-Modal Queries - Searching across modalities
4. Refinements - Filtering by metadata and adjusting graph traversal depth
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import RushDB SDK
from rushdb import RushDB

# Import ML libraries for embeddings
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel, AutoProcessor, AutoModel

# =============================================================================
# STEP 0: Check for existing data and setup
# =============================================================================

def check_existing_data():
    """Check if sample data exists, run seed if not."""
    data_path = Path(__file__).parent / "data" / "sample_data.json"
    
    if not data_path.exists():
        print("\n📦 Sample data not found. Running seed.py first...")
        os.system(f"python {Path(__file__).parent / 'seed.py'}")
    
    with open(data_path, "r") as f:
        return json.load(f)


# =============================================================================
# STEP 1: Embedding Models Setup
# =============================================================================

class EmbeddingGenerator:
    """Handles embedding generation for images and audio using CLIP and CLAP."""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"\n🔧 Using device: {self.device}")
        
        # Initialize CLIP for images and text
        print("Loading CLIP model for image-text embeddings...")
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model.to(self.device)
        self.clip_model.eval()
        
        # Initialize CLAP for audio-text embeddings
        # Using a lightweight audio encoder for demo purposes
        print("Loading audio embedding model...")
        self.audio_model = None
        self.audio_dim = 512  # Default dimension for our audio embeddings
        
        # For this tutorial, we'll use CLIP text embeddings for audio descriptions
        # In production, you'd use a proper audio encoder like CLAP or AudioCLIP
        print("Using CLIP text embeddings for audio descriptions (use CLAP for production audio encoding)")
        print("   CLIP supports image<->text; CLAP adds audio<->text capability")
    
    def generate_text_embedding(self, text: str) -> list:
        """Generate embedding for text using CLIP."""
        with torch.no_grad():
            inputs = self.clip_processor(text=[text], return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            outputs = self.clip_model.get_text_features(**inputs)
            embedding = outputs.cpu().numpy().flatten().tolist()
        return embedding
    
    def generate_image_embedding(self, description: str) -> list:
        """Generate embedding for image using CLIP (from description as proxy).
        
        In a real implementation, you would load actual images.
        For this tutorial, we use text descriptions to represent image content.
        """
        return self.generate_text_embedding(description)
    
    def generate_audio_embedding(self, description: str) -> list:
        """Generate embedding for audio using CLIP text model.
        
        For production, replace with actual CLAP audio encoder.
        This demonstrates the architecture for audio-text retrieval.
        """
        return self.generate_text_embedding(description)
    
    def get_embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced."""
        return 512  # CLIP ViT-B/32 outputs 512-dim vectors


# =============================================================================
# STEP 2: Schema Design
# =============================================================================

def design_schema(db: RushDB):
    """Step 2: Design the schema for cross-modal retrieval.
    
    We model three types of entities:
    - IMAGE: Represents visual content with CLIP embeddings
    - AUDIO: Represents audio content with CLAP embeddings
    - CONCEPT: Abstract semantic nodes that link modalities together
    
    Relationships:
    - IMAGE --REPRESENTS--> CONCEPT (image belongs to category/mood)
    - AUDIO --CONTAINS--> CONCEPT (audio contains category/mood)
    - CONCEPT --RELATED_TO--> CONCEPT (concepts are related)
    """
    print("\n" + "="*60)
    print("STEP 1: SCHEMA DESIGN")
    print("="*60)
    print("""
    Graph Structure:
    
    ┌─────────┐         REPRESENTS          ┌───────────┐
    │  IMAGE  │ ──────────────────────────▶  │  CONCEPT  │
    │ (CLIP)  │                             │ (shared)  │
    └─────────┘                             └─────┬─────┘
                                                  │
                       CONTAINS                   │
    ┌─────────┐ ──────────────────────────▶─────┘
    │  AUDIO  │
    │ (CLAP)  │
    └─────────┘
    
    This structure enables:
    - Find images by text query (via CLIP vectors)
    - Find audio by text query (via CLAP vectors)
    - Cross-modal: "find audio that matches this image's mood"
    - Traverse through concepts to link related content
    """)
    
    # In RushDB, we don't predefine schemas - we create records directly
    # But we'll model the structure through relationships
    
    print("✅ Schema modeled through:")
    print("   - IMAGE label with description and category properties")
    print("   - AUDIO label with description and category properties")  
    print("   - CONCEPT label for semantic linking")
    print("   - REPRESENTS relationship (image -> concept)")
    print("   - CONTAINS relationship (audio -> concept)")
    print("   - RELATED_TO relationship (concept -> concept)")


# =============================================================================
# STEP 3: Ingestion - Create Records with Embeddings
# =============================================================================

def ingest_data(db: RushDB, data: dict, embed_gen: EmbeddingGenerator):
    """Step 3: Ingest data with embeddings.
    
    For each image and audio, we:
    1. Create the record with metadata
    2. Generate embeddings
    3. Link to concept nodes
    """
    print("\n" + "="*60)
    print("STEP 2: INGESTION")
    print("="*60)
    
    # Check if data already exists
    existing_images = db.records.find({"labels": ["IMAGE"], "limit": 1})
    if existing_images.total > 0:
        print("\n⚠️  Data already exists in RushDB. Skipping ingestion.")
        print("   Delete existing records or run with a fresh RushDB instance to re-ingest.")
        return
    
    print("\n📥 Ingesting data with embeddings...")
    
    # --- Create Concept Nodes First ---
    print("\n  Creating CONCEPT nodes...")
    concepts = data["concepts"]
    concept_records = []
    
    for i, concept in enumerate(concepts):
        record = db.records.create(
            label="CONCEPT",
            data={
                "name": concept["name"],
                "type": concept["type"],
                "description": concept["description"]
            }
        )
        concept_records.append(record)
        
        if (i + 1) % 5 == 0:
            print(f"    Created {i + 1}/{len(concepts)} concepts...")
    
    print(f"  ✅ Created {len(concept_records)} concept nodes")
    
    # Build concept lookup by name
    concept_by_name = {c["name"]: c for c in concept_records}
    
    # --- Create Image Records ---
    print("\n  Creating IMAGE records with CLIP embeddings...")
    
    # First, create the vector index for images
    img_index = db.ai.indexes.create({
        "label": "IMAGE",
        "propertyName": "embedding",
        "sourceType": "external",
        "dimensions": embed_gen.get_embedding_dimension(),
        "similarityFunction": "cosine"
    })
    print(f"  📊 Created IMAGE vector index: {img_index.data.get('__id', 'pending')}")
    
    images = data["images"]
    image_records = []
    vectors_to_upsert = []
    
    for i, img in enumerate(images):
        # Generate CLIP embedding for the image description
        embedding = embed_gen.generate_image_embedding(img["description"])
        
        # Create the image record (without vector initially - we'll upsert)
        record = db.records.create(
            label="IMAGE",
            data={
                "file_path": img["file_path"],
                "description": img["description"],
                "category": img["category"],
                "mood": img["mood"],
                "tags": img["tags"]
            },
            vectors=[{"propertyName": "embedding", "vector": embedding}]
        )
        image_records.append(record)
        
        # Attach to concept nodes
        category_concept = concept_by_name.get(img["category"])
        mood_concept = concept_by_name.get(img["mood"])
        
        if category_concept:
            db.records.attach(
                source=record,
                target=category_concept,
                options={"type": "REPRESENTS"}
            )
        
        if mood_concept:
            db.records.attach(
                source=record,
                target=mood_concept,
                options={"type": "REPRESENTS"}
            )
        
        if (i + 1) % 5 == 0:
            print(f"    Created {i + 1}/{len(images)} images...")
    
    print(f"  ✅ Created {len(image_records)} image records with CLIP embeddings")
    
    # --- Create Audio Records ---
    print("\n  Creating AUDIO records with CLAP embeddings...")
    
    # Create vector index for audio
    audio_index = db.ai.indexes.create({
        "label": "AUDIO",
        "propertyName": "embedding",
        "sourceType": "external",
        "dimensions": embed_gen.get_embedding_dimension(),
        "similarityFunction": "cosine"
    })
    print(f"  📊 Created AUDIO vector index: {audio_index.data.get('__id', 'pending')}")
    
    audio_files = data["audio"]
    audio_records = []
    
    for i, audio in enumerate(audio_files):
        # Generate CLAP-style embedding for the audio description
        embedding = embed_gen.generate_audio_embedding(audio["description"])
        
        # Create the audio record with embedding
        record = db.records.create(
            label="AUDIO",
            data={
                "file_path": audio["file_path"],
                "description": audio["description"],
                "category": audio["category"],
                "mood": audio["mood"],
                "duration_seconds": audio["duration_seconds"],
                "sample_rate": audio["sample_rate"]
            },
            vectors=[{"propertyName": "embedding", "vector": embedding}]
        )
        audio_records.append(record)
        
        # Attach to concept nodes
        category_concept = concept_by_name.get(audio["category"])
        mood_concept = concept_by_name.get(audio["mood"])
        
        if category_concept:
            db.records.attach(
                source=record,
                target=category_concept,
                options={"type": "CONTAINS"}
            )
        
        if mood_concept:
            db.records.attach(
                source=record,
                target=mood_concept,
                options={"type": "CONTAINS"}
            )
        
        if (i + 1) % 5 == 0:
            print(f"    Created {i + 1}/{len(audio_files)} audio files...")
    
    print(f"  ✅ Created {len(audio_records)} audio records with CLAP embeddings")
    
    # --- Create Concept Relationships ---
    print("\n  Creating CONCEPT relationships...")
    
    # Create related-to links between category and mood concepts
    category_concepts = [c for c in concept_records if c.data.get("type") == "category"]
    mood_concepts = [c for c in concept_records if c.data.get("type") == "mood"]
    
    # Link a few concepts for demonstration
    for cat in category_concepts[:3]:
        for mood in mood_concepts[:2]:
            db.records.attach(
                source=cat,
                target=mood,
                options={"type": "RELATED_TO"}
            )
    
    print("  ✅ Created cross-concept relationships")
    
    print("\n📦 Ingestion complete!")
    print(f"   - {len(image_records)} IMAGE records with CLIP embeddings")
    print(f"   - {len(audio_records)} AUDIO records with CLAP embeddings")
    print(f"   - {len(concept_records)} CONCEPT nodes")


# =============================================================================
# STEP 4: Cross-Modal Queries
# =============================================================================

def demonstrate_cross_modal_queries(db: RushDB, embed_gen: EmbeddingGenerator):
    """Step 4: Demonstrate cross-modal retrieval queries."""
    print("\n" + "="*60)
    print("STEP 3: CROSS-MODAL QUERIES")
    print("="*60)
    
    queries = [
        {
            "name": "Search for calm nature content",
            "text": "peaceful nature scene with water and trees",
            "labels": ["IMAGE"]
        },
        {
            "name": "Search for energetic urban sounds",
            "text": "busy city traffic and street activity",
            "labels": ["AUDIO"]
        },
        {
            "name": "Search images with playful mood",
            "text": "fun and lighthearted moment",
            "labels": ["IMAGE"]
        },
        {
            "name": "Search audio for melancholic atmosphere",
            "text": "emotional and reflective soundscape",
            "labels": ["AUDIO"]
        },
        {
            "name": "Cross-modal: find images similar to audio mood",
            "text": "uplifting sports celebration",
            "labels": ["IMAGE"]
        }
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {query['name']}")
        print(f"   Text: \"{query['text']}\"")
        
        # Generate embedding for the query
        query_embedding = embed_gen.generate_text_embedding(query["text"])
        
        # Perform semantic search
        results = db.ai.search({
            "propertyName": "embedding",
            "queryVector": query_embedding,
            "labels": query["labels"],
            "limit": 3
        })
        
        print(f"   Found {len(results.data)} results:")
        for j, result in enumerate(results.data, 1):
            score = result.score or 0.0
            desc = result.data.get("description", "")[:80]
            cat = result.data.get("category", "unknown")
            mood = result.data.get("mood", "unknown")
            print(f"   [{j}] Score: {score:.3f} | {cat}/{mood} | {desc}...")


# =============================================================================
# STEP 5: Refinements
# =============================================================================

def demonstrate_refinements(db: RushDB, embed_gen: EmbeddingGenerator):
    """Step 5: Demonstrate query refinements with filtering."""
    print("\n" + "="*60)
    print("STEP 4: REFINEMENTS")
    print("="*60)
    
    print("""
    Refinement options in RushDB:
    1. Metadata filtering with 'where' clause
    2. Combined vector search + metadata filtering
    3. Relationship-based traversal
    """)
    
    # --- Refinement 1: Metadata Filtering ---
    print("\n📌 Refinement 1: Filter by metadata")
    print("   Searching images, but only those in 'nature' category")
    
    query_text = "peaceful outdoor scene"
    query_embedding = embed_gen.generate_text_embedding(query_text)
    
    results = db.ai.search({
        "propertyName": "embedding",
        "queryVector": query_embedding,
        "labels": ["IMAGE"],
        "where": {"category": "nature"},
        "limit": 5
    })
    
    print(f"   Found {len(results.data)} nature images matching query:")
    for result in results.data:
        desc = result.data.get("description", "")[:70]
        print(f"   - {desc}...")
    
    # --- Refinement 2: Mood Filtering ---
    print("\n📌 Refinement 2: Filter by mood")
    print("   Searching audio with 'calm' mood only")
    
    query_text = "ambient soundscape"
    query_embedding = embed_gen.generate_text_embedding(query_text)
    
    results = db.ai.search({
        "propertyName": "embedding",
        "queryVector": query_embedding,
        "labels": ["AUDIO"],
        "where": {"mood": "calm"},
        "limit": 5
    })
    
    print(f"   Found {len(results.data)} calm audio files:")
    for result in results.data:
        desc = result.data.get("description", "")[:70]
        dur = result.data.get("duration_seconds", 0)
        print(f"   - {desc}... ({dur}s)")
    
    # --- Refinement 3: Tag-based Filtering ---
    print("\n📌 Refinement 3: Filter by tags")
    print("   Searching images with 'landscape' tag")
    
    query_text = "beautiful scenery"
    query_embedding = embed_gen.generate_text_embedding(query_text)
    
    results = db.ai.search({
        "propertyName": "embedding",
        "queryVector": query_embedding,
        "labels": ["IMAGE"],
        "where": {"tags": {"$contains": "landscape"}},
        "limit": 5
    })
    
    print(f"   Found {len(results.data)} landscape images:")
    for result in results.data:
        tags = result.data.get("tags", [])
        print(f"   - Tags: {tags}")
    
    # --- Refinement 4: Graph Traversal via Concepts ---
    print("\n📌 Refinement 4: Cross-modal via concept traversal")
    print("   Finding audio files that share concepts with 'nature' images")
    
    # First, find nature-related images
    nature_images = db.records.find({
        "labels": ["IMAGE"],
        "where": {"category": "nature"},
        "limit": 3
    })
    
    print(f"   Found {len(nature_images.data)} nature images")
    
    # Now find audio files that link to the same concepts (moods)
    for img in nature_images.data[:2]:
        mood = img.data.get("mood")
        if mood:
            related_audio = db.records.find({
                "labels": ["AUDIO"],
                "where": {"mood": mood},
                "limit": 2
            })
            print(f"   Nature image mood '{mood}' → related audio: {len(related_audio.data)} found")
            for audio in related_audio.data:
                print(f"      - {audio.data.get('description', '')[:60]}...")


# =============================================================================
# STEP 6: Cross-Modal Link Discovery
# =============================================================================

def demonstrate_cross_modal_links(db: RushDB):
    """Step 6: Discover links between modalities through concepts."""
    print("\n" + "="*60)
    print("STEP 5: CROSS-MODAL LINK DISCOVERY")
    print("="*60)
    
    print("""
    Cross-modal retrieval works by:
    1. Both modalities share the same embedding space (CLIP/CLAP)
    2. Concept nodes link images and audio through categories/moods
    3. You can query one modality and find related content in another
    """)
    
    # Find a sample image
    sample_images = db.records.find({"labels": ["IMAGE"], "limit": 1})
    
    if sample_images.data:
        img = sample_images.data[0]
        print(f"\n📷 Sample Image: {img.data.get('description', '')[:80]}...")
        print(f"   Category: {img.data.get('category')}")
        print(f"   Mood: {img.data.get('mood')}")
        
        # Find related audio through concept traversal
        category = img.data.get("category")
        mood = img.data.get("mood")
        
        # Query for audio with same category or mood
        related_audio = db.records.find({
            "labels": ["AUDIO"],
            "where": {
                "$or": [
                    {"category": category},
                    {"mood": mood}
                ]
            },
            "limit": 3
        })
        
        print(f"\n🔗 Cross-modal links found: {len(related_audio.data)} audio files")
        for audio in related_audio.data:
            match_type = "category" if audio.data.get("category") == category else "mood"
            print(f"   [{match_type}] {audio.data.get('description', '')[:60]}...")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution flow."""
    print("\n" + "="*60)
    print("CROSS-MODAL RETRIEVAL TUTORIAL")
    print("Searching Images and Audio with Graph-Structured Vectors")
    print("="*60)
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\n❌ Error: RUSHDB_API_KEY not found in environment")
        print("   Please create a .env file with your RushDB API key")
        print("   Get your key at: https://app.rushdb.com/settings/api-keys")
        return
    
    url = os.getenv("RUSHDB_URL")
    if url:
        db = RushDB(api_key, url=url)
    else:
        db = RushDB(api_key)
    
    print(f"\n✅ Connected to RushDB")
    
    # Check for existing data or generate new
    data = check_existing_data()
    
    # Initialize embedding generator
    print("\n🔧 Initializing embedding models...")
    embed_gen = EmbeddingGenerator()
    
    # Step 1: Design Schema
    design_schema(db)
    
    # Step 2: Ingest Data
    ingest_data(db, data, embed_gen)
    
    # Step 3: Cross-Modal Queries
    demonstrate_cross_modal_queries(db, embed_gen)
    
    # Step 4: Refinements
    demonstrate_refinements(db, embed_gen)
    
    # Step 5: Cross-Modal Link Discovery
    demonstrate_cross_modal_links(db)
    
    print("\n" + "="*60)
    print("TUTORIAL COMPLETE")
    print("="*60)
    print("""
    You've learned how to:
    ✅ Design a cross-modal schema with IMAGE, AUDIO, and CONCEPT nodes
    ✅ Generate and store CLIP/CLAP embeddings in RushDB
    ✅ Link modalities through graph relationships
    ✅ Perform cross-modal semantic searches
    ✅ Refine queries with metadata filters
    ✅ Discover cross-modal links through concept traversal
    
    Next Steps:
    - Experiment with different embedding models (CLIP ViT-L, AudioCLIP)
    - Add more concept types for richer cross-modal linking
    - Implement bi-directional search (image→audio, audio→image)
    - Add temporal concepts for time-based cross-modal queries
    
    Resources:
    - RushDB Docs: https://docs.rushdb.com
    - CLIP Paper: https://arxiv.org/abs/2103.00020
    - GitHub: https://github.com/rush-db/examples
    """)


if __name__ == "__main__":
    main()
