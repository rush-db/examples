"""
Setup script to create the vector index on RushDB.

This creates the vector index needed for semantic search on CacheEntry.query_text.
Run this once before using the main tutorial script.
"""

import os
import sys
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

def setup_vector_index():
    """Create the vector index for semantic cache search."""
    
    # Check for API key
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("❌ RUSHDB_API_KEY not found in environment")
        print("   Copy .env.example to .env and add your API key")
        sys.exit(1)
    
    # Initialize RushDB
    db = RushDB(api_key, url=os.getenv("RUSHDB_URL"))
    
    print("\n🔧 Setting up Semantic Cache Vector Index\n")
    print("-" * 50)
    
    # Check embedding provider to determine dimensions
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
    
    if embedding_provider == "local":
        print("[*] Using local SentenceTransformers embeddings")
        print("[*] Loading model: all-MiniLM-L6-v2 (384 dimensions)")
        dimensions = 384
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            test_embedding = model.encode("test")
            dimensions = len(test_embedding)
            print(f"[*] Model loaded. Embedding dimension: {dimensions}")
        except Exception as e:
            print(f"❌ Failed to load SentenceTransformers: {e}")
            sys.exit(1)
    else:
        print("[*] Using OpenAI embeddings (text-embedding-ada-002)")
        print("[*] Embedding dimension: 1536")
        dimensions = 1536
    
    print("-" * 50)
    
    # Check if index already exists
    try:
        existing_indexes = db.ai.indexes.find()
        for idx in existing_indexes.data:
            if idx.get('label') == 'CacheEntry' and idx.get('propertyName') == 'query_text':
                print(f"\n✅ Vector index already exists:\n")
                print(f"   Label: {idx['label']}")
                print(f"   Property: {idx['propertyName']}")
                print(f"   Status: {idx['status']}")
                print(f"   Dimensions: {idx.get('dimensions', 'N/A')}")
                
                stats = db.ai.indexes.stats(idx['__id'])
                print(f"   Records indexed: {stats.data.get('indexedRecords', 0)}")
                return
    except Exception as e:
        print(f"[*] Note: Could not check existing indexes: {e}")
    
    # Create the vector index
    print("\n[*] Creating new vector index...")
    
    try:
        index = db.ai.indexes.create({
            "label": "CacheEntry",
            "propertyName": "query_text",
            "sourceType": "external",
            "dimensions": dimensions,
            "similarityFunction": "cosine"
        })
        
        print("\n✅ Vector index created successfully!\n")
        print("-" * 50)
        print(f"   Index ID: {index.data.get('__id')}")
        print(f"   Label: CacheEntry")
        print(f"   Property: query_text")
        print(f"   Dimensions: {dimensions}")
        print(f"   Similarity: cosine")
        print(f"   Status: {index.data.get('status')}")
        print("-" * 50)
        
        # Wait a moment for index to initialize
        print("\n[*] Waiting for index to initialize...")
        import time
        time.sleep(2)
        
        # Get final stats
        stats = db.ai.indexes.stats(index.data['__id'])
        print(f"[*] Index ready! {stats.data.get('indexedRecords', 0)} records indexed")
        
    except Exception as e:
        print(f"\n❌ Failed to create vector index: {e}")
        sys.exit(1)
    
    print("\n✨ Setup complete! You can now run main.py\n")

if __name__ == "__main__":
    setup_vector_index()
