#!/usr/bin/env python3
"""
Seed script for the Citation Graph Tracker.

Creates sample documents about AI/ML topics, splits them into chunks,
generates vector embeddings, and stores everything in RushDB.

Run this script once before main.py to populate the database.
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Configuration
VECTOR_DIMENSIONS = 384  # all-MiniLM-L6-v2 output dimension
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 3  # sentences per chunk


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """
    Split text into chunks of approximately chunk_size sentences.
    
    Args:
        text: The full text to chunk
        chunk_size: Number of sentences per chunk
    
    Returns:
        List of text chunks
    """
    sentences = text.replace('\n', ' ').split('. ')
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = '. '.join(sentences[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip() + '.' if not chunk.endswith('.') else chunk)
    return chunks


def generate_embeddings(texts: list[str], model) -> list[list[float]]:
    """
    Generate vector embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        model: SentenceTransformer model instance
    
    Returns:
        List of embedding vectors (as lists for JSON serialization)
    """
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def seed_documents():
    """
    Main seeding function. Creates documents, chunks, and vector indexes.
    """
    print("\n🌱 Seeding RushDB with sample documents...\n")
    
    # Initialize RushDB
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("❌ Error: RUSHDB_API_TOKEN not found in environment")
        print("   Please copy .env.example to .env and add your API key")
        return False
    
    db = RushDB(api_token)
    
    # Load sample documents
    data_path = Path(__file__).parent / "data" / "documents.json"
    with open(data_path, "r") as f:
        documents_data = json.load(f)
    
    print(f"📄 Loaded {len(documents_data)} documents")
    
    # Initialize embedding model
    print(f"📦 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Create vector index first (required before upserting vectors)
    print("\n🔧 Setting up vector index...")
    
    # Delete existing index if it exists (for idempotency)
    existing_indexes = db.ai.indexes.find()
    for idx in existing_indexes.data:
        if idx["label"] == "CHUNK" and idx["propertyName"] == "body":
            print(f"   Found existing index, deleting for clean seed...")
            db.ai.indexes.delete(idx["__id"])
    
    # Create new vector index
    index_response = db.ai.indexes.create({
        "label": "CHUNK",
        "propertyName": "body",
        "sourceType": "external",
        "dimensions": VECTOR_DIMENSIONS,
        "similarityFunction": "cosine"
    })
    
    index_id = index_response.data["__id"]
    print(f"   ✅ Created vector index (ID: {index_id})")
    
    # Process documents and create chunks
    all_chunks = []
    all_chunk_embeddings = []
    chunk_to_document_map = []
    
    for doc in documents_data:
        print(f"\n📝 Processing: {doc['title']}")
        
        # Create document record
        document = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc["title"],
                "author": doc["author"],
                "published_date": doc["published_date"],
                "category": doc["category"],
                "source_url": doc.get("source_url", "")
            }
        )
        print(f"   ✅ Created DOCUMENT: {document.id}")
        
        # Create chunks from content
        chunks = chunk_text(doc["content"])
        print(f"   📦 Created {len(chunks)} chunks from content")
        
        for i, chunk_text_content in enumerate(chunks):
            # Create chunk record (without vector first)
            chunk = db.records.create(
                label="CHUNK",
                data={
                    "body": chunk_text_content,
                    "position": i,
                    "document_id": document.id
                }
            )
            
            # Link chunk to document
            db.records.attach(
                source=chunk,
                target=document,
                options={"type": "PART_OF", "direction": "out"}
            )
            
            all_chunks.append(chunk_text_content)
            chunk_to_document_map.append({
                "chunk_id": chunk.id,
                "document_id": document.id,
                "document_title": doc["title"]
            })
        
        # Progress indicator
        if len(all_chunks) % 100 == 0:
            print(f"   ... {len(all_chunks)} chunks created so far")
    
    # Generate all embeddings
    print(f"\n🧠 Generating embeddings for {len(all_chunks)} chunks...")
    all_embeddings = generate_embeddings(all_chunks, model)
    print(f"   ✅ Generated {len(all_embeddings)} embeddings ({VECTOR_DIMENSIONS}D each)")
    
    # Upsert vectors to the index
    print(f"\n📊 Upserting vectors to index...")
    vector_items = [
        {
            "recordId": chunk_to_document_map[i]["chunk_id"],
            "vector": all_embeddings[i]
        }
        for i in range(len(all_chunks))
    ]
    
    db.ai.indexes.upsert_vectors(index_id, {"items": vector_items})
    print(f"   ✅ Upserted {len(vector_items)} vectors")
    
    # Print summary
    print(f"\n" + "="*50)
    print(f"✅ SEEDING COMPLETE!")
    print(f"   • {len(documents_data)} documents created")
    print(f"   • {len(all_chunks)} chunks created")
    print(f"   • Vector index created with {VECTOR_DIMENSIONS} dimensions")
    print(f"   • Using model: {EMBEDDING_MODEL}")
    print("="*50 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = seed_documents()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Seeding failed with error: {e}")
        raise
