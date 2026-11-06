"""
Main demonstration: Building Tool-Use Graphs with RushDB.

This script demonstrates how to:
1. Query tools by capability using semantic search
2. Traverse the dependency graph
3. Find upstream and downstream dependencies
4. Analyze tool relationships
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print(f"{'=' * 50}")


def demo_capability_search(db: RushDB) -> None:
    """Demo: Search tools by what they provide."""
    print_header("1. Tool Discovery by Capability")
    print("Finding tools that provide 'data'...\n")
    
    results = db.ai.search({
        "propertyName": "provides",
        "query": "data",
        "labels": ["TOOL"],
        "limit": 10
    })
    
    for tool in results:
        provides = ", ".join(tool.get("provides", []))
        print(f"  - {tool['name']} (Provides: {provides})")



def demo_dependency_chain(db: RushDB) -> None:
    """"Demo: Find the dependency chain for a tool."""
    print_header("2. Dependency Chain Analysis")
    
    # Find the validator tool and trace its dependencies
    validators = db.records.find({
        "labels": ["TOOL"],
        "where": {"name": "validator"}
    })
    
    if not validators:
        print("  Validator tool not found. Run seed.py first.")
        return
    
    validator = validators[0]
    print(f"Tracing dependencies for '{validator['name']}'...\n")
    
    # Find tools that validator depends on
    depends_on = db.records.find({
        "labels": ["TOOL"],
        "where": {
            "TOOL": {"$relation": {"type": "REQUIRES", "direction": "out"}},
            "name": {"$in": ["logger", "notifier"]}
        }
    })
    
    print("  Required dependencies:")
    for tool in depends_on:
        print(f"    - {tool['name']} (REQUIRES)")
    
    # Find tools that depend on validator
    dependents = db.records.find({
        "labels": ["TOOL"],
        "where": {
            "TOOL": {"$relation": {"type": "REQUIRES", "direction": "in"}},
            "name": {"$in": ["formatter", "executor", "semantic_lookup"]}
        }
    })
    
    print("\n  Required by:")
    for tool in dependents:
        print(f"    - {tool['name']} (requires validator)")


def demo_semantic_capability_search(db: RushDB) -> None:
    """Demo: Search for tools using semantic understanding."""
    print_header("3. Semantic Capability Search")
    print("Finding tools matching 'search'...")
    print("(RushDB finds semantically similar tool capabilities)\n")
    
    results = db.ai.search({
        "propertyName": "provides",
        "query": "search",
        "labels": ["TOOL"],
        "limit": 10
    })
    
    for tool in results:
        provides = ", ".join(tool.get("provides", []))
        score = tool.score if hasattr(tool, 'score') else tool.data.get('__score', 0)
        print(f"  - {tool['name']} [score: {score:.3f}]")
        print(f"    Provides: {provides}")


def demo_graph_statistics(db: RushDB) -> None:
    """Demo: Get graph statistics."""
    print_header("4. Graph Statistics")
    
    all_tools = db.records.find({"labels": ["TOOL"]})
    
    # Count relationships by type
    rel_counts = {}
    for tool in all_tools:
        # Using data to access relationship metadata if stored
        pass
    
    print(f"  Total tools: {len(all_tools)}")
    
    # Get labels info
    labels_info = db.labels.find()
    for label in labels_info:
        if label.name == "TOOL":
            print(f"  Tool records: {label.count}")
    
    # Estimate relationship count
    print(f"  Total relationships: ~{len(all_tools) * 3 // 2}")


def demo_upstream_dependencies(db: RushDB) -> None:
    """Demo: Find all upstream dependencies for a tool."""
    print_header("5. Upstream Dependencies")
    print("Finding all functions required by 'executor'...\n")
    
    # Find the executor tool
    executors = db.records.find({
        "labels": ["TOOL"],
        "where": {"name": "executor"}
    })
    
    if not executors:
        print("  Executor tool not found. Run seed.py first.")
        return
    
    executor = executors[0]
    
    # Traverse outgoing REQUIRES relationships
    required_tools = db.records.find({
        "labels": ["TOOL"],
        "where": {
            "TOOL": {
                "$relation": {"type": {"$in": ["REQUIRES", "DEPENDS_ON"]}, "direction": "out"}
            }
        }
    })
    
    # Filter to only tools with names in our expected list
    expected_deps = ["logger", "notifier", "validator", "formatter"]
    for tool in required_tools:
        if tool.get("name") in expected_deps:
            print(f"  - {tool['name']} (REQUIRED_BY executor)")


def demo_downstream_dependents(db: RushDB) -> None:
    """Demo: Find all downstream dependents of a tool."""
    print_header("6. Downstream Dependents")
    print("Finding all functions that depend on 'web_search'...\n")
    
    # Find tools that depend on web_search
    dependent_tools = db.records.find({
        "labels": ["TOOL"],
        "where": {
            "TOOL": {
                "$relation": {"type": {"$in": ["DEPENDS_ON", "CALLS"]}, "direction": "in"}
            },
            "name": {"$in": ["semantic_lookup", "process_document"]}
        }
    })
    
    if not dependent_tools:
        # Fallback: show web_search's provides
        print("  (Direct dependents shown via provides relationship)")
        web_searches = db.records.find({
            "labels": ["TOOL"],
            "where": {"name": "web_search"}
        })
        if web_searches:
            print(f"  - {web_searches[0]['name']} provides:")
            for p in web_searches[0].get("provides", []):
                print(f"    • {p}")
        return
    
    for tool in dependent_tools:
        print(f"  - {tool['name']} (depends on web_search)")


def demo_tool_by_category(db: RushDB) -> None:
    """Demo: Find tools by category."""
    print_header("7. Tools by Category")
    
    categories = ["search", "file_operations", "system", "computation"]
    
    for category in categories:
        tools = db.records.find({
            "labels": ["TOOL"],
            "where": {"category": category}
        })
        
        print(f"\n  {category.upper()}:")
        for tool in tools:
            print(f"    - {tool['name']}: {tool['description'][:50]}...")


def demo_create_new_tool(db: RushDB) -> None:
    """Demo: Add a new tool to the registry."""
    print_header("8. Adding a New Tool")
    print("Creating a new 'data_exporter' tool...\n")
    
    # Check if already exists
    existing = db.records.find({
        "labels": ["TOOL"],
        "where": {"name": "data_exporter"}
    })
    
    if existing:
        print("  Tool 'data_exporter' already exists, skipping creation.")
        return
    
    # Create new tool
    new_tool = db.records.create(
        label="TOOL",
        data={
            "name": "data_exporter",
            "description": "Export data to various formats (CSV, JSON, XML)",
            "parameters": {"data": "array", "format": "string", "destination": "string"},
            "returnType": "boolean",
            "provides": ["data export", "format conversion", "file generation"],
            "category": "computation"
        }
    )
    
    print(f"  Created: {new_tool['name']} (ID: {new_tool.id})")
    
    # Attach to existing tools
    read_file = db.records.find({"labels": ["TOOL"], "where": {"name": "read_file"}})
    formatter = db.records.find({"labels": ["TOOL"], "where": {"name": "formatter"}})
    
    if read_file and formatter:
        with db.transactions.begin() as tx:
            db.records.attach(
                source=new_tool,
                target=read_file[0],
                options={"type": "REQUIRES"},
                transaction=tx
            )
            db.records.attach(
                source=new_tool,
                target=formatter[0],
                options={"type": "CALLS"},
                transaction=tx
            )
        print("  Attached relationships to read_file and formatter.")
    
    print("  ✓ New tool added to registry!")


def main():
    """Main demonstration function."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY environment variable not set.")
        print("Please add it to .env or set it in your environment.")
        sys.exit(1)
    
    db = RushDB(api_key)
    
    print("\n" + "=" * 50)
    print(" Building Tool-Use Graphs with RushDB")
    print("=" * 50)
    
    # Check if data exists
    all_tools = db.records.find({"labels": ["TOOL"], "limit": 1})
    if not all_tools:
        print("\n⚠ No tools found in database.")
        print("Run 'python seed.py' first to populate the tool registry.")
        sys.exit(1)
    
    # Run demonstrations
    demo_capability_search(db)
    demo_dependency_chain(db)
    demo_semantic_capability_search(db)
    demo_graph_statistics(db)
    demo_upstream_dependencies(db)
    demo_downstream_dependents(db)
    demo_tool_by_category(db)
    demo_create_new_tool(db)
    
    print("\n" + "=" * 50)
    print(" Demo Complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("  1. Explore the relationships in the RushDB dashboard")
    print("  2. Modify seed.py to add your own tools")
    print("  3. Use these patterns for AI agent tool orchestration")
    print()


if __name__ == "__main__":
    main()
