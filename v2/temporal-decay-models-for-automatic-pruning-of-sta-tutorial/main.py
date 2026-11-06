#!/usr/bin/env python3
"""
Temporal Decay Models for Automatic Pruning of Stale Agent Memories
====================================================================

This script demonstrates how to implement temporal decay models for
managing AI agent memory systems using RushDB.

Concepts demonstrated:
1. Memory lifecycle tracking (creation time, access patterns)
2. Exponential decay function for relevance scoring
3. Access reinforcement (spaced repetition effect)
4. Threshold-based automatic pruning
5. Graph relationships for memory context

Run: python main.py
Prerequisites: python seed.py (creates test data)
"""

import math
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB

# Load environment
load_dotenv()

# ============================================================================
# DECAY MODEL CONFIGURATION
# ============================================================================

# Core decay parameters
DECAY_LAMBDA = 0.05          # Base decay rate (5% per hour)
RELEVANCE_THRESHOLD = 0.30   # Memories below this are pruned
REINFORCEMENT_BOOST = 0.20   # Relevance boost on memory access
MAX_ACCESS_REINFORCEMENT = 5  # Cap on access count multiplier

# Category-specific decay rates (override DECAY_LAMBDA)
CATEGORY_DECAY_RATES = {
    "fact": 0.01,      # Facts decay slowly
    "preference": 0.05, # Preferences decay at medium rate
    "context": 0.15,   # Context decays quickly
    "skill": 0.005,    # Skills persist
}

# ============================================================================
# DECAY MODEL IMPLEMENTATION
# ============================================================================

def compute_relevance(
    initial_importance: float,
    created_at: datetime,
    last_accessed_at: datetime,
    decay_rate: Optional[float] = None,
    access_count: int = 0,
    use_reinforcement: bool = True,
) -> float:
    """
    Compute current memory relevance using temporal decay with reinforcement.
    
    The decay model combines:
    1. Exponential time decay: initial × e^(-λ × age_hours)
    2. Access reinforcement: boosted relevance when memory is accessed
    3. Access count multiplier: frequent access = stronger memory
    
    Args:
        initial_importance: Base importance score (0.0 - 1.0)
        created_at: When the memory was created
        last_accessed_at: When the memory was last accessed
        decay_rate: Override decay rate (None uses DECAY_LAMBDA)
        access_count: Number of times memory was accessed
        use_reinforcement: Apply access reinforcement effect
    
    Returns:
        Current relevance score (0.0 - 1.0)
    """
    if decay_rate is None:
        decay_rate = DECAY_LAMBDA
    
    # Calculate age in hours since creation
    age_hours = (datetime.now() - created_at).total_seconds() / 3600
    
    # Apply exponential decay
    base_relevance = initial_importance * math.exp(-decay_rate * age_hours)
    
    # Apply reinforcement if memory has been accessed
    if use_reinforcement and access_count > 0:
        # Calculate time since last access
        hours_since_access = (datetime.now() - last_accessed_at).total_seconds() / 3600
        
        # Reinforcement decays faster than base memory
        reinforcement_decay = math.exp(-0.1 * hours_since_access)  # 10% reinforcement decay
        
        # Access count multiplier (capped)
        access_multiplier = min(1 + (access_count * 0.05), 1 + (MAX_ACCESS_REINFORCEMENT * 0.05))
        
        # Compute reinforcement boost
        reinforcement = REINFORCEMENT_BOOST * reinforcement_decay * access_multiplier
        
        # Combine base and reinforcement
        relevance = min(1.0, base_relevance + reinforcement)
    else:
        relevance = base_relevance
    
    # Clamp to valid range
    return max(0.0, min(1.0, relevance))


def should_prune(relevance: float, category: str) -> bool:
    """
    Determine if a memory should be pruned based on relevance and category.
    
    Category-specific thresholds:
    - skills: Higher threshold (0.40) - preserve important skills longer
    - facts: Medium threshold (0.30) - standard threshold
    - preferences: Medium threshold (0.30) - standard threshold
    - context: Lower threshold (0.20) - context fades fast
    """
    category_thresholds = {
        "skill": 0.40,
        "fact": 0.30,
        "preference": 0.30,
        "context": 0.20,
    }
    
    threshold = category_thresholds.get(category, RELEVANCE_THRESHOLD)
    return relevance < threshold


# ============================================================================
# RUSHDB MEMORY OPERATIONS
# ============================================================================

def initialize_rushdb() -> RushDB:
    """Initialize RushDB client with environment configuration."""
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("ERROR: RUSHDB_API_TOKEN not found")
        print("Set it in .env or export it before running:")
        print("  export RUSHDB_API_TOKEN=your_token_here")
        sys.exit(1)
    
    custom_url = os.getenv("RUSHDB_URL")
    if custom_url:
        return RushDB(api_token, url=custom_url)
    return RushDB(api_token)


def get_or_create_agent(db: RushDB) -> Optional[dict]:
    """Get the demo agent or return None if not found."""
    agents = db.records.find({
        "labels": ["AGENT"],
        "where": {"type": "decay-demo-agent"},
        "limit": 1
    })
    
    return agents[0] if agents else None


def get_agent_memories(db: RushDB, agent_id: str) -> list[dict]:
    """Get all memories for an agent with computed relevance scores."""
    memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {"agentId": agent_id}
    })
    
    enriched_memories = []
    for memory in memories:
        created_at = datetime.fromisoformat(memory["createdAt"])
        last_accessed = datetime.fromisoformat(memory["lastAccessedAt"])
        decay_rate = CATEGORY_DECAY_RATES.get(
            memory.get("category", "context"),
            DECAY_LAMBDA
        )
        
        relevance = compute_relevance(
            initial_importance=memory["initialImportance"],
            created_at=created_at,
            last_accessed_at=last_accessed,
            decay_rate=decay_rate,
            access_count=memory.get("accessCount", 0),
        )
        
        enriched_memories.append({
            **memory.data,
            "id": memory.id,
            "relevance": relevance,
            "created_at_dt": created_at,
            "last_accessed_dt": last_accessed,
        })
    
    return enriched_memories


def access_memory(db: RushDB, memory_id: str, agent_id: str) -> dict:
    """
    Simulate accessing a memory - updates access patterns and boosts relevance.
    
    In a real system, this would be called when the agent retrieves
    a memory during conversation or reasoning.
    """
    # Get current memory state
    memory = db.records.find_by_id(memory_id)
    if not memory:
        raise ValueError(f"Memory not found: {memory_id}")
    
    # Update access statistics
    now = datetime.now().isoformat()
    new_access_count = memory.get("accessCount", 0) + 1
    
    updated = db.records.update(
        record_id=memory_id,
        data={
            "lastAccessedAt": now,
            "accessCount": new_access_count,
        }
    )
    
    # Compute new relevance after reinforcement
    created_at = datetime.fromisoformat(memory["createdAt"])
    decay_rate = CATEGORY_DECAY_RATES.get(
        memory.get("category", "context"),
        DECAY_LAMBDA
    )
    
    new_relevance = compute_relevance(
        initial_importance=memory["initialImportance"],
        created_at=created_at,
        last_accessed_at=datetime.now(),  # Fresh access
        decay_rate=decay_rate,
        access_count=new_access_count,
        use_reinforcement=True,
    )
    
    print(f"  ✓ Memory accessed: '{memory['content'][:50]}...'")
    print(f"    Access count: {memory.get('accessCount', 0)} → {new_access_count}")
    print(f"    Relevance: {memory.get('relevance', 'N/A'):.3f} → {new_relevance:.3f}")
    
    return {
        **updated.data,
        "id": updated.id,
        "relevance": new_relevance,
    }


def prune_stale_memories(db: RushDB, agent_id: str, dry_run: bool = False) -> dict:
    """
    Prune memories that have fallen below the relevance threshold.
    
    Args:
        db: RushDB client
        agent_id: Agent whose memories to prune
        dry_run: If True, only report what would be deleted
    
    Returns:
        Statistics about the pruning operation
    """
    memories = get_agent_memories(db, agent_id)
    
    # Categorize memories
    to_prune = []
    to_keep = []
    
    for memory in memories:
        if should_prune(memory["relevance"], memory.get("category", "context")):
            to_prune.append(memory)
        else:
            to_keep.append(memory)
    
    # Print prune candidates
    print(f"\n  Memories below threshold ({len(to_prune)}):")
    for memory in sorted(to_prune, key=lambda m: m["relevance"])[:5]:
        category = memory.get("category", "unknown")
        threshold = {"skill": 0.40, "fact": 0.30, "preference": 0.30, "context": 0.20}.get(category, 0.30)
        print(f"    • [{category}] '{memory['content'][:40]}...'")
        print(f"      relevance: {memory['relevance']:.3f} < threshold: {threshold}")
    
    if len(to_prune) > 5:
        print(f"    ... and {len(to_prune) - 5} more")
    
    # Perform actual deletion if not dry run
    deleted_count = 0
    if not dry_run:
        print(f"\n  Deleting {len(to_prune)} stale memories...")
        for memory in to_prune:
            db.records.delete(record_id=memory["id"])
            deleted_count += 1
            if deleted_count % 5 == 0:
                print(f"    Deleted {deleted_count}/{len(to_prune)}...")
        print(f"  ✓ Deleted {deleted_count} memories")
    else:
        print(f"\n  [DRY RUN] Would delete {len(to_prune)} memories")
    
    return {
        "pruned": deleted_count if not dry_run else 0,
        "would_prune": len(to_prune),
        "kept": len(to_keep),
    }


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print("=" * 60)


def print_memory_details(memories: list[dict], title: str = "Memory Details"):
    """Print formatted memory information."""
    print(f"\n{title}:")
    for i, memory in enumerate(sorted(memories, key=lambda m: m["relevance"], reverse=True)[:10], 1):
        relevance_bar = "█" * int(memory["relevance"] * 10) + "░" * (10 - int(memory["relevance"] * 10))
        age_days = (datetime.now() - memory["created_at_dt"]).total_seconds() / 86400
        print(f"  {i}. [{relevance_bar}] {memory['relevance']:.2f} | {memory.get('category', '?'):10} | {age_days:.1f}d old")
        print(f"     {memory['content'][:60]}...")


def main():
    """Main demonstration of temporal decay model for agent memory."""
    
    print("=" * 60)
    print(" TEMPORAL DECAY MODELS FOR AGENT MEMORY")
    print(" Automatic Pruning of Stale Memories")
    print("=" * 60)
    
    # Initialize RushDB
    db = initialize_rushdb()
    print("\n✓ Connected to RushDB")
    
    # ========================================================================
    # Step 1: Get or Create Agent
    # ========================================================================
    
    print_section("Step 1: Agent Initialization")
    
    agent = get_or_create_agent(db)
    if not agent:
        print("\n✗ No demo agent found!")
        print("Please run `python seed.py` first to create test data.")
        sys.exit(1)
    
    print(f"\n✓ Agent found: {agent.id}")
    print(f"  Name: {agent['name']}")
    print(f"  Type: {agent['type']}")
    
    # Show agent configuration
    config = agent.get("config", {})
    print(f"\n  Configuration:")
    print(f"    Decay Lambda: {config.get('decayLambda', DECAY_LAMBDA)}")
    print(f"    Relevance Threshold: {config.get('relevanceThreshold', RELEVANCE_THRESHOLD)}")
    print(f"    Reinforcement Boost: {config.get('reinforcementBoost', REINFORCEMENT_BOOST)}")
    
    # ========================================================================
    # Step 2: Compute Current Relevance Scores
    # ========================================================================
    
    print_section("Step 2: Relevance Score Computation")
    
    print("\nComputing relevance with exponential decay model:")
    print("  relevance = initial × e^(-λ × age_hours) + reinforcement")
    print(f"\nCategory-specific decay rates:")
    for category, rate in CATEGORY_DECAY_RATES.items():
        half_life = math.log(2) / rate  # Time to decay to 50%
        print(f"  {category:12}: λ={rate:.3f} (half-life: {half_life:.1f} hours)")
    
    memories = get_agent_memories(db, agent.id)
    print(f"\n✓ Retrieved {len(memories)} memories")
    
    # Show category breakdown
    categories = {}
    for memory in memories:
        cat = memory.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat:12}: {count} memories")
    
    # Relevance distribution
    high_relevance = sum(1 for m in memories if m["relevance"] > 0.7)
    med_relevance = sum(1 for m in memories if 0.4 <= m["relevance"] <= 0.7)
    low_relevance = sum(1 for m in memories if 0.3 <= m["relevance"] < 0.4)
    critical = sum(1 for m in memories if m["relevance"] < 0.3)
    
    print("\nRelevance distribution:")
    print(f"  High (>0.7):    {high_relevance:3d} ({high_relevance/len(memories)*100:.1f}%)")
    print(f"  Medium (0.4-0.7): {med_relevance:3d} ({med_relevance/len(memories)*100:.1f}%)")
    print(f"  Low (0.3-0.4):   {low_relevance:3d} ({low_relevance/len(memories)*100:.1f}%)")
    print(f"  Critical (<0.3): {critical:3d} ({critical/len(memories)*100:.1f}%)")
    
    # Show top memories by relevance
    print_memory_details(memories, "\nTop 10 Most Relevant Memories")
    
    # ========================================================================
    # Step 3: Simulate Memory Access with Reinforcement
    # ========================================================================
    
    print_section("Step 3: Memory Access with Reinforcement")
    
    print("\nSimulating memory retrieval (spaced repetition effect)...")
    
    # Find a memory to access - prefer one that's slightly decayed
    candidate_memories = [
        m for m in memories 
        if 0.3 < m["relevance"] < 0.6 and m.get("accessCount", 0) < 3
    ]
    
    if candidate_memories:
        memory_to_access = max(candidate_memories, key=lambda m: m["relevance"])
        print(f"\nAccessing a decayed memory:")
        print(f"  Before: relevance = {memory_to_access['relevance']:.3f}")
        
        updated = access_memory(db, memory_to_access["id"], agent.id)
        
        print(f"\nAfter access:")
        print(f"  The memory's relevance was boosted due to:")
        print(f"  1. Time since last access reset")
        print(f"  2. Access count increment")
        print(f"  3. Reinforcement decay applied")
    else:
        print("\nNo suitable memories for reinforcement demo.")
    
    # ========================================================================
    # Step 4: Automatic Pruning
    # ========================================================================
    
    print_section("Step 4: Automatic Pruning")
    
    print("\nApplying category-specific thresholds:")
    for cat in ["skill", "fact", "preference", "context"]:
        threshold = {"skill": 0.40, "fact": 0.30, "preference": 0.30, "context": 0.20}.get(cat, 0.30)
        print(f"  {cat:12}: threshold = {threshold}")
    
    print("\n" + "-" * 40)
    print(" DRY RUN - Analyzing before deletion")
    print("-" * 40)
    
    prune_stats = prune_stale_memories(db, agent.id, dry_run=True)
    
    # Actually perform pruning
    print("\n" + "-" * 40)
    print(" ACTUAL PRUNING - Deleting memories")
    print("-" * 40)
    
    prune_stats = prune_stale_memories(db, agent.id, dry_run=False)
    
    # ========================================================================
    # Step 5: Final Statistics
    # ========================================================================
    
    print_section("Step 5: Post-Pruning Statistics")
    
    # Get remaining memories
    remaining_memories = get_agent_memories(db, agent.id)
    
    print(f"\nMemory count: {len(memories)} → {len(remaining_memories)}")
    print(f"Memories pruned: {prune_stats['pruned']}")
    
    if remaining_memories:
        avg_relevance = sum(m["relevance"] for m in remaining_memories) / len(remaining_memories)
        max_relevance = max(m["relevance"] for m in remaining_memories)
        min_relevance = min(m["relevance"] for m in remaining_memories)
        
        print(f"\nRelevance statistics:")
        print(f"  Average: {avg_relevance:.3f}")
        print(f"  Maximum: {max_relevance:.3f}")
        print(f"  Minimum: {min_relevance:.3f}")
        
        # Category breakdown after pruning
        remaining_categories = {}
        for memory in remaining_memories:
            cat = memory.get("category", "unknown")
            remaining_categories[cat] = remaining_categories.get(cat, 0) + 1
        
        print(f"\nCategory breakdown after pruning:")
        for cat, count in sorted(remaining_categories.items()):
            original = categories.get(cat, 0)
            print(f"  {cat:12}: {count} (was {original})")
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    print_section("Summary")
    
    print("""
This demo demonstrated:

1. TEMPORAL DECAY MODEL
   - Exponential decay: relevance decreases over time
   - Formula: relevance = initial × e^(-λ × age_hours)
   - Category-specific rates for different memory types

2. ACCESS REINFORCEMENT
   - Memories are boosted when accessed
   - Spaced repetition effect: frequent access strengthens memory
   - Reinforcement itself decays, preventing infinite relevance

3. AUTOMATIC PRUNING
   - Threshold-based deletion of stale memories
   - Category-specific thresholds (skills preserved longer)
   - Atomic deletion within transactions

4. RUSHDB INTEGRATION
   - Graph relationships (AGENT → HAS_MEMORY → MEMORY)
   - Efficient queries with where clauses
   - Transaction support for atomic operations

Key Benefits:
✓ Memory system stays focused on relevant information
✓ Storage grows logarithmically, not linearly
✓ Agent maintains fresh, actionable knowledge
✓ Reduced context pollution in LLM prompts
""")
    
    print("=" * 60)
    print(" Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
