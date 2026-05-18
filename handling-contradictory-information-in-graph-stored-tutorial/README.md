# Handling Contradictory Information in Graph-Stored Knowledge

A tutorial demonstrating how to use RushDB's property graph model to store, track, and reason about contradictory information in knowledge bases.

## Overview

Real-world knowledge bases often contain conflicting information from multiple sources, time periods, or perspectives. This tutorial shows how RushDB's native graph capabilities make it natural to model, discover, and resolve contradictions.

## What You'll Learn

- **Modeling contradictions** as first-class graph relationships
- **Attributing facts to sources** with timestamps and confidence scores
- **Discovering contradictions** through graph traversal queries
- **Resolving conflicts** with evidence-based reasoning
- **Version tracking** for evolving knowledge

## Prerequisites

- Python 3.10+
- A RushDB account (free tier available at [rushdb.com](https://rushdb.com))
- `rushdb>=2.0.0` Python SDK

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

Get your API key from the [RushDB dashboard](https://dash.rushdb.com).

### 3. Seed the Database

The seed script creates a realistic knowledge graph with contradictory claims:

```bash
python seed.py
```

This generates approximately 20 facts across multiple domains (science, health, history) with conflicting sources.

### 4. Run the Tutorial

```bash
python main.py
```

## Project Structure

```
handling-contradictory-information-in-graph-stored-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Mock data generator
└── main.py             # Tutorial demonstration
```

## Key Concepts

### Data Model

```
┌─────────────┐         ┌─────────────┐
│    FACT     │─────────│   SOURCE    │
│             │ASSERTED │             │
│ - claim     │   BY    │ - name      │
│ - domain    │         │ - type      │
│ - timestamp │         │ - url       │
└─────────────┘         └─────────────┘
       │
       │ CONTRADICTS
       ▼
┌─────────────┐
│    FACT     │
│             │
│ - claim     │
│ - domain    │
│ - timestamp │
└─────────────┘
```

### Why Graph?

Traditional databases force you to:
- Create complex join tables for contradictions
- Build elaborate WHERE clauses to find conflicts
- Maintain separate versioning tables

RushDB's graph model makes this natural:
- `CONTRADICTS` relationships are first-class citizens
- Traversal queries find related contradictions in O(1) relationship lookups
- Sources and facts are nodes you can query independently or together

## Expected Output

Running `main.py` produces:

1. **Database Status** - Shows current record counts
2. **All Sources** - Lists all knowledge sources in the graph
3. **Domain Analysis** - Facts grouped by domain with contradiction counts
4. **Contradiction Pairs** - All pairs of conflicting facts with evidence
5. **Resolution Example** - Demonstrates marking a contradiction as resolved
6. **Confidence Analysis** - Facts sorted by source reliability scores

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Modeling Best Practices](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/handling-contradictory-information-in-graph-stored-tutorial)
