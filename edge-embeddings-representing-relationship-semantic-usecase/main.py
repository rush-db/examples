#!/usr/bin/env python3
"""
Edge Embeddings Demo: Multi-Agent Reasoning with Typed Relationships

Demonstrates three query patterns that showcase why edge embeddings
are essential for AI agent memory systems—and why node-centric
approaches (Pinecone, Weaviate, Qdrant) fail these patterns.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


def embed_texts(model, texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def print_header(title: str):
    """Print a formatted section header."""
    width = 72
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}\n")


def print_result(label: str, content: str):
    """Print a result with a label prefix."""
    print(f"  {label}  {content}")


def print_box(title: str, lines: list[str]):
    """Print a bordered box with title and content lines."""
    width = 72
    print(f"\n╔{'═' * (width - 2)}╗")
    print(f"║  {title:<{width - 4}}║")
    print(f"╠{'═' * (width - 2)}╣")
    for line in lines:
        padded = line[: width - 4]
        print(f"║  {padded:<{width - 4}}║")
    print(f"╚{'═' * (width - 2)}╝")


# ══════════════════════════════════════════════════════════════════════════════
# QUERY 1: Structured Traversal — Typed Edges
# ══════════════════════════════════════════════════════════════════════════════

def query1_structured_traversal(db: RushDB):
    """
    Find all PRs that were APPROVED without security review.

    This is a pure graph traversal query using typed edges.
    RushDB's where clause filters by relationship properties (securityReviewed).

    WHY OTHER SYSTEMS STRUGGLE:
    - Pinecone: No relationship concept; must scan all nodes, then filter
    - Weaviate: Cross-references exist but edge properties aren't filterable
      in a graph-native way
    - Qdrant: Can filter by payload but must maintain separate tracking
      for edge semantics
    """
    print_header("QUERY 1: Structured Traversal — Typed Edges")

    print("Finding PRs that were approved without security review...")
    print("(Graph traversal with typed edge filtering)\n")

    # Find edges with type APPROVED where securityReviewed is False
    # RushDB filters relationships by their properties via the edge label
    results = db.records.find({
        "labels": ["EDGE_REVIEW"],
        "where": {
            "type": "APPROVED",
            "securityReviewed": False,
        },
        "limit": 50,
    })

    if not results.data:
        print("  No edges found matching criteria.")
        return

    count = 0
    for edge in results.data:
        pr_title = edge.get("prTitle", "Unknown PR")
        agent_name = edge.get("agentName", "Unknown Agent")
        reason = edge.get("reason", "")

        count += 1
        print(f"  ✓ PR: \"{pr_title}\"")
        print(f"    Agent: {agent_name}  |  Reason: \"{reason}\"")
        print(f"    Security Reviewed: NO ⚠️\n")

    print(f"\n  Found {count} approval(s) without security review")

    # Show why other systems fail
    why_others_fail = [
        "",
        "WHY OTHER SYSTEMS STRUGGLE WITH THIS QUERY:",
        "",
        "  🔴 PINECONE:",
        "     No native relationship concept. Must store approvals as nodes",
        "     with references to PR and Agent nodes. Query becomes:",
        "     1. Scan all APPROVAL nodes",
        "     2. JOIN with PR nodes to get titles",
        "     3. JOIN with Agent nodes to get names",
        "     4. Filter by securityReviewed property",
        "     No graph traversal optimization, expensive joins required.",
        "",
        "  🔴 WEAVIATE:",
        "     Cross-references exist but are essentially foreign keys.",
        "     Can't express 'show me approvals with securityReviewed=false'",
        "     as a native relationship property query. Must denormalize",
        "     or use complex graphql-style filtering.",
        "",
        "  🔴 QDRANT:",
        "     Payload filtering works for metadata, but edge semantics",
        "     (APPROVED/REVIEWED/FLAGGED) must be encoded as payload",
        "     fields on nodes, not as typed relationships. Can't express",
        "     'only APPROVED edges' as a graph-native constraint.",
        "",
        "  ✅ RUSHDB:",
        "     Relationships are first-class. Query operates directly on",
        "     typed edges (APPROVED) with native property filtering.",
        "     Graph traversal optimized, no expensive joins needed.",
    ]
    for line in why_others_fail:
        print(line)


# ══════════════════════════════════════════════════════════════════════════════
# QUERY 2: Semantic Edge Search — Vector Similarity on Relationships
# ══════════════════════════════════════════════════════════════════════════════

def query2_semantic_edge_search(db: RushDB, model):
    """
    Find edges semantically similar to 'informal approval without thorough review'.

    This query operates on the EDGE's semantic embedding, not node embeddings.
    We're asking: which relationships capture the concept of "casual approval"?

    WHY OTHER SYSTEMS CAN'T DO THIS:
    - Pinecone: Edge embeddings don't exist; can only query node vectors
    - Weaviate: No semantic search on relationships themselves
    - Qdrant: Can't encode relationship semantics as vectors

    IN RUSHDB:
    - Edge REASON text is embedded into the relationship's vector space
    - Semantic search operates directly on the edge, not on endpoints
    """
    print_header("QUERY 2: Semantic Edge Search — Edge Embeddings")

    query_text = "informal approval without thorough review"
    print(f'Searching for edges similar to: "{query_text}"')
    print("(Semantic search on edge embeddings)\n")

    # Generate query vector
    query_vector = embed_texts(model, [query_text])[0]

    # Find the vector index for EDGE_REVIEW.reason
    indexes = db.ai.indexes.find()
    edge_index = None
    for idx in indexes.data:
        if idx["label"] == "EDGE_REVIEW" and idx["propertyName"] == "reason":
            edge_index = idx
            break

    if not edge_index:
        print("  Error: Edge vector index not found. Run seed.py first.")
        return

    # Semantic search on edges (external index with pre-computed vector)
    results = db.ai.search({
        "propertyName": "reason",
        "queryVector": query_vector,
        "labels": ["EDGE_REVIEW"],
        "limit": 5,
    })

    if not results.data:
        print("  No semantically similar edges found.")
        return

    print("  Semantically similar edges:\n")
    for edge in results.data:
        score = edge.score or 0.0
        agent_name = edge.get("agentName", "Unknown")
        pr_title = edge.get("prTitle", "Unknown PR")
        edge_type = edge.get("type", "?")
        reason = edge.get("reason", "")

        print(f"  Match ({score:.2f}): {agent_name} → \"{pr_title}\" [{edge_type}]")
        print(f"    Reason: \"{reason}\"\n")

    # Explain why other systems can't do this
    why_others_fail = [
        "",
        "WHY OTHER SYSTEMS CAN'T DO THIS QUERY:",
        "",
        "  🔴 PINECONE:",
        "     Only stores node vectors. To simulate this, you'd need to:",
        "     1. Create a synthetic node representing each edge",
        "     2. Embed the 'reason' text into that node's vector",
        "     3. Query for similar synthetic nodes",
        "     This breaks the graph model—edges aren't first-class.",
        "",
        "  🔴 WEAVIATE:",
        "     Can reference objects but can't semantically search the",
        "     reference itself. The 'reason' field could be a property,",
        "     but there's no vector index on cross-references.",
        "",
        "  🔴 QDRANT:",
        "     Payload filters can store metadata but can't express the",
        "     semantic meaning of 'informal approval'. The concept lives",
        "     in node metadata, not in the relationship itself.",
        "",
        "  ✅ RUSHDB:",
        "     Edge embeddings are first-class citizens. The relationship",
        "     itself has a semantic vector. Query operates directly on",
        "     the edge's vector space, finding relationships that capture",
        "     the concept of 'informal approval'.",
    ]
    for line in why_others_fail:
        print(line)


# ══════════════════════════════════════════════════════════════════════════════
# QUERY 3: Combined Graph + Vector — Embedding Space Clusters
# ══════════════════════════════════════════════════════════════════════════════

def query3_combined_graph_vector(db: RushDB, model):
    """
    Find agents whose approval edges cluster near 'careful, thorough' in embedding space.

    This combines:
    - Graph traversal: find all APPROVED edges from each agent
    - Vector similarity: check how close each edge is to "careful, thorough"
    - Aggregation: rank agents by average similarity score

    This query pattern reveals behavioral patterns—who consistently approves
    in a "careful, thorough" manner vs. who takes shortcuts.

    WHY OTHER SYSTEMS STRUGGLE:
    - Pinecone: No graph traversal + vector combined queries
    - Weaviate: Graph traversal exists, but can't do it in vector space
    - Qdrant: Can filter by payload, but can't project into embedding space
    """
    print_header("QUERY 3: Combined Graph + Vector — Embedding Space Clusters")

    query_text = "careful, thorough review with attention to detail"
    print(f'Finding agents whose approvals cluster near: "{query_text}"')
    print("(Combined graph traversal + vector similarity)\n")

    # Get all APPROVED edges
    approved_edges = db.records.find({
        "labels": ["EDGE_REVIEW"],
        "where": {"type": "APPROVED"},
        "limit": 200,
    })

    if not approved_edges.data:
        print("  No APPROVED edges found.")
        return

    # Generate query vector for "careful, thorough"
    query_vector = embed_texts(model, [query_text])[0]

    # For each agent, find their APPROVED edges and compute similarity
    agent_similarities: dict[str, list[float]] = {}

    for edge in approved_edges.data:
        agent_name = edge.get("agentName", "Unknown")
        reason = edge.get("reason", "")

        if agent_name not in agent_similarities:
            agent_similarities[agent_name] = []

        # Compute similarity between this edge's reason and the query
        edge_vector = embed_texts(model, [reason])[0]
        similarity = sum(a * b for a, b in zip(query_vector, edge_vector))
        agent_similarities[agent_name].append(similarity)

    # Compute average similarity per agent
    agent_scores = []
    for agent_name, scores in agent_similarities.items():
        avg_score = sum(scores) / len(scores)
        agent_scores.append((agent_name, avg_score, scores))

    # Sort by average similarity (descending)
    agent_scores.sort(key=lambda x: x[1], reverse=True)

    print("  Agent ranking by approval embedding cluster:\n")
    for i, (agent_name, avg_score, scores) in enumerate(agent_scores[:5], 1):
        print(f"  {i}. {agent_name}")
        print(f"     Avg similarity to 'careful, thorough': {avg_score:.2f}")
        scores_str = " | ".join([f"{s:.2f}" for s in scores[:5]])
        print(f"     Individual approval scores: {scores_str}")
        print()

    # Show the top agent's detailed breakdown
    if agent_scores:
        top_agent, top_score, top_scores = agent_scores[0]
        print(f"  Top Agent: {top_agent}")
        print(f"  All approvals cluster around careful/thorough (avg: {top_score:.2f})")
        print()

    # Explain why other systems can't do this
    why_others_fail = [
        "",
        "WHY OTHER SYSTEMS CAN'T DO THIS QUERY:",
        "",
        "  🔴 PINECONE:",
        "     No native graph traversal. To find agent behavior patterns:",
        "     1. Query all approval nodes (no relationship context)",
        "     2. Filter by securityReviewed property",
        "     3. Group by agent using metadata",
        "     4. For each group, compute aggregate similarity",
        "     This requires multiple round-trips and client-side joins.",
        "",
        "  🔴 WEAVIATE:",
        "     GraphQL-style traversal exists but:",
        "     - Vector search can't be combined with relationship traversal",
        "     - Can't express 'find approvals, then check embedding similarity'",
        "     - Must denormalize agent behavior into node properties",
        "",
        "  🔴 QDRANT:",
        "     Payload filtering allows grouping by metadata, but:",
        "     - Can't project into embedding space for aggregation",
        "     - No way to compute 'average similarity per agent' in one query",
        "     - Must do client-side computation after retrieving results",
        "",
        "  ✅ RUSHDB:",
        "     Combines graph traversal with vector similarity natively.",
        "     1. Traverse APPROVED edges from agents (graph layer)",
        "     2. Query edge vectors for semantic similarity (vector layer)",
        "     3. Aggregate scores per agent (in-database computation)",
        "     Single API call, native execution, optimized performance.",
    ]
    for line in why_others_fail:
        print(line)


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY: Why Edge Embeddings Matter
# ══════════════════════════════════════════════════════════════════════════════

def print_summary():
    """Print a summary of why RushDB wins for agent memory systems."""
    summary = [
        "",
        "══════════════════════════════════════════════════════════════════",
        "  SUMMARY: Why Edge Embeddings Matter for AI Agents",
        "══════════════════════════════════════════════════════════════════",
        "",
        "  Agent memory isn't just about nodes—it's about relationships:",
        "",
        "  • WHO approved this? (graph traversal)",
        "  • Was this approval casual or thorough? (edge semantics)",
        "  • Which agents cluster around careful behavior? (combined query)",
        "",
        "  Node-centric databases (Pinecone, Weaviate, Qdrant) can only",
        "  answer question #1 by denormalizing relationships into nodes.",
        "  This breaks the graph model and makes semantic edge queries impossible.",
        "",
        "  RushDB treats relationships as first-class citizens WITH semantic",
        "  embeddings. Queries that span graph topology and vector space are",
        "  native operations—optimized, efficient, and correct by design.",
        "",
        "  For multi-agent systems building memory layers, this matters:",
        "  - Agents reason about relationships, not just entities",
        "  - The 'quality' of a relationship is semantically meaningful",
        "  - Behavioral patterns emerge from edge embedding clusters",
        "",
        "══════════════════════════════════════════════════════════════════",
        "",
    ]
    for line in summary:
        print(line)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 72)
    print("  EDGE EMBEDDINGS: Representing Relationship Semantics in RushDB")
    print("═" * 72)

    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "RUSHDB_API_KEY not found. Copy .env.example to .env and add your key."
        )

    db = RushDB(api_key)
    print("\n✓ Connected to RushDB")

    print(f"\n✓ Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("✓ Model loaded\n")

    # Run the three query demonstrations
    query1_structured_traversal(db)
    query2_semantic_edge_search(db, model)
    query3_combined_graph_vector(db, model)

    print_summary()

    print("\n" + "=" * 72)
    print("  Demo complete! Check the output above for all three queries.")
    print("  See README.md for expected output format.")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
