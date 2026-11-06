# Neo4j to RushDB Migration: A Step-by-Step Guide

This tutorial demonstrates how to migrate a property graph from Neo4j to RushDB. We'll walk through converting Cypher-style node and relationship data into RushDB records and links.

## What You'll Learn

- How Neo4j concepts map to RushDB primitives
- Converting nodes → records with labels
- Converting relationships → links via `attach()`
- Batch migration with transactions for ACID guarantees
- Querying migrated data with relationship traversal

## Prerequisites

- Python 3.9+
- A RushDB account (free tier available at [rushdb.com](https://rushdb.com))
- API token from your RushDB dashboard

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your API token
cp .env.example .env
# Edit .env and set RUSHDB_TOKEN=your_token_here
```

## Running the Migration

```bash
# Step 1: Generate sample Neo4j export data
python seed.py

# Step 2: Run the migration
python migration.py
```

## Neo4j to RushDB Concept Mapping

| Neo4j Concept | RushDB Equivalent | Notes |
|--------------|-------------------|-------|
| Node | Record | Created via `db.records.create()` |
| Label (:Movie) | Label | First argument to `db.records.create(label="Movie", ...)` |
| Property (title, year) | Properties | Stored as fields in the record's data dict |
| Relationship (:ACTED_IN) | Link | Created via `db.records.attach(source, target, options={"type": "ACTED_IN"})` |
| Cypher MATCH | `db.records.find()` | Filter via `where` clause |
| Pattern match (MATCH (a)-[:ACTED_IN]->(b)) | Relationship traversal | RushDB auto-traverses via nested label keys |

## How It Works

### 1. Data Preparation

The migration reads Neo4j export data structured as:

```python
# Neo4j export format (simplified)
{
    "nodes": [
        {"id": "1", "labels": ["Movie"], "properties": {"title": "Inception", "year": 2010}},
        {"id": "2", "labels": ["Actor"], "properties": {"name": "Leonardo DiCaprio"}}
    ],
    "relationships": [
        {"type": "ACTED_IN", "startNode": "1", "endNode": "2", "properties": {"role": "Dom Cobb"}}
    ]
}
```

### 2. Node Migration

Each Neo4j node becomes a RushDB record:

```sdk
movie = db.records.create(
    label="Movie",
    data={"title": "Inception", "year": 2010}
)
actor = db.records.create(
    label="Actor",
    data={"name": "Leonardo DiCaprio"}
)
___SPLIT___
const movie = await db.records.create({
  label: 'Movie',
  data: { title: 'Inception', year: 2010 }
})
const actor = await db.records.create({
  label: 'Actor',
  data: { name: 'Leonardo DiCaprio' }
})
```

### 3. Relationship Migration

Neo4j relationships become RushDB links via `attach()`:

```sdk
db.records.attach(
    source=actor,
    target=movie,
    options={"type": "ACTED_IN"}
)
___SPLIT___
await db.records.attach({
  source: actor,
  target: movie,
  options: { type: 'ACTED_IN' }
})
```

### 4. Transactional Batch Processing

Group operations in transactions for atomicity:

```sdk
with db.transactions.begin() as tx:
    db.records.create(label="Movie", data={...}, transaction=tx)
    db.records.create(label="Actor", data={...}, transaction=tx)
    db.records.attach(source=actor, target=movie, options={"type": "ACTED_IN"}, transaction=tx)
___SPLIT___
const tx = await db.transactions.begin()
try {
  await db.records.create({ label: 'Movie', data: {...} }, tx)
  await db.records.create({ label: 'Actor', data: {...} }, tx)
  await db.records.attach({ source: actor, target: movie, options: { type: 'ACTED_IN' } }, tx)
  await tx.commit()
} catch (e) {
  await tx.rollback()
  throw e
}
```

## Expected Output

```
=== Neo4j to RushDB Migration ===

[1/5] Loading Neo4j export data...
  Loaded 50 nodes and 72 relationships

[2/5] Clearing existing migration records (idempotency)...
  Deleted 0 existing records

[3/5] Migrating nodes...
  ✓ Created Movie: Inception (2010)
  ✓ Created Movie: The Matrix (1999)
  ✓ Created Actor: Leonardo DiCaprio
  ✓ Created Actor: Keanu Reeves
  ✓ Created Director: Christopher Nolan
  ... (45 more records)

  Created 50 records in 1 transaction

[4/5] Migrating relationships...
  ✓ Linked Leonardo DiCaprio --ACTED_IN--> Inception (role: Dom Cobb)
  ✓ Linked Keanu Reeves --ACTED_IN--> The Matrix (role: Neo)
  ... (69 more links)

  Created 72 relationships in 1 transaction

[5/5] Verifying migration...
  ✓ Found 30 Movie records
  ✓ Found 12 Actor records
  ✓ Found 8 Director records

  Migration complete! Data verified successfully.

=== Relationship Traversal Demo ===

Query: Actors who acted in Christopher Nolan films
Result: Leonardo DiCaprio, Michael Caine, Tom Hardy
```

## Querying Migrated Data

After migration, query using RushDB's relationship-aware syntax:

```sdk
# Find all actors in movies directed by Christopher Nolan
actors = db.records.find({
    "labels": ["Actor"],
    "where": {
        "DIRECTED_BY": {
            "$relation": {"type": "DIRECTED", "direction": "in"},
            "DIRECTOR": {"$relation": {"type": "DIRECTED", "direction": "out"}},
            "name": "Christopher Nolan"
        }
    }
})
___SPLIT___
const actors = await db.records.find({
  labels: ['Actor'],
  where: {
    DIRECTED_BY: {
      $relation: { type: 'DIRECTED', direction: 'in' },
      DIRECTOR: { $relation: { type: 'DIRECTED', direction: 'out' } },
      name: 'Christopher Nolan'
    }
  }
})
```

## Project Structure

```
neo4j-to-rushdb-migration/
├── README.md
├── requirements.txt
├── .env.example
├── config.py
├── seed.py           # Generates mock Neo4j export data
├── migration.py      # Main migration script
└── data/
    └── neo4j_export.json   # Generated sample data
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [RushDB GitHub](https://github.com/rush-db/examples)
