# 5 RAG Developer Pain Points That Graph Memory Solves

A use-case demonstration for customer support agents that need long-term memory across entities and sessions.

## The Problem

When building conversational AI or support agents, pure vector stores fail at the tasks that matter most:

| Pain Point | What You Want | What Vector-Only Gives You |
|---|---|---|
| **Entity traversal** | "Find user X's history" | Semantic chunks matching "user X" |
| **Multi-hop queries** | "Issues before release v2.3" | Unstructured retrieval |
| **Entity disambiguation** | "Which billing API?" | Fresh chunks, no context |
| **Relationship joins** | "Ticket → User → Issue → Release" | Manual multi-retrieval |
| **Temporal reasoning** | "Resolved before v2.4" | No time awareness |

## The Solution

This example shows how RushDB's graph + vector architecture solves all five problems in a unified query layer.

---

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Copy environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and set RUSHDB_API_KEY
   ```

3. **Seed the database:**
   ```bash
   python seed.py
   ```

   This creates a customer support scenario with:
   - 3 users with support history
   - 6 tickets across 3 software releases
   - 3 issues (billing, auth, search) with fixes
   - Semantic embeddings on ticket descriptions and issue summaries

4. **Run the demo:**
   ```bash
   python main.py
   ```

---

## What Each Script Demonstrates

### seed.py — Building the Graph

Creates the property graph with typed nodes and relationships:

```
USER ──submitted──▶ TICKET ──references──▶ ISSUE
                                           │
                                           ▼
                                         RELEASE ◀──fixed_in── FIX

USER ──has_session──▶ SESSION
```

Each node carries:
- **Graph edges** for relationship traversal
- **Vector embeddings** on `description` and `summary` fields for semantic search

### main.py — The 5 Pain Points in Action

| # | Pain Point | Demo Query |
|---|---|---|
| 1 | Entity traversal | "Find all tickets from user alice@example.com" |
| 2 | Multi-hop graph query | "Issues reported before v2.4, with their fixes" |
| 3 | Entity disambiguation | "Which billing API?" (v2.2 vs v2.3 context) |
| 4 | Relationship joins | "Ticket → User → Issue → Release in one query" |
| 5 | Temporal + semantic | "High-priority tickets mentioning billing" |

---

## Expected Output

```
=== PAIN POINT 1: Entity Traversal ===
Finding tickets from alice@example.com via graph traversal...
[Graph] Found 2 tickets in 1 query
  - Ticket T001: "Payment failed"
  - Ticket T002: "Invoice mismatch"

=== PAIN POINT 2: Multi-hop Graph Query ===
Finding issues before release v2.4 and their fixes...
[Graph] Found 3 issues in 1 query with relationship chain
  - Billing issue → Fixed in v2.3
  - Auth issue → Fixed in v2.4

=== PAIN POINT 3: Entity Disambiguation ===
Context-aware entity resolution...
[Graph] "billing API" in v2.2 = BillingAPI_v1 (payment processing)
[Graph] "billing API" in v2.3 = BillingAPI_v2 (invoice handling)

=== PAIN POINT 4: Relationship Joins ===
Ticket → User → Issue → Release in one query...
[Graph] Retrieved full chain in 1 query

=== PAIN POINT 5: Semantic + Graph Hybrid ===
High-priority tickets mentioning "billing"...
[Graph] Found 2 tickets using semantic search + status filter
```

---

## How This Compares to Pure Vector Stores

### ChromaDB / Pinecone alone:

```python
# Cannot do: "Find user X's tickets before release Y"
# Must do: 1. Search "user X" → 2. Filter results → 3. Join manually

# Cannot do: "Which billing API?" (needs graph context)
# Gets: Fresh chunks matching "billing API" without knowing WHICH
```

### With RushDB:

```python
# Single query: USER → tickets → issues → release → fix
db.records.find({
    "labels": ["TICKET"],
    "where": {
        "USER": {"$relation": {"type": "SUBMITTED", "direction": "in"}},
        "email": "alice@example.com"
    }
})
```

---

## Running on Self-Hosted RushDB

```bash
# In .env:
RUSHDB_API_KEY=your-api-key
RUSHDB_URL=https://your-host.com/api/v1
```

See [RushDB docs](https://docs.rushdb.com) for self-hosted setup.

---

## Files

```
├── README.md          # This file
├── requirements.txt   # pip dependencies
├── .env.example       # Environment template
├── seed.py            # Create mock support scenario
└── main.py            # Demonstrate the 5 pain points
```
