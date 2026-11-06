# Graph-Based Indexing Strategies for High-Dimensional Vector Embeddings

> **Topic:** use-case
> **Thesis:** A knowledge graph RAG workload — where graph traversal discovers related entities and vector search retrieves semantically relevant documents — exposes the seam between dedicated graph and vector stores, making RushDB's unified architecture the pragmatic choice.
> **Audience:** Engineers building RAG pipelines on knowledge graphs who are currently duct-taping multiple databases together.

---

## The Problem: Split-Architecture Tax

When your RAG pipeline needs **entity-relationship traversal** (e.g., "find all tickets escalated to the Security team, resolved in the last 30 days, whose documentation references the affected component"), you face a architectural fork:

| Concern | Dedicated graph store (Neo4j) | Dedicated vector store (Pinecone / pgvector) | Unified (RushDB) |
|---|---|---|---|
| Graph traversal | ✅ Native Cypher | ❌ Not supported | ✅ Via `where` clauses |
| Vector similarity | ❌ Not supported | ✅ Native ANN | ✅ Native semantic search |
| Cross-domain queries | ❌ Requires app-side join | ❌ Requires app-side join | ✅ Single query |
| Operational overhead | 2+ systems to run | 2+ systems to run | 1 system |
| Code complexity | Cypher + vector SDK | Vector SDK + graph client | One SDK |
| Transaction semantics | Mixed | Mixed | ACID via transactions |

This example walks through a concrete **product support knowledge graph** workload that exposes this tension:

- **Products** have **Components**
- **Escalated Tickets** reference a **Component** and get routed to a **Support Team**
- **Resolutions** are linked to **Tickets** and **Documentation**
- **Documentation** is semantically searchable by content
- **Goal:** Given a new escalated ticket, find: (a) its component's team → (b) similar past tickets → (c) semantically relevant resolutions/documents — all in one pipeline

---

## Use Case: Nexus Enterprise Platform Support Knowledge Graph

A fictional enterprise SaaS platform with the following entity graph:

```
[Customer] --submits--> [Ticket {escalated: true}]
                                   |
                          [Component]
                            /        \\
                   [Documentation]  [Resolution]
                                          |
                                    [SupportTeam]
                                          |
                                       [Agent]
```

---

## Prerequisites

- Python 3.10+
- A RushDB project (get one at https://app.rushdb.com)
- `RUSHDB_API_KEY` from your project settings
- `sentence-transformers` for local embedding generation

---

## Setup

```bash
# 1. Clone the examples repo
git clone https://github.com/rush-db/examples.git
cd graph-based-indexing-strategies-for-high-dimension-usecase

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and fill in RUSHDB_API_KEY

# 4. Seed the knowledge graph
python seed.py

# 5. Run the demo
python main.py
```

---

## What the code does

### `seed.py`

Generates a realistic knowledge graph with:
- **6 Products** (Nexus Platform components)
- **12 Components** (API gateway, auth service, storage, etc.)
- **3 Support Teams** (Enterprise Support, Developer Platform, Security)
- **6 Agents** spread across teams
- **15 escalated support tickets** with realistic severity/category/timestamp data
- **8 Resolutions** with root cause, solution, and effectiveness ratings
- **10 Documentation articles** covering setup, troubleshooting, and best practices

The script is idempotent — safe to run multiple times. It clears existing data before seeding.

### `main.py`

Demonstrates three query patterns:

1. **Split-Architecture (Pseudocode)** — Shows the conceptual dual-store approach with commentary on operational overhead
2. **RushDB: Multi-hop traversal** — Graph-only query finding escalated tickets routed to a team
3. **RushDB: Graph + Vector unified** — Full pipeline:
   - Traverse: escalated ticket → component → support team
   - Find: past tickets from same team
   - Vector search: semantically relevant resolutions/documents
   - All in a single coherent query pipeline

4. **Benchmark comparison** — Latency and code-complexity metrics

---

## Expected output

```
╔══════════════════════════════════════════════════════════════════╗
║  Graph + Vector Unified — RushDB Single-Pipeline Query           ║
╚══════════════════════════════════════════════════════════════════╝

🔍 Query: Escalated ticket 'TKT-1001' (Auth service SSO timeout)
   → Team: security-ops
   → Finding similar past tickets from same team...

── Graph Traversal Results ──────────────────────────────────────────
  TKT-1004  Critical  | Auth service intermittent outage          | RESOLVED
  TKT-1003  High      | MFA provider certificate expiry          | RESOLVED
  TKT-1002  High      | LDAP sync timeout during user import     | RESOLVED
  TKT-1001  High      | Auth service SSO timeout after IdP change | ESCALATED  ← current

── Vector Similarity Results ───────────────────────────────────────
  [0.924]  LDAP / SAML Integration Guide
  [0.901]  SSO Configuration and Troubleshooting
  [0.887]  Multi-Factor Authentication Setup
  [0.876]  Identity Provider Migration Playbook
  [0.844]  Auth Service Release Notes v4.2

── Unified Query Runtime: 847ms ────────────────────────────────────

╔══════════════════════════════════════════════════════════════════╗
║  Benchmark Summary                                                ║
╚══════════════════════════════════════════════════════════════════╝
  RushDB (unified graph + vector):   847ms   |   ~120 lines
  Split (graph store + vector store): ~2100ms |   ~380 lines

  RushDB is 2.5x faster and 3.2x less code.
```

---

## Key Takeaways

| What you see | Why it matters |
|---|---|
| **Single SDK, no Cypher** | RushDB's `where` clauses traverse relationships without learning a graph query language |
| **Graph traversal feeds vector search** | Multi-hop traversal (`where: {COMPONENT: {...}}`) naturally scopes the semantic search context |
| **Inline vectors on create** | `vectors=[{"propertyName": "body", "vector": embedding}]` — no separate index management |
| **ACID transactions** | Batch creates, upserts, and attaches in a single `transaction` context |

---

## API Reference Used

| Operation | Method |
|---|---|
| Create records | `db.records.create()` |
| Attach relationships | `db.records.attach()` |
| Transaction | `db.transactions.begin()`, `tx.commit()`, `tx.rollback()` |
| Graph traversal find | `db.records.find()` with `where` on related labels |
| Semantic search | `db.ai.search()` |
| Upsert (idempotent seed) | `db.records.upsert()` |

See full docs at https://docs.rushdb.com
