# Graph-backed Prompt Chaining: Composing Subgraphs for Multi-Step Reasoning

This tutorial demonstrates how to build a multi-step reasoning pipeline using RushDB's property graph as a memory layer. Each reasoning stage operates on a distinct subgraph, and the LLM's conclusions drive which subgraph to query next.

## What This Demonstrates

- **Graph schema design** for multi-hop relationships (documentation → concepts → decisions → tradeoffs)
- **Subgraph traversal** using typed edges to scope queries to relevant reasoning stages
- **Prompt chaining** where each LLM conclusion determines the next subgraph query
- **Round-trip workflow** from natural language question to final synthesized answer

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Question  │────▶│   Subgraph  │────▶│     LLM     │────▶│ Conclusion  │
│             │     │   Query 1   │     │   Stage 1   │     │   Node      │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                     │
                                                                     ▼
              ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
              │   Question  │◀────│   Subgraph  │◀────│   Next      │
              │   Refined   │     │   Query 2   │     │   Stage     │
              └─────────────┘     └─────────────┘     └─────────────┘
```

## Prerequisites

- Python 3.9+
- RushDB account (free tier works)
- `pip install -r requirements.txt`

## Setup

1. **Copy environment variables**:
   ```bash
   cp .env.example .env
   ```

2. **Configure your RushDB token** in `.env`:
   ```
   RUSHDB_TOKEN=your_api_token_here
   ```

3. **Seed the graph database** (creates sample documentation, concepts, decisions, and tradeoffs):
   ```bash
   python seed.py
   ```
   This is idempotent—run it multiple times safely.

4. **Run the prompt chain**:
   ```bash
   python main.py
   ```

## Expected Output

```
=== Graph-Backed Prompt Chaining Demo ===

Question: How should I implement caching in a distributed system?

--- Stage 1: Query CONCEPT subgraph ---
Found 3 related concepts: cache_coherency, eventual_consistency, distributed_hash_table
LLM Conclusion: Distributed caching must balance strong consistency with availability. 
               The choice between cache coherency and eventual consistency determines 
               both complexity and performance characteristics.
Created conclusion node: CONC-001

--- Stage 2: Query DECISION subgraph ---
Found 2 related decisions: cache_placement_decision, invalidation_strategy_decision
LLM Conclusion: Cache placement (client vs server) and invalidation frequency 
               create a configuration matrix. Most systems benefit from a tiered approach.
Created conclusion node: CONC-002

--- Stage 3: Query TRADEOFF subgraph ---
Found 2 related tradeoffs: latency_vs_consistency, availability_vs_consistency
LLM Conclusion: Key tradeoffs: (1) Strong consistency adds 10-50ms latency per operation,
               (2) Eventual consistency risks stale reads but improves availability.
Created conclusion node: CONC-003

--- Final Answer ---
For distributed caching implementation:
1. Start with eventual consistency unless strong coherence is required
2. Place cache tier between client and database
3. Use write-through for critical data, write-behind for high-throughput paths
4. Monitor latency vs staleness metrics to tune invalidation frequency
```

## Project Structure

```
graph-backed-prompt-chaining-composing-subgraphs-f-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Graph seeding script (run once)
└── main.py             # Prompt chaining pipeline (run multiple times)
```

## Architecture Notes

### Graph Schema

The graph models a software architecture reasoning domain:

| Label         | Purpose                                      | Key Properties                    |
|---------------|----------------------------------------------|-----------------------------------|
| DOCUMENTATION | Source articles and guides                   | title, body, domain                |
| CONCEPT       | Technical concepts and patterns              | name, description, category       |
| DECISION      | Architecture decisions                        | title, context, recommendation    |
| TRADEOFF      | Trade-off analyses                           | dimension, pro, con                |
| CONCLUSION    | LLM-generated reasoning (prompt chain output)| stage, content, source_question   |

### Relationship Types

- DOCUMENTATION → CONTAINS → CONCEPT
- CONCEPT → LEADS_TO → DECISION  
- DECISION → HAS_TRADEOFF → TRADEOFF
- CONCLUSION → BASED_ON → (CONCEPT/DECISION/TRADEOFF)

### Why Subgraph Chaining?

Traditional RAG queries the entire vector corpus. Subgraph chaining:
1. **Scopes context** to a specific reasoning stage
2. **Reduces noise** by filtering to relevant node types
3. **Enables refinement** as each conclusion narrows the next query
4. **Makes reasoning traceable** — conclusions are stored as first-class nodes

## API Reference

- RushDB Python SDK: https://docs.rushdb.com/sdk/python
- Prompt chaining pattern: Query subgraph → Generate conclusion → Store node → Repeat

## Related Examples

- `semantic-search/` — Basic vector similarity search
- `graph-traversals/` — Relationship-based querying
- `ai-grounded-responses/` — Combining vector search with LLM generation
