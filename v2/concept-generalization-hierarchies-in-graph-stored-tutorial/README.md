# Concept Generalization Hierarchies in Graph-Stored Embeddings

A practical tutorial demonstrating how to build and query concept generalization hierarchies using RushDB's property graph and vector search capabilities.

## Overview

Concept generalization hierarchies organize knowledge from specific to abstract:

```
Living Thing
    └── Animal
        └── Mammal
            └── Dog
                └── Golden Retriever
```

This tutorial shows how to:
1. Store concepts with vector embeddings in a graph structure
2. Build IS_A generalization relationships
3. Traverse hierarchies (ancestors, descendants, siblings)
4. Use semantic search to discover related concepts across the hierarchy
5. Leverage graph traversal for generalization/specialization queries

## Prerequisites

- Python 3.10+
- RushDB account (Free tier available at https://rushdb.com)
- `sentence-transformers` for generating embeddings

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### 3. Seed the database (creates concept hierarchy with ~50 concepts)

```bash
python seed.py
```

Expected output:
```
🌱 Seeding concept hierarchy...
✅ Created 48 concept records
✅ Created 47 IS_A relationships
✅ Created 3 level-0 roots (Living Thing, Information, Artifact)
✅ Seeding complete!
```

### 4. Run the main demonstration

```bash
python main.py
```

Expected output:
```
=== Concept Generalization Hierarchies Demo ===

1. All Root Concepts (top-level abstractions):
   - Living Thing (level 0, 6 descendants)
   - Information (level 0, 4 descendants)
   - Artifact (level 0, 2 descendants)

2. Descendants of 'Dog':
   - Golden Retriever
   - German Shepherd
   - Poodle

3. Full Ancestor Chain for 'Golden Retriever':
   Living Thing → Animal → Mammal → Dog → Golden Retriever

4. Siblings of 'German Shepherd' (same parent 'Dog'):
   - Golden Retriever
   - Poodle

5. Semantic Search: concepts similar to 'pet that retrieves'
   Top 3 results:
   - Golden Retriever (score: 0.89)
   - Dog (score: 0.76)
   - Mammal (score: 0.65)

6. Generalization Query: find all descendants of 'Mammal'
   - Dog
   - Cat
   - Horse
   - Whale

7. Specialization Query: concepts directly below 'Animal'
   - Mammal
   - Bird
   - Fish
```

## Project Structure

```
.
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── seed.py            # Creates the concept hierarchy
└── main.py            # Demonstrates hierarchy queries
```

## Key Concepts Demonstrated

### 1. Graph-Based Hierarchy Storage

Concepts are stored as RushDB records with labels, connected via directed IS_A relationships:

```sdk
# Python — 4-space indentation
concept = db.records.create(
    label="CONCEPT",
    data={
        "name": "Golden Retriever",
        "level": 4,
        "definition": "A breed of dog known for retrieving game"
    },
    vectors=[{"propertyName": "definition", "vector": embedding}]
)

# Link to parent via IS_A relationship
db.records.attach(
    source=concept,        # child
    target=parent_concept, # parent
    options={"type": "IS_A", "direction": "out"}
)
___SPLIT___
// TypeScript — 2-space indentation
const concept = await db.records.create({
  label: 'CONCEPT',
  data: {
    name: 'Golden Retriever',
    level: 4,
    definition: 'A breed of dog known for retrieving game'
  }
})

await db.records.attach({
  source: concept,
  target: parentConcept,
  options: { type: 'IS_A', direction: 'out' }
})
```

### 2. Hierarchy Traversal

Find all descendants of a concept by traversing IS_A relationships:

```sdk
# Python — 4-space indentation
def get_descendants(db, concept_id):
    """Find all concepts that inherit from this concept."""
    result = db.records.find({
        "labels": ["CONCEPT"],
        "where": {
            "CONCEPT": {
                "$relation": {"type": "IS_A", "direction": "in"},
                "$id": concept_id
            }
        }
    })
    return result.data
___SPLIT___
// TypeScript — 2-space indentation
async function getDescendants(db: RushDB, conceptId: string) {
  const result = await db.records.find({
    labels: ['CONCEPT'],
    where: {
      CONCEPT: {
        $relation: { type: 'IS_A', direction: 'in' },
        $id: conceptId
      }
    }
  })
  return result.data
}
```

### 3. Semantic Search Across Hierarchy

Use vector similarity to find conceptually related nodes regardless of hierarchy position:

```sdk
# Python — 4-space indentation
results = db.ai.search({
    "propertyName": "definition",
    "query": "pet that retrieves game",
    "labels": ["CONCEPT"],
    "limit": 5
})

for record in results.data:
    print(f"{record['name']} (score: {record.score:.2f})")
___SPLIT___
// TypeScript — 2-space indentation
const results = await db.ai.search({
  propertyName: 'definition',
  query: 'pet that retrieves game',
  labels: ['CONCEPT'],
  limit: 5
})

for (const record of results.data) {
  console.log(`${record.name} (score: ${record.score.toFixed(2)})`)
}
```

## Embedding Strategy

We use `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) because:
- Fast inference for real-time use
- Good semantic understanding for general concepts
- Lightweight model suitable for tutorials
- Free and open source

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Data Modeling Guide](https://docs.rushdb.com/concepts/graph)
- [Vector Search Guide](https://docs.rushdb.com/concepts/vector-search)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/concept-generalization-hierarchies-in-graph-stored-tutorial)
