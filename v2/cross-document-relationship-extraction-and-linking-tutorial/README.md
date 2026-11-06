# Cross-Document Relationship Extraction and Linking

A hands-on tutorial demonstrating how to build a cross-document entity linking pipeline using RushDB's unified graph + vector architecture.

## What You'll Build

This tutorial shows how to extract entities from academic papers, resolve coreferences, disambiguate mentions using vector similarity, and query complex relationship patterns — all within a single system.

## Architecture

```
DOCUMENT ──AUTHORED_BY──► PERSON
    │                        │
    │                    CO_AUTHOR_OF
    │                        │
    └───CITES───────────────►DOCUMENT
           (resolved via entity linking)
```

**Key insight**: RushDB stores nodes, edges, AND vectors in the same record — no ETL between a graph database and a vector store.


## Prerequisites

- Python 3.10+
- RushDB API key ([get one free](https://rushdb.com))
- `spacy` and a trained NER model
- `sentence-transformers` for embeddings

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy NER model
python -m spacy download en_core_web_sm

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your RUSHDB_API_KEY

# Seed the database with academic paper data
python seed.py
```

## Running the Tutorial

```bash
python main.py
```

The script demonstrates:
1. **Schema design** — creating document and entity nodes
2. **Entity extraction** — NER pipeline integration with spaCy
3. **Coreference resolution** — linking "John", "Dr. Smith", "the lead author" to one entity
4. **Vector disambiguation** — resolving same-name conflicts via cosine similarity
5. **Complex queries** — finding co-authors through citation chains

## Expected Output

```
=== Cross-Document Entity Linking Pipeline ===

[1] Schema & Data Loading
    ✓ Loaded 5 academic papers
    ✓ Found 12 author mentions across documents

[2] Entity Extraction (NER)
    ✓ Extracted 8 PERSON entities
    ✓ Extracted 3 ORG entities

[3] Coreference Resolution
    ✓ Resolved 3 co-referent clusters
    • "John" → "Dr. John Chen" (confidence: 0.92)
    • "the lead author" → "Dr. John Chen" (confidence: 0.88)
    • "Prof. Chen" → "Dr. John Chen" (confidence: 0.91)

[4] Vector Disambiguation
    ✓ Disambiguated "Dr. Sarah Kim" (university researcher vs. industry)
    • Using semantic similarity on institution context
    • Selected candidate: MIT researcher (similarity: 0.87)

[5] Complex Relationship Query
    Query: Find all co-authors of papers where the second author 
           cited someone who was cited by "Dr. John Chen"
    
    Results:
    ├─ Dr. Sarah Kim (MIT)
    │  └─ via citation chain: Chen → [A] → Kim
    ├─ Prof. Michael Torres (Stanford)  
    │  └─ via citation chain: Chen → [B] → Torres
    └─ Dr. Lisa Patel (Oxford)
       └─ via citation chain: Chen → [A] → Patel

[6] Knowledge Graph Summary
    • 5 DOCUMENT nodes
    • 8 PERSON nodes (entity canonical forms)
    • 23 relationship edges
    • 3 resolved coreference clusters
```

## How It Works

### 1. Schema Design

We model documents as `DOCUMENT` nodes, people as `PERSON` nodes, and relationships as typed edges:

```sdk
# Create a paper document
paper = db.records.create(
    label="DOCUMENT",
    data={
        "title": "Neural Approaches to Entity Resolution",
        "year": 2024,
        "abstract": "..."
    }
)

# Create an author entity
author = db.records.create(
    label="PERSON",
    data={
        "name": "Dr. Sarah Kim",
        "canonicalName": "Sarah Kim",
        "institution": "MIT"
    }
)

# Link author to document
db.records.attach(
    source=paper,
    target=author,
    options={"type": "AUTHORED_BY", "direction": "out"}
)
```

### 2. NER Pipeline Integration

We use spaCy to extract entities, then create RushDB records for each:

```python
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    doc = nlp(text)
    return [
        {"text": ent.text, "label": ent.label_, "start": ent.start_char}
        for ent in doc.ents
    ]
```

### 3. Coreference Resolution

Simple heuristic-based coreference: we cluster mentions by:
- Exact name match
- Last name match
- Title variations ("Dr.", "Prof.", "Mr.")
- Contextual cues ("the lead author", "the corresponding author")

```python
def resolve_coreference(mentions):
    clusters = {}
    for mention in mentions:
        # Group by normalized last name
        normalized = normalize_name(mention["text"])
        if normalized in clusters:
            clusters[normalized].append(mention)
        else:
            clusters[normalized] = [mention]
    return clusters
```

### 4. Vector Disambiguation

When two `PERSON` records share a name, we use vector similarity on their context (institution, co-authors, publication history) to determine if they're the same person or different people:

```sdk
# Create vector index on person descriptions
index = db.ai.indexes.create({
    "label": "PERSON",
    "propertyName": "embeddingContext",
    "sourceType": "external",
    "dimensions": 384
})

# Find candidates for "Dr. Sarah Kim"
results = db.ai.search({
    "propertyName": "embeddingContext",
    "queryVector": query_vector,
    "labels": ["PERSON"],
    "where": {"name": {"$contains": "Sarah Kim"}},
    "limit": 5
})
```

### 5. Complex Graph Queries

The thesis query: "Find all co-authors of papers where the second author cited someone who was cited by X"

```sdk
# Step 1: Find papers authored by Dr. John Chen
papers_by_chen = db.records.find({
    "labels": ["DOCUMENT"],
    "where": {"PERSON": {"name": "Dr. John Chen"}}
})

# Step 2: Find documents cited by these papers
cited_by_chen = db.records.find({
    "labels": ["DOCUMENT"],
    "where": {
        "DOCUMENT": {"$relation": {"type": "CITES", "direction": "in"}}
    }
})

# Step 3: Find second authors of papers citing Chen's citations
second_authors = db.records.find({
    "labels": ["PERSON"],
    "where": {
        "DOCUMENT": {
            "$relation": {"type": "AUTHORED_BY", "direction": "in"},
            "authorPosition": 2,
            "$id": {"$in": [d.id for d in cited_by_chen]}
        }
    }
})
```

## Project Structure

```
cross-document-relationship-extraction-and-linking-tutorial/
├── README.md
├── requirements.txt
├── .env.example
├── seed.py           # Generates mock academic paper data
├── main.py           # Complete tutorial implementation
└── data/
    └── papers.json   # Seed data for papers/authors/citations
```

## Key Takeaways

1. **Unified storage**: RushDB treats vectors as first-class data — no separate vector database required
2. **Schema flexibility**: Zero-schema API allows adding entity types without migration
3. **Query expressiveness**: Graph traversal + vector similarity in one query language
4. **Real-time linking**: Coreference and disambiguation happen at write time, not ETL

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/cross-document-relationship-extraction-and-linking-tutorial)
- [Pricing](https://rushdb.com/pricing) — Free tier includes full API access

## License

MIT