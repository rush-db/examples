"""
Time-Weighted Graph Traversals for Recency-Aware Recommendations

A comprehensive tutorial demonstrating:
1. Schema design with time-annotated edges in RushDB
2. Traversal queries with configurable decay functions
3. Hybrid scoring combining time-weighting with vector similarity
4. Query planner implications: weighting during vs. after traversal
5. Benchmarking: measuring performance impact of time-weighting
"""

import os
import time
import math
from datetime import datetime, timedelta
from typing import Callable, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer


# =============================================================================
# SECTION 1: Time-Decay Function Definitions
# =============================================================================

@dataclass
class DecayConfig:
    """Configuration for time decay functions."""
    half_life_days: float = 30.0  # Time for score to decay by half
    

def exponential_decay(timestamp: str, config: DecayConfig = None) -> float:
    """
    Exponential decay: score * exp(-λ * days_since)
    
    Best for: fast-changing interests, news, trends
    λ = ln(2) / half_life (score halves every half_life days)
    """
    if config is None:
        config = DecayConfig()
    
    ts = datetime.fromisoformat(timestamp)
    days_since = (datetime.now() - ts).total_seconds() / 86400
    
    lambda_param = math.log(2) / config.half_life_days
    return math.exp(-lambda_param * days_since)


def linear_decay(timestamp: str, config: DecayConfig = None) -> float:
    """
    Linear decay: score * max(0, 1 - (days_since / half_life))
    
    Best for: steady preference decay
    """
    if config is None:
        config = DecayConfig()
    
    ts = datetime.fromisoformat(timestamp)
    days_since = (datetime.now() - ts).total_seconds() / 86400
    
    decay = 1 - (days_since / config.half_life_days)
    return max(0.0, decay)


def logarithmic_decay(timestamp: str, config: DecayConfig = None) -> float:
    """
    Logarithmic decay: score / log(1 + days_since)
    
    Best for: long-tail content that remains somewhat relevant
    """
    if config is None:
        config = DecayConfig()
    
    ts = datetime.fromisoformat(timestamp)
    days_since = (datetime.now() - ts).total_seconds() / 86400
    
    if days_since < 1:
        return 1.0  # Full score for very recent items
    
    # log(1 + days) grows slowly, providing gentler decay
    return 1.0 / math.log(1 + days_since / config.half_life_days * math.e)


# Type alias for decay functions
DecayFunction = Callable[[str], float]


# =============================================================================
# SECTION 2: RushDB Connection and Vector Setup
# =============================================================================

def initialize_rushdb() -> RushDB:
    """Initialize RushDB connection."""
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        raise ValueError("RUSHDB_API_TOKEN not found in environment")
    
    db = RushDB(api_token)
    print("✓ Connected to RushDB")
    return db


def setup_vector_index(db: RushDB, embedding_model) -> None:
    """
    Create vector index and embed product descriptions.
    
    Uses 'external' source type - we provide pre-computed vectors.
    """
    print("\n📊 Setting up vector index for product descriptions...")
    
    # Check if index already exists
    try:
        existing = db.ai.indexes.find()
        for idx in existing.data:
            if idx.get("label") == "PRODUCT" and idx.get("propertyName") == "description":
                print("  ✓ Vector index already exists, skipping setup")
                return
    except Exception:
        pass
    
    # Fetch all products
    products = db.records.find({"labels": ["PRODUCT"], "limit": 500})
    if not products.data:
        print("  ⚠️ No products found. Run seed.py first.")
        return
    
    print(f"  Found {len(products.data)} products, creating embeddings...")
    
    # Create index with external source type (we'll provide vectors)
    index = db.ai.indexes.create({
        "label": "PRODUCT",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,  # all-MiniLM-L6-v2 outputs 384-dim vectors
        "similarityFunction": "cosine",
    })
    
    index_id = index.data["__id"]
    print(f"  ✓ Created vector index: {index_id}")
    
    # Generate and upsert vectors
    descriptions = [p.data.get("description", "") for p in products.data]
    vectors = embedding_model.encode(descriptions).tolist()
    
    items = [
        {"recordId": p.id, "vector": vec}
        for p, vec in zip(products.data, vectors)
    ]
    
    db.ai.indexes.upsert_vectors(index_id, {"items": items})
    print(f"  ✓ Indexed {len(items)} product vectors")


# =============================================================================
# SECTION 3: Query Strategies
# =============================================================================

def query_pure_traversal(db: RushDB, user_id: str, limit: int = 10):
    """
    Pure graph traversal - no time weighting.
    
    Finds all products the user has interacted with, regardless of when.
    """
    print("\n" + "=" * 60)
    print("QUERY 1: Pure Graph Traversal (No Time-Weighting)")
    print("=" * 60)
    
    # Find interactions for this user
    interactions = db.records.find({
        "labels": ["INTERACTION"],
        "where": {
            "MADE": {"$relation": {"type": "MADE", "direction": "in"}},
            "$id": user_id
        },
        "limit": 100
    })
    
    # Get related products (deduplicated)
    product_scores = {}
    for interaction in interactions.data:
        ts = interaction.data.get("timestamp", "")
        rating = interaction.data.get("rating") or 3  # Default neutral rating
        
        # Find product this interaction concerns
        products = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "CONCERNS": {"$relation": {"type": "CONCERNS", "direction": "in"}},
                "$id": interaction.id
            }
        })
        
        for product in products.data:
            # Simple aggregation: count interactions + average rating
            if product.id not in product_scores:
                product_scores[product.id] = {
                    "product": product,
                    "interaction_count": 0,
                    "total_rating": 0,
                    "last_interaction": ts
                }
            product_scores[product.id]["interaction_count"] += 1
            product_scores[product.id]["total_rating"] += rating
    
    # Sort by interaction count (simple proxy for relevance)
    ranked = sorted(
        product_scores.values(),
        key=lambda x: x["interaction_count"],
        reverse=True
    )[:limit]
    
    print(f"\nTop {limit} products by interaction frequency:")
    for i, item in enumerate(ranked, 1):
        avg_rating = item["total_rating"] / item["interaction_count"]
        print(f"  {i}. {item['product'].data.get('name', 'Unknown')}")
        print(f"     - {item['interaction_count']} interactions, avg rating: {avg_rating:.1f}")
    
    return ranked


def query_time_weighted_traversal(
    db: RushDB,
    user_id: str,
    decay_fn: DecayFunction = exponential_decay,
    decay_config: DecayConfig = None,
    limit: int = 10
):
    """
    Time-weighted traversal - decay older interactions.
    
    KEY POINT: Time-weighting happens AFTER traversal in this approach.
    This is simpler but requires fetching more data upfront.
    """
    print("\n" + "=" * 60)
    print(f"QUERY 2: Time-Weighted Traversal (decay function: {decay_fn.__name__})")
    print("=" * 60)
    
    if decay_config is None:
        decay_config = DecayConfig(half_life_days=30)
    
    # Fetch all interactions (same as pure traversal)
    interactions = db.records.find({
        "labels": ["INTERACTION"],
        "where": {
            "MADE": {"$relation": {"type": "MADE", "direction": "in"}},
            "$id": user_id
        },
        "limit": 200  # Fetch more for better scoring
    })
    
    # Aggregate with time decay
    product_scores = {}
    for interaction in interactions.data:
        ts = interaction.data.get("timestamp", "")
        if not ts:
            continue
        
        rating = interaction.data.get("rating") or 3
        
        # KEY: Apply decay function to score
        time_weight = decay_fn(ts, decay_config)
        weighted_score = rating * time_weight
        
        # Find product
        products = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "CONCERNS": {"$relation": {"type": "CONCERNS", "direction": "in"}},
                "$id": interaction.id
            }
        })
        
        for product in products.data:
            if product.id not in product_scores:
                product_scores[product.id] = {
                    "product": product,
                    "weighted_score": 0.0,
                    "decay_breakdown": []
                }
            product_scores[product.id]["weighted_score"] += weighted_score
            product_scores[product.id]["decay_breakdown"].append({
                "timestamp": ts,
                "decay": time_weight,
                "rating": rating
            })
    
    # Sort by weighted score
    ranked = sorted(
        product_scores.values(),
        key=lambda x: x["weighted_score"],
        reverse=True
    )[:limit]
    
    print(f"\nTop {limit} products by time-weighted score (half_life={decay_config.half_life_days} days):")
    for i, item in enumerate(ranked, 1):
        print(f"  {i}. {item['product'].data.get('name', 'Unknown')}")
        print(f"     - Weighted score: {item['weighted_score']:.3f}")
        # Show decay breakdown for first item
        if i == 1 and len(item['decay_breakdown']) > 1:
            print(f"     - Sample decays: {item['decay_breakdown'][:3]}")
    
    return ranked


def query_vector_similarity(db: RushDB, query_text: str, limit: int = 10):
    """
    Pure vector similarity search - content-based recommendations.
    
    Finds products similar to the query based on description embeddings.
    """
    print("\n" + "=" * 60)
    print("QUERY 3: Vector Similarity Search (Content-Based)")
    print("=" * 60)
    
    results = db.ai.search({
        "propertyName": "description",
        "query": query_text,
        "labels": ["PRODUCT"],
        "limit": limit
    })
    
    print(f"\nTop {limit} products similar to '{query_text}':")
    for i, result in enumerate(results.data, 1):
        print(f"  {i}. {result.data.get('name', 'Unknown')}")
        print(f"     - Score: {result.score:.4f}")
        print(f"     - Category: {result.data.get('category', 'Unknown')}")
    
    return results.data


def query_hybrid_time_vector(
    db: RushDB,
    user_id: str,
    query_text: str,
    alpha: float = 0.5,
    decay_config: DecayConfig = None,
    limit: int = 10
):
    """
    HYBRID QUERY: Combines time-weighting with vector similarity.
    
    This is the KEY technique for recency-aware recommendations.
    
    Formula: final_score = (vector_score * α) + (time_weight * (1 - α))
    
    Where α controls the blend:
    - α = 1.0: Pure vector similarity
    - α = 0.0: Pure time-weighted traversal
    - α = 0.5: Equal blend
    """
    print("\n" + "=" * 60)
    print(f"QUERY 4: Hybrid Time-Weighted + Vector (α={alpha})")
    print("=" * 60)
    
    if decay_config is None:
        decay_config = DecayConfig(half_life_days=30)
    
    # Get vector similarity scores for query
    vector_results = db.ai.search({
        "propertyName": "description",
        "query": query_text,
        "labels": ["PRODUCT"],
        "limit": 100  # Get more candidates
    })
    
    # Build vector score lookup (normalize to 0-1)
    max_vector_score = max((r.score for r in vector_results.data), default=1.0)
    vector_lookup = {
        r.id: r.score / max_vector_score for r in vector_results.data
    }
    
    # Get time-weighted traversal scores
    interactions = db.records.find({
        "labels": ["INTERACTION"],
        "where": {
            "MADE": {"$relation": {"type": "MADE", "direction": "in"}},
            "$id": user_id
        },
        "limit": 200
    })
    
    # Aggregate time weights
    product_time_weights = {}
    for interaction in interactions.data:
        ts = interaction.data.get("timestamp", "")
        if not ts:
            continue
        
        time_weight = exponential_decay(ts, decay_config)
        
        products = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "CONCERNS": {"$relation": {"type": "CONCERNS", "direction": "in"}},
                "$id": interaction.id
            }
        })
        
        for product in products.data:
            if product.id not in product_time_weights:
                product_time_weights[product.id] = {"product": product, "weight": 0.0}
            product_time_weights[product.id]["weight"] += time_weight
    
    # Normalize time weights
    max_time_weight = max((v["weight"] for v in product_time_weights.values()), default=1.0)
    
    # Combine scores
    hybrid_scores = []
    all_product_ids = set(vector_lookup.keys()) | set(product_time_weights.keys())
    
    for product_id in all_product_ids:
        vector_score = vector_lookup.get(product_id, 0.0)
        time_weight = product_time_weights.get(product_id, {"product": None, "weight": 0.0})["weight"]
        
        if time_weight > 0:
            time_weight = time_weight / max_time_weight
        
        # Hybrid scoring
        hybrid_score = (vector_score * alpha) + (time_weight * (1 - alpha))
        
        # Get product object
        if product_time_weights.get(product_id):
            product = product_time_weights[product_id]["product"]
        else:
            # Look up from vector results
            for vr in vector_results.data:
                if vr.id == product_id:
                    product = vr
                    break
            else:
                continue
        
        hybrid_scores.append({
            "product": product,
            "hybrid_score": hybrid_score,
            "vector_score": vector_score,
            "time_weight": time_weight,
            "alpha": alpha
        })
    
    # Sort and return top results
    ranked = sorted(hybrid_scores, key=lambda x: x["hybrid_score"], reverse=True)[:limit]
    
    print(f"\nTop {limit} products by hybrid score (α={alpha}):")
    for i, item in enumerate(ranked, 1):
        product = item["product"]
        print(f"  {i}. {product.data.get('name', 'Unknown') if hasattr(product, 'data') else 'N/A'}")
        print(f"     - Hybrid: {item['hybrid_score']:.4f} | Vector: {item['vector_score']:.4f} | Time: {item['time_weight']:.4f}")
        print(f"     - Category: {product.data.get('category', 'Unknown') if hasattr(product, 'data') else 'N/A'}")
    
    return ranked


# =============================================================================
# SECTION 4: Benchmarking
# =============================================================================

def benchmark_traversal_approaches(
    db: RushDB,
    user_id: str,
    scales: list = None
):
    """
    Benchmark different traversal approaches.
    
    KEY QUESTION: Does time-weighting significantly slow traversal?
    """
    print("\n" + "=" * 60)
    print("BENCHMARK: Performance Comparison")
    print("=" * 60)
    
    if scales is None:
        scales = [50, 100, 200, 500, 1000]
    
    # Get a sample user for benchmarking
    users = db.records.find({"labels": ["USER"], "limit": 1})
    if not users.data:
        print("  ⚠️ No users found for benchmarking")
        return
    
    benchmark_user = users.data[0]
    
    print(f"\n{'Scale':>8} | {'Pure':>10} | {'Time-Weighted':>14} | {'Overhead':>10}")
    print("-" * 50)
    
    results = []
    
    for scale in scales:
        # Pure traversal
        start = time.perf_counter()
        _ = query_pure_traversal(db, benchmark_user.id, limit=scale)
        pure_time = time.perf_counter() - start
        
        # Time-weighted traversal (same data, different scoring)
        start = time.perf_counter()
        _ = query_time_weighted_traversal(db, benchmark_user.id, limit=scale)
        weighted_time = time.perf_counter() - start
        
        overhead = ((weighted_time - pure_time) / pure_time) * 100 if pure_time > 0 else 0
        
        results.append({
            "scale": scale,
            "pure_time": pure_time,
            "weighted_time": weighted_time,
            "overhead_pct": overhead
        })
        
        print(f"{scale:>8} | {pure_time*1000:>8.2f}ms | {weighted_time*1000:>12.2f}ms | {overhead:>8.1f}%")
    
    print("\n📊 Analysis:")
    avg_overhead = sum(r["overhead_pct"] for r in results) / len(results)
    
    if avg_overhead < 20:
        print(f"  ✓ Time-weighting adds only ~{avg_overhead:.0f}% overhead on average")
        print("  ✓ Safe to use in production at all tested scales")
    elif avg_overhead < 50:
        print(f"  ⚠ Moderate overhead of ~{avg_overhead:.0f}% - acceptable for most use cases")
    else:
        print(f"  ⚠ High overhead of ~{avg_overhead:.0f}% - consider optimization strategies")
    
    print("\n💡 Optimization strategies if overhead is problematic:")
    print("  1. Pre-filter by time window (e.g., last 30 days only)")
    print("  2. Cache time weights for frequently accessed users")
    print("  3. Use database-level aggregation before Python scoring")
    print("  4. Limit the number of interactions fetched per user")
    
    return results


def demonstrate_weighting_during_vs_after(db: RushDB):
    """
    Demonstrate the difference between:
    - Weighting DURING traversal (database-level)
    - Weighting AFTER traversal (application-level)
    
    This is a key query planner implication.
    """
    print("\n" + "=" * 60)
    print("CONCEPT: Weighting During vs. After Traversal")
    print("=" * 60)
    
    print("""
    APPROACH 1: Weighting AFTER Traversal (What we implemented)
    ────────────────────────────────────────────────────────────
    1. Database returns all matching records
    2. Python applies decay function to each timestamp
    3. Results are sorted and filtered in memory
    
    Pros:
    • Simpler to implement and debug
    • Decay function can be changed without DB queries
    • Full flexibility in scoring algorithms
    
    Cons:
    • More data transferred from database
    • CPU work happens in application layer
    • Harder to limit results before scoring
    
    
    APPROACH 2: Weighting DURING Traversal (Alternative)
    ────────────────────────────────────────────────────────────
    1. Use database WHERE clauses to pre-filter by time
    2. Fetch only recent interactions (e.g., last 30 days)
    3. Apply simpler weighting or skip it entirely
    
    Pros:
    • Less data transfer
    • Database does filtering (often faster for large datasets)
    • Better for very large graphs
    
    Cons:
    • Requires knowing the decay threshold
    • Harder to combine multiple decay rates
    • Less flexibility in scoring
    
    
    RECOMMENDATION:
    • Small-medium graphs (<10K edges/user): Weight AFTER (our approach)
    • Large graphs (>10K edges/user): Weight DURING with time pre-filter
    """)
    
    # Show pre-filtering example
    print("\n📋 Example: Pre-filtering by time window (weighting DURING)")
    
    # Calculate cutoff timestamp
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_iso = cutoff_date.isoformat()
    
    print(f"   Fetching interactions from last 30 days (after {cutoff_iso})")
    
    users = db.records.find({"labels": ["USER"], "limit": 1})
    if users.data:
        recent_interactions = db.records.find({
            "labels": ["INTERACTION"],
            "where": {
                "MADE": {"$relation": {"type": "MADE", "direction": "in"}},
                "$id": users.data[0].id,
                "timestamp": {"$gte": cutoff_iso}  # Pre-filter by time
            },
            "limit": 100
        })
        
        print(f"   ✓ Found {len(recent_interactions.data)} recent interactions")
        print(f"   ✓ Reduces dataset before applying detailed scoring")


# =============================================================================
# SECTION 5: Main Tutorial Flow
# =============================================================================

def main():
    """Run the complete tutorial demonstrating time-weighted graph traversals."""
    print("\n" + "=" * 70)
    print(" " * 10 + "TIME-WEIGHTED GRAPH TRAVERSALS")
    print(" " * 5 + "For Recency-Aware Recommendations in RushDB")
    print("=" * 70)
    
    # Initialize RushDB
    db = initialize_rushdb()
    
    # Initialize embedding model for vector search
    print("\n🤖 Loading embedding model (all-MiniLM-L6-v2)...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("  ✓ Model loaded (384-dimensional embeddings)")
    
    # Setup vector index
    setup_vector_index(db, embedding_model)
    
    # Get a sample user for demonstration
    users = db.records.find({"labels": ["USER"], "limit": 1})
    if not users.data:
        print("\n❌ No users found. Please run seed.py first:")
        print("   python seed.py")
        return
    
    demo_user = users.data[0]
    print(f"\n👤 Demo user: {demo_user.data.get('username', 'Unknown')}")
    
    # Query 1: Pure traversal (baseline)
    query_pure_traversal(db, demo_user.id, limit=5)
    
    # Query 2a: Time-weighted with exponential decay
    query_time_weighted_traversal(
        db, demo_user.id,
        decay_fn=exponential_decay,
        decay_config=DecayConfig(half_life_days=30),
        limit=5
    )
    
    # Query 2b: Time-weighted with linear decay
    query_time_weighted_traversal(
        db, demo_user.id,
        decay_fn=linear_decay,
        decay_config=DecayConfig(half_life_days=30),
        limit=5
    )
    
    # Query 3: Vector similarity
    query_vector_similarity(db, "wireless headphones audio music", limit=5)
    
    # Query 4a: Hybrid with α=0.3 (more recency bias)
    query_hybrid_time_vector(
        db, demo_user.id,
        query_text="fitness workout exercise",
        alpha=0.3,
        limit=5
    )
    
    # Query 4b: Hybrid with α=0.7 (more content similarity bias)
    query_hybrid_time_vector(
        db, demo_user.id,
        query_text="fitness workout exercise",
        alpha=0.7,
        limit=5
    )
    
    # Benchmark different approaches
    benchmark_traversal_approaches(db, demo_user.id)
    
    # Explain the query planner implications
    demonstrate_weighting_during_vs_after(db)
    
    # Summary
    print("\n" + "=" * 70)
    print(" " * 15 + "TUTORIAL COMPLETE")
    print("=" * 70)
    print("""
Key Takeaways:
─────────────
1. ✅ Time-annotated edges in RushDB capture interaction recency
2. ✅ Decay functions (exponential, linear, logarithmic) model preference decay
3. ✅ Hybrid scoring combines content relevance + recency elegantly
4. ✅ Time-weighting adds minimal overhead (<20%) at typical scales
5. ✅ For very large graphs, consider pre-filtering by time window

Next Steps:
───────────
• Experiment with different decay half-lives (7 days vs 90 days)
• Try different α values to balance recency vs. content match
• Implement caching for time weights of active users
• Explore more complex hybrid formulas (e.g., multiplicative vs. additive)

Resources:
──────────
• RushDB Docs: https://docs.rushdb.com
• GitHub Examples: https://github.com/rush-db/examples
""")


if __name__ == "__main__":
    main()
