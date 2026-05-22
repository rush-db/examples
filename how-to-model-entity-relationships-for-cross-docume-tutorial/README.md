# How to Model Entity Relationships for Cross-Document Reference in RushDB

This project demonstrates how to use RushDB to model complex entity relationships for cross-document referencing — a common pattern in content management systems, knowledge bases, and collaborative platforms.

## What This Tutorial Covers

- **Entity creation**: Using labels to define different record types
- **Relationship modeling**: Creating directed edges between records using `attach()`
- **Cross-document queries**: Filtering records by properties of related entities
- **Graph traversal**: Querying across multiple hops in the relationship graph
- **Transactional consistency**: Ensuring atomic operations across multiple entities

## The Scenario

We build a lightweight documentation system with:

| Label | Description |
|---|---|
| `AUTHOR` | Content creators with names and expertise areas |
| `ARTICLE` | Documents with titles, content, and publication status |
| `TAG` | Categorization labels for articles |
| `CATEGORY` | High-level organizational buckets |

Relationships:

- `AUTHOR` → `ARTICLE` (WRITTEN_BY)
- `ARTICLE` → `TAG` (TAGGED_WITH)
- `ARTICLE` → `CATEGORY` (BELONGS_TO)
- `ARTICLE` → `ARTICLE` (REFERENCES) — cross-document links

## Prerequisites

- Python 3.9+
- A RushDB instance (cloud or self-hosted)
- API key from your RushDB workspace

## Setup

```bash
# Clone the repository
git clone https://github.com/rush-db/examples
cd how-to-model-entity-relationships-for-cross-docume-tutorial

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RUSHDB_TOKEN
```

## Running the Tutorial

```bash
# Seed the database with sample data (idempotent)
python seed.py

# Run the main tutorial demonstrating relationship patterns
python main.py
```

## Project Structure

```
.
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py            # Generates sample entities and relationships
└── main.py            # Tutorial demonstrating relationship modeling patterns
```

## Expected Output

Running `main.py` produces structured output showing:

1. **Entity counts** by label
2. **Related record queries** — finding articles by author email, articles with specific tags
3. **Cross-document traversal** — articles that reference other articles
4. **Relationship statistics** — how many articles each author has written

## Key Patterns Demonstrated

### Creating Entities

```sdk
author = db.records.create(
    label="AUTHOR",
    data={"name": "Alice Chen", "email": "alice@example.com", "expertise": "backend"}
)
article = db.records.create(
    label="ARTICLE",
    data={"title": "Understanding Async Patterns", "status": "published"}
)
___SPLIT___
const author = await db.records.create({
    label: "AUTHOR",
    data: { name: "Alice Chen", email: "alice@example.com", expertise: "backend" }
})
const article = await db.records.create({
    label: "ARTICLE",
    data: { title: "Understanding Async Patterns", status: "published" }
})
```

### Creating Relationships

```sdk
db.records.attach(
    source=author,
    target=article,
    options={"type": "WRITTEN_BY", "direction": "out"}
)
___SPLIT___
await db.records.attach({
    source: author,
    target: article,
    options: { type: "WRITTEN_BY", direction: "out" }
})
```

### Querying by Related Records

```sdk
# Find all articles by a specific author
articles = db.records.find({
    "labels": ["ARTICLE"],
    "where": {
        "AUTHOR": {"$relation": {"type": "WRITTEN_BY", "direction": "in"}},
        "AUTHOR": {"email": "alice@example.com"}
    }
})
___SPLIT___
// Find all articles by a specific author
const articles = await db.records.find({
    labels: ["ARTICLE"],
    where: {
        "AUTHOR": {
            $relation: { type: "WRITTEN_BY", direction: "in" },
            email: "alice@example.com"
        }
    }
})
```

### Cross-Document References

```sdk
# Link two articles together
db.records.attach(
    source=article_a,
    target=article_b,
    options={"type": "REFERENCES"}
)
___SPLIT___
await db.records.attach({
    source: articleA,
    target: articleB,
    options: { type: "REFERENCES" }
})
```

## Why This Approach?

RushDB's property graph model makes cross-document relationships first-class citizens:

1. **No joins needed**: Related records are directly connected via edges
2. **Flexible schema**: Each entity can have different properties
3. **Efficient traversal**: Neo4j powers O(1) relationship lookups
4. **Bidirectional queries**: Filter by source or target properties

This pattern scales from simple author→article to complex knowledge graphs with thousands of cross-references.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Entity Modeling Best Practices](https://docs.rushdb.com/concepts/records)
- [Relationship Query Syntax](https://docs.rushdb.com/api/records/find)
