# Graph Serialization Formats for Agent-to-Agent Communication

This project demonstrates how to use RushDB for serializing and deserializing graph data in agent-to-agent communication scenarios. It showcases different serialization formats and how they map to RushDB's property graph model.

## What This Tutorial Covers

- **JSON serialization**: Native JSON representation of graph structures
- **Adjacency list format**: Compact representation for efficient transmission
- **Edge list format**: Simple pairwise relationship encoding
- **Nested JSON (import_json)**: Hierarchical data import with automatic relationship creation
- **Graph traversal serialization**: Converting query results for agent consumption

## Prerequisites

- Python 3.9+
- A RushDB instance (cloud or self-hosted)
- API key from [RushDB Dashboard](https://dash.rushdb.com)

## Setup

```bash
# Clone the repository
cd graph-serialization-formats-for-agent-to-agent-com-tutorial

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API key
```

## Quick Start

```bash
# Seed mock data for agent communication scenarios
python seed.py

# Run the main demonstration
python main.py
```

## Project Structure

| File | Purpose |
|------|---------|
| `seed.py` | Generates mock agent communication data (messages, intents, context) |
| `main.py` | Demonstrates all serialization formats with RushDB |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

## Serialization Formats Explained

### 1. JSON Serialization (Native)

The default format for RushDB records. Each record is a JSON object with system fields (`__id`, `__label`) and user properties.

### 2. Adjacency List Format

Compact representation showing which records connect to which. Ideal for bandwidth-constrained agent communication.

### 3. Edge List Format

Pairwise representation of relationships: `[source_id, target_id, relationship_type]`. Useful for graph diffs and sync operations.

### 4. Nested JSON Import

Hierarchical JSON structures that RushDB automatically converts into linked records and relationships via `import_json`.

## Expected Output

Running `main.py` produces:
- Demonstration of each serialization format
- Sample output showing the serialized graph data
- Verification that agents can reconstruct the graph from serialized data

## Documentation

- [RushDB SDK Reference](https://docs.rushdb.com/sdk/python/)
- [Graph Data Model](https://docs.rushdb.com/concepts/data-model/)
- [Agent Memory Patterns](https://docs.rushdb.com/use-cases/agent-memory/)
