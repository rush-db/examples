# Personalization Engine Architecture Using Behavioral Graph Analysis

A production-grade tutorial demonstrating how to build a real-time personalization engine using RushDB's property graph capabilities. This project showcases behavioral data modeling, interest profiling, collaborative filtering, and session-based recommendations.

## What This Project Demonstrates

- **Behavioral Graph Modeling**: Structuring user behavior as a traversable property graph
- **Interest Profiling**: Deriving user preferences from interaction history
- **Product Similarity**: Computing recommendations via co-occurrence analysis
- **Session Analytics**: Tracking real-time browsing patterns for contextual suggestions
- **Collaborative Filtering**: Finding similar users for cross-recommendations

## Architecture Overview

```
┌─────────────┐    BEHAVIOR_EVENT    ┌─────────────┐
│    USER     │◄─────────────────────►│   PRODUCT   │
└─────────────┘                      └─────────────┘
       │                                    ▲
       │ INTERESTS_IN                       │
       ▼                                    │
┌─────────────┐                             │
│  INTEREST   │─────────────────────────────┘
│  (implicit) │        SIMILAR_TO
└─────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account with API key
- Neo4j-based property graph storage

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your RUSHDB_API_KEY
```

### 3. Seed the Database

```bash
python seed.py
```

This generates:
- 50 synthetic users with demographic profiles
- 120 products across 6 categories
- 1,500+ behavioral events (views, clicks, purchases, cart adds)
- Session chains for sequence analysis

### 4. Run the Personalization Engine

```bash
python main.py
```

## Project Structure

| File | Purpose |
|------|---------|
| `seed.py` | Generates synthetic behavioral dataset |
| `main.py` | Core personalization engine implementation |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

## Key Components

### 1. Behavioral Event Tracking

Every user action creates a `BEHAVIOR_EVENT` record linked to both user and product, enabling:
- Real-time intent signals
- Temporal pattern analysis
- Cross-session continuity

### 2. Interest Derivation

User interests are computed from behavior weight:
- `VIEW`: 1.0
- `CLICK`: 2.5
- `ADD_TO_CART`: 5.0
- `PURCHASE`: 10.0

### 3. Collaborative Filtering

Similar users identified by:
- Shared product interactions (Jaccard similarity)
- Overlapping category preferences
- Behavioral pattern matching

### 4. Session-Based Recommendations

Current session context + recent views → immediate next-action predictions

## Output Example

```
=== User Profile: user_001 ===
Interests: Electronics (score: 25.5), Books (score: 18.0)
Behavior Count: 47 events

=== Collaborative Recommendations ===
Product "Wireless Headphones" - Similar users bought this
Product "USB-C Hub" - Category affinity match
Product "Mechanical Keyboard" - Co-purchase pattern

=== Session-Based Suggestions ===
Based on recent views: ["Laptop Stand", "Monitor Arm"]

=== Product Affinity ===
"Laptop Stand" → frequently bought with → "USB-C Hub"
```

## Customization

The engine is modular. Key extension points:

- **Scoring weights**: Modify `BEHAVIOR_WEIGHTS` in `main.py`
- **Similarity thresholds**: Adjust for stricter/looser matching
- **Category hierarchy**: Expand the product taxonomy
- **Real-time scoring**: Add streaming updates via webhooks

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/personalization-engine-architecture-using-behavior-tutorial)
