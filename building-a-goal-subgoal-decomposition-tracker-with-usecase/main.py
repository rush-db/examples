#!/usr/bin/env python3
"""
Goal-Subgoal Decomposition Tracker with RushDB

This demo showcases RushDB's combined graph and vector capabilities for tracking
goal hierarchies with semantic search. It demonstrates:

1. Graph traversal: Navigate parent-child goal relationships
2. Semantic search: Find related goals even when terminology differs
3. Hybrid queries: Filter graph traversal by semantic similarity
4. Relationship types: Parent-child, prerequisite, and blocking relationships
"""

import os
from dotenv import load_dotenv

from rushdb import RushDB

# Load environment variables
load_dotenv()


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


def print_goal(goal, indent=0):
    """Print a goal with proper formatting and indentation."""
    prefix = "  " * indent
    title = goal.get("title", "Unknown")
    status = goal.get("status", "unknown")
    priority = goal.get("priority", "unknown")
    
    status_icon = {
        "completed": "✓",
        "active": "●",
        "in_progress": "○",
        "pending": "○",
    }.get(status, "○")
    
    print(f"{prefix}{status_icon} {title} [{status}, {priority}]")


def display_goal_hierarchy(db):
    """Display the complete goal hierarchy."""
    print_section("Goal Hierarchy")
    
    # Find top-level goals (level 0) with no parent
    top_level_goals = db.records.find({
        "labels": ["GOAL"],
        "where": {
            "level": 0,
        },
    })
    
    def print_tree(goal, indent=0):
        print_goal(goal, indent)
        # Get direct subgoals
        subgoals = db.records.find({
            "labels": ["GOAL"],
            "where": {
                "GOAL": {
                    "$relation": {"type": "HAS_SUBGOAL", "direction": "in"},
                    "id": goal.get("__id"),
                }
            },
        })
        for subgoal in subgoals.data:
            print_tree(subgoal, indent + 1)
    
    for goal in top_level_goals.data:
        print_tree(goal)
    
    print(f"\nTotal goals: {len(top_level_goals.data)}")


def find_related_goals_semantic(db):
    """Find goals semantically related to a search term."""
    print_section("Semantic Search: Finding Related Goals")
    
    queries = [
        "user authentication and security",
        "database performance",
        "documentation and guides",
    ]
    
    for query in queries:
        print(f"\n🔍 Search: \"{query}\"")
        results = db.ai.search({
            "propertyName": "description",
            "query": query,
            "labels": ["GOAL"],
            "limit": 5,
        })
        
        for i, goal in enumerate(results.data, 1):
            score = goal.get("__score", 0.0) or 0.0
            print(f"  {i}. {goal.get('title')} (similarity: {score:.3f})")


def traverse_prerequisite_chain(db):
    """Traverse the prerequisite chain for a specific goal."""
    print_section("Prerequisite Chain Traversal")
    
    # Find the billing integration goal
    billing_goal = db.records.find({
        "labels": ["GOAL"],
        "where": {
            "title": {"$contains": "billing"},
        },
    })
    
    if not billing_goal.data:
        print("No billing goal found")
        return
    
    goal = billing_goal.data[0]
    print(f"\n📋 Goal: {goal.get('title')}")
    print("Dependencies:")
    
    # Find all prerequisites of this goal
    prerequisites = db.records.find({
        "labels": ["GOAL"],
        "where": {
            "GOAL": {
                "$relation": {"type": "PREREQUISITE", "direction": "in"},
                "id": goal.get("__id"),
            }
        },
    })
    
    for prereq in prerequisites.data:
        print(f"  → {prereq.get('title')} [{prereq.get('status')}]")


def find_blocked_goals(db):
    """Find goals that are blocked by others."""
    print_section("Blocked Goals Analysis")
    
    # Find all goals with outgoing BLOCKS relationships
    blocked_candidates = db.records.find({
        "labels": ["GOAL"],
        "where": {
            "status": "in_progress",
        },
    })
    
    print("\nGoals currently in progress and their blockers:")
    
    for goal in blocked_candidates.data:
        # Find what blocks this goal
        blockers = db.records.find({
            "labels": ["GOAL"],
            "where": {
                "GOAL": {
                    "$relation": {"type": "BLOCKS", "direction": "in"},
                    "id": goal.get("__id"),
                }
            },
        })
        
        if blockers.data:
            print(f"\n  {goal.get('title')}")
            print("  Blocked by:")
            for blocker in blockers.data:
                print(f"    - {blocker.get('title')} [{blocker.get('status')}]")


def hybrid_graph_vector_query(db):
    """Demonstrate combining graph traversal with semantic filtering."""
    print_section("Hybrid Query: Graph + Semantic Search")
    
    print("\nFinding HIGH priority goals related to 'security' within the architecture subtree")
    
    # First, find the architecture goal
    arch_goals = db.records.find({
        "labels": ["GOAL"],
        "where": {
            "title": {"$contains": "architecture"},
        },
    })
    
    if not arch_goals.data:
        print("Architecture goal not found")
        return
    
    arch_goal = arch_goals.data[0]
    
    # Get all subgoals of architecture
    subgoals = db.records.find({
        "labels": ["GOAL"],
        "where": {
            "GOAL": {
                "$relation": {"type": "HAS_SUBGOAL", "direction": "in"},
                "id": arch_goal.get("__id"),
            },
            "priority": "high",
        },
    })
    
    print(f"\nHigh-priority subgoals under '{arch_goal.get('title')}':")
    for subgoal in subgoals.data:
        print(f"  → {subgoal.get('title')} [{subgoal.get('status')}]")
    
    # Now find semantically related goals within this subset
    print("\nAmong these, finding goals semantically related to 'security':")
    
    related = db.ai.search({
        "propertyName": "description",
        "query": "security",
        "labels": ["GOAL"],
        "where": {
            "priority": "high",
        },
        "limit": 10,
    })
    
    for result in related.data:
        print(f"  → {result.get('title')} (similarity: {result.get('__score', 0):.3f})")


def demonstrate_relationship_types(db):
    """Show all relationship types in the goal graph."""
    print_section("Relationship Types Summary")
    
    # Count HAS_SUBGOAL relationships
    parent_goals = db.records.find({"labels": ["GOAL"], "where": {"level": 0}})
    
    total_subgoals = 0
    for goal in parent_goals.data:
        children = db.records.find({
            "labels": ["GOAL"],
            "where": {
                "GOAL": {
                    "$relation": {"type": "HAS_SUBGOAL", "direction": "in"},
                    "id": goal.get("__id"),
                }
            },
        })
        total_subgoals += len(children.data)
    
    print(f"\n📊 Relationship Statistics:")
    print(f"  • HAS_SUBGOAL (parent-child): {total_subgoals}")
    print(f"  • PREREQUISITE (dependencies): See prerequisite chain demo")
    print(f"  • BLOCKS (blocking relationships): See blocked goals demo")
    
    print("\n💡 RushDB stores graph edges and vector embeddings in the same record.")
    print("   No joins between separate graph and vector systems needed.")


def main():
    """Main demo function."""
    # Get API key from environment
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not set in environment")
        print("Copy .env.example to .env and add your API key")
        return
    
    # Optional custom URL
    url = os.getenv("RUSHDB_URL") or None
    
    # Initialize RushDB client
    print("\n" + "=" * 60)
    print(" Goal-Subgoal Decomposition Tracker with RushDB")
    print("=" * 60)
    
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    
    # Check for data
    existing = db.records.find({"labels": ["GOAL"], "limit": 1})
    if not existing.data:
        print("\nNo goal data found.")
        print("Run `python seed.py` first to populate the database.")
        return
    
    # Run demonstrations
    display_goal_hierarchy(db)
    find_related_goals_semantic(db)
    traverse_prerequisite_chain(db)
    find_blocked_goals(db)
    hybrid_graph_vector_query(db)
    demonstrate_relationship_types(db)
    
    print("\n" + "=" * 60)
    print(" Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
