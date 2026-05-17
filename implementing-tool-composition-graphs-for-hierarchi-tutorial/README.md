# Implementing Tool Composition Graphs for Hierarchical Agent Task Decomposition

This project demonstrates how to use RushDB as a memory layer for building tool composition graphs that enable hierarchical task decomposition in multi-agent systems.


## What This Demonstrates

- **Graph-based tool modeling**: Representing tools as nodes with composition relationships
- **Hierarchical decomposition**: Breaking complex tasks into sub-tasks using directed edges
- **Tool execution traces**: Recording which agent used which tools and when
- **Composition traversal**: Querying the graph to understand tool dependencies
- **Transactional consistency**: Using transactions to create atomic tool compositions

## Core Concepts

### Tool Composition Graph Architecture

```
┌─────────────┐     DECOMPOSES_INTO     ┌─────────────────┐
│   Complex   │ ──────────────────────▶ │  Sub-Component  │
│    Task     │                         │     Tool        │
└─────────────┘                         └────────┬────────┘
                                                 │
                              COMPOSED_OF ───────┼─────── COMPOSED_OF
                                                 │
┌─────────────┐                         ┌────────▼────────┐
│   Simple   │ ◀─────────────────────── │  Primitive      │
│    Tool    │       COMPOSED_OF        │     Tool        │
└─────────────┘                          └─────────────────┘
```

### Labels Used

| Label | Purpose |
|-------|---------|
| `TOOL` | Atomic tool capability |
| `COMPOSITE_TOOL` | Tool composed of sub-tools |
| `TASK` | Task instance |
| `SUBTASK` | Decomposed sub-task |
| `AGENT` | Agent that executes tools |


### Relationships

| Type | Direction | Purpose |
|------|-----------|---------|
| `DECOMPOSES_INTO` | Task → Subtask | Task hierarchy |
| `COMPOSED_OF` | Composite → Component | Tool composition |
| `USES` | Agent → Tool | Tool assignment |
| `EXECUTED` | Task → Tool | Execution trace |

## Prerequisites

- Python 3.9+
- RushDB account with API key
- `rushdb>=2.0.0`

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running

```bash
python main.py
```

The script will:
1. Seed the database with sample tools and compositions
2. Decompose a complex task hierarchically
3. Query and display the resulting graph structure
4. Demonstrate relationship traversal

## Expected Output

```
=== Tool Composition Graph Demo ===

[1] Created 5 primitive tools
[2] Created 3 composite tools with compositions
[3] Decomposed task 'Build Customer Portal' into 5 sub-tasks
[4] Queried composition graph - found 3 composite tools
[5] Traversed task hierarchy - found 5 sub-tasks for root task

=== Graph Structure ===

Primitive Tools:
  - auth_user: User authentication with OAuth2
  - db_query: Execute database queries
  - send_email: Send transactional emails
  - generate_pdf: Generate PDF documents
  - log_activity: Log user activity

Composite Tools:
  - user_onboarding: auth_user + send_email + log_activity
  - report_generation: db_query + generate_pdf + log_activity
  - customer_portal: user_onboarding + report_generation + log_activity

Task Hierarchy (Build Customer Portal):
  - Build Customer Portal (root)
    ├── Setup User Authentication (primitive: auth_user)
    ├── Create User Dashboard (composite: report_generation)
    ├── Send Welcome Email (primitive: send_email)
    ├── Generate Privacy Report (composite: report_generation)
    └── Log Portal Creation (primitive: log_activity)
```

## Key RushDB Features Used

- **Records**: Store tools, tasks, and agents as typed nodes
- **Relationships**: Create directed edges for composition and decomposition
- **Transactions**: Atomic creation of tool compositions
- **Graph Queries**: Filter by related records using label-based filtering

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Modeling](https://docs.rushdb.com/concepts/property-graph)
- [Relationship Queries](https://docs.rushdb.com/api/records#finding-by-relationships)
