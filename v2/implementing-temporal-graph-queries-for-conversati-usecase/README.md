# Implementing Temporal Graph Queries for Conversation History Tracking

This project demonstrates how a graph database approach solves the structural problem of interconnected, time-ordered conversation data — something document stores and relational tables handle poorly.

## The Problem with Traditional Approaches

**Document stores** (MongoDB, Firestore) store conversations as arrays of messages:
```json
// conversations collection
{
  "_id": "conv_123",
  "messages": [
    {"text": "Hi, I need help", "timestamp": "..."},
    {"text": "How can I help?", "timestamp": "..."}
  ]
}
```
- Adding a message requires updating the entire document
- Querying "messages between user X and Y in Q3 where no agent replied within 4 hours" requires expensive aggregation pipelines
- Branching (escalation) means duplicating message arrays
- No native support for graph traversal

**Relational tables** normalize messages:
```sql
-- messages table
CREATE TABLE messages (
  id, conversation_id, sender_id, content, timestamp
);
```
- Temporal queries require complex self-joins
- "Previous message" queries need window functions with fragile ordering
- Schema migrations for new message properties

## The Graph Solution

Messages are **first-class nodes** with bidirectional temporal links:

```
(User) --SENT--> [Message A] --NEXT--> [Message B] --NEXT--> [Message C]
                 <--PREV---            <--PREV---            <--PREV---
                        |                                        |
                    PART_OF                                 PART_OF
                        |                                        |
                        v                                        v
                    (Conversation)
```

This enables:
- **O(1) message insertion** — no document updates, just create + link
- **Efficient temporal traversal** — follow NEXT/PREV links
- **First-class branching** — BRANCHED_FROM relationship
- **No schema migrations** — add any properties to any message
- **Vector embeddings** — semantic search without schema changes

## Features Demonstrated

### 1. Bidirectional Temporal Links
Messages are linked with `NEXT` and `PREV` relationships, enabling:
- Forward traversal (older → newer)
- Reverse traversal (newer → older)
- Efficient `nth` message retrieval

### 2. Conversation Window Queries
Find messages within specific time boundaries with participant filters.

### 3. Branching and Merging
Support for:
- **Escalation**: Chat → Phone conversation
- **Handoff**: Chat → Email thread
- First-class graph operations, not data duplication

### 4. Vector Embeddings for Semantic Search
Attach embeddings to message content for:
- "Find similar messages across all conversations"
- "Search for messages about X topic in user's history"
- Zero schema migration needed

### 5. Performance Comparison
Benchmarks showing:
- Graph traversal vs array iteration
- Temporal window queries vs date range filters
- Semantic search vs text matching

## Prerequisites

- Python 3.10+
- RushDB account ([sign up](https://rushdb.com))
- sentence-transformers for embeddings

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RushDB API key
```

Get your API key from [RushDB Dashboard](https://app.rushdb.com)

### 3. Seed the Database (Optional)

This project ships with inline mock data for demonstration. To generate a larger dataset for benchmarks:

```bash
python seed.py
```

This will create ~500 messages across 10 conversations.

## Running the Demo

```bash
python main.py
```

The script demonstrates:

1. **Conversation Creation** — Building a conversation with temporal links
2. **Message Insertion** — Adding messages with proper link management
3. **Temporal Traversal** — Walking through conversation history
4. **Conversation Windows** — Querying by date range and participants
5. **Branching Scenarios** — Handling escalation and handoff
6. **Semantic Search** — Vector similarity across messages
7. **Performance Benchmarks** — Graph vs document store patterns

## Project Structure

```
implementing-temporal-graph-queries-for-conversati-usecase/
├── README.md           # This file
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── seed.py              # Generate mock conversation data
└── main.py              # Main demonstration script
```

## Key Insights

| Pattern | Traditional | Graph Approach |
|---------|-------------|----------------|
| Message insert | Update array field | Create node + 2 links |
| Get last message | Sort + limit 1 | Follow PREV link |
| Conversation span | Aggregate query | Traverse NEXT chain |
| Similar messages | Regex/LIKE | Vector similarity |
| Branch conversation | Duplicate array | New node + BRANCHED_FROM |

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Data Modeling Guide](https://docs.rushdb.com/concepts)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/implementing-temporal-graph-queries-for-conversati-usecase)

## License

MIT
