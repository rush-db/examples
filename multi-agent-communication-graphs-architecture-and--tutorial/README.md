# Multi-Agent Communication Graphs: Architecture and Implementation

This project demonstrates how to use RushDB to build and query **multi-agent communication graphs** — a powerful architectural pattern for orchestrating complex AI agent systems.

## What It Demonstrates

- **Graph-based agent architecture**: Agents as nodes, communication channels as edges
- **Hierarchical agent structures**: Coordinator → Specialist agents → Tool agents
- **Message flow tracking**: Recording and querying inter-agent communications
- **Communication pattern analysis**: Finding bottlenecks, tracing message paths
- **Dynamic agent orchestration**: Building and querying agent networks at runtime

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Coordinator Agent                        │
│                         (Orchestrator)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Research   │  │  Coding    │  │  Planning  │
    │   Agent    │  │   Agent    │  │   Agent    │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Web Fetch │  │ Code Execute│  │   Memory   │
    │   Tool     │  │    Tool    │  │   Store    │
    └────────────┘  └────────────┘  └────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account and API key
- `rushdb>=2.0.0` package

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Seed the database** (creates sample agents and communications):
   ```bash
   python seed.py
   ```

## Running the Demo

```bash
python main.py
```

## What You'll See

1. **Agent Network Overview** — Display all agents and their roles
2. **Communication Analysis** — Query message patterns between agents
3. **Hierarchical Queries** — Find all agents subordinate to a coordinator
4. **Path Traversal** — Trace how a message flows through the agent network
5. **Bottleneck Detection** — Identify agents with high communication volume

## Key Concepts

### Labels Used

| Label | Description |
|-------|-------------|
| `AGENT` | AI agent node with metadata (name, role, capabilities) |
| `MESSAGE` | Communication record between agents |
| `CAPABILITY` | Skill or tool capability attached to agents |

### Relationship Types

| Type | Direction | Description |
|------|-----------|-------------|
| `COMMUNICATES_WITH` | Bidirectional | Direct message exchange |
| `COORDINATES` | Out → Sub | Coordinator supervises subordinate |
| `PROVIDES_CAPABILITY` | Out → Cap | Agent provides a capability |
| `REQUESTS_FROM` | Out → Source | Agent requests from another |

## Example Queries

```sdk
# Find all specialists under a coordinator
db.records.find({
    "labels": ["AGENT"],
    "where": {
        "COORDINATOR": {
            "name": "Main Coordinator"
        }
    }
})
___SPLIT___
// Find all specialists under a coordinator
const result = await db.records.find({
  labels: ['AGENT'],
  where: {
    COORDINATOR: {
      name: 'Main Coordinator'
    }
  }
})
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RUSHDB_API_KEY` | Your RushDB API key |
| `RUSHDB_URL` | Custom endpoint (optional, for self-hosted) |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Examples Repository](https://github.com/rush-db/examples)
- [Property Graphs vs Document Stores](https://rushdb.com/docs)
