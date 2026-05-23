# Semantic Rollback: Reverting Knowledge Base State

A complete tutorial demonstrating how to implement semantic rollback in a production knowledge base using RushDB.

## What This Tutorial Demonstrates

This project shows how to build a semantic rollback system that can revert a knowledge base to a previous state after problematic updates. It's designed for AI memory and knowledge management systems.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Knowledge Base Architecture                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐  │
│   │   Graph     │     │   Vector    │     │    Rollback         │  │
│   │   Layer     │◄───►│   Index     │     │    Controller       │  │
│   │             │     │             │     │                     │  │
│   │ • Articles  │     │ • Article    │     │ • Snapshot Capture  │  │
│   │ • Concepts  │     │   content   │     │ • Trigger Detection │  │
│   │ • Relations │     │ • Similarity │     │ • State Revert      │  │
│   └─────────────┘     └─────────────┘     └─────────────────────┘  │
│          │                   │                      │              │
│          └───────────────────┴──────────────────────┘              │
│                              │                                       │
│                    ┌─────────▼─────────┐                            │
│                    │     RushDB        │                            │
│                    │  (Neo4j Backend)  │                            │
│                    └───────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow Steps

1. **Prerequisite**: Graph for entities/relationships + Vector index for similarity
2. **Step 1**: Capture semantic snapshot before updates
3. **Step 2**: Detect rollback trigger (manual flag, LLM confidence)
4. **Step 3**: Revert graph subgraph while preserving unrelated nodes
5. **Step 4**: Rebuild affected vector index entries atomically

## Prerequisites

- Python 3.10+
- RushDB account ([Sign up free](https://rushdb.com))
- `rushdb>=2.0.0` Python package
- `sentence-transformers` for embedding generation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

### 3. Seed the Knowledge Base

This creates mock articles, concepts, and relationships:

```bash
python seed.py
```

The seed script creates:
- 20 articles with realistic content
- 10 concept nodes (topics/categories)
- Relationships between articles and concepts
- A vector index on article content for semantic search

### 4. Run the Tutorial

```bash
python main.py
```

## Project Structure

```
semantic-rollback-reverting-knowledge-base-state-a-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── seed.py           # Mock data generation script
└── main.py           # Main semantic rollback implementation
```

## Expected Output

The main script demonstrates:

1. **Snapshot Capture**: Records the current state of target articles
2. **Problematic Updates**: Simulates updates that degrade quality
3. **Rollback Detection**: Shows three trigger mechanisms
4. **Graph Restoration**: Reverts only affected nodes, preserves others
5. **Vector Index Rebuild**: Restores semantic search consistency

Example output:

```
=== Semantic Rollback System Demo ===

1. Capturing snapshot of 3 articles...
   Snapshot ID: snap_abc123
   Captured: [article_ml_intro, article_ml_supervised, article_python_basics]

2. Applying problematic updates...
   ✓ Updated 3 articles with degraded content

3. Detecting rollback triggers...
   [MANUAL] Rollback requested by user
   [CONFIDENCE] LLM confidence dropped from 0.92 to 0.34
   [VALIDATION] External validator flagged content quality issues

4. Executing semantic rollback...
   ✓ Reverted 3 articles to snapshot snap_abc123
   ✓ Preserved 17 unrelated articles
   ✓ Preserved 10 concept nodes

5. Rebuilding vector index...
   ✓ Updated 3 vectors in index
   ✓ Semantic search restored
```

## How It Works

### Snapshot Capture

Before applying updates, we capture a snapshot containing:

```sdk
# Capture snapshot
snapshot = capture_snapshot(db, article_ids)
# Snapshot stores: {record_id, data, vectors, relationships}
___SPLIT___
// Snapshot capture in TypeScript (conceptual)
const snapshot = await captureSnapshot(db, articleIds)
```

### Rollback Triggers

Three trigger mechanisms are demonstrated:

1. **Manual Trigger**: User explicitly requests rollback
2. **LLM Confidence**: Automated detection when embedding confidence drops below threshold
3. **External Validation**: Third-party system flags quality issues

### Graph Subgraph Revert

The rollback operation:

- Reverts only the affected article nodes
- Preserves all unrelated nodes and relationships
- Maintains graph integrity throughout

```sdk
# Revert to snapshot
rollback_to_snapshot(db, snapshot)
___SPLIT___
// TypeScript conceptual equivalent
await rollbackToSnapshot(db, snapshot)
```

### Vector Index Rebuild

After graph restoration:

- Re-embed restored content
- Update only affected vector entries
- Maintain index consistency

## API Reference

For detailed RushDB SDK documentation, visit: https://docs.rushdb.com

## Pricing Note

RushDB charges by **KnowledgeUnits (KU)** for write operations:
- Record created: 0.5 KU
- Property stored: 1 KU per property
- Relationship: 0.25 KU per link
- Embedding generated: 5 KU per record
- Vector search: 5 KU per call
- **Reads are always FREE**

See: https://rushdb.com/pricing

## License

MIT License - See LICENSE file for details.
