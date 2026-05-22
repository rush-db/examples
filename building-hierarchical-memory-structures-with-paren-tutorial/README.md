# Building Hierarchical Memory Structures with Parent-Child Relationships

This tutorial demonstrates how to use RushDB to build and query hierarchical memory structures using parent-child relationships. You'll learn how to model organizational data, file systems, product taxonomies, and other tree-like structures.

## What You'll Learn

- **Modeling hierarchies** in RushDB using labels and relationships
- **Creating parent-child links** with `db.records.attach()`
- **Traversing relationships** to query descendants and ancestors
- **Filtering by related records** using the `where` clause
- **Batched operations** with transactions for bulk hierarchy creation

## Prerequisites

- Python 3.9+
- A RushDB account (free tier available at [rushdb.com](https://rushdb.com))
- API key from your RushDB dashboard

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

### 3. Seed the Database (Optional)

The seed script creates a realistic product category hierarchy with sample products. Run it once to populate test data:

```bash
python seed.py
```

Expected output:
```
Seeding product categories...
Created: Electronics
Created: Computers
Created: Laptops
Created: Smartphones
Created: Clothing
Created: Footwear
Created: Accessories
Created 12 products
Seeding complete!
```

## Running the Tutorial

```bash
python main.py
```

### Expected Output

```
=== Hierarchical Memory Structures with RushDB ===

--- Example 1: Building a Category Tree ---
Created category: Electronics
Created category: Computers
Created category: Laptops
Created category: Smartphones
Linked Computers → Electronics (PARENT_OF)
Linked Laptops → Computers (PARENT_OF)
Linked Smartphones → Computers (PARENT_OF)

--- Example 2: Querying Related Records ---
Finding Laptops under Computers...
Found 1 categories under Computers: Laptops

Finding all descendants of Electronics...
Descendants of Electronics: Computers, Laptops, Smartphones

Finding category hierarchy by reverse traversal...
Parent of Laptops: Computers
Grandparent of Laptops: Electronics

--- Example 3: Attaching Leaf Records ---
Found 5 products in Laptops category

--- Example 4: Batch Operations with Transactions ---
Created 3 new products (batch mode)

--- Example 5: Deep Traversal (Multi-level) ---
Products under Electronics (2 levels deep):
  - Computers
    - Laptops (with 8 products)
    - Smartphones (with 4 products)

=== Tutorial Complete ===
```

## How It Works

### Data Model

We model a product category hierarchy where:

- **Categories** are records with a `PARENT_OF` relationship to child categories
- **Products** are records that attach to their direct category via `BELONGS_TO`

```
Electronics
└── Computers
    ├── Laptops (has 8 products)
    └── Smartphones (has 4 products)
```

### Key RushDB Operations

#### 1. Creating Parent-Child Links

```sdk
# Create category records
parent = db.records.create(label="CATEGORY", data={"name": "Electronics"})
child = db.records.create(label="CATEGORY", data={"name": "Computers"})

# Link them with attach
db.records.attach(
    source=parent,
    target=child,
    options={"type": "PARENT_OF"}
)
```

#### 2. Querying by Related Record

```sdk
# Find all children of a parent category
children = db.records.find({
    "labels": ["CATEGORY"],
    "where": {
        "CATEGORY": {
            "$relation": {"type": "PARENT_OF", "direction": "in"},
            "name": "Computers"
        }
    }
})
```

#### 3. Filtering Records by Related Records

```sdk
# Find products in a specific category
products = db.records.find({
    "labels": ["PRODUCT"],
    "where": {
        "CATEGORY": {"$relation": {"type": "BELONGS_TO", "direction": "in"},
            "name": "Laptops"
        }
    }
})
```

## Concepts Covered

| Concept | Description |
|---------|-------------|
| **Parent-Child Links** | Using `attach()` to create directional relationships between records |
| **Relationship Types** | Named edges like `PARENT_OF`, `BELONGS_TO` provide semantic meaning |
| **Directional Queries** | `$relation.direction` controls traversal direction (`in` or `out`) |
| **Transitive Queries** | Chaining relationship filters for multi-level traversal |
| **Transaction Batching** | Grouping multiple operations for atomic commits |

## Project Structure

```
building-hierarchical-memory-structures-with-paren-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py           # Mock data generator
└── main.py           # Tutorial code
```

## API Reference

- [Records API](https://docs.rushdb.com/api/records)
- [Relationships API](https://docs.rushdb.com/api/relationships)
- [Transactions](https://docs.rushdb.com/api/transactions)
