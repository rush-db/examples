# Hands-On: Building a Graph-Powered Sentiment Analysis Pipeline

A complete tutorial demonstrating how to build a sentiment analysis pipeline using RushDB's property graph capabilities. This project shows how to store product reviews with sentiment scores, establish meaningful relationships between reviews, products, and customers, and query the resulting graph to extract actionable insights.

## What This Project Demonstrates

- **Graph-native sentiment storage**: Store reviews as nodes with sentiment scores and link them to products and customers
- **Relationship traversal**: Query across the graph to find patterns (e.g., "all negative reviews for products by a specific customer")
- **Transaction-based writes**: Batch create records atomically with RushDB transactions
- **Sentiment-based filtering**: Use RushDB's query engine to filter by sentiment score ranges
- **Real-time aggregation patterns**: Calculate metrics across related records using graph traversal

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://app.rushdb.com))
- RushDB API key

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your `RUSHDB_API_KEY`.

3. **Seed the database** (creates sample data):
   ```bash
   python seed.py
   ```
   The seed script generates 50 mock products, 30 customers, and 150 reviews with realistic sentiment distributions. It's idempotent—safe to run multiple times.

4. **Run the main pipeline**:
   ```bash
   python main.py
   ```

## Project Structure

```
.
├── main.py        # Main pipeline demonstrating RushDB graph operations
├── seed.py        # Generates mock data and imports to RushDB
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

### Data Model

```
[PRODUCT] ←─REVIEWED─ [REVIEW] ─WRITTEN_BY─ [CUSTOMER]
                              │
                              ▼
                         [SENTIMENT]
                           (score)
```

| Node Type | Properties |
|-----------|------------|
| PRODUCT | name, category, brand, price |
| CUSTOMER | name, email, membership_tier |
| REVIEW | content, rating (1-5), sentiment_score (-1 to 1), sentiment_label |
| SENTIMENT | label (positive/neutral/negative), confidence |

### Sentiment Analysis Approach

This tutorial uses **TextBlob** for lightweight, rule-based sentiment analysis:
- Returns polarity score from -1.0 (negative) to +1.0 (positive)
- Classifies into: Negative (<-0.1), Neutral (-0.1 to 0.1), Positive (>0.1)
- No API keys or external services required—perfect for tutorials

For production, consider upgrading to transformer-based models (BERT, RoBERTa) or API services (OpenAI, Google Cloud NL).

## Expected Output

```
=== Graph-Powered Sentiment Analysis Pipeline ===

[1] Creating sample review records...
    ✓ Created 3 reviews with sentiment scores

[2] Querying reviews by sentiment...
    Negative reviews (score < 0): 12 found
    Positive reviews (score > 0): 28 found
    Neutral reviews (score ≈ 0): 10 found

[3] Traversal: Finding customers with frequent negative reviews...
    Customer 'John Smith' has 4 negative reviews
    Customer 'Jane Doe' has 3 negative reviews

[4] Aggregating sentiment by product category...
    Electronics: avg sentiment = 0.23 (mostly positive)
    Clothing: avg sentiment = -0.05 (mixed reviews)
    Home & Garden: avg sentiment = 0.41 (highly positive)

[5] Finding similar reviews using graph relationships...
    Found 5 reviews with similar sentiment profiles
```

## RushDB Concepts Used

| Concept | Usage in this project |
|---------|----------------------|
| **Labels** | Categorize nodes: PRODUCT, CUSTOMER, REVIEW |
| **Records** | Store entities with typed properties |
| **Relationships** | Link reviews to products and customers |
| **Transactions** | Batch writes atomically |
| **Where clauses** | Filter by sentiment scores and other properties |

## Key RushDB SDK Patterns

```sdk
# Create a review record
review = db.records.create(
    label="REVIEW",
    data={
        "content": "Great product, highly recommend!",
        "rating": 5,
        "sentiment_score": 0.75,
        "sentiment_label": "positive"
    }
)
___SPLIT___
// TypeScript — 2-space indentation for every nested level
const review = await db.records.create({
    label: 'REVIEW',
    data: {
        content: 'Great product, highly recommend!',
        rating: 5,
        sentiment_score: 0.75,
        sentiment_label: 'positive'
    }
})
```

## API Reference

For complete RushDB documentation, visit: https://docs.rushdb.com

GitHub repository: https://github.com/rush-db/examples/tree/main/hands-on-building-a-graph-powered-sentiment-analys-tutorial

## Cleanup

To remove all seeded data:
```python
db.records.delete({"labels": ["REVIEW"], "where": {}})
db.records.delete({"labels": ["PRODUCT"], "where": {}})
db.records.delete({"labels": ["CUSTOMER"], "where": {}})
```
