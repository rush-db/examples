# Implementing Belief Revision When Stored Facts Get Contradicted

A practical tutorial demonstrating how to implement belief revision patterns using RushDB's graph-based storage. This project shows how to handle contradicting facts, track belief provenance, and maintain consistency in a knowledge base.

## What is Belief Revision?

Belief revision is the process of updating stored knowledge when new information contradicts existing beliefs. In traditional databases, updating a record simply overwrites the old value. In a belief-based system, we need to:

1. **Preserve history** — Old beliefs remain accessible for audit trails
2. **Mark contradictions** — Explicitly link contradicting beliefs
3. **Track confidence** — Each belief has metadata about its reliability
4. **Maintain graph consistency** — Related beliefs may need cascading revision

## What This Tutorial Demonstrates

- **Storing beliefs as typed records** with provenance metadata
- **Detecting contradictions** using graph traversal and property comparison
- **Revising beliefs atomically** with RushDB transactions
- **Tracking revision chains** via relationships
- **Cascading revisions** when one belief affects others

## Prerequisites

- Python 3.10+
- A RushDB account (Free tier available at https://rushdb.com)
- `rushdb>=2.0.0` Python package

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

### 3. Seed Mock Data

```bash
python seed.py
```


This creates a sample knowledge base with facts about companies, their founding dates, CEO information, and headquarters locations — some of which will be contradicted during the demo.

## Running the Tutorial

```bash
python main.py
```

The script demonstrates:

1. **Loading the knowledge base** — Fetching existing beliefs
2. **Detecting contradictions** — Finding beliefs that conflict with incoming data
3. **Simple revision** — Updating a single contradicted belief
4. **Complex revision with history** — Creating a full audit trail with retraction records
5. **Cascading revision** — Revising beliefs that depend on other beliefs
6. **Querying revised knowledge** — Filtering for active vs. retracted beliefs

## Expected Output

```
=== Belief Revision Tutorial ===

[1] Loading knowledge base...
   Found 12 beliefs about 4 entities

[2] Detecting contradictions...
   Found 3 beliefs that contradict the incoming data:
   - Company:TechCorp (id: xxx): founding_date "1999" vs new "2000"
   - Company:TechCorp (id: xxx): ceo "John Smith" vs new "Jane Doe"
   - Company:DataInc (id: xxx): headquarters "New York" vs new "Boston"

[3] Simple revision...
   Updated TechCorp.founding_date: 1999 -> 2000

[4] Complex revision with history...
   Retracted: TechCorp.ceo = John Smith (id: xxx)
   Created: TechCorp.ceo = Jane Doe (id: xxx)
   Linked: RETRACTED -> CORRECTED relationship established

[5] Cascading revision...
   Detected 2 dependent beliefs referencing old CEO
   Revising: Employee record 'Alice' (CEO relationship will update)

[6] Querying revised knowledge...
   Active beliefs: 11
   Retracted beliefs: 3
```

## Project Structure

```
implementing-belief-revision-when-stored-facts-get-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── seed.py           # Mock data generation script
└── main.py           # Tutorial demonstration code
```

## Key RushDB Patterns Used

- **Transactions** (`db.transactions.begin()`) for atomic belief revisions
- **Relationships** for linking retracted beliefs to their corrections
- **Labels** (`BELIEF`, `ENTITY`) for organizing knowledge
- **Property tracking** for belief metadata (confidence, source, timestamp)

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [Knowledge Graph Patterns](https://rushdb.com/docs)

## License

MIT
