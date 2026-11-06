# Conflict Resolution Strategies in Concurrent Graph-Write Operations

A practical tutorial demonstrating how to handle concurrent writes in a graph database using RushDB. This project covers optimistic and pessimistic locking patterns, transaction-based atomicity, and upsert strategies for conflict-free graph mutations.

## What You'll Learn

- **Optimistic Locking** — Using version fields to detect conflicts before writes
- **Pessimistic Locking** — Using RushDB transactions to serialize concurrent operations
- **Upsert Patterns** — Using `mergeBy` for idempotent create-or-update operations
- **Relationship Conflicts** — Handling concurrent edge creation between nodes
- **Merge Strategies** — Combining field values instead of overwriting

## Prerequisites

- Python 3.10+
- RushDB account ([sign up free](https://rushdb.com))
- `rushdb>=2.0.0` package

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### Getting Your API Key

1. Sign in at [https://app.rushdb.com](https://app.rushdb.com)
2. Navigate to **Settings → API Keys**
3. Create a new API key with read/write permissions
4. Copy the key to your `.env` file

## Project Structure

```
conflict-resolution-strategies-in-concurrent-graph-tutorial/
├── README.md
├── requirements.txt
├── .env.example
├── main.py           # Full tutorial with all conflict resolution patterns
└── data/
    └── sample_graph.json  # Sample graph data for seeding
```

## How to Run

```bash
# Seed sample data and run all conflict resolution demos
python main.py

# Run individual strategies
python main.py --strategy optimistic    # Optimistic locking demo
python main.py --strategy pessimistic   # Transaction-based locking
python main.py --strategy upsert        # Upsert merge patterns
```

## Expected Output

```
=== Conflict Resolution: Optimistic Locking ===
[✓] Created initial record with version=1
[✓] Concurrent update detected! Current version: 1, expected: 1
[✓] Merge resolution: title='Updated Title (resolved conflict)'
[✓] Optimistic lock released after conflict

=== Conflict Resolution: Pessimistic Locking ===
[✓] Transaction started for atomic update
[✓] Record updated within transaction
[✓] Transaction committed successfully
[✓] Changes persisted atomically

=== Conflict Resolution: Upsert with mergeBy ===
[✓] First upsert created new record
[✓] Second upsert merged into existing record
[✓] Merge strategy 'append' combined array fields
[✓] Record ID preserved across upserts

=== Conflict Resolution: Relationship Edges ===
[✓] Concurrent relationship creation handled
[✓] Duplicate relationships prevented
[✓] Graph consistency maintained
```

## Key Patterns Explained

### 1. Optimistic Locking

Detect concurrent modifications using a version field. If the version has changed since your read, a conflict occurred and you must re-fetch and retry.

```sdk
# Read record with version
record = db.records.find_one({"labels": ["DOCUMENT"], "where": {"slug": "my-doc"}})
expected_version = record["version"]

# Attempt update only if version unchanged
try:
    db.records.update(
        record_id=record.id,
        data={"version": expected_version + 1, "content": new_content}
    )
except ConflictError:
    # Version changed — fetch latest and merge
    latest = db.records.find_by_id(record.id)
    resolve_conflict(latest, record)
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Read record with version
const record = await db.records.findOne({
  labels: ['DOCUMENT'],
  where: { slug: 'my-doc' }
})
const expectedVersion = record.data['version']

// Attempt update only if version unchanged
try {
  await db.records.update({
    recordId: record.id,
    data: { version: expectedVersion + 1, content: newContent }
  })
} catch (error) {
  if (error.code === 'CONFLICT') {
    // Version changed — fetch latest and merge
    const latest = await db.records.findById(record.id)
    resolveConflict(latest, record)
  }
}
```

### 2. Pessimistic Locking (Transactions)

Use RushDB transactions to serialize access to critical sections. All writes within a transaction are atomic — either all succeed or all fail.

```sdk
with db.transactions.begin() as tx:
    # Perform multiple operations atomically
    order = db.records.create(
        label="ORDER",
        data={"total": 99.99},
        transaction=tx
    )
    product = db.records.create(
        label="ORDER_ITEM",
        data={"quantity": 2},
        transaction=tx
    )
    db.records.attach(source=order, target=product, transaction=tx)
    # Transaction auto-commits on clean exit
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

const tx = await db.transactions.begin()
try {
  const order = await db.records.create({
    label: 'ORDER',
    data: { total: 99.99 },
    transaction: tx
  })
  
  const product = await db.records.create({
    label: 'ORDER_ITEM',
    data: { quantity: 2 },
    transaction: tx
  })
  
  await db.records.attach({
    source: order,
    target: product,
    transaction: tx
  })
  
  await tx.commit()
} catch (error) {
  await tx.rollback()
  throw error
}
```

### 3. Upsert with mergeBy

Use `mergeBy` for idempotent operations that create or update based on unique fields. The `mergeStrategy` controls how conflicts are resolved.

```sdk
# mergeStrategy options:
# - 'replace' (default): overwrite existing fields
# - 'append': merge arrays instead of replacing
# - 'merge': deep merge objects

# First call creates, second call updates
record = db.records.upsert(
    label="USER",
    data={"externalId": "user-123", "name": "Alice", "tags": ["beta-tester"]},
    options={"mergeBy": ["externalId"], "mergeStrategy": "append"}
)

# Third call appends to tags
record = db.records.upsert(
    label="USER",
    data={"externalId": "user-123", "tags": ["premium"]},
    options={"mergeBy": ["externalId"], "mergeStrategy": "append"}
)
# Result: tags = ["beta-tester", "premium"]
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// First call creates, second call updates
const record = await db.records.upsert({
  label: 'USER',
  data: { externalId: 'user-123', name: 'Alice', tags: ['beta-tester'] },
  options: { mergeBy: ['externalId'], mergeStrategy: 'append' }
})

// Third call appends to tags
const updated = await db.records.upsert({
  label: 'USER',
  data: { externalId: 'user-123', tags: ['premium'] },
  options: { mergeBy: ['externalId'], mergeStrategy: 'append' }
})
// Result: tags = ['beta-tester', 'premium']
```

## Conflicts in Graph Relationships

When multiple processes create the same relationship edge, RushDB prevents duplicates based on the relationship type and direction. This is handled automatically by the graph engine.

```sdk
# Process A and B both try to create FOLLOW relationship
# Only one edge is created; subsequent attempts are no-ops
db.records.attach(
    source=user_a,
    target=user_b,
    options={"type": "FOLLOWS"}
)

# Verify only one relationship exists
relationships = db.relationships.find({
    "where": {
        "type": "FOLLOWS",
        "sourceId": user_a.id,
        "targetId": user_b.id
    }
})
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Process A and B both try to create FOLLOW relationship
// Only one edge is created; subsequent attempts are no-ops
await db.records.attach({
  source: userA,
  target: userB,
  options: { type: 'FOLLOWS' }
})

// Verify only one relationship exists
const relationships = await db.relationships.find({
  where: {
    type: 'FOLLOWS',
    sourceId: userA.id,
    targetId: userB.id
  }
})
```

## Pricing Note


This tutorial primarily involves **write operations** (creates, updates, upserts, relationship attachments), which consume Knowledge Units (KU). Standard reads and queries are always free.


See [RushDB Pricing](https://rushdb.com/pricing) for details.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Transaction Reference](https://docs.rushdb.com/api/transactions)
- [Upsert Documentation](https://docs.rushdb.com/api/records#upsert)
- [GitHub Examples](https://github.com/rush-db/examples)
