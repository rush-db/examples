# RushDB for Agent Memory

A complete, runnable implementation demonstrating how to build persistent long-term memory for AI agents using RushDB's unique combination of property graph relationships and vector similarity search.

## What This Example Demonstrates

### Architecture Overview

This example implements a memory system for AI agents using RushDB's dual-layer storage:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Memory Architecture                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐     CONTAINS     ┌─────────────┐                   │
│  │   Session   │──────────────────│    Task     │                   │
│  └─────────────┘                  └──────┬──────┘                   │
│                                          │                           │
│                               ┌──────────┼──────────┐                │
│                               │          │          │                │
│                            EXECUTED   FAILED_ON  LEARNED_FROM        │
│                               │          │          │                │
│                               ▼          ▼          ▼                │
│                    ┌──────────────┐ ┌──────────┐ ┌──────────────┐   │
│                    │ToolExecution │ │ Memory   │ │ Memory       │   │
│                    └──────────────┘ │ Episode  │ │ Episode      │   │
│                                    └──────────┘ └──────────────┘   │
│                                              ▲                      │
│                                              │                      │
│                                    Semantic Similarity              │
│                                              │                      │
│                    ┌──────────────────────────────────────────┐      │
│                    │        Vector Index on 'content'         │      │
│                    │  (semantic search for similar issues)     │      │
│                    └──────────────────────────────────────────┘      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Features Demonstrated

1. **Zero-Schema Memory Records**: Add new memory types without migrations
   - `Session`: Tracks agent session context
   - `Task`: Individual tasks the agent handles
   - `ToolExecution`: Tool call history with parameters and results
   - `MemoryEpisode`: Lessons learned, failures, and context

2. **Graph Relationships**: Link related episodes across agent lifetimes
   - `CONTAINS`: Session → Task
   - `EXECUTED`: Task → ToolExecution
   - `FAILED_ON`: Task → MemoryEpisode (past failures)
   - `LEARNED_FROM`: Task → MemoryEpisode (lessons)

3. **Hybrid Retrieval**: Combine graph traversal with vector search
   - Graph: Follow `FAILED_ON` edges to find tasks that previously failed
   - Vector: Semantic search to find semantically similar issues

4. **Full Agent Loop**: From task receipt to memory-enriched response

## Setup

### Prerequisites

- Python 3.10+
- A RushDB account and API key ([sign up here](https://app.rushdb.com))

### Installation

```bash
# Clone the examples repository
git clone https://github.com/rush-db/examples.git
cd examples/rushdb-for-agent-memory-usecase

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### Running the Example

```bash
python main.py
```

## Code Walkthrough

### 1. Initializing the Memory System

```sdk
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

db = RushDB(api_key)
model = SentenceTransformer('all-MiniLM-L6-v2')

agent = AgentMemory(db, model)
```

### 2. Starting a Session

```sdk
session = agent.start_session(
    user_id="user_123",
    system_context="You are a helpful code review assistant"
)
# Creates a Session record linked to the user's context
```

### 3. Retrieving Relevant Memory (Hybrid Query)

```sdk
context = agent.get_relevant_memory(task_id="debug_api_timeout")

# Step 1: Graph traversal - find tasks that previously failed on this
past_failures = db.records.find({
    "labels": ["Task"],
    "where": {
        "MemoryEpisode": {"$relation": {"type": "FAILED_ON", "direction": "out"}},
        "task_id": task_id
    }
})

# Step 2: Vector search - find semantically similar issues
similar_issues = db.ai.search({
    "propertyName": "content",
    "query": task_description,
    "labels": ["MemoryEpisode"],
    "where": {"type": "failure"},
    "limit": 5
})
```

### 4. Recording Tool Executions

```sdk
tool_result = agent.record_tool_execution(
    task_id="review_pr_456",
    tool_name="git_diff",
    parameters={"file": "src/api.py"},
    result={"additions": 50, "deletions": 10}
)
```

### 5. Learning from Failures

```sdk
agent.record_failure(
    task_id="fix_login_bug",
    tool_name="sql_query",
    error_message="Connection timeout after 30 seconds",
    lesson="Always add retry logic with exponential backoff for external services"
)
# Creates a MemoryEpisode and links it via FAILED_ON and LEARNED_FROM edges
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RUSHDB_API_KEY` | Yes | Your RushDB API key |
| `RUSHDB_URL` | No | Self-hosted URL (defaults to RushDB cloud) |

## Project Structure

```
rushdb-for-agent-memory-usecase/
├── README.md           # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
└── main.py            # Complete agent memory implementation
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK Reference](https://docs.rushdb.com/sdks/python-sdk)
- [Vector Search in RushDB](https://docs.rushdb.com/features/vector-search)
- [Graph Relationships](https://docs.rushdb.com/features/relationships)

## License

MIT License - See [LICENSE](https://github.com/rush-db/examples/blob/master/LICENSE) for details.
