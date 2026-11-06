# Building a Semantic Dependency Graph for Code Interpretation Agents

This example demonstrates how to build and query a semantic dependency graph for change impact analysis — the canonical use case for AI-augmented code review and CI systems.

## What It Demonstrates

1. **Schema Design**: How to model code entities (functions, classes, services, tests) and their relationships in RushDB
2. **Change Impact Analysis**: Tracing the full blast radius of a shared utility modification across services and tests
3. **Hybrid Queries**: Combining graph traversal with semantic similarity search to find structurally-related code
4. **Contrast with Naive Approach**: Why N vector searches miss structural dependencies

## The Scenario

A pull request modifies a shared utility function `format_currency()`. The agent needs to:
1. Find all direct callers of `format_currency`
2. Identify services that transitively depend on it
3. Surface tests that cover the affected code path
4. Score related functions by semantic similarity to detect potential impact

## Prerequisites

- Python 3.10+
- RushDB API key ([get one free](https://app.rushdb.com))

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and fill in your API key
cp .env.example .env

# Generate mock code dependency data (idempotent)
python seed.py
```

## Running

```bash
python main.py
```

Expected output:
- Shows the naive approach failing to find structural dependencies
- Demonstrates RushDB's hybrid graph + vector query
- Displays the full impact chain for `format_currency`

## Project Structure

```
├── README.md         # This file
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
├── seed.py          # Generates mock code dependency graph
└── main.py          # Change impact analysis demonstration
```

## RushDB Documentation

- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
- [Property Graph Concepts](https://docs.rushdb.com/concepts/property-graph)
- [Vector Search](https://docs.rushdb.com/features/vector-search)
