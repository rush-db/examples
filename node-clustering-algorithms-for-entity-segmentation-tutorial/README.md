# Node Clustering Algorithms for Entity Segmentation in Large Graphs

A practical guide to implementing graph clustering algorithms for entity segmentation using RushDB's property graph model.

![RushDB](https://img.shields.io/badge/RushDB-2.0-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)

## Overview

This tutorial demonstrates how to use RushDB as a foundation for implementing node clustering algorithms that enable entity segmentation in large-scale graphs. We explore three complementary algorithms:

1. **Connected Components** — Identify isolated entity groups
2. **Label Propagation** — Community detection through iterative label spreading
3. **Louvain-style Partitioning** — Modularity-optimized community structure

## What You'll Learn

- Modeling entity graphs in RushDB with proper labels and relationships
- Implementing classic clustering algorithms on graph structures
- Querying and analyzing clusters using RushDB's traversal capabilities
- Entity segmentation strategies for downstream use cases

## Prerequisites

- Python 3.9+
- RushDB account with API key ([get one here](https://app.rushdb.com))
- Basic understanding of graph theory concepts

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### 3. Seed the Database

The seed script creates a synthetic organizational network with employees, teams, projects, and skills. Run it once to populate RushDB with test data:

```bash
python seed.py
```

Expected output:
```
Seeding entities...
✓ Created 150 EMPLOYEE records
✓ Created 40 TEAM records  
✓ Created 25 PROJECT records
✓ Created 30 SKILL records
✓ Created 200+ relationship links
Seeding complete.
```


## Running the Tutorial

```bash
python main.py
```

The script will:

1. **Build the Graph** — Load entities and relationships from RushDB
2. **Run Connected Components** — Find all isolated entity clusters
3. **Run Label Propagation** — Detect communities via label spreading
4. **Run Louvain Partitioning** — Optimize modularity for community structure
5. **Analyze Results** — Print cluster statistics and entity distributions

## Project Structure

```
node-clustering-algorithms-for-entity-segmentation-tutorial/
├── main.py                 # Main execution script
├── seed.py                 # Database seeding script
├── clustering/
│   ├── __init__.py
│   ├── connected_components.py  # Connected components algorithm
│   ├── label_propagation.py     # Label propagation algorithm
│   ├── louvain.py               # Louvain-style partitioning
│   └── utils.py                # Graph construction utilities
├── data/
│   └── entities.json      # Mock entity data
├── requirements.txt
├── .env.example
└── README.md
```

## Key Algorithms Explained

### Connected Components

Finds all groups of entities where each member is reachable from every other member. Useful for:
- Identifying isolated network segments
- Detecting data silos
- Finding orphaned records

### Label Propagation

Semi-supervised community detection where:
1. Each node starts with a unique label
2. Labels propagate iteratively based on neighbor majority
3. Convergence produces stable communities

Fast and scalable, ideal for large graphs.

### Louvain Partitioning

Greedy optimization algorithm that:
1. Maximizes modularity (quality of community structure)
2. Operates in two phases: local node movement → community aggregation
3. Produces hierarchical community structures

Gold standard for community detection in complex networks.

## RushDB Integration

This implementation uses RushDB's graph model:

```sdk
# Query all EMPLOYEE entities with their relationships
employees = db.records.find({
    "labels": ["EMPLOYEE"],
    "where": {"department": "Engineering"},
    "limit": 100
})

# Find employees on the same team
team_members = db.records.find({
    "labels": ["EMPLOYEE"],
    "where": {
        "TEAM": {"$relation": {"type": "MEMBER_OF", "direction": "out"}}
    }
})
___SPLIT___
// TypeScript implementation not shown for brevity
```

## Expected Output

```
=== Node Clustering for Entity Segmentation ===

[1] Connected Components Analysis
    Found 12 components
    Largest: 89 nodes (Engineering org)
    Isolated: 3 single-node components

[2] Label Propagation Communities
    Convergence after 5 iterations
    Detected 8 communities
    Largest: Engineering (42 members)

[3] Louvain Partitioning
    Modularity score: 0.647
    10 communities identified
    Hierarchical depth: 3 levels

[4] Entity Segmentation Summary
    Total entities: 245
    Segmented into 10 clusters
    Cluster size distribution: [...] 
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Clustering Algorithms](https://en.wikipedia.org/wiki/Category:Graph_clustering)
- [Louvain Method](https://en.wikipedia.org/wiki/Louvain_method)

## License

MIT
