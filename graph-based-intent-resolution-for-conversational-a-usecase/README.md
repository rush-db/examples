# Graph-Based Intent Resolution for Conversational AI

A runnable demonstration of RushDB's graph + vector architecture applied to intent resolution in conversational AI systems. This project shows how combining directed graph traversal with semantic vector search outperforms pure retrieval for ambiguous, multi-turn conversations.

## What it demonstrates

- **Graph modeling**: Intents as nodes, valid transitions as directed edges — capturing conversation flow rules
- **Semantic fallback**: Utterance embeddings on every intent node for when the graph has no exact match
- **Contextual disambiguation**: The same phrase (e.g. `"book a flight"`) resolves to different intents depending on entry point
- **Multi-turn resolution pipeline**: Full RushDB schema and queries for a hybrid graph+vector pipeline
- **Benchmark**: Quantitative comparison of pure retrieval vs. graph+vector hybrid for ambiguous queries

## Prerequisites

- Python 3.9+
- A RushDB account ([free tier](https://rushdb.com/pricing) is sufficient)
- `sentence-transformers` for local embedding generation (no API key required)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Then edit .env and set your RUSHDB_API_KEY
```

## Run

```bash
# Seed the RushDB project with the intent graph and embedding indexes
# (safe to run multiple times — idempotent with --reset flag)
python seed.py

# Run the full demonstration and benchmark
python main.py
```

## Expected output

- Console output showing each benchmark query, resolved intents from both approaches, and execution times
- Example contextual disambiguation: `"book a flight"` resolved from different entry points
- A summary table comparing pure retrieval vs. hybrid graph+vector accuracy

## Project structure

```
graph-based-intent-resolution-for-conversational-a-usecase/
├── .env.example          # Environment variable template
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── seed.py               # Seeds intent graph + vector indexes in RushDB
└── main.py               # Resolution pipeline + benchmark runner
```

## Key concepts

### Why graph + vector?

Pure vector retrieval picks the globally most similar intent. It has no concept of conversation state — so `"book a flight"` after `"cancel my trip"` might still route to `BOOK_FLIGHT` instead of the more contextually appropriate `RESUME_BOOKING` or `NEW_BOOKING`.

The graph layer adds conversation rules: you can only transition from valid nodes. When no exact graph path exists, vector search provides semantic fallback. Together they deliver context-aware routing that neither approach achieves alone.

### RushDB schema

| Label | Role |
|---|---|
| `INTENT` | Node representing a single intent |
| `UTTERANCE` | Example user phrases with vectors for semantic matching |

| Relationship | Direction | Role |
|---|---|---|
| `CAN_TRANSITION_TO` | `out` (INTENT → INTENT) | Valid next-intent edges in the graph |
| `HAS_UTTERANCE` | `out` (INTENT → UTTERANCE) | Links an intent to its example phrases |

### Benchmark results interpretation

The benchmark uses 15 ambiguous query/context pairs with known correct answers. Pure retrieval returns the globally best vector match; the hybrid approach filters candidates to graph-reachable intents first, then picks the best within that set.

Graph+vector typically achieves **10–30% higher accuracy** on context-dependent queries because it respects conversation flow rules. Pure retrieval excels on single-turn, out-of-domain queries.

## Learn more

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub](https://github.com/rush-db/examples)
- [RushDB Pricing](https://rushdb.com/pricing)
