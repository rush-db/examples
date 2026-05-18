# Personalization Engines: Graph-Based User Preference Modeling

A practical tutorial demonstrating how to build a graph-based personalization engine using RushDB. This project shows how to model user preferences as a property graph, enabling sophisticated recommendation patterns through relationship traversal.

## What This Demonstrates

- **Graph data modeling** for user preferences and item relationships
- **RushDB property graph API** for creating records and relationships
- **Collaborative filtering** patterns using graph traversal
- **Transaction-based writes** for data integrity
- **Preference scoring** through relationship aggregation

## Architecture Overview

```
┌─────────────┐       VIEWED/PURCHASED/RATED       ┌─────────────┐
│    USER     │◄─────────────────────────────────►│    ITEM     │
│  preferences│         interacted_with           │  category   │
│  profile    │                                   │  tags       │
└─────────────┘                                   └─────────────┘
       │                                                    │
       │              SIMILAR_TO                           │
       └───────────────────►───────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- A RushDB project (free tier at [rushdb.com](https://rushdb.com))
- `RUSHDB_API_KEY` from your project dashboard

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY

# Seed the database with sample data
python seed.py
```

## Running

```bash
# Run the main demonstration
python main.py
```

Expected output includes:
- Creating users and items
- Building interaction graph
- Finding collaborative filtering recommendations
- Getting personalized suggestions

## Project Structure

| File | Purpose |
|------|---------|
| `seed.py` | Generates 20 users, 50 items, and ~200 interactions |
| `main.py` | Demonstrates preference queries and recommendations |
| `requirements.txt` | Dependencies including RushDB SDK |
| `.env.example` | Required environment variables |

## Key Patterns

### Creating a Preference Relationship

```sdk
# Attach user preference to item
db.records.attach(
    source=user,
    target=item,
    options={"type": "INTERACTED_WITH", "direction": "out"}
)
___SPLIT___
// Not applicable - Python demonstration
```

### Finding Similar Users (Collaborative Filtering)

```sdk
# Find users who interacted with the same items
db.records.find({
    "labels": ["USER"],
    "where": {
        "INTERACTED_WITH": {
            "$relation": {"type": "INTERACTED_WITH", "direction": "in"},
            "ITEM": {"category": "electronics"}
        }
    }
})
___SPLIT___
// Not applicable - Python demonstration
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Modeling](https://docs.rushdb.com)
- [GitHub Examples](https://github.com/rush-db/examples)
