# Versioning Graph Schemas in Production Environments

A practical guide and runnable code for managing schema evolution in RushDB-powered production systems.

## What This Tutorial Demonstrates

- **Zero-downtime schema migrations** using labels as versioned namespaces
- **Audit trail patterns** for tracking schema changes over time
- **Backward-compatible evolution** via optional properties and type-safe versioning
- **Migration orchestration** using RushDB transactions
- **Ontology-driven schema inspection** via `db.ai.getOntology()`

## The Problem

In production graph systems, schemas evolve constantly: new product attributes, new user fields, renamed relationships. RushDB's zero-schema philosophy means you can start writing immediately — but as the system grows, you need structure to manage that evolution safely across multiple services and deployments.

## Key Concepts

| Pattern | Description |
|---|---|
| **Label Versioning** | Append version suffixes to labels (`PRODUCT_V2`) for major breaking changes |
| **Property Aliasing** | Shadow-migrate properties by writing both old and new keys during transition |
| **Migration Records** | Track migrations as first-class graph records with status and timestamps |
| **Migration Registry** | Maintain a central record that maps schema versions to active labels |
| **Ontology Snapshots** | Periodically capture `db.ai.getOntology()` output as schema documentation |

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works) — [sign up](https://rushdb.com)
- `rushdb>=2.0.0` Python SDK

## Setup

```bash
# Clone the repo and enter this directory
git clone https://github.com/rush-db/examples
cd versioning-graph-schemas-in-production-environment-tutorial

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and set RUSHDB_API_KEY=<your-key>
```

## Running

### 1. Seed the database (creates sample e-commerce schema)

```bash
python seed.py
```

This creates:
- `PRODUCT_V1`, `CATEGORY_V1`, `USER_V1`, `ORDER_V1` records
- Sample data across all entity types
- A `SCHEMA_VERSION` registry record
- A migration audit trail as `MIGRATION` records

### 2. Run the main tutorial

```bash
python main.py
```

The script walks through a realistic evolution scenario:

| Phase | What Happens |
|---|---|
| **Phase 1** | Inspect current ontology, list all labels |
| **Phase 2** | Add `PRODUCT_V2` with new fields (`tags`, `origin_country`, `sustainability_score`) |
| **Phase 3** | Migrate existing products — write both V1 and V2 fields |
| **Phase 4** | Verify migration, query mixed-version records |
| **Phase 5** | Attach migration metadata as a graph audit trail |
| **Phase 6** | Mark old version deprecated in registry |

### 3. Inspect your schema

```bash
# View all labels and their property counts
python -c "
from rushdb import RushDB
from dotenv import load_dotenv
load_dotenv()
db = RushDB(__import__('os').environ['RUSHDB_API_KEY'])
print(db.ai.getOntologyMarkdown())
"
```

## Expected Output

```
============================================================
  PHASE 1: Schema Inspection
============================================================
Current ontology snapshot:
- CATEGORY_V1 (4 records)
- PRODUCT_V1 (20 records)
- USER_V1 (50 records)
- ORDER_V1 (40 records)
- SCHEMA_VERSION (1 record)
- MIGRATION (2 records)

Registry: schema_version=1.0.0
Active product label: PRODUCT_V1

============================================================
  PHASE 2: Creating PRODUCT_V2
============================================================
Created 20 PRODUCT_V2 records via bulk upsert
New properties detected: tags, origin_country, sustainability_score

============================================================
  PHASE 3: Migration (V1 → V2)
============================================================
Migrating 20 PRODUCT records...
[100%] Migrated 20/20 products in 0 transactions

============================================================
  PHASE 4: Verification
============================================================
PRODUCT_V1 remaining: 0
PRODUCT_V2 total: 20
All V2 products have sustainability_score: ✓

============================================================
  PHASE 5: Audit Trail
============================================================
Migration record created: MIGRATION_{uuid}
Status: completed, duration=0.42s

============================================================
  PHASE 6: Registry Update
============================================================
Registry updated: activeLabel=PRODUCT_V2, version=2.0.0
Old PRODUCT_V1 records marked deprecated (not deleted)

Final ontology:
- CATEGORY_V1
- PRODUCT_V1 (deprecated, 0 active records)
- PRODUCT_V2 (20 records) ← current
- USER_V1
- ORDER_V1
```

## Project Structure

```
versioning-graph-schemas-in-production-environment-tutorial/
├── README.md
├── requirements.txt
├── .env.example
├── seed.py          # Creates initial e-commerce dataset with V1 schema
└── main.py          # Full schema evolution walkthrough
```

## Architecture Decisions

### Why labels as version namespaces?

RushDB labels are first-class citizens with no schema enforcement. Using `PRODUCT_V1`, `PRODUCT_V2` as separate labels lets multiple services coexist during migration windows — no coordination required, no downtime.

### Why not delete old records?

Graph data's value is in its relationships. Deleting `PRODUCT_V1` orphanates all `ORDERED` edges. Instead, mark the label as deprecated and route new writes to `PRODUCT_V2` via the registry record.

### Why transactions for migration?

Bulk migrations wrapped in a transaction guarantee atomicity: if any write fails, the entire migration rolls back. RushDB transactions cover all operations including `db.records.create()`, `db.records.upsert()`, and relationship creation.

## Further Reading

- [RushDB Python SDK docs](https://docs.rushdb.com/sdk/python/)
- [RushDB Graph Concepts](https://docs.rushdb.com/concepts/)
- [Schema Migration Patterns — RushDB Blog](https://rushdb.com/blog)
