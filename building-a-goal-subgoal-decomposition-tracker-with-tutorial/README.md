# Building a Goal-Subgoal Decomposition Tracker with RushDB

This tutorial demonstrates how RushDB's unified graph+vector model handles hierarchical task relationships and semantic retrieval in a single database—no stitching together separate graph and vector databases.

## What You'll Build

A goal decomposition tracker that:
- Organizes goals in a hierarchical tree structure (parent → subgoals → sub-subgoals)
- Enables semantic search across goal descriptions to find related goals across different branches
- Demonstrates how RushDB's single-database approach simplifies what would otherwise require Neo4j + Pinecone + sync logic

## Key Concepts Demonstrated

| Concept | RushDB Feature | Traditional Approach |
|---------|----------------|---------------------|
| Hierarchical relationships | Graph edges via `attach()` | Separate graph DB |
| Semantic goal matching | Vector embeddings + `ai.search()` | Separate vector DB |
| Mixed queries | Graph traversal + vector search in one call | Complex multi-DB queries |
| Transactional consistency | Atomic writes with relationships | Manual sync across systems |

## Prerequisites

- Python 3.9+
- A RushDB account ([free tier](https://rushdb.com/pricing) is sufficient)
- `sentence-transformers` for generating embeddings locally

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

Get your API token from the [RushDB dashboard](https://app.rushdb.com).

### 3. Run the Tutorial

```bash
python main.py
```

The script will:
1. Initialize the goal schema and create a vector index
2. Seed sample goals with hierarchical decomposition
3. Demonstrate graph traversal queries
4. Show semantic search across goal branches
5. Run comparison queries showing RushDB's unified approach

## Project Structure

```
.
├── README.md
├── requirements.txt
├── .env.example
├── main.py          # Complete tutorial implementation
└── goals.json       # Sample goal hierarchy data
```

## Expected Output

The tutorial outputs detailed explanations of each operation, showing:
- How relationships form a traversable goal tree
- How semantic search finds related goals regardless of tree position
- Console output comparing RushDB's single-DB approach vs. multi-system architecture

## How It Works

### Schema Definition

Goals use two key features:
- **Graph relationships**: `HAS_SUBGOAL` edges connect parent goals to subgoals
- **Vector embeddings**: Goal descriptions are embedded for semantic similarity search

### Goal Hierarchy

```
Learn System Design
├── Study Fundamentals
│   ├── Networking basics
│   └── Distributed systems theory
└── Practice Architecture Patterns
    ├── Design REST APIs
    └── Explore event-driven patterns
```

### Query Patterns

1. **Graph traversal**: Find all subgoals of a goal (recursive or single-level)
2. **Semantic search**: Find goals with similar descriptions across different branches
3. **Combined**: Find semantically similar subgoals of a specific parent

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Model](https://docs.rushdb.com/concepts/property-graph)
- [Vector Search](https://docs.rushdb.com/concepts/vector-search)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-a-goal-subgoal-decomposition-tracker-with-tutorial)
