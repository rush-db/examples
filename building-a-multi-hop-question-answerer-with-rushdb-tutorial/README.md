# Building a Multi-Hop Question Answerer with RushDB's Traversal API

This project demonstrates how to build a multi-hop question answering system using RushDB's Traversal API. Each hop traverses the knowledge graph to find related entities, chaining semantic search results through graph relationships.

## What You'll Build

A working Q&A system that answers complex questions like "What organizations are located in cities where AI researchers work?" by:

1. **Single-hop search**: Finding records via semantic similarity
2. **Two-hop traversal**: Chaining through relationships (Person → Organization)
3. **Parameterized N-hop**: Reusing the same query function for any number of hops
4. **Result ranking**: Scoring based on accumulated similarity and temporal properties

## Prerequisites

- Python 3.9+
- RushDB account with an API key ([sign up](https://rushdb.com))
- `sentence-transformers` for local embedding generation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHD_API_KEY
```

### 3. Seed the Knowledge Graph

This creates ~20 records across 3 entity types (Person, Organization, Location) with relationship edges:

```bash
python seed.py
```

Expected output:
```
Creating knowledge graph with 22 records and 18 relationships...
✓ Seeded 6 Person records
✓ Seeded 5 Organization records
✓ Seeded 5 Location records
✓ Created 14 relationship edges
✓ Indexed 22 records for vector search
Knowledge graph seeded successfully!
```

### 4. Run the Multi-Hop Q&A System

```bash
python main.py
```

Expected output:
```
=== Single-Hop Query ===
Query: "AI researcher" (1 hop)
Top 3 results:
  1. [score=0.892] Person: Dr. Sarah Chen | MIT
  2. [score=0.871] Person: Michael Rodriguez | Google
  3. [score=0.845] Person: Emma Wilson | Stanford

=== Two-Hop Query ===
Query: "AI researcher" (2 hops: Person → Organization)
Question: What organizations do AI researchers work at?
Top 3 results:
  1. [score=0.824] Organization: MIT | Cambridge
  2. [score=0.801] Organization: Google | Mountain View
  3. [score=0.778] Organization: Stanford University | Stanford

=== Three-Hop Query ===
Query: "AI researcher" (3 hops: Person → Organization → Location)
Question: What cities host organizations with AI researchers?
Top 3 results:
  1. [score=0.756] Location: Cambridge, MA | 92.8 (score)
  2. [score=0.734] Location: Mountain View, CA | 89.1 (score)
  3. [score=0.712] Location: Stanford, CA | 87.4 (score)

=== Four-Hop with Ranking ===
Query: "AI researcher" (4 hops with temporal ranking)
Top 2 results:
  1. [score=0.912] Person: Dr. Sarah Chen | MIT
     Temporal score: 0.95 (recent collaboration)
  2. [score=0.889] Person: Michael Rodriguez | Google
     Temporal score: 0.91 (recent collaboration)
```

## Project Structure

```
building-a-multi-hop-question-answerer-with-rushdb-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py            # Knowledge graph seeding script
└── main.py            # Multi-hop Q&A implementation
```

## How It Works

### Step 1: Knowledge Graph Schema

```
┌─────────────┐         ┌───────────────┐         ┌────────────┐
│   Person    │─────────▶│ Organization  │─────────▶│  Location  │
├─────────────┤          ├───────────────┤          ├────────────┤
│ name        │ WORKS_AT │ name          │ LOCATED  │ city       │
│ description │          │ description   │ _IN      │ description│
│ expertise   │          │ founded       │          │ population │
│ collaboration│         │ industry      │          │            │
│   _score    │          │    _score     │          │   _score   │
└─────────────┘          └───────────────┘          └────────────┘
     │                                                ▲
     │ KNOWS                                         │ VISITED
     ▼                                                │
┌─────────────┐                                        │
│   Person    │────────────────────────────────────────┘
└─────────────┘
```

### Step 2: Single-Hop Vector Search

```sdk
# Find people matching "AI researcher" description
candidates = db.ai.search({
    "propertyName": "description",
    "query": query_text,
    "labels": ["PERSON"],
    "limit": 10
})
___SPLIT___
// TypeScript
const candidates = await db.ai.search({
  propertyName: 'description',
  query: queryText,
  labels: ['PERSON'],
  limit: 10
})
```

### Step 3: Two-Hop Traversal

```sdk
# From candidates, find their WORKS_AT organizations
person_ids = [c.id for c in candidates]

organizations = db.records.find({
    "labels": ["ORGANIZATION"],
    "where": {
        "PERSON": {
            "$relation": {"type": "WORKS_AT", "direction": "in"},
            "$id": {"$in": person_ids}
        }
    },
    "limit": 10
})
___SPLIT___
// TypeScript
const organizations = await db.records.find({
  labels: ['ORGANIZATION'],
  where: {
    PERSON: {
      $relation: {type: 'WORKS_AT', direction: 'in'},
      $id: {$in: personIds}
    }
  },
  limit: 10
})
```

### Step 4: Parameterized N-Hop

```sdk
def multi_hop_search(query_text, num_hops=2, labels=None):
    """Reusable multi-hop query function."""
    hops = ["PERSON", "ORGANIZATION", "LOCATION"]
    labels = labels or hops[:num_hops]
    
    # Start with semantic search
    candidates = db.ai.search({
        "propertyName": "description",
        "query": query_text,
        "labels": [labels[0]],
        "limit": 10
    })
    current_ids = [r.id for r in candidates]
    
    # Traverse each remaining hop
    for hop_label in labels[1:]:
        prev_label = hops[hops.index(hop_label) - 1]
        current_ids = _traverse_hop(current_ids, prev_label, hop_label)
    
    return db.records.find_by_id(current_ids)
___SPLIT___
// TypeScript
async function multiHopSearch(
  queryText: string,
  numHops: number = 2,
  labels?: string[]
): Promise<Record[]> {
  const hops = ['PERSON', 'ORGANIZATION', 'LOCATION'];
  const targetLabels = labels || hops.slice(0, numHops);
  
  // Semantic search for initial candidates
  const candidates = await db.ai.search({
    propertyName: 'description',
    query: queryText,
    labels: [targetLabels[0]],
    limit: 10
  });
  let currentIds = candidates.data.map(r => r.id);
  
  // Traverse each remaining hop
  for (let i = 1; i < targetLabels.length; i++) {
    currentIds = await traverseHop(
      currentIds,
      hops[i - 1],
      targetLabels[i]
    );
  }
  
  return db.records.findById(currentIds);
}
```

### Step 5: Temporal Ranking

```sdk
def rank_by_temporal(results, date_field="collaboration_date"):
    """Rank results by temporal properties."""
    scored = []
    for record in results:
        score = record.score or 0
        date = record.get(date_field)
        if date:
            days_ago = (datetime.now() - date).days
            recency = max(0, 1 - (days_ago / 365))
            score = score * 0.7 + recency * 0.3
        scored.append((score, record))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored]
___SPLIT___
// TypeScript
function rankByTemporal(results: Record[], dateField = 'collaboration_date'): Record[] {
  const scored = results.map(record => {
    let score = record.score || 0;
    const date = record.data[dateField];
    if (date) {
      const daysAgo = (Date.now() - new Date(date).getTime()) / (1000 * 60 * 60 * 24);
      const recency = Math.max(0, 1 - (daysAgo / 365));
      score = score * 0.7 + recency * 0.3;
    }
    return { score, record };
  });
  
  return scored
    .sort((a, b) => b.score - a.score)
    .map(item => item.record);
}
```

## Key Concepts

### RushDB Relationship Syntax

In RushDB, you filter records by related record properties using the related record's **label** as the key in the `where` clause:

```python
# Find all PERSON records that have a WORKS_AT relationship to ORGANIZATION records
db.records.find({
    "labels": ["PERSON"],
    "where": {
        "ORGANIZATION": {"description": "tech company"}
    }
})

# Explicit relationship type and direction
db.records.find({
    "labels": ["ORGANIZATION"],
    "where": {
        "PERSON": {
            "$relation": {"type": "WORKS_AT", "direction": "in"},
            "$id": {"$in": [...]}
        }
    }
})
```

### Why This Matters

Traditional databases require multiple queries and manual joining for multi-hop questions. RushDB's Traversal API lets you:

1. **Start from semantic search**: Find initial candidates by meaning, not just keywords
2. **Chain relationships**: Traverse graph edges in a single query structure
3. **Accumulate scores**: Weight earlier hops more heavily (semantic → graph)
4. **Parameterize hops**: Reuse one function for any depth of traversal

## Cleanup

To remove seeded data and the vector index:

```python
from rushdb import RushDB
db = RushDB(os.getenv("RUSHD_API_KEY"))

# Delete all seeded records
db.records.delete({"labels": ["PERSON", "ORGANIZATION", "LOCATION"], "where": {}})

# Delete vector index
indexes = db.ai.indexes.find()
for idx in indexes.data:
    db.ai.indexes.delete(idx['__id'])
```

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [Traversal API Reference](https://docs.rushdb.com/api/records/find)
- [Vector Search Guide](https://docs.rushdb.com/features/vector-search)
