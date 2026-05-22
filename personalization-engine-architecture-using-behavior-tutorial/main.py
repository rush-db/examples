"""
Personalization Engine - Behavioral Graph Analysis

A production-grade implementation demonstrating how to use RushDB for building
real-time personalization engines. This module showcases graph-based behavioral
analysis for user interest profiling, collaborative filtering, and recommendations.

Architecture:
- User behavior tracked as BEHAVIOR_EVENT nodes in property graph
- Relationships enable O(1) traversal for collaborative filtering
- Interest scores derived from weighted behavioral signals
- Session chains enable real-time context awareness

Run seed.py first to populate the database with sample data.
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

BEHAVIOR_WEIGHTS = {
    "VIEW": 1.0,
    "CLICK": 2.5,
    "ADD_TO_CART": 5.0,
    "PURCHASE": 10.0,
}

SIMILARITY_THRESHOLD = 0.3  # Minimum Jaccard similarity for user matching
TOP_K_RECOMMENDATIONS = 5
SESSION_LOOKBACK_HOURS = 2


# ============================================================================
# Core Graph Analysis Functions
# ============================================================================

def get_user_profile(db: RushDB, user_id: str) -> Optional[dict]:
    """Retrieve comprehensive user profile including interest scores."""
    users = db.records.find({
        "labels": ["USER"],
        "where": {"user_id": user_id}
    })

    if not users.data:
        return None

    user = users.data[0]

    # Get all behavior events
    events = db.records.find({
        "labels": ["BEHAVIOR_EVENT"],
        "where": {
            "SESSION": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"},
                "$id": {"$in": [user.id]}
            }
        }
    })

    # Aggregate behavioral metrics
    behavior_by_type = defaultdict(int)
    products_interacted = set()

    for event in events.data:
        event_type = event.get("type", "VIEW")
        behavior_by_type[event_type] += 1

        # Get related product
        related = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "BEHAVIOR_EVENT": {
                    "$relation": {"type": "RELATES_TO", "direction": "in"},
                    "$id": {"$in": [event.get("__id") or event.get("id")]}
                }
            }
        })
        if related.data:
            products_interacted.add(related.data[0].get("product_id"))

    return {
        "user_id": user.data.get("user_id"),
        "name": user.data.get("name"),
        "total_events": len(events.data),
        "behavior_breakdown": dict(behavior_by_type),
        "products_interacted": list(products_interacted),
        "interest_profile": user.data.get("interest_profile", {}),
    }


def compute_user_interest_vector(db: RushDB, user_id: str) -> dict:
    """
    Compute weighted interest vector across product categories.
    This forms the foundation for collaborative filtering.
    """
    users = db.records.find({
        "labels": ["USER"],
        "where": {"user_id": user_id}
    })

    if not users.data:
        return {}

    user = users.data[0]

    # Find all events and their related products
    events = db.records.find({
        "labels": ["BEHAVIOR_EVENT"],
        "where": {
            "SESSION": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"},
                "$id": {"$in": [user.id]}
            }
        }
    })

    category_scores = defaultdict(float)

    for event in events.data:
        event_type = event.get("type", "VIEW")
        weight = BEHAVIOR_WEIGHTS.get(event_type, 1.0)

        # Get product category
        related = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "BEHAVIOR_EVENT": {
                    "$relation": {"type": "RELATES_TO", "direction": "in"},
                    "$id": {"$in": [event.get("__id") or event.get("id")]}
                }
            }
        })

        if related.data:
            category = related.data[0].get("category", "Unknown")
            category_scores[category] += weight

    # Normalize scores
    max_score = max(category_scores.values()) if category_scores else 1
    return {cat: round(score / max_score, 3) for cat, score in category_scores.items()}


def find_similar_users(db: RushDB, user_id: str, limit: int = 10) -> list:
    """
    Collaborative filtering via Jaccard similarity on product interactions.
    Returns users with overlapping interests for cross-recommendations.
    """
    target_profile = get_user_profile(db, user_id)
    if not target_profile:
        return []

    target_products = set(target_profile.get("products_interacted", []))

    # Get all other users
    all_users = db.records.find({
        "labels": ["USER"],
        "where": {
            "user_id": {"$ne": user_id}
        }
    })

    similarities = []

    for user in all_users.data:
        other_profile = get_user_profile(db, user.data.get("user_id"))
        if not other_profile:
            continue

        other_products = set(other_profile.get("products_interacted", []))

        # Jaccard similarity: intersection / union
        intersection = target_products & other_products
        union = target_products | other_products

        if union:
            similarity = len(intersection) / len(union)

            if similarity >= SIMILARITY_THRESHOLD:
                # Get products this similar user bought that target hasn't
                target_purchases = {
                    p for p in target_products if
                    any(e.get("type") == "PURCHASE" for e in
                        db.records.find({"labels": ["BEHAVIOR_EVENT"]}).data)
                }

                # Find purchases in other user's history
                other_purchases = []
                events = db.records.find({
                    "labels": ["BEHAVIOR_EVENT"],
                    "where": {
                        "SESSION": {
                            "$relation": {"type": "BELONGS_TO", "direction": "in"},
                            "$id": {"$in": [user.id]}
                        },
                        "type": "PURCHASE"
                    }
                })

                for event in events.data:
                    related = db.records.find({
                        "labels": ["PRODUCT"],
                        "where": {
                            "BEHAVIOR_EVENT": {
                                "$relation": {"type": "RELATES_TO", "direction": "in"},
                                "$id": {"$in": [event.get("__id") or event.get("id")]}
                            }
                        }
                    })
                    if related.data:
                        other_purchases.append(related.data[0])

                similarities.append({
                    "user": user.data.get("name"),
                    "user_id": user.data.get("user_id"),
                    "similarity_score": round(similarity, 3),
                    "shared_products": list(intersection),
                    "recommended_products": [p.data for p in other_purchases
                                            if p.data.get("product_id") not in target_products][:5]
                })

    # Sort by similarity and return top-k
    similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similarities[:limit]


def compute_product_affinity(db: RushDB, product_id: str) -> list:
    """
    Discover products frequently co-purchased or co-viewed.
    Essential for 'Frequently Bought Together' recommendations.
    """
    # Find all users who interacted with this product
    target_products = db.records.find({
        "labels": ["PRODUCT"],
        "where": {"product_id": product_id}
    })

    if not target_products.data:
        return []

    target_product = target_products.data[0]
    product_id_internal = target_product.get("__id") or target_product.get("id")

    # Find behavior events for this product
    events = db.records.find({
        "labels": ["BEHAVIOR_EVENT"],
        "where": {
            "PRODUCT": {
                "$relation": {"type": "RELATES_TO", "direction": "in"},
                "$id": {"$in": [product_id_internal]}
            }
        }
    })

    # Get user IDs who interacted with this product
    user_ids = set()
    for event in events.data:
        sessions = db.records.find({
            "labels": ["SESSION"],
            "where": {
                "BEHAVIOR_EVENT": {
                    "$relation": {"type": "PART_OF", "direction": "in"},
                    "$id": {"$in": [event.get("__id") or event.get("id")]}
                }
            }
        })
        for session in sessions.data:
            users = db.records.find({
                "labels": ["USER"],
                "where": {
                    "SESSION": {
                        "$relation": {"type": "BELONGS_TO", "direction": "in"},
                        "$id": {"$in": [session.get("__id") or session.get("id")]}
                    }
                }
            })
            for user in users.data:
                user_ids.add(user.get("__id") or user.get("id"))

    # Find other products these users interacted with
    co_occurrence = defaultdict(int)

    for user_id in user_ids:
        user_events = db.records.find({
            "labels": ["BEHAVIOR_EVENT"],
            "where": {
                "SESSION": {
                    "$relation": {"type": "BELONGS_TO", "direction": "in"},
                    "$id": {"$in": [user_id]}
                }
            }
        })

        for event in user_events.data:
            related = db.records.find({
                "labels": ["PRODUCT"],
                "where": {
                    "BEHAVIOR_EVENT": {
                        "$relation": {"type": "RELATES_TO", "direction": "in"},
                        "$id": {"$in": [event.get("__id") or event.get("id")]}
                    }
                }
            })

            for product in related.data:
                if product.data.get("product_id") != product_id:
                    co_occurrence[product.data.get("product_id")] += 1

    # Sort by co-occurrence frequency
    sorted_affinity = sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)

    results = []
    for pid, count in sorted_affinity[:10]:
        products = db.records.find({
            "labels": ["PRODUCT"],
            "where": {"product_id": pid}
        })
        if products.data:
            results.append({
                "product": products.data[0].data,
                "co_occurrence_count": count,
                "confidence": round(min(count / 10, 1.0), 2)
            })

    return results


def get_session_context(db: RushDB, user_id: str) -> dict:
    """
    Analyze recent session for real-time recommendation context.
    Returns recent product views/actions within lookback window.
    """
    users = db.records.find({
        "labels": ["USER"],
        "where": {"user_id": user_id}
    })

    if not users.data:
        return {}

    user = users.data[0]
    cutoff_time = datetime.now() - timedelta(hours=SESSION_LOOKBACK_HOURS)

    # Find recent sessions
    recent_sessions = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "USER": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"},
                "$id": {"$in": [user.id]}
            }
        },
        "orderBy": {"started_at": "desc"},
        "limit": 5
    })

    recent_views = []
    recent_purchases = []

    for session in recent_sessions.data:
        events = db.records.find({
            "labels": ["BEHAVIOR_EVENT"],
            "where": {
                "SESSION": {
                    "$relation": {"type": "PART_OF", "direction": "in"},
                    "$id": {"$in": [session.get("__id") or session.get("id")]}
                }
            }
        })

        for event in events.data:
            related = db.records.find({
                "labels": ["PRODUCT"],
                "where": {
                    "BEHAVIOR_EVENT": {
                        "$relation": {"type": "RELATES_TO", "direction": "in"},
                        "$id": {"$in": [event.get("__id") or event.get("id")]}
                    }
                }
            })

            if related.data:
                product_info = related.data[0].data
                if event.get("type") == "PURCHASE":
                    recent_purchases.append(product_info.get("name"))
                else:
                    recent_views.append(product_info.get("name"))

    return {
        "recent_views": recent_views[:5],
        "recent_purchases": recent_purchases[:3],
        "session_count": len(recent_sessions.data)
    }


def generate_personalized_recommendations(db: RushDB, user_id: str) -> dict:
    """
    Orchestrate all recommendation strategies into unified output.
    Combines collaborative filtering, interest-based, and session context.
    """
    profile = get_user_profile(db, user_id)
    if not profile:
        return {"error": f"User {user_id} not found"}

    interest_vector = compute_user_interest_vector(db, user_id)
    similar_users = find_similar_users(db, user_id)
    session_context = get_session_context(db, user_id)

    # Interest-based recommendations: top products in user's preferred categories
    interest_recommendations = []
    if interest_vector:
        top_categories = sorted(interest_vector.items(), key=lambda x: x[1], reverse=True)[:3]

        for category, _ in top_categories:
            category_products = db.records.find({
                "labels": ["PRODUCT"],
                "where": {
                    "category": category,
                    "in_stock": True
                },
                "orderBy": {"rating": "desc"},
                "limit": 3
            })

            for product in category_products.data:
                if product.data.get("product_id") not in profile.get("products_interacted", []):
                    interest_recommendations.append({
                        "name": product.data.get("name"),
                        "category": category,
                        "price": product.data.get("price"),
                        "reason": "Interest match"
                    })

    return {
        "user": profile.get("name"),
        "user_id": user_id,
        "interest_vector": interest_vector,
        "behavior_summary": {
            "total_interactions": profile.get("total_events", 0),
            "behavior_breakdown": profile.get("behavior_breakdown", {})
        },
        "collaborative_recommendations": [
            {
                "similar_user": su["user"],
                "similarity": su["similarity_score"],
                "recommended_products": [p.get("name") for p in su["recommended_products"]]
            }
            for su in similar_users[:3]
        ],
        "interest_based_recommendations": interest_recommendations[:TOP_K_RECOMMENDATIONS],
        "session_context": session_context,
    }


# ============================================================================
# Demo Runner
# ============================================================================

def run_demo(db: RushDB) -> None:
    """Execute comprehensive demo of personalization engine."""
    print("\n" + "=" * 70)
    print("PERSONALIZATION ENGINE - Behavioral Graph Analysis Demo")
    print("=" * 70)

    # Get a sample user for demonstration
    sample_users = db.records.find({"labels": ["USER"], "limit": 5})

    if not sample_users.data:
        print("\nNo users found. Please run 'python seed.py' first.")
        return

    # Demo user
    demo_user_id = sample_users.data[0].data.get("user_id", "user_000")

    print(f"\n{'─' * 70}")
    print(f"Analyzing user: {demo_user_id}")
    print(f"{'─' * 70}")

    # 1. User Profile
    print("\n📊 USER PROFILE")
    print("─" * 40)
    profile = get_user_profile(db, demo_user_id)
    if profile:
        print(f"Name: {profile.get('name')}")
        print(f"Total Interactions: {profile.get('total_events')}")
        print(f"Products Explored: {len(profile.get('products_interacted', []))}")
        breakdown = profile.get('behavior_breakdown', {})
        print(f"Behavior Breakdown: {breakdown}")

    # 2. Interest Vector
    print("\n🎯 INTEREST VECTOR")
    print("─" * 40)
    interest_vector = compute_user_interest_vector(db, demo_user_id)
    for category, score in sorted(interest_vector.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(score * 10)
        print(f"  {category:20s} {bar:10s} ({score:.3f})")

    # 3. Collaborative Filtering
    print("\n👥 COLLABORATIVE RECOMMENDATIONS")
    print("─" * 40)
    similar_users = find_similar_users(db, demo_user_id)
    if similar_users:
        for su in similar_users[:3]:
            print(f"  • {su['user']} (similarity: {su['similarity_score']})")
            print(f"    Shared products: {len(su['shared_products'])}")
            print(f"    Recommended: {su['recommended_products'][:2]}")
    else:
        print("  (Not enough behavioral data for similar users yet)")

    # 4. Session Context
    print("\n🕐 SESSION CONTEXT")
    print("─" * 40)
    context = get_session_context(db, demo_user_id)
    print(f"  Recent sessions: {context.get('session_count', 0)}")
    print(f"  Recently viewed: {context.get('recent_views', [])[:5]}")
    print(f"  Recent purchases: {context.get('recent_purchases', [])}")

    # 5. Product Affinity (pick a random product they've interacted with)
    if profile and profile.get('products_interacted'):
        sample_product = profile['products_interacted'][0]
        print(f"\n🔗 PRODUCT AFFINITY: {sample_product}")
        print("─" * 40)
        affinity = compute_product_affinity(db, sample_product)
        if affinity:
            print(f"  Frequently co-purchased with:")
            for item in affinity[:3]:
                print(f"    • {item['product'].get('name')} "
                      f"(count: {item['co_occurrence_count']}, conf: {item['confidence']})")
        else:
            print("  (Not enough purchase data for affinity analysis)")

    # 6. Complete Recommendations
    print("\n" + "=" * 70)
    print("🎁 PERSONALIZED RECOMMENDATIONS")
    print("=" * 70)

    recommendations = generate_personalized_recommendations(db, demo_user_id)

    print(f"\nUser: {recommendations.get('user')}")
    print(f"\nInterest-Based Recommendations:")
    for rec in recommendations.get('interest_based_recommendations', [])[:5]:
        print(f"  • {rec['name']} - ${rec['price']} [{rec['reason']}]")

    print(f"\nCollaborative Recommendations:")
    for collab in recommendations.get('collaborative_recommendations', [])[:3]:
        print(f"  • From '{collab['similar_user']}' users: {collab['recommended_products']}")

    # Graph statistics
    print("\n" + "=" * 70)
    print("📈 GRAPH STATISTICS")
    print("=" * 70)

    stats = {
        "labels": db.labels.find({}),
        "products": db.records.find({"labels": ["PRODUCT"]}),
        "users": db.records.find({"labels": ["USER"]}),
        "sessions": db.records.find({"labels": ["SESSION"]}),
        "events": db.records.find({"labels": ["BEHAVIOR_EVENT"]}),
    }

    print(f"\n  Labels in graph: {[l.name for l in stats['labels']]}")
    print(f"  Total users: {len(stats['users'].data)}")
    print(f"  Total products: {len(stats['products'].data)}")
    print(f"  Total sessions: {len(stats['sessions'].data)}")
    print(f"  Total behavior events: {len(stats['events'].data)}")


def main():
    """Entry point."""
    api_key = os.getenv("RUSHDB_API_KEY")

    if not api_key:
        print("Error: RUSHDB_API_KEY not found")
        print("Please create a .env file with your RushDB API key")
        return

    print("\nInitializing RushDB connection...")
    db = RushDB(api_key)

    # Verify connection and data
    try:
        test = db.records.find({"labels": ["USER"], "limit": 1})
        if not test.data:
            print("\n⚠ No data found in RushDB.")
            print("Please run 'python seed.py' to populate sample data.")
            return
    except Exception as e:
        print(f"\nError connecting to RushDB: {e}")
        return

    run_demo(db)

    print("\n" + "=" * 70)
    print("Demo complete! Explore the code to understand the personalization engine.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
