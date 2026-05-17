# Cross-Agent Knowledge Synchronization Protocols

A practical tutorial demonstrating how to use RushDB as a **knowledge synchronization layer** for multi-agent AI systems.

## What This Tutorial Covers

This project demonstrates core patterns for synchronizing knowledge across multiple AI agents using RushDB's property graph model:

1. **Agent Identity Registry** — Each agent has a unique identity record
2. **Knowledge Contexts** — Shared knowledge bases with provenance tracking
3. **Sync Protocol Patterns**:
   - Pull-based synchronization
   - Push-based synchronization  
   - Bidirectional merge synchronization
4. **Conflict Detection & Resolution** — Handle competing updates from multiple agents
5. **Transactional Consistency** — Atomic multi-agent knowledge updates
6. **Semantic Search** — Cross-agent knowledge discovery via vector similarity

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    RushDB Knowledge Graph                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    KNOWS     ┌──────────────┐                │
│  │ Agent:Alice  │◄────────────►│ Agent:Bob    │                │
│  └──────┬───────┘              └──────┬───────┘                │
│         │ CONTRIBUTED                 │ CONTRIBUTED            │
│         ▼                             ▼                        │
│  ┌──────────────────────────────────────────────┐               │
│  │          Knowledge: "ML Pipeline Design"     │               │
│  │          SYNCED_FROM: [Alice, Bob]           │               │
│  │          version: 3, lastSync: 2024-01-15   │               │
│  └──────────────────────────────────────────────┘               │
│         ▲ SYNC_BELONGS_TO                                     │
│         │                                                      │
│  ┌──────┴───────┐                                             │
│  │ SyncEvent   │  ← Tracks every cross-agent sync             │
│  │ timestamp   │                                             │
│  │ participants│                                             │
│  └─────────────┘                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account (free tier works)
- `rushdb>=2.0.0` Python SDK

## Setup

1. **Clone and install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Get your RushDB API key**:
   - Sign up at https://app.rushdb.com
   - Create a project
   - Copy the API key to `.env`

4. **Seed the database (optional)**:
   ```bash
   python seed.py
   ```
   This creates sample agents, knowledge bases, and sync events. Safe to run multiple times.

## How to Run

```bash
python main.py
```

The demo runs through all sync protocol patterns:

### 1. Agent Registration
Creates unique agent identity records with metadata.

### 2. Knowledge Context Creation
Establish shared knowledge bases that multiple agents can access.

### 3. Pull Synchronization
Agent pulls latest knowledge from a shared context.

### 4. Push Synchronization
Agent pushes its local knowledge to a shared context.

### 5. Bidirectional Merge
Two agents sync their knowledge with conflict detection.

### 6. Conflict Resolution
Demonstrates two resolution strategies:
- Last-write-wins (timestamp-based)
- Merge-by-version (version vector comparison)

### 7. Semantic Search
Cross-agent knowledge discovery using vector similarity.

## Expected Output

```
=== Cross-Agent Knowledge Sync Protocol Demo ===

[1/7] Agent Registry Setup
✅ Created 3 agent records
   - Agent:Synthesis-Alpha
   - Agent:Analysis-Beta  
   - Agent:Coordination-Gamma

[2/7] Knowledge Context Initialization
✅ Created shared knowledge context: 'ml-pipeline-design'
   Contributors: 2 agents

[3/7] Pull Synchronization
✅ Agent 'Synthesis-Alpha' pulled 3 knowledge items
   Latest: "Distributed Training Architecture"

[4/7] Push Synchronization  
✅ Agent 'Analysis-Beta' pushed 2 knowledge items
   Conflict check: 0 conflicts detected

[5/7] Bidirectional Merge Sync
✅ Sync event 'merge-001' completed
   Items synced: 5 | Conflicts resolved: 0

[6/7] Conflict Resolution Demo
✅ Conflict detected: 'feature-x-status'
   Resolution: LAST_WRITE_WINS (Agent:Coordination-Gamma wins)
   Final value: 'production-ready'

[7/7] Cross-Agent Semantic Search
✅ Found 4 semantically related knowledge items
   Top match: "Vector Database Integration" (similarity: 0.94)
```

## Key Patterns Explained

### Relationship Model for Sync

Each sync event creates a mini-graph:

```
AGENT ──CONTRIBUTED──► KNOWLEDGE_ITEM
   │                        ▲
   └──SYNCED──► SYNC_EVENT──┘
```

### Version Vector for Conflict Detection

```python
knowledge_item.version = {
    "Synthesis-Alpha": 3,
    "Analysis-Beta": 2,
    "Coordination-Gamma": 1
}
```

When an agent's local version differs from the shared version, a potential conflict exists.

## Pricing Note

RushDB charges by **KnowledgeUnits (KU)** for writes. Reads and queries are free.

This demo creates:
- ~20 records (agents, knowledge, sync events)
- ~5 vector embeddings (for semantic search)
- Total: ~25-30 KU per full run

See https://rushdb.com/pricing for details.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [Property Graph Concepts](https://docs.rushdb.com/concepts)
- [Vector Search Guide](https://docs.rushdb.com/features/vector-search)
