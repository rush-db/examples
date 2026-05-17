"""
5 RAG Developer Pain Points That Graph Memory Solves

This demo shows how RushDB's graph + vector architecture solves
the real problems that pure vector stores cannot handle.

Run after: python seed.py
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")

db = RushDB(api_key, url=url) if url else RushDB(api_key)

# ---------------------------------------------------------------------------
# PAIN POINT 1: Entity Traversal
# Vector stores can search "user X" but cannot traverse to find their history.
# Graph query: Find all tickets submitted by a specific user.
# ---------------------------------------------------------------------------

def pain_point_1_entity_traversal():
    print("\n" + "=" * 60)
    print("PAIN POINT 1: Entity Traversal")
    print("=" * 60)
    print("\nProblem: Pure vector stores return semantically similar chunks.")
    print("         They cannot traverse 'user X's support history' as a graph query.")
    print("\nSolution: RushDB finds user by email, then traverses SUBMITTED edges.")
    print()

    # Find user by email
    user = db.records.find_one({
        "labels": ["USER"],
        "where": {"email": "alice@example.com"}
    })

    if not user:
        print("  [ERROR] User alice@example.com not found. Run seed.py first.")
        return

    print(f"  User: {user['name']} ({user['email']})")
    print()

    # Graph traversal: Find user's tickets via relationship
    tickets = db.records.find({
        "labels": ["TICKET"],
        "where": {
            "USER": {
                "$relation": {"type": "SUBMITTED", "direction": "in"},
                "email": "alice@example.com"
            }
        }
    })

    print(f"  [Graph] Found {tickets.total} tickets via entity traversal:")
    for ticket in tickets.data:
        print(f"    - {ticket['ticketId']}: {ticket['description']}")
        print(f"      Status: {ticket['status']}, Priority: {ticket['priority']}")

    print("\n  ✓ Single graph query instead of:")
    print("    1. Search "user Alice" → 2. Get ID → 3. Filter tickets → 4. Join manually")


# ---------------------------------------------------------------------------
# PAIN POINT 2: Multi-hop Graph Queries
# Vector stores require multiple retrievals + manual joining.
# Graph query: "Issues before v2.4 → their fixes → release dates"
# ---------------------------------------------------------------------------

def pain_point_2_multi_hop_queries():
    print("\n" + "=" * 60)
    print("PAIN POINT 2: Multi-hop Graph Queries")
    print("=" * 60)
    print("\nProblem: 'Issues before v2.4 and their fixes' requires:")
    print("         - Multiple vector retrievals")
    print("         - Manual result joining")
    print("         - No relationship context")
    print("\nSolution: Single graph query traverses USER → TICKET → ISSUE → FIX → RELEASE")
    print()

    # Find issues reported in releases before v2.4
    issues = db.records.find({
        "labels": ["ISSUE"],
        "where": {
            "reportedIn": {"$in": ["v2.2", "v2.3"]}
        }
    })

    print(f"  [Graph] Found {issues.total} issues before v2.4:")
    for issue in issues.data:
        print(f"\n    Issue: {issue['summary']}")
        print(f"    Component: {issue['component']}, Severity: {issue['severity']}")

        # Traverse to fix via RESOLVED_BY edge
        fixes = db.records.find({
            "labels": ["FIX"],
            "where": {
                "ISSUE": {
                    "$relation": {"type": "RESOLVED_BY", "direction": "in"},
                    "__id": issue.id
                }
            }
        })

        if fixes.total > 0:
            fix = fixes.data[0]
            print(f"    Fix: {fix['description']}")
            print(f"    Released in: {fix['releasedIn']}")

        # Traverse to API affected
        apis = db.records.find({
            "labels": ["API"],
            "where": {
                "ISSUE": {
                    "$relation": {"type": "AFFECTS", "direction": "in"},
                    "__id": issue.id
                }
            }
        })

        if apis.total > 0:
            api = apis.data[0]
            print(f"    Affects: {api['name']} ({api['purpose']})")

    print("\n  ✓ Single logical query, multiple relationship traversals")
    print("    Equivalent vector approach: 3 separate searches + manual join")


# ---------------------------------------------------------------------------
# PAIN POINT 3: Entity Disambiguation
# "The billing API" means different things in different contexts.
# Vector stores retrieve fresh chunks without temporal context.
# ---------------------------------------------------------------------------

def pain_point_3_entity_disambiguation():
    print("\n" + "=" * 60)
    print("PAIN POINT 3: Entity Disambiguation")
    print("=" * 60)
    print("\nProblem: 'The billing API' — which one? v2.2 (payment) or v2.3 (invoices)?")
    print("         Vector stores return fresh chunks without knowing WHICH billing API.")
    print("\nSolution: Graph maintains temporal context; API nodes know their release.")
    print()

    # Query "billing API" - graph resolves to specific node by context
    apis = db.records.find({
        "labels": ["API"],
        "where": {
            "name": {"$contains": "Billing"}
        }
    })

    print("  [Graph] Resolving 'billing API' across contexts:")
    for api in apis.data:
        print(f"\n    {api['name']}")
        print(f"    Purpose: {api['purpose']}")
        print(f"    Introduced in: {api['context']}")

    # Find which tickets reference which billing API
    print("\n  Resolving which tickets relate to which billing API:")

    for api in apis.data:
        # Find tickets that track issues affecting this API
        tickets = db.records.find({
            "labels": ["TICKET"],
            "where": {
                "ISSUE": {
                    "$relation": {"type": "TRACKS", "direction": "out"}
                }
            }
        })

        # Filter tickets connected to this API through issue chain
        relevant_tickets = []
        for ticket in tickets.data:
            issues = db.records.find({
                "labels": ["ISSUE"],
                "where": {
                    "TICKET": {
                        "$relation": {"type": "TRACKS", "direction": "in"},
                        "ticketId": ticket["ticketId"]
                    },
                    "component": api["name"].replace("_v1", "").replace("_v2", "").replace("v1", "").replace("v2", "")
                }
            })
            if issues.total > 0:
                relevant_tickets.append(ticket)

        if relevant_tickets:
            print(f"\n    {api['name']} referenced in:")
            for t in relevant_tickets:
                print(f"      - {t['ticketId']}: {t['description'][:60]}...")

    print("\n  ✓ Graph maintains entity identity across time")
    print("    Vector stores would just return "billing API" chunks, no disambiguation")


# ---------------------------------------------------------------------------
# PAIN POINT 4: Relationship Joins
# "Ticket → User → Issue → Release" requires multiple retrievals + manual joining.
# ---------------------------------------------------------------------------

def pain_point_4_relationship_joins():
    print("\n" + "=" * 60)
    print("PAIN POINT 4: Relationship Joins")
    print("=" * 60)
    print("\nProblem: "Get full context for ticket T001" requires:")
    print("         1. Find ticket → 2. Find user → 3. Find issue → 4. Find release")
    print("\nSolution: Graph traversal follows edges in one logical operation.")
    print()

    ticket = db.records.find_one({
        "labels": ["TICKET"],
        "where": {"ticketId": "T001"}
    })

    if not ticket:
        print("  [ERROR] Ticket T001 not found. Run seed.py first.")
        return

    print(f"  Starting from ticket: {ticket['ticketId']}")
    print(f"  Description: {ticket['description']}")
    print()

    # Traverse: TICKET → USER
    users = db.records.find({
        "labels": ["USER"],
        "where": {
            "TICKET": {
                "$relation": {"type": "SUBMITTED", "direction": "in"},
                "ticketId": "T001"
            }
        }
    })
    if users.total > 0:
        user = users.data[0]
        print(f"  [Graph] User: {user['name']} ({user['email']})")
        print(f"           Tier: {user['tier']}")

    # Traverse: TICKET → ISSUE
    issues = db.records.find({
        "labels": ["ISSUE"],
        "where": {
            "TICKET": {
                "$relation": {"type": "TRACKS", "direction": "in"},
                "ticketId": "T001"
            }
        }
    })
    if issues.total > 0:
        issue = issues.data[0]
        print(f"\n  [Graph] Issue: {issue['summary']}")
        print(f"           Severity: {issue['severity']}")

        # Traverse: ISSUE → FIX
        fixes = db.records.find({
            "labels": ["FIX"],
            "where": {
                "ISSUE": {
                    "$relation": {"type": "RESOLVED_BY", "direction": "in"},
                    "__id": issue.id
                }
            }
        })
        if fixes.total > 0:
            fix = fixes.data[0]
            print(f"\n  [Graph] Fix: {fix['description']}")
            print(f"           Released in: {fix['releasedIn']}")

    # Traverse: TICKET → RELEASE
    releases = db.records.find({
        "labels": ["RELEASE"],
        "where": {
            "TICKET": {
                "$relation": {"type": "REPORTED_IN", "direction": "in"},
                "ticketId": "T001"
            }
        }
    })
    if releases.total > 0:
        release = releases.data[0]
        print(f"\n  [Graph] Reported in: {release['version']} ({release['codename']})")
        print(f"           Released: {release['releasedAt']}")

    print("\n  ✓ Full chain: TICKET → USER → ISSUE → FIX → RELEASE")
    print("    Pure vector would need 4+ separate retrievals + manual joining")


# ---------------------------------------------------------------------------
# PAIN POINT 5: Semantic + Graph Hybrid
# Combine semantic search with graph filtering.
# ---------------------------------------------------------------------------

def pain_point_5_semantic_graph_hybrid():
    print("\n" + "=" * 60)
    print("PAIN POINT 5: Semantic + Graph Hybrid")
    print("=" * 60)
    print("\nProblem: "Find high-priority tickets mentioning billing" requires:")
    print("         - Semantic search for "billing"")
    print("         - Manual filter for priority")
    print("         - No graph context")
    print("\nSolution: Semantic search + graph WHERE clause in one query.")
    print()

    # Get all indexes to find ticket description index
    indexes = db.ai.indexes.find().data
    ticket_index_id = None
    for idx in indexes:
        if idx.get("label") == "TICKET" and idx.get("propertyName") == "description":
            ticket_index_id = idx.get("__id")
            break

    if not ticket_index_id:
        print("  [ERROR] Ticket description index not found. Run seed.py first.")
        return

    # First, pure semantic search for "billing"
    print("  [Vector] Pure semantic search for 'billing':")
    semantic_results = db.ai.search({
        "propertyName": "description",
        "query": "billing payment invoice",
        "labels": ["TICKET"],
        "limit": 10
    })

    print(f"    Found {semantic_results.total} semantically similar tickets")
    for r in semantic_results.data[:3]:
        print(f"    - {r['ticketId']}: {r['description'][:50]}... (score: {r.score:.3f})")

    # Now, semantic + graph filter: high priority + "billing"
    print("\n  [Graph + Vector] Hybrid: high priority tickets mentioning 'billing':")

    # Get high priority tickets via graph
    high_priority_tickets = db.records.find({
        "labels": ["TICKET"],
        "where": {
            "priority": {"$in": ["high", "critical"]}
        }
    })

    # Embed high priority ticket descriptions and find similar to "billing"
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    query_vector = model.encode("billing payment invoice").tolist()

    # Search within the high priority subset
    for ticket in high_priority_tickets.data:
        ticket_vec = model.encode(ticket["description"]).tolist()
        from numpy import dot
        from numpy.linalg import norm
        similarity = dot(query_vector, ticket_vec) / (norm(query_vector) * norm(ticket_vec))

        if similarity > 0.3:  # Threshold for "billing" relevance
            print(f"\n    {ticket['ticketId']}: {ticket['description']}")
            print(f"      Priority: {ticket['priority']}, Status: {ticket['status']}")
            print(f"      Semantic relevance to 'billing': {similarity:.3f}")

    print("\n  ✓ Graph filters + semantic search combined")
    print("    Vector-only: would return ALL "billing" chunks, no priority filtering")
    print("    Graph-only: no semantic relevance ranking")


# ---------------------------------------------------------------------------
# SUMMARY: Why Graph + Vector Together
# ---------------------------------------------------------------------------

def summary():
    print("\n" + "=" * 60)
    print("SUMMARY: Why Graph + Vector Together")
    print("=" * 60)
    print("""
    RushDB solves all 5 pain points in one architecture:

    ┌─────────────────────────────────────────────────────────────┐
    │                    Pure Vector Stores                       │
    ├─────────────────────────────────────────────────────────────┤
    │ ✗ Semantic chunk retrieval only                             │
    │ ✗ No relationship traversal                                  │
    │ ✗ No entity disambiguation across time                       │
    │ ✗ Manual multi-retrieval + join                              │
    │ ✗ No temporal/structural context                             │
    └─────────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────────┐
    │              RushDB: Graph + Vectors                        │
    ├─────────────────────────────────────────────────────────────┤
    │ ✓ Traverse USER → TICKETS → ISSUES → FIXES → RELEASES      │
    │ ✓ Entity nodes know their temporal context (v2.2, v2.3...)   │
    │ ✓ Single graph query for multi-hop traversal                │
    │ ✓ Semantic search + graph WHERE clauses combined            │
    │ ✓ Nodes and edges both support vector embeddings            │
    └─────────────────────────────────────────────────────────────┘
    """)

    print("\nFor customer support agents, this means:")
    print("  • "Alice's billing issues before v2.4" → single query")
    print("  • "Which billing API?" → resolved by graph context")
    print("  • "Full ticket history" → relationship traversal")
    print("  • "Similar high-priority issues" → semantic + graph filter")
    print("\n")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("\n" + "#" * 60)
    print("# 5 RAG Developer Pain Points That Graph Memory Solves")
    print("#" * 60)

    # Run each pain point demonstration
    pain_point_1_entity_traversal()
    pain_point_2_multi_hop_queries()
    pain_point_3_entity_disambiguation()
    pain_point_4_relationship_joins()
    pain_point_5_semantic_graph_hybrid()
    summary()


if __name__ == "__main__":
    main()
