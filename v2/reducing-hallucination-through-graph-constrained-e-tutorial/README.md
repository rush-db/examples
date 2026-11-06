# Reducing Hallucination Through Graph-Constrained Evidence Retrieval

A practical tutorial demonstrating how to use RushDB's property graph structure to reduce LLM hallucinations by constraining retrieval to verified, provenance-tracked evidence chains.

## The Problem

LLMs hallucinate when they:
1. **Lack grounding context** — generate text without verified source material
2. **Miss provenance** — cannot trace claims back to authoritative sources
3. **Ignore dependencies** — present facts without understanding causal/evidential chains

## The Solution: Graph-Constrained Retrieval

By storing knowledge as a typed property graph with explicit provenance relationships, we can:

1. **Trace every claim to its source** — follow `CLAIMED_BY` → `SOURCE` edges
2. **Verify dependency chains** — follow `DEPENDS_ON` edges to ensure conclusions are well-supported
3. **Constrain retrieval scope** — only return evidence with `verified: true` and direct source paths
4. **Score evidence by trust** — weight claims by source authority and cross-reference density

## Project Structure

```
reducing-hallucination-through-graph-constrained-e-tutorial/
├── seed.py           # Populates knowledge graph with claims, sources, verifications
├── main.py           # Demonstrates graph-constrained evidence retrieval
├── requirements.txt  # Dependencies
├── .env.example      # Environment template
└── data/             # Seed data (auto-generated)
```

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- `rushdb>=2.0.0`

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/rush-db/examples.git
cd reducing-hallucination-through-graph-constrained-e-tutorial

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Example

```bash
# Step 1: Seed the knowledge graph (safe to run multiple times — idempotent)
python seed.py

# Step 2: Run the main demonstration
python main.py
```

## What the Code Demonstrates

### 1. Knowledge Graph Schema

We model knowledge with these labels:

| Label | Purpose |
|-------|---------|
| `SOURCE` | Authoritative documents (papers, docs, reports) |
| `CLAIM` | Factual statements extracted from sources |
| `CONCEPT` | Topic entities for semantic organization |
| `VERIFICATION` | Trust assessment linking claims to sources |

### 2. Relationship Types

| Type | Direction | Purpose |
|------|-----------|---------|
| `MAKES_CLAIM` | SOURCE → CLAIM | Author claims X |
| `SUPPORTS` | VERIFICATION → CLAIM | Evidence confirms claim |
| `ATTESTS` | SOURCE → VERIFICATION | Source provides verification |
| `RELATES_TO` | CONCEPT ↔ CONCEPT | Topic connections |
| `ADDRESSES` | CLAIM → CONCEPT | Claim about topic |
| `DEPENDS_ON` | CLAIM → CLAIM | Claim requires other claim |

### 3. Graph-Constrained Retrieval Flow

```
User Query: "What is the relationship between X and Y?"
        ↓
1. Semantic Search → Find relevant CONCEPT nodes
        ↓
2. Graph Traversal → Follow CONCEPT → CLAIM → SOURCE edges
        ↓
3. Verification Filter → Only return verified claims (verified: true)
        ↓
4. Provenance Check → Trace each claim back to SOURCE via MAKES_CLAIM
        ↓
5. Dependency Validation → Ensure DEPENDS_ON claims are also satisfied
        ↓
6. Evidence Assembly → Return structured, source-traced responses
```

### 4. Hallucination Prevention Techniques

1. **Source Gating**: Claims without `MAKES_CLAIM` edge are excluded
2. **Verification Enforcement**: Only `verified: true` claims enter the context
3. **Dependency Tracking**: Complex claims are rejected if dependencies fail
4. **Authority Weighting**: Trust scores based on source reliability

## Expected Output

```
=== Graph-Constrained Evidence Retrieval Demo ===

[1] Loading Knowledge Graph Schema...
    - Sources: 5
    - Claims: 15
    - Verifications: 12
    - Concepts: 8

[2] Query: "What are the key findings about machine learning interpretability?"

    Found 3 verified claims:
    
    ┌─ Claim: "SHAP values provide consistent feature attribution"
    │  Source: arxiv.org/papers/2019.01115
    │  Verified: ✓ (confidence: 0.95)
    │  Dependencies: Met (1/1)
    │  
    └─ Claim: "Model-agnostic methods outperform model-specific approaches"
       Source: Nature ML Journal Vol. 4
       Verified: ✓ (confidence: 0.88)
       Dependencies: Met (2/2)

[3] Hallucination Prevention Summary:
    - Claims retrieved: 3
    - Claims filtered (unverified): 0
    - Claims filtered (missing provenance): 0
    - Claims filtered (dependency failed): 0
    
    Retrieval confidence: HIGH
```

## Key Takeaways

1. **Graph structure enables provenance** — Every claim traces back to a SOURCE
2. **Verification is explicit** — Not implicit confidence, but structured VERIFICATION nodes
3. **Dependencies are first-class** — Claims can reference other claims, enabling logical chains
4. **RushDB simplifies graph ops** — Zero-schema API with full traversal support

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RAG Hallucination Prevention Patterns](https://docs.rushdb.com)
- [Property Graph Fundamentals](https://docs.rushdb.com)

## License

MIT — free to use, modify, and distribute.
