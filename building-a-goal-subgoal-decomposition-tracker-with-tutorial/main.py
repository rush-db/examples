"""
Goal-Subgoal Decomposition Tracker Tutorial

This tutorial demonstrates RushDB's unified graph+vector model for building
a goal decomposition system that handles:
- Hierarchical task relationships (graph)
- Semantic similarity search (vectors)
- Combined queries traversing relationships AND finding related items

In a traditional architecture, this would require:
- Neo4j (or similar) for graph relationships
- Pinecone/Weaviate (or similar) for vector search
- Sync logic to keep both databases consistent

RushDB provides both capabilities in a single, transactional API.
"""

import os
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
API_TOKEN = os.getenv("RUSHDB_API_TOKEN")
if not API_TOKEN:
    raise ValueError("RUSHDB_API_TOKEN is required. Get one at https://app.rushdb.com")

db = RushDB(API_TOKEN)

# Initialize embedding model (local, no API key needed)
# Using a lightweight model suitable for semantic similarity
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


def generate_embedding(text: str) -> list[float]:
    """Generate a vector embedding for text using sentence-transformers."""
    return embedding_model.encode(text).tolist()


def load_goal_data() -> list[dict]:
    """Load sample goal hierarchy data."""
    data_path = Path(__file__).parent / "goals.json"
    with open(data_path, 'r') as f:
        return json.load(f)


def setup_vector_index():
    """
    Create a vector index for goal descriptions.
    
    RushDB's ai.indexes.create() sets up the vector index on a label's property.
    We use 'external' sourceType because we'll supply our own embeddings.
    """
    print("\n" + "="*60)
    print("STEP 1: Setting Up Vector Index")
    print("="*60)
    
    # Check if index already exists
    existing_indexes = db.ai.indexes.find()
    for idx in existing_indexes.data:
        if idx['label'] == 'GOAL' and idx['propertyName'] == 'description':
            print(f"Vector index already exists: GOAL.description")
            return
    
    # Create index for goal descriptions
    # Dimensions: 384 for all-MiniLM-L6-v2 model
    index = db.ai.indexes.create({
        "label": "GOAL",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    
    print(f"Created vector index: GOAL.description")
    print(f"  Index ID: {index.id}")
    print(f"  Status: {index.data.get('status')}")
    print(f"  Dimensions: 384 (all-MiniLM-L6-v2 model)")


def create_goal_hierarchy(goals_data: list[dict], parent_id: str = None) -> dict[str, any]:
    """
    Recursively create goals with their subgoals.
    
    This demonstrates RushDB's graph model:
    - Each goal is a record with a 'GOAL' label
    - Parent-child relationships are explicit edges (HAS_SUBGOAL)
    - The relationship is directional: parent -> child
    """
    created_goals = {}
    
    for goal_data in goals_data:
        title = goal_data['title']
        description = goal_data['description']
        subgoals_data = goal_data.get('subgoals', [])
        
        # Generate embedding for the description
        embedding = generate_embedding(description)
        
        # Create the goal with inline vector embedding
        # Using vectors= parameter for clean, atomic write
        goal = db.records.create(
            label="GOAL",
            data={
                "title": title,
                "description": description,
                "status": "active"
            },
            vectors=[{"propertyName": "description", "vector": embedding}]
        )
        
        created_goals[title] = goal
        print(f"  Created goal: '{title}'")
        
        # Attach to parent if provided
        if parent_id:
            parent_goal = db.records.find_by_id(parent_id)
            db.records.attach(
                source=parent_goal,
                target=goal,
                options={"type": "HAS_SUBGOAL", "direction": "out"}
            )
            print(f"    ↳ Linked to parent: {parent_goal['title']}")
        
        # Recursively create subgoals
        if subgoals_data:
            for subgoal_data in subgoals_data:
                child_goals = create_goal_hierarchy([subgoal_data], parent_id=goal.id)
                
                # Link nested subgoals to their parent
                for subgoal in child_goals.values():
                    db.records.attach(
                        source=goal,
                        target=subgoal,
                        options={"type": "HAS_SUBGOAL", "direction": "out"}
                    )
    
    return created_goals


def demonstrate_graph_traversal():
    """
    Demonstrate graph traversal queries.
    
    RushDB's find() with relationship syntax allows filtering by related record properties.
    This is how we find subgoals: filter GOAL records where their parent matches.
    """
    print("\n" + "="*60)
    print("STEP 2: Graph Traversal - Finding Subgoals")
    print("="*60)
    
    # Find top-level goals (goals with no parent)
    all_goals = db.records.find({"labels": ["GOAL"]})
    
    # For each top-level goal, find its direct subgoals
    for goal in all_goals.data:
        # Find subgoals using relationship filtering
        # The key insight: filter by PARENT_GOAL relationship properties
        subgoals = db.records.find({
            "labels": ["GOAL"],
            "where": {
                "PARENT_GOAL": {
                    "$relation": {"type": "HAS_SUBGOAL", "direction": "in"},
                    "title": goal['title']
                }
            }
        })
        
        if subgoals.data:
            print(f"\n'{goal['title']}' has {len(subgoals.data)} direct subgoals:")
            for subgoal in subgoals.data:
                print(f"  → {subgoal['title']}")


def demonstrate_semantic_search():
    """
    Demonstrate vector similarity search.
    
    RushDB's ai.search() finds records by semantic similarity of their descriptions.
    This works across the entire goal tree, not just within a single branch.
    """
    print("\n" + "="*60)
    print("STEP 3: Semantic Search - Finding Related Goals")
    print("="*60)
    
    # Find goals semantically similar to "designing scalable APIs"
    query = "designing scalable APIs"
    print(f"\nSearching for goals related to: '{query}'")
    
    # Use ai.search() with semantic query
    results = db.ai.search({
        "propertyName": "description",
        "query": query,
        "labels": ["GOAL"],
        "limit": 5
    })
    
    print("\nTop semantically similar goals:")
    for result in results.data:
        score = result.score
        print(f"  [{score:.3f}] '{result['title']}'")
        print(f"       Description: {result['description'][:80]}...")
    
    # Now search for something about testing
    query = "writing automated tests and validation"
    print(f"\n\nSearching for goals related to: '{query}'")
    
    results = db.ai.search({
        "propertyName": "description",
        "query": query,
        "labels": ["GOAL"],
        "limit": 5
    })
    
    print("\nTop semantically similar goals:")
    for result in results.data:
        score = result.score
        print(f"  [{score:.3f}] '{result['title']}'")


def demonstrate_combined_query():
    """
    Demonstrate the real power: combining graph traversal with vector search.
    
    This is what makes RushDB unique - we can:
    1. Start with a specific goal (graph traversal)
    2. Find semantically related subgoals (vector search)
    3. All in one application, no multi-system queries
    """
    print("\n" + "="*60)
    print("STEP 4: Combined Queries - Graph + Vector Search")
    print("="*60)
    
    # Find the "Learn System Design" goal
    root_goal = db.records.find({
        "labels": ["GOAL"],
        "where": {"title": "Learn System Design"}
    })
    
    if not root_goal.data:
        print("Could not find root goal. Skipping combined query demo.")
        return
    
    root = root_goal.data[0]
    print(f"\nStarting from goal: '{root['title']}'")
    
    # Get direct subgoals
    direct_subgoals = db.records.find({
        "labels": ["GOAL"],
        "where": {
            "PARENT_GOAL": {
                "$relation": {"type": "HAS_SUBGOAL", "direction": "in"},
                "title": root['title']
            }
        }
    })
    
    subgoal_ids = [sg.id for sg in direct_subgoals.data]
    print(f"Direct subgoals: {[sg['title'] for sg in direct_subgoals.data]}")
    
    # Now search within these subgoals for semantic similarity
    # This finds "similar to testing" within the "Learn System Design" branch
    query = "testing and quality assurance"
    print(f"\nSearching within subgoals for: '{query}'")
    
    # RushDB allows filtering ai.search by related records
    results = db.ai.search({
        "propertyName": "description",
        "query": query,
        "labels": ["GOAL"],
        "where": {
            "PARENT_GOAL": {
                "$relation": {"type": "HAS_SUBGOAL", "direction": "in"},
                "title": root['title']
            }
        },
        "limit": 5
    })
    
    print("\nSemantically similar subgoals (within this branch):")
    for result in results.data:
        print(f"  [{result.score:.3f}] '{result['title']}'")



def demonstrate_single_db_advantage():
    """
    Explain the single-database advantage that RushDB provides.
    """
    print("\n" + "="*60)
    print("THE SINGLE-DATABASE ADVANTAGE")
    print("="*60)
    
    print("""
Traditional Architecture (without RushDB):
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Neo4j       │     │    Pinecone     │     │     Python       │
│  (graph data)   │ ←── │  (vectors)      │ ←── │  (sync logic)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                                 │
        └───────────────── PROBLEM: ────────────────────┘
                   • Two API endpoints to maintain
                   • Sync delays between systems
                   • Inconsistent data during failures
                   • Twice the authentication/permissions
                   • Two query languages (Cypher + vector DSL)

RushDB Architecture:
┌─────────────────────────────────────────────────┐
│                      RushDB                     │
│  ┌───────────────────────────────────────────┐  │
│  │         Neo4j (property graph)            │  │
│  │  • GOAL records (nodes)                   │  │
│  │  • HAS_SUBGOAL edges                      │  │
│  │  • Vector indexes on descriptions         │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │       One API, One SDK         │
         │   • Graph traversal ✓          │
         │   • Vector search ✓            │
         │   • Atomic transactions ✓      │
         │   • Single authentication ✓    │
         │   • One query interface ✓     │
         └───────────────────────────────┘

Key Benefits Demonstrated in This Tutorial:
1. Inline vector writes: `vectors=[{"propertyName": "...", "vector": [...]}]`
2. Graph + vector in one query: ai.search() with where clause for relationships
3. Transactional consistency: All writes (records + relationships + vectors) atomic
4. Single SDK: No need to coordinate Neo4j driver + vector DB client
""")


def cleanup_existing_data():
    """"Remove any existing goal records before seeding."""
    print("\nCleaning up existing data...")
    
    # Delete all GOAL records
    try:
        db.records.delete_many({"labels": ["GOAL"], "where": {}})
        print("  ✓ Removed existing GOAL records")
    except Exception as e:
        print(f"  Cleanup note: {e}")


def main():
    print("="*60)
    print("GOAL-SUBGOAL DECOMPOSITION TRACKER WITH RUSHDB")
    print("="*60)
    print("""
This tutorial shows how RushDB's unified graph+vector model
handles hierarchical goals and semantic search in a single database.
""")
    
    # Setup: Create vector index
    setup_vector_index()
    
    # Load and create goal hierarchy
    print("\n" + "="*60)
    print("SEEDING GOAL HIERARCHY")
    print("="*60)
    
    goals_data = load_goal_data()
    
    # Clean up existing data first
    cleanup_existing_data()
    
    print("\nCreating goal hierarchy...")
    create_goal_hierarchy(goals_data)
    
    # Demonstrate capabilities
    demonstrate_graph_traversal()
    demonstrate_semantic_search()
    demonstrate_combined_query()
    demonstrate_single_db_advantage()
    
    print("\n" + "="*60)
    print("TUTORIAL COMPLETE")
    print("="*60)
    print("""
You've just seen how RushDB handles:

1. HIERARCHICAL DATA: Goals connected via HAS_SUBGOAL edges
2. SEMANTIC SEARCH: Vector embeddings on descriptions
3. COMBINED QUERIES: Find semantically similar goals within a branch

In a traditional setup, this would require:
- Neo4j for the graph
- Pinecone/Weaviate for vectors
- Sync logic to keep them in sync

With RushDB: everything in one API call.

Next Steps:
- Try adding new goals and subgoals
- Experiment with different semantic queries
- Explore more complex relationship patterns
""")


if __name__ == "__main__":
    main()
