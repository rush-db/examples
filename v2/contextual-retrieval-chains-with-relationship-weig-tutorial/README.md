# Contextual Retrieval Chains with Relationship-Weighted Relevance

This project demonstrates how to build intelligent retrieval systems using RushDB's property graph capabilities combined with vector similarity search. You'll learn how to leverage relationship types and graph traversal depth to weight and chain retrieval results.

## What It Demonstrates

- **Contextual Retrieval**: Using RushDB's graph structure to provide context-aware search results
- **Relationship-Weighted Relevance**: Boosting search scores based on relationship types (e.g., citing relationships weighted higher than generic references)
- **Chain Queries**: Multi-hop traversals that build context from interconnected records
- **Property Graph + Vector Search**: Combining semantic similarity with graph traversal for nuanced retrieval

## Concepts

### Relationship-Weighted Scoring

When retrieving documents, not all connections are equal. A document that cites another is more contextually relevant than one that merely references it. We weight relationship types:

| Relationship | Weight | Meaning |
|--------------|--------|---------|
| `CITES` | 1.0 | Direct citation (highest relevance) |
| `AUTHORED_BY` | 0.8 | Same author context |
| `RELATED_TO` | 0.5 | Thematic similarity |
| `REFERENCES` | 0.3 | Mentioned in passing |

### Chain Depth Penalty

Results from direct neighbors score higher than those requiring multi-hop traversal:
- **Depth 1**: Weight × 1.0
- **Depth 2**: Weight × 0.6
- **Depth 3+**: Weight × 0.3

### Combined Score

```
final_score = (semantic_score × 0.7) + (relationship_score × 0.3)
```

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- `rushdb>=2.0.0`

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

3. **Seed the database:**
```bash
python seed.py
```

4. **Run the demonstration:**
```bash
python main.py
```

## Project Structure

```
contextual-retrieval-chains-with-relationship-weig-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Generates test data with relationships
└── main.py             # Demonstrates retrieval chains
```

## Expected Output

The demonstration shows:
1. Initial semantic search (baseline)
2. Relationship-weighted results
3. Chain traversal with context accumulation
4. Comparison of scoring approaches

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RUSHDB_API_KEY` | Your RushDB API key from the dashboard |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Concepts](https://docs.rushdb.com/concepts)
- [Vector Search Guide](https://docs.rushdb.com/guides/vector-search)

## License

MIT
