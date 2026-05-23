#!/usr/bin/env python3
"""
RushDB SDK Tutorial: Vector Search + Graph Query Integration

This script demonstrates core RushDB capabilities:
1. Vector search (semantic similarity)
2. Graph relationships (authors, categories, articles)
3. Hybrid queries (vector + graph traversal)
4. Transaction patterns

Run this after seed.py to see the full tutorial in action.

Usage:
    python main.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_step(num: int, description: str):
    """Print a numbered step."""
    print(f"\n[Step {num}] {description}")


# ============================================================================
# SECTION 1: Initialization and Connection
# ============================================================================

def initialize_client():
    """Initialize RushDB client and verify connection."""
    print_section("Initializing RushDB Client")
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)
    
    url = os.getenv("RUSHDB_URL")
    
    # Initialize client (cloud or self-hosted)
    if url:
        db = RushDB(api_key, url=url)
        print(f"✓ Connected to self-hosted instance: {url}")
    else:
        db = RushDB(api_key)
        print("✓ Connected to RushDB Cloud")
    
    # Verify connection by querying labels
    labels = db.labels.find()
    print(f"✓ Connection verified - {len(labels)} labels found")
    
    return db


# ============================================================================
# SECTION 2: Graph Query - Traversal via Related Records
# ============================================================================

def demonstrate_graph_queries(db: RushDB):
    """Demonstrate graph traversal - finding records by related record properties."""
    print_section("Graph Query: Traversal via Related Records")
    
    print("\nGraph queries use the related record's LABEL as the key in 'where' clause.")
    print("This allows filtering by properties of connected records.")
    
    # Demo: Find all articles written by authors who specialize in AI
    print_step(1, "Find articles by authors with AI expertise")
    
    ai_articles = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "AUTHOR": {
                "$relation": {"type": "EXPERTISE_IN", "direction": "out"},
            },
            "CATEGORY": {"name": "AI"}
        },
        "limit": 5
    })
    
    print(f"\n  Found {len(ai_articles.data)} AI articles by expert authors:")
    for article in ai_articles.data:
        author_name = article.data.get("author_name", "Unknown")
        print(f"  • {article.data.get('title', 'Untitled')} ({author_name})")
    
    # Demo: Find all articles in the AI category
    print_step(2, "Find articles in specific category (AI)")
    
    ai_category_articles = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "CATEGORY": {
                "name": "AI",
                "$relation": {"type": "BELONGS_TO", "direction": "in"}
            }
        },
        "limit": 10
    })
    
    print(f"\n  Found {len(ai_category_articles.data)} articles in AI category:")
    for article in ai_category_articles.data:
        print(f"  • {article.data.get('title', 'Untitled')}")
    
    # Demo: Find authors who write about DevOps
    print_step(3, "Find authors who write about DevOps")
    
    devops_authors = db.records.find({
        "labels": ["AUTHOR"],
        "where": {
            "CATEGORY": {
                "name": "DevOps",
                "$relation": {"type": "EXPERTISE_IN", "direction": "out"}
            }
        }
    })
    
    print(f"\n  Found {len(devops_authors.data)} authors with DevOps expertise:")
    for author in devops_authors.data:
        expertise = author.data.get("expertise", [])
        print(f"  • {author.data.get('name', 'Unknown')} (expertise: {', '.join(expertise)})")


# ============================================================================
# SECTION 3: Vector Search - Semantic Similarity
# ============================================================================

def demonstrate_vector_search(db: RushDB):
    """Demonstrate semantic search using vector similarity."""
    print_section("Vector Search: Semantic Similarity")
    
    print("\nVector search finds records by meaning, not just keywords.")
    print("RushDB generates embeddings for indexed properties and compares cosine similarity.")
    
    # Demo: Semantic search for "machine learning applications"
    print_step(1, "Semantic search: 'machine learning applications'")
    
    query = "machine learning applications"
    results = db.ai.search({
        "propertyName": "content",
        "query": query,
        "labels": ["ARTICLE"],
        "limit": 5
    })
    
    print(f"\n  Top 5 results for '{query}':")
    for result in results.data:
        score = result.score if hasattr(result, 'score') else result.data.get('__score', 0)
        title = result.data.get('title', 'Untitled')
        print(f"  [{score:.3f}] {title}")
    
    # Demo: Search for "web performance and speed optimization"
    print_step(2, "Semantic search: 'web performance and speed optimization'")
    
    query2 = "web performance and speed optimization"
    results2 = db.ai.search({
        "propertyName": "content",
        "query": query2,
        "labels": ["ARTICLE"],
        "limit": 3
    })
    
    print(f"\n  Top 3 results for '{query2}':")
    for result in results2.data:
        score = result.score if hasattr(result, 'score') else result.data.get('__score', 0)
        title = result.data.get('title', 'Untitled')
        print(f"  [{score:.3f}] {title}")
    
    # Demo: Search for "container orchestration and deployment"
    print_step(3, "Semantic search: 'container orchestration and deployment'")
    
    query3 = "container orchestration and deployment"
    results3 = db.ai.search({
        "propertyName": "content",
        "query": query3,
        "labels": ["ARTICLE"],
        "limit": 3
    })
    
    print(f"\n  Top 3 results for '{query3}':")
    for result in results3.data:
        score = result.score if hasattr(result, 'score') else result.data.get('__score', 0)
        title = result.data.get('title', 'Untitled')
        print(f"  [{score:.3f}] {title}")


# ============================================================================
# SECTION 4: Hybrid Queries - Vector + Graph
# ============================================================================

def demonstrate_hybrid_queries(db: RushDB):
    """Demonstrate combining vector search with graph traversal."""
    print_section("Hybrid Query: Vector Search + Graph Traversal")
    
    print("\nHybrid queries combine semantic similarity with relationship-based filtering.")
    print("Example: Find relevant AI articles written by authors with AI expertise.")
    
    # Demo: Find AI articles by expert authors with high relevance
    print_step(1, "Find high-relevance AI articles by expert authors")
    
    query = "neural networks and deep learning"
    
    # First, get all AI articles by expert authors via graph query
    ai_expert_articles = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "AUTHOR": {
                "$relation": {"type": "EXPERTISE_IN", "direction": "out"}
            },
            "CATEGORY": {"name": "AI"}
        },
        "limit": 10
    })
    
    print(f"\n  Found {len(ai_expert_articles.data)} AI articles by expert authors")
    
    # Then perform vector search on filtered results
    if ai_expert_articles.data:
        article_ids = [a.id for a in ai_expert_articles.data]
        
        # Vector search within AI category
        vector_results = db.ai.search({
            "propertyName": "content",
            "query": query,
            "labels": ["ARTICLE"],
            "limit": 5
        })
        
        print(f"\n  Vector search results for '{query}':")
        for result in vector_results.data:
            score = result.score if hasattr(result, 'score') else 0
            title = result.data.get('title', 'Untitled')
            author = result.data.get('author_name', 'Unknown')
            print(f"  [{score:.3f}] {title} - by {author}")
    
    # Demo: Find Backend articles about optimization
    print_step(2, "Find Backend articles about optimization")
    
    backend_optimization = db.ai.search({
        "propertyName": "content",
        "query": "database query optimization caching",
        "labels": ["ARTICLE"],
        "where": {
            "CATEGORY": {"name": "Backend"}
        },
        "limit": 5
    })
    
    print(f"\n  Backend articles about optimization:")
    for result in backend_optimization.data:
        score = result.score if hasattr(result, 'score') else 0
        title = result.data.get('title', 'Untitled')
        print(f"  [{score:.3f}] {title}")


# ============================================================================
# SECTION 5: Transactions - Atomic Batch Operations
# ============================================================================

def demonstrate_transactions(db: RushDB):
    """Demonstrate transaction patterns for atomic operations."""
    print_section("Transactions: Atomic Batch Operations")
    
    print("\nTransactions ensure atomicity: all operations succeed or all fail.")
    print("Use context manager (with) for automatic commit/rollback.")
    
    # Demo: Create a new author and their articles atomically
    print_step(1, "Create new author with articles using transaction")
    
    new_author_name = "Tutorial Author"
    
    # Check if author already exists
    existing = db.records.find({
        "labels": ["AUTHOR"],
        "where": {"name": new_author_name}
    })
    
    if existing.data:
        print(f"  Author '{new_author_name}' already exists, skipping creation")
        return
    
    # Use context manager for automatic commit/rollback
    with db.transactions.begin() as tx:
        # Create author
        author = db.records.create(
            label="AUTHOR",
            data={
                "name": new_author_name,
                "bio": "Demo author created in tutorial",
                "expertise": ["Tutorial"]
            },
            transaction=tx
        )
        print(f"  Created author: {author.data.get('name')}")
        
        # Create two articles
        for i, article_title in enumerate(["Tutorial Article 1", "Tutorial Article 2"]):
            article = db.records.create(
                label="ARTICLE",
                data={
                    "title": article_title,
                    "content": "This is a demo article created during the RushDB tutorial to demonstrate transaction patterns.",
                    "author_name": new_author_name,
                    "is_tutorial": True
                },
                transaction=tx
            )
            print(f"  Created article: {article.data.get('title')}")
            
            # Attach to author
            db.records.attach(
                source=article,
                target=author,
                options={"type": "WRITTEN_BY", "direction": "out"},
                transaction=tx
            )
        
        # No explicit commit needed - context manager handles it
        print("  Transaction committed automatically")
    
    print("\n  ✓ All operations completed atomically")


# ============================================================================
# SECTION 6: Upsert - Idempotent Create or Update
# ============================================================================

def demonstrate_upsert(db: RushDB):
    """Demonstrate upsert pattern for idempotent operations."""
    print_section("Upsert: Idempotent Create or Update")
    
    print("\nUpsert matches existing records and updates, or creates new if not found.")
    print("Useful for imports, webhooks, and ensuring data consistency.")
    
    # Demo: Upsert a category
    print_step(1, "Upsert category 'Tutorial' (create or update)")
    
    category = db.records.upsert(
        label="CATEGORY",
        data={
            "name": "Tutorial",
            "description": "Articles created during tutorials",
            "updated_at": "2024-01-01"
        },
        options={
            "mergeBy": ["name"],
            "mergeStrategy": "append"
        }
    )
    
    print(f"  Category upserted: {category.data.get('name')} (id: {category.id})")
    
    # Demo: Upsert again - should update, not create duplicate
    print_step(2, "Upsert again to verify update (not duplicate)")
    
    category2 = db.records.upsert(
        label="CATEGORY",
        data={
            "name": "Tutorial",
            "description": "Articles created during tutorials - UPDATED",
            "updated_at": "2024-01-02"
        },
        options={
            "mergeBy": ["name"],
            "mergeStrategy": "append"
        }
    )
    
    print(f"  Category upserted again: {category2.data.get('name')} (id: {category2.id})")
    print(f"  Same record ID: {category.id == category2.id}")


# ============================================================================
# SECTION 7: Record Access Patterns
# ============================================================================

def demonstrate_record_access(db: RushDB):
    """Demonstrate different ways to access record data."""
    print_section("Record Access Patterns")
    
    print("\nRecords expose data through multiple access patterns:")
    
    # Get a sample article
    articles = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    
    if articles.data:
        article = articles.data[0]
        
        print_step(1, "Access record properties")
        
        # Via dict-like access (preferred)
        title = article["title"]
        content = article.get("content", "")[:50] + "..."
        
        print(f"  article['title'] = {title}")
        print(f"  article.get('content', '')[:50] = {content}")
        
        print_step(2, "Access system fields")
        
        # Access via .data dict
        record_id = article.data.get("__id", "")
        label = article.data.get("__label", "")
        
        print(f"  article.id = {article.id}")
        print(f"  article.label = {article.label}")
        print(f"  article.data['__id'] = {record_id}")
        
        print_step(3, "Access vector similarity score")
        
        # Simulate search result score access
        print(f"  article.score = {article.score if hasattr(article, 'score') else 'N/A (not a search result)'}")
        print(f"  article.data.get('__score', 0) = {article.data.get('__score', 0)}")


# ============================================================================
# SECTION 8: Index Management
# ============================================================================

def demonstrate_index_management(db: RushDB):
    """Demonstrate vector index management."""
    print_section("Vector Index Management")
    
    # List all indexes
    print_step(1, "List vector indexes")
    
    indexes = db.ai.indexes.find()
    print(f"\n  Found {len(indexes.data)} vector index(es):")
    
    for idx in indexes.data:
        label = idx.get("label", "unknown")
        prop = idx.get("propertyName", "unknown")
        status = idx.get("status", "unknown")
        print(f"  • {label}.{prop} (status: {status})")
    
    # Get stats for ARTICLE.content index
    print_step(2, "Get index statistics")
    
    for idx in indexes.data:
        if idx.get("label") == "ARTICLE" and idx.get("propertyName") == "content":
            index_id = idx.get("__id")
            stats = db.ai.indexes.stats(index_id)
            
            if stats.data:
                indexed = stats.data.get("indexedRecords", 0)
                total = stats.data.get("totalRecords", 0)
                print(f"\n  Article content index:")
                print(f"  • Indexed records: {indexed}/{total}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the complete RushDB SDK tutorial."""
    print("\n" + "=" * 60)
    print(" RushDB SDK Tutorial: Vector Search + Graph Query")
    print("=" * 60)
    print("\nThis tutorial demonstrates how to combine:")
    print("  • Vector search for semantic similarity")
    print("  • Graph traversal for relationship-based queries")
    print("  • Hybrid queries combining both approaches")
    
    # Initialize
    db = initialize_client()
    
    # Run demonstrations
    demonstrate_graph_queries(db)
    demonstrate_vector_search(db)
    demonstrate_hybrid_queries(db)
    demonstrate_transactions(db)
    demonstrate_upsert(db)
    demonstrate_record_access(db)
    demonstrate_index_management(db)
    
    # Summary
    print_section("Tutorial Complete!")
    print("\nYou've learned how to:")
    print("  ✓ Query records via graph relationships")
    print("  ✓ Perform semantic vector search")
    print("  ✓ Combine vector search with graph traversal")
    print("  ✓ Use transactions for atomic operations")
    print("  ✓ Use upsert for idempotent create/update")
    print("  ✓ Access record data and scores")
    print("  ✓ Manage vector indexes")
    print("\nNext steps:")
    print("  • Read the docs: https://docs.rushdb.com")
    print("  • Check more examples: https://github.com/rush-db/examples")
    print("  • Try RushDB: https://rushdb.com")


if __name__ == "__main__":
    main()
