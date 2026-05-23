# Building Tool-Use Graphs with RushDB

This project demonstrates how to model callable functions and their dependencies as a property graph using RushDB. You'll learn how to store function metadata, create relationships between tools, and query the graph for dependency analysis and tool orchestration.

## What You'll Build

A **tool registry graph** where:
- Each node is a callable function with metadata (name, description, parameters, return type)
- Edges represent relationships: `DEPENDS_ON`, `CALLS`, `PROVIDES`, `REQUIRES`
- Enables AI agents to discover and chain tools based on capabilities and dependencies

## Use Cases

- **AI Agent Tool Orchestration**: Let agents dynamically discover and sequence tools
- **Dependency Analysis**: Find all functions a tool requires before execution
- **Capability Matching**: Search for tools by what they can provide
- **Graph-Based Planning**: Traverse relationships to build execution plans

## Prerequisites

- Python 3.9+
- RushDB account ([sign up free](https://app.rushdb.com))
- `rushdb>=2.0.0`

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

### 3. Seed the Database

```bash
python seed.py
```

This creates a tool registry with 12 interconnected functions representing a typical AI agent toolkit:

- **File Operations**: read_file, write_file, list_directory
- **Search**: web_search, vector_search, semantic_lookup
- **Computation**: calculator, formatter, validator
- **System**: executor, logger, notifier

## Running the Demo

```bash
python main.py
```

## Expected Output

```
=== Tool Registry Graph Demo ===

[1] Tool Discovery: Functions that provide 'data'
  - semantic_lookup (Provides: data analysis via semantic search)
  - calculator (Provides: numeric data processing)
  - web_search (Provides: external data retrieval)

[2] Dependency Chain: Functions required by 'process_document'
  - validator → notifier → logger
  - read_file
  - formatter

[3] Capability Search: Functions matching 'search'
  - semantic_lookup (Semantic search for context)
  - vector_search (Vector similarity search)
  - web_search (Web content search)

[4] Graph Statistics
  Total tools: 12
  Total relationships: 18

[5] Upstream Dependencies for 'executor'
  - logger (REQUIRED_BY)
  - notifier (REQUIRED_BY)
  - validator (REQUIRED_BY)
  - formatter (REQUIRED_BY)

[6] Downstream Dependents of 'web_search'
  - semantic_lookup (CALLS)
  - process_document (DEPENDS_ON)
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Generate mock tool registry
└── main.py             # Main demonstration
```


## Key RushDB Patterns Demonstrated

### Creating Tool Records
```sdk
tool = db.records.create(
    label="TOOL",
    data={
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {"query": "string", "limit": "integer"},
        "returnType": "array",
        "provides": ["external data", "web content"]
    }
)
___SPLIT___
const tool = await db.records.create({
  label: 'TOOL',
  data: {
    name: 'web_search',
    description: 'Search the web for information',
    parameters: { query: 'string', limit: 'integer' },
    returnType: 'array',
    provides: ['external data', 'web content']
  }
})
```


### Creating Relationships
```sdk
db.records.attach(
    source=formatter,
    target=logger,
    options={"type": "REQUIRES"}
)
___SPLIT___
await db.records.attach({
  source: formatter,
  target: logger,
  options: { type: 'REQUIRES' }
})
```

### Querying by Capability
```sdk
results = db.ai.search({
    "propertyName": "provides",
    "query": "data",
    "labels": ["TOOL"],
    "limit": 10
})
___SPLIT___
const { data: results } = await db.ai.search({
  propertyName: 'provides',
  query: 'data',
  labels: ['TOOL'],
  limit: 10
})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Concepts](https://docs.rushdb.com/concepts)
- [GitHub Examples](https://github.com/rush-db/examples)
