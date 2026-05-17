# Graph-Traversal-Based Routing: How Agents Select Next Actions

A practical demonstration of how AI agents can use RushDB's property graph capabilities to intelligently select their next actions by traversing relationships in a decision graph.

## Overview

In multi-step AI agent workflows, agents need to:
1. Understand their current state
2. Identify available actions
3. Select the next action based on preconditions and outcomes

This tutorial shows how to model agent routing as a graph traversal problem using RushDB. Instead of hardcoding if-else chains, the agent queries the graph to discover valid transitions.

## What This Demonstrates

- **Graph-based state machine**: Model agent states and transitions as nodes and edges
- **Precondition checking via traversal**: Query related records to validate action availability
- **Dynamic routing**: Let the graph structure determine the next action
- **Transactional state updates**: Safely update agent state as actions are taken

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works)
- API key from your RushDB workspace

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

### 3. Seed the Graph

The seed script creates a sample task graph with:
- Agent states (IDLE, RESEARCHING, WRITING, REVIEWING, COMPLETE)
- Tasks with varying priorities and dependencies
- Actions with preconditions and outcomes
- Relationships linking everything together

```bash
python seed.py
```

The script is idempotent—running it again clears existing data and reseeds.

### 4. Run the Demo

```bash
python main.py
```

## Expected Output

```
=== Graph-Traversal-Based Routing Demo ===

--- Initial Agent State ---
Agent: research_agent
Current State: IDLE
Available Actions: ['analyze_task', 'begin_research', 'fetch_context']

--- Selecting Next Action ---
Selected: begin_research
Reason: Valid preconditions met (state=IDLE, task=pending)

--- After Action: begin_research ---
Agent: research_agent
Current State: RESEARCHING
Available Actions: ['read_source', 'extract_key_points', 'synthesize_findings']

--- Completing Task Flow ---
Executing: read_source -> extract_key_points -> synthesize_findings

--- Final State ---
Task: research_agent_report (id: ...)
Status: IN_PROGRESS
Agent State: RESEARCHING

--- Dependency-Aware Routing ---
Task: build_prototype (priority: high)
Blocked by: ['design_ui'] (not complete)
Can proceed with: ['write_tests'] (dependency satisfied)

--- Complex Traversal: Finding Optimal Path ---
Path: IDLE -> RESEARCHING -> WRITING -> REVIEWING -> COMPLETE
```

## Project Structure

```
graph-traversal-based-routing-how-agents-select-ne-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py            # Graph initialization script
└── main.py            # Main demonstration
```

## Key Code Patterns

### Querying Available Actions by State

```sdk
# Find all actions available from current state
available_actions = db.records.find({
    "labels": ["ACTION"],
    "where": {
        "FROM_STATE": {
            "$relation": {"type": "AVAILABLE_FROM", "direction": "in"},
            "name": current_state
        }
    }
})
___SPLIT___
// Find all actions available from current state
const availableActions = await db.records.find({
    labels: ["ACTION"],
    where: {
        "FROM_STATE": {
            $relation: { type: "AVAILABLE_FROM", direction: "in" },
            name: currentState
        }
    }
});
```

### Checking Action Preconditions

```sdk
# Validate all preconditions are met before executing action
def check_preconditions(action, agent_state, task_status):
    state_valid = db.records.find({
        "labels": ["STATE"],
        "where": {
            "REQUIRES_FOR": {
                "$relation": {"type": "PRECONDITION", "direction": "in"},
                "$id": action.id
            },
            "name": agent_state
        }
    })
    return len(state_valid.data) > 0 and task_status == "pending"
___SPLIT___
// Validate all preconditions are met before executing action
async function checkPreconditions(action, agentState, taskStatus) {
    const stateValid = await db.records.find({
        labels: ["STATE"],
        where: {
            "REQUIRES_FOR": {
                $relation: { type: "PRECONDITION", direction: "in" },
                $id: action.id
            },
            name: agentState
        }
    });
    return stateValid.data.length > 0 && taskStatus === "pending";
}
```

### Updating Agent State Transactionally

```sdk
with db.transactions.begin() as tx:
    # Update task status
    db.records.update(
        record_id=task.id,
        data={"status": "in_progress"},
        transaction=tx
    )
    # Update agent state
    db.records.update(
        record_id=agent.id,
        data={"current_state": new_state},
        transaction=tx
    )
    # Link action execution
    db.records.attach(
        source=task,
        target=action,
        options={"type": "EXECUTED", "direction": "out"},
        transaction=tx
    )
# Auto-committed on clean exit
___SPLIT___
const tx = await db.transactions.begin();
try {
    // Update task status
    await db.records.update({
        recordId: task.id,
        data: { status: "in_progress" }
    }, tx);
    
    // Update agent state
    await db.records.update({
        recordId: agent.id,
        data: { current_state: newState }
    }, tx);
    
    // Link action execution
    await db.records.attach({
        source: task,
        target: action,
        options: { type: "EXECUTED", direction: "out" }
    }, tx);
    
    await tx.commit();
} catch (e) {
    await tx.rollback();
    throw e;
}
```

## Data Model

```
┌─────────────┐      EXECUTED       ┌─────────────┐
│    TASK     │────────────────────▶│   ACTION    │
│             │◀─────────────────────│             │
└──────┬──────┘      PRECONDITION   └──────┬──────┘n             │                              │
       │                                   │
       │ ASSIGNED                         │ AVAILABLE_FROM
       ▼                                   ▼
┌─────────────┐                      ┌─────────────┐
│    AGENT    │                      │    STATE    │
└─────────────┘                      └─────────────┘

┌─────────────┐      BLOCKS         ┌─────────────┐
│    TASK     │────────────────────▶│    TASK     │
└─────────────┘                      └─────────────┘
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Concepts](https://docs.rushdb.com/concepts/property-graph)
- [Relationship Queries](https://docs.rushdb.com/api/records/find#filtering-by-related-records)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/graph-traversal-based-routing-how-agents-select-ne-tutorial)
