# Building a Graph-Enhanced Code Review Assistant

A practical tutorial demonstrating how to build a code review assistant using RushDB's property graph capabilities. This project shows how to model code review data as an interconnected graph, enabling powerful queries like finding the best reviewers, tracking review patterns, and identifying bottlenecks.

## What You'll Learn

- **Graph modeling** for code review entities (PRs, authors, reviewers, comments)
- **Relationship traversal** to find reviewers by expertise and history
- **Transaction patterns** for atomic graph updates
- **Property-based queries** for filtering by related record characteristics
- **Upsert patterns** for idempotent data management

## Prerequisites

- Python 3.9+
- A RushDB account ([get one free](https://app.rushdb.com))
- `pip` or `uv` for dependency management

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `RUSHDB_API_KEY` — Your RushDB API key from the dashboard
- `RUSHDB_URL` — API endpoint (optional, defaults to cloud)


### 3. Seed the Database

The seed script creates sample code review data representing a small engineering team:

```bash
python seed.py
```

This creates:
- 3 repositories
- 6 developers
- 12 pull requests across various states
- 30+ comments
- Review relationships (approved, requested, commented)

The seed script is **idempotent** — safe to run multiple times.

### 4. Run the Tutorial

```bash
python main.py
```

## Expected Output

```
=== Graph-Enhanced Code Review Assistant ===

--- Query 1: Find PRs by author ---
Found 3 PRs by alice:
  PR #42: "Add caching layer" (OPEN)
  PR #38: "Fix auth bug" (MERGED)
  PR #35: "Update README" (MERGED)


--- Query 2: Find reviewers with most approvals ---
Top reviewers:
  - charlie: 4 approvals
  - bob: 3 approvals
  - diana: 2 approvals

--- Query 3: Find PRs in repository with pending reviews ---
PRs needing review in api-service:
  PR #45: "Add rate limiting" (OPEN)
    Reviewers: [charlie]
  PR #43: "Refactor endpoints" (OPEN)
    Reviewers: [bob, charlie]

--- Query 4: Find slow-to-review PRs ---
PRs open > 3 days without approval:
  PR #45: 5 days - "Add rate limiting"
  PR #44: 4 days - "Update dependencies"

--- Query 5: Find co-reviewer patterns ---
Developers who frequently review together:
  charlie and bob reviewed 3 PRs together

--- Query 6: Find author expertise by file patterns ---
  alice specializes in: ['src/cache/', 'src/auth/']
  bob specializes in: ['src/api/', 'src/middleware/']
```

## Project Structure

```
building-a-graph-enhanced-code-review-assistant-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Mock data generator
└── main.py            # Main tutorial code
```

## Key Concepts Demonstrated

### 1. Graph Model Design

Code review data naturally forms a graph:

```
[REPO] ──owns──> [PR] ──authored_by──> [AUTHOR]
                   │
                   ├──requests_review──> [REVIEWER]
                   │
                   ├──has_comment──> [COMMENT] ──authored_by──> [AUTHOR]
                   │
                   └──changes──> [FILE] ──owned_by──> [AUTHOR]
```

### 2. Relationship Traversal

Use `where` clauses with related labels to filter by connected records:

```sdk
# Find all PRs authored by a developer with a specific expertise
db.records.find({
    "labels": ["PULL_REQUEST"],
    "where": {
        "AUTHOR": {"$relation": {"type": "AUTHORED_BY", "direction": "in"}},
        "AUTHOR": {"expertise": {"$contains": "backend"}}
    }
})
___SPLIT___
// Find all PRs authored by a developer with a specific expertise
await db.records.find({
    labels: ['PULL_REQUEST'],
    where: {
        'AUTHOR': {
            $relation: { type: 'AUTHORED_BY', direction: 'in' },
            expertise: { $contains: 'backend' }
        }
    }
})
```


### 3. Transaction Patterns

Create PR with all relationships atomically:

```sdk
with db.transactions.begin() as tx:
    pr = db.records.create(
        label="PULL_REQUEST",
        data={"number": 42, "title": "Add feature", "status": "OPEN"},
        transaction=tx
    )
    author = db.records.find({"labels": ["AUTHOR"], "where": {"username": "alice"}}).data[0]
    db.records.attach(source=pr, target=author, options={"type": "AUTHORED_BY"}, transaction=tx)
    # Context manager handles commit/rollback automatically
___SPLIT___
const tx = await db.transactions.begin()
try {
    const pr = await db.records.create({
        label: 'PULL_REQUEST',
        data: { number: 42, title: 'Add feature', status: 'OPEN' }
    }, tx)
    const authors = await db.records.find({ labels: ['AUTHOR'], where: { username: 'alice' } })
    const author = authors.data[0]
    await db.records.attach({
        source: pr,
        target: author,
        options: { type: 'AUTHORED_BY' }
    }, tx)
    await tx.commit()
} catch (e) {
    await tx.rollback()
    throw e
}
```

## Further Exploration


- Add vector embeddings for code similarity (find PRs with similar changes)
- Implement review time tracking and alerting
- Build a reviewer recommendation engine based on file expertise
- Add sentiment analysis to comments for review quality metrics

## Resources

- [RushDB Documentation](https://docs.rushdb.com)
- [Python SDK Reference](https://docs.rushdb.com/sdks/python)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-a-graph-enhanced-code-review-assistant-tutorial)
