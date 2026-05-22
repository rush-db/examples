# Implementing Weighted Priority Queues with Graph-Based Scheduling

A practical tutorial demonstrating how to build a weighted priority queue scheduling system using RushDB's property graph capabilities.

## Overview

This project implements a task scheduling system where:
- Tasks have weighted priorities (1-10 scale)
- Tasks can have dependencies (graph edges)
- Scheduling uses a weighted topological sort algorithm
- RushDB stores tasks as nodes and dependencies as relationships

## Core Concepts Demonstrated


- **Weighted Priority Queues**: Tasks prioritized by a weight score combining urgency, importance, and deadline factors
- **Graph-Based Scheduling**: DAG-based task dependencies with topological ordering
- **Relationship Traversal**: Using RushDB relationships to track task dependencies
- **Transactional Operations**: Atomic task creation with dependency linking

## Prerequisites

- Python 3.10+
- RushDB account (free tier available at https://rushdb.com)
- `rushdb>=2.0.0` Python SDK

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API key
```


## Running the Example

```bash
# Seed mock task data
python seed.py

# Run the weighted priority queue scheduler
python main.py
```


## Expected Output

```
=== Weighted Priority Queue Scheduler ===

Original tasks (as created):
  • Design API endpoint (priority=7, weight=8.0)
  • Implement database schema (priority=8, weight=9.0)
  • Write authentication module (priority=9, weight=10.0)
  • Create frontend components (priority=6, weight=7.0)
  • Write integration tests (priority=5, weight=6.0)

Dependency graph:
  • Write authentication module depends on: Design API endpoint, Implement database schema
  • Write integration tests depends on: Write authentication module, Create frontend components
  • Create frontend components depends on: Design API endpoint

Scheduled execution order (weighted topological sort):
  1. Design API endpoint (weight=8.0, ready)
  2. Implement database schema (weight=9.0, ready)
  3. Write authentication module (weight=10.0, dependencies met)
  4. Create frontend components (weight=7.0, dependencies met)
  5. Write integration tests (weight=6.0, dependencies met)

Tasks by priority tier:
  Critical (weight >= 9): Write authentication module, Implement database schema
  High (weight 7-9): Design API endpoint, Create frontend components
  Standard (weight < 7): Write integration tests
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TASK (Node)                              │
│  id: string                                                 │
│  name: string                                               │
│  priority: number (1-10)                                    │
│  weight: number (computed)                                  │
│  deadline: datetime                                         │
│  estimated_hours: number                                    │
│  status: 'pending' | 'scheduled' | 'completed'             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ DEPENDS_ON (Relationship)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 WEIGHTED PRIORITY QUEUE                      │
│  • Sorted by weight (priority × deadline_factor × effort)   │
│  • Topological constraint: dependencies first               │
│  • Ready queue: all dependencies satisfied                  │
└─────────────────────────────────────────────────────────────┘
```

## Weight Calculation Formula

```
weight = (base_priority / 10.0) × deadline_factor × effort_factor

where:
  deadline_factor = 1.0 if deadline > 24h away
                   = 1.5 if deadline < 24h away
                   = 2.0 if deadline < 4h away
  effort_factor = 1.0 + (estimated_hours / 8.0)
```

## Key RushDB Operations Used

```sdk
# Create task with priority metadata
task = db.records.create(
    label="TASK",
    data={
        "name": "Implement auth module",
        "priority": 9,
        "weight": 10.0,
        "deadline": "2024-12-20T17:00:00Z",
        "estimated_hours": 8,
        "status": "pending"
    }
)

# Link dependency relationship
db.records.attach(
    source=task,
    target=dependency,
    options={"type": "DEPENDS_ON", "direction": "out"}
)

# Find all tasks ordered by weight
db.records.find({
    "labels": ["TASK"],
    "where": {"status": "pending"},
    "orderBy": {"weight": "desc"}
})

# Transactional batch operations
with db.transactions.begin() as tx:
    for task_data in batch:
        db.records.create(label="TASK", data=task_data, transaction=tx)
```

## Related Documentation

- RushDB SDK Reference: https://docs.rushdb.com
- Graph Data Modeling: https://docs.rushdb.com/concepts/graph-model
- API Documentation: https://docs.rushdb.com/api

## Project Structure

```
implementing-weighted-priority-queues-with-graph-b-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py           # Mock task data generator
└── main.py           # Weighted priority queue implementation
```
