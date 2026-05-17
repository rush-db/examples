# Edge Embeddings: Representing Relationship Semantics in RushDB

## What This Demo Shows

This project demonstrates why **typed edges with embeddings** outperform node-centric approaches for multi-agent reasoning in AI memory systems.

We build a working agent memory layer for a code review scenario with three query patterns that reveal the power of edge embeddings—and why they break in pure vector databases like Pinecone, Weaviate, and Qdrant.

## The Problem: Node-Centric Memory is Wrong for Agents

Agents don't just recall facts—they reason about *relationships between things*:

- "Who approved this without security review?"
- "Find approval decisions that look like shortcuts"
- "Which agents cluster around careful, thorough reviews?"

These queries operate on **edges**, not nodes. A vector DB with node-only embeddings can't express "this approval was casual" as a semantic concept attached to a relationship.

## Data Model

```
AGENT ──APPROVED──► PR
AGENT ──REVIEWED──► PR
AGENT ──FLAGGED───► PR
```

Each edge carries:
- `reason`: natural language describing the decision (embedded for semantic search)
- `securityReviewed`: boolean flag (filterable)
- `timestamp`: when the review occurred

The edge's semantic embedding captures the *nature* of the relationship, not just its endpoints.

## Prerequisites

- Python 3.10+
- RushDB account (https://app.rushdb.com)
- `sentence-transformers` for generating embeddings

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Run

```bash
# Seed data (idempotent — safe to run twice)
python seed.py

# Run all three query demonstrations
python main.py
```

## Expected Output

```
╔═══════════════════════════════════════════════════════════════════╗
║  QUERY 1: Structured Traversal — Typed Edges                      ║
╠═══════════════════════════════════════════════════════════════════╣
║  Finding PRs approved without security review...
║                                                                     ║
║  ✓ PR: "Add user authentication module"                             ║
║    Agent: Alice Chen  |  Reason: "Quick pass, seemed fine"         ║
║    Security Reviewed: NO ⚠️                                         ║
║                                                                     ║
║  ✓ PR: "Fix pagination bug"                                        ║
║    Agent: Bob Martinez  |  Reason: "Looks okay, good enough"       ║
║    Security Reviewed: NO ⚠️                                         ║
╚═══════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════╗
║  QUERY 2: Semantic Edge Search — Edge Embeddings                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  Finding edges semantically similar to:                            ║
║  "informal approval without thorough review"                       ║
║                                                                     ║
║  Match (0.94): Bob → PR-102 APPROVED                                ║
║    Reason: "Looks fine to me, passing along"                       ║
║                                                                     ║
║  Match (0.91): Alice → PR-101 APPROVED                              ║
║    Reason: "Quick pass, seemed fine"                                ║
╚═══════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════╗
║  QUERY 3: Combined Graph + Vector — Embedding Space Clusters       ║
╠═══════════════════════════════════════════════════════════════════╣
║  Finding agents whose approvals cluster near "careful, thorough"  ║
║                                                                     ║
║  Top Agent: Carol Davis  (avg similarity: 0.89)                     ║
║    All approvals near careful/thorough cluster:                    ║
║    • PR-102: 0.91 | PR-103: 0.87 | PR-104: 0.88                    ║
╚═══════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════╗
║  WHY OTHER SYSTEMS FAIL                                            ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  🔴 PINECONE: No Edge Embeddings                                    ║
║     Can only store node vectors. "Who approved without security    ║
║     review?" requires scanning every node for metadata, then       ║
║     filtering. No native edge semantic search.                     ║
║                                                                     ║
║  🔴 WEAVIATE: Cross-References Without Native Edge Embeddings       ║
║     Relationships exist as references, but edge properties aren't  ║
║     first-class vector citizens. You can filter by properties but  ║
║     not semantically search the relationship itself.              ║
║                                                                     ║
║  🔴 QDRANT: Payload Filters ≠ Edge Semantics                       ║
║     Stores vectors with metadata payloads. "Informal approval"     ║
║     must be encoded in node metadata, not as the relationship's    ║
║     semantic fingerprint. Can't represent edge semantics directly.║
║                                                                     ║
║  ✅ RUSHDB: First-Class Edge Embeddings                             ║
║     Relationships have their own semantic vectors. Queries like    ║
║     "find edges similar to X" or "traverse only APPROVED edges     ║
║     near cluster Y" are native operations.                          ║
╚═══════════════════════════════════════════════════════════════════╝
```

## Project Structure

```
edge-embeddings-representing-relationship-semantic-usecase/
├── README.md         # This file
├── requirements.txt  # Python dependencies
├── .env.example      # Environment template
├── seed.py          # Generates mock data (idempotent)
└── main.py          # Runs all three query demonstrations
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Model](https://docs.rushdb.com/concepts/property-graph)
- [Semantic Search](https://docs.rushdb.com/features/semantic-search)
- [Transactions & Relationships](https://docs.rushdb.com/features/transactions)
