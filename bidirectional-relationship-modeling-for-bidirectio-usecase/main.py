"""
Bidirectional Relationship Modeling - Main Example

This script demonstrates bidirectional recall patterns for agent memory systems
using RushDB's property graph structure.

Key patterns:
1. Forward queries: "What does the agent know about topic X?"
2. Reverse queries: "What tasks depend on this memory?"
3. Bidirectional traces: Full impact analysis
4. Semantic search: Find related memories by meaning

Run seed.py first to populate the database with example data.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB


# ============================================================================
# BIDIRECTIONAL QUERY FUNCTIONS
# ============================================================================

def forward_query_agent_knowledge(db, agent_name, concept_filter):
    """
    Forward query: "What does the agent know about X?"
    
    Traverses: AGENT → (HAS_MEMORY) → MEMORY → (ABOUT) → CONCEPT
    Returns all memories the agent has about a specific concept.
    """
    print("\n" + "=" * 70)
    print("FORWARD QUERY: What does the agent know about topic X?")
    print("=" * 70)
    
    # Find the agent first
    agents = db.records.find({
        "labels": ["AGENT"],
        "where": {"name": agent_name}
    })
    
    if not agents:
        print(f"Agent '{agent_name}' not found")
        return []
    
    agent = agents[0]
    print(f"Agent: {agent['name']} (v{agent['version']})")
    print(f"Domain: {agent['domain']}")
    
    # Query: Find memories linked to agent that are about the concept
    memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "AGENT": {
                "$relation": {"type": "HAS_MEMORY", "direction": "out"},
                "$id": agent.id
            },
            "CONCEPT": {
                "name": {"$contains": concept_filter}
            }
        }
    })
    
    print(f"\n→ Found {len(memories)} memory(ies) about '{concept_filter}':")
    for memory in memories:
        print(f"  • [{memory['type']}] {memory['content'][:80]}...")
    
    return memories


def reverse_query_dependencies(db, memory_content_hint):
    """
    Reverse query: "What in memory depends on this fact?"
    
    Traverses: MEMORY ← (USED) ← TASK_STEP
    Returns all task steps that rely on a specific memory.
    This is the "self-awareness" query — understanding impact.
    """
    print("\n" + "=" * 70)
    print("REVERSE QUERY: What depends on this memory? (Self-awareness)")
    print("=" * 70)
    
    # First find the memory
    memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "content": {"$contains": memory_content_hint}
        },
        "limit": 1
    })
    
    if not memories:
        print(f"No memory found containing: '{memory_content_hint}'")
        return []
    
    memory = memories[0]
    print(f"Memory: {memory['content'][:60]}...")
    print(f"Type: {memory['type']}, Importance: {memory['importance']}")
    
    # Query: Find tasks that USED this memory (reverse direction)
    dependent_tasks = db.records.find({
        "labels": ["TASK_STEP"],
        "where": {
            "MEMORY": {
                "$relation": {"type": "USED", "direction": "in"},
                "$id": memory.id
            }
        }
    })
    
    print(f"\n← {len(dependent_tasks)} task(s) depend on this memory:")
    for task in dependent_tasks:
        status_icon = "✓" if task['status'] == 'completed' else "→" if task['status'] == 'in_progress' else "○"
        print(f"  {status_icon} [{task['step_order']}] {task['action']} ({task['status']})")
    
    return dependent_tasks


def bidirectional_trace(db, memory_content_hint):
    """
    Bidirectional trace: Full impact chain analysis.
    
    Combines forward and reverse queries to show:
    - What the memory is about (forward)
    - What tasks use it (reverse)
    - Complete dependency picture
    """
    print("\n" + "=" * 70)
    print("BIDIRECTIONAL TRACE: Complete impact chain")
    print("=" * 70)
    
    # Find the memory
    memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "content": {"$contains": memory_content_hint}
        },
        "limit": 1
    })
    
    if not memories:
        print(f"No memory found containing: '{memory_content_hint}'")
        return None
    
    memory = memories[0]
    print(f"\nMemory: {memory['content'][:80]}...")
    print(f"Importance: {memory['importance']}")
    
    # Forward: What concepts does this memory relate to?
    related_concepts = db.records.find({
        "labels": ["CONCEPT"],
        "where": {
            "MEMORY": {
                "$relation": {"type": "ABOUT", "direction": "in"},
                "$id": memory.id
            }
        }
    })
    
    print(f"\n→ Related concepts ({len(related_concepts)}):")
    for concept in related_concepts:
        print(f"  • {concept['name']} ({concept['category']})")
    
    # Reverse: What tasks depend on this memory?
    dependent_tasks = db.records.find({
        "labels": ["TASK_STEP"],
        "where": {
            "MEMORY": {
                "$relation": {"type": "USED", "direction": "in"},
                "$id": memory.id
            }
        }
    })
    
    print(f"\n← Dependent tasks ({len(dependent_tasks)}):")
    for task in dependent_tasks:
        print(f"  • Step {task['step_order']}: {task['action']}")
    
    # Reverse: Which other memories reference this one?
    related_memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "MEMORY": {
                "$relation": {"type": "RELATED_TO", "direction": "in"},
                "$id": memory.id
            }
        }
    })
    
    if related_memories:
        print(f"\n↔ Related memories ({len(related_memories)}):")
        for rel in related_memories:
            print(f"  • {rel['content'][:60]}...")
    
    return {
        "memory": memory,
        "concepts": related_concepts,
        "tasks": dependent_tasks
    }


def semantic_search_within_context(db, query_text, agent_name=None):
    """
    Semantic search: Find memories by meaning, not just keywords.
    
    Uses vector similarity to find conceptually related memories,
    then filters by relationship context.
    """
    print("\n" + "=" * 70)
    print("SEMANTIC SEARCH: Find memories by meaning")
    print("=" * 70)
    print(f"Query: "{query_text}"")
    
    # Perform semantic search
    try:
        results = db.ai.search({
            "propertyName": "content",
            "query": query_text,
            "labels": ["MEMORY"],
            "limit": 5
        })
        
        if not results.data:
            print("No semantically similar memories found.")
            return []
        
        print(f"\n→ Found {len(results.data)} semantically similar memories:")
        
        similar_memories = []
        for result in results.data:
            score = result.score
            memory = db.records.find_by_id(result.id)
            
            print(f"\n  [{score:.3f}] {memory['content'][:70]}...")
            print(f"       Type: {memory['type']}, Importance: {memory['importance']}")
            
            # Reverse query: What tasks use this memory?
            if agent_name:
                tasks_using = db.records.find({
                    "labels": ["TASK_STEP"],
                    "where": {
                        "MEMORY": {
                            "$relation": {"type": "USED", "direction": "in"},
                            "$id": memory.id
                        }
                    }
                })
                if tasks_using:
                    task_names = ", ".join([t['action'] for t in tasks_using])
                    print(f"       Used by: {task_names}")
            
            similar_memories.append(memory)
        
        return similar_memories
        
    except Exception as e:
        print(f"Semantic search failed: {e}")
        print("Note: Ensure vector index exists for MEMORY.content")
        return []


def impact_analysis(db, concept_filter):
    """
    Impact analysis: "What would break if we update facts about X?"
    
    For a given concept, find:
    1. All related memories
    2. All tasks that depend on those memories
    3. Complete impact chain
    """
    print("\n" + "=" * 70)
    print("IMPACT ANALYSIS: What tasks would be affected?")
    print("=" * 70)
    print(f"Concept filter: '{concept_filter}'")
    
    # Find memories about this concept
    memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "CONCEPT": {
                "name": {"$contains": concept_filter}
            }
        }
    })
    
    if not memories:
        print(f"No memories found about '{concept_filter}'")
        return
    
    print(f"\nFound {len(memories)} memory(ies) about '{concept_filter}':")
    
    total_affected_tasks = set()
    
    for memory in memories:
        print(f"\n  Memory: {memory['content'][:60]}...")
        print(f"  Importance: {memory['importance']}")
        
        # Find tasks using this memory
        tasks = db.records.find({
            "labels": ["TASK_STEP"],
            "where": {
                "MEMORY": {
                    "$relation": {"type": "USED", "direction": "in"},
                    "$id": memory.id
                }
            }
        })
        
        for task in tasks:
            total_affected_tasks.add(task.id)
            status_icon = "✓" if task['status'] == 'completed' else "→" if task['status'] == 'in_progress' else "○"
            print(f"    {status_icon} → Task {task['step_order']}: {task['action']}")
    
    print(f"\n{'=' * 50}")
    print(f"IMPACT SUMMARY: {len(total_affected_tasks)} tasks would be affected")
    print("This demonstrates the 'self-awareness' of the agent's memory system.")
    print("Before updating any fact, the agent knows exactly what depends on it.")


def list_agent_context(db, agent_name):
    """
    List complete agent context: All knowledge and usage patterns.
    
    Shows the full memory graph for an agent including:
    - All memories organized by type
    - Concept coverage
    - Task dependency coverage
    """
    print("\n" + "=" * 70)
    print("AGENT CONTEXT: Full memory overview")
    print("=" * 70)
    
    agents = db.records.find({
        "labels": ["AGENT"],
        "where": {"name": agent_name}
    })
    
    if not agents:
        print(f"Agent '{agent_name}' not found")
        return
    
    agent = agents[0]
    print(f"\nAgent: {agent['name']}")
    print(f"Domain: {agent['domain']}")
    
    # Get all agent memories
    all_memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "AGENT": {
                "$relation": {"type": "HAS_MEMORY", "direction": "out"},
                "$id": agent.id
            }
        }
    })
    
    print(f"\nMemory count: {len(all_memories)}")
    
    # Group by type
    by_type = {}
    for memory in all_memories:
        mtype = memory['type']
        if mtype not in by_type:
            by_type[mtype] = []
        by_type[mtype].append(memory)
    
    print("\nMemories by type:")
    for mtype, mems in sorted(by_type.items()):
        print(f"  {mtype}: {len(mems)} memory(ies)")
    
    # Get all tasks
    all_tasks = db.records.find({"labels": ["TASK_STEP"]})
    completed = [t for t in all_tasks if t['status'] == 'completed']
    in_progress = [t for t in all_tasks if t['status'] == 'in_progress']
    planned = [t for t in all_tasks if t['status'] == 'planned']
    
    print(f"\nTask status: {len(completed)} completed, {len(in_progress)} in progress, {len(planned)} planned")
    
    print("\n" + "-" * 50)
    print("Bidirectional coverage:")
    
    # For each memory, show what depends on it
    memory_usage = []
    for memory in all_memories:
        tasks = db.records.find({
            "labels": ["TASK_STEP"],
            "where": {
                "MEMORY": {
                    "$relation": {"type": "USED", "direction": "in"},
                    "$id": memory.id
                }
            }
        })
        memory_usage.append((memory, len(tasks)))
    
    # Sort by usage
    memory_usage.sort(key=lambda x: x[1], reverse=True)
    
    print("\nMost referenced memories:")
    for memory, count in memory_usage[:5]:
        print(f"  [{count} tasks] {memory['content'][:50]}...")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all bidirectional relationship demonstrations."""
    
    print("\n" + "=" * 70)
    print("BIDIRECTIONAL RELATIONSHIP MODELING FOR AGENT MEMORY")
    print("=" * 70)
    
    # Initialize RushDB
    api_token = os.getenv("RUSHDB_API_TOKEN")
    
    if not api_token:
        print("\nError: RUSHDB_API_TOKEN not found in environment.")
        print("Copy .env.example to .env and add your API token.")
        print("Get your token from: https://app.rushdb.com/settings/api-tokens")
        sys.exit(1)
    
    db = RushDB(api_token)
    
    print("\n✓ Connected to RushDB")
    print("\nDemonstrating bidirectional recall patterns...")
    
    # 1. Forward query: What does the agent know about REST API?
    forward_query_agent_knowledge(db, "TaskPlanningAgent", "REST API")
    
    # 2. Reverse query: What depends on a specific memory?
    reverse_query_dependencies(db, "JWT")
    
    # 3. Bidirectional trace: Complete impact analysis
    bidirectional_trace(db, "database")
    
    # 4. Semantic search with relationship context
    semantic_search_within_context(db, "team resources and sprint capacity")
    
    # 5. Impact analysis for a concept
    impact_analysis(db, "project timeline")
    
    # 6. Full agent context overview
    list_agent_context(db, "TaskPlanningAgent")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: Bidirectional Recall Patterns")
    print("=" * 70)
    print("""
This example demonstrated:

1. FORWARD QUERY: "What does the agent know about X?"
   → AGENT → HAS_MEMORY → MEMORY → ABOUT → CONCEPT
   
2. REVERSE QUERY: "What depends on this memory?"
   → MEMORY ← USED ← TASK_STEP
   (This is "self-awareness" — knowing your impact)
   
3. BIDIRECTIONAL TRACE: Full impact chain
   → Shows both directions in a single query
   
4. SEMANTIC SEARCH: Find by meaning, not keywords
   → Vector similarity within relationship context
   
5. IMPACT ANALYSIS: "What would break if we update X?"
   → Aggregates all dependencies for a concept

These patterns are essential for agent memory systems because:
- Agents need to retrieve relevant knowledge (forward)
- Agents need to understand what they've used (self-awareness)
- Agents need to know impact before updates (bidirectional)

RushDB's graph structure enables O(1) traversal in both directions,
making bidirectional queries as fast as forward queries.
""")


if __name__ == "__main__":
    main()
