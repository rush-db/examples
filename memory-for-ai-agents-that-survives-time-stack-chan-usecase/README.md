# Memory for AI Agents That Survives Time, Stack Changes & Restarts

> **What this project demonstrates:** How to build a persistent memory layer for AI agents using RushDB — combining graph traversal for entity relationships with vector search for semantic recall, all in a single store.

## The Problem with Stateless Agents

Most AI agent frameworks treat memory as ephemeral — stored in RAM, lost on restart, isolated per service instance. When your agent restarts or your microservice scales horizontally, it forgets everything.

**True persistent memory for agents means:**
- **Learned entity relationships** — who is this user? what do they care about?
- **Accumulated context** — what has this agent done for them before?
- **Goal state** — what is this user trying to achieve?
- **Semantic recall** — has this agent encountered a similar situation before?

## Why RushDB?

Traditional stacks require stitching together:
- **Redis** — for caching, loses data on restart (unless persisted)
- **Vector DB** — for semantic search, no relationship model
- **Graph DB** — for entity relationships, no vector support

RushDB provides **both primitives in a single store** — eliminating dual-database overhead and schema synchronization nightmares.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent                               │
├─────────────────────────────────────────────────────────────┤
│  Memory Layer                                               │
│  ┌──────────────────┐  ┌─────────────────────────────────┐  │
│  │  Graph Queries   │  │      Vector Search              │  │
│  │  (entity graph)  │  │      (semantic recall)           │  │
│  └────────┬─────────┘  └────────────────┬────────────────┘  │
│           │                              │                   │
│           └──────────────┬───────────────┘                   │
│                          ▼                                    │
│                   ┌─────────────┐                              │
│                   │   RushDB    │                              │
│                   │  (Neo4j)    │                              │
│                   └─────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

## What This Demo Shows

1. **Define persistent memory** — structured records for users, tasks, goals, and past interactions
2. **Entity tracking via graph** — "Who is this user? What are their pending tasks?"
3. **Semantic recall via vectors** — "Find similar past situations to this query"
4. **Restart survival** — Query memory immediately after "restart" with no warmup
5. **Latency comparison** — Measure combined graph + vector queries vs. dual-store overhead

## Prerequisites

- Python 3.9+
- A RushDB account ([get free API key](https://rushdb.com))
- `sentence-transformers` for embeddings (local, no OpenAI required)

## Setup

```bash
# Clone the examples repo
git clone https://github.com/rush-db/examples.git
cd memory-for-ai-agents-that-survives-time-stack-chan-usecase

# Create virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Demo

### Step 1: Seed the memory store (optional — demo runs with or without seed)

```bash
python seed.py
```

This creates sample memory data:
- 3 users with profiles and preferences
- 10 tasks with status and priority
- 5 goals per user with progress tracking
- 20 past interactions with embedded descriptions

### Step 2: Run the main demonstration

```bash
python main.py
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║           RUSHDEMO: Persistent Memory for AI Agents                         ║
║           Surviving time, restarts, and stack changes                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. AGENT MEMORY STATE AFTER SIMULATED RESTART
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Agent cold-started. Loading memory from RushDB...
  ✓ Loaded 3 users
  ✓ Loaded 10 tasks
  ✓ Loaded 15 goals
  ✓ Loaded 20 past interactions
  ✓ Vector index ready: 20 interactions indexed

Agent is fully operational with full context. No warmup needed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. ENTITY TRACKING VIA GRAPH QUERIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query: Who is alice@example.com and what does she need?
  → User: Alice Chen (alice@example.com)
    - Role: Product Manager
    - Preferences: detailed specs, timeline estimates
    - Open Tasks: 3
    - Active Goals: 2
    - Past Interactions: 7

Graph traversal completed in 23ms

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. SEMANTIC RECALL VIA VECTOR SEARCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query: "user having trouble with checkout payment"
  → Similar past situations found:
    [0.94] "Customer reported checkout failing after updating payment method"
    [0.89] "User couldn't complete purchase due to expired card"
    [0.85] "Checkout timeout issue on mobile devices"

Vector search completed in 47ms

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. COMBINED GRAPH + VECTOR QUERY (Single Store)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query: User alice@example.com had a payment issue — find similar past cases
  → Graph query (find user): 12ms
  → Graph query (find interactions): 18ms
  → Vector search (semantic match): 44ms
  → Total: 74ms (single database connection)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. LAYERED MEMORY: GOAL STATE TRACKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

alice@example.com's active goals:
  1. "Q1 Product Launch" [████░░░░░░] 40% - pending: final review, marketing materials
  2. "User Research Analysis" [██████░░░░] 60% - pending: synthesis report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. FRAMEWORK-AGNOSTIC VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The memory graph structure is framework-agnostic:
  - Records: {__id, __label, ...fields}
  - Relationships: typed, directed edges
  - Labels: USER, TASK, GOAL, INTERACTION
  - All queryable via RushDB REST API directly

  Sample record structure:
  {
    "__id": "rec_abc123",
    "__label": "USER",
    "name": "Alice Chen",
    "email": "alice@example.com",
    "role": "product_manager"
  }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Persistent memory survives application restarts
✓ Graph queries: entity relationships in <25ms
✓ Vector search: semantic recall in <50ms
✓ Combined operations: single connection, single latency hit
✓ Memory is stack-agnostic: query via Python SDK, REST API, or future SDKs

RushDB eliminates the need for Redis + Vector DB + Graph DB stitched together.
One store, full memory layer.

Learn more: https://docs.rushdb.com
```

## Project Structure

```
memory-for-ai-agents-that-survives-time-stack-chan-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Generate sample memory data
└── main.py             # Main demonstration
```

## How It Works

### Memory Model

The agent's memory is stored as a **property graph** in RushDB:

```
┌─────────┐          ┌─────────┐          ┌─────────────┐
│  USER   │──────────│  TASK   │          │    GOAL     │
│ Alice   │  ASSIGNED│ Bug #42 │          │ Q1 Launch   │
└─────────┘          └─────────┘          └─────────────┘
     │                    │                      │
     │                    │                      │
     ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────┐
│                    INTERACTION                           │
│ "Customer reported checkout failing"                    │
│ [embedded_vector: 0.94 similarity to new query]         │
└─────────────────────────────────────────────────────────┘
```

### Code Pattern

```sdk
# Create user with memory
user = db.records.create(
    label="USER",
    data={"name": "Alice", "email": "alice@example.com", "role": "pm"}
)

# Attach task (relationship)
db.records.attach(source=user, target=task, options={"type": "ASSIGNED"})

# Store interaction with vector
interaction = db.records.create(
    label="INTERACTION",
    data={"description": "User had checkout payment issue", "resolution": "Updated payment method"},
    vectors=[{"propertyName": "description", "vector": embedding}]
)

# Query by entity relationship
alice_tasks = db.records.find({
    "labels": ["TASK"],
    "where": {"USER": {"email": "alice@example.com"}}
})

# Semantic recall
similar = db.ai.search({
    "propertyName": "description",
    "query": "payment issues",
    "labels": ["INTERACTION"],
    "limit": 5
})
___SPLIT___
// Create user with memory
const user = await db.records.create({
    label: 'USER',
    data: { name: 'Alice', email: 'alice@example.com', role: 'pm' }
})

// Attach task (relationship)
await db.records.attach({
    source: user,
    target: task,
    options: { type: 'ASSIGNED' }
})

// Query by entity relationship
const aliceTasks = await db.records.find({
    labels: ['TASK'],
    where: { USER: { email: 'alice@example.com' } }
})

// Semantic recall
const similar = await db.ai.search({
    propertyName: 'description',
    query: 'payment issues',
    labels: ['INTERACTION'],
    limit: 5
})
```

## Key Takeaways

| Feature | Without RushDB | With RushDB |
|---------|---------------|-------------|
| Entity relationships | Graph DB | Native |
| Semantic recall | Vector DB | Native |
| Schema management | Manual sync | Zero-schema |
| Query latency | 2 round-trips | 1 connection |
| Stack portability | DB-specific queries | Framework-agnostic |

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdk/python)
- [RushDB GitHub](https://github.com/rush-db/examples)
