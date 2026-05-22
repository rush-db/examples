# Cross-Document Coreference Resolution with Graph-Structured Context

A practical tutorial demonstrating how to use RushDB's property graph model for cross-document coreference resolution — the NLP task of identifying when mentions across different documents refer to the same real-world entity.

## What This Demonstrates

- **Graph-structured entity modeling**: Represent documents, mentions, and entities as interconnected graph nodes
- **Coreference chain storage**: Store coreference relationships as directed edges in the graph
- **Entity clustering**: Group mentions into canonical entities via relationship traversal
- **Cross-document resolution**: Resolve entity identity across multiple document boundaries
- **RushDB SDK patterns**: Transactions, record creation, relationship attachment, and graph traversal queries

## The Coreference Resolution Problem

In natural language, the same entity can be referenced in many ways:

| Document | Mention |
|----------|---------|
| Doc A | "The CEO announced..." |
| Doc A | "John Smith" |
| Doc A | "he" |
| Doc B | "Mr. Smith" |
| Doc B | "The executive" |

All of these refer to the same person. Cross-document coreference extends this to **multiple documents**, where "the CEO" in Doc A and "the executive" in Doc B might refer to the same real-world entity.

## Graph Model Design

```
┌─────────────┐       mentions        ┌──────────┐
│  Document   │◄─────────────────────│  Mention │
│  (source)   │                       │  (text)  │
└─────────────┘                       └────┬─────┘
                                           │
                                    refers_to (coreference)
                                           │
┌─────────────┐       canonical        ┌────▼─────┐
│  Entity     │◄─────────────────────│  Mention │
│ (resolved)  │                       │  (chain) │
└─────────────┘                       └──────────┘
```

- **Document nodes**: Source documents containing mentions
- **Mention nodes**: Individual entity mentions with position, text, and type
- **Entity nodes**: Canonical resolved entities
- **Relationships**: `MENTIONS_IN` (doc→mention), `REFERS_TO` (mention→entity), `SAME_AS` (mention→mention in coreference chain)

## Prerequisites

- Python 3.10+
- A RushDB instance (get one at [rushdb.com](https://rushdb.com))
- `pip` for package installation

## Setup

```bash
# Clone or navigate to this directory

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your RUSHDB_API_KEY
```

### Environment Variables

```env
RUSHDB_API_KEY=your_api_key_here
RUSHDB_URL=https://api.rushdb.com/api/v1  # for self-hosted instances
```

## Running the Example

### 1. Seed the database (generates sample documents with mentions)

```bash
python seed.py
```

This creates:
- 5 news articles about tech companies and executives
- ~15-20 entity mentions across documents
- Pre-resolved coreference chains linking mentions to entities

### 2. Run the main example

```bash
python main.py
```

Expected output:
```
=== Cross-Document Coreference Resolution ===

1. Loading sample documents with entity mentions...
2. Building coreference graph in RushDB...
3. Demonstrating graph traversal queries...

--- Resolved Entities ---

Entity: John Smith (ID: ...)
  Canonical mentions:
    - "John Smith" (Document: TechCorp Q4 Report)
    - "the CEO" (Document: TechCorp Q4 Report)
    - "Mr. Smith" (Document: Industry Weekly)
  Mentions in coreference chain: 3
  Cross-document: Yes (2 documents)

Entity: Sarah Chen (ID: ...)
  ...

--- Coreference Chain for 'the executive' ---
Chain: the executive -> John Smith -> Mr. Smith
Documents involved: TechCorp Q4 Report, Industry Weekly

--- Mentions grouped by entity across documents ---
Entity 'John Smith': found in 2 documents with 4 total mentions
Entity 'Sarah Chen': found in 3 documents with 5 total mentions
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generate and load sample data
├── main.py             # Main demonstration script
└── data/
    └── sample_articles.json  # Seed data (generated)
```

## Key RushDB Patterns Used

### Transaction-based bulk creation
```sdk
with db.transactions.begin() as tx:
    for mention in mentions:
        db.records.create(label="MENTION", data={...}, transaction=tx)
        db.records.attach(source=mention, target=entity, options={"type": "REFERS_TO"}, transaction=tx)
```

### Graph traversal for coreference chains
```sdk
# Find all mentions that refer to a specific entity
mentions = db.records.find({
    "labels": ["MENTION"],
    "where": {
        "ENTITY": {"$relation": {"type": "REFERS_TO", "direction": "in"}},
        "entityId": entity.id
    }
})
```

### Cross-document entity queries
```sdk
# Find entities mentioned across multiple documents
entities = db.records.find({
    "labels": ["ENTITY"],
    "where": {
        "DOCUMENT": {"$relation": {"type": "MENTIONS_IN", "direction": "in"}}
    }
})
```

## Understanding the Data Model

| Label | Purpose | Key Properties |
|-------|---------|----------------|
| `DOCUMENT` | Source article or text | `title`, `source`, `date`, `content` |
| `MENTION` | An entity reference | `text`, `type` (name/pronoun/description), `position`, `documentId` |
| `ENTITY` | Canonical resolved entity | `canonicalName`, `type` (person/org/location), `description` |

| Relationship | From → To | Purpose |
|--------------|-----------|---------|
| `MENTIONS_IN` | DOCUMENT → MENTION | Links a document to its entity mentions |
| `REFERS_TO` | MENTION → ENTITY | Associates a mention with its canonical entity |
| `SAME_AS` | MENTION → MENTION | Links mentions in the same coreference chain |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Coreference Resolution (Wikipedia)](https://en.wikipedia.org/wiki/Coreference)
- [Entity Linking Survey](https://arxiv.org/abs/2103.15110)

## License

MIT — Use freely for learning and prototyping.
