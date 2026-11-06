"""
Multi-Modal Retrieval Pipeline - Main Demo

Demonstrates RushDB's multi-modal retrieval capabilities:
1. Pure text search using semantic embeddings
2. Pure image search (simulated with metadata-based vectors)
3. Hybrid search combining text and image similarity
4. Relationship traversal for enriched results

Run seed.py first to populate the database with sample data.
"""

import os
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
URL = os.getenv("RUSHDB_URL")

if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

if URL:
    db = RushDB(API_KEY, url=URL)
else:
    db = RushDB(API_KEY)

# Initialize embedding model
print("\nInitializing embedding model...")
text_model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_simulated_image_vector(seed_text: str) -> list:
    """
    Generate a simulated image embedding for demo purposes.
    
    In production, you would use CLIP or similar to encode actual images.
    This creates deterministic vectors for demonstration.
    """
    import random
    
    seed_value = hash(seed_text) % (2**31)
    rng = random.Random(seed_value)
    raw = np.array([rng.gauss(0, 1) for _ in range(512)])
    
    # Normalize
    norm = np.linalg.norm(raw)
    return (raw / norm).tolist() if norm > 0 else raw.tolist()


def print_header(title: str):
    """Pretty print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(product, rank: int):
    """Print a single search result with formatting."""
    score = product.score if product.score is not None else 0.0
    name = product.data.get("name", "Unknown")
    category = product.data.get("category", "Unknown")
    price = product.data.get("price", 0.0)
    
    print(f"\n  [{rank}] {name}")
    print(f"      Category: {category} | Price: ${price:.2f}")
    print(f"      Similarity Score: {score:.4f}")


def get_index_id(property_name: str) -> str:
    """Get index ID for a specific property."""
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        if idx["propertyName"] == property_name and idx["label"] == "PRODUCT":
            return idx["__id"]
    return None


# =============================================================================
# DEMO 1: Pure Text Search
# =============================================================================
def demo_text_search():
    print_header("DEMO 1: Pure Text Search")
    print("\nQuery: 'premium wireless audio for long flights'")
    print("Method: Semantic search using text embeddings")
    
    # Generate query embedding
    query_text = "premium wireless audio for long flights"
    query_vector = text_model.encode(query_text, normalize_embeddings=True).tolist()
    
    # Search using external index (pre-computed vector)
    text_index_id = get_index_id("text_embedding")
    if not text_index_id:
        print("\n  ERROR: Text embedding index not found. Run seed.py first.")
        return
    
    results = db.ai.search({
        "propertyName": "text_embedding",
        "queryVector": query_vector,
        "labels": ["PRODUCT"],
        "limit": 5,
    })
    
    print(f"\n  Found {len(results.data)} results:\n")
    for i, product in enumerate(results.data[:5], 1):
        print_result(product, i)
    
    return results.data


# =============================================================================
# DEMO 2: Simulated Image Search
# =============================================================================
def demo_image_search():
    print_header("DEMO 2: Simulated Image Search")
    print("\nScenario: User selects a 'sleek electronics product' image")
    print("Method: Vector search using image embeddings")
    
    # Simulate image query (in production, encode actual image)
    query_seed = "sleek minimalist electronic device with clean lines"
    image_query_vector = generate_simulated_image_vector(query_seed)
    
    image_index_id = get_index_id("image_embedding")
    if not image_index_id:
        print("\n  ERROR: Image embedding index not found. Run seed.py first.")
        return
    
    results = db.ai.search({
        "propertyName": "image_embedding",
        "queryVector": image_query_vector,
        "labels": ["PRODUCT"],
        "limit": 5,
    })
    
    print(f"\n  Found {len(results.data)} results:\n")
    for i, product in enumerate(results.data[:5], 1):
        print_result(product, i)
    
    return results.data


# =============================================================================
# DEMO 3: Hybrid Search (Text + Image Combined)
# =============================================================================
def demo_hybrid_search():
    print_header("DEMO 3: Hybrid Search (Text + Image)")
    print("\nScenario: User searches for 'comfortable furniture for home office'")
    print("         with preference for lifestyle imagery")
    print("Method: Weighted combination of text and image similarity")
    
    query_text = "comfortable furniture for home office"
    query_seed = "cozy home office setup with ergonomic furniture"
    
    # Generate both embeddings
    text_vec = text_model.encode(query_text, normalize_embeddings=True).tolist()
    image_vec = generate_simulated_image_vector(query_seed)
    
    # Search both indexes
    text_results = db.ai.search({
        "propertyName": "text_embedding",
        "queryVector": text_vec,
        "labels": ["PRODUCT"],
        "limit": 20,
    })
    
    image_results = db.ai.search({
        "propertyName": "image_embedding",
        "queryVector": image_vec,
        "labels": ["PRODUCT"],
        "limit": 20,
    })
    
    # Combine scores with weighting
    text_scores = {r.id: r.score for r in text_results.data}
    image_scores = {r.id: r.score for r in image_results.data}
    
    # Get all unique product IDs
    all_ids = set(text_scores.keys()) | set(image_scores.keys())
    
    # Weighted combination (60% text, 40% image)
    TEXT_WEIGHT = 0.6
    IMAGE_WEIGHT = 0.4
    
    combined_scores = []
    for pid in all_ids:
        text_score = text_scores.get(pid, 0.0)
        img_score = image_scores.get(pid, 0.0)
        combined = (TEXT_WEIGHT * text_score) + (IMAGE_WEIGHT * img_score)
        combined_scores.append((pid, combined))
    
    # Sort by combined score
    combined_scores.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n  Top 5 hybrid results:\n")
    
    # Fetch full records for top results
    top_ids = [pid for pid, _ in combined_scores[:5]]
    records = db.records.find_by_id(top_ids)
    
    # Create lookup
    record_map = {r.id: r for r in records}
    
    for rank, (pid, score) in enumerate(combined_scores[:5], 1):
        if pid in record_map:
            product = record_map[pid]
            ts = text_scores.get(pid, 0.0)
            is_ = image_scores.get(pid, 0.0)
            
            name = product.data.get("name", "Unknown")
            category = product.data.get("category", "Unknown")
            
            print(f"\n  [{rank}] {name}")
            print(f"      Category: {category}")
            print(f"      Combined Score: {score:.4f} (text: {ts:.3f}, image: {is_:.3f})")


# =============================================================================
# DEMO 4: Relationship Traversal
# =============================================================================
def demo_relationship_traversal():
    print_header("DEMO 4: Relationship Traversal")
    print("\nFinding products belonging to a collection with filtered search")
    
    # Find the collection
    collections = db.records.find({
        "labels": ["COLLECTION"],
        "where": {"name": "E-Commerce Catalog"}
    })
    
    if not collections.data:
        print("\n  ERROR: Collection not found. Run seed.py first.")
        return
    
    collection = collections.data[0]
    print(f"\n  Found collection: {collection.data.get('name')}")
    print(f"  Description: {collection.data.get('description')}")
    
    # Find products that BELONG_TO this collection
    products_in_collection = db.records.find({
        "labels": ["PRODUCT"],
        "where": {
            "COLLECTION": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"}
            }
        },
        "limit": 10,
    })
    
    print(f"\n  Products in collection: {len(products_in_collection.data)}")
    print("\n  Sample products:\n")
    
    for i, product in enumerate(products_in_collection.data[:3], 1):
        print_result(product, i)


# =============================================================================
# DEMO 5: Cross-Modal Filtering
# =============================================================================
def demo_cross_modal_filtering():
    print_header("DEMO 5: Cross-Modal Filtering")
    print("\nScenario: Find 'audio products' using image similarity")
    print("         then filter by text match")
    
    # First, search by image (finding electronics-like products)
    audio_seed = "electronic device headphones speakers audio equipment"
    image_query = generate_simulated_image_vector(audio_seed)
    
    image_results = db.ai.search({
        "propertyName": "image_embedding",
        "queryVector": image_query,
        "labels": ["PRODUCT"],
        "limit": 10,
    })
    
    print(f"\n  Image search returned {len(image_results.data)} candidates")
    
    # Filter results by category using text embedding search
    category_query = text_model.encode("electronics audio sound", normalize_embeddings=True).tolist()
    
    text_results = db.ai.search({
        "propertyName": "text_embedding",
        "queryVector": category_query,
        "labels": ["PRODUCT"],
        "limit": 20,
    })
    
    # Get intersection
    image_ids = {r.id for r in image_results.data}
    text_ids = {r.id for r in text_results.data}
    
    matching_ids = image_ids & text_ids
    
    print(f"  Text embedding search found {len(text_ids)} candidates")
    print(f"  Intersection (cross-modal match): {len(matching_ids)} products\n")
    
    if matching_ids:
        matched_records = db.records.find_by_id(list(matching_ids))
        for i, product in enumerate(matched_records[:5], 1):
            print_result(product, i)
    else:
        print("  No exact matches found. Showing top image results:")
        for i, product in enumerate(image_results.data[:3], 1):
            print_result(product, i)


# =============================================================================
# DEMO 6: Index Statistics
# =============================================================================
def demo_index_stats():
    print_header("DEMO 6: Vector Index Statistics")
    
    indexes = db.ai.indexes.find()
    
    print(f"\n  Found {len(indexes.data)} indexes for PRODUCT label:\n")
    
    for idx in indexes.data:
        prop = idx["propertyName"]
        status = idx.get("status", "unknown")
        
        # Get stats if available
        try:
            stats = db.ai.indexes.stats(idx["__id"])
            indexed = stats.data.get("indexedRecords", "N/A")
            total = stats.data.get("totalRecords", "N/A")
            
            print(f"  • {prop}")
            print(f"    Status: {status}")
            print(f"    Indexed: {indexed}/{total} records")
        except Exception:
            print(f"  • {prop} ({status})")
    
    # Show all labels
    print("\n\nAll labels in database:")
    labels = db.labels.find()
    for label in labels:
        print(f"  • {label.name}: {label.count} records")


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "#" * 60)
    print("#  Multi-Modal Retrieval Pipeline Demo")
    print("#  Using RushDB for Vector Storage and Semantic Search")
    print("#" * 60)
    
    # Check that data exists
    existing = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    if not existing.data:
        print("\n\nERROR: No products found in database.")
        print("Please run 'python seed.py' first to populate sample data.\n")
        return
    
    print(f"\nFound existing data: {len(existing.data)} products\n")
    
    # Run all demos
    demo_text_search()
    demo_image_search()
    demo_hybrid_search()
    demo_relationship_traversal()
    demo_cross_modal_filtering()
    demo_index_stats()
    
    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)
    print("\n  Next steps:")
    print("  • Try modifying queries in each demo function")
    print("  • Adjust TEXT_WEIGHT/IMAGE_WEIGHT in hybrid search")
    print("  • Add your own products with real image embeddings")
    print("\n  Reference: https://docs.rushdb.com")
    print()


if __name__ == "__main__":
    main()
