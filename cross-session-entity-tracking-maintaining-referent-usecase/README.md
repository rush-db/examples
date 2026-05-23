# Cross-Session Entity Tracking with RushDB

**Maintain referential integrity across multi-turn AI conversations**

This example demonstrates how RushDB's graph structure and vector similarity capabilities enable robust entity tracking across conversation sessions. The scenario: a customer support chatbot that maintains context about products, issues, and resolutions across multiple chat sessions.

![RushDB](https://img.shields.io/badge/RushDB-Examples-blue) ![Python](https://img.shields.io/badge/Python-3.9+-green)

## What This Solves

In AI-powered conversational interfaces, users refer to entities in varied ways:

- **Session 1**: "I need a laptop for video editing"
- **Session 2**: "The laptop I looked at last time — can you check stock?"
- **Session 3**: "That ProBook 15 — what's the warranty?"

Without proper entity resolution, the AI loses context. With RushDB:

1. **Graph edges** link conversation turns to known entities
2. **Vector embeddings** enable semantic matching of ambiguous references
3. **Subgraph retrieval** injects relevant context before each response

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  SESSION    │────▶│  MESSAGE    │────▶│   ENTITY    │
│  (conversation)     │  (utterance)│     │  (product,  │
│             │◀────│            │◀────│   user)     │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                    │
      └───────────────────┴──────────┬─────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │     ENTITY STATE (temporal)      │
                    │  (tracks how entity is referenced │
                    │   and its status over time)       │
                    └─────────────────────────────────┘
```

## Schema Design

| Label | Purpose |
|-------|---------|
| `SESSION` | A conversation context with metadata |
| `MESSAGE` | Individual utterances with timestamps |
| `PRODUCT` | Items in the catalog |
| `USER` | Customer profiles |
| `ENTITY_REFERENCE` | Tracks entity mentions with resolution |
| `PRODUCT_STATE` | Temporal state tracking for products |

| Relationship | Meaning |
|--------------|---------|
| `BELONGS_TO` | Message → Session |
| `REFERS_TO` | Message → Product/User |
| `RESOLVED_AS` | Entity reference → Product |
| `REPLIES_TO` | Message → Message |
| `MENTIONS` | Session → Product |

## Setup

### Prerequisites

- Python 3.9+
- A RushDB account ([get free API key](https://app.rushdb.com))

### Installation

```bash
# Clone the examples repository
git clone https://github.com/rush-db/examples.git
cd cross-session-entity-tracking-maintaining-referent-usecase

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RUSHDB_API_TOKEN
```

### Seed the Database

```bash
# This creates initial products and sets up vector indexes
python seed.py
```

## Running the Demo

```bash
python main.py
```

The script demonstrates a multi-turn conversation where:

1. **Session 1**: User mentions "a laptop for editing" — system resolves to ProBook 15 via semantic search
2. **Session 2**: User says "that laptop again" — system resolves via entity history, not re-embedding
3. **Context injection**: System retrieves full product subgraph before generating responses

## Expected Output

```
=== Cross-Session Entity Tracking Demo ===

[1] Creating product catalog with embeddings...
    ✓ Created product: ProBook 15 (ID: prod_xxx)
    ✓ Created product: AeroSlim 14
    ✓ Created product: PixelBook Go
    ✓ Vector index ready for semantic search

[2] Session 1: "I need a laptop for video editing"
    → Semantic query: "laptop for video editing"
    → Resolved: ProBook 15 (similarity: 0.94)
    → Context injected: {brand, specs, price, stock}

[3] Session 2: "Is the laptop I looked at still available?"
    → Entity reference: "the laptop" (ambiguous)
    → Resolution strategy: Recent session history
    → Resolved: ProBook 15
    → Status: In stock (4 units)

[4] Session 3: "What's the warranty on that ProBook?"
    → Entity reference: "that ProBook"
    → Resolution strategy: Partial match + session context
    → Resolved: ProBook 15
    → Warranty: 2 years manufacturer

=== All entities tracked across 3 sessions ===
```

## Key Patterns

### Entity Resolution Flow

```sdk
# 1. Attempt exact match first (fastest)
known_entities = db.records.find({
    "labels": ["PRODUCT"],
    "where": {"sku": "PHB15-2024"}
})

# 2. Fall back to semantic search for ambiguous references
if not known_entities:
    matches = db.ai.search({
        "propertyName": "description",
        "query": "laptop for video editing",
        "labels": ["PRODUCT"],
        "limit": 5
    })

# 3. Link resolved entity to conversation
db.records.attach(
    source=message,
    target=resolved_product,
    options={"type": "REFERS_TO"}
)
___SPLIT___
// Entity resolution in production would use similar patterns
// with the TypeScript SDK's async methods
```

### Context Injection Pattern

```sdk
def get_entity_context(product_id):
    """Retrieve full entity subgraph for context injection."""
    # Get the product
    product = db.records.find_by_id(product_id)
    
    # Find all sessions that mentioned this product
    related_sessions = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "PRODUCT": {"$id": product_id}
        }
    })
    
    # Get recent messages about this product
    messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "$or": [
                {"product_id": product_id},
                {"product_name": {"$contains": product["name"]}}
            ]
        },
        "orderBy": {"timestamp": "desc"},
        "limit": 5
    })
    
    return {
        "product": product,
        "session_history": related_sessions,
        "recent_messages": messages
    }
___SPLIT___
// TypeScript implementation
async function getEntityContext(db, productId: string) {
  const product = await db.records.findById(productId);
  
  const relatedSessions = await db.records.find({
    labels: ['SESSION'],
    where: { PRODUCT: { $id: productId } }
  });
  
  return { product, relatedSessions };
}
```

## Files

| File | Purpose |
|------|---------|
| `main.py` | End-to-end demonstration of entity tracking flow |
| `seed.py` | Sets up products, vector index, and sample data |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

## Related Documentation

- [RushDB Python SDK](https://docs.rushdb.com/sdk/python/)
- [Vector Search](https://docs.rushdb.com/features/vector-search/)
- [Property Graph Model](https://docs.rushdb.com/concepts/)
- [Transaction Management](https://docs.rushdb.com/sdk/python/#transactions)

## License

MIT — use freely in your projects.
