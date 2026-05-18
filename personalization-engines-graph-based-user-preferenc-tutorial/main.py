"""
Personalization Engine: Graph-Based User Preference Modeling

This script demonstrates how to build a personalization engine using RushDB's
property graph capabilities. It showcases:

1. User preference modeling as a graph
2. Collaborative filtering through relationship traversal
3. Content-based recommendations using item similarities
4. Hybrid recommendation patterns

Run `python seed.py` first to populate the database with sample data.
"""

import os
from collections import Counter, defaultdict
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
URL = os.getenv("RUSHDB_URL")

if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found. Copy .env.example to .env and add your key.")

db = RushDB(API_KEY, url=URL) if URL else RushDB(API_KEY)


def demo_user_preference_profile():
    """
    DEMO 1: User Preference Profile
    
    Show how to model a user's preferences as a graph with multiple
    interaction types (views, purchases, ratings).
    """
    print("\n" + "=" * 70)
    print("DEMO 1: User Preference Profile")
    print("=" * 70)
    
    # Find a premium user
    user_result = db.records.find_one({
        "labels": ["USER"],
        "where": {"tier": "premium"}
    })
    
    if not user_result:
        print("No premium user found. Run seed.py first.")
        return
    
    user = user_result
    print(f"\nUser: {user['name']}")
    print(f"Email: {user['email']}")
    print(f"Tier: {user['tier']}")
    print(f"Age Group: {user['age_group']}")
    
    # Find all interactions for this user
    interactions = db.records.find({
        "labels": ["ITEM"],
        "where": {
            "$relation": {"type": {"$in": ["VIEWED", "PURCHASED", "RATED"]}, "direction": "out"},
            "USER": {"$id": user.id}
        }
    })
    
    print(f"\nTotal interactions: {interactions.total}")
    
    # Categorize interactions
    categories = Counter()
    for item in interactions.data:
        categories[item["category"]] += 1
    
    print("\nPreference breakdown by category:")
    for category, count in categories.most_common():
        print(f"  {category}: {count} items")
    
    # Show top items
    print("\nTop interacted items:")
    for item in interactions.data[:5]:
        print(f"  - {item['name']} ({item['category']}, ${item['price']})")


def demo_collaborative_filtering():
    """
    DEMO 2: Collaborative Filtering
    
    Find users with similar preferences and recommend items
    they interacted with that our target user hasn't seen.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Collaborative Filtering")
    print("=" * 70)
    
    # Get a target user (Alice)
    target_user = db.records.find_one({
        "labels": ["USER"],
        "where": {"name": "Alice Chen"}
    })
    
    if not target_user:
        print("Alice not found. Run seed.py first.")
        return
    
    print(f"\nFinding recommendations for: {target_user['name']}")
    
    # Get items Alice has already interacted with
    alice_items = db.records.find({
        "labels": ["ITEM"],
        "where": {
            "$relation": {"type": {"$in": ["VIEWED", "PURCHASED"]}, "direction": "out"},
            "USER": {"$id": target_user.id}
        },
        "select": ["id"]
    })
    
    alice_item_ids = {item.id for item in alice_items.data}
    print(f"Alice has interacted with {len(alice_item_ids)} items")
    
    # Find items that other users in the same age group interacted with
    # (users with similar demographics tend to have similar preferences)
    similar_users = db.records.find({
        "labels": ["USER"],
        "where": {
            "age_group": target_user["age_group"],
            "tier": target_user["tier"]
        }
    })
    
    print(f"Found {similar_users.total} users with similar profile")
    
    # Collect items from similar users
    candidate_items = Counter()
    for similar_user in similar_users.data:
        if similar_user.id == target_user.id:
            continue
        
        user_items = db.records.find({
            "labels": ["ITEM"],
            "where": {
                "$relation": {"type": {"$in": ["VIEWED", "PURCHASED"]}, "direction": "out"},
                "USER": {"$id": similar_user.id}
            },
            "select": ["id", "name", "category"]
        })
        
        for item in user_items.data:
            if item.id not in alice_item_ids:
                candidate_items[(item.id, item["name"], item["category"])] += 1
    
    print("\nCollaborative filtering recommendations:")
    print("(Items popular among similar users that Alice hasn't seen)")
    print("-" * 50)
    
    for (item_id, item_name, category), score in candidate_items.most_common(8):
        print(f"  [{score:2d} similar users] {item_name} ({category})")


def demo_content_based_filtering():
    """
    DEMO 3: Content-Based Filtering
    
    Use item SIMILAR_TO relationships to recommend items similar
    to what the user has already interacted with.
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Content-Based Filtering")
    print("=" * 70)
    
    # Find Bob who has some interactions
    target_user = db.records.find_one({
        "labels": ["USER"],
        "where": {"name": "Bob Martinez"}
    })
    
    if not target_user:
        print("Bob not found. Run seed.py first.")
        return
    
    print(f"\nFinding similar items for: {target_user['name']}")
    
    # Get Bob's interacted items
    bob_items = db.records.find({
        "labels": ["ITEM"],
        "where": {
            "$relation": {"type": {"$in": ["VIEWED", "PURCHASED"]}, "direction": "out"},
            "USER": {"$id": target_user.id}
        }
    })
    
    print(f"Bob has interacted with {bob_items.total} items")
    
    # Find similar items for each interacted item
    similar_items = []
    seen_ids = {item.id for item in bob_items.data}
    
    for item in bob_items.data[:3]:  # Limit to first 3 for demo
        print(f"\n  Item: {item['name']}")
        
        # Find similar items using relationship query
        similar = db.records.find({
            "labels": ["ITEM"],
            "where": {
                "$relation": {"type": "SIMILAR_TO", "direction": "in"},
                "ITEM": {"$id": item.id}
            }
        })
        
        for sim_item in similar.data:
            if sim_item.id not in seen_ids:
                similar_items.append(sim_item)
                seen_ids.add(sim_item.id)
                print(f"    -> Similar: {sim_item['name']} ({sim_item['category']})")
    
    print(f"\nTotal content-based recommendations: {len(similar_items)}")


def demo_hybrid_recommendations():
    """
    DEMO 4: Hybrid Recommendation System
    
    Combine collaborative filtering and content-based filtering
    with a scoring algorithm to rank recommendations.
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Hybrid Recommendation System")
    print("=" * 70)
    
    target_user = db.records.find_one({
        "labels": ["USER"],
        "where": {"name": "Emma Wilson"}
    })
    
    if not target_user:
        print("Emma not found. Run seed.py first.")
        return
    
    print(f"\nGenerating hybrid recommendations for: {target_user['name']}")
    
    # Get Emma's preferences
    emma_items = db.records.find({
        "labels": ["ITEM"],
        "where": {
            "$relation": {"type": {"$in": ["VIEWED", "PURCHASED"]}, "direction": "out"},
            "USER": {"$id": target_user.id}
        }
    })
    
    emma_item_ids = {item.id for item in emma_items.data}
    emma_categories = Counter(item["category"] for item in emma_items.data)
    
    print(f"Emma's preference profile:")
    for cat, count in emma_categories.most_common(3):
        print(f"  - {cat}: {count} interactions")
    
    # Collect candidates from multiple sources
    candidates = defaultdict(lambda: {"collab_score": 0, "content_score": 0, "category_score": 0})
    
    # 1. Collaborative filtering: items from similar users
    similar_users = db.records.find({
        "labels": ["USER"],
        "where": {"tier": target_user["tier"]}
    })
    
    for user in similar_users.data:
        if user.id == target_user.id:
            continue
        user_items = db.records.find({
            "labels": ["ITEM"],
            "where": {
                "$relation": {"type": "PURCHASED", "direction": "out"},
                "USER": {"$id": user.id}
            }
        })
        for item in user_items.data:
            if item.id not in emma_item_ids:
                candidates[item.id]["item"] = item
                candidates[item.id]["collab_score"] += 1
    
    # 2. Content-based: similar to Emma's items
    for emma_item in emma_items.data[:3]:
        similar = db.records.find({
            "labels": ["ITEM"],
            "where": {
                "$relation": {"type": "SIMILAR_TO", "direction": "in"},
                "ITEM": {"$id": emma_item.id}
            }
        })
        for item in similar.data:
            if item.id not in emma_item_ids:
                candidates[item.id]["item"] = item
                candidates[item.id]["content_score"] += 1
    
    # 3. Category affinity
    top_category = emma_categories.most_common(1)[0][0] if emma_categories else None
    if top_category:
        category_items = db.records.find({
            "labels": ["ITEM"],
            "where": {"category": top_category}
        })
        for item in category_items.data:
            if item.id not in emma_item_ids:
                candidates[item.id]["item"] = item
                candidates[item.id]["category_score"] += 2  # Weight category higher
    
    # Calculate hybrid scores
    ranked = []
    for item_id, scores in candidates.items():
        item = scores["item"]
        hybrid_score = (
            scores["collab_score"] * 3 +
            scores["content_score"] * 2 +
            scores["category_score"]
        )
        ranked.append((hybrid_score, item))
    
    ranked.sort(reverse=True)
    
    print("\nHybrid Recommendations (sorted by combined score):")
    print("-" * 70)
    print(f"{'Score':>6} | {'Item':<30} | {'Category':<12}")
    print("-" * 70)
    
    for score, item in ranked[:10]:
        print(f"{score:>6} | {item['name']:<30} | {item['category']:<12}")


def demo_preference_aggregation():
    """
    DEMO 5: Preference Aggregation
    
    Show how to aggregate user preferences across multiple dimensions
    to build a comprehensive user preference profile.
    """
    print("\n" + "=" * 70)
    print("DEMO 5: Preference Aggregation Analysis")
    print("=" * 70)
    
    # Get all premium users
    premium_users = db.records.find({
        "labels": ["USER"],
        "where": {"tier": "premium"}
    })
    
    print(f"\nAnalyzing {premium_users.total} premium users")
    
    # Aggregate preferences across all premium users
    category_prefs = Counter()
    brand_prefs = Counter()
    price_ranges = {"budget": 0, "mid": 0, "premium": 0}
    
    for user in premium_users.data:
        user_items = db.records.find({
            "labels": ["ITEM"],
            "where": {
                "$relation": {"type": {"$in": ["VIEWED", "PURCHASED"]}, "direction": "out"},
                "USER": {"$id": user.id}
            }
        })
        
        for item in user_items.data:
            category_prefs[item["category"]] += 1
            brand_prefs[item["brand"]] += 1
            
            price = item["price"]
            if price < 30:
                price_ranges["budget"] += 1
            elif price < 80:
                price_ranges["mid"] += 1
            else:
                price_ranges["premium"] += 1
    
    print("\nPremium User Segment Analysis:")
    print("\nTop categories:")
    for cat, count in category_prefs.most_common(5):
        print(f"  {cat}: {count} interactions")
    
    print("\nTop brands:")
    for brand, count in brand_prefs.most_common(5):
        print(f"  {brand}: {count} interactions")
    
    print("\nPrice range preferences:")
    for range_name, count in price_ranges.items():
        pct = (count / sum(price_ranges.values())) * 100 if sum(price_ranges.values()) > 0 else 0
        print(f"  {range_name}: {pct:.1f}%")


def demo_graph_traversal_patterns():
    """
    DEMO 6: Advanced Graph Traversal Patterns
    
    Demonstrate complex relationship traversal for finding:
    - Users who bought items you viewed
    - Items frequently bought together
    - Cross-category preferences
    """
    print("\n" + "=" * 70)
    print("DEMO 6: Advanced Graph Traversal Patterns")
    print("=" * 70)
    
    # Pattern: Find "users who viewed X also viewed Y"
    # This requires finding users who viewed item X, then finding
    # what else those users viewed
    
    print("\nPattern: Users who viewed [X] also viewed...")
    
    # Find a specific item
    target_item = db.records.find_one({
        "labels": ["ITEM"],
        "where": {"category": "electronics"}
    })
    
    if not target_item:
        print("No electronics item found.")
        return
    
    print(f"  Target item: {target_item['name']}")
    
    # Find users who viewed this item
    viewers = db.records.find({
        "labels": ["USER"],
        "where": {
            "$relation": {"type": "VIEWED", "direction": "in"},
            "ITEM": {"$id": target_item.id}
        }
    })
    
    print(f"  Viewed by {viewers.total} users")
    
    # Find what else those users viewed
    co_viewed = Counter()
    for viewer in viewers.data:
        viewer_items = db.records.find({
            "labels": ["ITEM"],
            "where": {
                "$relation": {"type": "VIEWED", "direction": "out"},
                "USER": {"$id": viewer.id}
            }
        })
        for item in viewer_items.data:
            if item.id != target_item.id:
                co_viewed[(item.id, item["name"], item["category"])] += 1
    
    print("\n  Co-viewed items:")
    for (item_id, name, category), count in co_viewed.most_common(5):
        print(f"    [{count} viewers] {name} ({category})")
    
    # Pattern: Find items frequently purchased together
    print("\n\nPattern: Frequently purchased together...")
    
    # Find items that share purchasers
    purchase_pairs = Counter()
    
    all_purchasers = db.records.find({
        "labels": ["USER"],
        "where": {
            "$relation": {"type": "PURCHASED", "direction": "out"}
        }
    })
    
    user_purchases = defaultdict(set)
    for user in all_purchasers.data:
        purchased = db.records.find({
            "labels": ["ITEM"],
            "where": {
                "$relation": {"type": "PURCHASED", "direction": "out"},
                "USER": {"$id": user.id}
            },
            "select": ["id", "name"]
        })
        for item in purchased.data:
            user_purchases[user.id].add((item.id, item["name"]))
    
    # Find pairs
    for user_id, items in user_purchases.items():
        items_list = list(items)
        for i in range(len(items_list)):
            for j in range(i + 1, len(items_list)):
                pair = tuple(sorted([items_list[i][0], items_list[j][0]]))
                names = tuple(sorted([items_list[i][1], items_list[j][1]]))
                purchase_pairs[(pair, names)] += 1
    
    print("  Frequently purchased together:")
    for (pair, names), count in purchase_pairs.most_common(5):
        if count > 1:
            print(f"    [{count} users] {names[0]} <-> {names[1]}")


def main():
    print("\n" + "=" * 70)
    print("PERSONALIZATION ENGINE - GRAPH-BASED USER PREFERENCE MODELING")
    print("=" * 70)
    print("\nThis demonstration shows how to build personalization engines")
    print("using RushDB's property graph capabilities.")
    
    # Check if data exists
    users = db.records.find({"labels": ["USER"], "limit": 1})
    if users.total == 0:
        print("\n" + "=" * 70)
        print("No data found! Run `python seed.py` first.")
        print("=" * 70)
        return
    
    # Run all demos
    demo_user_preference_profile()
    demo_collaborative_filtering()
    demo_content_based_filtering()
    demo_hybrid_recommendations()
    demo_preference_aggregation()
    demo_graph_traversal_patterns()
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Model user preferences as graph relationships")
    print("  2. Use relationship queries for collaborative filtering")
    print("  3. Traverse SIMILAR_TO edges for content-based recs")
    print("  4. Combine multiple signals for hybrid recommendations")
    print("  5. Aggregate across relationships for segment analysis")
    print("\nLearn more: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
