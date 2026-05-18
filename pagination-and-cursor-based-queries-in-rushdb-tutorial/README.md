# Pagination and Cursor-Based Queries in RushDB

A practical tutorial demonstrating how to implement efficient pagination strategies in RushDB — from basic `skip/limit` pagination to cursor-based pagination for high-performance data traversal.

## What This Tutorial Covers

- **Basic pagination** with `skip` and `limit` parameters
- **Cursor-based pagination** using the "seek method" pattern
- **Page metadata** including total counts and page information
- **Best practices** for large dataset traversal
- **Performance considerations** for each approach

## Prerequisites

- Python 3.10+
- A RushDB project (get one at [rushdb.com](https://rushdb.com))
- `pip` or `uv` for dependency management

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your RushDB API key:

```bash
cp .env.example .env
```

Edit `.env`:

```
RUSHDB_API_KEY=your_api_key_here
```

### 3. Seed Mock Data

Before running the main tutorial, seed the database with sample articles:

```bash
python seed.py
```

This creates 100 mock articles across 5 categories. The seed script is idempotent — safe to run multiple times.

## How to Run

```bash
python main.py
```

## Expected Output

```
=== Basic Pagination Demo ===

Fetching page 1 (items 1-10 of 100):
  1. Article #0 (General)
  2. Article #1 (General)
  3. Article #2 (General)
  4. Article #3 (General)
  5. Article #4 (General)
  6. Article #5 (General)
  7. Article #6 (General)
  8. Article #7 (General)
  9. Article #8 (General)
  10. Article #9 (General)

Fetching page 2 (items 11-20 of 100):
  11. Article #10 (General)
  12. Article #11 (General)
  ...

=== Cursor-Based Pagination Demo ===

Page 1: Articles from 'article-0' to 'article-9'
Page 2: Articles from 'article-10' to 'article-19'
Page 3: Articles from 'article-20' to 'article-29'

=== Paginated Query with Filtering ===

Category 'tech' articles - Page 1:
  1. Tech Article #50
  2. Tech Article #51
  3. Tech Article #52
  4. Tech Article #53
  5. Tech Article #54
```

## Pagination Strategies Explained

### Strategy 1: Basic Pagination (skip/limit)

The simplest approach using RushDB's built-in pagination:

```sdk
result = db.records.find({
    "labels": ["ARTICLE"],
    "limit": 10,
    "skip": 0
})
___SPLIT___
const { data, total } = await db.records.find({
    labels: ['ARTICLE'],
    limit: 10,
    skip: 0
})
```

**Pros**: Simple, native support, includes total count
**Cons**: Performance degrades with large `skip` values (O(n) scan)
**Best for**: Small to medium datasets, admin UIs, "Jump to page X" features

### Strategy 2: Cursor-Based Pagination (Seek Method)

More performant for large datasets by using stable ordering:

```sdk
# First page - order by the cursor field
results = db.records.find({
    "labels": ["ARTICLE"],
    "limit": 10,
    "orderBy": {"id": "asc"}
})
last_id = results.data[-1].id if results.data else None

# Next page - start AFTER the last item
if last_id:
    results = db.records.find({
        "labels": ["ARTICLE"],
        "limit": 10,
        "where": {"id": {"$gt": last_id}},
        "orderBy": {"id": "asc"}
    })
___SPLIT___
// First page
let { data } = await db.records.find({
    labels: ['ARTICLE'],
    limit: 10,
    orderBy: { id: 'asc' }
})
let lastId = data[data.length - 1]?.id

// Next page
if (lastId) {
    const next = await db.records.find({
        labels: ['ARTICLE'],
        limit: 10,
        where: { id: { $gt: lastId } },
        orderBy: { id: 'asc' }
    })
}
```

**Pros**: Consistent performance regardless of page number, no count scans
**Cons**: No random access ("go to page 5"), no total count without extra query
**Best for**: Infinite scroll, API pagination, large dataset exports

## Project Structure

```
pagination-and-cursor-based-queries-in-rushdb-tutorial/
├── .env.example          # Environment template
├── .env                   # Your API key (git-ignored)
├── requirements.txt       # Dependencies
├── seed.py               # Mock data generator
├── main.py               # Tutorial code
└── README.md             # This file
```

## Key Takeaways

| Strategy | Use When |
|----------|----------|
| `skip/limit` | Small datasets, need total count, random page access |
| Cursor-based | Large datasets, infinite scroll, API endpoints |
| Filtered + Cursor | Category views, user-specific data, dated queries |

## Resources

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/pagination-and-cursor-based-queries-in-rushdb-tutorial)
- [RushDB SDK Reference](#)
