# Building a Goal-Subgoal Decomposition Tracker with RushDB

This example demonstrates how to build a goal-subgoal decomposition tracker using RushDB's combined graph and vector capabilities.

## What It Demonstrates

- **Graph relationships**: Model goal hierarchy with parent-child, prerequisite, and blocking relationships
- **Semantic search**: Find related goals using vector embeddings even when terminology differs
- **Hybrid queries**: Traverse subgoal trees while filtering by semantic similarity
- **Single-store architecture**: Graph topology and vector embeddings coexist in the same record type

## Why RushDB for This Use Case?

Goal decomposition naturally forms a graph structure — goals have parents, children, prerequisites, and blockers. Simultaneously, finding related goals across a large corpus requires semantic search. RushDB stores both in one system, eliminating the need to join a graph database with a vector database.

## Prerequisites

- Python 3.9+
- A RushDB account (free tier works)
- `sentence-transformers` for local embeddings (no OpenAI required)

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your RushDB API key

# Seed the database with sample goals
python seed.py

# Run the main demo
python main.py
```

## Project Structure

```
.
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py            # Generates sample goal hierarchy data
└── main.py            # Demonstrates RushDB goal tracking features
```

## Expected Output

The demo will:
1. Display the goal hierarchy
2. Find semantically related goals to "user authentication"
3. Trace prerequisite chains for goals
4. Identify goals blocked by dependencies

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RUSHDB_API_KEY` | Your RushDB API key from the dashboard |
| `RUSHDB_URL` | Optional: self-hosted endpoint (defaults to cloud) |

Get your API key at https://app.rushdb.com

## Related Resources

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-a-goal-subgoal-decomposition-tracker-with-usecase)
