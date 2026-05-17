#!/usr/bin/env python3
"""
End-to-end document-to-knowledge-graph pipeline with RushDB.

This script demonstrates:
1. Ingesting documents with inline vector embeddings
2. Creating managed vector indexes
3. Semantic similarity search
4. Multi-hop graph traversal
5. In-place reindexing after content updates
"""

import os
import sys
import time
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rushdb import RushDB

# =============================================================================
# CONFIGURATION
# =============================================================================

api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)

# =============================================================================
# PHASE 1: SETUP - Ensure documents are seeded
# =============================================================================

def run_seed_if_needed():
    """Check if data exists, run seed if not."""
    existing = db.records.find({
        "labels": ["SOURCE"],
        "where": {"name": "research-papers-2024"}
    })
    
    if existing.total == 0:
        print("\n⚠ No data found. Running seed script first...")
        os.system(f"{sys.executable} {Path(__file__).parent}/seed.py")
        print("✓ Seed complete. Continuing with main pipeline.\n")
    else:
        print("✓ Data already seeded. Skipping seed.")


# =============================================================================
# PHASE 2: VECTOR INDEX SETUP
# =============================================================================

def create_vector_index():
    """Create a managed vector index on DOCUMENT.content."""
    print("\n=== PHASE 2: Vector Index Setup ===")
    
    # Check for existing index
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        if idx["label"] == "DOCUMENT" and idx["propertyName"] == "content":
            print(f"✓ Index already exists on DOCUMENT.content")
            return idx
    
    # Create new managed index
    print("  Creating managed index on DOCUMENT.content...")
    index = db.ai.indexes.create({
        "label": "DOCUMENT",
        "propertyName": "content",
        "sourceType": "managed"
    })
    
    print(f"  ✓ Created managed index (model: rushdb-embed-768)")
    
    # Wait for indexing to complete
    print("  Waiting for initial indexing...")
    time.sleep(10)  # Allow time for server to embed and index
    
    # Check stats
    stats = db.ai.indexes.stats(index.data["__id"])
    indexed = stats.data.get("indexedRecords", 0)
    total = stats.data.get("totalRecords", 0)
    print(f"  ✓ Index stats: {indexed}/{total} records indexed")
    
    return index.data


# =============================================================================
# PHASE 3: SEMANTIC SEARCH
# =============================================================================

def run_semantic_search():
    """Find contextually similar document chunks using vector search."""
    print("\n=== PHASE 3: Semantic Search ===")
    
    queries = [
        {
            "query": "distributed systems consensus",
            "description": "Finding documents about consensus algorithms"
        },
        {
            "query": "machine learning production deployment",
            "description": "Finding ML infrastructure content"
        }
    ]
    
    for q in queries:
        print(f"\n  Query: \"{q['query']}\"")
        print(f"  ({q['description']})")
        
        results = db.ai.search({
            "propertyName": "content",
            "query": q["query"],
            "labels": ["DOCUMENT"],
            "limit": 3
        })
        
        for i, record in enumerate(results.data):
            score = record.score or 0.0
            content = record.data.get("content", "")[:80]
            title = record.data.get("title", record.data.get("id", "Unknown"))
            print(f"    [{score:.2f}] {title}")
            print(f"         \"{content}...\"")
    
    print("\n  ✓ Semantic search complete")


# =============================================================================
# PHASE 4: GRAPH TRAVERSAL
# =============================================================================

def run_graph_traversal():
    """Traverse relationships to find entity connections across documents."""
    print("\n=== PHASE 4: Graph Traversal ===")
    
    # Find all documents authored by Dr. Sarah Chen
    print("\n  Query: Documents authored by 'Dr. Sarah Chen'")
    print("  (Two-hop traversal: ENTITY → AUTHORED → DOCUMENT)")
    
    sara = db.records.find({
        "labels": ["ENTITY"],
        "where": {"name": "Dr. Sarah Chen"}
    })
    
    if sara.total > 0:
        sara_entity = sara.data[0]
        print(f"  Found entity: {sara_entity.data.get('name')} ({sara_entity.data.get('role')})")
        
        # Find documents that have AUTHORED relationship from this entity
        docs_by_sara = db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "$source": {
                    "$id": sara_entity.id
                }
            }
        })
        
        print(f"  Found {docs_by_sara.total} documents")
        
        for doc in docs_by_sara.data:
            print(f"\n    📄 {doc.data.get('title', doc.id)}")
            print(f"       Content: {doc.data.get('content', '')[:100]}...")
            
            # Find entities mentioned in this document
            mentioned = db.records.find({
                "labels": ["ENTITY"],
                "where": {
                    "$target": {
                        "$id": doc.id
                    }
                }
            })
            
            if mentioned.total > 0:
                print(f"       Mentions: {', '.join(e.data.get('name', '') for e in mentioned.data)}")
    
    # Find all documents mentioning "transformer architectures"
    print("\n  ---")
    print("\n  Query: Documents mentioning 'transformer architectures'")
    print("  (Direct relationship traversal: DOCUMENT → MENTIONS → ENTITY)")
    
    transformer = db.records.find({
        "labels": ["ENTITY"],
        "where": {"name": "transformer architectures"}
    })
    
    if transformer.total > 0:
        transformer_entity = transformer.data[0]
        
        # Find documents that mention this entity
        docs_mentioning = db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "$target": {
                    "$id": transformer_entity.id
                }
            }
        })
        
        print(f"  Found {docs_mentioning.total} documents")
        for doc in docs_mentioning.data:
            title = doc.data.get('title', 'Untitled')
            content = doc.data.get('content', '')[:60]
            print(f"    • {title}: \"{content}...\"")
    
    print("\n  ✓ Graph traversal complete")


# =============================================================================
# PHASE 5: REINDEXING DEMO
# =============================================================================

def run_reindex_demo():
    """Demonstrate updating document content and vectors in-place."""
    print("\n=== PHASE 5: Reindexing Demo ===")
    
    # Find a document to update
    print("\n  Finding a document to update...")
    
    result = db.records.find({
        "labels": ["DOCUMENT"],
        "where": {"type": "research_paper"},
        "limit": 1
    })
    
    if result.total == 0:
        print("  ⚠ No documents found to update")
        return
    
    doc = result.data[0]
    original_content = doc.data.get("content", "")
    
    print(f"  Selected: {doc.data.get('title', doc.id)}")
    print(f"  Before: \"{original_content[:60]}...\"")
    
    # Update with new content
    new_content = original_content + " Additionally, recent advances in linear attention have shown promising results for long-context applications."
    
    print("\n  Updating content in-place...")
    db.records.set(
        target=doc,
        label="DOCUMENT",
        data={"content": new_content}
    )
    
    # Fetch updated record
    updated = db.records.findById(doc.id)
    updated_content = updated.data.get("content", "")
    
    print(f"  ✓ Content updated")
    print(f"  After: \"{updated_content[:80]}...\"")
    print("\n  ✓ In-place reindex complete (vectors regenerated by server)")


# =============================================================================
# PHASE 6: ONTOLOGY INSPECTION
# =============================================================================

def inspect_ontology():
    """Show the schema that was auto-created from our documents."""
    print("\n=== PHASE 6: Auto-Generated Ontology ===")
    
    # Get all labels
    labels = db.labels.find()
    print(f"\n  Labels created ({len(labels)}):")
    for label in labels:
        print(f"    • {label.name} ({label.count} records)")
    
    # Get all properties
    props = db.properties.find({"limit": 10}
    )
    print(f"\n  Properties discovered ({len(props.data)} shown):")
    for prop in props.data:
        ptype = prop.data.get("type", "unknown")
        print(f"    • {prop.data.get('name', 'unnamed')} ({ptype})")
    
    print("\n  ✓ Zero-schema: labels and properties auto-created on write")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("RUSHDB: Document-to-Knowledge-Graph Pipeline")
    print("=" * 60)
    
    # Ensure data exists
    run_seed_if_needed()
    
    # Run pipeline phases
    create_vector_index()
    run_semantic_search()
    run_graph_traversal()
    run_reindex_demo()
    inspect_ontology()
    
    print("\n" + "=" * 60)
    print("ALL PHASES COMPLETE")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  • No schema setup required — RushDB auto-creates labels/properties")
    print("  • Documents, vectors, and graph edges live in ONE database")
    print("  • Semantic search works out-of-the-box with managed indexes")
    print("  • Relationship traversal uses simple find() with $source/$target")
    print("  • Reindexing is atomic — update content and vectors together")


if __name__ == "__main__":
    main()
