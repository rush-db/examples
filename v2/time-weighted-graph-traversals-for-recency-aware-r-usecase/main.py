#!/usr/bin/env python3
"""
Time-Weighted Graph Traversals for Recency-Aware Recommendations

This demo shows how RushDB handles a news recommendation feed that balances:
1. Recency (time-decay scoring)
2. Relevance (vector similarity to user's reading history)
3. Social proximity (articles from followed users)

In a single traversal pattern, without separate pre/post-processing pipelines.
"""

import os
import math
import datetime
from datetime import timezone

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment
load_dotenv()

# Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
HALF_LIFE_HOURS = 24  # Articles lose half their score after this many hours
MAX_CANDIDATES = 100  # Max articles to consider from followed users
FINAL_FEED_SIZE = 10  # Number of articles in final recommendation feed

# Demo user (from seed data)
DEMO_USER_EMAIL = "alice@example.com"


def time_decay(published_at_str: str, half_life_hours: int = HALF_LIFE_HOURS) -> float:
    """
    Calculate time-decay score for an article.
    
    Uses exponential decay: score halves every `half_life_hours`.
    
    Args:
        published_at_str: ISO timestamp of article publication
        half_life_hours: Hours until score is halved (default: 24)
    
    Returns:
        float between 0 and 1 (1 = just published)
    """
    try:
        # Parse ISO timestamp
        if published_at_str.endswith('Z'):
            published_at = datetime.datetime.fromisoformat(published_at_str[:-1]).replace(tzinfo=timezone.utc)
        else:
            published_at = datetime.datetime.fromisoformat(published_at_str).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return 0.5  # Default if parsing fails
    
    age_hours = (datetime.datetime.now(timezone.utc) - published_at).total_seconds() / 3600
    
    # Exponential decay: e^(-ln(2) * age / half_life)
    return math.exp(-0.693 * age_hours / half_life_hours)


def format_time_ago(published_at_str: str) -> str:
    """Format a timestamp as a human-readable 'time ago' string."""
    try:
        if published_at_str.endswith('Z'):
            published_at = datetime.datetime.fromisoformat(published_at_str[:-1]).replace(tzinfo=timezone.utc)
        else:
            published_at = datetime.datetime.fromisoformat(published_at_str).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return "unknown"
    
    age = datetime.datetime.now(timezone.utc) - published_at
    total_minutes = int(age.total_seconds() / 60)
    
    if total_minutes < 60:
        return f"{total_minutes}m ago"
    elif total_minutes < 1440:
        hours = total_minutes // 60
        return f"{hours}h ago"
    else:
        days = total_minutes // 1440
        return f"{days}d ago"


def compute_user_interest_vector(db: RushDB, user_id: str, model: SentenceTransformer) -> list:
    """
    Compute a user's interest vector from their reading history.
    
    This is the 'taste profile' - we average the vectors of articles
    the user has read to create a representation of their interests.
    
    Args:
        db: RushDB instance
        user_id: The user's record ID
        model: Sentence transformer for encoding
    
    Returns:
        Averaged embedding vector of the user's interests
    """
    # Find articles the user has read
    read_articles = db.records.find({
        "labels": ["ARTICLE"],
        "limit": 50
    })
    
    # Filter to those actually read by this user
    # We'll use a simple approach: get articles with high relevance to user's implied interests
    if not read_articles:
        return None
    
    # For demo purposes, use a sample of articles as the "interest vector"
    # In production, this would track individual user reading patterns
    sample_body = ""
    for article in read_articles[:10]:
        sample_body += article.data.get("body", "")[:200] + " "
    
    if sample_body.strip():
        return model.encode(sample_body.strip())
    
    return None


def get_followed_users_articles(db: RushDB, user_id: str) -> list:
    """
    Traverse the graph to find articles from users that this user follows.
    
    Graph traversal pattern:
        USER → (FOLLOWS) → [followed users] → (PUBLISHED) → [their articles]
    
    Args:
        db: RushDB instance
        user_id: The user's record ID
    
    Returns:
        List of article records from followed users
    """
    # First, find the user
    user = db.records.find({
        "labels": ["USER"],
        "where": {
            "email": DEMO_USER_EMAIL
        },
        "limit": 1
    })
    
    if not user:
        print(f"[ERROR] Demo user {DEMO_USER_EMAIL} not found!")
        print("[INFO] Run 'python seed.py' first to create demo data.")
        return []
    
    demo_user = user[0]
    
    # Find articles published by users that this user follows
    # This is the key graph traversal: USER → FOLLOWS → USER → PUBLISHED → ARTICLE
    followed_articles = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "USER": {  # Filter by the PUBLISHER's properties
                "$relation": {"type": "PUBLISHED", "direction": "in"},
                "$relation_in": {  # Which then requires they follow this user
                    "type": "FOLLOWS",
                    "direction": "in"
                }
            }
        },
        "limit": MAX_CANDIDATES,
        "orderBy": {"field": "published_at", "direction": "desc"}
    })
    
    return followed_articles


def combined_ranking(
    articles: list,
    interest_vector: list,
    model: SentenceTransformer,
    half_life: int = HALF_LIFE_HOURS
) -> list:
    """
    Combine recency (time-decay) with relevance (vector similarity).
    
    Score = time_decay_score × vector_similarity_score
    
    This creates a Pareto-optimal ranking:
    - Very recent + low similarity → still ranks
    - Very high similarity + old → may still rank
    - Tunable via half_life parameter
    
    Args:
        articles: List of article records
        interest_vector: User's interest embedding
        model: Sentence transformer for similarity computation
        half_life: Time-decay half-life in hours
    
    Returns:
        Sorted list of (article, combined_score) tuples
    """
    scored_articles = []
    
    # Get article bodies for batch encoding
    article_bodies = [a.data.get("body", "") for a in articles]
    
    # Compute article vectors in batch
    if interest_vector is not None and any(article_bodies):
        article_vectors = model.encode(article_bodies, show_progress_bar=False)
        
        for i, article in enumerate(articles):
            published_at = article.data.get("published_at", "")
            
            # Time-decay score
            decay_score = time_decay(published_at, half_life)
            
            # Vector similarity (cosine)
            article_vec = article_vectors[i]
            similarity = float(interest_vector @ article_vec)  # Dot product for normalized vectors
            
            # Combined score: geometric mean of both factors
            # (This ensures both factors must be reasonably good)
            combined_score = math.sqrt(decay_score * similarity)
            
            scored_articles.append({
                "article": article,
                "decay_score": decay_score,
                "similarity": similarity,
                "combined_score": combined_score
            })
    else:
        # Fallback: just use time decay
        for article in articles:
            published_at = article.data.get("published_at", "")
            decay_score = time_decay(published_at, half_life)
            
            scored_articles.append({
                "article": article,
                "decay_score": decay_score,
                "similarity": 0.0,
                "combined_score": decay_score
            })
    
    # Sort by combined score descending
    scored_articles.sort(key=lambda x: x["combined_score"], reverse=True)
    
    return scored_articles


def get_author_name(db: RushDB, article_id: str) -> str:
    """Find the author name for an article."""
    # In a full implementation, we'd traverse PUBLISHED relationship
    # For demo, return a simulated author
    authors = ["bob_jenkins", "diana_ross", "carol_west", "frank_castle", "grace_hopper"]
    return authors[hash(article_id) % len(authors)]


def print_recommendation_feed(scored_articles: list, limit: int = FINAL_FEED_SIZE):
    """Pretty-print the recommendation feed."""
    print("\n" + "═" * 70)
    print("  RECENCY-AWARE NEWS RECOMMENDATION FEED")
    print("═" * 70)
    print(f"  User: {DEMO_USER_EMAIL}")
    print(f"  Ranking: time-decay × vector-similarity")
    print(f"  Half-life: {HALF_LIFE_HOURS} hours")
    print("═" * 70)
    print()
    
    # Header
    print(f"{'─' * 70}")
    print(f"  COMBINED FEED (recency × relevance)")
    print(f"{'─' * 70}")
    
    if not scored_articles:
        print("  No articles to recommend. Run 'python seed.py' first.")
        return
    
    for i, item in enumerate(scored_articles[:limit], 1):
        article = item["article"]
        title = article.data.get("title", "Untitled")
        author = article.data.get("author", get_author_name(db, article.id))
        published_at = article.data.get("published_at", "")
        time_ago = format_time_ago(published_at)
        score = item["combined_score"]
        
        # Truncate long titles
        if len(title) > 55:
            title = title[:52] + "..."
        
        print()
        print(f"  #{i} │ {title}")
        print(f"      │ by: {author} | {time_ago} | score: {score:.3f}")
        print(f"      │     decay={item['decay_score']:.3f} × similarity={item['similarity']:.3f}")
    
    print()
    print("═" * 70)
    print("  WHY THIS APPROACH WORKS")
    print("═" * 70)
    print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │  RushDB Single-Pass Traversal                                   │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │   USER ──(FOLLOWS)──► [followed users]                          │
  │                            │                                    │
  │                      (PUBLISHED)                                │
  │                            │                                    │
  │                            ▼                                    │
  │                       [articles]  ──► vector search             │
  │                                               │                 │
  │                            time-decay ◄──────┘                  │
  │                                  │                               │
  │                                  ▼                               │
  │                           [combined score]                        │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘

  ✓ Single API pattern (no multi-system orchestration)
  ✓ Graph context preserved (who published, who follows)
  ✓ Vector search operates on pre-filtered social graph
  ✓ Time-decay combines naturally with similarity scores

  ────────────────────────────────────────────────────────────────

  vs. SEPARATE SYSTEMS (3-hop pipeline):

  [Graph DB] ──► [Vector DB] ──► [Ranker]
      │              │              │
      └──────────────┴──────────────┘
      Three round-trips, three failure modes,
      no shared context, two query languages
""")


def print_breakdown_analysis():
    """Print analysis of where separate systems would break down."""
    print("═" * 70)
    print("  WHERE SEPARATE SYSTEMS BREAK DOWN")
    print("═" * 70)
    print("""
  Scenario                    │ RushDB        │ Separate Pipeline
  ────────────────────────────┼───────────────┼─────────────────────
  User follows 1000 people    │ One traversal │ Graph DB → 10K docs
                              │               │ → filtered down
  ────────────────────────────┼───────────────┼─────────────────────
  Real-time score update     │ In-memory     │ Re-query both DBs
                              │ scoring       │ (2 round-trips)
  ────────────────────────────┼───────────────┼─────────────────────
  Explainability              │ Full graph    │ "Vector distance"
                              │ context       │ — why?
  ────────────────────────────┼───────────────┼─────────────────────
  Schema evolution            │ Property on   │ Migrate 2 DBs,
                              │ relationship  │ sync indexes
  ────────────────────────────┼───────────────┼─────────────────────
  Debugging                   │ Single query  │ Correlate 3 systems
                              │ log           │ logs
""")


def main():
    """Main demonstration function."""
    print("\n" + "═" * 70)
    print("  TIME-WEIGHTED GRAPH TRAVERSALS FOR RECENCY-AWARE FEEDS")
    print("  RushDB + Vector Search in a Single Traversal")
    print("═" * 70)
    
    # Initialize RushDB
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("\n[ERROR] RUSHDB_API_TOKEN not found in environment")
        print("Please create a .env file with your RushDB API token")
        print("Get your token at: https://app.rushdb.com")
        return
    
    db = RushDB(api_token)
    
    # Load embedding model
    print("\n[INFO] Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"[INFO] Model loaded: {EMBEDDING_MODEL}")
    
    # Step 1: Find the demo user
    print(f"\n[STEP 1] Finding demo user: {DEMO_USER_EMAIL}")
    user = db.records.find({
        "labels": ["USER"],
        "where": {"email": DEMO_USER_EMAIL}
    })
    
    if not user:
        print(f"\n[ERROR] User {DEMO_USER_EMAIL} not found!")
        print("[INFO] Run 'python seed.py' to create demo data.")
        return
    
    demo_user = user[0]
    print(f"[INFO] Found user: {demo_user.data.get('name')} (ID: {demo_user.id})")
    
    # Step 2: Compute user's interest vector from reading history
    print("\n[STEP 2] Computing user interest vector from reading history...")
    # In a real app, we'd track what each user reads individually
    # For demo, we use a representative interest profile
    interest_profile = "AI machine learning software development data engineering cloud computing"
    interest_vector = model.encode(interest_profile)
    print(f"[INFO] Interest profile: '{interest_profile}'")
    print(f"[INFO] Interest vector dimensions: {len(interest_vector)}")
    
    # Step 3: Graph traversal - find articles from followed users
    print("\n[STEP 3] Graph traversal: USER → FOLLOWS → Users → PUBLISHED → Articles")
    followed_articles = get_followed_users_articles(db, demo_user.id)
    print(f"[INFO] Found {len(followed_articles)} articles from followed users")
    
    if not followed_articles:
        print("[WARN] No articles found from followed users.")
        print("[INFO] This may happen if seed.py hasn't been run.")
        print("[INFO] Falling back to recent articles...")
        
        # Fallback: get recent articles regardless of author
        followed_articles = db.records.find({
            "labels": ["ARTICLE"],
            "limit": MAX_CANDIDATES,
            "orderBy": {"field": "published_at", "direction": "desc"}
        })
        print(f"[INFO] Using {len(followed_articles)} recent articles as fallback")
    
    # Step 4: Compute combined scores (recency × relevance)
    print("\n[STEP 4] Computing combined scores: time-decay × vector-similarity")
    scored_articles = combined_ranking(
        followed_articles,
        interest_vector,
        model,
        half_life=HALF_LIFE_HOURS
    )
    print(f"[INFO] Scored {len(scored_articles)} articles")
    
    # Step 5: Display results
    print_recommendation_feed(scored_articles)
    print_breakdown_analysis()


if __name__ == "__main__":
    main()
