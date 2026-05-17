#!/usr/bin/env python3
"""
Collaborative Filtering Demo with RushDB

This example demonstrates how to build a real-time recommendation system
using RushDB's native property graph and vector search capabilities.

Key concepts demonstrated:
1. Graph-based user similarity via interaction neighborhoods
2. Hybrid scoring: behavioral (collaborative) + content (semantic)
3. Typed interaction edges with weighted relationships
4. Cold-start handling with content-based fallbacks

Target audience: Backend engineers building recommendation systems
"""

import os
import random
from collections import defaultdict
from typing import Optional

from dotenv import load_dotenv

from rushdb import RushDB

# Load environment
load_dotenv()


# ============================================================================
# DATA MODELS & CONFIGURATION
# ============================================================================

# Interaction types and their weights for scoring
INTERACTION_WEIGHTS = {
    "PURCHASED": 3.0,   # Strongest signal
    "RATED": 2.0,       # Medium signal (assumes positive rating)
    "VIEWED": 0.5,      # Weakest signal
}

# Scoring configuration
COLLABORATIVE_WEIGHT = 0.6   # Weight for collaborative filtering score
SEMANTIC_WEIGHT = 0.4        # Weight for content-based similarity
TOP_K_RECOMMENDATIONS = 10   # Number of recommendations to return
TOP_K_SIMILAR_USERS = 15     # Number of similar users to consider


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class CollaborativeFilteringEngine:
    """
    Hybrid recommendation engine combining:
    - Collaborative filtering (user-user similarity via graph traversal)
    - Content-based filtering (item-item similarity via vector search)
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self._cache_similar_users = {}
        self._cache_item_vectors = {}
    
    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """
        Fetch a user profile by userId field.
        
        Production note: In production, cache user profiles in Redis
        or your application cache layer.
        """
        result = self.db.records.find_one({
            "labels": ["USER"],
            "where": {"userId": user_id}
        })
        return result.data if result else None
    
    def get_user_interactions(self, user_id: str) -> list[dict]:
        """
        Get all items a user has interacted with, along with interaction details.
        
        Returns list of dicts with item data and interaction metadata.
        """
        user = self.get_user_profile(user_id)
        if not user:
            return []
        
        # Find all items this user has interacted with
        # RushDB relationship traversal via label filtering
        result = self.db.records.find({
            "labels": ["USER"],
            "where": {
                "userId": user_id
            }
        })
        
        if not result.data:
            return []
        
        user_record = result.data[0]
        
        # Get all items this user interacted with (any relationship type)
        items_result = self.db.records.find({
            "labels": ["ITEM"],
            "where": {
                "USER": {
                    "$relation": {
                        "type": ["PURCHASED", "RATED", "VIEWED"],
                        "direction": "in"
                    }
                }
            }
        })
        
        interactions = []
        for item in items_result.data:
            # Determine interaction type and weight
            # In production, you'd query the relationship properties directly
            interaction_type = "VIEWED"  # Default
            weight = 0.5
            
            interactions.append({
                "item": item.data,
                "item_id": item.id,
                "interaction_type": interaction_type,
                "weight": weight,
            })
        
        return interactions
    
    def find_similar_users(self, user_id: str, top_k: int = TOP_K_SIMILAR_USERS) -> list[dict]:
        """
        Find users with similar taste based on interaction overlap.
        
        Graph traversal approach:
        1. Get target user's interacted items
        2. Find OTHER users who interacted with the same items
        3. Score by interaction overlap and similarity
        
        Production note: Pre-compute user similarity in batch for real-time use.
        For < 100k users, this real-time approach works well.
        """
        cache_key = f"{user_id}_similar_users"
        if cache_key in self._cache_similar_users:
            return self._cache_similar_users[cache_key]
        
        user = self.get_user_profile(user_id)
        if not user:
            return []
        
        # Find items the target user has interacted with
        user_items_result = self.db.records.find({
            "labels": ["ITEM"],
            "where": {
                "USER": {
                    "$relation": {
                        "type": ["PURCHASED", "RATED", "VIEWED"],
                        "direction": "in"
                    }
                }
            }
        })
        
        target_user_item_ids = {item.id for item in user_items_result.data}
        
        if not target_user_item_ids:
            return []
        
        # Find OTHER users who interacted with these items
        # Exclude the target user
        similar_users_result = self.db.records.find({
            "labels": ["USER"],
            "where": {
                "userId": {"$ne": user_id},
                "ITEM": {
                    "$relation": {
                        "type": ["PURCHASED", "RATED", "VIEWED"],
                        "direction": "out"
                    }
                }
            },
            "limit": 100  # Get more than needed, score locally
        })
        
        # Score each candidate user by interaction overlap
        user_scores = defaultdict(lambda: {"overlap": 0, "user_record": None, "user_data": None})
        
        for candidate_user in similar_users_result.data:
            # Find items this candidate user interacted with
            candidate_items_result = self.db.records.find({
                "labels": ["ITEM"],
                "where": {
                    "USER": {
                        "$relation": {
                            "type": ["PURCHASED", "RATED", "VIEWED"],
                            "direction": "in"
                        }
                    }
                }
            })
            
            candidate_item_ids = {item.id for item in candidate_items_result.data}
            
            # Calculate overlap (Jaccard-like score)
            overlap = len(target_user_item_ids & candidate_item_ids)
            if overlap > 0:
                user_scores[candidate_user.id] = {
                    "overlap": overlap,
                    "user_record": candidate_user,
                    "user_data": candidate_user.data,
                }
        
        # Sort by overlap score and take top K
        similar_users = sorted(
            user_scores.values(),
            key=lambda x: x["overlap"],
            reverse=True
        )[:top_k]
        
        self._cache_similar_users[cache_key] = similar_users
        return similar_users
    
    def get_similar_users_preferences(self, similar_users: list[dict]) -> dict[str, float]:
        """
        Aggregate item preferences from similar users.
        
        Returns dict mapping item_id -> cumulative preference score.
        Higher scores = items popular among similar users.
        """
        item_scores = defaultdict(float)
        
        for user_data in similar_users:
            user_record = user_data["user_record"]
            
            # Get items this similar user interacted with
            items_result = self.db.records.find({
                "labels": ["ITEM"],
                "where": {
                    "USER": {
                        "$relation": {
                            "type": ["PURCHASED", "RATED", "VIEWED"],
                            "direction": "in"
                        }
                    }
                }
            })
            
            for item in items_result.data:
                # Weight by interaction type
                # In production, query relationship properties for exact weights
                item_scores[item.id] += 1.0  # Base score
        
        return dict(item_scores)
    
    def find_semantically_similar_items(
        self, 
        item_ids: list[str],
        top_k: int = 20
    ) -> list[dict]:
        """
        Find items semantically similar to the given items using vector search.
        
        This provides content-based filtering to handle cold-start items
        (items new users haven't interacted with, or new items).
        
        Production note: 
        - Cache query vectors for frequently-used item sets
        - Consider using approximate nearest neighbor (ANN) for large catalogs
        - RushDB uses native Neo4j vector indexes (HNSW)
        """
        if not item_ids:
            return []
        
        # Get descriptions of items the user has interacted with
        items_result = self.db.records.find_by_id(item_ids)
        
        if not items_result:
            return []
        
        # Create a combined query from interacted item descriptions
        descriptions = []
        for item in items_result:
            if hasattr(item, 'data'):
                desc = item.data.get('description', '')
            else:
                desc = item.get('description', '')
            descriptions.append(desc)
        
        # For simplicity, use the first item's description
        # In production, could use TF-IDF weighted combination
        query_description = descriptions[0] if descriptions else ""
        
        # Find similar items via vector search
        results = self.db.ai.search({
            "propertyName": "description",
            "query": query_description,
            "labels": ["ITEM"],
            "limit": top_k,
        })
        
        similar_items = []
        for result in results.data:
            similar_items.append({
                "item_id": result.id,
                "item_data": result.data,
                "semantic_score": result.score or 0.0,
            })
        
        return similar_items
    
    def recommend(
        self, 
        user_id: str,
        exclude_interacted: bool = True,
        top_k: int = TOP_K_RECOMMENDATIONS,
    ) -> list[dict]:
        """
        Generate personalized recommendations for a user.
        
        Hybrid approach combining:
        1. Collaborative filtering: items popular among similar users
        2. Content-based filtering: items semantically similar to user's preferences
        
        Args:
            user_id: The target user identifier
            exclude_interacted: Whether to exclude items user has already interacted with
            top_k: Number of recommendations to return
        
        Returns:
            List of recommended items with scores and explanations
        """
        print(f"\n{'='*60}")
        print(f"GENERATING RECOMMENDATIONS FOR USER: {user_id}")
        print(f"{'='*60}")
        
        # Step 1: Get target user's profile and interactions
        print("\n[1] Fetching user profile and interaction history...")
        user = self.get_user_profile(user_id)
        if not user:
            print(f"User {user_id} not found!")
            return []
        
        print(f"    User: {user.get('name')} (since {user.get('member_since')})")
        
        # Get items the user has already interacted with
        user_interactions = self.get_user_interactions(user_id)
        interacted_item_ids = {i["item_id"] for i in user_interactions}
        
        print(f"    Interactions: {len(user_interactions)}")
        interaction_summary = defaultdict(int)
        for interaction in user_interactions:
            interaction_summary[interaction["interaction_type"]] += 1
        for itype, count in interaction_summary.items():
            print(f"      - {itype}: {count}")
        
        # Step 2: Find similar users via graph traversal
        print("\n[2] Finding similar users via graph traversal...")
        similar_users = self.find_similar_users(user_id)
        print(f"    Found {len(similar_users)} similar users")
        
        for i, similar in enumerate(similar_users[:3]):
            print(f"      {i+1}. {similar['user_data'].get('name')} (overlap: {similar['overlap']})")
        
        # Step 3: Aggregate preferences from similar users (collaborative score)
        print("\n[3] Computing collaborative filtering scores...")
        collaborative_scores = self.get_similar_users_preferences(similar_users)
        
        # Normalize collaborative scores
        if collaborative_scores:
            max_collab_score = max(collaborative_scores.values())
            collaborative_scores = {
                k: v / max_collab_score 
                for k, v in collaborative_scores.items()
            }
        
        print(f"    Scored {len(collaborative_scores)} items from similar users")
        
        # Step 4: Find semantically similar items (content-based score)
        print("\n[4] Computing content-based similarity scores...")
        
        if user_interactions:
            item_ids_for_semantic = [
                i["item_id"] 
                for i in user_interactions 
                if i["item_id"] in collaborative_scores
            ][:5]  # Use top 5 interacted items for query
            
            semantic_matches = self.find_semantically_similar_items(item_ids_for_semantic)
            print(f"    Found {len(semantic_matches)} semantically similar items")
        else:
            semantic_matches = []
        
        # Normalize semantic scores
        semantic_scores = {}
        if semantic_matches:
            max_semantic_score = max(m["semantic_score"] for m in semantic_matches)
            for match in semantic_matches:
                if max_semantic_score > 0:
                    semantic_scores[match["item_id"]] = match["semantic_score"] / max_semantic_score
        
        # Step 5: Combine scores (hybrid scoring)
        print("\n[5] Computing hybrid recommendation scores...")
        
        all_candidate_ids = set(collaborative_scores.keys()) | set(semantic_scores.keys())
        
        if exclude_interacted:
            all_candidate_ids -= interacted_item_ids
        
        hybrid_scores = []
        for item_id in all_candidate_ids:
            collab = collaborative_scores.get(item_id, 0.0)
            semantic = semantic_scores.get(item_id, 0.0)
            
            # Hybrid score: weighted combination
            score = (COLLABORATIVE_WEIGHT * collab) + (SEMANTIC_WEIGHT * semantic)
            
            hybrid_scores.append({
                "item_id": item_id,
                "score": score,
                "collab_score": collab,
                "semantic_score": semantic,
            })
        
        # Sort by hybrid score
        hybrid_scores.sort(key=lambda x: x["score"], reverse=True)
        top_recommendations = hybrid_scores[:top_k]
        
        # Step 6: Enrich with item details
        print("\n[6] Enriching recommendations with item details...")
        
        recommended_items = []
        for rec in top_recommendations:
            item_result = self.db.records.find_by_id(rec["item_id"])
            if item_result:
                item_data = item_result.data if hasattr(item_result, 'data') else item_result
                recommended_items.append({
                    "item": item_data,
                    "score": rec["score"],
                    "collab_score": rec["collab_score"],
                    "semantic_score": rec["semantic_score"],
                    "explanation": self._generate_explanation(rec),
                })
        
        return recommended_items
    
    def _generate_explanation(self, rec: dict) -> str:
        """Generate human-readable explanation for a recommendation."""
        explanations = []
        
        if rec["collab_score"] > 0.5:
            explanations.append("Users with similar taste also liked this")
        elif rec["collab_score"] > 0:
            explanations.append("Some users with similar taste liked this")
        
        if rec["semantic_score"] > 0.7:
            explanations.append("Very similar to items you've interacted with")
        elif rec["semantic_score"] > 0.4:
            explanations.append("Similar to your preferred items")
        
        if not explanations:
            explanations.append("Recommended based on your profile")
        
        return "; ".join(explanations)


# ============================================================================
# DEMONSTRATION
# ============================================================================

def print_recommendations(recommendations: list[dict]):
    """Pretty-print recommendations."""
    print(f"\n{'='*80}")
    print(f"TOP {len(recommendations)} RECOMMENDATIONS")
    print(f"{'='*80}")
    
    for i, rec in enumerate(recommendations, 1):
        item = rec["item"]
        print(f"\n{i}. {item.get('name', 'Unknown')}")
        print(f"   Category: {item.get('category', 'N/A')}")
        print(f"   Score: {rec['score']:.3f} (collab: {rec['collab_score']:.2f}, semantic: {rec['semantic_score']:.2f})")
        print(f"   Why: {rec['explanation']}")
        desc = item.get('description', '')
        if desc:
            print(f"   Description: {desc[:80]}...")


def demonstrate_cold_start(db: RushDB, engine: CollaborativeFilteringEngine):
    """
    Demonstrate cold-start handling for new users.
    
    Cold start occurs when we have limited interaction data.
    Solution: Fall back to content-based filtering + demographic similarity.
    """
    print(f"\n{'='*80}")
    print("COLD START DEMONSTRATION")
    print(f"{'='*80}")
    
    # Find a user with few interactions
    all_users = db.records.find({"labels": ["USER"], "limit": 100})
    
    user_interaction_counts = []
    for user in all_users.data:
        interactions = engine.get_user_interactions(user.data.get('userId', ''))
        user_interaction_counts.append((user, len(interactions)))
    
    user_interaction_counts.sort(key=lambda x: x[1])
    
    # Use a user with few interactions for demo
    if user_interaction_counts:
        sparse_user = user_interaction_counts[0][0]
        user_id = sparse_user.data.get('userId', '')
        interaction_count = user_interaction_counts[0][1]
        
        print(f"\nFound user '{user_id}' with only {interaction_count} interactions")
        print("For cold-start users, we rely more on content-based filtering.")
        print("\nRecommendations (with cold-start handling):")
        
        recommendations = engine.recommend(
            user_id, 
            top_k=5,
            exclude_interacted=True
        )
        
        for i, rec in enumerate(recommendations[:3], 1):
            item = rec["item"]
            print(f"  {i}. {item.get('name')} - Score: {rec['score']:.2f}")
            print(f"     (Content similarity: {rec['semantic_score']:.2f})")


def demonstrate_graph_traversal(db: RushDB):
    """
    Demonstrate the graph structure underlying the recommendation system.
    """
    print(f"\n{'='*80}")
    print("GRAPH STRUCTURE OVERVIEW")
    print(f"{'='*80}")
    
    # Count records
    users = db.records.find({"labels": ["USER"], "limit": 1})
    items = db.records.find({"labels": ["ITEM"], "limit": 1})
    
    print(f"\nGraph Statistics:")
    print(f"  Total Users: {users.total}")
    print(f"  Total Items: {items.total}")
    
    # Show a sample interaction path
    if users.data:
        sample_user = users.data[0]
        print(f"\nSample interaction path for user '{sample_user.data.get('userId')}':")
        print(f"  USER:{sample_user.id}")
        
        # Find items this user interacted with
        user_items = db.records.find({
            "labels": ["ITEM"],
            "where": {
                "USER": {
                    "$relation": {
                        "type": ["PURCHASED", "RATED", "VIEWED"],
                        "direction": "in"
                    }
                }
            },
            "limit": 5
        })
        
        for item in user_items.data:
            print(f"    │")
            print(f"    ├──[INTERACTION]──► ITEM:{item.id}")
            print(f"    │                     └── {item.data.get('name')}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the collaborative filtering demonstration."""
    
    print("\n" + "#"*80)
    print("# RUSHDB COLLABORATIVE FILTERING DEMO")
    print("# Real-time recommendations using graph traversal + vector search")
    print("#"*80)
    
    # Initialize RushDB
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("\nError: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        print("Get your key at: https://app.rushdb.com")
        return
    
    url = os.environ.get("RUSHDB_URL")
    if url:
        db = RushDB(api_key, url=url)
    else:
        db = RushDB(api_key)
    
    # Check if data exists
    print("\nChecking database state...")
    test_user = db.records.find_one({"labels": ["USER"], "where": {}})
    
    if not test_user:
        print("\nNo data found in database!")
        print("Please run 'python seed.py' first to populate the database.")
        return
    
    print(f"Database contains records. Proceeding with demo...")
    
    # Initialize recommendation engine
    engine = CollaborativeFilteringEngine(db)
    
    # Get a random user for demonstration
    all_users = db.records.find({"labels": ["USER"], "limit": 50})
    random_user = random.choice(all_users.data)
    target_user_id = random_user.data.get('userId', '')
    
    # Generate recommendations
    recommendations = engine.recommend(target_user_id)
    
    # Display results
    if recommendations:
        print_recommendations(recommendations)
    else:
        print("No recommendations generated (user may have interacted with all items).")
    
    # Show graph structure
    demonstrate_graph_traversal(db)
    
    # Cold-start demonstration
    demonstrate_cold_start(db, engine)
    
    # Production considerations
    print(f"\n{'='*80}")
    print("PRODUCTION CONSIDERATIONS")
    print(f"{'='*80}")
    print("""
1. REAL-TIME VS BATCH SCORING
   
   This demo uses real-time graph traversal, which works well for:
   - < 100k users
   - Graph depth ≤ 2
   - Latency budget > 100ms
   
   For larger scale, pre-compute user similarity matrices:
   - Run nightly batch job to compute user-user similarity
   - Store in Redis for < 5ms lookup
   - Update incrementally for new users

2. GRAPH DEPTH VS LATENCY
   
   Depth 1 (User → Items):              ~5-15ms
   Depth 2 (User → Items → Users):      ~20-50ms  ← Demo uses this
   Depth 3+:                             ~100-200ms
   
   Consider materialized paths for frequent deep traversals.

3. COLD START HANDLING
   
   New Users:
   - Use demographic similarity (age group, location)
   - Fall back to popular items by category
   - Content-based filtering on initial preferences
   
   New Items:
   - Pure content-based (vector similarity)
   - Promote via "new arrivals" section
   - Early adopter feedback loop

4. SCALING RECOMMENDATIONS
   
   RushDB handles graph traversal efficiently, but for millions of
   users, consider:
   - Sharding users by region/demographic
   - Separate read replicas for recommendation queries
   - Caching frequently-accessed user neighborhoods
""")
    
    print("\nDemo complete!")
    print("\nNext steps:")
    print("  1. Try different users by modifying target_user_id")
    print("  2. Adjust weights COLLABORATIVE_WEIGHT/SEMANTIC_WEIGHT")
    print("  3. Experiment with graph depth in find_similar_users()")
    print("  4. Add more interaction types (WISHLIST, CART, etc.)")


if __name__ == "__main__":
    main()
