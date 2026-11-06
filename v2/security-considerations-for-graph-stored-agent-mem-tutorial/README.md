# Security Considerations for Graph-Stored Agent Memories

This project demonstrates security best practices for implementing agent memory systems using RushDB's property graph model. It showcases how to leverage RushDB's features to build secure, isolated, and auditable memory layers for AI agents.

## What This Tutorial Covers

1. **Data Isolation** — Multi-tenant workspace architecture for agent memories
2. **Relationship-Based Access Control (RBAC)** — Using graph edges to model permissions
3. **Audit Trails** — Tracking all memory read/write operations
4. **Input Validation & Sanitization** — Preventing injection attacks on memory queries
5. **Memory Classification** — Labeling sensitive vs. non-sensitive memories
6. **Secure Transactions** — Atomic operations for memory consistency

## Prerequisites

- Python 3.10+
- A RushDB account ([sign up free](https://rushdb.com))
- `rushdb>=2.0.0` Python package

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rush-db/examples.git
   cd security-considerations-for-graph-stored-agent-mem-tutorial
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_TOKEN
   ```

4. **Seed mock data (optional — skip if running for the first time to create fresh data):**
   ```bash
   python seed.py
   ```

## Running the Demo

```bash
python main.py
```

## Expected Output

The script demonstrates security patterns through sequential examples:

1. **Workspace Isolation** — Creates separate workspaces for different agents
2. **Access Control Model** — Establishes permission relationships between agents and memory types
3. **Secure Memory Creation** — Writes memories with proper validation
4. **Access Control Enforcement** — Demonstrates query filtering based on permissions
5. **Audit Trail** — Logs all memory operations with timestamps and actor info
6. **Data Classification** — Marks sensitive memories for restricted access
7. **Secure Transaction** — Atomic memory updates with rollback capability

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RushDB Property Graph                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    CAN_ACCESS     ┌──────────────────────┐    │
│  │  AGENT  │◄──────────────────│   AGENT_MEMORY       │    │
│  │ (alice) │                   │   (sensitive=true)   │    │
│  └────┬────┘                   └──────────┬───────────┘    │
│       │                                     │              │
│       │                                     │              │
│       │              ┌──────────────────────┘              │
│       │              │                                   │
│       │              ▼                                   │
│       │    ┌──────────────────────┐                      │
│       └────│   AUDIT_RECORD       │                      │
│            │   (operation=READ)   │                      │
│            │   (actor=alice)      │                      │
│            │   (timestamp=...)    │                      │
│            └──────────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Security Patterns

### 1. Workspace Isolation

Each agent operates within its own workspace, ensuring data isolation:

```sdk
agent_workspace = db.records.create(
    label="WORKSPACE",
    data={"agent_id": "agent-123", "name": "Alice's Memory Space"}
)
___SPLIT___
// Workspace isolation is handled at the project level in RushDB
// Create separate projects for each agent tenant
```

### 2. Relationship-Based Access Control

Use graph relationships to model permissions:

```sdk
db.records.attach(
    source=agent,
    target=memory_type,
    options={"type": "CAN_ACCESS", "direction": "out"}
)
___SPLIT___
await db.records.attach({
    source: agent,
    target: memoryType,
    options: { type: 'CAN_ACCESS', direction: 'out' }
})
```

### 3. Audit Trail

Every memory operation creates an audit record:

```sdk
db.records.create(
    label="AUDIT_LOG",
    data={
        "operation": "CREATE",
        "actor": agent.id,
        "resource": memory.id,
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": "192.168.1.1"
    }
)
___SPLIT___
await db.records.create({
    label: 'AUDIT_LOG',
    data: {
        operation: 'CREATE',
        actor: agent.id,
        resource: memory.id,
        timestamp: new Date().toISOString()
    }
})
```

### 4. Secure Transactions

Use transactions for atomic memory operations:

```sdk
with db.transactions.begin() as tx:
    memory = db.records.create(
        label="MEMORY",
        data={"content": "Secure memory content", "classification": "internal"},
        transaction=tx
    )
    # Audit log is created within same transaction
    db.records.create(
        label="AUDIT_LOG",
        data={"operation": "CREATE", "resource": memory.id},
        transaction=tx
    )
    # Context manager handles commit/rollback automatically
___SPLIT___
const tx = await db.transactions.begin()
try {
    const memory = await db.records.create({
        label: 'MEMORY',
        data: { content: 'Secure memory content', classification: 'internal' }
    }, tx)
    await db.records.create({
        label: 'AUDIT_LOG',
        data: { operation: 'CREATE', resource: memory.id }
    }, tx)
    await tx.commit()
} catch (e) {
    await tx.rollback()
    throw e
}
```

## Security Considerations Summary

| Concern | RushDB Solution |
|---------|-----------------|
| Data Isolation | Workspace-level separation |
| Access Control | Relationship-based permissions via graph edges |
| Audit Trail | Dedicated AUDIT_LOG label with timestamps |
| Input Validation | Transaction-based sanitization |
| Data Classification | Label-based memory types (SENSITIVE, INTERNAL, PUBLIC) |
| Consistency | ACID transactions |
| Query Security | Parameterized queries via `where` clause |

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Repository](https://github.com/rush-db/examples)
- [Agent Memory Patterns](https://docs.rushdb.com/concepts/memory-systems)
