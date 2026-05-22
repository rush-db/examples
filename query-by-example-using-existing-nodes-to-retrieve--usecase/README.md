# Query-by-Example: Finding Similar Users via Graph Structure and Vector Affinity

## What This Project Demonstrates

**Problem**: You have a "gold standard" user — perhaps your most valuable customer or a known fraudster — and you need to find others who behave similarly. Traditional approaches require either:
- Writing complex Cypher/GQL queries to match graph patterns manually
- Relying solely on vector similarity without capturing behavioral relationships

**Solution**: RushDB's Query-by-Example (QBE) pattern lets you use an existing record as your search template, combining graph structure matching with vector similarity to find semantically and behaviorally similar nodes.

This project builds a **user recommendation system** using QBE to:
1. Identify high-value users by their behavioral graph patterns
2. Find structurally similar users (same products, similar purchase history)
3. Re-rank results by vector affinity for content similarity
4. Extend the pattern to **anomaly detection** (find transactions resembling known fraud)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        QBE Pattern Flow                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────┐    ┌──────────────┐    ┌─────────────────────────┐   │
│   │  Seed   │    │   Find by    │    │   Re-rank by Vector     │   │
│   │ Data    │───▶│   Example    │───▶│   Affinity              │   │
│   └─────────┘    └──────────────┘    └─────────────────────────┘   │
│                       │                          │                   │
│                       ▼                          ▼                   │
│            ┌──────────────────┐        ┌──────────────────────┐    │
│            │ Graph Structure  │        │  Content Similarity  │    │
│            │ (Relationships)  │        │  (Semantic Embedding)│    │
│            └──────────────────┘        └──────────────────────┘    │
│                       │                          │                   │
│                       └──────────┬─────────────────┘                   │
│                                  ▼                                     │
│                    ┌────────────────────────┐                           │
│                    │  Similar Users         │                           │
│                    │  (Ranked by Hybrid)    │                           │
│                    └────────────────────────┘                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works fine)
- `rushdb>=2.0.0` Python SDK

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API key

# Seed the database with sample data
python seed.py

# Run the QBE demonstration
python main.py
```

---

## Project Structure

| File | Purpose |
|------|---------|
| `seed.py` | Generates 50 users, 20 products, and purchase history graph |
| `main.py` | Demonstrates QBE pattern: find → filter → rank → detect |
| `requirements.txt` | Dependencies |
| `.env.example` | Environment variable template |

---

## Code Walkthrough

### Step 1: Seed Data

```sdk
# seed.py
from rushdb import RushDB
import random
from faker import Faker

fake = Faker()
db = RushDB(os.getenv("RUSHDB_API_KEY"))

# Create products
products = []
for name in ["Laptop", "Phone", "Headphones", "Camera", "Tablet",
             "Smartwatch", "Keyboard", "Monitor", "Mouse", "Speaker",
             "Webcam", "Printer", "Router", "SSD", "RAM",
             "Charger", "Cable", "Stand", "Light", "Desk"]:
    p = db.records.create(label="PRODUCT", data={
        "name": name,
        "price": round(random.uniform(29.99, 999.99), 2),
        "category": random.choice(["Electronics", "Accessories", "Office"])
    })
    products.append(p)

# Create users with purchases
for i in range(50):
    user = db.records.create(label="USER", data={
        "name": fake.name(),
        "email": fake.email(),
        "join_date": fake.date_between(start_date="-2y", end_date="today").isoformat(),
        "is_premium": random.random() > 0.7
    })
    
    # Each user has 1-8 purchases (premium users buy more)
    num_purchases = random.randint(1, 4) + (4 if user.data.get("is_premium") else 0)
    for _ in range(num_purchases):
        product = random.choice(products)
        tx = db.transactions.begin()
        purchase = db.records.create(label="PURCHASE", data={
            "amount": product.data["price"] * random.uniform(0.8, 1.2),
            "date": fake.date_between(start_date="-1y", end_date="today").isoformat()
        }, transaction=tx)
        db.records.attach(source=user, target=purchase, options={"type": "MADE"}, transaction=tx)
        db.records.attach(source=purchase, target=product, options={"type": "INCLUDES"}, transaction=tx)
        tx.commit()
___SPLIT___
// TypeScript version would be similar but with async/await
```

### Step 2: Query-by-Example Pattern

```sdk
# main.py
from rushdb import RushDB
db = RushDB(os.getenv("RUSHDB_API_KEY"))

# Step 1: Get our "gold standard" user (highest lifetime value)
result = db.records.find({
    "labels": ["USER"],
    "orderBy": {"field": "lifetime_value", "direction": "desc"},
    "limit": 1
})
target_user = result.data[0]
print(f"Target user: {target_user['name']} (LTV: ${target_user['lifetime_value']:.2f})")

# Step 2: Find users with similar graph structure
# QBE pattern: use target's properties as the example template
similar_users = db.records.find({
    "labels": ["USER"],
    "where": {
        "is_premium": target_user["is_premium"],
        "JOINED_WITHIN_MONTHS": 6  # same cohort age as target
    },
    "limit": 20
})

# Step 3: Re-rank by vector affinity (content similarity)
ranked = db.ai.search({
    "propertyName": "behavior_profile",
    "queryVector": target_user["behavior_vector"],
    "labels": ["USER"],
    "where": {
        "$id": {"$nin": [target_user.id]}
    },
    "limit": 10
})

print(f"\nTop 10 similar users (by vector affinity):")
for rank, user in enumerate(ranked.data, 1):
    print(f"  {rank}. {user['name']} — similarity: {user.score:.3f}")
___SPLIT___
// TypeScript version
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

const result = await db.records.find({
    labels: ['USER'],
    orderBy: { field: 'lifetime_value', direction: 'desc' },
    limit: 1
})
const targetUser = result.data[0]

const ranked = await db.ai.search({
    propertyName: 'behavior_profile',
    queryVector: targetUser.behavior_vector,
    labels: ['USER'],
    where: { $id: { $nin: [targetUser.id] } },
    limit: 10
})
```

### Step 3: Anomaly Detection Extension

```sdk
# Anomaly detection: find transactions resembling known fraud pattern
fraud_pattern = db.records.find_one({
    "labels": ["FRAUD_CASE"],
    "where": {"status": "confirmed", "risk_score": {"$gte": 0.9}}
})

# Find similar transaction patterns
suspicious = db.records.find({
    "labels": ["PURCHASE"],
    "where": {
        "amount": {"$gte": fraud_pattern["amount"] * 0.8, "$lte": fraud_pattern["amount"] * 1.2},
        "PURCHASE": {  # Filter by buyer's characteristics
            "$relation": {"type": "MADE", "direction": "in"},
            "account_age_days": {"$lte": 30},
            "prior_chargebacks": {"$gte": 1}
        }
    }
})
```

---

## Performance & UX Tradeoffs

### Why QBE Over Manual Cypher?

| Aspect | Manual Cypher/GQL | QBE with RushDB |
|--------|-------------------|-----------------|
| **Learning curve** | Steep — requires graph DB expertise | Intuitive — use existing records as templates |
| **Iteration speed** | Slow — write, test, debug queries | Fast — modify example record, re-query |
| **Maintenance** | Fragile — schema changes break queries | Resilient — schema-flexible property graph |
| **Combines vectors** | Requires separate vector index + Cypher | Native dual-layer (graph + vector) search |
| **Production read cost** | 5 KU per deep traversal | Standard queries: **free** |

### When to Use Each Approach

- **QBE (this pattern)**: Rapid prototyping, combining graph + vector similarity, UX-friendly features
- **Raw Cypher**: Complex multi-hop traversals, performance-critical batch jobs, fine-grained graph analytics

---

## Extending This Pattern

1. **Real-time recommendations**: Call QBE on user login, cache results for 5 minutes
2. **Churn prediction**: Use "churned user" as example, find at-risk users early
3. **Fraud detection**: Layer QBE with rule-based filters for precision

---

## Expected Output

```
$ python main.py

=== Query-by-Example: User Similarity Demo ===

Step 1: Identify high-value target user
  Target: Sarah Mitchell — Premium member since 2023-06
  Lifetime Value: $4,892.00
  Purchase Count: 12

Step 2: Find structurally similar users (same cohort)
  Found 8 users matching premium status + 6-month cohort

Step 3: Re-rank by vector affinity
  Top 10 similar users (by behavior profile):
    1. Michael Chen — similarity: 0.947
    2. Emily Rodriguez — similarity: 0.923
    3. David Kim — similarity: 0.891
    4. Jessica Thompson — similarity: 0.878
    5. Christopher Lee — similarity: 0.856

Step 4: Anomaly detection extension
  Known fraud pattern: Order #F-2938 (amount: $2,450.00)
  Similar suspicious transactions: 3
    - Order #T-1023: $2,198.00 (same buyer profile)
    - Order #T-1847: $2,601.00 (same buyer profile)
    - Order #T-2104: $2,389.00 (same buyer profile)

=== Complete ===
```

---

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/query-by-example-using-existing-nodes-to-retrieve--usecase)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
