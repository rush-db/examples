# Hyperedge Representation for Multi-Party Conversations

A practical demonstration of how RushDB's property graph model elegantly handles Slack-style threads with branching replies, mentions, and cross-channel references.

## The Problem with Traditional Approaches

**Relational databases** require junction tables for many-to-many relationships, making thread queries with multiple participants slow at scale:
```sql
-- Finding threads where Alice AND Bob both participated
SELECT DISTINCT thread_id FROM messages WHERE user_id IN (alice_id, bob_id)
GROUP BY thread_id HAVING COUNT(DISTINCT user_id) = 2
```

**Flat document stores** can embed mentions as arrays, but querying "all threads mentioning X" requires scanning every document.

**RushDB's hyperedge model** treats mentions as first-class relationships, enabling O(1) graph traversal instead of O(n) scans.

## What This Demo Shows

1. **Schema Design** — How to model conversations with labels and relationships
2. **Data Seeding** — Creating a realistic multi-channel conversation dataset
3. **Mention Queries** — Finding all messages mentioning a user across channels
4. **Co-participation Queries** — Finding threads where two users both participated
5. **Performance Analysis** — Why graph traversal beats table scans

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://rushdb.com))
- `rushdb>=2.0.0`

## Setup

```bash
# Clone the examples repo
git clone https://github.com/rush-db/examples.git
cd hyperedge-representation-for-multi-party-conversat-usecase

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Demo

```bash
# Seed the database with mock conversation data
python seed.py

# Run the hyperedge queries
python main.py
```

## Expected Output

```
=== Hyperedge Representation Demo ===

[1] Schema Overview
  Labels: USER, CHANNEL, THREAD, MESSAGE
  Relationships: AUTHORED_BY, PART_OF, MENTIONS, REPLY_TO, POSTED_IN, THREAD_REFERENCE

[2] Seeding Complete
  Created: 5 users, 3 channels, 4 threads, 12 messages

[3] Query: Messages mentioning @alice across all channels
  Found 3 messages:
    - Thread "Q4 Planning" (engineering): @alice great point about the API changes!
    - Thread "Sprint Review" (general): @alice can you review the PR?
    - Thread "Deploy Issues" (ops): @alice this is blocking prod

[4] Query: Threads where @alice AND @bob co-participated
  Found 2 threads:
    - "Q4 Planning" (engineering)
    - "Sprint Review" (general)

[5] Graph Traversal Performance
  Traditional DB: O(n) — scans every message document/row
  RushDB Graph:  O(1) — follows indexed edges directly from MESSAGE to USER

[6] Cleanup Complete
```

## Schema Design

### Labels (Node Types)

| Label | Purpose |
|-------|---------|
| `USER` | Participants in the conversation |
| `CHANNEL` | Communication channels (e.g., #engineering, #general) |
| `THREAD` | A conversation thread with a topic |
| `MESSAGE` | Individual messages within threads |

### Relationship Types (Edges)

| Type | From | To | Description |
|------|------|-----|-------------|
| `AUTHORED_BY` | MESSAGE | USER | Who wrote the message |
| `PART_OF` | MESSAGE | THREAD | Which thread contains this message |
| `MENTIONS` | MESSAGE | USER | Users @mentioned in the message |
| `REPLY_TO` | MESSAGE | MESSAGE | Direct reply relationship |
| `POSTED_IN` | MESSAGE | CHANNEL | Original channel of the message |
| `THREAD_REFERENCE` | THREAD | CHANNEL | Which channel the thread belongs to |

### Why Hyperedges Matter

A message mentioning multiple users creates multiple `MENTIONS` edges from a single MESSAGE node to multiple USER nodes. This is the "hyperedge" pattern — one source, many destinations:

```
    [USER:alice] <--MENTIONS-- [MESSAGE:"@alice @bob review this"] --MENTIONS--> [USER:bob]
                                              |
                                              |--AUTHORED_BY--> [USER:charlie]
```

## Documentation

- [RushDB Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [GitHub Examples](https://github.com/rush-db/examples)
