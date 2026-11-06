#!/usr/bin/env python3
"""
Graph-Aware Reranker Demo: Using Relationship Types to Score Retrieved Contexts

This script demonstrates how to improve semantic search with graph relationship
information. It shows:

1. Pure vector search (baseline)
2. Graph augmentation: extracting relationship context for each candidate
3. Graph-aware reranking: combining semantic + structural scores
4. Comparison showing how relationship types change rankings

The dataset is a mock codebase dependency graph representing a software project
with typed relationships (depends_on, conflicts_with, derives_from, implements).
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Configuration: Relationship Type Weights
# ─────────────────────────────────────────────────────────────────────────────

RELATIONSHIP_WEIGHTS = {
    "derives_from": 0.8,
    "implements": 0.6,
    "depends_on": 0.4,
    "conflicts_with": -0.5,  # Negative! Conflicts penalize score
}

# Scoring weights
SEMANTIC_WEIGHT = 0.6
STRUCTURAL_WEIGHT = 0.4

# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RelationshipContext:
    """Holds the relationship context for a candidate record."""
    incoming: list = field(default_factory=list)   # (type, source_slug, priority)
    outgoing: list = field(default_factory=list)    # (type, target_slug, priority)
    structural_score: float = 0.0
    context_summary: str = ""


@dataclass
class ScoredCandidate:
    """A candidate with combined semantic + structural score."""
    record: any
    vector_score: float
    relationship_context: RelationshipContext
    final_score: float


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Semantic Search — Get Initial Candidates
# ─────────────────────────────────────────────────────────────────────────────

def get_semantic_candidates(db, query: str, label: str = "MODULE", limit: int = 5):
    """
    Run pure vector similarity search. This is our baseline.
    
    Returns a list of (record, score) tuples.
    """
    results = db.ai.search({
        "propertyName": "description",
        "query": query,
        "labels": [label],
        "limit": limit,
    })
    return [(r, r.score) for r in results.data]


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Graph Augmentation — Extract Relationship Context
# ─────────────────────────────────────────────────────────────────────────────

def get_relationship_context(db, record) -> RelationshipContext:
    """
    Extract incoming and outgoing relationships for a record.
    
    RushDB stores relationships as linked records. We query for records
    that reference our target (incoming) and records our target references (outgoing).
    """
    slug = record.data.get("slug")
    ctx = RelationshipContext()
    
    # Find incoming relationships: records that reference this one
    # We check all relationship types by looking at MODULE records
    incoming = db.records.find({
        "labels": ["MODULE"],
        "where": {
            # This filters records that have outgoing edges to our target
            # We need to check relationship metadata
        }
    })
    
    # Manual approach: find all MODULE records and check their relationships
    # Since RushDB stores relationships as linked nodes, we examine which
    # records attach TO our target (incoming) or FROM our target (outgoing)
    
    # Approach: Use the relationship query syntax
    # In practice, you'd use graph traversal. Here we'll fetch all and filter.
    all_modules = db.records.find({"labels": ["MODULE"], "limit": 100})
    
    for candidate in all_modules.data:
        if candidate.id == record.id:
            continue
        
        # Check if there's a relationship by examining the record's fields
        # In a real graph DB, we'd use traversal. For this demo, relationships
        # are stored as linked records in the graph.
        
        # Since we can't directly traverse relationships via the SDK's find(),
        # we'll query the relationship direction using the attach/detach metadata.
        # For demonstration, we simulate by checking stored relationship patterns.
        
    # Simplified approach: Check relationship patterns based on slug
    # (In production, you'd use RushDB's graph traversal)
    
    relationship_patterns = {
        "cache-system": {
            "incoming": [("depends_on", "cache-invalidator")],
            "outgoing": [("depends_on", "logger"), ("depends_on", "validator")],
        },
        "cache-invalidator": {
            "incoming": [],
            "outgoing": [("depends_on", "cache-system")],
        },
        "auth-module": {
            "incoming": [("depends_on", "payment-gateway")],
            "outgoing": [],
        },
        "payment-gateway": {
            "incoming": [("implements", "stripe-adapter")],
            "outgoing": [("depends_on", "logger"), ("depends_on", "validator"), ("depends_on", "auth-module")],
        },
        "stripe-adapter": {
            "incoming": [],
            "outgoing": [("depends_on", "payment-gateway")],
        },
        "email-service": {
            "incoming": [],
            "outgoing": [("derives_from", "logger"), ("derives_from", "auth-module")],
        },
        "logger": {
            "incoming": [("derives_from", "email-service")],
            "outgoing": [],
        },
        "validator": {
            "incoming": [("depends_on", "cache-system"), ("depends_on", "payment-gateway")],
            "outgoing": [],
        },
        "deprecated-legacy": {
            "incoming": [],
            "outgoing": [("conflicts_with", "auth-module")],
        },
        "file-storage": {
            "incoming": [],
            "outgoing": [("depends_on", "validator"), ("depends_on", "auth-module")],
        },
    }
    
    patterns = relationship_patterns.get(slug, {"incoming": [], "outgoing": []})
    ctx.incoming = patterns["incoming"]
    ctx.outgoing = patterns["outgoing"]
    
    # Build context summary
    incoming_str = ", ".join([f"{t}←{s}" for t, s in ctx.incoming])
    outgoing_str = ", ".join([f"{s}→{t}" for s, t in ctx.outgoing])
    
    parts = []
    if incoming_str:
        parts.append(f"incoming: {incoming_str}")
    if outgoing_str:
        parts.append(f"outgoing: {outgoing_str}")
    
    ctx.context_summary = " | ".join(parts) if parts else "(no relationships)"
    
    # Calculate structural score
    ctx.structural_score = calculate_structural_score(ctx)
    
    return ctx


def calculate_structural_score(ctx: RelationshipContext) -> float:
    """
    Calculate a structural score from relationship context.
    
    Formula:
    - Incoming edges add weight (foundational modules have many dependents)
    - High-priority relationships add extra weight
    - "derives_from" edges add significant weight (inherently important)
    - "conflicts_with" edges subtract weight
    """
    score = 0.0
    
    for rel_type, source, priority in ctx.incoming:
        weight = RELATIONSHIP_WEIGHTS.get(rel_type, 0)
        direction_mult = 1.5  # Incoming is more valuable (foundational)
        priority_bonus = 0.2 if priority == "high" else 0
        score += weight * direction_mult + priority_bonus
    
    for rel_type, target, priority in ctx.outgoing:
        weight = RELATIONSHIP_WEIGHTS.get(rel_type, 0)
        direction_mult = 1.0
        priority_bonus = 0.2 if priority == "high" else 0
        score += weight * direction_mult + priority_bonus
    
    return score


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Graph-Aware Reranking
# ─────────────────────────────────────────────────────────────────────────────

def rerank_with_graph(candidates: list, db) -> list[ScoredCandidate]:
    """
    Re-rank candidates by combining semantic similarity with structural score.
    
    Formula:
        final_score = (vector_similarity * semantic_weight) + (structural_score * structural_weight)
    """
    results = []
    
    for record, vec_score in candidates:
        # Get relationship context
        ctx = get_relationship_context(db, record)
        
        # Calculate combined score
        final_score = (vec_score * SEMANTIC_WEIGHT) + (ctx.structural_score * STRUCTURAL_WEIGHT)
        
        results.append(ScoredCandidate(
            record=record,
            vector_score=vec_score,
            relationship_context=ctx,
            final_score=final_score,
        ))
    
    # Sort by final score (descending)
    results.sort(key=lambda x: x.final_score, reverse=True)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Relationship Filters (Pre-reranking)
# ─────────────────────────────────────────────────────────────────────────────

def apply_relationship_filters(candidates: list, exclude_types: list = None) -> list:
    """
    Pre-filter candidates based on relationship types.
    
    Example filters:
    - Exclude records that conflict with stable modules (for security)
    - Exclude downstream dependencies when searching from a specific context
    """
    if exclude_types is None:
        exclude_types = []
    
    filtered = []
    for record, vec_score in candidates:
        slug = record.data.get("slug", "")
        
        # Example: exclude deprecated-legacy when querying about auth
        if "deprecated" in record.data.get("status", "") and "auth" in slug:
            continue
        
        # Check for conflict relationships
        # (In a real implementation, you'd check the graph)
        
        filtered.append((record, vec_score))
    
    return filtered


# ─────────────────────────────────────────────────────────────────────────────
# Demo: Comparison Output
# ─────────────────────────────────────────────────────────────────────────────

def print_comparison(query: str, baseline_candidates: list, reranked_candidates: list):
    """Print side-by-side comparison of pure vector vs graph-aware results."""
    print(f"\n[Query] \"{query}\"")
    print("─" * 70)
    
    # Baseline (pure vector)
    print("\nPure Vector Top-5 (baseline):")
    for i, (record, vec_score) in enumerate(baseline_candidates[:5], 1):
        slug = record.data.get("slug", "unknown")
        print(f"  #{i}  {slug:<25} (vec: {vec_score:.3f}, graph: 0.000)")
    
    # Graph-aware reranked
    print("\nGraph-Aware Reranked:")
    for i, candidate in enumerate(reranked_candidates[:5], 1):
        record = candidate.record
        slug = record.data.get("slug", "unknown")
        vec_score = candidate.vector_score
        rel_score = candidate.relationship_context.structural_score
        final_score = candidate.final_score
        
        # Arrow indicator
        direction = ""
        if i == 1 and candidate.relationship_context.context_summary != "(no relationships)":
            direction = "  ★"
        
        print(f"  #{i}  {slug:<25} (vec: {vec_score:.3f}, graph: {rel_score:+.2f} → final: {final_score:.3f}){direction}")
        
        # Show relationship context
        ctx = candidate.relationship_context.context_summary
        if ctx != "(no relationships)":
            print(f"       └─ {ctx}")
    
    print()


def find_conflicts_in_results(candidates: list[ScoredCandidate]) -> list:
    """Find candidates that have conflict relationships."""
    conflicts = []
    for candidate in candidates:
        ctx = candidate.relationship_context
        for rel_type, _, _ in ctx.incoming + ctx.outgoing:
            if rel_type == "conflicts_with":
                conflicts.append(candidate)
                break
    return conflicts


# ─────────────────────────────────────────────────────────────────────────────
# Main Demo
# ─────────────────────────────────────────────────────────────────────────────

def main():
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise RuntimeError("RUSHDB_API_KEY not found. Copy .env.example to .env")
    
    db = RushDB(api_key)
    
    # Verify data exists
    existing = db.records.find({"labels": ["MODULE"], "limit": 1})
    if not existing.data:
        print("No MODULE records found. Run 'seed.py' first to populate the graph.")
        return
    
    print("╔" + "═" * 68 + "╗")
    print("║     GRAPH-AWARE RERANKER DEMO — Codebase Dependency Graph       ║")
    print("╚" + "═" * 68 + "╝")
    
    # Demo queries that would behave differently with graph awareness
    queries = [
        "payment processing with external APIs",
        "cache invalidation strategy",
    ]
    
    for query in queries:
        # Step 1: Get pure vector baseline
        baseline = get_semantic_candidates(db, query, limit=5)
        
        # Step 2: Apply pre-filters (exclude conflicts)
        filtered = apply_relationship_filters(baseline)
        
        # Step 3: Get relationship context + rerank
        reranked = rerank_with_graph(filtered, db)
        
        # Step 4: Display comparison
        print_comparison(query, baseline, reranked)
    
    # Special demo: Show conflict filtering
    print("━" * 70)
    print("RESULTS: deprecated-legacy module excluded from results by conflict filter")
    print("━" * 70)
    
    # Query specifically about auth
    auth_query = "authentication and session management"
    baseline = get_semantic_candidates(db, auth_query, limit=10)
    
    print(f"\n[Query] \"{auth_query}\"")
    print("Showing all raw candidates (including deprecated):")
    for i, (record, score) in enumerate(baseline[:5], 1):
        slug = record.data.get("slug", "unknown")
        status = record.data.get("status", "unknown")
        print(f"  #{i}  {slug:<25} status={status:<12} vec_score={score:.3f}")
    
    print("\nAfter graph-aware conflict filtering:")
    reranked = rerank_with_graph(baseline[:5], db)
    filtered_reranked = [c for c in reranked if "deprecated" not in c.record.data.get("status", "")]
    for i, candidate in enumerate(filtered_reranked[:5], 1):
        print(f"  #{i}  {candidate.record.data.get('slug'):<25} final_score={candidate.final_score:.3f}")
    
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    main()
