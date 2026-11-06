# Graph-Structured Prompt Routing

**Directing queries to the right subgraph with RushDB**

## Overview

This project demonstrates how to implement graph-structured prompt routing — a technique where user queries are analyzed and routed to specialized subgraphs (domains) before being processed by a targeted prompt strategy.

In complex AI systems, routing queries to the correct domain subgraph ensures:
- Faster response times (smaller search space)
- More accurate answers (domain-specific context)
- Better resource allocation (specialized models per domain)

## What This Tutorial Demonstrates

1. **Domain Subgraphs** — Organizing knowledge into topic-specific subgraphs
2. **Routing Rules** — Creating pattern-to-domain mappings as graph relationships
3. **Query Analysis** — Using semantic search to classify incoming queries
4. **Trajectory Routing** — Traversing the graph to find the correct domain
5. **Targeted Retrieval** — Searching within the routed subdomain

## Architecture

```
User Query
    │
    ▼
┌─────────────────────┐
│  Query Router       │
│  (classify intent)  │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Domain Graph       │
│  (routing rules)    │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Routed Subgraph    │ ────▶ Targeted Prompt + Retrieval
│  (domain knowledge) │
└─────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- `rushdb>=2.0.0`

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Generate mock data:**
   ```bash
   python seed.py
   ```
   This creates:
   - 5 topic domains (Coding, Design, Marketing, Finance, Support)
   - 25+ query patterns per domain
   - 50+ knowledge entries per domain
   - Routing relationships linking patterns to domains

4. **Run the demo:**
   ```bash
   python main.py
   ```

## Project Structure

```
.
├── README.md          # This file
├── requirements.txt   # Dependencies
├── .env.example       # Environment template
├── seed.py            # Generates mock knowledge graph
└── main.py            # Demo: query routing through subgraphs
```

## How It Works

### Step 1: Query Classification

Incoming queries are analyzed using semantic search against a pattern graph.
The system finds the most similar routing patterns and extracts their target domains.

### Step 2: Domain Resolution

The routing graph is traversed to:
1. Find patterns that match the query intent
2. Resolve the target domain subgraph
3. Validate the domain exists and has content

### Step 3: Knowledge Retrieval

Once routed to the correct subdomain:
1. Search within domain-specific knowledge entries
2. Retrieve relevant context for prompt generation
3. Return structured results for downstream processing

## Example Queries

The seed data includes patterns for queries like:

| Query | Routed Domain |
| ----- | ------------- |
| "How do I fix a null pointer error?" | Coding |
| "What are the best practices for REST APIs?" | Coding |
| "Design a color palette for a tech startup" | Design |
| "How do I set up a Stripe payment integration?" | Finance |
| "Reset my password doesn't work" | Support |

## Expected Output

```
=== Graph-Structured Prompt Routing Demo ===

Processing: "How do I fix a null pointer exception in Java?"
  → Classified intent: Programming/Java
  → Routed to: CODING domain
  → Found 3 relevant entries

Processing: "What colors work for a modern dashboard?"
  → Classified intent: UI/Color Theory
  → Routed to: DESIGN domain
  → Found 2 relevant entries

Processing: "How much should I charge for consulting?"
  → Classified intent: Business/Pricing
  → Routed to: FINANCE domain
  → Found 4 relevant entries

=== Routing Summary ===
Total queries: 3
Domains visited: [CODING, DESIGN, FINANCE]
Avg retrieval time: ~45ms
```

## Key RushDB Features Used

- **Record creation** — domains, patterns, knowledge entries
- **Relationships** — routing rules between patterns and domains
- **Semantic search** — pattern matching for query classification
- **Graph traversal** — finding related entries within subgraphs
- **Transactions** — atomic graph construction during seeding

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)
- [Property Graph Concepts](https://docs.rushdb.com/concepts)
