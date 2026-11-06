# How to Add Long-Term Memory to an AI Agent

This tutorial demonstrates how to build persistent memory into an AI agent using RushDB as a semantic memory store. You'll learn how to:

- Store agent experiences, learned facts, and conversation history
- Create vector embeddings for semantic similarity search
- Retrieve relevant memories based on current context
- Use transactions for atomic memory operations

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent                                │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │  Perceive   │→│   Remember   │→│       Think        │   │
│  └─────────────┘  └──────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │       RushDB          │
              │  ┌──────────────────┐  │
              │  │  Memory Store    │  │
              │  │  (Vector Index)  │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB API key (get one at https://dash.rushdb.com)
- `sentence-transformers` for local embeddings (no OpenAI key required)

## Setup

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd examples/how-to-add-long-term-memory-to-an-ai-agent-tutorial

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Quick Start

### 1. Seed initial memories (optional)

```bash
python seed.py
```

This creates ~100 realistic memory records including:
- Conversation summaries
- Learned user preferences
- Factual knowledge acquired during interactions
- Procedural memories (how to handle certain tasks)

### 2. Run the demo

```bash
python main.py
```

The demo simulates an AI agent that:
1. Receives a user query
2. Searches memory for relevant past context
3. Uses retrieved memories to inform the response
4. Optionally stores the new interaction as a memory

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Core agent with memory capabilities |
| `seed.py` | Generates initial memory dataset |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

## Key Concepts Demonstrated

### 1. Semantic Memory Storage

Memories are stored with vector embeddings for similarity search:

```sdk
memory = db.records.create(
    label="MEMORY",
    data={
        "content": "User prefers concise responses",
        "type": "preference",
        "importance": 0.8,
        "timestamp": "2025-01-15T10:30:00Z"
    },
    vectors=[{"propertyName": "content", "vector": embedding}]
)
___SPLIT___
// TypeScript example (not used in this Python project)
```

### 2. Contextual Memory Retrieval

When the agent needs to recall relevant information:

```sdk
relevant_memories = db.ai.search({
    "propertyName": "content",
    "query": "What does the user like for breakfast?",
    "labels": ["MEMORY"],
    "where": {
        "type": "preference"
    },
    "limit": 5
})
___SPLIT___
// TypeScript example
```

### 3. Transactional Memory Operations

Complex operations use transactions for atomicity:

```sdk
with db.transactions.begin() as tx:
    memory = db.records.create(label="MEMORY", data={...}, transaction=tx)
    db.records.attach(source=agent, target=memory, options={"type": "KNOWS"}, transaction=tx)
___SPLIT___
// TypeScript example
```

## Memory Types

| Type | Description | Example |
|------|-------------|---------|
| `conversation` | Summary of past interactions | "User asked about Python decorators" |
| `preference` | User likes/dislikes | "User prefers detailed explanations" |
| `fact` | Learned factual knowledge | "User works at Acme Corp" |
| `skill` | Procedural knowledge | "User is familiar with async/await patterns" |

## Expected Output

```
=== AI Agent with Long-Term Memory Demo ===

[1] Query: "What did we discuss about Python last time?"
    Memories found: 3
    Retrieved: ['User asked about decorators...', 'Explained async/await...', 'User wanted Flask examples...']
    Response: Based on our previous discussion, you were interested in...

[2] Query: "Remember my preference for morning updates?"
    Memories found: 1
    Retrieved: ['User prefers morning emails at 8am...']
    Response: I recall you prefer receiving updates in the morning...

[3] Query: "What project am I working on?"
    Memories found: 2
    Retrieved: ['Working on ML pipeline project...', 'Uses scikit-learn and pandas...']
    Response: You're currently working on an ML pipeline using...
```

## How It Works

1. **Embedding Generation**: Uses `all-MiniLM-L6-v2` (384 dimensions) from sentence-transformers
   - Fast, efficient model suitable for demo purposes
   - Runs locally, no API calls needed

2. **Memory Storage**: Each memory record contains:
   - `content`: The textual memory
   - `type`: Category of memory
   - `importance`: Relevance score (0-1)
   - `embedding`: Vector representation stored in RushDB

3. **Retrieval Pipeline**:
   - User query → embed → semantic search → top-k results → context injection

## Clean Up

To remove all memory records:

```python
from rushdb import RushDB
import os

db = RushDB(os.getenv("RUSHDB_API_KEY"))
db.records.delete({"labels": ["MEMORY"]})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB SDK Reference](#) (link to SDK docs)
- [Pricing](https://rushdb.com/pricing)

## License

MIT
