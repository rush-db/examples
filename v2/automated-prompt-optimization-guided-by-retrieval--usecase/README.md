# Automated Prompt Optimization Guided by Retrieval Success Metrics

A practical demonstration of using RushDB's hybrid graph + vector architecture to build a feedback loop that continuously improves prompt quality based on retrieval outcomes.

## Scenario: Technical Documentation Search Assistant

This project implements a documentation search assistant for a developer tools company. The challenges in this domain are representative of many retrieval-heavy applications:

- **Domain-specific jargon**: Terms like "hot reload", "HMR", "tree-shaking" have precise meanings that differ from general usage
- **Ambiguous queries**: "doesn't work" could mean runtime errors, build failures, or configuration issues
- **Multi-intent requests**: "How do I set up CI/CD with container registry and custom domains?" contains three distinct sub-intents

## What This Demo Shows

1. **Data Model**: How RushDB's property graph captures the full retrieval lifecycle — queries, retrieval paths, results, and outcomes
2. **Vector + Graph Hybrid**: Semantic search via embeddings + graph traversal for structural relationships (documentation hierarchy, related concepts)
3. **Feedback Loop**: How retrieval success/failure metrics feed into prompt optimization suggestions
4. **Measurable Results**: Comparison of retrieval quality before and after prompt optimization

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Query     │────▶│  Retrieval  │────▶│   Result    │
│   (User)    │     │   Engine    │     │  (Record)   │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Metric    │────▶│   Prompt    │
                    │   Tracker   │     │ Optimizer   │
                    └─────────────┘     └─────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (free tier works)
- `sentence-transformers` for embeddings (all-MiniLM-L6-v2, 384 dimensions)

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Demo

```bash
# Seed the database with technical documentation (one-time setup)
python seed.py

# Run the main demonstration
python main.py
```

The demo will:
1. Load sample documentation from RushDB (or seed if empty)
2. Run a series of test queries through unoptimized prompts
3. Analyze retrieval outcomes using RushDB's graph queries
4. Generate optimized prompts based on patterns
5. Re-run queries and compare results

## Expected Output

```
=== Retrieval Quality Analysis ===
Queries analyzed: 12
Average precision@3: 0.42
Failed retrievals: 5 (42%)

Top failure patterns:
  • Vague intent (e.g., "doesn't work") → 3 failures
  • Missing domain terminology → 2 failures

=== Generated Prompt Optimizations ===

Suggestion 1: Add intent classification prefix
  Original: {query}
  Suggested: "Developer API question about: {query}\nClassify intent: [Troubleshooting/How-to/Reference]"
  Expected improvement: +15% precision

Suggestion 2: Include domain context
  Suggested: "As a {role} working with {tool}, I want to {query}"
  Expected improvement: +23% precision

=== After Optimization ===
Queries re-tested: 12
Average precision@3: 0.71
Failed retrievals: 2 (17%)

Improvement: +69% relative precision gain
```

## Honest Assessment of Limits

This approach works best when:
- You have sufficient historical data to identify patterns
- Retrieval failures have clear root causes
- Domain terminology can be semantically anchored

It struggles with:
- Novel queries that don't match historical patterns
- Purely subjective quality judgments ("helpful" vs "correct")
- Real-time requirements where optimization latency matters

## Project Structure

```
automated-prompt-optimization-guided-by-retrieval--usecase/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── seed.py            # Generates mock documentation and creates indexes
├── main.py            # Core retrieval + feedback loop implementation
└── data/
    └── seed_data.json # Sample technical documentation (inline in seed.py)
```

## Key RushDB Features Used

- **Vector search** (`db.ai.search`) for semantic similarity
- **Graph relationships** (`db.records.attach`) for documentation hierarchy
- **Property graph queries** (`db.records.find`) for retrieval path analysis
- **Transactions** for atomic feedback recording

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Vector Search in RushDB](https://docs.rushdb.com/ai-search)
- [Property Graph Model](https://docs.rushdb.com/concepts/property-graph)
