#!/usr/bin/env python3
"""
Time-Decay Scoring Tutorial for RushDB

This module demonstrates how to implement recency-aware retrieval using
time-decay scoring in RushDB's graph-stored memories.

Topics covered:
1. Decay function implementations (exponential, logarithmic, halflife)
2. Temporal metadata storage for efficient decay queries
3. Combining semantic search with time-decay scoring
4. Decay on edge weights vs node properties
5. Parameter tuning and testing
"""

import os
import math
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import RushDB SDK
from rushdb import RushDB

# ============================================================================
# PART 1: DECAY FUNCTION IMPLEMENTATIONS
# ============================================================================

def exponential_decay(base_score: float, hours_elapsed: float, decay_rate: float) -> float:
    """
    Exponential decay: score decreases exponentially over time.
    
    Formula: score * e^(-λ * t)
    
    Best for: rapid information decay (social feeds, notifications, chat history)
    
    Args:
        base_score: Original importance/relevance score
        hours_elapsed: Time since creation in hours
        decay_rate: Decay constant (higher = faster decay)
                   Use get_decay_rate_from_halflife() to convert from halflife
    
    Returns:
        Decayed score (always >= 0)
    
    Example:
        >>> exponential_decay(10.0, 24, 0.029)  # 24h with 24h halflife
        5.0
    """
    return base_score * math.exp(-decay_rate * hours_elapsed)


def logarithmic_decay(base_score: float, hours_elapsed: float, scale: float = 1.0) -> float:
    """
    Logarithmic decay: score decreases slowly, diminishing over time.
    
    Formula: score / (1 + log(1 + t/scale))
    
    Best for: slow decay (knowledge bases, documentation, long-term memories)
    
    Args:
        base_score: Original importance/relevance score
        hours_elapsed: Time since creation in hours
        scale: Scaling factor (higher = slower initial decay)
    
    Returns:
        Decayed score (always >= 0)
    
    Example:
        >>> logarithmic_decay(10.0, 168, scale=24)  # 1 week with 24h scale
        ~3.8
    """
    if hours_elapsed < 0:
        hours_elapsed = 0
    return base_score / (1 + math.log(1 + hours_elapsed / scale))


def halflife_decay(base_score: float, hours_elapsed: float, half_life_hours: float) -> float:
    """
    Halflife decay: score halves every `half_life_hours`.
    
    Formula: score * 0.5^(t / halflife)
    
    Best for: predictable, tunable decay (spaced repetition, content curation)
    
    Args:
        base_score: Original importance/relevance score
        hours_elapsed: Time since creation in hours
        half_life_hours: Time for score to decay to 50%
    
    Returns:
        Decayed score (always >= 0)
    
    Example:
        >>> halflife_decay(10.0, 24, 24)  # 24h halflife at 24h elapsed
        5.0
    """
    if hours_elapsed < 0:
        hours_elapsed = 0
    if half_life_hours <= 0:
        return 0.0
    return base_score * math.pow(0.5, hours_elapsed / half_life_hours)


def linear_decay(base_score: float, hours_elapsed: float, max_hours: float) -> float:
    """
    Linear decay: score decreases linearly until max_hours, then zero.
    
    Formula: max(0, score * (1 - t / max_hours))
    
    Best for: hard cutoff after expiration (temporary permissions, TTL-based)
    
    Args:
        base_score: Original importance/relevance score
        hours_elapsed: Time since creation in hours
        max_hours: Time until score reaches zero
    
    Returns:
        Decayed score (0 to base_score)
    
    Example:
        >>> linear_decay(10.0, 12, 24)  # Halfway through 24h window
        5.0
    """
    if hours_elapsed >= max_hours:
        return 0.0
    if hours_elapsed < 0:
        hours_elapsed = 0
    return base_score * (1 - hours_elapsed / max_hours)


def get_decay_rate_from_halflife(half_life_hours: float) -> float:
    """
    Convert halflife period to exponential decay rate (lambda).
    
    λ = ln(2) / halflife
    
    Args:
        half_life_hours: Time for score to decay to 50%
    
    Returns:
        Exponential decay rate constant
    """
    return math.log(2) / half_life_hours


# ============================================================================
# PART 2: RUSSDB QUERY FUNCTIONS WITH DECAY
# ============================================================================

class TimeDecayScorer:
    """
    Time-decay scoring engine for RushDB memory retrieval.
    
    This class provides methods to:
    - Fetch records with temporal metadata
    - Calculate decayed scores using various decay functions
    - Combine semantic search with time-decay
    - Handle edge-weighted decay
    """
    
    # Default halflives by memory type (in hours)
    DEFAULT_HALFLIVES = {
        "quick_note": 24,       # 1 day
        "project_doc": 168,     # 1 week
        "knowledge_base": 720,  # 1 month
        "user_preference": 336, # 2 weeks
    }
    
    def __init__(self, db: RushDB):
        """
        Initialize the scorer with a RushDB client.
        
        Args:
            db: RushDB client instance
        """
        self.db = db
    
    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO timestamp string to datetime.
        
        Handles various ISO formats that RushDB might return.
        """
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        
        # Try parsing ISO format
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
        
        # Fallback to current time for invalid timestamps
        return datetime.utcnow()
    
    def get_hours_elapsed(self, created_at: str) -> float:
        """
        Calculate hours elapsed since creation.
        
        Args:
            created_at: ISO timestamp string
        
        Returns:
            Hours elapsed (float)
        """
        created = self.parse_timestamp(created_at)
        elapsed = datetime.utcnow() - created
        return max(0, elapsed.total_seconds() / 3600)
    
    def calculate_composite_score(
        self,
        record: dict,
        decay_method: str = "halflife",
        decay_param: float = None,
        semantic_weight: float = 0.5
    ) -> dict:
        """
        Calculate composite score combining importance and time decay.
        
        Args:
            record: RushDB record with 'importance' and 'created_at' fields
            decay_method: 'exponential', 'logarithmic', 'halflife', or 'linear'
            decay_param: Method-specific parameter (halflife hours, etc.)
            semantic_weight: Weight for semantic score (0-1), importance gets 1-weight
        
        Returns:
            Dict with original record, decayed scores, and metadata
        """
        # Extract base importance (1-10 scale)
        importance = float(record.data.get("importance", 5))
        
        # Calculate semantic score if available
        semantic_score = record.score if hasattr(record, 'score') and record.score else 0.0
        
        # Calculate hours elapsed
        created_at = record.data.get("created_at", datetime.utcnow().isoformat())
        hours_elapsed = self.get_hours_elapsed(created_at)
        
        # Get memory type for halflife lookup
        memory_type = record.data.get("memory_type", "project_doc")
        
        # Calculate time-decayed importance
        if decay_method == "exponential":
            if decay_param is None:
                decay_param = get_decay_rate_from_halflife(
                    self.DEFAULT_HALFLIVES.get(memory_type, 168)
                )
            time_decayed = exponential_decay(importance, hours_elapsed, decay_param)
        elif decay_method == "logarithmic":
            if decay_param is None:
                decay_param = 24  # 24-hour scale
            time_decayed = logarithmic_decay(importance, hours_elapsed, decay_param)
        elif decay_method == "linear":
            if decay_param is None:
                decay_param = self.DEFAULT_HALFLIVES.get(memory_type, 168) * 2
            time_decayed = linear_decay(importance, hours_elapsed, decay_param)
        else:  # halflife (default)
            if decay_param is None:
                decay_param = self.DEFAULT_HALFLIVES.get(memory_type, 168)
            time_decayed = halflife_decay(importance, hours_elapsed, decay_param)
        
        # Calculate composite score
        # Normalize semantic score to 0-10 scale
        normalized_semantic = semantic_score * 10 if semantic_score else 0.0
        
        composite = (
            (1 - semantic_weight) * time_decayed +
            semantic_weight * normalized_semantic
        )
        
        return {
            "record": record,
            "importance": importance,
            "time_decayed": time_decayed,
            "semantic_score": semantic_score,
            "composite_score": composite,
            "hours_elapsed": hours_elapsed,
            "decay_method": decay_method,
        }
    
    def fetch_memories_with_decay(
        self,
        memory_type: str = None,
        topic: str = None,
        limit: int = 20,
        decay_method: str = "halflife",
        decay_param: float = None
    ) -> list:
        """
        Fetch memories and apply time-decay scoring.
        
        Args:
            memory_type: Filter by memory type (optional)
            topic: Filter by topic via relationship (optional)
            limit: Maximum records to return
            decay_method: Decay function to use
            decay_param: Decay parameter (e.g., halflife hours)
        
        Returns:
            List of scored records sorted by composite score
        """
        # Build query
        query = {"labels": ["MEMORY"], "limit": limit * 2}  # Fetch extra for filtering
        
        if memory_type:
            query["where"] = {"memory_type": memory_type}
        
        if topic:
            if "where" not in query:
                query["where"] = {}
            query["where"]["CONCEPT"] = {"name": topic}
        
        # Fetch from RushDB
        results = self.db.records.find(query)
        
        # Apply decay scoring
        scored = [
            self.calculate_composite_score(
                record, decay_method, decay_param
            )
            for record in results.data
        ]
        
        # Sort by composite score and limit
        scored.sort(key=lambda x: x["composite_score"], reverse=True)
        return scored[:limit]
    
    def semantic_search_with_decay(
        self,
        query_text: str,
        limit: int = 10,
        decay_method: str = "halflife",
        semantic_weight: float = 0.6
    ) -> list:
        """
        Combine semantic search with time-decay scoring.
        
        This is the key method for recency-aware retrieval:
        - Semantic search finds relevant content
        - Time decay boosts recent, important memories
        
        Args:
            query_text: Natural language query
            limit: Maximum results to return
            decay_method: Decay function to use
            semantic_weight: Weight for semantic relevance (1-decay_weight)
        
        Returns:
            List of scored records with semantic + decay scores
        """
        # Perform semantic search
        # Note: Requires a vector index on the 'content' property
        # For this tutorial, we'll use regular find if search isn't available
        try:
            search_results = self.db.ai.search({
                "propertyName": "content",
                "query": query_text,
                "labels": ["MEMORY"],
                "limit": limit * 2
            })
            records = search_results.data
        except Exception as e:
            # Fallback to regular find if vector index doesn't exist
            print(f"  (Semantic search unavailable: {e})")
            find_results = self.db.records.find({
                "labels": ["MEMORY"],
                "limit": limit * 2
            })
            records = find_results.data
        
        # Apply decay scoring
        scored = [
            self.calculate_composite_score(
                record, decay_method, semantic_weight=semantic_weight
            )
            for record in records
        ]
        
        # Sort by composite score
        scored.sort(key=lambda x: x["composite_score"], reverse=True)
        return scored[:limit]


# ============================================================================
# PART 3: EDGE-WEIGHTED DECAY (GRAPH TRAVERSAL)
# ============================================================================

def fetch_memories_by_concept_with_edge_decay(
    db: RushDB,
    concept_name: str,
    decay_method: str = "halflife",
    edge_decay_factor: float = 0.5
) -> list:
    """
    Fetch memories about a concept with decay applied to edge weights.
    
    This demonstrates decay on relationships (edges) rather than nodes.
    The edge between MEMORY and CONCEPT can carry temporal metadata
    that affects retrieval priority.
    
    Args:
        db: RushDB client
        concept_name: Name of the concept to filter by
        decay_method: Decay function for edge weights
        edge_decay_factor: Base factor for edge weight decay
    
    Returns:
        List of memories with edge-weighted scores
    """
    # Find the concept
    concepts = db.records.find({
        "labels": ["CONCEPT"],
        "where": {"name": concept_name}
    })
    
    if not concepts.data:
        return []
    
    concept = concepts.data[0]
    
    # Find memories related to this concept
    # RushDB's related record filtering syntax
    memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "CONCEPT": {
                "$relation": {"type": "ABOUT", "direction": "in"},
                "name": concept_name
            }
        },
        "limit": 50
    })
    
    results = []
    for memory in memories.data:
        # Get node importance
        importance = float(memory.data.get("importance", 5))
        created_at = memory.data.get("created_at", datetime.utcnow().isoformat())
        
        # Calculate hours elapsed
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            hours_elapsed = (datetime.utcnow() - created).total_seconds() / 3600
        except (ValueError, AttributeError):
            hours_elapsed = 0
        
        # Apply node decay
        if decay_method == "halflife":
            node_score = halflife_decay(importance, hours_elapsed, 168)
        elif decay_method == "exponential":
            node_score = exponential_decay(importance, hours_elapsed, get_decay_rate_from_halflife(168))
        else:
            node_score = halflife_decay(importance, hours_elapsed, 168)
        
        # Apply edge decay (relationship is "older" if memory was created long ago)
        # This simulates the idea that edges can carry their own temporal weight
        if decay_method == "halflife":
            edge_score = halflife_decay(1.0, hours_elapsed, 336)  # Edges decay slower
        else:
            edge_score = 1.0
        
        # Combined score with edge weight
        combined = node_score * (edge_decay_factor * edge_score + (1 - edge_decay_factor))
        
        results.append({
            "memory": memory,
            "node_score": node_score,
            "edge_score": edge_score,
            "combined_score": combined,
            "hours_elapsed": hours_elapsed,
        })
    
    # Sort by combined score
    results.sort(key=lambda x: x["combined_score"], reverse=True)
    return results


# ============================================================================
# PART 4: DECAY PARAMETER TUNING
# ============================================================================

def tune_decay_parameters(
    db: RushDB,
    decay_methods: list = None,
    sample_size: int = 20
) -> dict:
    """
    Compare different decay parameters and show their effects.
    
    This helps you understand how different decay settings affect
    retrieval results and choose the right parameters for your use case.
    
    Args:
        db: RushDB client
        decay_methods: List of methods to compare
        sample_size: Number of records to sample
    
    Returns:
        Dictionary with tuning results
    """
    if decay_methods is None:
        decay_methods = ["halflife", "exponential", "logarithmic", "linear"]
    
    # Fetch sample memories
    memories = db.records.find({
        "labels": ["MEMORY"],
        "limit": sample_size
    })
    
    results = {
        "sample_count": len(memories.data),
        "by_method": {},
        "score_distribution": {},
    }
    
    # Parameters to test for each method
    test_params = {
        "halflife": [6, 24, 72, 168, 720],  # hours
        "exponential": [0.01, 0.029, 0.05, 0.1, 0.2],  # decay rates
        "logarithmic": [6, 24, 72, 168],  # scale factors
        "linear": [48, 168, 336, 720],  # max hours
    }
    
    for method in decay_methods:
        if method not in test_params:
            continue
        
        results["by_method"][method] = {}
        
        for param in test_params[method]:
            scores = []
            
            for memory in memories.data:
                importance = float(memory.data.get("importance", 5))
                created_at = memory.data.get("created_at", datetime.utcnow().isoformat())
                
                try:
                    created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    hours_elapsed = (datetime.utcnow() - created).total_seconds() / 3600
                except (ValueError, AttributeError):
                    hours_elapsed = 0
                
                if method == "halflife":
                    score = halflife_decay(importance, hours_elapsed, param)
                elif method == "exponential":
                    score = exponential_decay(importance, hours_elapsed, param)
                elif method == "logarithmic":
                    score = logarithmic_decay(importance, hours_elapsed, param)
                elif method == "linear":
                    score = linear_decay(importance, hours_elapsed, param)
                else:
                    score = importance
                
                scores.append(score)
            
            if scores:
                results["by_method"][method][str(param)] = {
                    "mean": sum(scores) / len(scores),
                    "max": max(scores),
                    "min": min(scores),
                    "zero_count": sum(1 for s in scores if s == 0),
                }
    
    return results


# ============================================================================
# PART 5: DEMONSTRATION
# ============================================================================

def print_separator(title: str):
    """Print a formatted section separator."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_scored_results(results: list, max_items: int = 10):
    """Print formatted scored results."""
    for i, item in enumerate(results[:max_items], 1):
        if "record" in item:  # From TimeDecayScorer
            record = item["record"]
            print(f"\n  [{i}] {record.data.get('memory_type', 'unknown'):15} "
                  f"score: {item['composite_score']:.3f} "
                  f"(importance: {item['importance']:.1f}, "
                  f"decayed: {item['time_decayed']:.3f}, "
                  f"age: {item['hours_elapsed']:.1f}h)")
            content = record.data.get('content', '')[:60]
            print(f"      {content}...")
        elif "memory" in item:  # From edge decay
            memory = item["memory"]
            print(f"\n  [{i}] combined: {item['combined_score']:.3f} "
                  f"(node: {item['node_score']:.3f}, "
                  f"edge: {item['edge_score']:.3f}, "
                  f"age: {item['hours_elapsed']:.1f}h)")
            content = memory.data.get('content', '')[:60]
            print(f"      {content}...")


def demonstrate_decay_functions():
    """
    Part 1: Demonstrate all decay function implementations.
    """
    print_separator("PART 1: DECAY FUNCTION COMPARISONS")
    
    # Test parameters
    base_score = 10.0
    hours_test_points = [0, 6, 12, 24, 48, 72, 168, 336, 720]
    
    # 24-hour halflife parameters
    halflife_24h = 24.0
    exp_rate_24h = get_decay_rate_from_halflife(halflife_24h)
    
    print("\nComparing decay functions with 24-hour halflife/rate:")
    print(f"{'Hours':>6} {'Exponential':>12} {'Logarithmic':>12} {'Halflife':>12} {'Linear*':>12}")
    print("-" * 60)
    
    # Linear uses 48h max for comparison (2x halflife)
    for hours in hours_test_points:
        exp = exponential_decay(base_score, hours, exp_rate_24h)
        log = logarithmic_decay(base_score, hours, scale=24)
        half = halflife_decay(base_score, hours, halflife_24h)
        linear = linear_decay(base_score, hours, max_hours=48)
        
        print(f"{hours:>6} {exp:>12.3f} {log:>12.3f} {half:>12.3f} {linear:>12.3f}")
    
    print("\n* Linear uses 48h max_hours for 2x halflife comparison")
    
    # Show different halflives
    print("\n\nHalflife decay at different periods:")
    print(f"{'Hours':>6} {'6h HL':>10} {'24h HL':>10} {'168h HL':>10} {'720h HL':>10}")
    print("-" * 50)
    
    for hours in [0, 6, 12, 24, 48, 168, 336, 720, 1440]:
        h6 = halflife_decay(base_score, hours, 6)
        h24 = halflife_decay(base_score, hours, 24)
        h168 = halflife_decay(base_score, hours, 168)
        h720 = halflife_decay(base_score, hours, 720)
        print(f"{hours:>6} {h6:>10.3f} {h24:>10.3f} {h168:>10.3f} {h720:>10.3f}")


def demonstrate_temporal_queries(db: RushDB):
    """
    Part 2: Fetch memories with temporal metadata and apply decay.
    """
    print_separator("PART 2: TEMPORAL METADATA & DECAY SCORING")
    
    scorer = TimeDecayScorer(db)
    
    # Show raw importance vs time-decayed importance
    print("\nFetching all memories and comparing raw vs decayed scores:")
    print("(Using halflife decay with type-specific halflives)")
    
    # Fetch a sample of each memory type
    for memory_type in ["quick_note", "project_doc", "knowledge_base", "user_preference"]:
        print(f"\n  --- {memory_type.upper().replace('_', ' ')} ---")
        
        results = scorer.fetch_memories_with_decay(
            memory_type=memory_type,
            limit=3,
            decay_method="halflife"
        )
        
        if not results:
            print("    (No records found)")
            continue
        
        for item in results[:3]:
            record = item["record"]
            print(f"    Raw importance: {item['importance']:.1f} -> "
                  f"Decayed: {item['time_decayed']:.3f} "
                  f"(age: {item['hours_elapsed']:.1f}h)")


def demonstrate_semantic_with_decay(db: RushDB):
    """
    Part 3: Combine semantic search with time-decay.
    """
    print_separator("PART 3: SEMANTIC SEARCH + TIME-DECAY")
    
    scorer = TimeDecayScorer(db)
    
    # Try semantic search with decay
    print("\nSearching for 'performance optimization' with time-decay:")
    print("(Combines semantic relevance with recency weighting)")
    
    results = scorer.semantic_search_with_decay(
        query_text="performance optimization",
        limit=10,
        decay_method="halflife",
        semantic_weight=0.6
    )
    
    if results:
        print("\nTop results (semantic + decay weighted):")
        print_scored_results(results, max_items=5)
    else:
        print("\n  (No results - try running seed.py first)")
    
    # Compare different semantic weights
    print("\n\nComparing semantic weight effects:")
    print("-" * 50)
    
    for weight in [0.0, 0.3, 0.6, 1.0]:
        results = scorer.semantic_search_with_decay(
            query_text="meeting notes",
            limit=5,
            decay_method="halflife",
            semantic_weight=weight
        )
        if results:
            top_score = results[0]["composite_score"]
            print(f"  Weight {weight:.1f}: top composite score = {top_score:.3f}")


def demonstrate_edge_decay(db: RushDB):
    """
    Part 4: Edge-weighted decay with graph traversal.
    """
    print_separator("PART 4: EDGE-WEIGHTED DECAY (GRAPH TRAVERSAL)")
    
    # Get available concepts
    concepts = db.labels.find({"where": {"name": {"$in": ["CONCEPT"]}}}
    )
    
    concept_results = db.records.find({"labels": ["CONCEPT"], "limit": 5})
    
    if not concept_results.data:
        print("\n  (No CONCEPT nodes found - try running seed.py first)")
        return
    
    # Pick a concept
    topic = concept_results.data[0].data.get("name", "machine_learning")
    
    print(f"\nFetching memories about '{topic}' with edge-weighted decay:")
    print("(Edge decay factor: 0.5 - edges contribute 50% to final score)")
    
    results = fetch_memories_by_concept_with_edge_decay(
        db,
        concept_name=topic,
        decay_method="halflife",
        edge_decay_factor=0.5
    )
    
    if results:
        print(f"\nFound {len(results)} related memories. Top 5 by combined score:")
        print_scored_results(results, max_items=5)
        
        print("\n\nScore breakdown (node vs edge contribution):")
        for item in results[:3]:
            print(f"  Node: {item['node_score']:.3f} + "
                  f"Edge: {item['edge_score']:.3f} = "
                  f"Combined: {item['combined_score']:.3f}")
    else:
        print("\n  (No memories found for this concept)")


def demonstrate_parameter_tuning(db: RushDB):
    """
    Part 5: Tune and compare decay parameters.
    """
    print_separator("PART 5: DECAY PARAMETER TUNING")
    
    print("\nComparing decay methods and parameters on sample data:")
    
    results = tune_decay_parameters(db, sample_size=20)
    
    print(f"\nSample size: {results['sample_count']} records")
    
    for method, params in results["by_method"].items():
        print(f"\n  {method.upper()} DECAY:")
        print(f"  {'Parameter':>12} {'Mean':>10} {'Max':>10} {'Zero Count':>12}")
        print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*12}")
        
        for param_str, stats in params.items():
            print(f"  {param_str:>12} {stats['mean']:>10.3f} "
                  f"{stats['max']:>10.3f} {stats['zero_count']:>12}")
    
    print("\n\nTuning tips:")
    print("  - Use 'zero_count' to find parameters that fully decay old records")
    print("  - Higher 'mean' keeps more historical weight in results")
    print("  - Linear decay zeros out after max_hours (hard cutoff)")
    print("  - Halflife is most predictable for user expectations")


def demonstrate_halflife_by_use_case():
    """
    Part 6: Recommended halflives for different use cases.
    """
    print_separator("PART 6: RECOMMENDED HALFLIVES BY USE CASE")
    
    use_cases = [
        ("Chat messages / Notifications", 4, 24, "Messages lose relevance quickly"),
        ("Social media posts", 24, 72, "Viral content peaks in 1-3 days"),
        ("News articles", 48, 168, "News has ~1 week relevance window"),
        ("Project documentation", 168, 720, "Docs relevant for weeks to months"),
        ("Knowledge base articles", 720, 2160, "Long-term knowledge, slower decay"),
        ("User preferences", 336, 720, "Preferences semi-stable over weeks"),
        ("Legal / Compliance records", 8760, None, "Year+ halflife or no decay"),
    ]
    
    print("\n{:<35} {:>12} {:>12}  {}".format("Use Case", "Min (hours)", "Max (hours)", "Notes"))
    print("-" * 90)
    
    for use_case, min_hl, max_hl, notes in use_cases:
        max_str = str(max_hl) if max_hl else "∞"
        print(f"{use_case:<35} {min_hl:>12} {max_str:>12}  {notes}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the tutorial."""
    print("\n" + "#" * 70)
    print("#" + " " * 68 + "#")
    print("#   TIME-DECAY SCORING IN RUSHDB GRAPH-STORED MEMORIES")
    print("#   A Complete Implementation Guide")
    print("#" + " " * 68 + "#")
    print("#" * 70)
    
    # Initialize RushDB client
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("\nERROR: RUSHDB_API_TOKEN not found in environment!")
        print("Please copy .env.example to .env and add your API token.")
        return
    
    url = os.getenv("RUSHDB_URL")
    if url:
        db = RushDB(api_token, url=url)
    else:
        db = RushDB(api_token)
    
    print(f"\n✓ Connected to RushDB")
    
    # Run all demonstrations
    demonstrate_decay_functions()
    demonstrate_temporal_queries(db)
    demonstrate_semantic_with_decay(db)
    demonstrate_edge_decay(db)
    demonstrate_parameter_tuning(db)
    demonstrate_halflife_by_use_case()
    
    # Summary
    print_separator("SUMMARY: KEY TAKEAWAYS")
    print("""
    1. CHOOSE YOUR DECAY FUNCTION WISELY:
       - Exponential: Fast decay, good for real-time data
       - Halflife: Predictable decay, easiest to tune
       - Logarithmic: Slow decay, good for knowledge bases
       - Linear: Hard cutoff, good for TTL-based data

    2. STORE TEMPORAL METADATA CORRECTLY:
       - Always include 'created_at' (ISO 8601 format)
       - Use type-specific halflives for different content types
       - Consider 'updated_at' for mutable content

    3. COMBINE SEMANTIC + DECAY:
       - Use semantic_weight parameter to balance relevance vs recency
       - For discovery: higher semantic weight
       - For recency-sensitive: higher decay weight

    4. EDGE VS NODE DECAY:
       - Node decay: importance/quality of the memory itself
       - Edge decay: relevance of the relationship over time
       - Combined approach gives nuanced retrieval

    5. TUNE ON YOUR DATA:
       - Use tune_decay_parameters() to compare settings
       - Consider zero_count to identify overly-aggressive decay
       - Match halflife to content update frequency
    """)
    
    print("\n✓ Tutorial complete! Check the code for implementation details.")


if __name__ == "__main__":
    main()
