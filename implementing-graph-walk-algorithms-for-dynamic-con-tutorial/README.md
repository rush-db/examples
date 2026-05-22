# Implementing Graph Walk Algorithms for Dynamic Context Assembly

## Overview

This project demonstrates how to implement graph-walk algorithms using RushDB's property graph capabilities to dynamically assemble context for AI applications. It showcases traversal strategies ranging from simple BFS/DFS to weighted walks that prioritize high-relevance paths.

## What This Tutorial Demonstrates

- **Graph Construction**: Building a knowledge graph with documents, concepts, and relationships
- **BFS Traversal**: Finding shortest paths to related entities
- **DFS Traversal**: Deep exploration for comprehensive topic coverage
- **Weighted Walks**: Personalized PageRank-style prioritization of high-similarity nodes
- **Context Assembly**: Aggregating walk results into structured prompts for AI systems

## Prerequisites

- Python 3.9+
- A RushDB account (free tier available at [rushdb.com](https://rushdb.com))
- `rushdb>=2.0.0` Python SDK

## Setup

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone https://github.com/rush-db/examples.git
   cd implementing-graph-walk-algorithms-for-dynamic-con-tutorial
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your RushDB credentials:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API key from https://app.rushdb.com/settings/api-keys
   ```

5. **Seed the database with sample knowledge graph:**
   ```bash
   python seed.py
   ```

## How to Run

After seeding the database, execute the main demonstration:

```bash
python main.py
```

This will run all graph walk algorithms and display:
- BFS traversal from a seed document
- DFS deep exploration of related concepts
- Weighted walk prioritizing high-connectivity nodes
- Context assembly and formatted output for AI consumption

## Expected Output

The script outputs detailed logs of each algorithm's traversal, showing:
- Nodes visited and paths taken
- Context snippets collected from traversed nodes
- Final assembled context ready for AI prompting

## Project Structure

```
implementing-graph-walk-algorithms-for-dynamic-con-tutorial/
├── README.md         # This file
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
├── seed.py           # Knowledge graph seeding script
└── main.py           # Graph walk algorithm implementations
```

## Key Design Decisions

### Why Graph Walks for Context Assembly?

Traditional RAG systems retrieve isolated chunks. Graph walks enable:
- **Multi-hop reasoning**: Connect concepts across documents
- **Relevance propagation**: Weight walk paths by connectivity
- **Diverse context**: Aggregate from multiple source types

### RushDB Advantages

- Zero-schema design lets you model any knowledge structure
- Native relationship queries eliminate JOIN complexity
- Transactional operations ensure graph consistency

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph-Based Retrieval Strategies](https://docs.rushdb.com/guides/retrieval)
- [RushDB Python SDK Reference](https://docs.rushdb.com/sdk/python)
