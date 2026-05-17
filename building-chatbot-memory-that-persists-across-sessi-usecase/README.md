# Building Chatbot Memory That Persists Across Sessions

A production-ready implementation of persistent, cross-session chatbot memory using RushDB's graph structure and vector search.

## What This Demo Shows

- **Schema Design**: Graph hierarchy (User → Session → Message) with ExtractedEntity nodes
- **Vector Embeddings**: Semantic search across message content without loading entire chat logs
- **Entity Memory**: Extract and retrieve user facts (e.g., "my cat Luna") for personalized responses
- **Context Retrieval**: Combine graph traversal with semantic search in a single query
- **Production Patterns**: Concurrent writes, pagination, TTL strategies for session expiry

## Architecture

```
┌─────────┐      has_session       ┌─────────┐
│  User   │ ──────────────────────►│ Session │
└─────────┘                       └────┬────┘
      │                                    │
      │ knows_about                        │ contains
      ▼                                    ▼
┌───────────────┐                   ┌─────────────┐
│ ExtractedEntity│                 │   Message   │
│ (cat Luna,    │                  │ (vectors on │
│  preferences) │                  │  content)   │
└───────────────┘                   └─────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account and API key ([get one here](https://dash.rushdb.com))

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### 3. Generate Mock Data (Optional)

```bash
python seed.py
```

This creates:
- 2 demo users (Alice and Bob)
- 4 sessions per user with realistic conversation history
- ~50 messages with varied topics (greetings, tech questions, personal)
- Extracted entities (pet names, preferences, context facts)

The seed script is **idempotent** — safe to run multiple times.

## Running the Demo

```bash
python main.py
```

### What You'll See

1. **Schema initialization** — vector index creation for semantic search
2. **User and session setup** — demonstrating the graph hierarchy
3. **Message ingestion** — creating messages with embedded vectors
4. **Entity extraction** — capturing "my cat Luna" style facts
5. **Context retrieval** — combining recent sessions with semantic search
6. **Entity recall** — "what does the user know about their pets?"

## Key Code Patterns

### Creating a Message with Vector Embedding

```sdk
# Inline vector writes on create
message = db.records.create(
    label="Message",
    data={"role": "user", "content": "Hello, how are you?"},
    vectors=[{"propertyName": "content", "vector": embedding}],
    transaction=tx
)
db.records.attach(source=session, target=message, options={"type": "CONTAINS"}, transaction=tx)
___SPLIT___
// Not applicable — Python example shown
```

### Semantic Search Within a Session

```sdk
results = db.ai.search({
    "propertyName": "content",
    "query": "questions about my Python project",
    "labels": ["Message"],
    "where": {
        "SESSION": {
            "$relation": {"type": "CONTAINS", "direction": "out"},
            "userId": user.id
        }
    },
    "limit": 5
})
___SPLIT___
// Not applicable — Python example shown
```

### Entity Extraction and Retrieval

```sdk
# Extract: "I have a cat named Luna"
entity = db.records.create(
    label="ExtractedEntity",
    data={"type": "pet", "name": "Luna", "category": "cat"},
    transaction=tx
)
db.records.attach(source=user, target=entity, options={"type": "KNOWS_ABOUT"}, transaction=tx)

# Later retrieve: "what pets does Alice have?"
pets = db.records.find({
    "labels": ["ExtractedEntity"],
    "where": {
        "User": {"$relation": {"type": "KNOWS_ABOUT", "direction": "in"}, "id": user.id},
        "category": "pet"
    }
})
___SPLIT___
// Not applicable — Python example shown
```

## Production Considerations

### Concurrent Message Writes

Use transactions to batch writes:

```python
with db.transactions.begin() as tx:
    for msg_data in messages:
        msg = db.records.create(label="Message", data=msg_data, transaction=tx)
        db.records.attach(source=session, target=msg, options={"type": "CONTAINS"}, transaction=tx)
    # Auto-commits on clean exit
```

### Pagination Through Long Conversations

```python
# Get messages 21-40 from a session
messages = db.records.find({
    "labels": ["Message"],
    "where": {
        "SESSION": {"$relation": {"type": "CONTAINS", "direction": "in"}, "id": session.id}
    },
    "skip": 20,
    "limit": 20,
    "orderBy": {"createdAt": "asc"}
})
```

### TTL Strategies for Old Sessions

```python
# Set expiration when creating session
session = db.records.create(
    label="Session",
    data={
        "title": "Support Chat",
        "status": "active",
        "ttl_expires_at": datetime.now() + timedelta(days=30)  # 30-day retention
    }
)

# Query for expired sessions
expired = db.records.find({
    "labels": ["Session"],
    "where": {"status": "closed", "ttl_expires_at": {"$lt": datetime.now()}}
})
```

## Embedding Strategy

This demo uses a **deterministic hash-based embedding** for demonstration purposes. It produces consistent 384-dimensional vectors from message content without requiring an external embedding service.

For production, replace `generate_embedding()` with:

- **OpenAI**: `openai.embeddings.create(model="text-embedding-3-small", input=text)`
- **Sentence Transformers**: `model.encode(text, normalize_embeddings=True)`

The vector index is configured for 384 dimensions to match the hash-based embeddings.

## Cleanup

To remove all demo data:

```python
db.records.delete_many({"labels": ["Message", "Session", "User", "ExtractedEntity"], "where": {}})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub](https://github.com/rush-db/examples)
- [Graph-Based Memory Patterns](https://docs.rushdb.com/concepts/property-graph)
