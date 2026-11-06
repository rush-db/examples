# Building a Contextual Grounding Layer for LLMs with RushDB

This project demonstrates a practical architecture for LLM context grounding that combines **graph traversal** for relationship discovery with **vector similarity** for semantic recall.

## The Problem with Naive RAG

Traditional RAG (Retrieval-Augmented Generation) pipelines hit a quality wall when:

- **Entity relationships matter**: "Customer X's billing issue on their Pro plan" requires knowing Pro → Customer → Billing history
- **Transitive context is needed**: "Similar issues on this product model" means traversing product → issues → resolutions
- **Confidence scoring is superficial**: Vector similarity alone can't distinguish "resolved" from "escalated" tickets

## What This Project Demonstrates

This example builds a **customer support assistant** that uses RushDB's dual-layer storage (property graph + vectors) to ground responses with:

1. **Semantic recall**: Vector search finds semantically similar past tickets
2. **Relationship resolution**: Graph traversal filters/boosts results by entity connections
3. **Confidence via paths**: Longer resolution paths = more confident solutions

### Real-World Scenario

A customer asks: "My billing portal shows wrong charges for my enterprise account"

**Naive RAG response**: Finds tickets mentioning "billing" and "wrong charges" — may return irrelevant consumer-tier issues.

**Graph+RAG response**: 
1. Vector search finds "billing portal charges" similarity
2. Graph traversal filters to ENTERPRISE-tier accounts only
3. Further filters to billing-related product category
4. Boosts results with direct CUSTOMER relationship
5. Returns highly relevant, confidence-scored context

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Query                                    │
│  "My billing portal shows wrong charges"                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            Combined Retrieval Pipeline                          │
│                                                                 │
│  ┌─────────────────┐     ┌─────────────────────────────────┐   │
│  │  Vector Search  │────▶│  Graph Traversal + Filtering    │   │
│  │  (Semantic)     │     │  (Entity Relationships)         │   │
│  └─────────────────┘     └─────────────────────────────────┘   │
│           │                          │                           │
│           ▼                          ▼                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Scored & Ranked Context                       │    │
│  │  {ticket, score, path_confidence, entity_links}          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               LLM Grounded Response                             │
└─────────────────────────────────────────────────────────────────┘
```

## Data Model

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  CUSTOMER   │         │   TICKET    │         │   PRODUCT   │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ name        │◀───────▶│ filed_by    │◀────────│ relates_to  │
│ email       │         │ status      │         │ name        │
│ tier        │         │ priority    │         │ category    │
│ account_age │         │ description │         │ version     │
└─────────────┘         └─────────────┘         └─────────────┘
       │                       │
       │                       │
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│  CONTRACT   │         │  CATEGORY   │
├─────────────┤         ├─────────────┤
│ plan_type   │         │ name        │
│ start_date  │         │ resolution_rate
└─────────────┘         └─────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │  SOLUTION   │
                       ├─────────────┤
                       │ title       │
                       │ steps       │
                       │ verified    │
                       └─────────────┘
```

## Tradeoffs

| Aspect | Naive RAG | Graph+RAG |
|--------|-----------|-----------|
| **Setup complexity** | Low | Medium |
| **Query latency** | ~100ms | ~150-250ms |
| **Relevance (entities)** | Low | High |
| **Relevance (transitive)** | None | High |
| **Confidence scoring** | Single vector score | Multi-factor (score + path + entity links) |
| **Indexing overhead** | Embeddings only | Embeddings + relationship setup |

**When it pays off**:
- Complex product/service catalogs with rich entity relationships
- Customer-specific context (tier, history, ownership)
- Multi-hop questions ("similar issues on products my team uses")
- Scenarios where false positives are costly

**When to skip**:
- Simple knowledge bases with flat documents
- Latency-critical real-time applications
- When entity relationships don't matter for your domain

## Setup

### Prerequisites

- Python 3.10+
- A RushDB account (free tier available at [rushdb.com](https://rushdb.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd building-a-contextual-grounding-layer-for-llms-wit-usecase

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API credentials
```

### Obtaining RushDB Credentials

1. Sign up at [rushdb.com](https://rushdb.com)
2. Create a new project
3. Copy your API token from the dashboard
4. Paste into `.env` as `RUSHDB_API_TOKEN`

## Running

### Step 1: Seed the Database

This creates a realistic support ticket dataset with products, customers, and relationships:

```bash
python seed.py
```

Expected output:
```
Seeding RushDB with support ticket data...
Created 15 customers (0/15)
Created 8 products (0/8)
Created 6 categories
Created 50 tickets (0/50)
Created 25 solutions
Created 200+ relationships
Seeding complete! RushDB is ready for queries.
```

### Step 2: Run the Demonstration

```bash
python main.py
```

This demonstrates:
1. **Naive RAG** — pure vector search
2. **Graph+RAG** — combined retrieval with relationship filtering
3. **Comparative analysis** — showing what graph structure adds

## Project Structure

```
building-a-contextual-grounding-layer-for-llms-wit-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py            # Data seeding script
└── main.py            # Main demonstration script
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `rushdb>=2.0.0` | RushDB Python SDK |
| `sentence-transformers` | Local embeddings (no API key required) |
| `python-dotenv` | Environment variable loading |

## Related Resources

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub](https://github.com/rush-db)
- [Property Graph vs Vector Databases](https://docs.rushdb.com/concepts)
