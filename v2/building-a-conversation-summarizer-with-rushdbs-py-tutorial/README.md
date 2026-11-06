# Building a Conversation Summarizer with RushDB's Python SDK

A practical tutorial demonstrating how to build a conversation summarizer using RushDB's property graph capabilities and vector search.

## What You'll Build

A system that:
- Stores conversations as a property graph (participants → conversations → messages)
- Uses vector embeddings to enable semantic search across conversation content
- Demonstrates graph traversal to retrieve conversation context
- Summarizes conversations by aggregating related messages

## Why RushDB?

RushDB combines the power of a property graph (Neo4j) with vector search in a zero-schema API. For a conversation summarizer:

- **Graph structure** naturally models who participated in which conversation
- **Property nodes** let you filter by metadata without storing duplicates
- **Vector search** enables semantic queries like "find conversations about project planning"
- **No schema** means you can evolve your data model as needs change

## Architecture

```
┌──────────────┐       PARTICIPANT_IN       ┌─────────────────┐
│  PARTICIPANT │◄────────────────────────────│   CONVERSATION  │
│  (person)    │                             │   (thread/room) │
└──────────────┘                             └───────┬─────────┘
                                                      │
                                                      │ CONTAINS
                                                      ▼
                                              ┌───────────────┐
                                              │    MESSAGE    │
                                              │  (text, time) │
                                              └───────────────┘
```

## Setup

### Prerequisites

- Python 3.10+
- A RushDB account (Free tier: https://rushdb.com)
- `sentence-transformers` for local embeddings

### Installation

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd building-a-conversation-summarizer-with-rushdbs-py-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDBSDK_API_TOKEN
```

### Get Your RushDB API Token

1. Sign up at https://app.rushdb.com
2. Create a new project (or use existing)
3. Navigate to Settings → API Tokens
4. Copy your token and add it to `.env`

## Running the Project

### 1. Seed the Database

Generate sample conversation data:

```bash
python seed.py
```

This creates:
- 5 participants
- 8 conversations (mix of technical, project planning, and casual topics)
- ~40 messages distributed across conversations

### 2. Run the Summarizer

```bash
python main.py
```

Expected output:
```
=== Conversation Summarizer Demo ===

1. Finding conversations by participant 'alice@example.com'...
   Found 3 conversations
   - 'Project Alpha Kickoff' (6 messages)
   - 'Q4 Planning Discussion' (4 messages)
   - 'Lunch Plans' (2 messages)

2. Searching for 'database migration strategies'...
   Most relevant: 'Project Alpha Kickoff' (score: 0.847)
   Key participants: alice@example.com, bob@example.com
   Summary: Discussion about migration timeline, testing phases, and rollback procedures.

3. Finding similar conversations to 'frontend testing approaches'...
   Similar: 'Frontend Architecture Review' (score: 0.812)

4. Generating conversation summary for 'Project Alpha Kickoff'...
   Full conversation summary:
   - 6 messages between 2 participants
   - Topics covered: migration planning, timeline, testing phases
   - Key decisions: 2-week sprint for migration, need for comprehensive testing
```

## Project Structure

```
building-a-conversation-summarizer-with-rushdbs-py-tutorial/
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
├── seed.py              # Generate sample conversation data
├── main.py              # Main summarizer implementation
└── README.md            # This file
```

## Key Concepts Demonstrated

### 1. Graph Relationships

```sdk
# Link participant to conversation
db.records.attach(
    source=participant,
    target=conversation,
    options={"type": "PARTICIPANT_IN"}
)

# Link message to conversation
db.records.attach(
    source=message,
    target=conversation,
    options={"type": "CONTAINS"}
)
___SPLIT___
// TypeScript equivalent for documentation
// This project uses Python SDK only
```

### 2. Filtering by Related Records

```sdk
# Find all conversations for a specific participant
db.records.find({
    "labels": ["CONVERSATION"],
    "where": {
        "PARTICIPANT": {"$relation": {"type": "PARTICIPANT_IN", "direction": "in"}},
        "email": "alice@example.com"
    }
})
___SPLIT___
// TypeScript equivalent for documentation
```

### 3. Vector Search for Semantic Queries

```sdk
# Find conversations similar to a query
results = db.ai.search({
    "propertyName": "content",
    "query": "database migration strategies",
    "labels": ["MESSAGE"],
    "limit": 5
})
___SPLIT___
// TypeScript equivalent for documentation
```

### 4. Transactions for Atomic Operations

```sdk
with db.transactions.begin() as tx:
    conversation = db.records.create(
        label="CONVERSATION",
        data={"title": title, "created_at": timestamp},
        transaction=tx
    )
    for msg in messages:
        message = db.records.create(
            label="MESSAGE",
            data={"content": msg["content"], "timestamp": msg["timestamp"]},
            transaction=tx
        )
        db.records.attach(source=message, target=conversation, options={"type": "CONTAINS"}, transaction=tx)
    # Auto-commits on success, auto-rolls back on exception
___SPLIT___
// TypeScript equivalent for documentation
```

## Embedding Strategy

This tutorial uses **local embeddings** (`sentence-transformers/all-MiniLM-L6-v2`) because:

- No API key required for the embedding service
- Fast iteration during development
- Predictable costs (RushDB's embedding cost: 5 KU per record)

For production, you might switch to OpenAI or other hosted embedding services.

## Customization Ideas

1. **Add summarization**: Integrate an LLM API to generate AI summaries
2. **Filter by time**: Add date range filtering to find recent conversations
3. **Sentiment analysis**: Add sentiment property to messages for filtering
4. **Thread support**: Add reply-to relationships for nested conversations
5. **Multi-modal**: Store attachments as references to external storage

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdk/python)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-a-conversation-summarizer-with-rushdbs-py-tutorial)
