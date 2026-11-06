# Storing Tool Definitions and Execution Traces as Graph Nodes

A complete multi-agent tool orchestrator demonstrating how to store every tool definition and execution trace in RushDB, enabling live debugging of agent decision chains.

## What This Demonstrates

This project shows how to build a traceable agent system where:

1. **Tool Definitions** are stored as graph nodes with metadata (name, parameters, description) and vector embeddings for semantic tool matching
2. **Execution Traces** record every tool call, linked to the tool, calling agent, parent execution (chains), and sibling executions (parallel calls)
3. **Graph Traversal** enables finding the root trigger of any failed execution and all affected parallel branches
4. **Semantic Search** finds tools similar to one that was available but not used

## Prerequisites

- Python 3.9+
- A RushDB account ([get one free](https://rushdb.com))
- `sentence-transformers` for generating embeddings

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your RushDB API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
RUSHDB_API_KEY=your_api_key_here
```

### 3. Run the Demo

The demo is self-contained and will:
- Seed tools and agents
- Run mock agent decisions with chains and parallel calls
- Record all execution traces
- Demonstrate traversal queries and semantic search

```bash
python main.py
```

## Expected Output

```
=== Tool Definition & Execution Trace Demo ===

[1] Seeding agents...
Created 3 agents

[2] Seeding tool definitions...
Created 8 tools with vector embeddings

[3] Creating vector index for semantic search...
Vector index 'TOOL.description' ready

[4] Simulating Agent Decisions...

--- Decision Chain: User asks about weather ---
Execution #1: AGENT_USED tool 'get_weather'
Execution #2: AGENT_USED tool 'format_weather_response'
Execution #3: CHILD_OF execution #2 → 'send_notification'

--- Parallel Execution: Multi-source data fetch ---
Execution #4: PARALLEL_OF execution #5 → 'fetch_stock_price'
Execution #5: PARALLEL_OF execution #4 → 'fetch_news'

--- Failed Execution (simulated) ---
Execution #6: FAILED tool 'process_payment'

[5] Traversal Query: Finding failure root cause ===

Failed execution: process_payment
Parent chain:
  - process_payment (FAILED)
  - checkout_session (SUCCESS)
  - initiate_checkout (SUCCESS)
  - user_clicked_checkout (SUCCESS - ROOT TRIGGER)

Affected parallel branches:
  - validate_inventory (ran in parallel with process_payment)
  - calculate_shipping (ran in parallel with process_payment)

[6] Semantic Search: Finding unused similar tools ===


Query: "send an email to a user"
Used tool: send_email

Similar tools that were available but not used:
  - send_sms: 0.94 similarity - "Send SMS notification"
  - slack_message: 0.89 similarity - "Post to Slack channel"
  - push_notification: 0.87 similarity - "Send push notification"

[7] Querying all execution traces for 'orchestrator' agent ===

Found 4 executions by orchestrator agent
  - get_weather (SUCCESS)
  - format_weather_response (SUCCESS)
  - fetch_stock_price (SUCCESS)
  - fetch_news (SUCCESS)
```

## Project Structure

```
storing-tool-definitions-and-execution-traces-as-g-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── main.py            # Main demo script
└── data/
    └── seed_data.py   # Tool and agent definitions
```

## Graph Schema

### Labels

| Label | Description |
|-------|-------------|
| `TOOL` | Tool definition with name, description, parameters |
| `AGENT` | Agent with name, role, capabilities |
| `EXECUTION` | Execution trace with status, input, output, timing |

### Relationship Types

| Type | From | To | Description |
|------|------|----|-------------|
| `EXECUTED` | AGENT | EXECUTION | Agent triggered an execution |
| `USED` | EXECUTION | TOOL | Execution used a tool |
| `CHILD_OF` | EXECUTION | EXECUTION | Chain: child execution follows parent |
| `PARALLEL_OF` | EXECUTION | EXECUTION | Parallel branch: executed concurrently |
| `TRIGGERED` | EXECUTION | EXECUTION | Root cause: first execution in a chain |

## Key Patterns

### Storing Tool Definitions with Vectors

```sdk
from rushdb import RushDB

db = RushDB(os.getenv("RUSHDB_API_KEY"))

# Create tool with vector embedding for semantic search
tool = db.records.create(
    label="TOOL",
    data={
        "name": "send_email",
        "description": "Send an email to a user",
        "parameters": {
            "to": "string",
            "subject": "string",
            "body": "string"
        },
        "category": "communication"
    },
    vectors=[{"propertyName": "description", "vector": embedding}],
)
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Create tool with vector embedding for semantic search
const tool = await db.records.create({
    label: 'TOOL',
    data: {
        name: 'send_email',
        description: 'Send an email to a user',
        parameters: {
            to: 'string',
            subject: 'string',
            body: 'string'
        },
        category: 'communication'
    },
    vectors: [{ propertyName: 'description', vector: embedding }]
})
```

### Recording Execution Traces with Relationships

```sdk
# Link execution to tool
db.records.attach(source=execution, target=tool, options={"type": "USED"})

# Chain: mark child execution
db.records.attach(source=child_exec, target=parent_exec, options={"type": "CHILD_OF"})

# Parallel: link sibling executions
db.records.attach(source=exec_a, target=exec_b, options={"type": "PARALLEL_OF"})
___SPLIT___
// Link execution to tool
await db.records.attach({ source: execution, target: tool, options: { type: 'USED' } })

// Chain: mark child execution
await db.records.attach({ source: childExec, target: parentExec, options: { type: 'CHILD_OF' } })

// Parallel: link sibling executions
await db.records.attach({ source: execA, target: execB, options: { type: 'PARALLEL_OF' } })
```

### Traversing Failed Executions to Root Cause

```sdk
# Find all parent executions (CHILD_OF incoming)
failed_execs = db.records.find({
    "labels": ["EXECUTION"],
    "where": {"status": "failed"}
})

# For each failed exec, follow CHILD_OF backwards to find root
root_causes = db.records.find({
    "labels": ["EXECUTION"],
    "where": {
        "EXECUTION": {
            "$relation": {"type": "CHILD_OF", "direction": "in"},
            "id": failed_exec.id
        }
    }
})
___SPLIT___
// Find all failed executions
const { data: failedExecs } = await db.records.find({
    labels: ['EXECUTION'],
    where: { status: 'failed' }
})

// For each failed exec, follow CHILD_OF backwards to find root
const { data: rootCauses } = await db.records.find({
    labels: ['EXECUTION'],
    where: {
        EXECUTION: {
            $relation: { type: 'CHILD_OF', direction: 'in' },
            id: failedExec.id
        }
    }
})
```

### Semantic Tool Search

```sdk
# Find tools similar to one that was used
similar_tools = db.ai.search({
    "propertyName": "description",
    "query": "send notification to user",
    "labels": ["TOOL"],
    "limit": 5
})
___SPLIT___
// Find tools similar to one that was used
const { data: similarTools } = await db.ai.search({
    propertyName: 'description',
    query: 'send notification to user',
    labels: ['TOOL'],
    limit: 5
})
```

## Learn More


- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/storing-tool-definitions-and-execution-traces-as-g-usecase)
- [RushDB SDK Reference](https://docs.rushdb.com/sdks/python-sdk)
