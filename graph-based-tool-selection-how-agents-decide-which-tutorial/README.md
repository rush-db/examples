# Graph-Based Tool Selection: How Agents Decide Which Capabilities to Use

This example demonstrates how to use RushDB as a **knowledge graph backend for AI agent tool selection**. Instead of hardcoding "if/else" logic to pick tools, agents can query a graph of capabilities and let relationships guide the selection process.


## What It Demonstrates

- **Capability Graph**: Model tools as nodes with typed relationships to their capabilities
- **Intent Matching**: Use vector semantic search to match user goals to tool capabilities
- **Dependency Resolution**: Let agents traverse the graph to find tools that satisfy requirements
- **Dynamic Tool Discovery**: Query RushDB at runtime to discover compatible tool combinations

## Architecture

```
┌─────────────┐       CAN_USE       ┌─────────────────────┐
│    GOAL     │────────────────────▶│      CAPABILITY      │
│ (user task) │                     │  (search, compute,   │
└─────────────┘                     │   read, write, ...)  │
        │                          └──────────┬──────────┘
        │ REQUIRES                             │
        ▼                                      │ ENABLES
┌─────────────┐       NEEDS          ┌─────────┴──────────┐
│  REQUIRED   │─────────────────────▶│       TOOL          │
│  CONTEXT    │                     │  (name, version,    │
└─────────────┘                     │   params, ...)      │
                                     └──────────┬──────────┘
                                                │
                                                │ DEPENDS_ON
                                                ▼
                                     ┌─────────────────────┐
                                     │    DEPENDENCY        │
                                     │  (auth, storage, ...)│
                                     └─────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (free tier works)
- `rushdb>=2.0.0` and `sentence-transformers` installed

## Setup

### 1. Clone and install dependencies

```bash
cd graph-based-tool-selection-how-agents-decide-which-tutorial
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your RUSHzDB_API_TOKEN
```

### 3. Create the vector index (one-time setup)

```bash
python main.py --setup
```

This creates a vector index on the `description` property of `TOOL` records, enabling semantic search for capability matching.

### 4. Run the demo

```bash
python main.py
```

The script will:
1. Seed the graph with sample tools and capabilities
2. Demonstrate semantic intent matching
3. Show dependency-aware tool selection
4. Display graph traversal queries

## Expected Output

```
=== SEEDING TOOL GRAPH ===
✓ Created 12 tools
✓ Created 8 capabilities
✓ Created 15 dependencies
✓ Built capability index

=== SEMANTIC TOOL DISCOVERY ===
Query: "I need to fetch data from an external API"
Best match: WebFetchTool (similarity: 0.923)
Fallback: FileReadTool (similarity: 0.687)

=== TOOL SELECTION BY REQUIREMENTS ===
Goal: analyze_sales_data
Required context: ["financial_data", "historical_quarters"]
Selected tools:
  - DataAggregator (satisfies: time_series_analysis)
  - ReportGenerator (satisfies: financial_reports)
  - APIConnector (satisfies: external_data)

=== DEPENDENCY RESOLUTION ===
Tool: MLModelTrainer
Direct dependencies:
  - DataPreprocessor
  - ModelRegistry
Transitive dependencies:
  - DataPreprocessor
  - ModelRegistry
  - CachedDataset
  - ModelVersioning
  - AuthenticationService

=== CAPABILITY-BASED FILTERING ===
Capabilities required: ["read", "compute", "write"]
Tools with ALL capabilities:
  - DataPipelineOrchestrator
  - ETLProcessor
  - ReportGenerator
```

## How It Works

### 1. Semantic Capability Matching

When an agent receives a goal like "fetch and analyze sales data", we:
1. Embed the goal as a query vector
2. Search the tool descriptions for semantic similarity
3. Return ranked tools with similarity scores

```sdk
results = db.ai.search({
    "propertyName": "description",
    "query": goal,
    "labels": ["TOOL"],
    "limit": 5
})
```

### 2. Graph-Based Requirement Resolution

For complex goals requiring multiple capabilities:
1. Find all capabilities matching the intent
2. Traverse relationships to find tools that provide those capabilities
3. Resolve dependencies to ensure all prerequisites are satisfied

```sdk
# Find tools that provide a specific capability
tools = db.records.find({
    "labels": ["TOOL"],
    "where": {
        "CAPABILITY": {
            "type": "provides",
            "name": "data_analysis"
        }
    }
})
```

### 3. Dependency-Aware Selection

When selecting a tool, we traverse the dependency graph to ensure all prerequisites are available:

```sdk
# Get all dependencies (transitive closure)
def get_all_dependencies(tool):
    deps = db.records.find({
        "labels": ["TOOL"],
        "where": {
            "TOOL": {
                "$relation": {"type": "DEPENDS_ON", "direction": "out"},
                "id": tool.id
            }
        }
    })
    return deps
```

## Key Design Patterns

### Pattern 1: Capability Nodes

Tools don't have hardcoded capability lists. Instead, they're linked to `CAPABILITY` nodes:


```python
{
    "type": "TOOL",
    "name": "DataAggregator",
    "description": "Aggregates data from multiple sources"
}
---
(TOOL)-[:ENABLES]->(CAPABILITY {name: "data_aggregation"})
(TOOL)-[:ENABLES]->(CAPABILITY {name: "time_series_analysis"})
```

### Pattern 2: Intent Semantics

Each tool's description is indexed for semantic search. This allows flexible, natural-language tool discovery:

```python
"I need to calculate statistics" → matches StatisticalAnalyzer
"fetch content from URLs" → matches WebFetchTool
"persist results to disk" → matches FileWriteTool
```

### Pattern 3: Dependency Edges

The `DEPENDS_ON` relationship forms a DAG, allowing agents to:
- Check if a tool's dependencies are satisfied
- Auto-select missing dependencies
- Avoid circular dependencies

## Extending This Example

- Add more tools and capabilities
- Implement multi-agent coordination via shared tool registry
- Add tool versioning and compatibility constraints
- Implement cost/latency modeling for tool selection

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph-Based Tool Selection Article](https://rushdb.com/blog/graph-based-tool-selection)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/graph-based-tool-selection-how-agents-decide-which-tutorial)
