# Self-Improving Knowledge Bases with RushDB Feedback Loops

A production-grade demonstration of how RushDB's dual graph+vector architecture enables knowledge bases that learn from user corrections. This project shows a complete feedback loop: correction → propagation → ranking improvement.

## Why This Architecture Matters

Traditional vector stores treat knowledge as flat embeddings. When a user corrects an article, the correction exists in isolation. RushDB's architecture means every correction is a first-class graph edge that:

1. **Propagates** to related articles (correcting one Python article updates related Python articles)
2. **Builds trust** scores based on correction frequency and source reliability
3. **Creates provenance** so every search result can explain its ranking
4. **Combines semantic similarity** with graph-based trust for better relevance

## What This Demo Shows

- **Correction as Graph Edges**: User corrections stored with full metadata (user_id, timestamp, context, type)
- **Correction Propagation**: One correction triggers updates to related articles
- **Trust Score Computation**: Graph traversal determines article reliability
- **Hybrid Ranking**: Vector similarity + trust score = better results
- **Provenance Chains**: Every result explains why it ranked

## Prerequisites

- Python 3.9+
- RushDB account ([free tier](https://rushdb.com) is sufficient)
- Sentence transformers for embeddings

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RUSHDB_API_KEY
```

## Running

```bash
# 1. Seed the knowledge base with sample articles
python seed.py

# 2. Run the complete feedback loop demo
python main.py
```

The main script demonstrates:
1. Semantic search BEFORE corrections (baseline)
2. User submits a factual correction
3. Correction propagates to related articles
4. Trust scores recalculate
5. Semantic search AFTER corrections (improved ranking)

## Project Structure

```
self-improving-knowledge-bases-with-rushdb-feedbac-usecase/
├── README.md
├── requirements.txt
├── .env.example
├── seed.py              # Knowledge base initialization
├── main.py              # Complete feedback loop demonstration
└── data/
    └── corrections.json # Sample user corrections
```

## Key Architecture Decisions

### Labels

| Label | Purpose |
|-------|---------|
| `Article` | Knowledge base entries with body text |
| `Correction` | User-submitted fixes with metadata |
| `User` | Correction contributors |

### Relationships

| Type | Direction | Purpose |
|------|-----------|---------|
| `CORRECTED` | Correction → Article | Links fix to original |
| `RELATED_TO` | Article ↔ Article | Knowledge graph links |
| `AUTHORED` | User → Correction | Provenance chain |
| `CORRECTION_RECEIVED` | Article → Correction | What corrections affect an article |

### Trust Score Algorithm

```
trust_score = base_score
             + correction_bonus          (positive corrections add trust)
             - correction_penalty       (negative corrections reduce trust)
             + user_reputation_factor   (trusted users' corrections matter more)
             - correction_decay         (old corrections fade in importance)
```

## Expected Output

```
=== SEMANTIC SEARCH BEFORE CORRECTIONS ===
Query: "how to handle memory management in Python"
Results: sorted by vector similarity only

=== USER SUBMITS CORRECTION ===
User alice@example.com corrects article #1
Old: "Python uses automatic garbage collection"
New: "Python uses reference counting with cyclic garbage collection"

=== CORRECTION PROPAGATES ===
Found 3 related articles
Propagating correction to: "Python Memory Management Deep Dive"
Propagating correction to: "Garbage Collection Strategies"
Propagating correction to: "Python Performance Optimization"

=== TRUST SCORES RECALCULATE ===
Article #1 trust: 0.95 (many verified corrections)
Article #2 trust: 0.78 (some corrections applied)
Article #3 trust: 0.82 (connected to high-trust articles)

=== SEMANTIC SEARCH AFTER CORRECTIONS ===
Query: "how to handle memory management in Python"
Results: sorted by hybrid score (similarity × trust)
Provenance: Each result shows which corrections affected its ranking
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/self-improving-knowledge-bases-with-rushdb-feedbac-usecase)
- [RushDB Pricing](https://rushdb.com/pricing)
