# Building a Graph-Backed Plan Execution Tracker with Milestone Dependencies

This project demonstrates how to use RushDB's property graph capabilities to build a plan execution tracker with complex milestone dependency chains.

## What You'll Learn

- Modeling hierarchical plans with milestone dependencies as a graph
- Creating bidirectional relationships between milestones
- Querying dependency chains using relationship traversal patterns
- Tracking execution status across interdependent milestones
- Identifying blocked vs. ready-to-execute milestones

## Data Model

```
Plan
  └── HAS_MILESTONE ──► Milestone
                            │
                            └─── DEPENDS_ON ──► Milestone (other)
                            │
                            └─── HAS_TASK ──► Task
```

- **Plan**: Top-level container with name, description, status
- **Milestone**: Individual checkpoint with dependencies on other milestones
- **Task**: Actionable work item within a milestone

## Prerequisites

- Python 3.10+
- RushDB account (get one at https://rushdb.com)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set your RUSHDB_API_KEY
   ```

3. **Seed sample data:**
   ```bash
   python seed.py
   ```
   This creates sample plans with milestones that have cross-dependencies.

## Running the Demo

```bash
python main.py
```

## Expected Output

The demo will:
1. Query all plans with their milestones
2. Find milestones blocked by incomplete dependencies
3. Identify ready-to-execute milestones (all dependencies met)
4. Show the full dependency chain for any milestone
5. Update milestone status and show cascading effects

## Project Structure

```
├── main.py          # Main demo script
├── seed.py          # Sample data generator
├── requirements.txt  # Python dependencies
├── .env.example     # Environment template
└── README.md        # This file
```

## Key RushDB Patterns Used

- **Transactions**: Atomic creation of plans with milestones and dependencies
- **Relationships**: `HAS_MILESTONE`, `DEPENDS_ON`, `HAS_TASK`
- **Graph traversal**: Query by related record labels and IDs
- **Upsert**: Idempotent updates to plan/milestone status

## Further Reading

- RushDB SDK: https://docs.rushdb.com/sdk/python
- Graph Modeling: https://docs.rushdb.com/concepts/property-graph
