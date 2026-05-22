# Graph-based Entity Deduplication using RushDB Relationships

This tutorial demonstrates how to perform sophisticated entity deduplication using RushDB's graph relationship capabilities. Unlike simple exact-match deduplication, graph-based approaches can identify duplicate entities by analyzing shared relationships, indirect connections, and overlapping property patterns.

## What You'll Learn

- How to model entities with rich relationship graphs in RushDB
- Strategies for identifying duplicate candidates through relationship analysis
- Techniques for merging duplicate entities while preserving graph integrity
- When graph-based deduplication outperforms traditional methods

## Why Graph-based Deduplication?

Traditional deduplication relies on exact or fuzzy property matching (email, phone, name). However:

1. **Data quality issues**: Typos, formatting differences, and incomplete data break exact matching
2. **Limited signals**: Single-field matching misses duplicates with partial overlap
3. **No context**: Property matching ignores the relational context of entities

Graph-based deduplication overcomes these by:
- Analyzing shared relationships (e.g., two people who share the same employer, address, or contacts)
- Building confidence scores based on multiple weak signals
- Leveraging transitive relationships (A shares info with B, B shares with C → A and C may be related)

## Data Model

Our example models a customer database with potential duplicates:

```
┌─────────────────────────────────────────────────────────────────┐
│                        CANONICAL_CUSTOMER                        │
│                              (id: c1)                            │
│                    ┌─────────────────────┐                      │
│                    │ email: john@acme.co │                      │
│                    │ phone: +1-555-0123  │                      │
│                    └─────────────────────┘                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │  ORDER_1  │        │  ORDER_2  │        │  ORDER_3  │
    └──────────┘        └──────────┘        └──────────┘
          ▲                    ▲                    ▲
          │         ┌──────────┴──────────┐         │
          │         │                     │         │
    ┌──────────┐    │    POTENTIAL         │    ┌──────────┐
    │ DUPLICATE│◄───┤    DUPLICATE         ├───►│ DUPLICATE│
    │  (c2)    │    │      (c3)             │    │   (c4)   │
    └──────────┘    └─────────────────────┘    └──────────┘
```

All three customers are identified as duplicates because they share:
- The same email domain (acme.co)
- The same phone area code
- Multiple shared orders
- Indirect relationship through shared contacts

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier available at https://rushdb.com)
- `rushdb>=2.0.0` Python SDK

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_TOKEN
   ```

3. **Seed the database (creates sample data with duplicates):**
   ```bash
   python seed.py
   ```

4. **Run the deduplication:**
   ```bash
   python main.py
   ```

## Expected Output

```
=== Graph-based Entity Deduplication ===

Loading 50 customer records with relationships...
Found 12 potential duplicate groups

Duplicate Group #1:
  Canonical: CUSTOMER_canonical_001 (John Smith - john@acme.co)
  Duplicates: 2 records merged
  Shared signals:
    - Email domain: acme.co (2 records)
    - Phone prefix: +1-555 (2 records)
    - Shared orders: 3
    - Shared contacts: 1
  Confidence: 0.92

Duplicate Group #2:
  Canonical: CUSTOMER_canonical_004 (Jane Doe - jane@startup.io)
  Duplicates: 1 records merged
  Shared signals:
    - Email domain: startup.io (2 records)
    - Exact phone match
  Confidence: 0.88

...

Deduplication complete:
  12 duplicate groups resolved
  50 records → 38 unique customers
  15 orders re-linked
  8 contacts re-linked
```

## How It Works

### Step 1: Relationship Analysis

For each pair of potential duplicates, we analyze:

- **Direct shared relationships**: Same orders, addresses, companies
- **Indirect connections**: Shared contacts who interact with both entities
- **Property similarity**: Email domain, phone prefix, name fuzzy match

### Step 2: Similarity Scoring

```python
def calculate_dedup_score(customer_a, customer_b, shared_signals):
    """
    Compute deduplication confidence score.
    
    Signals are weighted by reliability:
    - Shared orders: 0.35 (strongest indicator)
    - Shared contacts: 0.25
    - Email domain match: 0.20
    - Phone prefix match: 0.15
    - Address match: 0.05
    """
    score = 0.0
    
    if shared_signals["shared_orders"] > 0:
        score += 0.35 * min(shared_signals["shared_orders"] / 3, 1.0)
    
    if shared_signals["shared_contacts"] > 0:
        score += 0.25 * min(shared_signals["shared_contacts"] / 2, 1.0)
    
    # ... additional signal calculations
    
    return min(score, 1.0)
```

### Step 3: Clustering

Records are clustered using Union-Find to group all related duplicates:

```python
def union_find_dedup(customers):
    """
    Group all records that should be merged together.
    Uses relationship graph to find transitive connections.
    """
    uf = UnionFind()
    
    for customer in customers:
        for other in find_potential_duplicates(customer):
            if calculate_dedup_score(customer, other) > THRESHOLD:
                uf.union(customer.id, other.id)
    
    return uf.get_clusters()
```

### Step 4: Consolidation

For each cluster, we:

1. Select the canonical record (most relationships, most complete data)
2. Re-link all relationships to the canonical record
3. Merge property data (canonical record wins on conflicts)
4. Delete the duplicate records

## When to Use Graph-based Deduplication

| Scenario | Best Approach |
|----------|----------------|
| Customer records with shared orders | Graph-based ✓ |
| User accounts with social connections | Graph-based ✓ |
| Product catalog with category hierarchy | Property-based |
| Simple email-only deduplication | Exact match |
| Companies with shared addresses | Graph-based ✓ |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://github.com/rush-db/sdk-python)
- [Property Graph Deduplication Patterns](https://docs.rushdb.com/concepts/relationships)

## Repository

https://github.com/rush-db/examples/tree/main/graph-based-entity-deduplication-using-rushdb-rela-tutorial
