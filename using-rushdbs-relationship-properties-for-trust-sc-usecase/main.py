"""
Trust-Scored Retrieval Demo

Demonstrates how RushDB combines graph relationships with vector similarity
to enable trust-weighted content retrieval.

This solves a real-world problem: ranking content by both semantic relevance
AND source trustworthiness — something that requires complex multi-system
logic in traditional Postgres + vector DB architectures.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

db = RushDB(os.environ["RUSHD_API_TOKEN"])


def create_vector_index():
    """Create vector index on article body content."""
    print("\n[SETUP] Creating vector index on ARTICLE.body...")

    # Check for existing index
    existing_indexes = db.ai.indexes.find()
    for idx in existing_indexes.data:
        if idx["label"] == "ARTICLE" and idx["propertyName"] == "body":
            print("  Index already exists, skipping creation")
            return

    # Create managed index (RushDB handles embedding generation)
    index = db.ai.indexes.create({
        "label": "ARTICLE",
        "propertyName": "body",
        "sourceType": "managed",
        "dimensions": 768,
        "similarityFunction": "cosine",
    })

    print(f"  ✓ Created index: {index.id}")
    print("  Indexing articles (this may take a moment)...")


def demonstrate_trust_scored_retrieval():
    """
    Demonstrate trust-weighted semantic search.

    The key insight: RushDB stores relationship properties (trust scores)
    as first-class graph entities alongside vector embeddings, enabling
    unified retrieval that combines both signals.
    """
    print("\n" + "=" * 70)
    print("DEMO: Trust-Scored Content Retrieval")
    print("=" * 70)

    query = "machine learning applications"
    print(f"\nQuery: \"{query}\"")
    print("\nRetrieving articles similar to query, weighted by source trust...\n")

    # Step 1: Semantic search to find relevant articles
    print("[STEP 1] Semantic search for relevant articles...")
    search_results = db.ai.search({
        "propertyName": "body",
        "query": query,
        "labels": ["ARTICLE"],
        "limit": 10,
    })

    if not search_results.data:
        print("  No articles found. Run `python seed.py` first.")
        return

    print(f"  Found {len(search_results.data)} semantically similar articles\n")

    # Step 2: For each article, find verifier trust scores via graph traversal
    print("[STEP 2] Graph traversal to get source trust scores...")
    articles_with_trust = []

    for article in search_results.data:
        article_id = article["id"]

        # Find users who verified this article (incoming VERIFIED_BY relationship)
        # In RushDB's relationship model, we query from the article
        verifiers = db.records.find({
            "labels": ["USER"],
            "where": {
                "ARTICLE": {
                    "$relation": {
                        "type": "VERIFIED_BY",
                        "direction": "in"
                    },
                    "$id": article_id
                }
            }
        })

        # Calculate maximum trust score from all verifiers
        max_trust = 0.0
        verifier_names = []
        trust_scores = []

        for verifier in verifiers.data:
            trust = verifier.get("trust_score", 0.0)
            trust_scores.append(trust)
            if trust > max_trust:
                max_trust = trust
            verifier_names.append(verifier.get("name", "Unknown"))

        articles_with_trust.append({
            "article": article,
            "max_trust": max_trust,
            "verifier_count": len(verifiers.data),
            "verifier_names": verifier_names,
            "trust_scores": trust_scores,
        })

    print(f"  Traversed {len(articles_with_trust)} articles for trust data\n")

    # Step 3: Calculate combined score and rank
    print("[STEP 3] Computing combined trust-weighted ranking...\n")

    for item in articles_with_trust:
        # Semantic similarity score from vector search
        semantic_score = item["article"].get("__score", 0.0)
        trust_score = item["max_trust"]

        # Combined score: semantic similarity * (0.5 + 0.5 * trust)
        # This weights trust at 50% of the ranking factor
        combined_score = semantic_score * (0.5 + 0.5 * trust_score)

        item["combined_score"] = combined_score
        item["semantic_score"] = semantic_score

    # Sort by combined score (descending)
    articles_with_trust.sort(key=lambda x: x["combined_score"], reverse=True)

    # Step 4: Display results
    print("=" * 70)
    print("RANKED RESULTS (Trust-Weighted Semantic Search)")
    print("=" * 70)
    print(f"\n{'Rank':<5} {'Title':<45} {'Trust':<6} {'Combined':<8}")
    print("-" * 70)

    for rank, item in enumerate(articles_with_trust, 1):
        article = item["article"]
        title = article.get("title", "Untitled")[:43]
        if len(title) > 40:
            title = title[:40] + "..."

        trust_pct = f"{item['max_trust']:.0%}"
        combined = f"{item['combined_score']:.3f}"

        print(f"{rank:<5} {title:<45} {trust_pct:<6} {combined:<8}")

    # Show detailed breakdown for top result
    print("\n" + "=" * 70)
    print("TOP RESULT DETAIL")
    print("=" * 70)

    top = articles_with_trust[0]
    article = top["article"]

    print(f"\n  Title: {article.get('title')}")
    print(f"  Category: {article.get('category')}")
    print(f"  Semantic Score: {top['semantic_score']:.4f}")
    print(f"  Max Trust: {top['max_trust']:.2%}")
    print(f"  Combined Score: {top['combined_score']:.4f}")
    print(f"  Verified By: {', '.join(top['verifier_names'])}")
    print(f"  Trust Scores: {[f'{s:.0%}' for s in top['trust_scores']]}")


def explain_traditional_approach():
    """Explain why this is complex in Postgres + vector DB."""
    print("\n" + "=" * 70)
    print("WHY THIS MATTERS: Traditional Approach Challenges")
    print("=" * 70)
    print("""
In a Postgres + separate vector database architecture:

1. STORAGE SEPARATION
   - Postgres stores: users, articles, verification relationships, trust scores
   - Vector DB stores: article embeddings for semantic search
   - No native way to join across systems

2. QUERY COMPLEXITY
   - Need separate queries to each system:
     a) Vector DB: semantic similarity search
     b) Postgres: join articles → verifications → users for trust scores
   - Application layer must merge results and calculate combined scores

3. CONSISTENCY CHALLENGES
   - Trust scores update in Postgres, not reflected in vector DB
   - Synchronization issues between systems
   - Two separate consistency models

4. PAGINATION PROBLEMS
   - Top-k results from vector DB may have no trust data
   - Cross-system pagination requires complex buffer management
   - Trust scores not available until after vector search

RushDB solves this by:
   ✓ Single backend (Neo4j) for graph and vectors
   ✓ Relationship properties as first-class citizens
   ✓ Unified query language across both signals
   ✓ Consistent data model for trust and content
""")


def show_why_trust_matters():
    """Show a scenario where trust changes the ranking."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Trust Changes the Ranking")
    print("=" * 70)
    print("""
Consider two articles about the same topic:

  Article A: Technical deep-dive on neural networks
  - Very similar to query (semantic score: 0.92)
  - Verified by "Anonymous User" with trust_score: 0.45
  - Combined Score: 0.92 × (0.5 + 0.5 × 0.45) = 0.92 × 0.725 = 0.667

  Article B: Accessible intro to machine learning
  - Moderately similar to query (semantic score: 0.78)
  - Verified by "Dr. Sarah Chen" with trust_score: 0.99
  - Combined Score: 0.78 × (0.5 + 0.5 × 0.99) = 0.78 × 0.995 = 0.776

  Result: Article B ranks higher despite lower semantic match,
  because the source is significantly more trusted!

This is crucial for:
  - Content moderation: suppress unverified claims
  - Fraud detection: flag suspicious sources
  - Recommendation: prioritize authoritative content
""")


def main():
    print("\n" + "=" * 70)
    print("RUSHDB TRUST-SCORED RETRIEVAL DEMO")
    print("=" * 70)

    # Setup vector index
    create_vector_index()

    # Demonstrate trust-scored retrieval
    demonstrate_trust_scored_retrieval()

    # Explain why this matters
    explain_traditional_approach()

    # Show practical example of trust impact
    show_why_trust_matters()

    print("\n" + "=" * 70)
    print("END OF DEMO")
    print("=" * 70)
    print("\nLearn more: https://docs.rushdb.com")
    print("Get started: https://app.rushdb.com")


if __name__ == "__main__":
    main()
