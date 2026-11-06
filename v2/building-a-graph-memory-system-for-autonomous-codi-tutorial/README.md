# Building a Graph-Memory System for Autonomous Coding Agents

A complete, runnable implementation demonstrating how to build persistent memory for autonomous coding agents using RushDB's property graph and vector search capabilities.

**Thesis:** Building a working graph-memory system for an autonomous coding agent with RushDB takes under 200 lines of code and eliminates the need for manual context management.

## What This Tutorial Demonstrates

1. **Schema Design** — Defining a memory schema that captures code entities and their relationships
2. **Observation Logging** — Pushing agent observations (file changes, hypotheses, confirmed facts) into the graph
3. **Semantic Context Retrieval** — Querying relevant context using vector similarity, not full history scans
4. **Memory Pruning** — Forgetting stale observations while preserving important decisions
5. **Agent Loop** — A minimal working loop demonstrating the full memory cycle

## Prerequisites

- Python 3.9+
- A RushDB account (free tier works)
- `RUSHDB_API_KEY` from your RushDB dashboard

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY

# Seed the database with sample memory data
python seed.py
```

## Running the Example

```bash
python main.py
```

The example will:
1. Initialize the graph memory schema
2. Create a simulated agent session
3. Log observations about file changes and decisions
4. Demonstrate semantic search to retrieve relevant context
5. Show memory pruning in action

## Project Structure

```
building-a-graph-memory-system-for-autonomous-codi-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py           # Seed script with sample memory data
└── main.py           # Main agent loop with graph memory
```

## Memory Schema

The system uses these record labels:

| Label | Purpose |
|-------|---------|
| `Agent` | Represents the autonomous agent |
| `Task` | A coding task or goal |
| `File` | A file being modified or referenced |
| `Observation` | An observation or hypothesis from the agent |
| `ConfirmedFact` | A validated/confirmed piece of knowledge |
| `Decision` | A decision made during task execution |

## Relationships

```
Agent --WORKING_ON--> Task
Task --MODIFIES--> File
Agent --CREATED--> Observation
Agent --MADE_DECISION--> Decision
Observation --VALIDATED_AS--> ConfirmedFact
Decision --INFORMS--> Task
```

## Memory Pruning Strategy

The system uses a three-tier importance system:

- **High** (`importance: 3`): Confirmed facts, architectural decisions — never auto-delete
- **Medium** (`importance: 2`): Task-related observations — prune after 30 days if not confirmed
- **Low** (`importance: 1`): Speculative observations — prune after 7 days

## Embedding Model

This example uses `sentence-transformers/all-MiniLM-L6-v2` for generating embeddings:
- Fast and lightweight (384 dimensions)
- Good general-purpose performance for code-related text
- Self-hosted (no API costs)

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdks/python)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-a-graph-memory-system-for-autonomous-codi-tutorial)
