# Building Streaming Ingestion Pipelines for Agent Interaction Logs

This project demonstrates how to build a streaming ingestion pipeline for agent interaction logs using RushDB. It simulates real-time events from an AI agent system, batch-processes them, and stores them as structured records for querying and analysis.

## What This Project Demonstrates

- **Streaming data simulation**: Generating realistic agent interaction events in real-time
- **Batch processing**: Aggregating streaming events into efficient RushDB writes using `create_many`
- **Transaction-based writes**: Using transactions for atomic batch commits
- **Upsert patterns**: Idempotent updates for stateful events like tool results
- **Graph relationships**: Linking interactions as a property graph (Agent → Sessions → Events)
- **Query patterns**: Filtering and analyzing the ingested logs

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────┐
│  Event Source   │────▶│  Stream Pipeline │────▶│    RushDB     │
│  (Simulator)    │     │  (Batch/Batch)   │     │  (Storage)    │
└─────────────────┘     └──────────────────┘     └───────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼─────┐      ┌─────▼─────┐
              │  AGENT    │      │  SESSION  │
              │  (node)   │◀────▶│  (node)   │
              └───────────┘      └─────┬─────┘
                                        │
                              ┌─────────┼─────────┐
                        ┌─────▼───┐ ┌──▼──┐ ┌───▼───┐
                        │ MESSAGE │ │TOOL_│ │TOOL_ │
                        │         │ │CALL │ │RESULT │
                        └─────────┘ └─────┘ └───────┘
```

## Event Types

| Event Type | Description | RushDB Label |
|------------|-------------|--------------|
| `user_message` | Raw user input to the agent | `MESSAGE` |
| `assistant_message` | Agent's response | `MESSAGE` |
| `tool_call` | Agent invoking a tool | `TOOL_CALL` |
| `tool_result` | Result returned from a tool | `TOOL_RESULT` |
| `session_start` | New conversation session begins | `SESSION` |
| `session_end` | Session terminates | `SESSION` |

## Setup

### Prerequisites

- Python 3.9+
- A RushDB account (free tier works)

### Installation

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd building-streaming-ingestion-pipelines-for-agent-i-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

### Getting Your RushDB API Token

1. Sign up at https://app.rushdb.com
2. Create a new project or select an existing one
3. Go to Settings → API Keys
4. Copy your API token

## Running the Pipeline

### Full Pipeline (Ingest + Query)

```bash
python main.py
```

This will:
1. Simulate a streaming session with 50 events
2. Batch-ingest them into RushDB
3. Run analysis queries on the ingested data
4. Print results to the console

### Seed Existing Data

If you want to add more historical data:

```bash
python seed.py
```

This generates a configurable number of sessions with realistic conversation patterns.

### Run Only Ingestion

```bash
python main.py --mode ingest --events 100
```

### Run Only Analysis

```bash
python main.py --mode analyze
```

## Expected Output

```
[STREAM] Starting streaming pipeline simulation...
[BATCH] Processing batch 1/5: 10 events
[BATCH] Committed 10 events to RushDB
[BATCH] Processing batch 2/5: 10 events
[BATCH] Committed 10 events to RushDB
...
[ANALYSIS] Query Results:
  Total Sessions: 3
  Total Messages: 47
  Total Tool Calls: 23
  Active Agents: 2

[TOP TOOLS]
  tool_use_email_send: 8 calls
  tool_use_database_query: 6 calls
  tool_use_file_write: 4 calls

[SESSION BREAKDOWN]
  session_abc123: 15 events (active)
  session_def456: 18 events (active)
  session_ghi789: 17 events (active)
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── main.py             # Entry point & analysis queries
├── pipeline.py         # Stream processing logic
├── models.py           # Event data models
├── simulator.py        # Event source simulator
└── seed.py             # Batch seed script for historical data
```

## Key Implementation Details

### Batch Processing Strategy

The pipeline collects events into batches (configurable, default: 10) before writing to RushDB. This balances latency (fresh data) with throughput (efficient writes).

```sdk
# Buffer events
batch = []
for event in event_stream:
    batch.append(event)
    if len(batch) >= batch_size:
        # Write batch atomically
        with db.transactions.begin() as tx:
            db.records.create_many(label=event.label, data=batch, transaction=tx)
        batch = []
```

### Upsert for Stateful Events

Tool results are upserted to handle retries and updates:

```sdk
db.records.upsert(
    label="TOOL_RESULT",
    data=result_data,
    options={"mergeBy": ["call_id", "tool_name"]}
)
```

### Relationship Linking

Events are linked to their parent session:

```sdk
db.records.attach(
    source=event_record,
    target=session_record,
    options={"type": "BELONGS_TO"}
)
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `RUSHDB_API_TOKEN` | Your RushDB API key | Required |
| `RUSHDB_URL` | Self-hosted URL (optional) | Cloud |
| `BATCH_SIZE` | Events per batch write | 10 |
| `STREAM_DELAY` | Seconds between events | 0.1 |

## Query Examples

### Find all tool calls for a specific session

```sdk
db.records.find({
    "labels": ["TOOL_CALL"],
    "where": {
        "SESSION": {"$id": {"$in": [session_id]}}
    }
})
```

### Get session timeline

```sdk
db.records.find({
    "labels": ["MESSAGE", "TOOL_CALL", "TOOL_RESULT"],
    "where": {
        "session_id": "session_abc123"
    },
    "orderBy": {"timestamp": "asc"}
})
```

## License

MIT License - See LICENSE file for details.
