# Graph-Structured Embedding Spaces: Modeling Concept Proximity Explicitly

A practical tutorial demonstrating how to use RushDB's property graph model to represent and query concept proximity spaces — where relationships between concepts carry as much semantic weight as the concepts themselves.

## What This Demonstrates

Traditional embedding spaces infer proximity from distributional semantics (co-occurrence). **Graph-structured embedding spaces** make proximity explicit through typed relationships, enabling:

- **Hierarchical inheritance** — concept taxonomies via `IS_A` / `PART_OF` relationships
- **Explicit similarity** — typed `RELATED_TO` edges between semantically adjacent concepts
- **Path-based traversal** — finding concepts through multi-hop relationship chains
- **Hybrid queries** — combining graph traversal with vector similarity search

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Concept Proximity Graph                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐     IS_A      ┌──────────────────┐           │
│   │   Factory    │◄─────────────│ Creational       │           │
│   │   (Pattern)  │              │ (Category)       │           │
│   └──────┬───────┘              └────────┬─────────┘           │
│          │ RELATED_TO                      │ IS_A                │
│          ▼                                ▼                     │
│   ┌──────────────┐                ┌──────────────────┐         │
│   │   Builder    │◄──RELATED_TO───│  Design Patterns  │         │
│   │   (Pattern)  │                │   (Domain)        │         │
│   └──────────────┘                └────────┬─────────┘           │
│                                           │                     │
│   ┌──────────────┐                         │ RELATED_TO         │
│   │   Adapter    │◄────────────────────────┘                    │
│   │   (Pattern)  │                                               │
│   └──────────────┘                                               │
│                                                                  │
│         ▲                                ▲                       │
│         │            RELATED_TO          │                       │
│   ┌─────────────┐                  ┌─────────────────┐          │
│   │  Monolithic │──────────────────│   Microservices  │          │
│   │  Architecture│                 │   Architecture   │          │
│   └─────────────┘                  └──────────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://rushdb.com))

## Setup

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd graph-structured-embedding-spaces-modeling-concept-tutorial

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set RUSHDB_API_KEY
```

## Running the Project

### 1. Seed the Database

```bash
python seed.py
```

This creates ~20 concept records with hierarchical and similarity relationships, forming a knowledge graph around software architecture concepts. The seed script is **idempotent** — safe to run multiple times.

### 2. Run the Tutorial

```bash
python main.py
```

Expected output demonstrates:
1. Concept hierarchy traversal (parent → child → sibling)
2. Multi-hop relationship queries (finding indirect connections)
3. Concept proximity via shared relationships
4. Hybrid queries combining graph structure with vector similarity

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Concept graph initialization script
└── main.py             # Tutorial demonstration code
```

## Key RushDB Patterns Used

| Pattern | Description |
|---------|-------------|
| `db.records.create()` | Create concept nodes |
| `db.records.attach()` | Connect concepts with typed relationships |
| `db.records.find()` with `where` | Filter concepts by related record properties |
| Transaction context managers | Atomic creation of related concepts |
| Vector embedding writes | Enable semantic similarity on concept descriptions |

## Embedding Strategy

This example uses **inline vector writes** with `vectors=[...]` parameter on `db.records.create()`. For production, either:
- Use RushDB's managed embedding service (server-side)
- Pre-compute vectors externally and write them during record creation

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Model](https://docs.rushdb.com/concepts/property-graph)
- [Vector Search](https://docs.rushdb.com/concepts/vector-search)
