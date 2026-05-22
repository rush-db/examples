#!/usr/bin/env python3
"""
Query-by-Example: Finding Similar Users via Graph Structure and Vector Affinity

This script demonstrates the QBE pattern using RushDB to:
1. Identify a high-value "target" user from existing data
2. Find structurally similar users using graph relationships
3. Re-rank results by vector similarity for content affinity
4. Extend to anomaly detection (fraud pattern matching)
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()


@dataclass
class SimilarUser:
    """Represents a similar user result."""
    id: str
    name: str
    email: str
    is_premium: bool
    lifetime_value: float
    purchase_count: int
    similarity_score: float


def find_target_user(db: RushDB) -> Optional[dict]:
    """
    Step 1: Find the high-value "target" user.
    
    We use the user marked as 'is_target=True' during seeding,
    which represents our gold-standard user profile.
    """
    print("\n" + "=" * 60)
    print("Step 1: Identifying High-Value Target User")
    print("=" * 60 + "\n")

    # Find the designated target user
    result = db.records.find({
        "labels": ["USER"],
        "where": {"is_target": True}
    })

    if not result.data:
        # Fallback: find highest LTV user
        result = db.records.find({
            "labels": ["USER"],
            "orderBy": {"field": "lifetime_value", "direction": "desc"},
            "limit": 1
        })

    if not result.data:
        print("ERROR: No users found. Please run `python seed.py` first.")
        return None

    target = result.data[0]
    print(f"Target User: {target['name']}")
    print(f"  Email: {target['email']}")
    print(f"  Premium: {target['is_premium']}")
    print(f"  Lifetime Value: ${target['lifetime_value']:.2f}")
    print(f"  Purchase Count: {target['purchase_count']}")
    print(f"  Join Date: {target['join_date']}")

    return target


def find_structurally_similar_users(db: RushDB, target: dict, limit: int = 20) -> list:
    """
    Step 2: Find users with similar graph structure.
    
    QBE Pattern: Use the target's properties as a template to find
    structurally similar users. This captures relationship patterns
    (same products purchased, similar cohorts) that pure vector search misses.
    """
    print("\n" + "=" * 60)
    print("Step 2: Finding Structurally Similar Users (Graph Pattern)")
    print("=" * 60 + "\n")

    # Get target's cohort parameters
    target_premium = target.get("is_premium", False)
    target_join_date = target.get("join_date", "")

    # QBE: Find users with same premium status (structural similarity)
    result = db.records.find({
        "labels": ["USER"],
        "where": {
            # Direct property match from target
            "is_premium": target_premium,
            # Exclude target user
            "is_target": {"$ne": True},
            # Similar account age (±30 days)
            "account_age_days": {
                "$gte": max(0, target.get("account_age_days", 0) - 30),
                "$lte": target.get("account_age_days", 0) + 30
            }
        },
        "limit": limit
    })

    print(f"Found {len(result.data)} users matching structural pattern:")
    print(f"  - Premium status: {target_premium}")
    print(f"  - Account age range: ±30 days of target")
    print(f"  - Excluded: Target user\n")

    for user in result.data[:5]:  # Show first 5
        print(f"  • {user['name']} — LTV: ${user['lifetime_value']:.2f}")

    return result.data


def rank_by_vector_affinity(db: RushDB, target: dict, candidates: list, limit: int = 10) -> list:
    """
    Step 3: Re-rank candidates by vector similarity.
    
    The dual-layer advantage: graph filtering gives us structurally similar
    candidates, then vector search ranks by content/semantic affinity.
    
    This combines:
    - Graph structure (relationship patterns)
    - Vector similarity (behavior profile embedding)
    """
    print("\n" + "=" * 60)
    print("Step 3: Re-ranking by Vector Affinity (Dual-Layer Search)")
    print("=" * 60 + "\n")

    # Get candidate IDs (exclude target)
    candidate_ids = [u.id for u in candidates if u.id != target.id]

    if not candidate_ids:
        print("No candidates to rank.")
        return []

    # Use RushDB's managed AI search with the target's behavior profile
    # The SDK will embed the query from target's profile text
    results = db.ai.search({
        "propertyName": "behavior_profile",
        "labels": ["USER"],
        "where": {
            "$id": {"$in": candidate_ids}
        },
        "limit": limit
    })

    print(f"Top {limit} users ranked by behavior profile similarity:\n")

    ranked_users = []
    for rank, result in enumerate(results.data, 1):
        similarity = result.score if hasattr(result, 'score') else 0.0
        print(f"  {rank}. {result['name']:<25} similarity: {similarity:.3f}  LTV: ${result.get('lifetime_value', 0):.2f}")
        ranked_users.append({
            "rank": rank,
            "user": result,
            "similarity": similarity
        })

    return ranked_users


def detect_anomalies(db: RushDB, target: Optional[dict] = None) -> list:
    """
    Step 4: Extend QBE to anomaly detection.
    
    Use a known fraud pattern to find structurally similar suspicious transactions.
    This demonstrates how QBE scales beyond recommendations to detection use cases.
    """
    print("\n" + "=" * 60)
    print("Step 4: Anomaly Detection (Fraud Pattern Matching)")
    print("=" * 60 + "\n")

    # Find confirmed fraud cases
    fraud_cases = db.records.find({
        "labels": ["FRAUD_CASE"],
        "where": {
            "status": "confirmed",
            "risk_score": {"$gte": 0.9}
        }
    })

    if not fraud_cases.data:
        print("No fraud patterns found in database.")
        return []

    fraud_pattern = fraud_cases.data[0]
    fraud_amount = fraud_pattern.get("amount", 0)

    print(f"Known fraud pattern: Order #{fraud_pattern.id[:8]}")
    print(f"  Amount: ${fraud_amount:.2f}")
    print(f"  Risk Score: {fraud_pattern.get('risk_score', 0):.2f}")
    print(f"  Pattern Type: {fraud_pattern.get('pattern_type', 'unknown')}")

    # QBE: Find purchases with similar structural characteristics
    # - Similar amount range (±15%)
    # - Associated with new accounts (≤30 days)
    # - Has prior chargebacks
    similar_purchases = db.records.find({
        "labels": ["PURCHASE"],
        "where": {
            "amount": {
                "$gte": fraud_amount * 0.85,
                "$lte": fraud_amount * 1.15
            },
            "status": {"$ne": "refunded"},
            # Filter by buyer's characteristics via relationship
            "MADE_BY": {
                "$relation": {"type": "MADE", "direction": "in"},
                "account_age_days": {"$lte": 30},
                "prior_chargebacks": {"$gte": 1}
            }
        },
        "limit": 10
    })

    print(f"\nFound {len(similar_purchases.data)} potentially suspicious transactions:\n")

    suspicious_list = []
    for tx in similar_purchases.data:
        # Get the buyer info through the relationship
        buyer_query = db.records.find({
            "labels": ["USER"],
            "where": {
                "MADE": {
                    "$relation": {"type": "MADE", "direction": "out"},
                    "$id": tx.id
                }
            }
        })

        buyer = buyer_query.data[0] if buyer_query.data else None
        print(f"  ⚠ Order #{tx.id[:8]} — ${tx['amount']:.2f}")
        print(f"     Buyer: {buyer['name'] if buyer else 'Unknown'}")
        print(f"     Account Age: {buyer['account_age_days'] if buyer else '?'} days")
        print(f"     Chargebacks: {buyer['prior_chargebacks'] if buyer else '?'}")
        print()

        suspicious_list.append({
            "transaction": tx,
            "buyer": buyer
        })

    return suspicious_list


def demonstrate_qbe_advantages():
    """
    Print a comparison of QBE vs manual Cypher approaches.
    """
    print("\n" + "=" * 60)
    print("QBE vs Manual Cypher: Tradeoffs")
    print("=" * 60 + "\n")

    print("""
Approach 1: Manual Cypher Query (equivalent logic)
──────────────────────────────────────────────────

    MATCH (target:USER {is_target: true})
    MATCH (u:USER)-[:MADE]->(p:PURCHASE)-[:INCLUDES]->(prod:PRODUCT)
    WHERE u.is_premium = target.is_premium
      AND u.account_age_days BETWEEN target.account_age_days - 30 
                                      AND target.account_age_days + 30
    WITH u, collect(prod.name) as products
    // Then call vector similarity separately
    // etc...

Pro: Fine-grained control
Con: Requires graph DB expertise, harder to maintain


Approach 2: QBE with RushDB (this pattern)
─────────────────────────────────────────────

    # Step 1: Find target
    target = db.records.find({"labels": ["USER"], "where": {"is_target": True}})

    # Step 2: Find structurally similar (property matching)
    similar = db.records.find({
        "labels": ["USER"],
        "where": {
            "is_premium": target.is_premium,
            "account_age_days": {"$gte": ..., "$lte": ...}
        }
    })

    # Step 3: Rank by vector affinity
    ranked = db.ai.search({
        "propertyName": "behavior_profile",
        "labels": ["USER"],
        "where": {"$id": {"$in": candidate_ids}}
    })

Pro: Intuitive, schema-flexible, combines graph + vector natively
Con: Less control over traversal depth (use raw Cypher for complex hops)
""")


def main():
    """Run the complete QBE demonstration."""
    print("\n" + "=" * 60)
    print("Query-by-Example: User Similarity with RushDB")
    print("=" * 60)

    # Check API key
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\nERROR: RUSHDB_API_KEY not found in environment.")
        print("Please create a .env file with your API key (see .env.example)")
        return

    # Connect to RushDB
    print("\nConnecting to RushDB...")
    db = RushDB(api_key)
    print("  ✓ Connected\n")

    # Step 1: Find target user
    target = find_target_user(db)
    if not target:
        return

    # Step 2: Find structurally similar users (QBE pattern)
    candidates = find_structurally_similar_users(db, target)

    # Step 3: Re-rank by vector affinity (dual-layer)
    ranked_users = rank_by_vector_affinity(db, target, candidates)

    # Step 4: Anomaly detection extension
    suspicious = detect_anomalies(db, target)

    # Show QBE advantages
    demonstrate_qbe_advantages()

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60 + "\n")
    print(f"Target User: {target['name']}")
    print(f"Structurally Similar Users Found: {len(candidates)}")
    print(f"Top Similar by Vector Affinity: {len(ranked_users)}")
    print(f"Suspicious Transactions Detected: {len(suspicious)}")
    print("\nQBE Pattern Complete ✓\n")


if __name__ == "__main__":
    main()
