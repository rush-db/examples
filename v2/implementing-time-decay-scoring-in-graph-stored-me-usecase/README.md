# Implementing Time-Decay Scoring in Graph-Stored Memories

## What This Demonstrates

A working agentic memory system requires three capabilities working in concert:

1. **Graph traversal** — entity relationships (who talked to whom, what topics were discussed)
2. **Vector similarity** — semantic matching (finding conceptually related memories)
3. **Time-decay** — recency weighting (recent context matters more than ancient history)

RushDB is the only backend that combines all three without stitching together separate systems (Vector DB + Graph DB + custom decay logic).

## The Scenario: Conversational Memory Agent

A chatbot that:
- Remembers past conversations with users
- Tracks entities mentioned across sessions
- Uses historical context to inform responses
- Prioritizes recent interactions while still surfacing relevant historical patterns

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    RushDB (Single Backend)               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   GRAPH LAYER          VECTOR LAYER       TIME LAYER    │
│   ───────────         ───────────       ──────────    │
│   Entity edges         Semantic          timestamps    │
│   CONVERSATION          similarity        + decay      │
│       │                     │                │        │
│       ▼                     ▼                ▼        │
│   ┌─────────┐          ┌─────────┐    ┌─────────┐   │
│   │ User A  │◄─────────►│Memory 1 │    │ today   │   │
│   │ User B  │   talks   │Memory 2 │    │ yesterday   │
│   │ Topic X │   about   │Memory 3 │    │ last week    │
│   └─────────┘          └─────────┘    └─────────┘   │
│                                                         │
│   Single API call: db.records.find() with where clause │
│   + db.ai.search() with temporal scoring               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your RushDB API credentials

# 4. Seed mock conversational memory data
python seed.py

# 5. Run the time-decay demonstration
python main.py
```

## Expected Output

The demo will:
1. Show how RushDB combines graph traversal + vector search + time-decay in one query
2. Display memory scores with decay applied
3. Compare against a "separated stack" simulation
4. Highlight latency and consistency benefits

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RUSHDB_API_KEY` | Your RushDB API key |
| `RUSHDB_URL` | RushDB server URL (optional, for self-hosted) |
| `EMBEDDING_MODEL` | Sentence-transformer model for embeddings (default: all-MiniLM-L6-v2) |

## The Time-Decay Algorithm

We use an exponential decay function:

```
score = base_similarity * e^(-λ * days_since_memory)
```

Where:
- `base_similarity`: Vector cosine similarity score
- `λ` (lambda): Decay rate constant (higher = faster decay)
- `days_since_memory`: Age of the memory in days

This ensures:
- Very recent memories (hours old) score near 1.0
- Week-old memories score around 0.5-0.7
- Month-old memories score around 0.1-0.3
- Historical patterns still surface when semantically relevant
