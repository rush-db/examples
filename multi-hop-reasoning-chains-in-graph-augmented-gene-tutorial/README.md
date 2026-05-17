# Multi-hop Reasoning Chains in Graph-Augmented Generation

This tutorial demonstrates how to build and traverse multi-hop knowledge graphs using RushDB to augment LLM responses with structured reasoning chains.

## What You'll Learn

- How to model domain knowledge as a property graph with typed relationships
- How to perform multi-hop traversals (2+ hops) for complex query resolution
- How to use graph traversal results to augment LLM prompts with reasoned context
- RushDB patterns for creating, linking, and querying hierarchical data

## The Domain: Biomedical Knowledge Graph

We model a simplified biomedical domain with four entity types:

```
GENE ──codes_for──▶ PROTEIN
                     │
                     │involved_in
                     ▼
                  DISEASE
                     │
                     │treated_by
                     ▼
                  DRUG
```

**Multi-hop reasoning example**: Given a gene, traverse to its proteins, then to associated diseases, then to approved drugs — enabling questions like: "What drugs might be relevant for this gene's associated diseases?"

## Prerequisites

- Python 3.9+
- A RushDB instance (cloud or self-hosted)
- API key from your RushDB workspace

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Tutorial

### Step 1: Seed the Knowledge Graph

This creates ~50 mock gene/protein/disease/drug records with relationships:

```bash
python seed.py
```

Expected output:
```
Seeding knowledge graph...
[1/4] Created 12 GENE records
[2/4] Created 10 PROTEIN records
[3/4] Created 8 DISEASE records
[4/4] Created 6 DRUG records
[5/5] Created 25 relationships (4 types)
Done! Graph contains 36 records and 25 relationships.
```

### Step 2: Run the Multi-hop Reasoning Demo

```bash
python main.py
```

Expected output:
```
=== Multi-hop Reasoning Chains Demo ===

[Chain 1] GENE → PROTEIN → DISEASE (3 hops)
  Query: TP53
  Path: TP53 → p53 → Breast Cancer
  Confidence: 0.95

[Chain 2] GENE → PROTEIN → DISEASE → DRUG (4 hops)
  Query: TP53
  Path: TP53 → p53 → Breast Cancer → Tamoxifen
  Confidence: 0.87
  Reason: "Protein p53 is involved in Breast Cancer, which is treated by Tamoxifen"

[Chain 3] Multi-drug aggregation across diseases
  Query: BRCA1
  Paths: 2 drugs found (Tamoxifen, Ribociclib)
  Reasoning: Combined evidence from 2 disease connections
```

## Project Structure

```
.
├── README.md          # This file
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Data generation script
└── main.py            # Multi-hop reasoning demo
```

## Key RushDB Patterns Used

### 1. Creating Records with Relationships

```sdk
# Create entities and link them in a transaction
with db.transactions.begin() as tx:
    gene = db.records.create(label="GENE", data={"symbol": "TP53"}, transaction=tx)
    protein = db.records.create(label="PROTEIN", data={"name": "p53"}, transaction=tx)
    db.records.attach(source=gene, target=protein, options={"type": "CODES_FOR"}, transaction=tx)
```

### 2. Multi-hop Traversal with Relationship Filtering

```sdk
# Find diseases linked to a gene via its proteins (2 hops via PROTEIN)
diseases = db.records.find({
    "labels": ["DISEASE"],
    "where": {
        "PROTEIN": {  # Filter by related PROTEIN's properties
            "GENE": {"$relation": {"type": "CODES_FOR", "direction": "in"}},
                "symbol": "TP53"
            }
        }
    }
})
```

### 3. Chaining Multiple Relationship Types

```sdk
# Find drugs for diseases associated with a gene's protein
drugs = db.records.find({
    "labels": ["DRUG"],
    "where": {
        "DISEASE": {
            "PROTEIN": {
                "GENE": {"symbol": "TP53"}
            }
        }
    }
})
```

## Embedding Strategy

For graph-augmented generation, we embed:
- **Gene symbols/names** → for semantic gene lookup
- **Relationship reasoning paths** → for context grounding

The `main.py` demonstrates a simplified embedding simulation. In production, integrate with your preferred embedding model (OpenAI, Sentence-Transformers, etc.).

## Cleanup

To remove all seeded data:

```python
from rushdb import RushDB
db = RushDB(os.environ["RUSHDB_API_KEY"])
db.records.delete({"labels": ["GENE", "PROTEIN", "DISEASE", "DRUG"], "where": {}})
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Modeling Best Practices](https://docs.rushdb.com)
- [Graph-Augmented Generation Patterns](https://docs.rushdb.com)

---

View on GitHub: https://github.com/rush-db/examples/tree/main/multi-hop-reasoning-chains-in-graph-augmented-gene-tutorial
