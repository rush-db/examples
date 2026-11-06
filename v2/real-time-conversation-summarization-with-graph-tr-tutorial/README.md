# Real-Time Conversation Summarization with Graph-Traced References

A demonstration of using RushDB as a full-cycle memory layer for real-time conversation tracking, automatic summarization, and graph-traced entity references.

## What This Project Demonstrates

- **Conversation Threading**: Storing messages as linked graph nodes with temporal ordering
- **Automatic Summarization**: Creating summary records with embedded vector representations
- **Graph-Traced References**: Connecting messages to mentioned entities (users, topics, actions)
- **Real-Time Querying**: Traversing conversation graphs to retrieve contextual summaries
- **Transactional Integrity**: Using RushDB transactions for atomic conversation updates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RushDB Graph Layer                       │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Conversation │────│   Message    │────│   Summary    │   │
│  │              │    │              │    │              │   │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                   │                   │           │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │    User      │    │    Topic     │    │   Entity     │   │
│  │   (MENTIONS) │    │  (REFERENCES)│    │  (TRACES)    │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- A RushDB account (free tier available at https://rushdb.com)
- `RUSHDB_API_KEY` environment variable

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Seed mock data** (optional — creates sample conversations):
   ```bash
   python seed.py
   ```

## Running the Demo

```bash
python main.py
```

The script will:
1. Create a vector index for message embeddings
2. Initialize sample conversations with messages
3. Demonstrate real-time message ingestion
4. Show automatic summary generation
5. Query graph-traced references across conversations

## Expected Output

```
=== Real-Time Conversation Summarization Demo ===

[1] Creating conversations and messages...
    ✓ Created conversation: project-alpha-kickoff
    ✓ Added 12 messages to conversation

[2] Creating summary with vector embedding...
    ✓ Generated summary with 384-dim embedding
    ✓ Linked summary to conversation

[3] Graph-traced reference query...
    ✓ Found 8 messages mentioning 'deploy'
    ✓ Found 3 referenced entities: @alice, #backend, @bob

[4] Real-time message search...
    ✓ Semantic search: 'deployment pipeline'
      - msg_7: "Let's verify the deploy script..."
      - msg_3: "Deploy checklist review with team"

[5] Conversation traversal...
    ✓ Traversing conversation graph
    ✓ Found 2 summaries with high relevance

=== Demo Complete ===
```

## Key RushDB Features Used

| Feature | Method | Purpose |
|---------|--------|---------|
| Record creation | `db.records.create()` | Store messages, summaries, entities |
| Relationship linking | `db.records.attach()` | Connect messages to conversations |
| Vector indexing | `db.ai.indexes.create()` | Enable semantic search on content |
| Semantic search | `db.ai.search()` | Find relevant messages by meaning |
| Graph traversal | `db.records.find()` | Query messages by related entities |
| Transactions | `db.transactions.begin()` | Atomic conversation updates |

## Project Structure

```
real-time-conversation-summarization-with-graph-tr-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py           # Mock data generation
└── main.py           # Main demonstration
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB SDK Reference](https://docs.rushdb.com/sdk/python)
- [Graph Database Concepts](https://docs.rushdb.com/core-concepts/property-graph)

## License

MIT License - See LICENSE file for details.
