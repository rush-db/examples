# Context Window Overflow Solutions: Managing Long-Horizon Agent Interactions

This project demonstrates how to use RushDB as an external memory layer to solve context window overflow problems in long-running agent interactions.

## The Problem

When building AI agents that handle extended conversations or tasks spanning many steps, the context window fills up quickly. Naive approaches either:
- Truncate history (losing important context)
- Stuff everything in (hitting token limits and high costs)

## The Solution: External Memory with RushDB

RushDB provides a full-cycle memory layer that lets you:
1. **Store** conversation history and intermediate results
2. **Compress** semantically meaningful information
3. **Retrieve** only relevant context for each new turn
4. **Query** historical patterns to inform future decisions

## What This Demo Shows

1. **Conversation Storage** — Storing full dialogue history as structured records
2. **Semantic Chunking** — Breaking long conversations into meaningful chunks
3. **Summarization** — Extracting key facts and compressing older context
4. **Context Retrieval** — Using vector similarity to pull only relevant history
5. **Memory Pruning** — Intelligent cleanup of obsolete context

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and add your RushDB API key
cp .env.example .env
```

Get your API key from [RushDB Dashboard](https://app.rushdb.com).

## Run the Demo

```bash
# First, seed mock conversation data (optional — skip if already seeded)
python seed.py

# Run the main demonstration
python main.py
```

## Expected Output

```
=== Context Window Overflow Solutions Demo ===

[1] Storing Conversation History
✅ Created 3 conversation records (total: 3)
   Latest: project_planning_convo

[2] Semantic Chunking
✅ Created 8 chunks from conversations
   Sample chunk: "The user mentioned needing to ship by Q2"

[3] Summarization & Fact Extraction
✅ Extracted 5 key facts from conversation history
   Sample fact: User needs budget approval from finance team

[4] Context Retrieval (Vector Search)
🔍 Query: "What are the project deadlines?"
✅ Retrieved 3 relevant chunks with similarity scores
   Top match: "Project planning session - deadline is end of Q2"

[5] Memory Pruning
✅ Pruned 2 obsolete chunks (old summary data)
   Remaining active chunks: 8

=== All operations completed successfully! ===
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent                                │
│  (your application using RushDB as external memory)          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      RushDB                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ CONVERSATION│  │    CHUNK    │  │         FACT        │   │
│  │   records   │  │   records   │  │    (extracted)     │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
│         │               │                    │              │
│         └───────────────┴────────────────────┘              │
│                         │                                    │
│              Vector Similarity Index                        │
│              (semantic search for retrieval)                │
└─────────────────────────────────────────────────────────────┘
```

## Key RushDB Operations Used

| Operation | Purpose |
|-----------|---------|
| `db.records.create()` | Store conversation history |
| `db.records.upsert()` | Update summaries in place |
| `db.ai.search()` | Semantic retrieval of relevant context |
| `db.records.find()` | Query historical data |
| `db.records.delete()` | Prune obsolete records |

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/context-window-overflow-solutions-managing-long-ho-tutorial)
- [Pricing](https://rushdb.com/pricing)
