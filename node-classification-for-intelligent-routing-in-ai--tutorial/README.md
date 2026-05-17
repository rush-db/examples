# Node Classification for Intelligent Routing in AI Pipelines

A practical demonstration of how RushDB's property graph model powers intelligent classification and routing in AI pipelines. This example builds a support ticket classification system that automatically routes incoming tickets to the right handlers based on semantic understanding.

## What This Demonstrates

- **Graph-based node classification**: Using RushDB labels and properties to model ticket types, categories, and handlers
- **Semantic routing**: Leveraging RushDB's vector search to match tickets with appropriate handlers
- **Transactional pipeline integrity**: Atomic operations for classification and routing decisions
- **Relationship traversal**: Navigating the classification graph to find optimal routes

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   TICKET    │────▶│   ROUTE      │────▶│   HANDLER     │
│  (incoming) │     │ (classifier) │     │ (assigned)    │
└─────────────┘     └──────────────┘     └───────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌──────────────┐
│  CATEGORY   │◀────│   PRIORITY   │
│ (classified)│     │   (scored)   │
└─────────────┘     └──────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (free tier works)
- `rushdb>=2.0.0` package

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

3. **Seed the database** (creates categories, handlers, and routes):
   ```bash
   python seed.py
   ```

4. **Run the demo**:
   ```bash
   python main.py
   ```

## Project Structure

```
node-classification-for-intelligent-routing-in-ai--tutorial/
├── README.md          # This file
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variable template
├── seed.py            # Creates classification graph and sample data
└── main.py            # Main demonstration script
```

## Expected Output

The demo will:
1. Create sample support tickets with varied content
2. Classify each ticket against the taxonomy
3. Route tickets to appropriate handlers using semantic matching
4. Display the routing decisions with confidence scores

## How It Works

### 1. Classification Graph

The system defines a classification taxonomy using RushDB labels:

| Label | Purpose |
|-------|--------|
| `TICKET` | Incoming support request |
| `CATEGORY` | Classification category (billing, technical, sales, etc.) |
| `HANDLER` | Agent who handles certain ticket types |
| `ROUTE` | Routing rule connecting category to handler |

### 2. Semantic Routing

For each ticket:
1. **Classify**: Find the best-matching category using `db.ai.search()`
2. **Route**: Find the handler(s) connected to that category via ROUTE relationships
3. **Assign**: Attach the ticket to the winning handler

### 3. Pipeline Integration

The classification happens within a transaction, ensuring:
- Ticket is created
- Category is assigned
- Handler is matched
- Route is recorded

All-or-nothing: either the entire pipeline completes or nothing persists.

## Pricing Note

RushDB charges by **KnowledgeUnits (KU)** for writes. This demo:
- Creates ~15 records (categories, handlers, routes, tickets)
- Runs ~10 semantic searches
- Estimated cost: ~75 KU (well within free tier limits)

Reads are always free.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Pricing](https://rushdb.com/pricing)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/node-classification-for-intelligent-routing-in-ai--tutorial)
