#!/usr/bin/env python3
"""
Main demonstration script for RushDB in Retrieval-Augmented Fine-Tuning.


This script demonstrates:
1. Semantic search for similar training examples
2. Graph-traversal queries (filter by metadata via relationships)
3. Combined vector + graph queries
4. Batching examples for fine-tuning iterations

See README.md for detailed documentation.
"""

import os
from typing import Optional

from dotenv import load_dotenv

from rushdb import RushDB

# Load environment
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")

if not API_KEY:
    raise ValueError("Missing RUSHDB_API_KEY. Copy .env.example to .env and fill in your API key.")

# Initialize RushDB
db = RushDB(API_KEY)


# =============================================================================
# DEMO 1: Semantic Search for Similar Examples
# =============================================================================
def demo_semantic_search():
    """Demonstrate vector similarity search for finding similar training examples."""
    print("\n" + "=" * 60)
    print("DEMO 1: Semantic Search for Similar Examples")
    print("=" * 60)
    
    query = "How do I reset my password"
    print(f"\n📝 Query: \"{query}\"")
    
    # Search for similar examples using semantic similarity
    results = db.ai.search({
        "propertyName": "instruction",
        "query": query,
        "labels": ["TrainingExample"],
        "limit": 3
    })
    
    print(f"\n🔍 Found {len(results.data)} similar examples:\n")
    
    for i, example in enumerate(results.data, 1):
        print(f"   {i}. \"{example['instruction']}\"")
        print(f"      Score: {example.score:.3f}")
        print(f"      Confidence: {example.get('label_confidence', 'N/A')}")
        print(f"      Label: {example.get('label', 'N/A')}")
        print(f"      Feedback: {example.get('user_feedback', 'N/A')}")
        print()


# =============================================================================
# DEMO 2: Graph-Traversal Query
# =============================================================================
def demo_graph_traversal():
    """Demonstrate graph traversal with metadata filtering.
    
    Query: Find high-confidence examples with manual labels (user_feedback=accepted)
    """
    print("\n" + "=" * 60)
    print("DEMO 2: Graph-Traversal Query (High Confidence + Manual Label)")
    print("=" * 60)
    
    print("\n📋 Criteria:")
    print("   • label_confidence >= 0.85")
    print("   • user_feedback = 'accepted'")
    print("   • order by confidence descending")
    
    # Find examples matching criteria
    examples = db.records.find({
        "labels": ["TrainingExample"],
        "where": {
            "label_confidence": {"$gte": 0.85},
            "user_feedback": "accepted"
        },
        "limit": 10,
        "orderBy": {"label_confidence": "desc"}
    })
    
    print(f"\n🔍 Found {len(examples)} examples matching criteria:\n")
    
    for i, example in enumerate(examples[:5], 1):
        print(f"   {i}. Source: {example.get('source', 'N/A')}")
        print(f"      Domain: {example.get('domain', 'N/A')}")
        print(f"      Confidence: {example.get('label_confidence', 'N/A')}")
        print(f"      Label: {example.get('label', 'N/A')}")
        print(f"      Feedback: {example.get('user_feedback', 'N/A')}")
        print()


# =============================================================================
# DEMO 3: Combined Vector + Graph Query
# =============================================================================
def demo_combined_query():
    """Demonstrate combining vector search with graph-based filtering.
    
    Query: Find examples similar to 'API authentication errors'
    Filter: source_type=documentation AND confidence>=0.8
    """
    print("\n" + "=" * 60)
    print("DEMO 3: Combined Vector + Graph Query")
    print("=" * 60)
    
    query = "API authentication errors"
    print(f"\n📝 Query: \"{query}\"")
    print("📋 Additional Filters:")
    print("   • source = 'documentation'")
    print("   • label_confidence >= 0.8")
    
    # Combined search: semantic similarity + metadata filters
    results = db.ai.search({
        "propertyName": "instruction",
        "query": query,
        "labels": ["TrainingExample"],
        "where": {
            "source": "documentation",
            "label_confidence": {"$gte": 0.8}
        },
        "limit": 5
    })
    
    print(f"\n🔍 Found {len(results.data)} examples:\n")
    
    if results.data:
        for i, example in enumerate(results.data, 1):
            print(f"   {i}. \"{example['instruction']}\"")
            print(f"      Score: {example.score:.3f}")
            print(f"      Domain: {example.get('domain', 'N/A')}")
            print(f"      Confidence: {example.get('label_confidence', 'N/A')}")
            print(f"      Task: {example.get('task_id', 'N/A')}")
            print()
    else:
        print("   (No examples match all criteria - try relaxing filters)")



# =============================================================================
# DEMO 4: Batch Retrieval for Fine-Tuning Loop
# =============================================================================
def get_training_batch(
    db: RushDB,
    batch_size: int = 8,
    strategy: str = "stratified",
    min_confidence: float = 0.7
) -> list:
    """Retrieve a batch of examples for fine-tuning.
    
    Args:
        db: RushDB instance
        batch_size: Number of examples to retrieve
        strategy: 'stratified' (balanced across tasks) or 'random'
        min_confidence: Minimum label confidence threshold
    
    Returns:
        List of training examples for a batch
    """
    
    # Get all unique domains/tasks
    domains = set()
    
    # Use graph traversal to get unique domains via relationships
    all_examples = db.records.find({
        "labels": ["TrainingExample"],
        "where": {
            "label_confidence": {"$gte": min_confidence}
        },
        "limit": 100
    })
    
    for example in all_examples:
        if "domain" in example:
            domains.add(example["domain"])
    
    domains = list(domains) if domains else ["customer_support", "code_generation", "data_analysis"]
    
    batch = []
    
    if strategy == "stratified":
        # Stratified sampling: balanced across domains
        per_domain = max(1, batch_size // len(domains))
        
        for domain in domains:
            domain_examples = db.records.find({
                "labels": ["TrainingExample"],
                "where": {
                    "domain": domain,
                    "label_confidence": {"$gte": min_confidence},
                    "user_feedback": {"$in": ["accepted", "reviewed"]}
                },
                "limit": per_domain,
                "orderBy": {"label_confidence": "desc"}
            })
            batch.extend(domain_examples)
    else:
        # Random sampling (by confidence)
        batch = db.records.find({
            "labels": ["TrainingExample"],
            "where": {
                "label_confidence": {"$gte": min_confidence}
            },
            "limit": batch_size,
            "orderBy": {"label_confidence": "desc"}
        })
    
    return batch[:batch_size]



def demo_batch_retrieval():
    """Demonstrate batching for fine-tuning training iterations."""
    print("\n" + "=" * 60)
    print("DEMO 4: Batch Retrieval for Fine-Tuning Loop")
    print("=" * 60)
    
    batch_size = 6
    print(f"\n📦 Batch size: {batch_size} examples")
    print(f"📋 Strategy: stratified (balanced across domains)")
    print(f"📊 Min confidence: 0.7")
    
    batch = get_training_batch(db, batch_size=batch_size, strategy="stratified")
    
    print(f"\n🔍 Retrieved batch with {len(batch)} examples:\n")
    
    # Group by domain
    by_domain = {}
    for example in batch:
        domain = example.get("domain", "unknown")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(example)
    
    for domain, examples in by_domain.items():
        avg_conf = sum(e.get("label_confidence", 0) for e in examples) / len(examples)
        print(f"   📁 {domain}: {len(examples)} examples (avg confidence: {avg_conf:.2f})")
        for ex in examples:
            print(f"      • \"{ex.get('instruction', 'N/A')[:50]}...\"")
            print(f"        Confidence: {ex.get('label_confidence', 'N/A')}, Feedback: {ex.get('user_feedback', 'N/A')}")
    
    return batch


# =============================================================================
# DEMO 5: Relationship Traversal
# =============================================================================
def demo_relationship_traversal():
    """Demonstrate traversing relationships to find source documents and tasks."""
    print("\n" + "=" * 60)
    print("DEMO 5: Relationship Traversal")
    print("=" * 60)
    
    print("\n📋 Finding examples and their related documents/tasks:\n")
    
    # Get a few examples
    examples = db.records.find({
        "labels": ["TrainingExample"],
        "limit": 3
    })
    
    for i, example in enumerate(examples, 1):
        print(f"   Example {i}: \"{example.get('instruction', 'N/A')[:50]}...\"")
        
        # Find source document via DERIVED_FROM relationship
        source_docs = db.records.find({
            "labels": ["SourceDocument"],
            "where": {
                "TrainingExample": {
                    "$relation": {"type": "DERIVED_FROM", "direction": "in"}
                }
            }
        })
        
        # Find task via TRAINS_FOR relationship
        tasks = db.records.find({
            "labels": ["FineTuningTask"],
            "where": {
                "TrainingExample": {
                    "$relation": {"type": "TRAINS_FOR", "direction": "in"}
                }
            }
        })
        
        if source_docs:
            print(f"      Source doc: {source_docs[0].get('title', 'N/A')}")
            print(f"      Source type: {source_docs[0].get('source_type', 'N/A')}")
        if tasks:
            print(f"      Fine-tuning task: {tasks[0].get('name', 'N/A')}")
        print()


# =============================================================================
# DEMO 6: Contrast with Fragmented Approach
# =============================================================================
def demo_fragmented_contrast():
    """Show what the fragmented approach would look like."""
    print("\n" + "=" * 60)
    print("DEMO 6: Contrast with Fragmented Storage Approach")
    print("=" * 60)
    
    print(""""
    With a FRAGMENTED approach, the same queries require:
    
    ┌─────────────────────────────────────────────────────────────────┐
    │ Step 1: Find similar examples in vector DB (Pinecone/Weaviate)  │
    │         → Returns record IDs                                     │
    │         → 5 KU per query                                        │
    └─────────────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │ Step 2: Fetch metadata from PostgreSQL                           │
    │         → SELECT * FROM examples WHERE id IN (...)               │
    │         → Filter by label_confidence, user_feedback              │
    │         → 3+ JOINs for source_doc, task, category tables         │
    └─────────────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │ Step 3: Get source document content from S3                     │
    │         → Download raw text for context                          │
    │         → Must maintain ID mapping between systems              │
    └─────────────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │ Step 4: Sync issues when data changes                            │
    │         → Embeddings drift when examples update                  │
    │         → Metadata sync failures cause inconsistencies          │
    └─────────────────────────────────────────────────────────────────┘
    
    TOTAL: 4 systems, 4 API calls, manual sync, multiple failure points
    
    ─────────────────────────────────────────────────────────────────
    
    With RUSHDB, the same query is:
    
    ┌─────────────────────────────────────────────────────────────────┐
    │ db.ai.search({                                                    │
    │     propertyName="instruction",                                    │
    │     query="password reset",                                       │
    │     labels=["TrainingExample"],                                    │
    │     where={                                                        │
    │         "label_confidence": {"$gte": 0.8},                       │
    │         "user_feedback": "accepted"                                │
    │     },                                                            │
    │     limit=10                                                      │
    │ })                                                                │
    └─────────────────────────────────────────────────────────────────┘
    
    TOTAL: 1 system, 1 API call, automatic sync, no drift
    """)


# =============================================================================
# MAIN
# =============================================================================
def main():
    """Run all demonstrations."""
    print("\n" + "#" * 60)
    print("# RUSHDB FOR RETRIEVAL-AUGMENTED FINE-TUNING")
    print("# Storing and Querying Training Examples")
    print("#" * 60)
    
    # Check if data exists
    examples = db.records.find({"labels": ["TrainingExample"], "limit": 1})
    if not examples:
        print("\n⚠️  No training examples found.")
        print("   Run `python seed.py` first to populate the database.")
        return
    
    # Run demos
    try:
        demo_semantic_search()
        demo_graph_traversal()
        demo_combined_query()
        demo_batch_retrieval()
        demo_relationship_traversal()
        demo_fragmented_contrast()
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        print("   Make sure your RUSHDB_API_KEY is correct and you have seeded data.")
        raise
    
    print("\n" + "#" * 60)
    print("# DEMO COMPLETE")
    print("#" * 60)
    print("\n📚 Next steps:")
    print("   1. Read README.md for detailed documentation")
    print("   2. Adapt patterns to your fine-tuning pipeline")
    print("   3. Check docs.rushdb.com for API reference")
    print()


if __name__ == "__main__":
    main()
