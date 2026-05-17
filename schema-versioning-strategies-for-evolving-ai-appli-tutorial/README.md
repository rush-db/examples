# Schema Versioning Strategies for Evolving AI Applications

This tutorial demonstrates how to use RushDB's flexible, zero-schema architecture to handle schema versioning in AI applications. AI systems frequently evolve: models change, new fields are introduced, legacy properties are deprecated, and data structures need to migrate while preserving history.

## What You'll Learn

- **Version tagging patterns** — Attach semantic version metadata to records for tracking
- **Migration records** — Track schema changes as first-class records in the graph
- **Rolling upgrades** — Handle mixed-version data during transitions
- **Rollback patterns** — Revert to previous schema states when migrations fail
- **Property lineage** — Track how fields evolved across versions

## Why RushDB for Schema Versioning?

Traditional databases require DDL migrations whenever schemas change. RushDB's property graph model treats schema as an emergent property:

- **No upfront schema definition** — Fields are created on first use
- **Version records** are just regular records with version metadata
- **Property relationships** capture field lineage across versions
- **Transactions** ensure atomic migration operations

## Prerequisites

- Python 3.10+
- RushDB account (free tier works)
- `rushdb>=2.0.0`

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RUSHDB_API_KEY
```

## Running the Tutorial

```bash
# Run all demonstrations
python main.py

# Run with verbose output
python main.py --verbose
```

The script will:
1. Initialize the RushDB client
2. Run schema versioning demonstrations
3. Clean up created records on completion

## Project Structure

```
schema-versioning-strategies-for-evolving-ai-appli-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py            # Sample AI model metadata generator
└── main.py            # Tutorial demonstrations
```

## Key Patterns

### 1. Version Tagging Pattern

Attach semantic version metadata to records:

```python
model = db.records.create(
    label="MODEL",
    data={
        "name": "sentiment-analyzer-v2",
        "version": "2.1.0",
        "schemaVersion": "2024.1",
        "inputFields": ["text"],
        "outputFields": ["sentiment", "confidence"]
    }
)
```

### 2. Migration Record Pattern

Track schema changes as first-class records:

```python
migration = db.records.create(
    label="SCHEMA_MIGRATION",
    data={
        "fromVersion": "2023.4",
        "toVersion": "2024.1",
        "appliedAt": datetime.utcnow().isoformat(),
        "affectedLabels": ["MODEL", "PREDICTION"],
        "addedFields": ["confidence", "modelVersion"],
        "deprecatedFields": ["score"]
    }
)
```

### 3. Rolling Upgrade Pattern

Query mixed-version data with version filtering:

```python
# Get records matching specific schema version
current = db.records.find({
    "labels": ["MODEL"],
    "where": {
        "schemaVersion": "2024.1"
    }
})

# Get legacy records needing migration
legacy = db.records.find({
    "labels": ["MODEL"],
    "where": {
        "schemaVersion": {"$lt": "2024.1"}
    }
})
```

## Cleanup

The tutorial includes automatic cleanup. To manually remove all tutorial records:

```python
db.records.delete({"labels": ["MODEL"], "where": {"tutorial": True}})
db.records.delete({"labels": ["SCHEMA_MIGRATION"], "where": {"tutorial": True}})
db.records.delete({"labels": ["PREDICTION"], "where": {"tutorial": True}})
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdks/python)
- [Schema Evolution Best Practices](https://docs.rushdb.com/concepts/schema-evolution)

## License

MIT License - See [LICENSE](../LICENSE) for details.
