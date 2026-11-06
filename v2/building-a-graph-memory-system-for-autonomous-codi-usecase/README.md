# Building a Graph Memory System for Autonomous Coding Agents

A practical demonstration of how RushDB's property graph architecture solves the **context-window overflow problem** that plagues autonomous coding agents working on long-horizon tasks.

## The Problem: Context Windows Fail at Scale

When a coding agent works on a complex bug across hundreds of files and many sessions, it faces a fundamental limitation:

1. **Each session re-explains the problem**: The agent forgets everything from previous sessions
2. **RAG-only retrieval loses relationships**: Vector search returns similar code snippets but loses "why this file was ruled out"
3. **Context window overflow**: As the codebase grows, the agent wastes tokens re-explaining what it already "knew"

## The Solution: A Persistent Graph Memory

Instead of relying on expanding context windows, a graph-memory system:

- **Remembers investigation trails**: "I already checked `/auth/middleware.ts` — the bug wasn't there"
- **Captures relationships**: "This function calls that function, which imports this module"
- **Enables traversal queries**: "Show me the full dependency chain for this bug's root cause"
- **Learns from past sessions**: "In similar bugs, the root cause was usually in the validation layer"

## What This Demo Shows

### 1. The Context Window Failure Pattern
Simulates how a naive agent repeatedly re-explains the same context, burning through tokens.

### 2. Graph Memory Architecture
How RushDB's labels and relationships model a code entity graph:
- **Nodes**: Files, functions, bugs, investigation sessions, hypotheses
- **Edges**: `INVESTIGATED`, `RULED_OUT`, `CALLS`, `DEPENDS_ON`, `CAUSED_BY`

### 3. Bug-Hunting Agent with Memory
A concrete autonomous agent that:
- Investigates a bug by traversing the dependency graph
- Records each file it checks (and whether it ruled it out)
- Asks "show me the dependency chain for this bug's root cause"
- Answers: "The bug is caused by `validateToken` in `/auth/jwt.ts`, which is called by 3 other files"

### 4. Graph vs. Vector Search for Code
Why edges are more useful than flat vector retrieval for code understanding:
- **Vector search**: "Find files similar to 'authentication token validation'"
- **Graph traversal**: "Find all files that depend on the file where the bug lives"

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Graph Memory Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐     INVESTIGATED    ┌──────────────────────┐   │
│   │  BUG #42  │────────────────────▶│  /auth/jwt.go        │   │
│   └──────────┘                      └──────────────────────┘   │
│        │                                    │                   │
│        │ CAUSED_BY                         │ CALLS             │
│        ▼                                    ▼                   │
│   ┌──────────┐                      ┌──────────────────────┐   │
│   │validate  │                      │  /api/middleware.go  │   │
│   │Token()   │                      └──────────────────────┘   │
│   └──────────┘                            │                    │
│        │                                   │ DEPENDS_ON        │
│        │ DEFINED_IN                       ▼                    │
│        ▼                            ┌──────────────────────┐   │
│   ┌──────────┐                      │  /auth/middleware.go │   │
│   │jwt.ts    │                      │  ← RULED_OUT=true   │   │
│   └──────────┘                      └──────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- A RushDB account ([get one free](https://app.rushdb.com))

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RushDB API key
```

### 3. Seed the Database

This creates a realistic codebase graph with bugs, files, functions, and investigation history:

```bash
python seed.py
```

Expected output:
```
Creating 50 code entity records (files, functions, modules)...
Creating 3 bugs...  
Creating investigation sessions and dependency chains...  
Creating historical investigation records...
Graph memory seeded successfully!
  - 50 code entities
  - 3 bugs with dependency chains
  - 75 investigation records
```

### 4. Run the Demo

```bash
python main.py
```

This demonstrates:
1. **Context window failure** (simulated token waste)
2. **Graph memory query** (finding the root cause)
3. **Ruled-out investigation trail** (what was already checked)
4. **Dependency chain traversal** (graph traversal for code understanding)
5. **Comparison**: Vector search vs. graph traversal for code understanding

## Project Structure

```
.
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── seed.py              # Seeds the graph with mock codebase data
├── data/
│   └── mock_entities.py  # Mock code entity definitions
└── main.py              # Main demonstration script
```

## Key RushDB Patterns Demonstrated

### Creating Records with Labels
```sdk
bug = db.records.create(
    label="BUG",
    data={
        "id": "BUG-1234",
        "title": "Authentication fails for expired tokens",
        "severity": "high"
    }
)
```

### Building Relationships (Graph Edges)
```sdk
# Link a bug to the file where its root cause was found
db.records.attach(
    source=bug,
    target=root_cause_file,
    options={"type": "ROOT_CAUSE_IN", "direction": "out"}
)

# Record that an investigation session checked a file
db.records.attach(
    source=investigation,
    target=file,
    options={"type": "INVESTIGATED", "direction": "out"}
)
```

### Graph Traversal Queries
```sdk
# Find all files checked during investigation of BUG-1234
investigated = db.records.find({
    "labels": ["FILE"],
    "where": {
        "INVESTIGATION": {
            "$relation": {"type": "INVESTIGATED", "direction": "in"},
            "BUG": {"$relation": {"type": "FOR_BUG", "direction": "in"}},
            "bug_id": "BUG-1234"
        }
    }
})
```

## Why This Beats Vector-Only Retrieval

| Capability | Vector RAG | Graph Memory |
|------------|-----------|--------------|
| Find similar code | ✅ | ❌ |
| Remember what was already checked | ❌ | ✅ |
| Traverse dependency chains | ❌ | ✅ |
| Ask "why was this ruled out?" | ❌ | ✅ |
| Learn from past bug fixes | Limited | ✅ |
| Query "show cause chain" | ❌ | ✅ |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Concepts](https://docs.rushdb.com/concepts/property-graph)
- [Relationship Queries](https://docs.rushdb.com/api/records/find)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-a-graph-memory-system-for-autonomous-codi-usecase)
