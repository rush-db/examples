# Graph-Structured Debate Trees for Multi-Agent Deliberation

A demonstration of how RushDB's property graph model enables complex multi-agent debate systems with hierarchical argument structures, bidirectional relationships, and intelligent traversal.

## What This Demonstrates

- **Graph-native debate modeling**: Arguments as nodes, logical relationships as typed edges
- **Multi-agent deliberation**: Agents as first-class nodes with authored positions and arguments
- **Hierarchical argument trees**: Nested support/refutation chains with depth tracking
- **Bidirectional traversal**: Navigate from conclusion to premises or vice versa
- **Transaction-based writes**: Atomic creation of complex graph structures

## Core Concepts

### The Debate Graph Model

```
DEBATE (topic)
    └── AGENT (participant)
            └── POSITION (stance)
                    └── ARGUMENT (node)
                            ├── SUPPORTS → parent ARGUMENT
                            ├── REFUTES → opposing ARGUMENT
                            ├── RESPONDS_TO → previous ARGUMENT
                            └── AUTHORED_BY → AGENT
```

### Relationship Types

| Type | Direction | Meaning |
|------|-----------|---------|
| `AUTHORED_BY` | out | Agent created this argument |
| `SUPPORTS` | out | Argument supports another |
| `REFUTES` | out | Argument opposes another |
| `RESPONDS_TO` | out | Argument responds to another |
| `PARTICIPATES_AS` | out | Agent plays a role in debate |

## Prerequisites

- Python 3.9+
- RushDB account (free tier works)
- `RUSHDB_API_KEY` from your dashboard

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Demo

```bash
# Generate sample debate data (idempotent — safe to run multiple times)
python seed.py

# Run the main demonstration
python main.py
```

## Expected Output

The demo will:
1. Load or create a debate on "Should autonomous vehicles replace human drivers?"
2. Show agent roles (Proponent, Opponent, Judge)
3. Display the argument tree structure
4. Demonstrate traversal queries (find all arguments by an agent, find supporting arguments)
5. Calculate a simple debate score based on argument strength and coverage

## Project Structure

```
graph-structured-debate-trees-for-multi-agent-deli-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Generate mock debate data
└── main.py            # Core demonstration
```

## Key RushDB Patterns Used

```sdk
# Creating a typed argument node
argument = db.records.create(
    label="ARGUMENT",
    data={
        "text": "Safety statistics support automation",
        "strength": 0.85,
        "depth": 1
    }
)

# Linking agent to argument
db.records.attach(
    source=argument,
    target=agent,
    options={"type": "AUTHORED_BY", "direction": "out"}
)

# Linking argument to parent (support relationship)
db.records.attach(
    source=child_argument,
    target=parent_argument,
    options={"type": "SUPPORTS", "direction": "out"}
)

# Finding arguments by agent relationship
proponent_args = db.records.find({
    "labels": ["ARGUMENT"],
    "where": {
        "AGENT": {"$relation": {"type": "AUTHORED_BY", "direction": "in"}}
    }
})
___SPLIT___
// TypeScript — 2-space indentation for every nested level
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Creating a typed argument node
const argument = await db.records.create({
  label: 'ARGUMENT',
  data: {
    text: 'Safety statistics support automation',
    strength: 0.85,
    depth: 1
  }
})

// Linking agent to argument
await db.records.attach({
  source: argument,
  target: agent,
  options: { type: 'AUTHORED_BY', direction: 'out' }
})

// Linking argument to parent (support relationship)
await db.records.attach({
  source: childArgument,
  target: parentArgument,
  options: { type: 'SUPPORTS', direction: 'out' }
})

// Finding arguments by agent relationship
const proponentArgs = await db.records.find({
  labels: ['ARGUMENT'],
  where: {
    AGENT: { $relation: { type: 'AUTHORED_BY', direction: 'in' } }
  }
})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Modeling Best Practices](https://docs.rushdb.com/concepts/property-graph)
- [API Reference](https://docs.rushdb.com/api)
