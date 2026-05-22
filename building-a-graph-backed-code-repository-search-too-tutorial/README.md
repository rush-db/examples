# Building a Graph-Backed Code Repository Search Tool

A practical tutorial demonstrating how to build a powerful code search engine using RushDB's property graph model. This project models a code repository as a graph, enabling rich queries like "find all functions in files that depend on this module" or "search for code handling authentication."

## What This Demonstrates

- **Graph modeling of code repositories** — Represent repositories, files, functions, and classes as interconnected nodes
- **Relationship-based traversal** — Navigate dependency chains, file hierarchies, and import graphs
- **Hybrid search** — Combine structured queries with semantic similarity search on code
- **Transaction-based writes** — Safely import complex nested data structures

## Prerequisites

- Python 3.10+
- A RushDB account (free tier works)
- `sentence-transformers` for embeddings (or configure OpenAI)

## Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Seed mock data (optional but recommended):**
   ```bash
   python seed.py
   ```
   This creates a realistic codebase graph with 3 repositories, ~50 files, and ~200 functions/classes.

4. **Run the search tool:**
   ```bash
   python main.py
   ```

## Project Structure

```
.
├── main.py          # Main search application
├── seed.py          # Mock data generator
├── requirements.txt # Python dependencies
├── .env.example     # Environment template
└── README.md        # This file
```

## The Graph Model

```
REPOSITORY
    │
    ├── IMPORTS ──→ REPOSITORY (cross-repo dependencies)
    │
    └── CONTAINS ──→ FILE
                        │
                        ├── IMPORTS ──→ FILE
                        │
                        ├── DEFINES ──→ FUNCTION
                        │                   │
                        │                   └── CALLS ──→ FUNCTION
                        │
                        └── DEFINES ──→ CLASS
                                              │
                                              └── METHOD ──→ FUNCTION
```

## Search Capabilities

| Query Type | Example |
|------------|---------|
| Find by label | `find_files("auth")` |
| Relationship traversal | `find_functions_in_file(file_id)` |
| Graph traversal | `find_dependents(entity_id)` |
| Semantic search | `semantic_search("authentication middleware")` |
| Complex graph query | `find_call_chain(start_func, end_func)` |

## Expected Output

Running `python main.py` demonstrates:
1. Creating the graph schema
2. Querying repositories
3. Finding files by path pattern
4. Traversing function relationships
5. Semantic code search
6. Dependency graph exploration

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Concepts in RushDB](https://docs.rushdb.com/concepts/property-graph)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-a-graph-backed-code-repository-search-too-tutorial)
