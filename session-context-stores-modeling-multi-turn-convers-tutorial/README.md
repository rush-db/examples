# Session Context Stores: Modeling Multi-Turn Conversations as Connected Subgraphs

This tutorial demonstrates how to use RushDB's property graph model to store and query
multi-turn conversations as connected subgraphs — enabling efficient context retrieval,
conversation replay, and semantic search across dialogue history.

## What You'll Learn

- How to model conversation sessions with explicit turn relationships
- Using transactions to create complex subgraph structures atomically
- Traversing conversation history via relationship queries
- Context windows: fetching recent turns for any participant
- Semantic search across message content to find relevant conversation segments

## Why Graph Model for Conversations?

Traditional database schemas force conversations into flat tables (session_id, timestamp, 
message) that lose the rich structure of dialogue. RushDB's property graph treats each 
message as a first-class node with typed relationships to:

- Its parent session
- Preceding/following messages
- Author participants
- Referenced entities (documents, tools, external data)

This structure enables queries like:
- "Find all messages in session X where user asked about pricing"
- "Get the last 5 turns for user Y across all their sessions today"
- "Traverse conversation context to understand what led to a specific response"

## Prerequisites

- Python 3.9+
- RushDB account (free tier at https://rushdb.com)
- `pip install rushdb>=2.0.0`

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Seed demo data:**
   ```bash
   python seed.py
   ```
   This creates sample sessions, messages, and participants. Safe to run multiple times —
   checks for existing data before creating new records.

## Running the Demo

```bash
python main.py
```

The script demonstrates:
1. **Session creation** — creating new conversation sessions with metadata
2. **Message threading** — linking messages into turn sequences
3. **Context retrieval** — fetching recent turns for context windows
4. **Conversation traversal** — walking the message graph by relationship type
5. **Semantic search** — finding relevant messages across sessions

## Project Structure

```
├── README.md         # This file
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
├── seed.py           # Generates demo conversation data
└── main.py           # Main demo script
```

## Data Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SESSION (root)                                 │
│   id, title, status, created_at, metadata                                │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │ CONTAINS     │ INITIATED_BY │
              ▼              ▼              ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │   MESSAGE   │   │PARTICIPANT  │   │  CONTEXT    │
    │             │   │             │   │   STORE     │
    │ content     │   │ name        │   │             │
    │ turn        │   │ role        │   │ data        │
    │ timestamp   │   │ metadata    │   │ session_id  │
    └──────┬──────┘   └─────────────┘   └─────────────┘
           │
           │ REPLY_TO, FOLLOWS
           ▼
    ┌─────────────┐
    │   MESSAGE   │
    │   (next)    │
    └─────────────┘
```

Each message can be linked to previous messages (REPLY_TO) and following messages 
(FOLLOWS), creating an ordered chain. Participants are linked via AUTHORED relationships.

## Expected Output

When you run `python main.py` after seeding data, you should see:
- Session list with metadata
- Message chains with turn sequences
- Context windows (last 3 messages per session)
- Semantic search results matching conversation content

---

For SDK documentation, visit: https://docs.rushdb.com
For this tutorial's source: https://github.com/rush-db/examples/tree/main/session-context-stores-modeling-multi-turn-convers-tutorial
