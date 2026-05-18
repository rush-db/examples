# Implementing Reranking with RushDB's Hybrid Query Capabilities

A practical tutorial demonstrating how to implement sophisticated reranking strategies using RushDB's hybrid query capabilities. This project shows senior engineers how to combine vector semantic search with structured filtering and custom relevance scoring.

## What This Demonstrates

- **Hybrid Query Pattern**: Combining semantic (vector) search with structured filtering
- **Two-Stage Retrieval**: Initial semantic search → reranking by structured criteria
- **Custom Reranking Strategies**: Scoring functions that blend multiple relevance signals
- **Graph-Aware Queries**: Leveraging RushDB's relationship traversal in reranking

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Query Request                              │
│                   "machine learning"                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stage 1: Semantic Vector Search                     │
│         RushDB AI Search on article content                     │
│         Returns top-K candidates with similarity scores         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stage 2: Structured Filtering                      │
│         Apply metadata filters (category, tags, date)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stage 3: Custom Reranking                           │
│         Combine semantic score + recency + popularity           │
│         Final ranking with blended relevance score              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Ranked Results                             │
│              Top-N results with final scores                    │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Node.js >= 18.x
- A RushDB account with an API key ([Get started](https://rushdb.com))
- `sentence-transformers` compatible environment or OpenAI API access for embeddings

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment**:
n   Copy `.env.example` to `.env` and add your credentials:
   ```bash
   cp .env.example .env
   ```

   Required variables:
   - `RUSHDB_API_KEY` — Your RushDB API key from the dashboard
   - `RUSHDB_URL` — API endpoint (defaults to cloud: `https://api.rushdb.com/api/v1`)

3. **Seed the database**:

   This creates sample articles with embeddings:
   ```bash
   npm run seed
   ```

   The seed script:
   - Creates 50 articles with realistic content
   - Generates embeddings for article bodies
   - Establishes category and author relationships
   - Is idempotent (safe to run multiple times)

## How to Run

### Basic Hybrid Search with Reranking

```bash
npm start
```

This executes a complete demo:
1. Performs semantic search for "machine learning"
2. Applies category and tag filters
3. Reranks results using a custom scoring function
4. Displays before/after rankings

### Run Specific Examples

```bash
# Interactive search
npx ts-node src/main.ts --query "deep learning neural networks"

# Search with specific filters
npx ts-node src/main.ts --query "data science" --category "research" --limit 10

# Show raw scores before/after reranking
npx ts-node src/main.ts --query "python programming" --show-scores
```

## Project Structure

```
.
├── README.md              # This file
├── package.json           # Dependencies and scripts
├── .env.example           # Environment template
├── data/
│   └── articles.json       # Sample article seed data
├── src/
│   ├── main.ts            # Main demo execution
│   ├── seed.ts            # Database seeding script
│   ├── types.ts           # TypeScript type definitions
│   ├── reranker.ts        # Reranking logic and scoring
│   └── search.ts          # Hybrid search implementation
└── tsconfig.json          # TypeScript configuration
```

## Reranking Strategy Explained

The demo implements a **Linear Combination Reranker** that blends multiple signals:

```typescript
finalScore = (α × semanticScore) + (β × recencyScore) + (γ × popularityScore)
```

Where:
- **semanticScore** (0-1): Vector similarity from RushDB AI search
- **recencyScore** (0-1): Time decay based on publish date
- **popularityScore** (0-1): Normalized view count

Default weights: `α=0.5, β=0.3, γ=0.2`

## Expected Output

```
=== RushDB Hybrid Search with Reranking Demo ===

Query: "machine learning"
Filters: category=tech, tags includes [ai, ml]

--- Stage 1: Initial Semantic Search (top 20) ---
  [0.923] Introduction to Machine Learning Fundamentals
  [0.891] Deep Learning Architectures Overview
  [0.845] Python Data Processing Guide
  ...

--- Stage 2: After Reranking ---
  [0.812] Machine Learning Best Practices 2024  ← boosted by recency
  [0.789] Deep Learning Architectures Overview
  [0.756] ML Pipeline Optimization Techniques
  ...

--- Score Breakdown (top 3) ---
┌─────────────────────────────────────────────────────────────┐
│ Machine Learning Best Practices 2024                        │
│   Semantic: 0.712 | Recency: 0.95 | Popularity: 0.88        │
│   Final: 0.812                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key SDK Methods Used

| Method | Purpose |
|--------|---------|
| `db.ai.search()` | Semantic vector search |
| `db.records.find()` | Structured data filtering |
| `db.ai.indexes.create()` | Create vector index |
| `db.ai.indexes.upsertVectors()` | Add embeddings to index |
| `db.transactions.begin()` | Batch operations |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Hybrid Search Best Practices](https://docs.rushdb.com/concepts/hybrid-search)
- [Vector Index Management](https://docs.rushdb.com/api/ai-indexes)

## License

MIT — see [LICENSE](./LICENSE) for details.
