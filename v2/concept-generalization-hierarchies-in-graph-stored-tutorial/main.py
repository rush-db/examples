"""
Main demonstration: Concept Generalization Hierarchies in RushDB

This script demonstrates core operations for working with concept hierarchies
using RushDB's graph structure and vector search capabilities.
"""

import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(api_key)


def find_root_concepts(db: RushDB) -> list:
    """
    Find all root concepts (level 0) - concepts with no IS_A parent.
    
    These are the top-level abstractions in our hierarchy.
    """
    roots = db.records.find({
        "labels": ["CONCEPT"],
        "where": {"level": 0}
    })
    return roots.data


def count_descendants(db: RushDB, concept_id: str) -> int:
    """Count all descendants of a concept by traversing IS_A relationships."""
    descendants = db.records.find({
        "labels": ["CONCEPT"],
        "where": {
            "CONCEPT": {
                "$relation": {"type": "IS_A", "direction": "in"},
                "$id": concept_id
            }
        }
    })
    return len(descendants.data)


def get_direct_children(db: RushDB, concept_id: str) -> list:
    """Get immediate children of a concept (one level down)."""
    children = db.records.find({
        "labels": ["CONCEPT"],
        "where": {
            "CONCEPT": {
                "$relation": {"type": "IS_A", "direction": "in"},
                "$id": concept_id
            },
            "level": db.records.find_by_id(concept_id).data.get("level", 0) + 1
        }
    })
    return children.data


def get_all_descendants(db: RushDB, concept_name: str) -> list:
    """Get all descendants of a concept by name (recursive search)."""
    # First find the concept
    concepts = db.records.find({
        "labels": ["CONCEPT"],
        "where": {"name": concept_name}
    })
    
    if not concepts.data:
        return []
    
    concept = concepts.data[0]
    concept_level = concept.data.get("level", 0)
    
    # Find all concepts with higher level that are connected via IS_A
    all_descendants = []
    to_visit = [concept]
    visited = set()
    
    while to_visit:
        current = to_visit.pop(0)
        if current.id in visited:
            continue
        visited.add(current.id)
        
        # Get children of current concept
        children = db.records.find({
            "labels": ["CONCEPT"],
            "where": {
                "CONCEPT": {
                    "$relation": {"type": "IS_A", "direction": "in"},
                    "$id": current.id
                }
            }
        })
        
        for child in children.data:
            all_descendants.append(child)
            to_visit.append(child)
    
    return all_descendants


def get_ancestor_chain(db: RushDB, concept_name: str) -> list:
    """
    Get the full ancestor chain from a concept up to the root.
    Returns list of [concept, parent, grandparent, ...]
    """
    # Find the starting concept
    concepts = db.records.find({
        "labels": ["CONCEPT"],
        "where": {"name": concept_name}
    })
    
    if not concepts.data:
        return []
    
    chain = []
    current = concepts.data[0]
    
    while current:
        chain.append(current)
        
        # Find parent via IS_A relationship
        parents = db.records.find({
            "labels": ["CONCEPT"],
            "where": {
                "CONCEPT": {
                    "$relation": {"type": "IS_A", "direction": "out"},
                    "$id": current.id
                }
            }
        })
        
        if parents.data:
            current = parents.data[0]
        else:
            current = None
    
    return chain


def get_siblings(db: RushDB, concept_name: str) -> list:
    """
    Find siblings of a concept - other children of the same parent.
    """
    # Find the concept
    concepts = db.records.find({
        "labels": ["CONCEPT"],
        "where": {"name": concept_name}
    })
    
    if not concepts.data:
        return []
    
    concept = concepts.data[0]
    
    # Find parent
    parents = db.records.find({
        "labels": ["CONCEPT"],
        "where": {
            "CONCEPT": {
                "$relation": {"type": "IS_A", "direction": "out"},
                "$id": concept.id
            }
        }
    })
    
    if not parents.data:
        return []  # Root concept has no siblings
    
    parent = parents.data[0]
    
    # Find all children of the parent, excluding the original concept
    siblings = db.records.find({
        "labels": ["CONCEPT"],
        "where": {
            "CONCEPT": {
                "$relation": {"type": "IS_A", "direction": "in"},
                "$id": parent.id
            }
        }
    })
    
    return [s for s in siblings.data if s.id != concept.id]


def semantic_search_concepts(db: RushDB, query: str, limit: int = 5) -> list:
    """
    Search for semantically similar concepts using vector embeddings.
    
    This finds concepts whose definition vectors are similar to the
    embedding of the query text, regardless of hierarchy position.
    """
    results = db.ai.search({
        "propertyName": "definition",
        "query": query,
        "labels": ["CONCEPT"],
        "limit": limit
    })
    return results.data


def main():
    print("=" * 60)
    print("Concept Generalization Hierarchies Demo")
    print("=" * 60)
    print()
    
    # =========================================================================
    # 1. List all root concepts (top-level abstractions)
    # =========================================================================
    print("1. All Root Concepts (top-level abstractions):")
    roots = find_root_concepts(db)
    for root in roots:
        descendant_count = count_descendants(db, root.id)
        print(f"   - {root['name']} (level 0, {descendant_count} descendants)")
    print()
    
    # =========================================================================
    # 2. Get descendants of a specific concept (Dog)
    # =========================================================================
    print("2. Descendants of 'Dog':")
    descendants = get_all_descendants(db, "Dog")
    if descendants:
        for desc in descendants:
            level = desc.data.get("level", 0)
            indent = "   " + "  " * (level - 3)  # Dog is level 3
            print(f"{indent}└── {desc['name']} (level {level})")
    else:
        print("   Run seed.py first to create the hierarchy")
    print()
    
    # =========================================================================
    # 3. Get ancestor chain (specialization to generalization)
    # =========================================================================
    print("3. Full Ancestor Chain for 'Golden Retriever':")
    chain = get_ancestor_chain(db, "Golden Retriever")
    if chain:
        chain_names = [c["name"] for c in chain]
        print(f"   {" → ".join(chain_names)}")
        print(f"   (distance from root: {len(chain) - 1} levels)")
    else:
        print("   Run seed.py first to create the hierarchy")
    print()
    
    # =========================================================================
    # 4. Find siblings (concepts with same parent)
    # =========================================================================
    print("4. Siblings of 'German Shepherd' (same parent 'Dog'):")
    siblings = get_siblings(db, "German Shepherd")
    if siblings:
        for sib in siblings:
            print(f"   - {sib['name']}")
    else:
        print("   Run seed.py first to create the hierarchy")
    print()
    
    # =========================================================================
    # 5. Semantic search across hierarchy
    # =========================================================================
    print("5. Semantic Search: concepts similar to 'pet that retrieves'")
    search_results = semantic_search_concepts(db, "pet that retrieves", limit=5)
    if search_results:
        print("   Top 5 results:")
        for i, result in enumerate(search_results, 1):
            score = result.score if hasattr(result, 'score') else result.get('__score', 0)
            print(f"   {i}. {result['name']} (score: {score:.2f})")
    else:
        print("   Run seed.py first to create the hierarchy")
    print()
    
    # =========================================================================
    # 6. Generalization query - all descendants of a category
    # =========================================================================
    print("6. Generalization Query: find all descendants of 'Mammal'")
    mammal_descendants = get_all_descendants(db, "Mammal")
    if mammal_descendants:
        print("   Direct and indirect descendants:")
        for desc in mammal_descendants:
            level = desc.data.get("level", 0)
            indent = "   " + "  " * (level - 2)
            print(f"{indent}└── {desc['name']}")
    else:
        print("   Run seed.py first to create the hierarchy")
    print()
    
    # =========================================================================
    # 7. Specialization query - direct children only
    # =========================================================================
    print("7. Specialization Query: concepts directly below 'Animal'")
    animal_concepts = db.records.find({"labels": ["CONCEPT"], "where": {"name": "Animal"}})
    if animal_concepts.data:
        direct_children = get_direct_children(db, animal_concepts.data[0].id)
        if direct_children:
            for child in direct_children:
                print(f"   - {child['name']}")
        else:
            print("   Run seed.py first to create the hierarchy")
    else:
        print("   Run seed.py first to create the hierarchy")
    print()
    
    # =========================================================================
    # 8. Cross-hierarchy semantic discovery
    # =========================================================================
    print("8. Cross-hierarchy Discovery: concepts similar to 'electronic device'")
    cross_results = semantic_search_concepts(db, "electronic device", limit=5)
    if cross_results:
        print("   Results spanning different hierarchy branches:")
        for i, result in enumerate(cross_results, 1):
            level = result.data.get("level", 0)
            chain = get_ancestor_chain(db, result["name"])
            category = chain[-1]["name"] if chain else "Unknown"
            print(f"   {i}. {result['name']} (from {category})")
    else:
        print("   Run seed.py first to create the hierarchy")
    print()
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
