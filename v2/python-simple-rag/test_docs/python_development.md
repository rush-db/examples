# Python Development with RushDB

This guide covers best practices for developing Python applications with RushDB.

## Installation and Setup

```python
# Install RushDB Python SDK
pip install rushdb

# Basic connection setup
from rushdb import RushDB

db = RushDB("your-api-token")
```

## Creating Records

RushDB supports flexible record creation with labels and arbitrary data structures:

```python
# Single record
result = db.records.create(
    label="User",
    data={"name": "John", "email": "john@example.com"}
)

# Multiple records
results = db.records.create_many(
    label="Document",
    data={
        "title": "My Document",
        "content": "Document content here",
        "Chunk": [
            {"text": "First chunk", "embedding": [0.1, 0.2, 0.3]},
            {"text": "Second chunk", "embedding": [0.4, 0.5, 0.6]}
        ]
    }
)
```

## Querying Data

RushDB provides powerful query capabilities:

```python
# Simple find
users = db.records.find({
    "labels": ["User"],
    "where": {"name": "John"}
})

# Vector search
similar_docs = db.records.find({
    "labels": ["Chunk"],
    "where": {
        "embedding": {
            "$vector": {
                "fn": "gds.similarity.cosine",
                "query": [0.1, 0.2, 0.3],
                "threshold": {"$gte": 0.5}
            }
        }
    },
    "limit": 10
})
```

## Error Handling

Always implement proper error handling when working with external APIs:

```python
try:
    result = db.records.create(label="Test", data={"key": "value"})
except Exception as e:
    print(f"Error creating record: {e}")
```
