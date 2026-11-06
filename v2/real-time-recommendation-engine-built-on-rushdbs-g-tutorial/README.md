# Real-time Recommendation Engine Built on RushDB's Graph-Vector Store

This example demonstrates how to build a **real-time recommendation engine** using RushDB's dual-layer storage: property graph traversal (Neo4j) for collaborative filtering combined with vector similarity search for content-based recommendations.

## What This Example Demonstrates

1. **Hybrid Recommendation Architecture** — combining graph-based collaborative filtering with vector similarity search
2. **Content-Based Filtering** — using semantic embeddings on product descriptions
3. **Collaborative Filtering** — graph traversal to find products liked by similar users
4. **Real-Time Recommendations** — fast lookups leveraging RushDB's indexed queries

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Recommendation Engine                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │   Graph Layer        │    │     Vector Layer              │  │
│  │   (Neo4j)            │    │     (Vector Index)            │  │
│  │                      │    │                               │  │
│  │  USER ──INTERACTS──►│    │  Product.embeddings          │  │
│  │         PRODUCT      │    │  (semantic similarity)        │  │
│  │                      │    │                               │  │
│  │  Collaborative       │    │  Content-Based                │  │
│  │  Filtering           │    │  Filtering                    │  │
│  └──────────────────────┘    └──────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Hybrid Recommendation Score                   │  │
│  │   score = α × collaborative_score + (1-α) × content_score │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- `sentence-transformers` for generating embeddings

## Setup

1. **Clone and install dependencies:**
   ```bash
   cd real-time-recommendation-engine-built-on-rushdbs-g-tutorial
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your RushDB API key
   ```

3. **Generate mock data:**
   ```bash
   python seed.py
   ```
   This creates:
   - 50 products with semantic descriptions
   - 30 users with preferences
   - 300+ interactions (views, purchases, ratings)

4. **Run the recommendation engine:**
   ```bash
   python main.py
   ```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Generates mock data and sets up RushDB
├── main.py            # Core recommendation engine
└── data/
    └── products.json  # Sample product catalog (auto-generated)
```

## How It Works

### 1. Data Model

| Label       | Properties                                      | Purpose                        |
|-------------|-------------------------------------------------|--------------------------------|
| `USER`      | id, name, email, preferences                     | User profiles                  |
| `PRODUCT`   | id, name, description, category, price          | Product catalog                |
| `INTERACTION` | type, rating, timestamp                       | User-product interactions      |

**Relationships:**
- `USER` ──`INTERACTED_WITH`──► `PRODUCT` (typed: view, purchase, rated)
- `PRODUCT` ──`SIMILAR_TO`──► `PRODUCT` (computed similarity edges)

### 2. Content-Based Filtering

```sdk
# Find products similar to "Wireless Headphones" using vector search
similar = db.ai.search({
    "propertyName": "description",
    "query": "Wireless Headphones",
    "labels": ["PRODUCT"],
    "limit": 5
})

for product in similar:
    print(f"[{product.score:.3f}] {product['name']}")
___SPLIT___
// Find products similar to "Wireless Headphones" using vector search
const similar = await db.ai.search({
    propertyName: 'description',
    query: 'Wireless Headphones',
    labels: ['PRODUCT'],
    limit: 5
});

for (const product of similar.data) {
    console.log(`[${product.score?.toFixed(3)}] ${product.name}`);
}
```

### 3. Collaborative Filtering

```sdk
# Find products purchased by users who also bought product_id
# Using graph traversal through INTERACTED_WITH relationships

def get_collaborative_recommendations(product_id, limit=5):
    # Find users who interacted with this product
    users = db.records.find({
        "labels": ["USER"],
        "where": {
            "PRODUCT": {
                "$relation": {"type": "INTERACTED_WITH", "direction": "in"},
                "id": product_id
            }
        }
    })
    
    # Find products those users also interacted with
    # (excluding the original product)
    recommendations = db.records.find({
        "labels": ["PRODUCT"],
        "where": {
            "INTERACTION": {
                "$relation": {"type": "INTERACTED_WITH", "direction": "in"},
                "USER": {
                    "$id": {"$in": [u.id for u in users]}
                }
            },
            "id": {"$ne": product_id}
        },
        "limit": limit
    })
    
    return recommendations
___SPLIT___
// Find products purchased by users who also bought product_id
async function getCollaborativeRecommendations(productId: string, limit = 5) {
    // Find users who interacted with this product
    const users = await db.records.find({
        labels: ['USER'],
        where: {
            PRODUCT: {
                $relation: { type: 'INTERACTED_WITH', direction: 'in' },
                id: productId
            }
        }
    });
    
    // Find products those users also interacted with
    const recommendations = await db.records.find({
        labels: ['PRODUCT'],
        where: {
            INTERACTION: {
                $relation: { type: 'INTERACTED_WITH', direction: 'in' },
                USER: {
                    $id: { $in: users.data.map(u => u.id) }
                }
            },
            id: { $ne: productId }
        },
        limit
    });
    
    return recommendations;
}
```

### 4. Hybrid Scoring

```sdk
def get_hybrid_recommendations(user_id, product_id, alpha=0.6):
    """
    Combine collaborative and content-based signals.
    
    Args:
        user_id: Target user
        product_id: Reference product
        alpha: Weight for collaborative (1-alpha for content)
    """
    # Get content-based scores
    content_scores = db.ai.search({
        "propertyName": "description",
        "query": get_product_description(product_id),
        "labels": ["PRODUCT"],
        "limit": 20
    })
    
    # Get collaborative scores
    collab_scores = get_user_collab_scores(user_id)
    
    # Normalize and combine
    hybrid_scores = []
    for product in content_scores:
        collab_score = collab_scores.get(product.id, 0)
        content_score = product.score or 0
        combined = alpha * collab_score + (1 - alpha) * content_score
        hybrid_scores.append((product, combined))
    
    # Sort and return top recommendations
    hybrid_scores.sort(key=lambda x: x[1], reverse=True)
    return hybrid_scores[:10]
```

## Expected Output

```
=== Real-time Recommendation Engine ===

[1] Content-Based: Products similar to "Ergonomic Office Chair"
  [0.923] Premium Mesh Office Chair - $349.99
  [0.891] Standing Desk Converter - $199.99
  [0.867] Lumbar Support Cushion - $49.99
  [0.854] Adjustable Armrest Set - $79.99
  [0.821] Ergonomic Footrest - $39.99

[2] Collaborative: Users who liked "Ergonomic Office Chair" also bought
  ✓ Premium Mesh Office Chair (purchased by 8 similar users)
  ✓ Standing Desk Converter (purchased by 6 similar users)
  ✓ Monitor Arm Mount (purchased by 5 similar users)

[3] Hybrid: Personalized recommendations for user_john_doe
  [0.89] Premium Mesh Office Chair - $349.99 (Collab: 0.95, Content: 0.82)
  [0.82] Mechanical Keyboard - $149.99 (Collab: 0.78, Content: 0.86)
  [0.79] Ultrawide Monitor 34" - $599.99 (Collab: 0.85, Content: 0.72)
  ...

[4] Real-time: "Smart Watch" search results
  [0.912] Fitness Smart Watch Pro - $199.99
  [0.887] Health Tracker Band - $79.99
  [0.834] Sports Smart Watch - $149.99
  [0.798] Classic Smart Watch - $129.99
```

## Key Insights for Senior Engineers

1. **Zero Schema Flexibility** — Add new interaction types without migrations
2. **Relationship Traversal** — Graph queries find patterns SQL can't express easily
3. **Vector Hybrid** — RushDB combines semantic search with graph traversal natively
4. **ACID Transactions** — Consistent state for interaction graphs
5. **Free Reads** — RushDB doesn't charge for queries, only writes

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Recommendations Explained](https://docs.rushdb.com/docs/graphs)
- [Vector Search Guide](https://docs.rushdb.com/docs/vectors)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/real-time-recommendation-engine-built-on-rushdbs-g-tutorial)
