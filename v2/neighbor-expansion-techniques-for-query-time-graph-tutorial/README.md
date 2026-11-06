# Neighbor Expansion Techniques for Query-Time Graph Augmentation

A practical tutorial demonstrating multi-hop neighbor expansion in RushDB — filtering by relationship type, applying vector similarity ranking, and enforcing depth limits to prevent runaway queries on high-degree nodes.

**GitHub**: https://github.com/rush-db/examples/tree/main/neighbor-expansion-techniques-for-query-time-graph-tutorial

**RushDB Docs**: https://docs.rushdb.com

---

## What This Tutorial Demonstrates

- ✅ Basic 2-hop expansion: Product → Category → Related Products
- ✅ Relationship type filtering at each hop using `$relation`
- ✅ Vector similarity as a post-expansion ranking signal
- ✅ Depth limits to control query scope on high-degree nodes
- ✅ Complete working example: finding related products through category taxonomy, then re-ranking by embedding similarity

**Thesis**: All of the above can be implemented in under 50 lines of practical application code.

---


## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works): https://rushdb.com
- `RUSHDB_API_KEY` environment variable

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your API key:

```env
RUSHDB_API_KEY=your_api_key_here
```

### 3. Run the Tutorial

```bash
python main.py
```

The script will:
1. Check if data is already seeded (idempotent — safe to run twice)
2. Create the vector index if it doesn't exist
3. Seed the product taxonomy and relationships
4. Run through all expansion patterns and print results

---

## Project Structure

```
neighbor-expansion-techniques-for-query-time-graph-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── data/
│   └── products.json    # Sample product taxonomy data
├── seed.py             # Database seeding script
└── main.py             # Main tutorial script
```

---

## Key Code Patterns

### 2-Hop Expansion

```sdk
# Find all products in the same category as a target product
related_products = db.records.find({
    "labels": ["PRODUCT"],
    "where": {
        "CATEGORY": {"slug": target_product["categorySlug"]}
    },
    "limit": 20
})
```

### Filtering with Relationship Type

```sdk
# Filter by specific relationship type (BELONGS_TO) and direction
db.records.find({
    "labels": ["PRODUCT"],
    "where": {
        "CATEGORY": {
            "$relation": {"type": "BELONGS_TO", "direction": "out"},
            "slug": category_slug
        }
    }
})
```


### Depth-Limited Expansion

```sdk
# Limit results to prevent runaway queries on high-degree nodes
def expand_with_depth_limit(db, product_slug, max_depth=2, max_results=10):
    if max_depth == 1:
        # Single-hop: direct category siblings only
        return db.records.find({
            "labels": ["PRODUCT"],
            "where": {"CATEGORY": {"name": category_name}},
            "limit": max_results
        })
    # Multi-hop: category taxonomy expansion with limit
    return db.records.find({
        "labels": ["PRODUCT"],
        "where": {"CATEGORY": {"slug": category_slug}},
        "limit": max_results
    })
```

### Vector Similarity Ranking (Post-Expansion)

```sdk
# 1. Get expansion candidates
candidates = db.records.find({
    "labels": ["PRODUCT"],
    "where": {"CATEGORY": {"slug": category_slug}},
    "limit": 50
})

# 2. Re-rank by vector similarity
ranked = db.ai.search({
    "propertyName": "description",
    "query": "ergonomic typing experience",
    "labels": ["PRODUCT"],
    "where": {"__id": {"$in": [p.id for p in candidates]}},
    "limit": 5
})
```

---

## Understanding the Data Model

```
CATEGORY (Electronics)
  └── CATEGORY (Computers & Tablets)
       ├── PRODUCT (Wireless Keyboard)
       ├── PRODUCT (Gaming Keyboard)
       ├── PRODUCT (Business Laptop)
       └── PRODUCT (Developer Laptop)
  └── CATEGORY (Mobile Phones)
       ├── PRODUCT (Flagship Phone)
       ├── PRODUCT (Budget Phone)
       └── PRODUCT (Gaming Phone)
```

**Expansion patterns tested**:
- Product → Category → Same-category products (2-hop)
- Product → Category → Parent Category → Other-subcategory products (3-hop)
- Filtering by relationship type and depth limits
- Post-expansion re-ranking by vector similarity

---

## Expected Output

```
============================================================
RushDB Neighbor Expansion Tutorial
============================================================

✓ Database initialized
✓ Checking for existing data...
✓ Seeding 8 categories and 15 products...
✓ Vector index ready

--- Basic 2-hop Expansion ---
Found 3 products in 'Computers & Tablets'
  - Wireless Keyboard ($79.99)
  - Gaming Keyboard ($149.99)
  - Business Laptop ($999.99)

--- Relationship Type Filtering ---
Found 3 products using BELONGS_TO filter
  - Wireless Keyboard ($79.99)
  - Gaming Keyboard ($149.99)
  - Business Laptop ($999.99)

--- Depth-Limited Expansion ---
Direct category (depth=1): 3 products
Full taxonomy (depth=2): 3 products
Max-results enforced: 2 products

--- Vector Similarity Ranking ---
Query: "ergonomic typing experience"
Top 5 products ranked by semantic similarity:
  - Wireless Keyboard: score=0.892
  - Gaming Keyboard: score=0.734
  - Developer Laptop: score=0.701
  - Business Laptop: score=0.658
  - Flagship Phone: score=0.423

============================================================
Tutorial complete!
============================================================
```

---

## How It Works

### The Graph Model

RushDB stores records as nodes and automatically creates relationships when you nest JSON or use `attach()`. For this tutorial:

1. **Categories** are linked via `PARENT_OF` relationships forming a taxonomy
2. **Products** are linked to categories via `BELONGS_TO` relationships
3. **Embeddings** are pre-computed and stored for vector similarity search

### Expansion Patterns

**Pattern 1: Related Record Filtering**
The `where` clause accepts related record labels as keys. When you write `{"CATEGORY": {"slug": "computers"}}`, RushDB traverses the `BELONGS_TO` edge and filters by the category's `slug` property.

**Pattern 2: Relationship Type Filtering**
Use `$relation` inside a related record filter to specify exact edge type and direction: `{ "CATEGORY": { "$relation": {"type": "BELONGS_TO", "direction": "out"}, "slug": ... } }`.

**Pattern 3: Vector Re-Ranking**
After getting expansion candidates, use `db.ai.search()` with an `$in` filter on record IDs to re-rank results by semantic similarity without fetching all candidates into memory.

**Pattern 4: Depth Limits**
Control query scope by:
- Setting explicit `limit` on result sets
- Using depth parameters to choose between single-hop vs. multi-hop expansion
- Applying `skip` + `limit` for pagination on large result sets

---

## Common Pitfalls

### ❌ Don't use `$via`
The `$via` operator doesn't exist in RushDB. Use `{ "RELATED_LABEL": {...} }` for relationship filtering.

### ❌ Don't use positional arguments
RushDB Python SDK uses keyword-only arguments: `db.records.create(label="PRODUCT", data={...})`.

### ❌ Don't access `record.__id`
Python name-mangling converts this to `_Record__id`. Use `record.id` instead.

### ❌ Don't double-commit transactions
When using `with db.transactions.begin() as tx:`, don't call `tx.commit()` inside the block — the context manager handles it automatically.

---

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB SDK Reference](https://docs.rushdb.com/sdk/python)
- [Property Graph Model](https://docs.rushdb.com/concepts/property-graph)
- [Vector Search](https://docs.rushdb.com/features/vector-search)
