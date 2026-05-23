# Bidirectional Relationship Modeling for Agent Memory

## Overview

This example demonstrates how RushDB's property graph structure enables **bidirectional recall** — the ability to both retrieve information from memory AND understand what depends on that information (self-awareness).

In agent systems, bidirectional recall is critical for:
- **Memory retrieval**: "What does the agent know about topic X?"
- **Impact analysis**: "What would break if we update fact Y?"
- **Contextual awareness**: "Which decisions used this information?"

## Architecture

The example models a **task-planning agent** with three core concepts:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT MEMORY GRAPH                         │
└─────────────────────────────────────────────────────────────────────┘

    ┌─────────┐                    ┌──────────────┐
    │  AGENT  │──HAS_MEMORY───────▶│  MEMORY_NODE │
    └─────────┘                    └──────┬───────┘
                                          │
                         ┌────────────────┼────────────────┐
                         │ABOUT           │USED_BY         │REFERENCED_BY
                         ▼                ▼                ▼
                  ┌────────────┐    ┌───────────┐    ┌────────────┐
                  │  CONCEPT  │    │ TASK_STEP │    │ TASK_STEP  │
                  └────────────┘    └─────┬─────┘    └────────────┘
                                          │
                                   CREATES ──────▶│
                                                  │
                                          ┌────────┴────────┐
                                          │   MEMORY_NODE    │
                                          └──────────────────┘

Bidirectional paths:
  MemoryNode ──USED_BY──▶ TaskStep
  TaskStep  ──USED───▶ MemoryNode

This enables queries like:
  • "What does the agent know about X?"      (MemoryNode → Concept)
  • "What tasks used this fact?"             (MemoryNode → TaskStep via USED_BY)
  • "What facts does this task rely on?"     (TaskStep → MemoryNode via USED)
```

## Key Concepts Demonstrated

### 1. Bidirectional Relationship Structure

Records and relationships form a navigable graph where:
- **Outbound** (what this record knows/does): Relationships from source to target
- **Inbound** (what references this record): Reverse traversal

### 2. Bidirectional Query Patterns

```sdk
# Forward query: "What does the agent know about 'project planning'?"
memories = db.records.find({
    "labels": ["MEMORY"],
    "where": {
        "AGENT": {"$relation": {"type": "HAS_MEMORY", "direction": "out"}},
        "CONCEPT": {"name": {"$contains": "project planning"}}
    }
})

# Reverse query: "What tasks depend on this memory?"
dependent_tasks = db.records.find({
    "labels": ["TASK_STEP"],
    "where": {
        "MEMORY": {"$relation": {"type": "USED", "direction": "in"}}}
})
```

### 3. Semantic Search Within Relationship Context

Vectors enable semantic retrieval while the graph structure provides context:

```sdk
# Find semantically similar memories about a topic
similar = db.ai.search({
    "propertyName": "content",
    "query": "user requirements and constraints",
    "labels": ["MEMORY"],
    "limit": 5
})

# Then trace: "Which tasks used these memories?"
for memory in similar.data:
    tasks = db.records.find({
        "labels": ["TASK_STEP"],
        "where": {
            "MEMORY": {"$relation": {"type": "USED", "direction": "in"}}}
    })
```

## Prerequisites

- Python 3.9+
- RushDB account (free tier works)
- `rushdb>=2.0.0` Python package

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your RushDB API token
```

Get your API token from: https://app.rushdb.com/settings/api-tokens

### 3. Create vector index

Before running, create a vector index for semantic search:

```sdk
# Create external index (you'll supply embeddings)
index = db.ai.indexes.create({
    "label": "MEMORY",
    "propertyName": "content",
    "sourceType": "external",
    "dimensions": 384,  # for all-MiniLM-L6-v2
    "similarityFunction": "cosine"
})
```

Or use managed indexing (server embeds for you):

```sdk
index = db.ai.indexes.create({
    "label": "MEMORY",
    "propertyName": "content"
    # sourceType defaults to "managed"
})
```

### 4. Seed the database (optional)

The seed script populates realistic agent memory data. Run it once:

```bash
python seed.py
```

The script is idempotent — safe to run multiple times. It checks for existing data before creating.

## Running the Example

```bash
python main.py
```

The example demonstrates:

1. **Creating Memory Structure**: Build the agent's memory graph
2. **Forward Query**: "What does the agent know about X?"
3. **Reverse Query**: "What depends on this fact?"
4. **Bidirectional Trace**: "Show me the full impact chain"
5. **Semantic Search**: "Find memories semantically related to X"
6. **Impact Analysis**: "What tasks would be affected by updating this fact?"

## Output Structure

Each query prints:
- Query description
- Results with relationship context
- Execution metadata (record counts, query time)

## Understanding Bidirectional Recall

### Why Graph Native?

Traditional databases store relationships as foreign keys or documents:
- **Forward access**: Fast (you know what it points to)
- **Reverse access**: Slow (scan all records to find references)

RushDB's graph structure stores edges as first-class citizens:
- **Both directions**: O(1) traversal, no index scan needed
- **Relationship typing**: "USED" ≠ "SUGGESTED" ≠ "CONFLICTS_WITH"
- **Property edges**: Edges can have metadata (confidence, timestamp)

### The Self-Awareness Pattern

Agent self-awareness comes from bidirectional queries:

```python
# Self-awareness query: "What is the agent's current context?"
def get_agent_context(agent_id, topic):
    # Forward: What does this agent know about the topic?
    knowledge = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "AGENT": {"$id": agent_id},
            "CONCEPT": {"name": topic}
        }
    })
    
    # Reverse: What tasks are using this knowledge?
    impacted_tasks = []
    for memory in knowledge:
        tasks = db.records.find({
            "labels": ["TASK_STEP"],
            "where": {
                "MEMORY": {
                    "$relation": {"type": "USED", "direction": "in"},
                    "$id": memory.id
                }
            }
        })
        impacted_tasks.extend(tasks)
    
    return {
        "knowledge": knowledge,
        "dependent_tasks": impacted_tasks,  # Self-awareness!
        "confidence": calculate_confidence(knowledge, impacted_tasks)
    }
```

## Customization

### Adapting for your agent

1. **Define your labels**: Replace AGENT, MEMORY, TASK_STEP with your domain labels
2. **Define relationships**: Map your bidirectional dependencies to RushDB relationship types
3. **Add vector properties**: Enable semantic search on key content fields

### Scaling considerations

- **100-1000 memories**: Single index works fine
- **10K+ memories**: Consider partitioning by agent or domain
- **Real-time updates**: Use transactions for atomic updates to memory+relationships

## References

- RushDB Documentation: https://docs.rushdb.com
- Python SDK: https://docs.rushdb.com/sdk/python
- GitHub Example: https://github.com/rush-db/examples
