"""
From Retrieval to Reasoning: Graph-Structured Memory for AI Agents

This tutorial demonstrates how RushDB enables AI agents to navigate multi-step
problems by leveraging graph-structured memory. We'll show three patterns:

1. Semantic Retrieval - Finding relevant context via vector search
2. Multi-hop Reasoning - Tracing chains of thought to reach conclusions
3. Decision Reconstruction - Full replay of an agent's reasoning path

Each pattern showcases a different way RushDB's property graph model enables
sophisticated reasoning that pure vector databases cannot support.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB


def init_db():
    """Initialize RushDB connection."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "RUSHDB_API_KEY not found. "
            "Copy .env.example to .env and add your API key."
        )
    return RushDB(api_key)


def demo_semantic_retrieval(db):
    """
    Pattern 1: Semantic Retrieval
    
    Query the memory store for context relevant to "neural network optimization".
    RushDB's vector index enables semantic search without manual keyword matching.
    """
    print("\n" + "=" * 60)
    print("PATTERN 1: Semantic Retrieval")
    print("=" * 60)
    
    query = "neural network optimization techniques"
    print(f"\nQuery: \"{query}\"")
    print("-" * 40)
    
    # Perform semantic search across CONTEXT records
    results = db.ai.search({
        "propertyName": "content",
        "query": query,
        "labels": ["CONTEXT"],
        "limit": 5
    })
    
    found_count = len(results.data) if results.data else 0
    print(f"Found: {found_count} relevant context records\n")
    
    for i, record in enumerate(results.data or [], 1):
        title = record.data.get("title", "Untitled")
        score = record.score
        tags = record.data.get("tags", [])
        print(f"  {i}. \"{title}\"")
        print(f"     Score: {score:.3f} | Tags: {', '.join(tags)}")
    
    # Filter by tag
    print("\nFiltered search: optimization-related only")
    print("-" * 40)
    
    filtered_results = db.ai.search({
        "propertyName": "content",
        "query": "training strategies",
        "labels": ["CONTEXT"],
        "where": {
            "tags": {"$contains": "training"}
        },
        "limit": 3
    })
    
    for record in filtered_results.data or []:
        print(f"  - \"{record.data.get('title')}\" (score: {record.score:.3f})")
    
    return results.data


def demo_multihop_reasoning(db):
    """
    Pattern 2: Multi-hop Reasoning
    
    Trace a chain of reasoning: from observation → thought → action.
    This demonstrates RushDB's ability to traverse relationships and reconstruct
    the logical path an agent took to reach a conclusion.
    """
    print("\n" + "=" * 60)
    print("PATTERN 2: Multi-hop Reasoning")
    print("=" * 60)
    
    # Find high-priority observations
    print("\nStep 1: Find high-priority observations")
    print("-" * 40)
    
    observations = db.records.find({
        "labels": ["OBSERVATION"],
        "where": {"priority": "high"},
        "limit": 5
    })
    
    if not observations.data:
        print("  No high-priority observations found")
        print("  Run 'python seed.py' first to populate data")
        return
    
    for obs in observations.data:
        content = obs.data.get("content", "")
        source = obs.data.get("source", "unknown")
        print(f"  [{source}] {content[:60]}...")
    
    # Find thoughts that reason about these observations
    print("\nStep 2: Find reasoning chain (THOUGHTs linked to observations)")
    print("-" * 40)
    
    first_obs = observations.data[0]
    obs_id = first_obs.id
    
    # Query thoughts that reason about our observation
    thoughts = db.records.find({
        "labels": ["THOUGHT"],
        "where": {
            "OBSERVATION": {"$id": {"$in": [obs_id]}}
        },
        "limit": 5
    })
    
    if thoughts.data:
        for thought in thoughts.data:
            content = thought.data.get("content", "")
            t_type = thought.data.get("type", "unknown")
            confidence = thought.data.get("confidence", 0)
            print(f"  [{t_type}] {content[:60]}...")
            print(f"           Confidence: {confidence:.0%}")
    else:
        # Fallback: show all thoughts
        all_thoughts = db.records.find({
            "labels": ["THOUGHT"],
            "limit": 5
        })
        for thought in all_thoughts.data:
            content = thought.data.get("content", "")
            t_type = thought.data.get("type", "unknown")
            print(f"  [{t_type}] {content[:60]}...")
    
    # Find actions caused by these thoughts
    print("\nStep 3: Find resulting actions")
    print("-" * 40)
    
    # Get first thought from earlier query
    thought_sample = db.records.find({
        "labels": ["THOUGHT"],
        "limit": 1
    })
    
    if thought_sample.data:
        thought_id = thought_sample.data[0].id
        
        actions = db.records.find({
            "labels": ["ACTION"],
            "where": {
                "THOUGHT": {"$id": {"$in": [thought_id]}}
            },
            "limit": 3
        })
        
        for action in actions.data or []:
            content = action.data.get("content", "")
            tool = action.data.get("tool", "unknown")
            status = action.data.get("status", "unknown")
            print(f"  [{tool}] {content}")
            print(f"           Status: {status}")
    
    # Demonstrate relationship direction
    print("\nStep 4: Traverse relationships (show reasoning direction)")
    print("-" * 40)
    
    # Find actions that address observations
    address_actions = db.records.find({
        "labels": ["ACTION"],
        "where": {
            "OBSERVATION": {
                "$relation": {"type": "ADDRESSES", "direction": "in"}
            }
        },
        "limit": 3
    })
    
    if address_actions.data:
        print("  Actions that address high-priority observations:")
        for action in address_actions.data:
            content = action.data.get("content", "")[:70]
            print(f"    → {content}...")
    
    print("\n✓ Multi-hop reasoning chain reconstructed")
    return observations.data


def demo_decision_reconstruction(db):
    """
    Pattern 3: Decision Reconstruction
    
    Replay a complete agent decision: from initial observation through
    reasoning to final action. This is the key pattern for explaining
    AI decisions and for agent self-reflection.
    """
    print("\n" + "=" * 60)
    print("PATTERN 3: Decision Reconstruction")
    print("=" * 60)
    
    print("\nScenario: Reconstructing a batch size optimization decision")
    print("-" * 40)
    
    # Find the observation about batch size
    batch_obs = db.records.find({
        "labels": ["OBSERVATION"],
        "where": {"content": {"$contains": "batch"}}
    })
    
    if batch_obs.data:
        obs = batch_obs.data[0]
        print(f"\n[0] INITIAL OBSERVATION")
        print(f"    \"{obs.data.get('content')}\"")
        print(f"    Source: {obs.data.get('source')} | Priority: {obs.data.get('priority')}")
    else:
        print("\n  No batch size observation found")
        return
    
    # Find related thoughts
    print("\n[1] REASONING CHAIN")
    
    obs_id = obs.id
    reasoning_thoughts = db.records.find({
        "labels": ["THOUGHT"],
        "where": {
            "OBSERVATION": {"$id": {"$in": [obs_id]}}
        },
        "limit": 5
    })
    
    if reasoning_thoughts.data:
        for i, thought in enumerate(reasoning_thoughts.data, 1):
            content = thought.data.get("content", "")
            t_type = thought.data.get("type", "")
            print(f"    Step {i}: {content}")
            print(f"             (type: {t_type})")
    else:
        # Show all thoughts with optimization type
        opt_thoughts = db.records.find({
            "labels": ["THOUGHT"],
            "where": {"type": "optimization"},
            "limit": 3
        })
        if opt_thoughts.data:
            for i, thought in enumerate(opt_thoughts.data, 1):
                content = thought.data.get("content", "")
                print(f"    Step {i}: {content}")
    
    # Find the resulting action
    print("\n[2] FINAL ACTION")
    
    actions = db.records.find({
        "labels": ["ACTION"],
        "where": {
            "OBSERVATION": {"$id": {"$in": [obs_id]}}
        },
        "limit": 2
    })
    
    if actions.data:
        for action in actions.data:
            content = action.data.get("content", "")
            tool = action.data.get("tool", "")
            status = action.data.get("status", "")
            print(f"    \"{content}\"")
            print(f"    Tool: {tool} | Status: {status}")
    else:
        # Show actions containing batch_size
        batch_actions = db.records.find({
            "labels": ["ACTION"],
            "where": {"content": {"$contains": "batch"}}
        })
        if batch_actions.data:
            action = batch_actions.data[0]
            print(f"    \"{action.data.get('content')}\"")
            print(f"    Tool: {action.data.get('tool')} | Status: {action.data.get('status')}")
    
    # Show the full graph path
    print("\n[3] COMPLETE DECISION GRAPH")
    print("-" * 40)
    print("    OBSERVATION")
    print("       │\n")
    print("       ├──[REASONED_ABOUT]──▶ THOUGHT")
    print("       │                     │")
    print("       │                     └──[CAUSED_BY]──▶ ACTION")
    print("       │\n")
    print("       └──[ADDRESSES]────────▶ ACTION")
    
    print("\n✓ Decision reconstruction complete")


def demo_graph_stats(db):
    """Display statistics about the memory graph."""
    print("\n" + "=" * 60)
    print("MEMORY GRAPH STATISTICS")
    print("=" * 60)
    
    labels = ["CONTEXT", "OBSERVATION", "THOUGHT", "ACTION"]
    
    print("\nRecord counts:")
    for label in labels:
        result = db.records.find({"labels": [label], "limit": 1000})
        count = len(result.data) if result.data else 0
        print(f"  {label:12} : {count:3} records")
    
    # Check vector index status
    print("\nVector indexes:")
    try:
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            label = idx.get("label", "unknown")
            prop = idx.get("propertyName", "unknown")
            status = idx.get("status", "unknown")
            print(f"  {label}.{prop}: {status}")
    except Exception as e:
        print(f"  Unable to list indexes: {e}")
    
    print("\n" + "=" * 60)


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("FROM RETRIEVAL TO REASONING")
    print("Graph-Structured Memory for AI Agents")
    print("=" * 60)
    
    try:
        db = init_db()
    except Exception as e:
        print(f"\nFailed to connect to RushDB: {e}")
        print("\nMake sure to:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your RUSHDB_API_KEY")
        print("  3. Run 'python seed.py' to populate data")
        return
    
    # Run demonstrations
    demo_semantic_retrieval(db)
    demo_multihop_reasoning(db)
    demo_decision_reconstruction(db)
    demo_graph_stats(db)
    
    print("\n" + "=" * 60)
    print("TUTORIAL COMPLETE")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  • Semantic search enables contextual retrieval")
    print("  • Graph relationships enable multi-hop reasoning")
    print("  • Transactional operations ensure consistency")
    print("  • RushDB serves as a production memory layer for AI agents")
    print("\n")


if __name__ == "__main__":
    main()
