# Graph-based Feature Stores for ML Model Training Pipelines

## Overview

This tutorial demonstrates how to use RushDB as a graph-based feature store for ML model training pipelines. You'll learn how to:

- **Model features as graph entities** with typed relationships
- **Build feature engineering pipelines** using graph traversal
- **Construct training datasets** by traversing connected features
- **Compute aggregated features** (counts, sums, recency) via graph queries
- **Version and track features** using record properties

## Why Graph-based Feature Stores?

Traditional flat feature stores treat features as independent columns in a table. A graph-based approach unlocks:

- **Feature reuse** via relationship traversal (e.g., user's friends' preferences)
- **Multi-hop aggregations** (e.g., products purchased by similar users)
- **Natural feature composition** (features inherit relationships from source entities)
- **Lineage tracking** (graph structure preserves data provenance)

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- API key from your RushDB workspace

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY

# Generate mock training data
python seed.py

# Run the tutorial
python main.py
```

## What the Code Demonstrates

### 1. Feature Schema Modeling

Features are stored as records with labels. Relationships between features encode domain knowledge:

```
USER ──[PURCHASED]──> PRODUCT
  │                      │
  └──[VIEWED]────────────┘
  │
  └──[BELONGS_TO]──> SEGMENT
```

### 2. Feature Engineering via Graph Traversal

We compute features by traversing the graph:

- **Count features**: Number of purchases, views, interactions
- **Aggregate features**: Total spend, average order value
- **Recency features**: Days since last purchase
- **Graph-based features**: Cross-user aggregations (collaborative signals)

### 3. Training Dataset Construction

Build training batches by:
1. Selecting anchor entities (e.g., users for churn prediction)
2. Traversing to related features (purchases, views, demographics)
3. Aggregating into flat feature vectors
4. Joining with labels

### 4. Real-time Feature Serving Pattern

The same graph structure used for batch training can power online inference:

```python
# Batch: traverse all historical data
user_features = db.records.find({
    "labels": ["USER"],
    "where": {
        "PURCHASE": {
            "date": {"$gte": "2024-01-01"}
        }
    }
})

# Online: fetch single user's features
user = db.records.findById(user_id)
recent_purchases = db.records.find({
    "labels": ["PURCHASE"],
    "where": {
        "USER": {"$id": {"$in": [user_id]}},
        "date": {"$gte": last_30_days}
    }
})
```

## Expected Output

```
=== Graph-based Feature Store Demo ===

[1] Created 150 users across 3 segments
[2] Created 50 products across 5 categories
[3] Created 600 transactions linking users to products
[4] Created 2000 view events for behavioral features

=== Feature Engineering Examples ===

User 'alice@example.com' features:
  - purchase_count: 12
  - total_spend: 1,234.56
  - avg_order_value: 102.88
  - days_since_last_purchase: 3
  - view_count: 45
  - category_affinity_electronics: 0.42
  - category_affinity_clothing: 0.35

Segment 'premium' aggregate features:
  - avg_purchase_count: 15.2
  - avg_total_spend: 2,891.00
  - avg_session_duration: 847 seconds

=== Training Dataset Construction ===

Batch 0 (100 samples):
  features shape: (100, 12)
  label distribution: {0: 68, 1: 32}

=== Graph Traversal for Collaborative Features ===

Users similar to 'alice@example.com' (purchased same products):
  - bob@example.com: 8 shared products
  - carol@example.com: 6 shared products
  - david@example.com: 5 shared products

Recommendations based on collaborative signals:
  - 'Product 42' (purchased by 15 similar users)
  - 'Product 17' (purchased by 12 similar users)

=== Feature Store Schema ===

Labels:
  - USER (150 records)
  - PRODUCT (50 records)
  - PURCHASE (600 records)
  - VIEW (2000 records)
  - SEGMENT (3 records)

Relationships:
  - USER → PURCHASED → PRODUCT (600 edges)
  - USER → VIEWED → PRODUCT (2000 edges)
  - USER → BELONGS_TO → SEGMENT (150 edges)
  - PRODUCT → BELONGS_TO → CATEGORY (50 edges)
```

## Code Structure

```
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py            # Mock data generation
└── main.py            # Tutorial demonstration
```

## Related Resources

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB SDK Reference](https://docs.rushdb.com/sdk/python/)
- [Feature Store Patterns](https://en.wikipedia.org/wiki/Feature_engineering)

## License

MIT
