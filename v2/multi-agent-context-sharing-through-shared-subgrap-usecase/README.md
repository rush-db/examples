# Multi-Agent Context Sharing Through Shared Subgraph References

> **Problem**: Multi-agent LLM pipelines suffer from token overhead and state inconsistency when passing full context to every agent in the chain.
> 
> **Solution**: RushDB's graph-based shared subgraph references let agents read/write to their local graph slice without duplicating context.

## The Core Problem

In a typical multi-agent pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│  NAIVE APPROACH: Full Context Injection                         │
│                                                                 │
│  User Request                                                    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────┐   "Here is user John, 42 years old, premium tier,   │
│  │ Triage  │    has 12 orders, 3 pending, prefers express ship,  │
│  │ Agent   │    current session started 5min ago..."            │
│  └────┬────┘       │                                             │
│       │            │ (full context, ~800 tokens)                │
│       ▼            ▼                                             │
│  ┌─────────┐   "Here is user John, 42 years old, premium tier... │
│  │ Routing │    previous agent determined intent: RETURN_REQUEST │
│  │ Agent   │    full context again..."                           │
│  └────┬────┘       │                                             │
│       │            ▼                                             │
│       ▼      "Here is user John, 42 years old..."                │
│  ┌─────────┐                                                     │
│  │Fulfillment│   (3x the tokens, context drift risk)            │
│  │ Agent    │                                                    │
│  └─────────┘                                                     │
└─────────────────────────────────────────────────────────────────┘
```

With a 128k token context window and 3 agents, you're burning **2,400+ tokens per request** just on context — before the actual task.

## The Solution: Shared Subgraph References

```
┌─────────────────────────────────────────────────────────────────┐
│  SHARED SUBGRAPH APPROACH                                        │
│                                                                 │
│           ┌─────────────────────────────────────┐              │
│           │   USER CONTEXT SUBGRAPH (Neo4j)     │              │
│           │                                     │              │
│           │  [USER:John]────[PREFERENCES]       │              │
│           │      │              │               │              │
│           │      └────[ORDERS]───┘               │              │
│           │      │                               │              │
│           │      └──[SESSION]                    │              │
│           └──────────────┬──────────────────────┘              │
│                          │ (query once, share reference)        │
│       ┌──────────────────┼──────────────────┐                   │
│       ▼                  ▼                  ▼                   │
│  ┌─────────┐       ┌─────────┐       ┌─────────┐              │
│  │ Triage  │       │ Routing │       │Fulfillmt│              │
│  │ Agent   │       │ Agent   │       │ Agent   │              │
│  │         │       │         │       │         │              │
│  │ Reads:  │       │ Reads:  │       │ Reads:  │              │
│  │ SESSION │       │ intent  │       │ ORDER+  │              │
│  │ Updates:│       │ Writes: │       │ PREFS   │              │
│  │ intent  │       │ route   │       │ Writes: │              │
│  │         │       │         │       │ result  │              │
│  └─────────┘       └─────────┘       └─────────┘              │
│                                                                 │
│  Token cost: ~150 tokens/query vs 800 tokens/prompt            │
└─────────────────────────────────────────────────────────────────┘
```

## What is a "Shared Subgraph" in RushDB?

A **shared subgraph** is a connected set of RushDB records (nodes) and relationships (edges) that multiple agents can:

1. **Read** — Query specific slices without loading the entire context
2. **Write** — Update their slice with results, decisions, or state
3. **Reference** — Pass subgraph IDs instead of full payloads between agents

### Graph Structure

```
┌──────────────┐      has_preferences       ┌──────────────┐
│    USER      │ ◄────────────────────────► │  PREFERENCES │
│  ──────────  │                            │  ──────────  │
│  id: john_1  │                            │  shipping:   │
│  name: John  │         placed             │    express  │
│  age: 42     │ ◄───────┐                 │  language:  │
│  tier: pro   │         │    belongs_to   │    en-US    │
└──────┬───────┘         │         ┌───────┴──┴──────────┘
       │                 │         │
       │         ┌───────┴─────────┘
       │         │
       │         ▼
       │    ┌──────────┐
       │    │  ORDER   │
       │    │  ──────  │
       │    │  id: ... │
       │    │  total:  │
       │    │    149.99│
       │    │  status: │
       │    │  shipped │
       │    └────┬─────┘
       │         │
       │         ▼
       │    ┌──────────┐
       │    │ SESSION  │
       │    │  ──────  │
       │    │  started │
       │    │  intent: │
       │    │  pending │
       │    │  agent:  │
       │    │  triage  │
       │    └──────────┘
       │
       └──────────────────► [AGENT_RECORDS] (per-agent slices)
```

## Token & Latency Comparison

| Metric | Naive Context Injection | Shared Subgraph |
|--------|------------------------|-----------------|
| Tokens per agent call | ~800 (full context) | ~150 (query) |
| 3-agent pipeline total | ~2,400 tokens | ~450 tokens |
| Token reduction | — | **83%** |
| State consistency | Risk of drift | Single source of truth |
| Per-agent isolation | None | Agents see only their slice |
| Latency (read) | N/A | ~50-200ms per query |

## Prerequisites

- Python 3.9+
- RushDB account ([sign up free](https://rushdb.com))
- `RUSHDB_API_KEY` from your RushDB project

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/rush-db/examples.git
cd multi-agent-context-sharing-through-shared-subgrap-usecase

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY

# 5. Seed mock data (optional — main.py checks and skips if data exists)
python seed.py
```

## Running the Demo

```bash
python main.py
```

The script will:

1. **Initialize** — Connect to RushDB and verify the subgraph structure
2. **Run naive simulation** — Show token costs of context injection
3. **Create shared subgraph** — Build the user context subgraph in RushDB
4. **Execute multi-agent pipeline** —
   - Triage Agent reads SESSION, determines user intent
   - Routing Agent reads intent, selects fulfillment path
   - Fulfillment Agent reads ORDER + PREFERENCES, executes
5. **Compare results** — Token counts, latency, state consistency metrics

## Project Structure

```
multi-agent-context-sharing-through-shared-subgrap-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Mock data generator (users, orders, sessions)
├── main.py             # Main demonstration script
└── data/
    └── sample_users.json  # Sample user data for seeding
```

## Key Code Patterns

### Creating a Shared Subgraph

```sdk
# Create user context subgraph with relationships
with db.transactions.begin() as tx:
    # User node
    user = db.records.create(
        label="USER",
        data={"name": "John Doe", "tier": "premium", "email": "john@example.com"},
        transaction=tx
    )
    
    # Preferences linked to user
    prefs = db.records.create(
        label="PREFERENCES",
        data={"shipping": "express", "language": "en-US", "notifications": True},
        transaction=tx
    )
    
    # Session for current interaction
    session = db.records.create(
        label="SESSION",
        data={"started_at": "2024-01-15T10:30:00Z", "agent": "triage"},
        transaction=tx
    )
    
    # Link them together
    db.records.attach(source=user, target=prefs, options={"type": "HAS_PREFERENCES"}, transaction=tx)
    db.records.attach(source=user, target=session, options={"type": "HAS_SESSION"}, transaction=tx)
___SPLIT___
// TypeScript
const tx = await db.transactions.begin()
try {
  // User node
  const user = await db.records.create({
    label: 'USER',
    data: { name: 'John Doe', tier: 'premium', email: 'john@example.com' }
  }, tx)
  
  // Preferences linked to user
  const prefs = await db.records.create({
    label: 'PREFERENCES',
    data: { shipping: 'express', language: 'en-US', notifications: true }
  }, tx)
  
  // Session for current interaction
  const session = await db.records.create({
    label: 'SESSION',
    data: { startedAt: '2024-01-15T10:30:00Z', agent: 'triage' }
  }, tx)
  
  // Link them together
  await db.records.attach({ source: user, target: prefs, options: { type: 'HAS_PREFERENCES' } }, tx)
  await db.records.attach({ source: user, target: session, options: { type: 'HAS_SESSION' } }, tx)
  
  await tx.commit()
} catch (e) {
  await tx.rollback()
  throw e
}
```

### Agent Reading Its Slice

```sdk
# Triage Agent: Read only the session slice
session = db.records.find({
    "labels": ["SESSION"],
    "where": {"status": "active", "user_id": user_id},
    "orderBy": {"started_at": "desc"},
    "limit": 1
}).data[0]

# Routing Agent: Read the intent field only
intent = session.get("intent", "unknown")

# Fulfillment Agent: Read orders for this user
orders = db.records.find({
    "labels": ["ORDER"],
    "where": {"USER": {"id": user_id}}
})
___SPLIT___
// TypeScript
// Triage Agent: Read only the session slice
const { data: sessions } = await db.records.find({
  labels: ['SESSION'],
  where: { status: 'active', userId: userId },
  orderBy: { startedAt: 'desc' },
  limit: 1
})
const session = sessions[0]

// Routing Agent: Read the intent field only
const intent = session?.get('intent') ?? 'unknown'

// Fulfillment Agent: Read orders for this user
const { data: orders } = await db.records.find({
  labels: ['ORDER'],
  where: { userId: userId }
})
```

### Agent Writing to Its Slice

```sdk
# Triage Agent: Update session with determined intent
db.records.update(
    record_id=session.id,
    data={"intent": "return_request", "confidence": 0.94}
)

# Fulfillment Agent: Create result record linked to session
result = db.records.create(
    label="RESULT",
    data={"type": "return_label_sent", "order_id": order_id, "agent": "fulfillment"}
)
db.records.attach(source=session, target=result, options={"type": "PRODUCED"})
___SPLIT___
// TypeScript
// Triage Agent: Update session with determined intent
await db.records.update({
  recordId: session.id,
  data: { intent: 'return_request', confidence: 0.94 }
})

// Fulfillment Agent: Create result record linked to session
const result = await db.records.create({
  label: 'RESULT',
  data: { type: 'return_label_sent', orderId: orderId, agent: 'fulfillment' }
})
await db.records.attach({ source: session, target: result, options: { type: 'PRODUCED' } })
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Concepts](https://docs.rushdb.com/concepts/property-graph)
- [Multi-Agent Architectures](https://docs.rushdb.com/use-cases/ai-agents)

## License

MIT — see [LICENSE](../LICENSE) in the root of the repository.