# Graph-Native Pagination for Streaming AI Response Contexts

A complete runnable tutorial demonstrating how RushDB's graph-native architecture handles pagination for streaming AI conversations — without manual bookkeeping or complex cursor management.

## What This Demonstrates

- **Schema Design**: Nodes for stream chunks, tool calls, and documents; edges for `PRECEDES` and `REFERENCES` relationships
- **Cursor-Based Pagination**: Using node IDs as stable cursors that survive concurrent writes
- **Concurrent Write Handling**: How RushDB handles new chunks while clients paginate through earlier context
- **Context-Aware Retrieval**: Fetching page N while maintaining relationship context (what tool triggered this chunk, what document did it cite?)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streaming Conversation                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [ToolCall] ───TRIGGERED──▶ [StreamChunk]                       │
│      │                              │                            │
│      │              ┌───────────────┼───────────────┐            │
│      │              │               │               │            │
│      ▼              ▼               ▼               ▼            │
│  [Document]    [Chunk 1] ──PRECEDES→ [Chunk 2] ──PRECEDES→ ... │
│     │               ▲                                           │
│     │               │                                           │
│     └─CITES─────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account (free tier available at https://rushdb.com)

## Setup

```bash
# 1. Clone the examples repo
git clone https://github.com/rush-db/examples.git
cd graph-native-pagination-for-streaming-ai-response--tutorial

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running

```bash
# Generate mock streaming conversation data
python seed.py

# Run the complete demo
python main.py
```

## Expected Output

```
=== Graph-Native Pagination Demo ===

📡 Simulating 3 concurrent streams...
   ✓ Stream conv_abc created
   ✓ Stream conv_def created
   ✓ Stream conv_ghi created

📄 Fetching page 1 of 'general' conversation (3 chunks/page):
   Chunk: 'Let me check the current weather...' [id: 01H...]
   Chunk: 'Looking up weather data...' [id: 01H...]
   Chunk: 'The current temperature is...' [id: 01H...]

   → What triggered this chunk? ToolCall 'get_weather'
   → What did it cite? Document 'weather_api_docs'
   → Previous chunk: None

📄 Fetching page 2 of 'general' conversation:
   Chunk: 'Wind speed is around 12 mph...' [id: 01H...]
   Chunk: 'Humidity at 65%...' [id: 01H...]
   Chunk: 'Overall conditions are...' [id: 01H...]

🔄 Concurrent write demo: adding new chunk while paginating...
   ✓ New chunk added to conv_abc (id: 01H...)
   → Cursor stable: original page 1 chunks unchanged
```

## Key Concepts

### Why Graph-Native Pagination?

Traditional offset-based pagination (`OFFSET 20 LIMIT 10`) breaks when:
- New records are inserted during traversal
- Records are deleted by concurrent operations
- You need to traverse through related context

RushDB solves this with **ID-based cursors** — node IDs are stable identifiers that don't shift when other records are created or modified.

### The Precedes Relationship

By linking chunks with `PRECEDES` relationships, we preserve the exact streaming order regardless of when chunks were created or how the database stores them internally.

```sdk
# Fetch a page and get the previous chunk in constant time
chunks = db.records.find({
    "labels": ["StreamChunk"],
    "where": {"conversationId": "conv_abc"},
    "limit": 3
})
for chunk in chunks:
    # Navigate backwards through the graph, not through offsets
    prev = db.records.find({
        "labels": ["StreamChunk"],
        "where": {
            "PRECEDES": {"$id": chunk.id}
        }
    })
```

## Files

| File | Description |
|------|-------------|
| `seed.py` | Generates realistic streaming conversation data with chunks, tool calls, and document references |
| `main.py` | Complete demo: schema setup, concurrent streaming simulation, cursor-based pagination, context retrieval |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Model Best Practices](https://docs.rushdb.com/concepts/property-graph)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)

---

GitHub: https://github.com/rush-db/examples/tree/main/graph-native-pagination-for-streaming-ai-response--tutorial
