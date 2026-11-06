"""
Graph-based Feature Stores for ML Model Training Pipelines

This tutorial demonstrates how to use RushDB as a graph-based feature store
for building ML training pipelines. It covers:

1. Feature schema design using graph records and relationships
2. Feature engineering via graph traversal
3. Training dataset construction from graph queries
4. Collaborative features using multi-hop traversal

Target audience: Senior engineers building ML infrastructure
"""

import os
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
db = RushDB()


def print_section(title):
    """Pretty-print section headers."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def count_records():
    """Count records by label for summary."""
    labels = ["USER", "PRODUCT", "PURCHASE", "VIEW", "SEGMENT", "CATEGORY"]
    counts = {}
    for label in labels:
        result = db.records.find({"labels": [label], "limit": 1})
        counts[label] = result.total
    return counts


# ============================================================================
# SECTION 1: Feature Schema Design
# ============================================================================

def demonstrate_feature_schema():
    """
    Graph-based feature stores model features as interconnected records.
    Each record type (label) represents a feature category.
    """
    print_section("1. Feature Schema Design")

    print("\nFeature schema modeled as graph:")
    print("""
    ┌─────────┐      ┌──────────┐      ┌──────────┐
    │   USER  │──────│ PURCHASE │──────│  PRODUCT │
    └─────────┘      └──────────┘      └──────────┘
         │                 │                 │
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐      ┌─────────┐      ┌──────────┐
    │ SEGMENT │      │   VIEW  │      │ CATEGORY │
    └─────────┘      └─────────┘      └──────────┘

    Each node = feature group
    Each edge = relationship between features
    """)

    # Query the schema to show what we have
    labels = db.labels.find()
    print("\nAvailable feature labels in this graph:")
    for label in labels:
        print(f"  - {label.name}: {label.count} records")


# ============================================================================
# SECTION 2: Feature Engineering via Graph Traversal
# ============================================================================

def demonstrate_feature_engineering():
    """
    Features are computed by traversing the graph.
    This shows common feature engineering patterns.
    """
    print_section("2. Feature Engineering via Graph Traversal")

    # Find a sample user
    users = db.records.find({"labels": ["USER"], "limit": 1}).data
    if not users:
        print("\nNo users found. Run seed.py first.")
        return

    sample_user = users[0]
    user_email = sample_user.data.get("email", "unknown")

    print(f"\nComputing features for user: {user_email}")

    # Pattern 1: Count features via relationship traversal
    # Find all purchases by this user
    purchases = db.records.find({
        "labels": ["PURCHASE"],
        "where": {
            "USER": {"$id": {"$in": [sample_user.id]}}
        }
    })
    purchase_count = purchases.total

    # Pattern 2: Aggregate features (sum, avg)
    total_spend = sum(p.data.get("total", 0) for p in purchases.data)
    avg_order_value = total_spend / purchase_count if purchase_count > 0 else 0

    # Pattern 3: Recency features
    if purchases.data:
        latest_purchase = max(
            purchases.data,
            key=lambda p: p.data.get("date", "")
        )
        latest_date = datetime.fromisoformat(latest_purchase.data["date"])
        days_since_purchase = (datetime.now() - latest_date).days
    else:
        days_since_purchase = 999

    # Pattern 4: View-based behavioral features
    views = db.records.find({
        "labels": ["VIEW"],
        "where": {
            "USER": {"$id": {"$in": [sample_user.id]}}
        }
    })
    view_count = views.total

    # Pattern 5: Cross-category aggregations (affinity features)
    # Get products from purchases and calculate category distribution
    purchase_products = []
    for p in purchases.data:
        # Find product related to this purchase
        related_products = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "PURCHASE": {"$id": {"$in": [p.id]}}
            }
        })
        purchase_products.extend(related_products.data)

    # Calculate category affinity
    category_counts = defaultdict(int)
    for prod in purchase_products:
        # Find category of product
        cats = db.records.find({
            "labels": ["CATEGORY"],
            "where": {
                "PRODUCT": {"$id": {"$in": [prod.id]}}
            }
        })
        for cat in cats.data:
            category_counts[cat.data["name"]] += 1

    # Normalize to probabilities
    total_purchases = sum(category_counts.values()) or 1
    category_affinity = {
        cat: round(count / total_purchases, 2)
        for cat, count in category_counts.items()
    }

    # Display computed features
    print("\nComputed features:")
    print(f"  - purchase_count: {purchase_count}")
    print(f"  - total_spend: ${total_spend:,.2f}")
    print(f"  - avg_order_value: ${avg_order_value:,.2f}")
    print(f"  - days_since_last_purchase: {days_since_purchase}")
    print(f"  - view_count: {view_count}")
    print(f"  - category_affinity: {dict(category_affinity)}")


def demonstrate_aggregate_features():
    """
    Compute aggregate features across segments using graph traversal.
    """
    print("\n--- Segment-level Aggregate Features ---")

    segments = db.records.find({"labels": ["SEGMENT"]}).data

    for segment in segments:
        segment_name = segment.data.get("name", "unknown")

        # Find all users in this segment
        users_in_segment = db.records.find({
            "labels": ["USER"],
            "where": {
                "SEGMENT": {"$id": {"$in": [segment.id]}}
            }
        })

        # Compute aggregate stats
        user_ids = [u.id for u in users_in_segment.data]

        if not user_ids:
            continue

        # Get all purchases for these users
        purchases = db.records.find({
            "labels": ["PURCHASE"],
            "where": {
                "USER": {"$id": {"$in": user_ids}}
            }
        })

        # Get all views for these users
        views = db.records.find({
            "labels": ["VIEW"],
            "where": {
                "USER": {"$id": {"$in": user_ids}}
            }
        })

        # Calculate aggregates
        purchase_count = purchases.total
        total_spend = sum(p.data.get("total", 0) for p in purchases.data)
        view_count = views.total
        avg_purchases = purchase_count / len(user_ids) if user_ids else 0
        avg_spend = total_spend / len(user_ids) if user_ids else 0

        print(f"\n  Segment: {segment_name}")
        print(f"    - users: {len(user_ids)}")
        print(f"    - avg_purchase_count: {avg_purchases:.1f}")
        print(f"    - avg_total_spend: ${avg_spend:,.2f}")
        print(f"    - avg_view_count: {view_count / len(user_ids):.1f}")


# ============================================================================
# SECTION 3: Training Dataset Construction
# ============================================================================

def build_feature_vector(user_record, purchases, views):
    """
    Build a feature vector for a single user.
    This is the core function that would be used in a training pipeline.
    """
    features = {}

    # Basic user features
    features["age"] = user_record.data.get("age", 0)
    features["is_active"] = 1 if user_record.data.get("is_active", False) else 0

    # Registration age (days since registration)
    reg_date = user_record.data.get("registration_date")
    if reg_date:
        reg = datetime.fromisoformat(reg_date)
        features["account_age_days"] = (datetime.now() - reg).days
    else:
        features["account_age_days"] = 0

    # Purchase-based features
    features["purchase_count"] = len(purchases)
    features["total_spend"] = sum(p.data.get("total", 0) for p in purchases)
    features["avg_order_value"] = (
        features["total_spend"] / features["purchase_count"]
        if features["purchase_count"] > 0
        else 0
    )

    # View-based features
    features["view_count"] = len(views)
    if views:
        avg_duration = sum(v.data.get("duration_seconds", 0) for v in views) / len(views)
        features["avg_view_duration"] = avg_duration
    else:
        features["avg_view_duration"] = 0

    # Recency features
    if purchases:
        latest = max(purchases, key=lambda p: p.data.get("date", ""))
        latest_date = datetime.fromisoformat(latest.data["date"])
        features["days_since_last_purchase"] = (datetime.now() - latest_date).days
    else:
        features["days_since_last_purchase"] = 999

    return features


def demonstrate_training_dataset():
    """
    Construct a training dataset by traversing the graph.
    This pattern is the foundation of graph-based feature stores.
    """
    print_section("3. Training Dataset Construction")

    # Get all users
    all_users = db.records.find({"labels": ["USER"]}).data
    print(f"\nBuilding training dataset for {len(all_users)} users...")

    # Process in batches (simulating real pipeline)
    batch_size = 50
    all_features = []
    all_labels = []

    for i in range(0, len(all_users), batch_size):
        batch_users = all_users[i:i + batch_size]
        batch_features = []
        batch_labels = []

        for user in batch_users:
            # Get user's purchases
            purchases = db.records.find({
                "labels": ["PURCHASE"],
                "where": {
                    "USER": {"$id": {"$in": [user.id]}}
                }
            }).data

            # Get user's views
            views = db.records.find({
                "labels": ["VIEW"],
                "where": {
                    "USER": {"$id": {"$in": [user.id]}}
                }
            }).data

            # Build feature vector
            features = build_feature_vector(user, purchases, views)
            batch_features.append(features)

            # Create label (example: high-value customer = spent > $500)
            label = 1 if features["total_spend"] > 500 else 0
            batch_labels.append(label)

        all_features.extend(batch_features)
        all_labels.extend(batch_labels)

        print(f"  Batch {i // batch_size + 1}: processed {len(batch_users)} users")

    # Convert to matrix form (what you'd feed to sklearn/tensorFlow)
    feature_names = list(all_features[0].keys())
    X = [[f[name] for name in feature_names] for f in all_features]
    y = all_labels

    print(f"\nTraining dataset built:")
    print(f"  - samples: {len(X)}")
    print(f"  - features: {len(feature_names)}")
    print(f"  - feature names: {feature_names}")
    print(f"  - label distribution: 0={y.count(0)}, 1={y.count(1)}")

    return X, y, feature_names


# ============================================================================
# SECTION 4: Collaborative Features via Multi-hop Traversal
# ============================================================================

def demonstrate_collaborative_features():
    """
    Graph-based feature stores enable collaborative features.
    Find users with similar behavior patterns via graph traversal.
    """
    print_section("4. Collaborative Features (Multi-hop Traversal)")

    # Pick a sample user
    users = db.records.find({"labels": ["USER"], "limit": 10}).data
    if not users:
        return

    sample_user = users[0]
    sample_email = sample_user.data.get("email", "unknown")
    print(f"\nFinding users similar to: {sample_email}")

    # Find products this user purchased
    user_purchases = db.records.find({
        "labels": ["PURCHASE"],
        "where": {
            "USER": {"$id": {"$in": [sample_user.id]}}
        }
    }).data

    # Get the products from these purchases
    purchased_products = set()
    for purchase in user_purchases:
        products = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "PURCHASE": {"$id": {"$in": [purchase.id]}}
            }
        }).data
        for prod in products:
            purchased_products.add(prod.id)

    print(f"  - Purchased {len(purchased_products)} unique products")

    # Multi-hop: find other users who purchased the same products
    # This is the core of collaborative filtering
    other_users = db.records.find({
        "labels": ["USER"],
        "where": {
            "$not": {"$id": {"$in": [sample_user.id]}}
        }
    }).data

    similarity_scores = []
    for other_user in other_users:
        # Find other user's purchases
        other_purchases = db.records.find({
            "labels": ["PURCHASE"],
            "where": {
                "USER": {"$id": {"$in": [other_user.id]}}
            }
        }).data

        # Get other user's products
        other_products = set()
        for purchase in other_purchases:
            products = db.records.find({
                "labels": ["PRODUCT"],
                "where": {
                    "PURCHASE": {"$id": {"$in": [purchase.id]}}
                }
            }).data
            for prod in products:
                other_products.add(prod.id)

        # Calculate Jaccard similarity
        if purchased_products or other_products:
            intersection = len(purchased_products & other_products)
            union = len(purchased_products | other_products)
            similarity = intersection / union if union > 0 else 0

            if similarity > 0:
                similarity_scores.append({
                    "user": other_user,
                    "similarity": similarity,
                    "shared_products": intersection
                })

    # Sort by similarity and show top matches
    similarity_scores.sort(key=lambda x: x["similarity"], reverse=True)
    top_matches = similarity_scores[:5]

    print(f"\n  Top {len(top_matches)} similar users:")
    for i, match in enumerate(top_matches, 1):
        email = match["user"].data.get("email", "unknown")
        print(f"    {i}. {email}")
        print(f"       similarity: {match['similarity']:.3f}")
        print(f"       shared products: {match['shared_products']}")

    # Use similar users to generate collaborative recommendations
    print("\n  Collaborative recommendations:")

    # Aggregate products purchased by similar users
    recommendation_counts = defaultdict(int)
    for match in similarity_scores[:10]:  # Use top 10 similar users
        # Get their purchases
        purchases = db.records.find({
            "labels": ["PURCHASE"],
            "where": {
                "USER": {"$id": {"$in": [match["user"].id]}}
            }
        }).data

        for purchase in purchases:
            products = db.records.find({
                "labels": ["PRODUCT"],
                "where": {
                    "PURCHASE": {"$id": {"$in": [purchase.id]}}
                }
            }).data

            for prod in products:
                # Only recommend if sample user hasn't purchased it
                if prod.id not in purchased_products:
                    recommendation_counts[prod.data.get("name", "unknown")] += 1

    # Sort and show top recommendations
    sorted_recs = sorted(
        recommendation_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    for product_name, count in sorted_recs:
        print(f"    - {product_name} (purchased by {count} similar users)")


# ============================================================================
# SECTION 5: Real-time Feature Serving Pattern
# ============================================================================

def demonstrate_realtime_pattern():
    """
    Show how the same graph structure supports both batch training
    and real-time feature serving.
    """
    print_section("5. Real-time Feature Serving Pattern")

    print("""
    The graph structure naturally supports both use cases:

    BATCH TRAINING:
    ├─ Traverse all historical data for all users
    ├─ Build feature matrices for model fitting
    └─ Run periodically (daily, weekly)

    REAL-TIME SERVING:
    ├─ Fetch single user's record by ID
    ├─ Traverse recent relationships (last 30 days)
    ├─ Compute same features on-the-fly
    └─ Return within milliseconds
    """)

    # Simulate real-time feature fetch
    users = db.records.find({"labels": ["USER"], "limit": 1}).data
    if not users:
        return

    user = users[0]
    user_id = user.id

    print(f"\nReal-time feature fetch for user ID: {user_id}")

    # Fetch user record directly (fast, O(1) lookup)
    user_record = db.records.findById(user_id)
    print(f"  User: {user_record.data.get('email', 'unknown')}")

    # Fetch recent purchases (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    recent_purchases = db.records.find({
        "labels": ["PURCHASE"],
        "where": {
            "USER": {"$id": {"$in": [user_id]}},
            "date": {"$gte": thirty_days_ago}
        }
    })

    print(f"  Recent purchases (30d): {recent_purchases.total}")

    # Fetch recent views
    recent_views = db.records.find({
        "labels": ["VIEW"],
        "where": {
            "USER": {"$id": {"$in": [user_id]}},
            "date": {"$gte": thirty_days_ago}
        }
    })

    print(f"  Recent views (30d): {recent_views.total}")

    # Build real-time feature vector (same function as batch)
    rt_features = build_feature_vector(
        user_record,
        recent_purchases.data,
        recent_views.data
    )

    print(f"\n  Real-time features:")
    for name, value in rt_features.items():
        print(f"    - {name}: {value}")


# ============================================================================
# SECTION 6: Feature Lineage Tracking
# ============================================================================

def demonstrate_feature_lineage():
    """
    Graph structure naturally tracks feature lineage.
    Every feature inherits the provenance of its source records.
    """
    print_section("6. Feature Lineage Tracking")

    print("""
    Graph structure preserves data provenance:

    Feature = USER.purchase_count
    ├─ Source: PURCHASE records
    ├─ Traversal: USER → PURCHASE
    ├─ Aggregation: COUNT
    └─ Lineage: user_id, purchase_id, date

    This enables:
    - Debugging feature computation
    - Auditing model inputs
    - Explaining predictions
    """)

    # Demonstrate by showing a purchase's lineage
    purchases = db.records.find({"labels": ["PURCHASE"], "limit": 1}).data
    if not purchases:
        return

    purchase = purchases[0]
    print(f"\nPurchase {purchase.id} lineage:")
    print(f"  - total: ${purchase.data.get('total', 0):.2f}")
    print(f"  - date: {purchase.data.get('date', 'unknown')}")
    print(f"  - payment: {purchase.data.get('payment_method', 'unknown')}")

    # Show connected records (proving the graph relationship)
    # Find the user who made this purchase
    users = db.records.find({
        "labels": ["USER"],
        "where": {
            "PURCHASE": {"$id": {"$in": [purchase.id]}}
        }
    })
    print(f"  - placed_by: {users.data[0].data.get('email', 'unknown') if users.data else 'unknown'}")

    # Find the product purchased
    products = db.records.find({
        "labels": ["PRODUCT"],
        "where": {
            "PURCHASE": {"$id": {"$in": [purchase.id]}}
        }
    })
    if products.data:
        print(f"  - product: {products.data[0].data.get('name', 'unknown')}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the complete tutorial."""
    print("\n" + "=" * 60)
    print(" GRAPH-BASED FEATURE STORES FOR ML MODEL TRAINING ")
    print("=" * 60)

    # Check if data exists
    counts = count_records()
    print(f"\nGraph contains: {sum(counts.values())} total records")

    if sum(counts.values()) == 0:
        print("\n⚠ No data found. Please run 'python seed.py' first.")
        return

    for label, count in counts.items():
        if count > 0:
            print(f"  - {label}: {count}")

    # Run all sections
    demonstrate_feature_schema()
    demonstrate_feature_engineering()
    demonstrate_aggregate_features()
    demonstrate_training_dataset()
    demonstrate_collaborative_features()
    demonstrate_realtime_pattern()
    demonstrate_feature_lineage()

    print("\n" + "=" * 60)
    print(" Tutorial complete!")
    print("=" * 60)
    print("""
    Key takeaways:

    1. Features as Graph Records:
       - Each feature category = label
       - Each feature instance = record
       - Rich attributes on every node

    2. Feature Engineering via Traversal:
       - Count features: traverse relationships and count
       - Aggregate features: collect and sum/avg
       - Recency features: compare dates
       - Affinity features: cross-category aggregations

    3. Training Data from Graph:
       - Traverse from anchor entities
       - Build feature vectors per sample
       - Same pattern scales to millions

    4. Collaborative Features:
       - Multi-hop traversal finds similar users
       - Jaccard similarity on product overlap
       - Collaborative filtering without matrix ops

    5. Real-time Serving:
       - Same graph, single-user queries
       - Efficient via ID lookups
       - Sub-second feature computation

    Learn more: https://docs.rushdb.com
    """)


if __name__ == "__main__":
    main()
