# Query-by-Example: Using Existing Nodes to Retrieve Similar Context

This project demonstrates how to use **Query-by-Example (QBE)** in RushDB to find similar graph contexts by providing a single representative node — no complex traversal queries required.


## What is Query-by-Example in RushDB?

Query-by-Example is a retrieval pattern where you provide an existing record as a "seed" and RushDB finds records with similar properties, graph contexts, or vector embeddings. This eliminates the need to manually construct complex `WHERE` clauses or vector similarity queries.


In RushDB, QBE works through two complementary mechanisms:

1. **Property-based QBE** — Use `db.records.find()` with the example record's field values
2. **Vector-based QBE** — Use `db.ai.search()` with the example record's text content
3. **Hybrid QBE** — Combine graph traversal with semantic similarity

## Prerequisites

- Python 3.9+
- A RushDB account (free tier available at [rushdb.com](https://rushdb.com))
- `rushdb>=2.0.0` Python package

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

## Project Structure

```
query-by-example-using-existing-nodes-to-retrieve--tutorial/
├── README.md
├── requirements.txt
├── .env.example
├── seed.py              # Seed sample session data
└── main.py              # Main tutorial demonstrations
```

## Seed Data

Before running the tutorial, seed the database with sample user sessions:

```bash
python seed.py
```

This creates 15 user sessions across 4 user profiles, each with interaction data suitable for QBE queries.

## Running the Tutorial

```bash
python main.py
```

The tutorial covers:

### 1. Property-Based QBE
Find sessions similar to a known session using exact property matching.

### 2. Vector-Based QBE  
Find documents similar to an existing document using semantic search.

### 3. Hybrid QBE
Combine graph context (user relationships) with vector similarity for better results.

### 4. Edge Cases & Tuning
- Balancing graph distance vs. vector similarity
- Handling missing properties
- Tuning similarity thresholds

## Expected Output

```
================================================================================
QBE Tutorial: Finding Similar Contexts in RushDB
================================================================================

[1] Property-Based QBE: Finding Similar User Sessions
--------------------------------------------------------------------------------
Seed session: Session s_sarah_dashboard (user: sarah_chen, duration: 180s)
Found 3 similar sessions with same user:
  - Session s_sarah_profile (user: sarah_chen) - 95% field match
  - Session s_sarah_settings (user: sarah_chen) - 80% field match
  - Session s_sarah_reports (user: sarah_chen) - 70% field match

[2] Vector-Based QBE: Finding Similar Help Articles
--------------------------------------------------------------------------------
Using article about 'account security' as example...
Found 4 semantically similar articles:
  - 'Setting Up Two-Factor Authentication' (score: 0.94)
  - 'Managing Your Password' (score: 0.89)
  - 'API Authentication Guide' (score: 0.85)
  - 'Session Management' (score: 0.81)

[3] Hybrid QBE: Combining Graph Context with Vector Similarity
--------------------------------------------------------------------------------
Finding articles similar to 'billing_invoice' by same label AND content...
Found 2 hybrid matches:
  - 'Understanding Your Bill' (score: 0.88) - in BILLING label
  - 'Payment Methods' (score: 0.82) - in BILLING label

[4] Edge Cases & Tuning
--------------------------------------------------------------------------------
4a. Sessions with partial property match:
  - Found 5 sessions matching 'viewing_product' trigger

4b. Low-similarity threshold (0.5):
  - Found 8 articles with similarity >= 0.50

4c. High-similarity threshold (0.85):
  - Found 2 articles with similarity >= 0.85

4d. Graph-distance weighted (same user, any session):
  - Found 3 sessions within 1 hop from sarah_chen

================================================================================
Tutorial completed successfully!
================================================================================
```

## How It Works

### Property-Based QBE Pattern

```sdk
# Get an example record
example_session = db.records.find_one({
    "labels": ["SESSION"],
    "where": {"sessionId": "s_sarah_dashboard"}
})

# Use its properties as the QBE query
similar_sessions = db.records.find({
    "labels": ["SESSION"],
    "where": {
        "userId": example_session["userId"],
        "page": example_session["page"]
    }
})
```

### Vector-Based QBE Pattern

```sdk
# Get an example record with text content
example_article = db.records.find_one({
    "labels": ["ARTICLE"],
    "where": {"slug": "account-security"}
})

# Search using its content (server embeds automatically)
similar_articles = db.ai.search({
    "propertyName": "body",
    "query": example_article["body"],
    "labels": ["ARTICLE"],
    "limit": 5
})
```

### Hybrid QBE Pattern

```sdk
# Find similar records that ALSO share a graph relationship
user_sessions = db.records.find({
    "labels": ["SESSION"],
    "where": {
        "USER": {"userId": current_user["userId"]}
    }
})

# Then filter by semantic similarity
similar_to_last = db.ai.search({
    "propertyName": "body",
    "query": user_sessions[-1]["body"],
    "labels": ["DOCUMENT"],
    "limit": 10
})
```

## Key Takeaways

| Approach | Use Case | API Method |
|----------|----------|------------|
| Property QBE | Exact match on structured fields | `db.records.find()` |
| Vector QBE | Semantic similarity on text | `db.ai.search()` |
| Hybrid QBE | Structured + semantic combined | Both + graph traversal |

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
