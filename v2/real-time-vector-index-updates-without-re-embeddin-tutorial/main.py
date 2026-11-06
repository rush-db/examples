"""
Real-Time Vector Index Updates Without Re-Embedding Overhead

This tutorial demonstrates how to update vector-indexed records in RushDB
without incurring the cost and latency of re-computing embeddings from scratch.

Key concept: Use db.records.set() with pre-computed vectors to update both
data and vector index in a single operation, skipping managed embedding.
"""

import os
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

from rushdb import RushDB

# Initialize RushDB
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(api_key)

# Initialize embedding model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Simulated "your embedding pipeline" - in production this could be
# a separate service, batch job, or external API you control.
def compute_embedding(text: str) -> list:
    """
    Simulates your external embedding pipeline.
    
    In a real scenario, this could be:
    - Your own model running locally
    - An embedding API you control
    - A batch process that generated embeddings ahead of time
    
    The key point: the embedding cost is incurred ONCE, not on every update.
    """
    vector = model.encode(text).tolist()
    return vector


def print_section(title):
    """Pretty print a section header."""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print('=' * 50)


def print_result(result, show_data=True):
    """Print a search result nicely."""
    score = result.score if result.score is not None else result.data.get("__score", 0)
    title = result.data.get("title", "Untitled")
    print(f"  [{score:.3f}] {title}")
    if show_data and len(result.data.get("body", "")) > 80:
        body = result.data["body"][:80] + "..."
        print(f"          {body}")


def main():
    print_section("REAL-TIME VECTOR INDEX UPDATES")
    print("\nThis demo shows how to update vector-indexed records")
    print("without re-computing embeddings from RushDB's managed service.")
    print("\nKey method: db.records.set() with pre-computed vectors")
    
    # ========================================================
    # Step 1: Verify existing data
    # ========================================================
    print_section("STEP 1: VERIFY SEEDED DATA")
    
    documents = db.records.find({"labels": ["Document"]}).data
    
    if not documents:
        print("✗ No documents found. Run seed.py first!")
        return
    
    print(f"Found {len(documents)} documents in database")
    
    # Get the index info
    indexes = db.ai.indexes.find().data
    doc_index = next((idx for idx in indexes 
                      if idx['label'] == 'Document' and idx['propertyName'] == 'body'), None)
    
    if not doc_index:
        print("✗ No Document.body index found. Run seed.py first!")
        return
    
    print(f"✓ Using index: {doc_index['__id']}")
    print(f"  Status: {doc_index['status']}")
    print(f"  Dimensions: {doc_index.get('dimensions', 'N/A')}")
    
    # ========================================================
    # Step 2: Initial semantic search
    # ========================================================
    print_section("STEP 2: INITIAL SEMANTIC SEARCH")
    
    initial_query = "machine learning applications"
    print(f"Query: \"{initial_query}\"\n")
    
    initial_results = db.ai.search({
        "propertyName": "body",
        "query": initial_query,
        "labels": ["Document"],
        "limit": 3
    }).data
    
    print(f"Found {len(initial_results)} results:")
    for result in initial_results:
        print_result(result)
    
    # ========================================================
    # Step 3: Pre-computed vector updates
    # ========================================================
    print_section("STEP 3: PRE-COMPUTED VECTOR UPDATES")
    
    print("\nSimulating a scenario where content gets updated:")
    print("- Document content changes (e.g., article revisions)")
    print("- We have pre-computed the new embeddings from our own pipeline")
    print("- We update RushDB with both the new data AND new vector")
    print("- NO re-embedding via RushDB's managed service needed\n")
    
    # Documents to update with their new content
    updates = [
        {
            "title": "Understanding Neural Networks in Production",
            "new_body": "Neural networks serve as the foundation for modern AI systems. Production deployment requires optimizing for latency, implementing batching for throughput, and establishing robust model versioning. Monitor for data drift and establish retraining schedules. Consider using model registries and feature stores for MLOps maturity.",
            "new_category": "mlops"
        },
        {
            "title": "Deep Learning for Beginners",
            "new_body": "Deep learning leverages neural networks with many layers to learn hierarchical representations. Core concepts include backpropagation for gradient computation, optimization via gradient descent variants, and non-linear activation functions. Begin with simple feedforward networks before progressing to convolutional or recurrent architectures.",
            "new_category": "deep-learning"
        },
        {
            "title": "Machine Learning Model Deployment",
            "new_body": "ML model deployment demands systematic approaches. Select inference mode based on latency requirements: synchronous for real-time, asynchronous for batch. Containerize models with Docker for consistency. Implement GitOps for model CI/CD, use model monitoring for drift detection, and establish rollback procedures for failed deployments.",
            "new_category": "mlops"
        }
    ]
    
    print("Updating documents with pre-computed vectors:\n")
    
    for i, update in enumerate(updates):
        # Find the existing document
        results = db.records.find({
            "labels": ["Document"],
            "where": {"title": update["title"]},
            "limit": 1
        }).data
        
        if not results:
            print(f"  ⚠ Document not found: {update['title']}")
            continue
        
        record = results[0]
        
        # Compute new embedding (simulating your external pipeline)
        print(f"  [{i+1}] Computing embedding for: {update['title'][:45]}...")
        new_embedding = compute_embedding(update["new_body"])
        
        # Update BOTH data and vector in one operation
        # This is the key: db.records.set() replaces data AND updates the vector index
        updated = db.records.set(
            target=record,
            label="Document",
            data={
                "title": update["title"],
                "body": update["new_body"],
                "category": update["new_category"]
            },
            vectors=[{"propertyName": "body", "vector": new_embedding}]
        )
        
        print(f"      ✓ Updated with pre-computed vector (no managed embedding)")
        print(f"      ✓ Vector dimension: {len(new_embedding)}")
    
    # ========================================================
    # Step 4: Verify updates with semantic search
    # ========================================================
    print_section("STEP 4: POST-UPDATE SEMANTIC SEARCH")
    
    # Search for content that should now be more relevant after updates
    update_query = "MLOps deployment containerization model monitoring"
    print(f"Query: \"{update_query}\"\n")
    print("Note: This query should return the updated documents higher,")
    print("since they now contain MLOps-related content.\n")
    
    updated_results = db.ai.search({
        "propertyName": "body",
        "query": update_query,
        "labels": ["Document"],
        "limit": 3
    }).data
    
    print(f"Found {len(updated_results)} results:")
    for result in updated_results:
        print_result(result)
    
    # ========================================================
    # Step 5: Compare with managed re-embedding approach
    # ========================================================
    print_section("STEP 5: COST COMPARISON")
    
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│ Scenario: Update 3 documents with new content              │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│ APPROACH 1: Managed Re-Embedding (traditional)            │")
    print("│   - RushDB generates embeddings via managed service        │")
    print("│   - Cost: 5 KU per document × 3 = 15 KU                    │")
    print("│   - Latency: API call + embedding generation               │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│ APPROACH 2: Pre-Computed Vectors (this tutorial)            │")
    print("│   - You generate embeddings via your own pipeline          │")
    print("│   - Cost: 0 KU for embedding generation (you control)      │")
    print("│   - Latency: Vector storage only                           │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│ SAVINGS: 15 KU per update cycle                             │")
    print("│          (assuming you have embedding capacity anyway)      │")
    print("└─────────────────────────────────────────────────────────────┘")
    
    # ========================================================
    # Step 6: Demonstrate relationship to other updates
    # ========================================================
    print_section("STEP 6: BATCH UPDATE SCENARIO")
    
    print("\nIn production, you might receive a batch of content updates:")
    print("- A CMS publishes revised articles")
    print("- A product catalog gets updated")
    print("- User-generated content is revised")
    print("\nWith pre-computed vectors, you can:")
    print("1. Generate embeddings for all updates in one batch")
    print("2. Update RushDB records in a transaction")
    print("3. Skip managed embedding entirely\n")
    
    # Example batch update
    print("Example batch update (pseudocode):")
    print("""
    # 1. Your embedding pipeline generates vectors
    new_vectors = your_embedding_model.encode(updated_contents)
    
    # 2. Transaction updates all records with pre-computed vectors
    with db.transactions.begin() as tx:
        for record, new_data, new_vector in updates:
            db.records.set(
                target=record,
                label="Document",
                data=new_data,
                vectors=[{"propertyName": "body", "vector": new_vector}],
                transaction=tx
            )
    # 3. All updates complete atomically, no managed embedding costs
    """)
    
    # Final stats
    print_section("FINAL INDEX STATUS")
    stats = db.ai.indexes.stats(doc_index['__id'])
    print(f"  Total records: {stats.data['totalRecords']}")
    print(f"  Indexed records: {stats.data['indexedRecords']}")
    print(f"  Index status: {stats.data['status']}")
    
    print("\n✓ Tutorial complete!")
    print("\nKey takeaways:")
    print("  • Use db.records.set() for data + vector updates")
    print("  • Pre-computed vectors skip managed embedding (5 KU savings)")
    print("  • Update both data and vectors atomically in one call")
    print("  • Works great with your existing embedding pipeline")


if __name__ == "__main__":
    main()
