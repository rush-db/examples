# Query Planning Strategies in Graph-Vector Hybrids: Path vs Beam Search

A practical tutorial demonstrating how RushDB enables advanced query planning strategies that combine graph traversal with vector similarity search.

## What This Tutorial Demonstrates

- **Path Search**: Sequential graph traversal following relationship chains (depth-first, exploring full paths)
- **Beam Search**: Parallel exploration maintaining top-K candidates at each level (breadth-weighted)
- **Hybrid Strategies**: Combining both approaches for optimal query planning

## The Problem

When building AI applications over knowledge graphs, you often need to:
1. Start with semantic similarity (vector search)
2. Navigate relationships (graph traversal)
3. Score and rank by multiple factors

Traditional approaches force you to choose: do you start with vectors and then filter, or traverse the graph and then re-rank? RushDB's hybrid model lets you implement both strategies and compare them.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Query Planning Layer                          │
├────────────────────────────┬────────────────────────────────────┤
│     Path Search            │        Beam Search                 │
│  ┌─────────────────┐       │    ┌─────────────────────────┐     │
│  │ Start Node      │       │    │ B=3 candidates/level    │     │
│  │       ↓         │       │    │                         │     │
│  │ Traverse Path 1 │       │    │ Level 0: [A, B, C]      │     │
│  │       ↓         │       │    │ Level 1: [A→D, A→E,     │     │
│  │ End Node        │       │    │       B→D, B→E, C→D]    │     │
│  │ (full path)     │       │    │ Keep top 3: [A→D,       │     │
│  └─────────────────┘       │    │    A→E, B→D]            │     │
│                           │    └─────────────────────────┘     │
└───────────────────────────┴────────────────────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │   RushDB Graph +    │
                    │   Vector Index      │
                    └─────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (free tier works)
- `rushdb>=2.0.0` Python package

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Seed the database**:
   ```bash
   python seed.py
   ```
   This creates a knowledge graph with:
   - 20 concepts (topics with vector embeddings)
   - 30 documents linked to concepts
   - Hierarchical relationships between concepts

## Running the Tutorial

```bash
python main.py
```

The script demonstrates:

### 1. Path Search Implementation
Explores the graph by following relationship chains:
- Start from semantic similarity results
- Traverse parent/child relationships
- Collect all documents along each path
- Score paths by aggregate relevance

### 2. Beam Search Implementation
Explores multiple branches in parallel:
- Start from semantic candidates (beam width B)
- Expand top B candidates at each level
- Prune to top B using combined score
- Terminate when depth limit reached

### 3. Hybrid Strategy
Combines both approaches:
- Vector search provides initial candidates
- Path traversal explores connections
- Beam pruning optimizes exploration

## Expected Output

```
=== PATH SEARCH DEMO ===
Starting with semantic query: 'machine learning optimization'
Found 5 initial concept matches
Traversed 12 relationship paths
Best path score: 0.847 (neural networks → deep learning → backprop)
Documents found: 7

=== BEAM SEARCH DEMO ===
Beam width: 4, Max depth: 3
Level 0: 4 candidates (from vector search)
Level 1: 16 candidates → pruned to 4 best
Level 2: 12 candidates → pruned to 4 best
Final results: 4 documents

=== HYBRID SEARCH DEMO ===
Combined score: vector_similarity * path_authority * edge_strength
Top 3 results with explanation:
  1. [0.923] Document: 'Backpropagation Explained' (path: ML→DL→NN)
  2. [0.891] Document: 'Gradient Descent Variants' (path: ML→Opt)
  3. [0.876] Document: 'Neural Network Architectures' (path: ML→DL)
```

## Project Structure

```
query-planning-strategies-in-graph-vector-hybrids--tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Database seeding script
└── main.py             # Main tutorial demonstration
```

## Key Concepts Explained

### Path Search
**Pros**: Complete path exploration, good for finding all connected documents
**Cons**: Exponential blowup, no pruning, slow for deep graphs
**Use when**: You need exhaustive results or paths are short

### Beam Search
**Pros**: Constant memory, focused exploration, faster
**Cons**: May miss better paths, depends on beam width tuning
**Use when**: Speed matters, deep traversals, approximate results acceptable

### Hybrid Approach
**Pros**: Leverages strengths of both, tunable balance
**Cons**: More complex implementation
**Use when**: Production systems needing both quality and speed

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/query-planning-strategies-in-graph-vector-hybrids--tutorial)
