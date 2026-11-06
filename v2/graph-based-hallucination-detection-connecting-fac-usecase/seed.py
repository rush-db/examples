#!/usr/bin/env python3
"""
Seed script for Hallucination Detection demo.

Creates:
- 3 source documents about renewable energy / agrivoltaics
- 12 chunk nodes (3-4 per document)
- Vector embeddings for each chunk
- SOURCED_FROM edges connecting chunks to documents

Run this once before main.py. Safe to re-run (idempotent - checks for existing data).
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Configuration
SIMILARITY_THRESHOLD = 0.65
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Sample documents about renewable energy / agrivoltaics
DOCUMENTS = [
    {
        "title": "NREL Agrivoltaics Study 2021",
        "url": "https://www.nrel.gov/news/2021/agrivoltaics.html",
        "author": "National Renewable Energy Laboratory",
        "content": """Agrivoltaics represents the co-location of agricultural activities and solar photovoltaic energy generation on the same land. Research conducted by NREL in 2021 found that solar panels installed above crops can increase yields by 20-30% in certain climate conditions.

The shading provided by elevated solar panels creates a microclimate that reduces heat stress on plants during peak summer months. This thermal regulation allows for extended growing seasons in some regions. Water evaporation from soil decreases by 20-30%, reducing irrigation needs.

Case studies from Oregon and Massachusetts demonstrate that sheep grazing among solar installations provide natural vegetation management while earning farmers additional revenue of $500-800 per acre annually. The combination of energy production and agricultural output can increase land equivalent efficiency to 160% compared to single-use installations.

The initial capital cost for agrivoltaic systems runs 20-40% higher than standard ground-mounted solar, but the dual revenue streams typically achieve payback periods of 7-10 years versus 12-15 years for solar-only installations."""
    },
    {
        "title": "Fraunhofer Institute Agrivoltaics Report 2022",
        "url": "https://www.fraunhofer.de/en/agrivoltaics",
        "author": "Fraunhofer Institute for Solar Energy Systems",
        "content": """The Fraunhofer Institute published comprehensive findings on agrivoltaic systems in 2022, covering 45 installations across Europe and Asia. Their research confirmed that crop water requirements drop by 30-50% under agrivoltaic installations due to reduced evapotranspiration.

Light wavelength optimization studies showed that specific crop varieties perform better under the diffused light conditions created by semi-transparent solar modules. Lettuce, spinach, and other leafy greens showed 15-25% yield improvements while maintaining premium quality grades.

The technology was first conceptualized in the early 2000s, with the first commercial installations appearing in Germany and the Netherlands around 2011-2013. Japanese researchers at the University of Tokyo pioneered much of the early agrivoltaic research, with significant developments occurring between 2004-2010.

Agrivoltaic systems with bifacial solar panels (panels that capture light on both sides) can increase energy yields by 10-15% compared to monofacial installations. This additional energy generation helps offset the higher installation costs associated with elevated structures needed for agricultural equipment access."""
    },
    {
        "title": "USDA Agricultural Solar Integration Guidelines",
        "url": "https://www.usda.gov/agrivoltaics",
        "author": "United States Department of Agriculture",
        "content": """The USDA published guidelines for agricultural solar integration in 2023, addressing regulatory frameworks and best management practices. Their analysis of 200 agrivoltaic installations found average energy yields of 800-1200 kWh per kilowatt of installed capacity annually.

Height clearance requirements vary by agricultural operation type. Row crop operations typically require minimum 3.5 meters (11.5 feet) clearance, while orchard systems need 4.5-6 meters depending on tree height and pruning schedules. Vineyards can accommodate lower elevations with 2.5 meter minimums.

Soil compaction from construction activities remains a primary concern, with the USDA recommending soil remediation protocols including deep tillage and organic matter amendment post-installation. Vegetative ground covers under solar installations have shown 40% reduction in erosion compared to bare soil control plots.

The economic analysis indicated that farms integrating solar generation alongside crop production achieved 15-25% higher overall land value compared to single-use properties. However, property insurance costs typically increase 10-20% due to the additional infrastructure on-site."""
    }
]


def chunk_text(text: str, chunk_size: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def create_vector_index_if_needed(db: RushDB) -> str:
    """Create vector index for CHUNK.text if it doesn't exist."""
    # Check existing indexes
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx.get("label") == "CHUNK" and idx.get("propertyName") == "text":
            print(f"  Vector index already exists: CHUNK.text (ID: {idx['__id']})")
            return idx["__id"]
    
    # Create new index
    print("  Creating vector index for CHUNK.text...")
    result = db.ai.indexes.create({
        "label": "CHUNK",
        "propertyName": "text",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    index_id = result.data["__id"]
    print(f"  Created index: {index_id}")
    return index_id


def seed_database():
    """Main seeding function."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        sys.exit(1)
    
    db = RushDB(api_key)
    print("\n=== RushDB Hallucination Detection Seed Script ===\n")
    
    # Check if data already exists
    existing_docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if existing_docs.total > 0:
        print(f"⚠️  Database already contains {existing_docs.total} document(s). Skipping seed.")
        print("   Run 'python main.py' to test the pipeline.")
        return
    
    # Load embedding model
    print(f"📦 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("   Model loaded successfully\n")
    
    # Create vector index
    print("🗄️  Setting up RushDB vector index...")
    index_id = create_vector_index_if_needed(db)
    
    # Process each document
    print("\n📚 Processing documents...")
    for doc_idx, doc in enumerate(DOCUMENTS):
        print(f"\n  [{doc_idx + 1}/{len(DOCUMENTS)}] {doc['title']}")
        
        # Create source document
        source_doc = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc["title"],
                "url": doc["url"],
                "author": doc["author"]
            }
        )
        print(f"    ✓ Created DOCUMENT node: {source_doc.id}")
        
        # Chunk the content
        chunks = chunk_text(doc["content"])
        print(f"    ✓ Split into {len(chunks)} chunks")
        
        # Generate embeddings and create chunk nodes
        embeddings = model.encode(chunks)
        
        for chunk_idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = db.records.create(
                label="CHUNK",
                data={
                    "text": chunk_text,
                    "chunk_index": chunk_idx,
                    "source_title": doc["title"]
                },
                vectors=[{"propertyName": "text", "vector": embedding.tolist()}]
            )
            
            # Create SOURCED_FROM edge
            db.records.attach(
                source=chunk,
                target=source_doc,
                options={"type": "SOURCED_FROM", "direction": "out"}
            )
            print(f"    ✓ Chunk {chunk_idx + 1}: {chunk.id[:16]}...")
        
        if (doc_idx + 1) % 100 == 0:
            print(f"    ... processed {doc_idx + 1} documents")
    
    # Print summary
    total_docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1000}).total
    total_chunks = db.records.find({"labels": ["CHUNK"], "limit": 1000}).total
    
    print(f"\n✅ Seed complete!")
    print(f"   Documents: {total_docs}")
    print(f"   Chunks: {total_chunks}")
    print(f"\nRun 'python main.py' to test the hallucination detection pipeline.\n")


if __name__ == "__main__":
    seed_database()
