# Building Real-Time Context Windows with Persistent Graph Memory

**Project:** `building-real-time-context-windows-with-persistent-usecase`  
**GitHub:** https://github.com/rush-db/examples/tree/main/building-real-time-context-windows-with-persistent-usecase  
**Docs:** https://docs.rushdb.com

---

## What This Demonstrates

A multi-session AI agent memory system where RushDB's property-graph + vector combination tracks:

- **User preferences** — stored as graph edges with weighted strengths
- **Conversation history** — nodes per session, linked by temporal edges
- **Entity relationships** — people, topics, and objects mentioned across sessions
- **Exact context retrieval** — graph traversal narrows the search space, vector ranking picks the right memory

The result: no summarization, no hallucination risk from compressed memory — every context window is a live subgraph pulled fresh from storage.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       User (node)                           │
│   ──HAS_SESSION──► Session ──CONTAINS──► Message            │
│   ──PREFERS──────► Preference                                │
│   ──MENTIONED────► Entity                                    │
│                          │                                  │
│         ┌─────────────────┼──────────────────┐              │
│         ▼                 ▼                  ▼              │
│   mentioned_in      mentioned_in       mentioned_in         │
│   Session A         Session B          Session C            │
│         │                 │                  │              │
│         └────────┬─────────┴──────────────────┘              │
│                  ▼                                          │
│         Graph Traversal narrows session scope               │
│                  │                                          │
│                  ▼                                          │
│         Vector search within subgraph                       │
│         → ranked by semantic relevance                      │
│                  │                                          │
│                  ▼                                          │
│         Context Window (injected into prompt)               │
└─────────────────────────────────────────────────────────────┘
```

### Labels

| Label       | Purpose                                            |
| ----------- | -------------------------------------------------- |
| `USER`      | Persistent user identity                           |
| `SESSION`   | A conversation thread / interaction window          |
| `MESSAGE`   | A single turn (user or agent)                      |
| `ENTITY`    | A person, topic, product, or object                |
| `PREFERENCE`| A user preference edge with a confidence score     |

### Relationships

| Type               | From → To           | Meaning                                          |
| ------------------ | ------------------- | ------------------------------------------------ |
| `HAS_SESSION`      | USER → SESSION      | User opened a session                            |
| `CONTAINS`         | SESSION → MESSAGE   | Message belongs to this session                  |
| `AUTHORED`         | USER → MESSAGE      | User (not agent) wrote this message             |
| `MENTIONED_IN`     | ENTITY → SESSION    | Entity was referenced in this session            |
| `PREFERS_X_OVER_Y` | USER → PREFERENCE   | Explicit preference (stores `prefers` JSON)      |
| `RELATED_TO`       | ENTITY → ENTITY     | Entities are semantically linked                 |
| `REFERENCES`       | MESSAGE → ENTITY    | Message directly references this entity          |

---

## Setup

### Prerequisites

- Python 3.10+
- A RushDB project with an API key
  - Cloud: sign up at https://app.rushdb.com
  - Self-hosted: set `RUSHDB_URL` accordingly

### Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set RUSHDB_API_KEY
```

### Seed the mock data

```bash
python seed.py
```

The seed script creates:

- 1 user (`Alice Chen`)
- 3 sessions across different dates
- ~15 messages mixing user and agent turns
- 6 entities (2 people, 2 topics, 2 products)
- 4 preference relationships
- All messages vectorized for semantic search

Safe to re-run — checks for existing data before writing.

### Run the demo

```bash
python main.py
```

---

## Expected Output

```
=== Session 1: New user arrives ===
No prior memory found for Alice Chen
  → Cold start: no context window needed

=== Session 2: Returning user ===
Context window for Alice Chen:
──────────────────────────────────────
Alice's preferences:
  • prefers React over Angular
  • prefers dark mode over light mode

Recent sessions:
  • 2024-11-20: TypeScript project setup
  • 2024-11-18: VSCode extension research

Relevant memories (semantic):
  • [0.94] "I want to use React for the frontend"
  • [0.87] "Can you help me set up a TypeScript project"

Context window ready for injection:
──────────────────────────────────────
[SYSTEM] You are helping Alice Chen.
  Known preferences: prefers React over Angular.
  Recent work: TypeScript project setup (2024-11-20).
  Relevant memory: Alice mentioned wanting to use React for the frontend.

[USER] How do I structure a React component?
──────────────────────────────────────

=== Session 3: Preferences updated ===
Preference updated: prefers Tailwind over plain CSS (confidence: 0.9)

Context window now reflects updated preferences:
  • prefers React over Angular
  • prefers Tailwind over plain CSS [NEW]
```

---

## How the Context Window Is Built

### Step 1 — Graph traversal narrows scope

```sdk
# Find all sessions for this user, newest first
sessions = db.records.find({
    "labels": ["SESSION"],
    "where": {"USER": {"email": "alice@example.com"}},
    "orderBy": {"startedAt": "desc"},
    "limit": 5
})
```

### Step 2 — Vector search within the subgraph

```sdk
# Semantic search scoped to those sessions
results = db.ai.search({
    "propertyName": "content",
    "query": "React component structure",
    "labels": ["MESSAGE"],
    "where": {
        "SESSION": {"$id": {"$in": [s.id for s in sessions]}}
    },
    "limit": 3
})
```

### Step 3 — Context is assembled, never summarized

```python
context = {
    "user": user,
    "preferences": preferences,
    "sessions": sessions,
    "top_memories": results
}
```

No LLM summarization step — the full subgraph is injected verbatim into the prompt.

---

## Key Design Decisions

### Why store as graph events, not chat logs?

A flat chat log stores *what* was said. Graph events store *what happened* — relationships, entities, and state changes. This means the system can traverse "all sessions where product X was mentioned by users who prefer Y" without scanning every message.

### Why not just vector search?

Vector search alone is a flat retrieval surface. Without graph traversal, you can't answer "retrieve memories from users who share this preference" or "find sessions where entity A and entity B both appeared". The graph narrows the search space before vector ranking runs.

### Why no summarization?

Summarization is a lossy compression step that introduces hallucination risk — the LLM re-phrases memories and can shift meaning. This approach stores *events* (not compressed versions of events) and reconstructs the context window at query time from the actual stored data.
