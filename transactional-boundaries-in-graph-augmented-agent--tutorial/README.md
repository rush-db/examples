# Transactional Boundaries in Graph-Augmented Agent Workflows

A hands-on tutorial demonstrating how RushDB's ACID transactions provide reliable execution boundaries for graph-augmented AI agents.

**Target audience**: Senior engineers building agentic systems that need reliable memory, state management, and workflow orchestration.

---

## What Are Transactional Boundaries?

In graph-augmented agent systems, a "transaction" represents an **atomic unit of work** — either everything succeeds together, or nothing is persisted. This is critical when:

- An agent reads context, plans actions, and writes results
- Multiple records and relationships must be created atomically
- Partial failures require complete rollback to maintain consistency

### Why Transactions Matter for Agents

Consider an agent that:
1. Reads a user's request from memory
2. Plans sub-tasks based on context
3. Executes actions and stores results
4. Updates its belief state

Without transactions, a failure in step 3 could leave the agent in an inconsistent state — goals created but not tracked, beliefs updated but actions not recorded. Transactions ensure **all-or-nothing** semantics.

---

## RushDB Transaction Patterns

### Pattern 1: Explicit Begin/Commit/Rollback

```sdk
tx = db.transactions.begin()
try:
    task = db.records.create(
        label="TASK",
        data={"description": "Process order", "status": "pending"},
        transaction=tx
    )
    subtask = db.records.create(
        label="SUBTASK",
        data={"description": "Validate items", "parentId": task.id},
        transaction=tx
    )
    db.records.attach(
        source=task,
        target=subtask,
        options={"type": "HAS_SUBTASK"},
        transaction=tx
    )
    tx.commit()
except Exception as e:
    tx.rollback()
    raise e
___SPLIT___
const tx = await db.transactions.begin()
try {
    const task = await db.records.create(
        { label: 'TASK', data: { description: 'Process order', status: 'pending' } },
        tx
    )
    const subtask = await db.records.create(
        { label: 'SUBTASK', data: { description: 'Validate items', parentId: task.id } },
        tx
    )
    await db.records.attach(
        { source: task, target: subtask, options: { type: 'HAS_SUBTASK' } },
        tx
    )
    await tx.commit()
} catch (e) {
    await tx.rollback()
    throw e
}
```

### Pattern 2: Context Manager (Preferred)

```sdk
with db.transactions.begin() as tx:
    agent = db.records.create(
        label="AGENT",
        data={"name": "DataPipelineAgent", "state": "idle"},
        transaction=tx
    )
    session = db.records.create(
        label="SESSION",
        data={"startedAt": "2024-01-15T10:00:00Z"},
        transaction=tx
    )
    db.records.attach(source=agent, target=session, options={"type": "RUNNING"}, transaction=tx)
# Auto-commits on success, auto-rollbacks on exception
___SPLIT___
// TypeScript lacks native context managers; use try/finally pattern
let tx = await db.transactions.begin()
try {
    const agent = await db.records.create(
        { label: 'AGENT', data: { name: 'DataPipelineAgent', state: 'idle' } },
        tx
    )
    const session = await db.records.create(
        { label: 'SESSION', data: { startedAt: '2024-01-15T10:00:00Z' } },
        tx
    )
    await db.records.attach(
        { source: agent, target: session, options: { type: 'RUNNING' } },
        tx
    )
    await tx.commit()
} finally {
    if (tx.isOpen()) await tx.rollback()
}
```

---

## What This Tutorial Demonstrates

This project simulates a **graph-augmented research agent** that:

1. Maintains memory of tasks and context
2. Plans research sub-tasks based on goals
3. Executes research steps atomically
4. Records beliefs and observations
5. Handles failures gracefully with full rollback

You'll see how transactional boundaries keep the agent's knowledge graph consistent even when failures occur.

---

## Prerequisites

- Python 3.10+
- A RushDB account (free tier works)
- API key from https://dash.rushdb.com

---

## Setup

```bash
# Clone the examples repository
git clone https://github.com/rush-db/examples.git
cd transactional-boundaries-in-graph-augmented-agent--tutorial

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHD_API_KEY
```

---

## Running the Tutorial

```bash
python main.py
```

The script will:
1. Clean up any existing demo data
2. Run three scenarios demonstrating transaction patterns
3. Show successful commits, then simulate failures with rollback

### Expected Output

```
===============================================
Graph-Augmented Agent: Transactional Boundaries
===============================================

[1/3] SCENARIO: Successful atomic planning
─────────────────────────────────────────────
✓ Created AGENT: research-agent-001
✓ Created GOAL: research-graph-transactions
✓ Created 3 TASK nodes
✓ Attached all relationships
✓ Transaction committed successfully

[2/3] SCENARIO: Failure recovery with rollback
─────────────────────────────────────────────
✗ Simulated failure in step 2
✓ Transaction rolled back - no partial data
✓ Agent state preserved, ready for retry

[3/3] SCENARIO: Nested workflow with context manager
─────────────────────────────────────────────
✓ Created RESEARCH_SESSION: session-abc123
✓ Nested TASK_PLAN with 2 steps
✓ All operations atomic via context manager
✓ Session tracked in agent memory
```

---

## Project Structure

```
├── main.py           # Main tutorial script with all scenarios
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── README.md         # This file
```

---

## Key Takeaways

| Pattern | Use When |
|---------|----------|
| Explicit try/except | Complex error handling, conditional commits |
| Context manager | Linear workflows where success = commit, failure = rollback |
| Mixed approach | Agent planning with separate plan/execute phases |

**Golden rule**: If your agent does multiple writes that must succeed together, wrap them in a transaction. Partial state is corrupted state.

---

## Further Reading

- [RushDB Transactions Documentation](https://docs.rushdb.com/features/transactions)
- [Graph-Augmented Agents: Memory Patterns](https://docs.rushdb.com/guides/agent-memory)
- [RushDB SDK Reference](https://docs.rushdb.com/sdks/python)

---

## Troubleshooting

**"Transaction is closed" error**
→ You're calling `tx.commit()` inside a `with` block. The context manager handles this automatically.

**"Invalid token" error**
→ Check your API key in `.env`. Get one at https://dash.rushdb.com

**"Connection refused"**
→ Ensure you're using the correct API endpoint for self-hosted deployments.
