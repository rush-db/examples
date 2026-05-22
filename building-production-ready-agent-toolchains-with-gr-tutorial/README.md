# Building Production-Ready Agent Toolchains with Graph-Native Orchestration

A comprehensive tutorial demonstrating how to build production-grade agent toolchains using RushDB's property graph and vector search capabilities.

## What This Tutorial Demonstrates

- **Graph Schema Design**: Define nodes for tools, agents, and tasks; edges for dependencies and call hierarchy
- **Semantic Tool Routing**: Use RushDB's vector search to find relevant tools by description similarity to agent intent
- **Graph-Native Orchestration**: Traverse the graph, execute tool nodes, and write results back as node properties
- **Failure Handling**: Graph structure enables retry from any checkpoint, not just the beginning
- **Execution Trace Analysis**: Run queries on execution history to understand agent decision-making

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works perfectly)
- `pip` for package management

## Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd building-production-ready-agent-toolchains-with-gr-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your RushDB API key
# Get your API key at: https://app.rushdb.com/settings/api-keys
```

### 3. Seed the Database (Generates Mock Data)

```bash
python seed.py
```

This creates:
- 10 tool definitions with semantic descriptions
- 3 agent profiles with different intents
- Execution history for tracing analysis

## Running the Tutorial

```bash
python main.py
```

The tutorial executes in phases:

### Phase 1: Schema Setup
Creates graph structure for tools, agents, and tasks with appropriate relationships.

### Phase 2: Vector Index Creation
Creates a vector index on tool descriptions for semantic search.

### Phase 3: Semantic Tool Routing
Demonstrates finding relevant tools by matching agent intent against tool descriptions.

### Phase 4: Orchestrated Execution
Traverses the graph, executes tools in dependency order, and records results.

### Phase 5: Failure Simulation & Recovery
Shows how to resume from a checkpoint after simulated failure.

### Phase 6: Execution Trace Analysis
Queries the execution history to understand decision patterns.

## Expected Output

```
=== Phase 1: Graph Schema Setup ===
✓ Created 10 TOOL nodes
✓ Created 3 AGENT nodes
✓ Created 10 TASK nodes
✓ Created relationship edges

=== Phase 2: Vector Index ===
✓ Created vector index on TOOL.description
✓ Indexed 10 tool descriptions

=== Phase 3: Semantic Tool Routing ===
Query: "I need to analyze customer sentiment from reviews"
Top 3 relevant tools:
  1. [0.94] sentiment_analysis - Analyze text for emotional tone
  2. [0.87] text_summarizer - Summarize long documents
  3. [0.76] keyword_extractor - Extract key terms and phrases

=== Phase 4: Orchestrated Execution ===
Execution order: [fetch_data -> process_data -> generate_insights -> send_notification]
✓ fetch_data completed: 245 records fetched
✓ process_data completed: 198 records processed
✓ generate_insights completed: 15 insights generated
✓ send_notification completed: notification sent to 3 recipients

=== Phase 5: Failure & Recovery ===
Simulated failure at: generate_insights
✓ Checkpoint saved at: process_data
✓ Recovery: Resuming from process_data

=== Phase 6: Execution Trace Analysis ===
Recent tool calls in last 24h:
  - fetch_data: 12 calls (100% success)
  - process_data: 10 calls (100% success)
  - generate_insights: 8 calls (75% success)
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      RUSHDBSDK                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐               │
│   │  TOOL   │────▶│  AGENT  │────▶│  TASK   │               │
│   │  node   │     │  node   │     │  node   │               │
│   └────┬────┘     └────┬────┘     └────┬────┘               │
│        │               │               │                     │
│        ▼               ▼               ▼                     │
│   ┌─────────────────────────────────────────┐                │
│   │           RELATIONSHIPS                 │                │
│   │  - USES (agent → tool)                  │                │
│   │  - DEPENDS_ON (task → task)             │                │
│   │  - EXECUTED_BY (task → agent)           │                │
│   │  - CALLED (tool → tool)                 │                │
│   └─────────────────────────────────────────┘                │
│                                                              │
│   ┌─────────────────────────────────────────┐                │
│   │         VECTOR INDEX                    │                │
│   │  - Tool descriptions embedded           │                │
│   │  - Semantic similarity search          │                │
│   └─────────────────────────────────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key RushDB Features Used

| Feature | Method | Purpose |
|---------|--------|---------|
| Record Creation | `db.records.create()` | Create tool, agent, task nodes |
| Relationships | `db.records.attach()` | Connect nodes with typed edges |
| Vector Index | `db.ai.indexes.create()` | Enable semantic search |
| Semantic Search | `db.ai.search()` | Find tools by description similarity |
| Transactions | `db.transactions.begin()` | Atomic execution of tool chains |
| Query | `db.records.find()` | Filter nodes and traverse relationships |

## Why RushDB for Agent Toolchains?

1. **Zero-Schema Flexibility**: Add new tools and agents without migrations
2. **Native Graph Structure**: Model tool dependencies and call hierarchies naturally
3. **Vector Search Built-In**: Semantic tool routing without external vector DB
4. **ACID Transactions**: Reliable execution of tool chains
5. **Free Reads**: Query execution traces without per-query costs

## Documentation

- [RushDB SDK Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdks/python)
- [Graph Data Modeling](https://docs.rushdb.com/concepts/schema)

## License

MIT License - See LICENSE file for details.
