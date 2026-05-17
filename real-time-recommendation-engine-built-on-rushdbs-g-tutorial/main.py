#!/usr/bin/env python3
"""
Real-time Recommendation Engine built on RushDB's Graph-Vector Store.

This example demonstrates a hybrid recommendation system combining:
1. Content-based filtering (vector similarity on product descriptions)
2. Collaborative filtering (graph traversal through user interactions)
3. Hybrid scoring (weighted combination of both signals)

Run `seed.py` first to populate sample data.
"""

import os
import time
from collections import defaultdict
from typing import Optional

from dotenv import load_dotenv

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY not found. See .env.example")

db = RushDB(api_key, url=os.getenv("RUSHDB_URL"))


# =============================================================================
# CONTENT-BASED FILTERING: Vector Similarity Search
# =============================================================================

def get_content_recommendations(product_id: str, limit: int = 5) -> list:
    """
    Find products similar to the given product using vector search.
    
    Uses RushDB's semantic search on product descriptions to find
    items with similar content characteristics.
    
    Args:
        product_id: ID of the reference product
        limit: Maximum number of recommendations
        
    Returns:
        List of (product, score) tuples sorted by similarity
    """
    # Get the reference product's description
    product = db.records.find_by_id(product_id)
    if not product:
        print(f"  ⚠ Product {product_id} not found")
        return []
    
    description = product.data.get("description", "")
    
    # Search for similar products using vector similarity
    results = db.ai.search({
        "propertyName": "description",
        "query": description,
        "labels": ["PRODUCT"],
        "limit": limit + 10  # Fetch extra to filter out self
    })
    
    # Filter out the reference product and convert to list
    recommendations = [
        (r, r.score)
        for r in results.data
        if r.id != product_id and r.score is not None
    ][:limit]
    
    return recommendations


def search_products_by_text(query: str, limit: int = 5) -> list:
    """
    Semantic search for products matching a text query.
    
    Args:
        query: Natural language search query
        limit: Maximum results to return
        
    Returns:
        List of matching products with similarity scores
    """
    results = db.ai.search({
        "propertyName": "description",
        "query": query,
        "labels": ["PRODUCT"],
        "limit": limit
    })
    
    return [(r, r.score) for r in results.data if r.score is not None]


# =============================================================================
# COLLABORATIVE FILTERING: Graph Traversal
# =============================================================================

def get_user_purchase_history(user_id: str) -> list:
    """
    Get all products a user has purchased.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of product records the user has purchased
    """
    # Find INTERACTION records attached to this user with type=purchase
    interactions = db.records.find({
        "labels": ["INTERACTION"],
        "where": {
            "type": "purchase",
            "USER": {
                "$relation": {"type": "INTERACTED_WITH", "direction": "in"},
                "id": user_id
            }
        },
        "limit": 50
    })
    
    # Find products attached to these interactions
    products = db.records.find({
        "labels": ["PRODUCT"],
        "where": {
            "INTERACTION": {
                "$relation": {"type": "INTERACTED_WITH", "direction": "in"},
                "id": {"$in": [i.id for i in interactions.data]}
            }
        },
        "limit": 50
    })
    
    return products.data


def get_similar_users(user_id: str, limit: int = 10) -> list:
    """
    Find users who have purchased similar products.
    
    Args:
        user_id: ID of the reference user
        limit: Maximum number of similar users to return
        
    Returns:
        List of similar user records
    """
    # Find products this user has purchased
    user_products = get_user_purchase_history(user_id)
    if not user_products:
        return []
    
    # Find other users who purchased ANY of these same products
    similar_users = db.records.find({
        "labels": ["USER"],
        "where": {
            "INTERACTION": {
                "$relation": {"type": "INTERACTED_WITH", "direction": "in"},
                "type": "purchase",
                "PRODUCT": {
                    "$id": {"$in": [p.id for p in user_products]}
                }
            },
            "id": {"$ne": user_id}  # Exclude the user themselves
        },
        "limit": limit
    })
    
    return similar_users.data


def get_collaborative_recommendations(user_id: str, limit: int = 5) -> list:
    """
    Recommend products based on what similar users purchased.
    
    Algorithm:
    1. Find similar users (users who bought overlapping products)
    2. Get products those similar users bought that the target user hasn't
    3. Score by number of similar users who bought each product
    
    Args:
        user_id: ID of the target user
        limit: Maximum number of recommendations
        
    Returns:
        List of (product, score) tuples where score is purchase frequency
    """
    # Get user's purchase history
    user_products = get_user_purchase_history(user_id)
    user_product_ids = {p.id for p in user_products}
    
    if not user_products:
        return []
    
    # Find products purchased by similar users
    similar_users = get_similar_users(user_id, limit=20)
    
    if not similar_users:
        return []
    
    # Get products purchased by similar users (excluding user's existing purchases)
    recommendations = db.records.find({
        "labels": ["PRODUCT"],
        "where": {
            "INTERACTION": {
                "$relation": {"type": "INTERACTED_WITH", "direction": "in"},
                "type": "purchase",
                "USER": {
                    "$id": {"$in": [u.id for u in similar_users]}
                }
            },
            "id": {"$nin": list(user_product_ids)}  # Exclude already purchased
        },
        "limit": limit * 3  # Fetch extra
    })
    
    # Count purchase frequency by similar users
    product_scores = defaultdict(int)
    for product in recommendations.data:
        product_scores[product.id] += 1
    
    # Convert to sorted list with normalized scores
    max_score = max(product_scores.values()) if product_scores else 1
    scored_products = [
        (rec, product_scores[rec.id] / max_score)
        for rec in recommendations.data
    ]
    
    # Sort by score and deduplicate
    seen = set()
    unique_results = []
    for product, score in scored_products:
        if product.id not in seen:
            seen.add(product.id)
            unique_results.append((product, score))
    
    return unique_results[:limit]


# =============================================================================
# HYBRID RECOMMENDATIONS: Combining Signals
# =============================================================================

def get_hybrid_recommendations(
    user_id: str,
    product_id: Optional[str] = None,
    alpha: float = 0.6,
    limit: int = 5
) -> list:
    """
    Combine content-based and collaborative filtering for personalized recommendations.
    
    Args:
        user_id: Target user ID
        product_id: Optional reference product (for content signal)
        alpha: Weight for collaborative score (1-alpha for content)
        limit: Maximum recommendations
        
    Returns:
        List of (product, collab_score, content_score, hybrid_score) tuples
    """
    # Get collaborative signal
    collab_results = get_collaborative_recommendations(user_id, limit=limit * 2)
    collab_scores = {p.id: score for p, score in collab_results}
    
    # Get content signal (either from product or user's purchased products)
    if product_id:
        content_results = get_content_recommendations(product_id, limit=limit * 2)
    else:
        # Use the user's most recent purchase as content reference
        user_products = get_user_purchase_history(user_id)
        if user_products:
            # Use first product from history
            content_results = get_content_recommendations(user_products[0].id, limit=limit * 2)
        else:
            content_results = []
    
    content_scores = {p.id: score for p, score in content_results}
    
    # Collect all candidate products
    all_product_ids = set(collab_scores.keys()) | set(content_scores.keys())
    
    # Normalize scores to 0-1 range
    max_collab = max(collab_scores.values()) if collab_scores else 1
    max_content = max(content_scores.values()) if content_scores else 1
    
    # Calculate hybrid scores
    candidates = []
    for pid in all_product_ids:
        collab = (collab_scores.get(pid, 0) / max_collab) if max_collab else 0
        content = (content_scores.get(pid, 0) / max_content) if max_content else 0
        hybrid = alpha * collab + (1 - alpha) * content
        
        # Fetch full product record
        product_records = db.records.find_by_id(pid)
        if product_records:
            product = product_records[0] if isinstance(product_records, list) else product_records
            candidates.append((product, collab, content, hybrid))
    
    # Sort by hybrid score
    candidates.sort(key=lambda x: x[3], reverse=True)
    
    return candidates[:limit]


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def format_product(p, score=None):
    """Format product for display."""
    name = p.data.get("name", "Unknown")
    price = p.data.get("price", 0)
    category = p.data.get("category", "Unknown")
    
    if score is not None:
        return f"  [{score:.3f}] {name} - ${price:.2f} ({category})"
    return f"  • {name} - ${price:.2f} ({category})"


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'─' * 60}")
    print(f" {title}")
    print(f"{'─' * 60}")


# =============================================================================
# MAIN DEMONSTRATION
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print(" REAL-TIME RECOMMENDATION ENGINE")
    print(" Built on RushDB's Graph-Vector Store")
    print("=" * 60)
    
    # Get sample data
    all_products = db.records.find({"labels": ["PRODUCT"], "limit": 100})
    all_users = db.records.find({"labels": ["USER"], "limit": 100})
    
    if all_products.total == 0:
        print("\n⚠ No products found. Run `python seed.py` first!")
        return
    
    products = all_products.data
    users = all_users.data
    
    print(f"\n📊 Dataset: {len(products)} products, {len(users)} users")
    
    # =========================================================================
    # Demo 1: Content-Based Recommendations
    # =========================================================================
    print_section("1️⃣  Content-Based: Similar Products")
    
    # Pick a product as reference
    reference_product = products[0]  # First product
    print(f"\nFinding products similar to:")
    print(f"  → {reference_product.data['name']}")
    print(f"  Category: {reference_product.data['category']}")
    
    content_recs = get_content_recommendations(reference_product.id, limit=5)
    
    print(f"\n📦 Top 5 similar products (by vector similarity):")
    for product, score in content_recs:
        print(format_product(product, score))
    
    # =========================================================================
    # Demo 2: Collaborative Filtering
    # =========================================================================
    print_section("2️⃣  Collaborative: What Similar Users Bought")
    
    # Find a user with purchase history
    user_with_history = None
    for user in users:
        purchases = get_user_purchase_history(user.id)
        if len(purchases) >= 2:
            user_with_history = user
            break
    
    if user_with_history:
        print(f"\nAnalyzing purchase history for: {user_with_history.data['name']}")
        print(f"  Username: @{user_with_history.data['username']}")
        
        user_purchases = get_user_purchase_history(user_with_history.id)
        print(f"\n  📦 Purchased items ({len(user_purchases)}):")
        for p in user_purchases[:3]:
            print(f"      • {p.data['name']}")
        if len(user_purchases) > 3:
            print(f"      ... and {len(user_purchases) - 3} more")
        
        # Get collaborative recommendations
        collab_recs = get_collaborative_recommendations(user_with_history.id, limit=5)
        
        print(f"\n  🔗 Products bought by similar users:")
        if collab_recs:
            for product, score in collab_recs:
                print(f"      • {product.data['name']} (bought by {int(score * 10)} similar users)")
        else:
            print("      No collaborative recommendations available")
        
        # Show similar users
        similar = get_similar_users(user_with_history.id, limit=3)
        print(f"\n  👥 Users with similar taste:")
        for u in similar:
            print(f"      • @{u.data['username']} ({u.data['preference']})")
    else:
        print("\n  ⚠ No user with sufficient purchase history found")
    
    # =========================================================================
    # Demo 3: Hybrid Recommendations
    # =========================================================================
    print_section("3️⃣  Hybrid: Personalized Recommendations")
    
    if user_with_history:
        print(f"\nGenerating hybrid recommendations for: {user_with_history.data['name']}")
        print("  (Combining content similarity + collaborative filtering)")
        
        hybrid_recs = get_hybrid_recommendations(
            user_id=user_with_history.id,
            alpha=0.6,  # 60% collaborative, 40% content
            limit=5
        )
        
        print(f"\n  🎯 Top hybrid recommendations:")
        for product, collab, content, hybrid in hybrid_recs:
            print(f"\n  {product.data['name']} - ${product.data['price']:.2f}")
            print(f"     Collab: {collab:.2f} | Content: {content:.2f} | Hybrid: {hybrid:.2f}")
    else:
        print("\n  ⚠ Skipped (no user with history)")
    
    # =========================================================================
    # Demo 4: Real-Time Semantic Search
    # =========================================================================
    print_section("4️⃣  Real-Time: Semantic Search")
    
    search_queries = [
        "ergonomic workspace setup",
        "gaming peripherals",
        "audio recording equipment",
        "fitness tracking device"
    ]
    
    for query in search_queries:
        print(f"\n  🔍 Query: \"{query}\"")
        results = search_products_by_text(query, limit=3)
        for product, score in results:
            print(f"      [{score:.3f}] {product.data['name']}")
    
    # =========================================================================
    # Demo 5: Category-Based Recommendations
    # =========================================================================
    print_section("5️⃣  Category Explorer")
    
    categories = set(p.data.get("category") for p in products)
    print(f"\nAvailable categories: {', '.join(sorted(categories))}")
    
    # Show top-rated products per category
    for category in sorted(categories)[:3]:
        category_products = db.records.find({
            "labels": ["PRODUCT"],
            "where": {"category": category},
            "limit": 3
        })
        print(f"\n  📁 {category}:")
        for p in category_products.data:
            print(f"      • {p.data['name']} - ${p.data['price']:.2f}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print_section("📋 Summary: Recommendation Patterns")
    
    print("""
    This example demonstrated three recommendation strategies:
    
    1️⃣  CONTENT-BASED (Vector Similarity)
        Uses semantic embeddings to find products with similar
        descriptions. Works even for new products with no history.
        
        RushDB API: db.ai.search({ propertyName: 'description', query: '...' })
    
    2️⃣  COLLABORATIVE (Graph Traversal)
        Finds products purchased by similar users through graph
        relationships. Leverages collective user behavior.
        
        RushDB API: db.records.find({ where: { USER: { $relation: ... } } })
    
    3️⃣  HYBRID (Combined Scoring)
        Blends both signals with configurable weights for
        more robust recommendations.
        
        Implementation: Normalize scores → Weighted sum → Rerank
    
    Key RushDB Features Used:
    ✓ Vector index on product.description (semantic search)
    ✓ Graph relationships (USER → INTERACTION → PRODUCT)
    ✓ Property graph traversal with $relation filters
    ✓ ACID transactions for consistent data
    """)
    
    print("=" * 60)
    print(" Recommendation Engine Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
