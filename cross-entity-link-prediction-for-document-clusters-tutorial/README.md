# Cross-Entity Link Prediction for Document Clusters: A Practical Implementation

This project demonstrates how to use RushDB for cross-entity link prediction within document clusters. It shows patterns for discovering潜在 relationships between documents, authors, topics, and tags using graph traversal and semantic similarity.

## What This Tutorial Demonstrates

- **Graph-based relationship modeling** in RushDB
- **Cross-entity link prediction** using shared properties, tags, and semantic similarity
- **Graph traversal patterns** to discover indirect relationship opportunities
- **Vector similarity search** for content-based link discovery
- **Transaction-based bulk operations** for creating predicted links

## Prerequisites

- Python 3.10+
- A RushDB account (Free tier works)
- `RUSHDB_API_TOKEN` from your RushDB project

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

### 3. Seed the Database

The seed script creates sample documents, authors, topics, and tags to simulate a realistic document management system:

```bash
python seed.py
```

This creates:
- 12 documents across 4 topics
- 6 authors
- 8 tags (shared across documents)
- Existing relationships (AUTHORED, BELONGS_TO, TAGGED_WITH)

### 4. Run the Tutorial

```bash
python main.py
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Mock data generator
└── main.py             # Main tutorial code
```

## Expected Output

The tutorial outputs:
1. Current graph statistics
2. Predicted links based on shared tags
3. Predicted links based on semantic similarity
4. Predicted links based on graph patterns (common neighbors)
5. Summary of all predicted links with confidence scores

## Link Prediction Strategies Demonstrated

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Shared Tag Analysis | Documents with overlapping tags suggest related topics | Content discovery |
| Semantic Similarity | Vector-based similarity finds conceptually related content | Recommendation engine |
| Common Neighbor | If A→B and C→B, predict A→C | Social networks, citation graphs |
| Co-authorship | Authors who work on similar topics may collaborate | Expert matching |

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/cross-entity-link-prediction-for-document-clusters-tutorial)
