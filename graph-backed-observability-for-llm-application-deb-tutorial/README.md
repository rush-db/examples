# Graph-backed Observability for LLM Application Debugging

## Overview

This project demonstrates how to use RushDB as a **graph-backed observability layer** for LLM application debugging. Instead of querying flat logs or relying on proprietary tracing systems, you store every interaction as a property graph — making it trivial to traverse prompt→response→tool_call chains, find correlated errors, and reconstruct full execution traces.

## What You'll Learn

- How to model LLM observability data as a property graph
- Storing prompts, responses, tool calls, and errors as connected records
- Using RushDB's graph traversal to debug LLM applications
- Finding correlated errors across sessions
- Reconstructing execution traces from stored records

## Why Graph-backed Observability?

Traditional logging gives you flat timelines. RushDB gives you **structure**:

| Traditional Logs | RushDB Graph |
|-----------------|--------------|
| grep through JSON blobs | Query by label and relationships |
| Correlate IDs manually | Traverse connected records directly |
| No semantic relationships | ACTED_IN, INVOKED, ERRONEOUS links |
| Flat key-value storage | Property nodes shared across records |

## Prerequisites

- Python 3.9+
- A RushDB account (free tier works)
- `rushdb>=2.0.0`

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set RUSHDB_API_TOKEN
```

Get your API token from [RushDB Dashboard](https://app.rushdb.com).

### 3. Seed Mock Observability Data

The seed script generates a realistic LLM application trace with sessions, messages, tool calls, and errors:

```bash
python seed.py
```

Expected output:
```
[✓] Connected to RushDB
[✓] Seeded 3 sessions, 12 messages, 8 tool calls, 5 errors
[✓] All records linked via graph relationships
```

The seed is idempotent — running twice cleans up and reseeds.

### 4. Run the Demo

```bash
python main.py
```

Expected output shows:
- Session trace reconstruction
- Error correlation analysis
- Tool call chain traversal
- Latency pattern queries

## Project Structure


```
graph-backed-observability-for-llm-application-deb-tutorial/
├── README.md           # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Mock observability data generator
└── main.py            # Main demonstration script
```

## Data Model

The observability graph uses these labels and relationships:

```
SESSION ──[CONTAINS]──> MESSAGE ──[RESPONDS_TO]──> MESSAGE
     │                      │
     │                      └──[TRIGGERS]──> TOOL_CALL
     │                               │
     │                               └──[HAS_ERROR]──> ERROR
     │
     └──[HAS_ERROR]──> ERROR
```

### Labels

| Label | Description | Key Properties |
|-------|-------------|----------------|
| `SESSION` | A user conversation or request session | `session_id`, `user_id`, `created_at` |
| `MESSAGE` | A prompt or response | `role`, `content`, `model`, `tokens_used`, `latency_ms` |
| `TOOL_CALL` | An LLM tool invocation | `tool_name`, `arguments`, `result`, `latency_ms` |
| `ERROR` | An error or exception | `error_type`, `message`, `stack_trace`, `severity` |

### Relationships

| Type | From → To | Description |
|------|-----------|-------------|
| `CONTAINS` | SESSION → MESSAGE | Message belongs to session |
| `RESPONDS_TO` | MESSAGE → MESSAGE | Response to a prompt |
| `TRIGGERS` | MESSAGE → TOOL_CALL | Tool call was triggered by message |
| `HAS_ERROR` | TOOL_CALL → ERROR | Tool call resulted in error |
| `CAUSED_BY` | ERROR → TOOL_CALL | Error caused by tool invocation |

## Key RushDB Features Demonstrated

1. **Record Creation** — Creating observability records with `db.records.create()`
2. **Relationships** — Linking records with `db.records.attach()`
3. **Graph Traversal** — Querying related records via label-based filtering
4. **Transactions** — Atomic multi-record creation for consistency
5. **Filtering** — Using `where` clauses with nested labels for graph queries

## Further Reading


- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Model](https://docs.rushdb.com/concepts/property-graph)
- [Relationships API](https://docs.rushdb.com/api/relationships)
- [RushDB SDK Reference](https://docs.rushdb.com/sdks/python)
