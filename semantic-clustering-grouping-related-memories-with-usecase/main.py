#!/usr/bin/env python3
"""
Semantic Memory Cluster Demo

This script demonstrates RushDB's hybrid graph + vector search capabilities
for building a contextual memory assistant.

The scenario: A developer is working on "Refactor auth service" and needs
to recall relevant context from past work.

This script shows:
1. Graph traversal for explicit relationships
2. Vector search for semantic similarity
3. Combined approach for complete context

Usage: python main.py
"""

import os
import sys

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("❌ Error: RUSHDB_API_KEY not found in environment")
    print("   Copy .env.example to .env and add your API key")
    print("   Then run: python seed.py")
    sys.exit(1)

db = RushDB(API_KEY)


def print_header(title: str):
    """Print a section header with formatting."""
    print(f"\n{'═' * 70}")
    print(f"   {title}")
    print(f"{'═' * 70}")


def print_subheader(title: str):
    """Print a subsection header."""
    print(f"\n  📊 {title}")
    print(f"  {'─' * 50}")


def format_record(record, indent: int = 4) -> str:
    """Format a record for display."""
    label = record.label
    data = record.fields or record.data
    title = data.get("title", data.get("name", "Unknown"))
    
    prefix = " " * indent
    return f"{prefix}• [{label}] {title}"


def find_graph_relationships(current_task_title: str):
    """
    Find explicit graph relationships for the current task.
    
    This uses RushDB's graph traversal to find:
    - Tasks that block/are blocked by the current task
    - Decisions that informed or relate to the task
    - Related refactors and learnings
    """
    print("\n  Looking for graph relationships...")
    
    # Find the current task
    current_tasks = db.records.find({
        "labels": ["TASK"],
        "where": {"title": {"$contains": "Auth Service Refactoring"}}
    })
    
    if not current_tasks:
        print("  ⚠️  No task found. Run 'python seed.py' first.")
        return [], None
    
    current_task = current_tasks[0]
    print(f"  ✓ Found current task: {current_task.fields.get('title')}")
    
    # Find all related records via graph traversal
    # Using where clause to find related records
    related_records = []
    
    # Find tasks that are blocked by this one
    blocked_tasks = db.records.find({
        "labels": ["TASK"],
        "where": {
            "TASK": {
                "$relation": {"type": "BLOCKED_BY", "direction": "in"},
                "title": {"$contains": "Auth Service Refactoring"}
            }
        }
    })
    
    for task in blocked_tasks:
        task.data["_relation_type"] = "BLOCKS"
        task.data["_related_to"] = current_task.fields.get('title')
        related_records.append(task)
    
    # Find decisions that inform this task
    informed_by = db.records.find({
        "labels": ["DECISION"],
        "where": {
            "$or": [
                {
                    "TASK": {
                        "$relation": {"type": "INFORMED_BY", "direction": "in"},
                        "title": {"$contains": "Auth Service Refactoring"}
                    }
                },
                {
                    "TASK": {
                        "$relation": {"type": "RELATES_TO", "direction": "in"},
                        "title": {"$contains": "Auth Service Refactoring"}
                    }
                }
            ]
        }
    })
    
    for decision in informed_by:
        decision.data["_relation_type"] = "RELATES_TO"
        decision.data["_related_to"] = current_task.fields.get('title')
        related_records.append(decision)
    
    # Find parent tasks
    parent_tasks = db.records.find({
        "labels": ["TASK"],
        "where": {
            "TASK": {
                "$relation": {"type": "PARENT_OF", "direction": "in"},
                "title": {"$contains": "Auth Service Refactoring"}
            }
        }
    })
    
    for task in parent_tasks:
        task.data["_relation_type"] = "PARENT_OF"
        task.data["_related_to"] = current_task.fields.get('title')
        related_records.append(task)
    
    # Also find related refactors
    related_refactors = db.records.find({
        "labels": ["REFACTOR"],
        "where": {
            "REFACTOR": {
                "$relation": {"type": "RELATES_TO", "direction": "in"},
                "title": {"$contains": "Auth Service"}
            },
            "$or": [
                {"TASK": {"title": {"$contains": "Auth Service Refactoring"}}}
            ]
        }
    })
    
    for refactor in related_refactors:
        refactor.data["_relation_type"] = "RELATES_TO"
        refactor.data["_related_to"] = current_task.fields.get('title')
        related_records.append(refactor)
    
    return related_records, current_task


def find_semantic_similarity(current_task: object):
    """
    Find semantically similar memories using vector search.
    
    This uses RushDB's AI search to find:
    - Past refactors with similar content
    - Discussions about similar problems
    - Decisions about similar architectural changes
    """
    print("\n  Performing vector similarity search...")
    
    # Extract search terms from current task
    search_query = "auth service refactoring jwt token migration middleware authentication"
    
    try:
        # Search for similar content across all memory types
        similar = db.ai.search({
            "propertyName": "content",
            "query": search_query,
            "labels": ["DECISION", "REFACTOR", "BUG", "LEARNING", "TASK"],
            "limit": 6
        })
        
        results = similar.data if hasattr(similar, 'data') else []
        print(f"  ✓ Found {len(results)} semantically similar records")
        
        return results
        
    except Exception as e:
        # Vector search might fail if index doesn't exist yet
        # Fall back to text search
        print(f"  ⚠️  Vector search not available: {str(e)[:50]}")
        print("  Falling back to text-based search...")
        
        return db.records.find({
            "labels": ["DECISION", "REFACTOR", "BUG", "LEARNING"],
            "where": {
                "$or": [
                    {"content": {"$contains": "auth"}},
                    {"content": {"$contains": "JWT"}},
                    {"content": {"$contains": "token"}},
                    {"content": {"$contains": "refactor"}}
                ]
            },
            "limit": 5
        })


def build_context_cluster(current_task: object, graph_relations: list, similar: list):
    """
    Build a complete context cluster combining both approaches.
    
    This demonstrates the key insight: graph traversal finds explicit
    relationships, while vector search finds implicit semantic connections.
    Together, they provide a complete picture.
    """
    print("\n  Building complete context cluster...")
    
    cluster = {
        "current_task": current_task,
        "graph_path": [],      # From explicit relationships
        "vector_proximity": [], # From semantic similarity
        "combined": []         # Union of both
    }
    
    # Add graph relationships
    for record in graph_relations:
        cluster["graph_path"].append({
            "record": record,
            "relation_type": record.data.get("_relation_type", "RELATED"),
            "source": "graph"
        })
    
    # Add vector similarity results
    for record in similar:
        # Avoid duplicates from graph search
        existing_ids = [r["record"].id for r in cluster["graph_path"]]
        if record.id not in existing_ids:
            score = record.score if hasattr(record, 'score') else 0.0
            cluster["vector_proximity"].append({
                "record": record,
                "score": score,
                "source": "vector"
            })
    
    # Combine into unified cluster
    for item in cluster["graph_path"]:
        cluster["combined"].append({
            **item,
            "combined_reason": f"Graph: {item['relation_type']}"
        })
    
    for item in cluster["vector_proximity"]:
        cluster["combined"].append({
            **item,
            "combined_reason": f"Vector similarity: {item['score']:.3f}"
        })
    
    return cluster


def display_results(cluster: dict):
    """Display the complete context cluster with formatting."""
    print_header("SEMANTIC MEMORY CLUSTER: Auth Service Refactoring")
    
    current = cluster["current_task"]
    print(f"\n  📍 Current context: {current.fields.get('title', 'Unknown')}")
    print(f"     Status: {current.fields.get('status', 'unknown')}")
    print(f"     Priority: {current.fields.get('priority', 'unknown')}")
    
    # Graph relationships section
    print_subheader("GRAPH RELATIONSHIPS (Explicit)")
    
    if cluster["graph_path"]:
        for item in cluster["graph_path"]:
            record = item["record"]
            rel_type = item["relation_type"]
            title = record.fields.get("title", record.id)
            label = record.label
            print(f"    └─ [{rel_type}] [{label}] {title[:50]}")
    else:
        print("    (No direct graph relationships found)")
    
    # Vector similarity section
    print_subheader("VECTOR SIMILARITY (Semantic)")
    
    if cluster["vector_proximity"]:
        for i, item in enumerate(cluster["vector_proximity"], 1):
            record = item["record"]
            score = item["score"]
            title = record.fields.get("title", record.data.get("title", record.id))
            label = record.label
            print(f"    {i}. [{score:.3f}] [{label}] {title[:45]}")
    else:
        print("    (No semantically similar records found)")
    
    # Combined view
    print_subheader("COMPLETE CONTEXT CLUSTER")
    print("    (All relevant memories, sorted by relevance)")
    print()
    
    if cluster["combined"]:
        for item in cluster["combined"]:
            record = item["record"]
            title = record.fields.get("title", record.id)
            label = record.label
            
            if item["source"] == "graph":
                reason = item["relation_type"]
                print(f"    🔗 (Graph) [{label}] {title[:40]}")
                print(f"        └─ via {reason}")
            else:
                score = item.get("score", 0.0)
                print(f"    🔍 (Vector) [{label}] {title[:40]}")
                print(f"        └─ similarity: {score:.3f}")
            print()
    
    # Key insight
    print_subheader("KEY INSIGHT")
    print("""
    This demo shows how combining graph traversal with vector search
    provides complete context that neither approach alone can offer:
    
    • Graph traversal finds explicit relationships (blocks, informs)
    • Vector search finds implicit semantic connections (similar patterns)
    • Combined = everything relevant to make informed decisions
    """)


def main():
    """Main entry point for the demo."""
    print("\n" + "=" * 70)
    print("   RUSHDB SEMANTIC MEMORY ASSISTANT")
    print("   Context-aware recall for developer tooling")
    print("=" * 70)
    
    print("\n📍 Scenario: Developer is working on 'Auth Service Refactoring'")
    print("   Need to recall: past decisions, related bugs, similar refactors")
    
    # Step 1: Find graph relationships
    print_header("STEP 1: Graph Traversal")
    print("   Searching explicit relationships in the knowledge graph...")
    graph_relations, current_task = find_graph_relationships(
        "Auth Service Refactoring"
    )
    
    if not current_task:
        print("\n❌ No records found. Please run 'python seed.py' first.")
        sys.exit(1)
    
    print(f"\n   Found {len(graph_relations)} graph relationships")
    
    # Step 2: Find semantic similarity
    print_header("STEP 2: Vector Similarity Search")
    print("   Searching for semantically similar memories...")
    similar_records = find_semantic_similarity(current_task)
    
    # Step 3: Build combined context
    print_header("STEP 3: Context Assembly")
    cluster = build_context_cluster(
        current_task,
        graph_relations,
        similar_records
    )
    
    # Display final results
    display_results(cluster)
    
    print("\n" + "=" * 70)
    print("   Demo complete! Run 'python seed.py' to reset data.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
