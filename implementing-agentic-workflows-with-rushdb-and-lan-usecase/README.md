# Implementing Agentic Workflows with RushDB and LangChain

This example demonstrates how RushDB's unified graph+vector architecture replaces the "Pinecone + Neo4j + Redis" stack that LangChain agents typically require. Instead of stitching together three separate systems, your agent gets atomic graph traversal, semantic retrieval, and state management from a single API.

## What This Example Demonstrates

1. **Agent Loop**: A working plan → tool call → retrieve context → update memory → decide cycle
2. **Unified Memory**: Tool outputs as JSON properties, agent state as nodes, context as vectors — all in one transaction
3. **Graph Traversal**: Finding related conversation turns by following `AGENT_ACTION → outcome` edges
4. **Hybrid Search**: Vector similarity filtered by graph-relationship context (not just embedding scores)
5. **Atomic Operations**: RushDB transactions wrap related writes so you never get partial state

## Architecture Comparison

### Before: Three Systems to Manage

```
LangChain Agent
    ├── Pinecone (vector memory for RAG)
    ├── Neo4j (conversation graph)
    └── Redis (short-term state / history)
```

Every operation requires:
- Serializing/deserializing between systems
- Coordinating writes across multiple APIs
- Handling partial failures when one system succeeds and another fails
- Managing three sets of credentials and connection pools

### After: One System

```
LangChain Agent
    └── RushDB (unified graph + vector + state)
```

All operations are atomic, consistent, and use a single API.

## Prerequisites

- Python 3.10+
- A RushDB account ([get one free](https://rushdb.com))
- `langchain` and `langchain-openai` for the agent framework
- `sentence-transformers` for local embeddings (no OpenAI required for this example)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

Get your API key from the [RushDB dashboard](https://app.rushdb.com).

### 3. Seed the Database (Optional)

The seed script creates a realistic agent session history so you can see how RushDB handles related data retrieval. Run it once:

```bash
python seed.py
```

This creates:
- 3 agent sessions with varying states
- 15+ tool calls with realistic outputs
- Conversation turns connected via graph relationships

### 4. Run the Example

```bash
python main.py
```

## Expected Output

The example runs a multi-turn agent conversation that:

1. **Creates a new agent session** — stored as a `SESSION` node with initial state
2. **Executes tool calls** — each tool result stored atomically with graph relationships
3. **Retrieves context** — vector search + graph traversal working together
4. **Updates memory** — agent state and conversation history persisted in one transaction
5. **Demonstrates hybrid retrieval** — finds semantically similar turns filtered by session relationship

Sample output:

```
=== Agentic Workflow with RushDB ===

[1] Creating agent session...
Session created: SESSION-id

[2] Executing agent loop...
Step 1: Plan → Tool Call: search_knowledge_base
Tool result: Found 2 relevant documents about Python async patterns

Step 2: Plan → Tool Call: execute_code
Tool result: Code executed successfully, returned 42

Step 3: Plan → Tool Call: retrieve_context
Tool result: Retrieved 3 related conversation turns from session

[3] Demonstrating graph traversal...
Found 4 conversation turns related to 'code_execution' in this session

[4] Demonstrating hybrid search with relationship filter...
Vector search for 'async programming patterns' filtered by SESSION relation
Found 2 semantically similar turns with strong session context

[5] Updating agent memory atomically...
Agent state updated: {thinking: 'evaluating results', confidence: 0.85}
All operations committed in single transaction
```

## Project Structure

```
implementing-agentic-workflows-with-rushdb-and-lan-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generate mock agent session data
└── main.py             # Main example demonstrating the workflow
```

## Key Code Patterns

### Atomic Transaction (Everything Succeeds or Fails Together)

```sdk
with db.transactions.begin() as tx:
    session = db.records.create(
        label="SESSION",
        data={"task": "analyze_data", "status": "active"},
        transaction=tx
    )
    tool_call = db.records.create(
        label="TOOL_CALL",
        data={"tool": "search", "input": "python async", "output": "found 3 results"},
        transaction=tx
    )
    db.records.attach(
        source=session,
        target=tool_call,
        options={"type": "INITIATED", "direction": "out"},
        transaction=tx
    )
    # NO tx.commit() — context manager handles this
```

### Graph Traversal Query

```sdk
# Find all conversation turns connected to a session through tool calls
related_turns = db.records.find({
    "labels": ["CONVERSATION_TURN"],
    "where": {
        "SESSION": {"$relation": {"type": "PART_OF", "direction": "in"}},
        "intent": {"$contains": "code"}
    },
    "limit": 10
})
```

### Vector Search with Relationship Filter

```sdk
# Semantic search filtered by session context
context_results = db.ai.search({
    "propertyName": "content",
    "query": "async programming patterns",
    "labels": ["CONVERSATION_TURN"],
    "where": {
        "SESSION": {"$id": session.id}
    },
    "limit": 5
})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [LangChain Integration Guide](https://docs.rushdb.com/integrations/langchain)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/implementing-agentic-workflows-with-rushdb-and-lan-usecase)
