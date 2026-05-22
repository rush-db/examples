#!/usr/bin/env python3
"""
Graph-Based Tool Selection: How Agents Decide Which Capabilities to Use

This example demonstrates using RushDB as a knowledge graph backend for AI agent
tool selection. Instead of hardcoded if/else logic, agents query the graph to find
the right tools based on capabilities, dependencies, and semantic intent matching.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB

# Initialize embedding model (MiniLM-L6-v2 - fast and efficient)
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')


def setup_vector_index(db: RushDB) -> str:
    """
    One-time setup: Create vector index for semantic tool search.
    """
    print("=== SETUP: Creating Vector Index ===\n")
    
    # Check if index already exists
    indexes = db.ai.indexes.find().data
    for idx in indexes:
        if idx["label"] == "TOOL" and idx["propertyName"] == "description":
            print(f"Index already exists: {idx['__id']}")
            return idx["__id"]
    
    # Create index for tool descriptions
    index = db.ai.indexes.create({
        "label": "TOOL",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    
    print(f"Created index: {index.data['__id']}")
    return index.data["__id"]


def compute_and_index_vectors(db: RushDB, index_id: str):
    """
    Compute embeddings for all tool descriptions and upsert them.
    """
    print("\n=== SETUP: Computing Tool Embeddings ===\n")
    
    # Get all tools
    tools_result = db.records.find({"labels": ["TOOL"]})
    tools = tools_result.data
    
    # Compute embeddings in batch
    descriptions = [tool["description"] for tool in tools]
    embeddings = EMBEDDING_MODEL.encode(descriptions)
    
    # Prepare upsert data
    items = [
        {
            "recordId": tool["__id"],
            "vector": embeddings[i].tolist()
        }
        for i, tool in enumerate(tools)
    ]
    
    # Upsert vectors
    db.ai.indexes.upsert_vectors(index_id, {"items": items})
    
    print(f"Indexed {len(items)} tool descriptions")


def semantic_tool_discovery(db: RushDB, goal: str, limit: int = 5):
    """
    Discover tools by semantically matching their descriptions to a user goal.
    Uses vector search to find tools whose documented capabilities best match the intent.
    """
    print(f"\n=== SEMANTIC TOOL DISCOVERY ===")
    print(f'Query: "{goal}"')
    print()
    
    # Compute query embedding
    query_vector = EMBEDDING_MODEL.encode([goal]).tolist()[0]
    
    # Search using query vector
    results = db.ai.search({
        "propertyName": "description",
        "queryVector": query_vector,
        "labels": ["TOOL"],
        "limit": limit
    })
    
    print("Top matching tools:")
    for i, tool in enumerate(results.data, 1):
        score = tool.score if hasattr(tool, 'score') else tool.data.get("__score", 0)
        print(f"  {i}. {tool['name']} (similarity: {score:.3f})")
        print(f"     {tool['description'][:60]}...")
    
    return results.data


def find_tools_by_capabilities(db: RushDB, required_caps: list, match_all: bool = True):
    """
    Find tools that provide specific capabilities.
    Uses graph traversal to filter tools by their linked capability nodes.
    """
    print(f"\n=== CAPABILITY-BASED TOOL FILTERING ===")
    print(f"Required capabilities: {required_caps}")
    print(f"Match mode: {'ALL' if match_all else 'ANY'} capabilities")
    print()
    
    # Get all tools
    all_tools = db.records.find({"labels": ["TOOL"]}).data
    
    matched_tools = []
    for tool in all_tools:
        # Find capabilities this tool provides
        cap_result = db.records.find({
            "labels": ["CAPABILITY"],
            "where": {
                "TOOL": {
                    "$relation": {"type": "ENABLES", "direction": "in"},
                    "name": tool["name"]
                }
            }
        })
        
        tool_caps = [cap["name"] for cap in cap_result.data]
        
        if match_all:
            if all(cap in tool_caps for cap in required_caps):
                matched_tools.append(tool)
                print(f"  ✓ {tool['name']} provides all: {tool_caps}")
        else:
            if any(cap in tool_caps for cap in required_caps):
                matched_tools.append(tool)
                print(f"  ~ {tool['name']} provides some: {tool_caps}")
    
    if not matched_tools:
        print("  No tools match the criteria")
    else:
        print(f"\n  Found {len(matched_tools)} matching tools")
    
    return matched_tools


def resolve_dependencies(db: RushDB, tool_name: str, transitive: bool = False):
    """
    Resolve dependencies for a tool.
    Traverses DEPENDS_ON relationships to find all required tools.
    """
    print(f"\n=== DEPENDENCY RESOLUTION ===")
    print(f"Tool: {tool_name}")
    print(f"Mode: {'Transitive closure' if transitive else 'Direct only'}")
    print()
    
    # Find the tool record
    tool_result = db.records.find({
        "labels": ["TOOL"],
        "where": {"name": tool_name}
    })
    
    if not tool_result.data:
        print(f"  Tool '{tool_name}' not found")
        return []
    
    tool = tool_result.data[0]
    
    def get_direct_deps(t: dict) -> list:
        """Get direct dependencies of a tool."""
        deps_result = db.records.find({
            "labels": ["TOOL"],
            "where": {
                "TOOL": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "out"},
                    "name": t["name"]
                }
            }
        })
        return deps_result.data
    
    def get_all_deps_reursive(t: dict, visited: set) -> list:
        """Get all transitive dependencies."""
        deps = []
        direct = get_direct_deps(t)
        
        for dep in direct:
            if dep["__id"] not in visited:
                visited.add(dep["__id"])
                deps.append(dep)
                deps.extend(get_all_deps_reursive(dep, visited))
        
        return deps
    
    if transitive:
        visited = {tool["__id"]}
        all_deps = get_all_deps_reursive(tool, visited)
        deps = all_deps
    else:
        deps = get_direct_deps(tool)
    
    print(f"  Direct dependencies ({len(deps)}):")
    for dep in deps:
        print(f"    - {dep['name']} (v{dep['version']})")
    
    if transitive:
        print(f"\n  Transitive dependencies ({len(all_deps)} total):")
        for dep in all_deps:
            print(f"    - {dep['name']}")
    
    return deps


def select_tools_for_goal(db: RushDB, goal: str, required_caps: list):
    """
    High-level tool selection: combines semantic search with capability filtering
    and dependency resolution to find the best toolset for a complex goal.
    """
    print(f"\n=== TOOL SELECTION FOR GOAL ===")
    print(f'Goal: "{goal}"')
    print(f"Required capabilities: {required_caps}")
    print()
    
    # Step 1: Semantic discovery
    semantic_results = semantic_tool_discovery(db, goal, limit=3)
    
    # Step 2: Capability filtering on top results
    top_tool_names = [t["name"] for t in semantic_results[:3]]
    print("\nFiltering top semantic matches by capabilities...")
    
    selected = []
    for tool_name in top_tool_names:
        tool_result = db.records.find({
            "labels": ["TOOL"],
            "where": {"name": tool_name}
        })
        if tool_result.data:
            # Check if tool has required capabilities
            cap_result = db.records.find({
                "labels": ["CAPABILITY"],
                "where": {
                    "TOOL": {
                        "$relation": {"type": "ENABLES", "direction": "in"},
                        "name": tool_name
                    }
                }
            })
            tool_caps = [c["name"] for c in cap_result.data]
            
            if all(cap in tool_caps for cap in required_caps):
                selected.append(tool_result.data[0])
                print(f"  ✓ {tool_name} matches requirements")
            else:
                print(f"  ✗ {tool_name} missing capabilities: {set(required_caps) - set(tool_caps)}")
    
    if not selected:
        print("\n  No perfect match found. Suggesting fallback...")
        # Fallback: find any tool that provides at least some capabilities
        fallback = find_tools_by_capabilities(db, required_caps, match_all=False)
        return fallback[:2]
    
    print(f"\n  Selected tools: {[t['name'] for t in selected]}")
    return selected


def demonstrate_graph_traversal(db: RushDB):
    """
    Demonstrate various graph traversal patterns for tool discovery.
    """
    print("\n=== GRAPH TRAVERSAL PATTERNS ===\n")
    
    # Pattern 1: Find all capabilities and their enabling tools
    print("Pattern 1: Capabilities → Tools (reverse lookup)")
    caps = db.records.find({"labels": ["CAPABILITY"]}).data
    for cap in caps[:3]:
        tools = db.records.find({
            "labels": ["TOOL"],
            "where": {
                "CAPABILITY": {
                    "$relation": {"type": "ENABLES", "direction": "in"},
                    "name": cap["name"]
                }
            }
        })
        tool_names = [t["name"] for t in tools.data]
        print(f"  {cap['name']}: {tool_names or 'No tools'}")
    
    # Pattern 2: Find tools that other tools depend on
    print("\nPattern 2: Find infrastructure tools (no dependencies)")
    all_tools = db.records.find({"labels": ["TOOL"]}).data
    infrastructure_tools = []
    
    for tool in all_tools:
        deps = db.records.find({
            "labels": ["TOOL"],
            "where": {
                "TOOL": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "out"},
                    "name": tool["name"]
                }
            }
        })
        if not deps.data:
            infrastructure_tools.append(tool["name"])
    
    print(f"  Found {len(infrastructure_tools)} infrastructure tools: {infrastructure_tools}")
    
    # Pattern 3: Find tools that need a specific dependency
    print("\nPattern 3: Tools that depend on CacheManager")
    dependent_tools = db.records.find({
        "labels": ["TOOL"],
        "where": {
            "TOOL": {
                "$relation": {"type": "DEPENDS_ON", "direction": "out"},
                "name": "CacheManager"
            }
        }
    })
    print(f"  Found {len(dependent_tools.data)} dependent tools: {[t['name'] for t in dependent_tools.data]}")


def main():
    """Main demonstration function."""
    load_dotenv()
    
    api_token = os.environ.get("RUSHzDB_API_TOKEN")
    if not api_token:
        print("Error: RUSHzDB_API_TOKEN not found in environment")
        print("Copy .env.example to .env and add your token")
        sys.exit(1)
    
    db = RushDB(api_token)
    
    # Check for --setup flag
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print("Running setup mode...")
        setup_vector_index(db)
        
        # Import seed module to seed data
        from seed import seed_tools_and_capabilities, seed_dependencies, create_capability_index
        tool_records = seed_tools_and_capabilities(db)
        seed_dependencies(db, tool_records)
        index_id = create_capability_index(db)
        
        # Compute and index vectors
        compute_and_index_vectors(db, index_id)
        
        print("\n✓ Setup complete!")
        print("Run `python main.py` to see the demonstration.")
        return
    
    # Import and run seed
    from seed import seed_tools_and_capabilities, seed_dependencies, create_capability_index
    tool_records = seed_tools_and_capabilities(db)
    seed_dependencies(db, tool_records)
    index_id = create_capability_index(db)
    
    # Compute vectors if needed
    if tool_records:
        compute_and_index_vectors(db, index_id)
    
    print("\n" + "="*60)
    print("GRAPH-BASED TOOL SELECTION DEMO")
    print("="*60)
    
    # Demo 1: Semantic tool discovery
    semantic_tool_discovery(db, "I need to fetch data from external websites and cache it")
    
    # Demo 2: Capability-based filtering
    find_tools_by_capabilities(db, ["read", "transform", "write"])
    
    # Demo 3: Dependency resolution
    resolve_dependencies(db, "DataPipelineOrchestrator", transitive=True)
    
    # Demo 4: Goal-based tool selection
    select_tools_for_goal(db, "analyze sales data and generate a report", ["compute", "write"])
    
    # Demo 5: Graph traversal patterns
    demonstrate_graph_traversal(db)
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nThis demonstration showed:")
    print("  1. Semantic tool discovery via vector search")
    print("  2. Capability filtering via graph traversal")
    print("  3. Dependency resolution (direct and transitive)")
    print("  4. Goal-based tool selection combining multiple strategies")
    print("  5. Various graph traversal patterns for tool discovery")

    print("\nNext steps:")
    print("  - Try different queries and capability combinations")
    print("  - Add your own tools to the graph")
    print("  - Implement multi-step tool orchestration")


if __name__ == "__main__":
    main()
