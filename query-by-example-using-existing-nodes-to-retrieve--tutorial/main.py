"""
Query-by-Example Tutorial for RushDB

This script demonstrates how to use existing nodes as seeds to retrieve
similar contexts in RushDB using Query-by-Example patterns.

Topics covered:
1. Property-Based QBE - find records by example field values
2. Vector-Based QBE - find semantically similar text content
3. Hybrid QBE - combine graph relationships with vector search
4. Edge Cases & Tuning - balancing precision and recall
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()
API_TOKEN = os.getenv("RUSHDB_API_TOKEN")

if not API_TOKEN:
    raise ValueError("RUSHDB_API_TOKEN not found in environment")


db = RushDB(API_TOKEN)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_subsection(title):
    """Print a formatted subsection header."""
    print(f"\n{title}")
    print("-" * 60)


def calculate_field_match(record, example, fields):
    """Calculate how many fields match between two records."""
    matching = sum(1 for f in fields if record.get(f) == example.get(f))
    return int((matching / len(fields)) * 100)


def demonstrate_property_based_qbe():
    """
    DEMO 1: Property-Based Query-by-Example
    
    Use an existing session record as a template to find similar sessions
    based on matching property values.
    """
    print_section("DEMO 1: Property-Based QBE - Finding Similar User Sessions")
    
    # Step 1: Find an example session to use as our QBE seed
    # We'll use a session from Sarah Chen viewing the dashboard
    all_sessions = db.records.find({"labels": ["SESSION"], "limit": 20})
    
    # Find a specific session as our example
    example_session = None
    for session in all_sessions:
        if session.data.get("page") == "dashboard":
            example_session = session
            break
    
    if not example_session:
        print("[SKIP] No dashboard session found. Run seed.py first.")
        return
    
    print(f"\n[STEP 1] Using session as QBE seed:")
    print(f"  - Session ID: {example_session.id}")
    print(f"  - User: {example_session.data.get('userId')}")
    print(f"  - Page: {example_session.data.get('page')}")
    print(f"  - Trigger: {example_session.data.get('trigger')}")
    print(f"  - Duration: {example_session.data.get('duration')}s")
    
    # Step 2: Use QBE to find sessions with similar properties
    # We want sessions from the same user, regardless of page
    print(f"\n[STEP 2] Finding sessions with same userId using QBE pattern...")
    
    similar_by_user = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "userId": example_session.data.get("userId")
        },
        "limit": 10
    })
    
    print(f"\n[RESULT] Found {len(similar_by_user)} sessions from same user:")
    for session in similar_by_user[:5]:
        print(f"  - {session.data.get('sessionId')} ({session.data.get('page')})")
    
    # Step 3: More specific QBE - match multiple fields
    print(f"\n[STEP 3] More specific QBE - matching user AND trigger...")
    
    similar_by_context = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "userId": example_session.data.get("userId"),
            "trigger": example_session.data.get("trigger")
        },
        "limit": 10
    })
    
    print(f"\n[RESULT] Found {len(similar_by_context)} sessions with matching user+trigger:")
    for session in similar_by_context[:3]:
        fields = ["userId", "trigger"]
        match_pct = calculate_field_match(session.data, example_session.data, fields)
        print(f"  - {session.data.get('sessionId')}: {match_pct}% field match")
    
    # Step 4: QBE with graph traversal
    print(f"\n[STEP 4] QBE with graph traversal - find sessions BELONGS_TO same user...")
    
    # Find the user record first
    user = db.records.find({
        "labels": ["USER"],
        "where": {
            "userId": example_session.data.get("userId")
        }
    })
    
    if user:
        # Use graph relationship to find all sessions for this user
        # (Alternative: using USER label in where clause acts as graph traversal)
        related_sessions = db.records.find({
            "labels": ["SESSION"],
            "where": {
                "USER": {
                    "$relation": {"type": "BELONGS_TO", "direction": "in"},
                    "userId": example_session.data.get("userId")
                }
            },
            "limit": 10
        })
        
        print(f"\n[RESULT] Found {len(related_sessions)} sessions via graph traversal:")
        for session in related_sessions[:5]:
            print(f"  - {session.data.get('sessionId')} ({session.data.get('page')})")


def demonstrate_vector_based_qbe():
    """
    DEMO 2: Vector-Based Query-by-Example
    
    Use an existing article's content to find semantically similar articles
    using RushDB's AI semantic search capability.
    """
    print_section("DEMO 2: Vector-Based QBE - Finding Similar Help Articles")
    
    # Step 1: Find an example article about security
    security_article = db.records.find({
        "labels": ["ARTICLE"],
        "where": {"slug": "account-security"}
    })
    
    if not security_article:
        print("[SKIP] No security article found. Run seed.py first.")
        return
    
    security_record = security_article[0]
    print(f"\n[STEP 1] Using article as QBE seed:")
    print(f"  - Title: {security_record.data.get('title')}")
    print(f"  - Tags: {security_record.data.get('tags')}")
    print(f"  - Body preview: {security_record.data.get('body')[:80]}...")
    
    # Step 2: Use the article's body content for vector QBE
    # RushDB automatically embeds the query text using its configured model
    print(f"\n[STEP 2] Performing vector-based QBE with article body...")
    
    similar_articles = db.ai.search({
        "propertyName": "body",
        "query": security_record.data.get("body"),
        "labels": ["ARTICLE"],
        "limit": 5
    })
    
    print(f"\n[RESULT] Found {len(similar_articles)} semantically similar articles:")
    for article in similar_articles:
        score = article.score if hasattr(article, 'score') else article.data.get('__score', 0)
        print(f"  - '{article.data.get('title')}' (score: {score:.2f})")
    
    # Step 3: QBE with query text (not body) - using keywords
    print(f"\n[STEP 3] Vector QBE using search keywords instead of full body...")
    
    keyword_matches = db.ai.search({
        "propertyName": "body",
        "query": "two factor authentication security",
        "labels": ["ARTICLE"],
        "limit": 5
    })
    
    print(f"\n[RESULT] Articles matching 'two factor authentication security':")
    for article in keyword_matches:
        score = article.score if hasattr(article, 'score') else article.data.get('__score', 0)
        print(f"  - '{article.data.get('title')}' (score: {score:.2f})")
    
    # Step 4: QBE filtered by tags (combining vector + structured)
    print(f"\n[STEP 4] Hybrid QBE - vector search filtered by tags...")
    
    filtered_matches = db.ai.search({
        "propertyName": "body",
        "query": "account password login",
        "labels": ["ARTICLE"],
        "where": {
            "tags": {"$contains": "account"}
        },
        "limit": 5
    })
    
    print(f"\n[RESULT] Account-related articles matching query:")
    for article in filtered_matches:
        score = article.score if hasattr(article, 'score') else article.data.get('__score', 0)
        tags = article.data.get('tags', [])
        print(f"  - '{article.data.get('title')}' (score: {score:.2f}, tags: {tags})")


def demonstrate_hybrid_qbe():
    """
    DEMO 3: Hybrid Query-by-Example
    
    Combine graph relationship traversal with vector similarity search
    to find records that are both contextually related AND semantically similar.
    """
    print_section("DEMO 3: Hybrid QBE - Graph Context + Vector Similarity")
    
    # Step 1: Find a billing document as our seed
    billing_seed = db.records.find({
        "labels": ["BILLING"],
        "where": {"slug": "billing_invoice"}
    })
    
    if not billing_seed:
        print("[SKIP] No billing documents found. Run seed.py first.")
        return
    
    billing_record = billing_seed[0]
    print(f"\n[STEP 1] Using billing document as QBE seed:")
    print(f"  - Title: {billing_record.data.get('title')}")
    print(f"  - Body: {billing_record.data.get('body')}")
    
    # Step 2: Perform vector QBE across all documents
    print(f"\n[STEP 2] Vector QBE to find similar content across all labels...")
    
    all_similar = db.ai.search({
        "propertyName": "body",
        "query": billing_record.data.get("body"),
        "limit": 10
    })
    
    print(f"\n[RESULT] Top semantically similar to billing content:")
    for item in all_similar[:5]:
        score = item.score if hasattr(item, 'score') else item.data.get('__score', 0)
        label = item.data.get('__label', 'UNKNOWN')
        print(f"  - [{label}] '{item.data.get('title')}' (score: {score:.2f})")
    
    # Step 3: Filter vector results by label (hybrid approach)
    print(f"\n[STEP 3] Hybrid QBE - combining label filter with vector similarity...")
    
    # First, get all ARTICLE records that mention similar concepts
    billing_articles = db.ai.search({
        "propertyName": "body",
        "query": billing_record.data.get("body"),
        "labels": ["ARTICLE", "BILLING"],  # Search across multiple labels
        "limit": 10
    })
    
    print(f"\n[RESULT] Articles + Billing docs similar to seed:")
    for item in billing_articles:
        score = item.score if hasattr(item, 'score') else item.data.get('__score', 0)
        label = item.data.get('__label', 'UNKNOWN')
        print(f"  - [{label}] '{item.data.get('title')}' (score: {score:.2f})")
    
    # Step 4: Sequential hybrid - find user, then find their sessions
    print(f"\n[STEP 4] Sequential Hybrid QBE:")
    print(f"  (Find related records via graph, then apply vector similarity)")
    
    # Find a pro user
    pro_user = db.records.find({
        "labels": ["USER"],
        "where": {"plan": "pro"}
    })
    
    if pro_user:
        pro_user = pro_user[0]
        print(f"\n  - Found pro user: {pro_user.data.get('name')}")
        
        # Find all their sessions (graph traversal)
        their_sessions = db.records.find({
            "labels": ["SESSION"],
            "where": {
                "USER": {
                    "userId": pro_user.data.get("userId")}
            },
            "limit": 10
        })
        
        print(f"  - Found {len(their_sessions)} sessions via graph traversal")
        
        # Show session patterns
        if their_sessions:
            pages = [s.data.get("page") for s in their_sessions]
            print(f"  - Pages visited: {', '.join(pages[:5])}")


def demonstrate_edge_cases_and_tuning():
    """
    DEMO 4: Edge Cases & Tuning
    
    Explore practical considerations when using QBE:
    - Partial property matching
    - Score threshold tuning
    - Graph distance weighting
    """
    print_section("DEMO 4: Edge Cases & Tuning")
    
    # 4a: Partial property matching
    print_subsection("4a. Partial Property Match - Sessions with Specific Trigger")
    
    # Find sessions triggered by 'viewing_product'
    product_sessions = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "trigger": {"$in": ["viewing_product", "checkout_started"]}
        },
        "limit": 10
    })
    
    print(f"\n[RESULT] Found {len(product_sessions)} product-focused sessions:")
    for session in product_sessions[:5]:
        print(f"  - {session.data.get('sessionId')}: {session.data.get('trigger')}")
    
    # 4b: Low similarity threshold
    print_subsection("4b. Low Similarity Threshold (0.5) - More Results")
    
    broad_matches = db.ai.search({
        "propertyName": "body",
        "query": "authentication security login",
        "labels": ["ARTICLE"],
        "limit": 10
    })
    
    # Filter to low threshold
    low_threshold = [m for m in broad_matches 
                      if (m.score if hasattr(m, 'score') else m.data.get('__score', 0)) >= 0.50]
    
    print(f"\n[RESULT] Found {len(low_threshold)} articles with similarity >= 0.50:")
    for article in low_threshold:
        score = article.score if hasattr(article, 'score') else article.data.get('__score', 0)
        print(f"  - '{article.data.get('title')}' (score: {score:.2f})")
    
    # 4c: High similarity threshold
    print_subsection("4c. High Similarity Threshold (0.85) - Precise Results")
    
    # Filter to high threshold
    high_threshold = [m for m in broad_matches 
                       if (m.score if hasattr(m, 'score') else m.data.get('__score', 0)) >= 0.85]
    
    print(f"\n[RESULT] Found {len(high_threshold)} articles with similarity >= 0.85:")
    for article in high_threshold:
        score = article.score if hasattr(article, 'score') else article.data.get('__score', 0)
        print(f"  - '{article.data.get('title')}' (score: {score:.2f})")
    
    # 4d: Graph distance as a factor
    print_subsection("4d. Graph-Distance Weighted Results - Same User Context")
    
    # Find a specific user
    sarah = db.records.find({
        "labels": ["USER"],
        "where": {"name": {"$contains": "Sarah"}}
    })
    
    if sarah:
        sarah = sarah[0]
        print(f"\n[RESULT] User '{sarah.data.get('name')}' sessions:")
        
        # All sessions for Sarah (1-hop graph distance)
        sarah_sessions = db.records.find({
            "labels": ["SESSION"],
            "where": {
                "USER": {
                    "$relation": {"type": "BELONGS_TO", "direction": "in"},
                    "userId": sarah.data.get("userId")
                }
            },
            "limit": 10
        })
        
        print(f"  - Found {len(sarah_sessions)} sessions (1-hop from user):")
        for session in sarah_sessions[:5]:
            print(f"    * {session.data.get('sessionId')}: {session.data.get('page')}")
    
    # 4e: Handling missing properties with fallbacks
    print_subsection("4e. QBE with Missing Properties - Using Fallbacks")
    
    # Some records might not have all properties - use $exists or provide defaults
    all_sessions = db.records.find({"labels": ["SESSION"], "limit": 5})
    
    print(f"\n[RESULT] Sample session properties check:")
    for session in all_sessions[:3]:
        has_events = session.data.get("events") is not None
        has_duration = session.data.get("duration") is not None
        print(f"  - {session.data.get('sessionId')}:")
        print(f"    * has 'events': {has_events}, value: {session.data.get('events')}")
        print(f"    * has 'duration': {has_duration}, value: {session.data.get('duration')}")


def main():
    """"Run all QBE demonstrations."""
    print("\n" + "=" * 80)
    print("Query-by-Example Tutorial: Finding Similar Contexts in RushDB")
    print("=" * 80)
    print("\nThis tutorial demonstrates 4 QBE patterns:")
    print("  1. Property-Based QBE - find records by example field values")
    print("  2. Vector-Based QBE - find semantically similar text content")
    print("  3. Hybrid QBE - combine graph relationships with vector search")
    print("  4. Edge Cases & Tuning - practical considerations")
    
    try:
        demonstrate_property_based_qbe()
        demonstrate_vector_based_qbe()
        demonstrate_hybrid_qbe()
        demonstrate_edge_cases_and_tuning()
        
        print("\n" + "=" * 80)
        print("Tutorial completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Tutorial failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure you've run 'python seed.py' to create sample data")
        print("  2. Verify your RUSHDB_API_TOKEN is correct in .env")
        print("  3. Check your RushDB dashboard for any API issues")
        raise


if __name__ == "__main__":
    main()
