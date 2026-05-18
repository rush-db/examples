# Subgraph Extraction Strategies for Context-Window Optimization

A practical guide to extracting optimal subgraphs from RushDB for LLM context windows. Learn how to structure your graph data and extract relevant knowledge subsets that fit within token limits while maximizing information density.

## Overview

When using graph-backed RAG or agentic systems, the challenge isn't just finding relevant data—it's extracting the right *shape* of knowledge to fit your context window. This tutorial demonstrates five subgraph extraction strategies using RushDB's property graph model.

## What This Tutorial Demonstrates

| Strategy | Description | Best For |
|----------|-------------|----------|
| **N-Hop Neighborhood** | Extract all nodes within K hops from seed nodes | Exploring local context |
| **Relationship-Type Filter** | Extract by following specific edge types | Domain-specific traversal |
| **Importance Scoring** | Rank nodes by connectivity and prune | Dense graphs with noise |
| **Entity-Centric** | Extract star-shaped subgraphs around key entities | Fact-checking, entity analysis |
| **Meta-Path Guided** | Follow sequences of relationship types | Multi-hop reasoning chains |

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- `rushdb>=2.0.0` installed

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your RUSHDB_API_KEY
```

## Running the Tutorial

```bash
# Seed the knowledge graph (creates ~200 nodes and relationships)
python seed.py

# Run the extraction strategies demo
python main.py
```

### Seeded Data Structure

The seed creates a **Software Architecture Knowledge Graph** with:

- **CONCEPT** nodes: Design patterns, architectural styles, principles
- **TECHNOLOGY** nodes: Languages, frameworks, tools
- **PATTERN** nodes: Implementation patterns and their contexts
- **IMPLEMENTS** relationships: Concepts implement patterns
- **DEPENDS_ON** relationships: Technologies depend on others
- **USES** relationships: Technologies use concepts
- **SOLVES** relationships: Patterns solve problems

## Expected Output

```
========================================
SUBGRAPH EXTRACTION STRATEGIES
========================================

Strategy 1: N-Hop Neighborhood (k=2)
--------------------------------------
Extracted 47 nodes, 73 relationships
Context tokens: ~1,240 | Format: compact

Strategy 2: Relationship-Type Filter
--------------------------------------
Extracted 23 nodes (IMPLEMENTS edges only)
Context tokens: ~680 | Format: hierarchical

Strategy 3: Importance-Based Pruning
--------------------------------------
Extracted 15 high-importance nodes
Context tokens: ~420 | Format: ranked

Strategy 4: Entity-Centric Extraction
--------------------------------------
Extracted 12 nodes around 'microservices'
Context tokens: ~380 | Format: star-graph

Strategy 5: Meta-Path Guided
--------------------------------------
Extracted 31 nodes via PATTERN→CONCEPT→TECHNOLOGY
Context tokens: ~890 | Format: path-based

========================================
CONTEXT WINDOW COMPARISON
========================================
Strategies ranked by info density (nodes/token ratio):
1. Entity-Centric: 0.032 (best compression)
2. Importance-Based: 0.036
3. Relationship-Type: 0.034
4. Meta-Path: 0.035
5. N-Hop: 0.038
```

## Project Structure

```
subgraph-extraction-strategies-for-window-optimiza-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generates the knowledge graph
└── main.py             # Extraction strategy demonstrations
```

## Key Implementation Details

### Graph Model Design

The knowledge graph uses RushDB's property graph model where:
- **Labels** = node types (CONCEPT, TECHNOLOGY, PATTERN)
- **Relationships** = typed, directional edges with properties
- **Properties** = first-class nodes enabling cross-label queries

### Extraction Pipeline

```sdk
# Each strategy follows the same extraction pattern:
1. Identify seed nodes via semantic search
2. Traverse relationships with configurable depth/types
3. Score and rank extracted nodes
4. Format for LLM consumption
___SPLIT___
// TypeScript: each strategy follows the same pattern:
// 1. Identify seed nodes via semantic search
// 2. Traverse relationships with configurable depth/types
// 3. Score and rank extracted nodes
// 4. Format for LLM consumption
```

## Choosing the Right Strategy

| Scenario | Recommended Strategy |
|----------|---------------------|
| Exploring unfamiliar domains | N-Hop Neighborhood |
| Domain-specific queries (e.g., "uses Python") | Relationship-Type Filter |
| Limited context window, high noise | Importance-Based Pruning |
| Entity-focused analysis | Entity-Centric |
| Multi-step reasoning chains | Meta-Path Guided |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Modeling Best Practices](https://docs.rushdb.com/concepts/property-graph)
- [Vector Search Integration](https://docs.rushdb.com/ai/vector-search)
