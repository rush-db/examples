"""
Indexing for Speed: RushDB Index Configuration Best Practices

This tutorial demonstrates:
1. Creating vector indexes (managed vs external)
2. Using inline vectors during record upsert
3. Monitoring index statistics
4. Performing semantic search with filters
5. Best practices for index configuration
"""

import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Initialize the embedding model (all-MiniLM-L6-v2 is fast and efficient)
# This model produces 384-dimensional vectors
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 50}")
    print(title)
    print("=" * 50)


def print_step(step_num: int, description: str):
    """Print a formatted step."""
    print(f"\n[{step_num}/5] {description}...")


def create_indexes(db: RushDB) -> dict:
    """Create vector indexes for the tutorial."""
    print_section("Step 1: Creating Vector Indexes")
    
    indexes = {}
    
    # First, list existing indexes
    print("\n  Checking existing indexes...")
    existing = db.ai.indexes.find()
    existing_index_names = set()
    for idx in existing.data:
        full_name = f"{idx['label']}.{idx['propertyName']}"
        existing_index_names.add(full_name)
        print(f"    Found: {full_name} ({idx['status']})")
    
    # External index for detailed descriptions (requires pre-computed vectors)
    if "PRODUCT.description" not in existing_index_names:
        print("\n  Creating 'external' index for PRODUCT.description...")
        result = db.ai.indexes.create({
            "label": "PRODUCT",
            "propertyName": "description",
            "sourceType": "external",
            "dimensions": 384,  # Match our model's output dimension
            "similarityFunction": "cosine"  # Best for normalized embeddings
        })
        indexes['external_id'] = result.data["__id"]
        print(f"    ✓ Created external index: {result.data['__id']}")
    else:
        # Find the existing index ID
        for idx in existing.data:
            if idx['label'] == "PRODUCT" and idx['propertyName'] == "description":
                indexes['external_id'] = idx['__id']
                print(f"    ✓ Using existing external index")
    
    # Managed index for short descriptions (server handles embedding)
    if "PRODUCT.shortDescription" not in existing_index_names:
        print("\n  Creating 'managed' index for PRODUCT.shortDescription...")
        result = db.ai.indexes.create({
            "label": "PRODUCT",
            "propertyName": "shortDescription",
            "sourceType": "managed"  # Server uses configured embedding model
        })
        indexes['managed_id'] = result.data["__id"]
        print(f"    ✓ Created managed index: {result.data['__id']}")
    else:
        for idx in existing.data:
            if idx['label'] == "PRODUCT" and idx['propertyName'] == "shortDescription":
                indexes['managed_id'] = idx['__id']
                print(f"    ✓ Using existing managed index")
    
    return indexes


def upsert_records_with_vectors(db: RushDB, model) -> int:
    """Upsert records with pre-computed vectors for external index."""
    print_section("Step 2: Upserting Records with Vectors")
    
    # Fetch all products
    print("\n  Fetching existing products...")
    products = db.records.find({"labels": ["PRODUCT"], "limit": 300})
    print(f"    Found {products.total} products")
    
    if products.total == 0:
        print("    ERROR: No products found. Please run seed.py first.")
        return 0
    
    count = 0
    batch_size = 20
    records = list(products.data)
    
    print(f"\n  Upserting vectors in batches of {batch_size}...")
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        with db.transactions.begin() as tx:
            for record in batch:
                description = record.get("description", "")
                short_desc = record.get("shortDescription", "")
                
                # Generate embeddings
                desc_vector = model.encode(description).tolist()
                short_vector = model.encode(short_desc).tolist()
                
                # Upsert with inline vectors
                db.records.upsert(
                    label="PRODUCT",
                    data=record.data,  # Keep all existing data
                    options={"mergeBy": ["name"]},
                    vectors=[
                        {"propertyName": "description", "vector": desc_vector},
                        {"propertyName": "shortDescription", "vector": short_vector}
                    ],
                    transaction=tx
                )
                count += 1
        
        if (i + batch_size) % 100 == 0 or i + batch_size >= len(records):
            print(f"    Processed {min(i + batch_size, len(records))}/{len(records)} records...")
    
    print(f"\n  ✓ Upserted {count} products with vectors")
    return count


def check_index_stats(db: RushDB, indexes: dict):
    """Monitor index statistics and health."""
    print_section("Step 3: Monitoring Index Statistics")
    
    # Wait for indexing to complete (async on server side)
    print("\n  Waiting for indexing to complete...")
    time.sleep(2)
    
    for idx_type, index_id in indexes.items():
        print(f"\n  Index: {idx_type} ({index_id})")
        stats = db.ai.indexes.stats(index_id)
        
        print(f"    Status: {stats.data.get('status', 'unknown')}")
        print(f"    Indexed Records: {stats.data.get('indexedRecords', 0)}")
        print(f"    Total Records: {stats.data.get('totalRecords', 0)}")
        print(f"    Dimensions: {stats.data.get('dimensions', 'N/A')}")
        print(f"    Similarity: {stats.data.get('similarityFunction', 'N/A')}")
    
    print("\n  ✓ All indexes are online and healthy")


def demonstrate_vector_search(db: RushDB):
    """Demonstrate various vector search techniques."""
    print_section("Step 4: Vector Search Demonstrations")
    
    # Search queries
    queries = [
        {
            "query": "wireless headphones with noise cancellation",
            "filter": None,
            "description": "Basic semantic search"
        },
        {
            "query": "powerful laptop for developers",
            "filter": {"category": "Electronics"},
            "description": "Semantic search with label filter"
        },
        {
            "query": "comfortable shoes for running",
            "filter": {"inStock": True},
            "description": "Semantic search with property filter"
        }
    ]
    
    for idx, q in enumerate(queries, 1):
        print(f"\n  Demo {idx}: {q['description']}")
        print(f"  Query: \"{q['query']}\"")
        
        search_params = {
            "propertyName": "description",
            "query": q["query"],
            "labels": ["PRODUCT"],
            "limit": 5
        }
        
        if q["filter"]:
            search_params["where"] = q["filter"]
        
        start_time = time.time()
        results = db.ai.search(search_params)
        elapsed = time.time() - start_time
        
        print(f"  Found {len(results.data)} results in {elapsed*1000:.1f}ms:")
        
        for i, result in enumerate(results.data[:3], 1):
            name = result.get("name", "Unknown")
            price = result.get("price", 0)
            score = result.score
            print(f"    {i}. [{score:.3f}] {name} - ${price:.2f}")


def demonstrate_combined_search(db: RushDB):
    """Demonstrate combining vector search with property filters."""
    print_section("Step 5: Advanced Search Patterns")
    
    print("\n  Pattern: Semantic search + multiple filters")
    print("  Query: \"laptop computer\"")
    print("  Filter: category == 'Electronics', price < 1000, inStock == True")
    
    results = db.ai.search({
        "propertyName": "description",
        "query": "laptop computer",
        "labels": ["PRODUCT"],
        "where": {
            "category": "Electronics",
            "price": {"$lt": 1000},
            "inStock": True
        },
        "limit": 5
    })
    
    print(f"\n  Results ({len(results.data)} found):")
    for i, result in enumerate(results.data, 1):
        name = result.get("name", "Unknown")
        price = result.get("price", 0)
        score = result.score
        print(f"    {i}. [{score:.3f}] {name}")
        print(f"       Price: ${price:.2f}")
    
    print("\n  ✓ Combined searches leverage both vector index and property filters")
    
    # Show available indexes
    print("\n  Listing all available indexes:")
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        print(f"    - {idx['label']}.{idx['propertyName']} ({idx['status']})")


def show_best_practices(db: RushDB):
    """Display best practices summary."""
    print_section("Indexing Best Practices Summary")
    
    practices = [
        {
            "title": "Choose the Right Index Type",
            "details": "Use 'managed' for short fields where server embedding is acceptable. Use 'external' for custom embeddings or high-volume scenarios."
        },
        {
            "title": "Match Dimensions to Your Model",
            "details": "When using external indexes, ensure dimensions match your embedding model (e.g., 384 for all-MiniLM-L6-v2, 768 for text-embedding-ada-002)."
        },
        {
            "title": "Use cosine for Normalized Vectors",
            "details": "sentence-transformers produces normalized vectors, making cosine similarity optimal. Use euclidean for exact distances."
        },
        {
            "title": "Combine with Property Filters",
            "details": "Vector search + property filters = powerful queries. Filters narrow results before vector comparison, improving both speed and relevance."
        },
        {
            "title": "Monitor Index Health",
            "details": "Use index.stats() to track indexing progress and identify issues. Wait for 'online' status before querying."
        },
        {
            "title": "Inline Vectors on Upsert",
            "details": "The vectors= parameter on upsert/create is cleaner than separate upsert_vectors() calls. Use mergeBy for idempotent updates."
        }
    ]
    
    for i, practice in enumerate(practices, 1):
        print(f"\n  {i}. {practice['title']}")
        print(f"     {practice['details']}")


def main():
    """Main tutorial execution."""
    print("\n" + "=" * 50)
    print("  RushDB Index Configuration Best Practices")
    print("  Indexing for Speed Tutorial")
    print("=" * 50)
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\nERROR: RUSHDB_API_KEY environment variable not set.")
        print("Please create a .env file with your API key (see .env.example)")
        return
    
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    print(f"\n✓ Connected to RushDB")
    
    try:
        # Step 1: Create indexes
        print_step(1, "Creating vector indexes")
        indexes = create_indexes(db)
        
        # Step 2: Upsert records with vectors
        print_step(2, "Upserting records with vectors")
        count = upsert_records_with_vectors(db, model)
        if count == 0:
            print("\nERROR: No records to index. Run seed.py first.")
            return
        
        # Step 3: Check index statistics
        print_step(3, "Checking index statistics")
        check_index_stats(db, indexes)
        
        # Step 4: Demonstrate vector search
        print_step(4, "Running vector searches")
        demonstrate_vector_search(db)
        
        # Step 5: Advanced patterns
        print_step(5, "Demonstrating advanced patterns")
        demonstrate_combined_search(db)
        
        # Show best practices
        show_best_practices(db)
        
        print("\n" + "=" * 50)
        print("  Tutorial Complete! ✓")
        print("=" * 50)
        print("\nNext steps:")
        print("  1. Experiment with different embedding models")
        print("  2. Try combining vector search with relationship traversal")
        print("  3. Monitor your KU usage at https://rushdb.com/pricing")
        print()
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise


if __name__ == "__main__":
    main()
