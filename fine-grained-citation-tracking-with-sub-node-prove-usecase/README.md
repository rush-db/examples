# Fine-Grained Citation Tracking with Sub-Node Provenance

This project demonstrates how to build a citation-aware research aggregator where every synthesized insight carries its full provenance graph. It showcases RushDB's combined graph + vector strengths in a concrete scenario: tracking citations at the section level (not just document level), enabling verifiable sourcing for AI-generated outputs.

## What This Solves

Traditional citation tracking operates at the **document level**: Paper A cites Paper B. But when an AI system synthesizes information from multiple sections within a paper, coarse-grained citations are insufficient. You need:

1. **Sub-document provenance** — know exactly which section was cited, not just the paper
2. **Citation context** — why was this section cited? (supporting, contradicting, building upon?)
3. **Lineage tracking** — trace a derived insight back through its full citation chain
4. **Update propagation** — know when upstream changes affect downstream citations

## Architecture

```
PAPER ──CONTAINS──> SECTION (vector-embedded)
  │                    │
  │                    └──CITES──> CITATION (provenance sub-node)
  │                                  │
  │                                  └──> TARGET_SECTION (vector-embedded)
  │
  └───AUTHORED_BY──> AUTHOR

INSIGHT ──SOURCED_FROM──> CITATION
                         │
                         └──> SECTION (section-level attribution)
```

### Node Schema

| Label | Properties | Purpose |
|-------|-----------|---------|
| `PAPER` | `title`, `year`, `doi`, `abstract` | Research document |
| `SECTION` | `title`, `content`, `type` (abstract/method/result/discussion) | Sub-document unit |
| `CITATION` | `context`, `type` (support/contrast/extend), `created_at` | Provenance sub-node |
| `INSIGHT` | `text`, `generated_at` | Derived output needing provenance |
| `AUTHOR` | `name`, `affiliation` | Paper author |

### Key Relationship Types

| From | Relationship | To | Purpose |
|------|-------------|---|---------|
| PAPER | `CONTAINS` | SECTION | Document structure |
| SECTION | `CITES` | CITATION | Creates provenance sub-node |
| CITATION | `TARGETS` | SECTION | Points to cited section |
| INSIGHT | `SOURCED_FROM` | CITATION | Links output to provenance |
| PAPER | `AUTHORED_BY` | AUTHOR | Attribution |

## Prerequisites

- Python 3.9+
- RushDB account and API key ([get one free](https://rushdb.com))

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### 3. Seed the Database

```bash
python seed.py
```

This creates:
- 5 research papers with multiple sections each
- Inter-section citations with provenance sub-nodes
- Sample insights with full citation lineage

### 4. Run the Demo

```bash
python main.py
```

## What the Demo Shows

### 1. Vector Search → Graph Traversal

Find sections related to "neural networks" using semantic search, then traverse the citation graph to get the full lineage:

```sdk
# Find related sections
results = db.ai.search({
    "propertyName": "content",
    "query": "neural networks",
    "labels": ["SECTION"],
    "limit": 5
})

# For each result, traverse citation provenance
for section in results.data:
    citations = db.records.find({
        "labels": ["CITATION"],
        "where": {
            "SECTION": {
                "$relation": {"type": "CITES", "direction": "out"},
                "$id": section.id
            }
        }
    })
```

### 2. Full Lineage Retrieval

From a derived insight, traverse back to original sources:

```sdk
insight = db.records.findOne({
    "labels": ["INSIGHT"],
    "where": {"text": "Transformer architectures excel at..."}
})

# Follow the provenance chain
lineage = db.records.find({
    "labels": ["CITATION"],
    "where": {"INSIGHT": {"$relation": {"type": "SOURCED_FROM", "direction": "in"}, "$id": insight.id}}
})
```

### 3. Re-Citation Workflow

When a source paper is updated, find all downstream citations and trigger re-citation:

```sdk
# Find all citations targeting sections of a paper
citations_to_update = db.records.find({
    "labels": ["CITATION"],
    "where": {
        "SECTION": {
            "$relation": {"type": "TARGETS", "direction": "in"},
            "PAPER": {"$relation": {"type": "CONTAINS", "direction": "out"}},
            "__label": "SECTION"
        }
    }
})
```

### 4. Section-Level Attribution

Link an insight to specific sections (not just papers):

```sdk
# Create insight with section-level provenance
citation = db.records.create({
    "label": "CITATION",
    "data": {
        "context": "supported by empirical results",
        "type": "support"
    }
})
db.records.attach(source=insight, target=citation, options={"type": "SOURCED_FROM"})
db.records.attach(source=citation, target=section, options={"type": "TARGETS"})
```

## Expected Output

```
===============================================
FINE-GRAINED CITATION TRACKING DEMO
===============================================

[1] VECTOR SIMILARITY SEARCH
   Found 3 sections related to 'neural networks':
   - 'Attention Mechanisms in Deep Learning' (score: 0.92)
   - 'Sequence Modeling with RNNs' (score: 0.87)
   - 'Optimization Techniques' (score: 0.81)

[2] CITATION LINEAGE TRAVERSAL
   From 'Attention Mechanisms' section:
   - Cited by: 'Improving Sequence Labeling' (context: 'building upon')
   - Cited by: 'Neural Machine Translation' (context: 'extend')
   - Citation type: support (2), extend (1)

[3] INSIGHT PROVENANCE
   Insight: 'Transformer architectures excel at...'
   Sourced from:
   - Paper: 'Attention Is All You Need'
     Section: 'Model Architecture'
     Context: 'supported by empirical results'

[4] RE-CITATION WORKFLOW
   Found 3 downstream citations affected by upstream update
   Re-citation candidates:
   - 'Improving Sequence Labeling' -> 'Attention Mechanisms in Deep Learning'
   - 'Neural Machine Translation' -> 'Sequence Modeling with RNNs'
   - 'Cross-lingual Transfer' -> 'Attention Mechanisms in Deep Learning'

[5] AGGREGATED ATTRIBUTION REPORT
   Paper: 'Improving Sequence Labeling'
   Direct citations: 3 sections
   Total provenance chain: 7 sections
   Attributed insights: 2
```

## Project Structure

```
fine-grained-citation-tracking/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py            # Generates mock research data
└── main.py            # Demonstrates all key patterns
```

## Key RushDB Patterns Used

1. **Nested JSON import** for creating papers with sections in one call
2. **Inline vector writes** for embedding section content
3. **Provenance sub-nodes** as intermediate citation trackers
4. **Relationship traversal** for lineage queries
5. **Label-based filtering** for provenance chain analysis

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph + Vector Search Pattern](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/fine-grained-citation-tracking-with-sub-node-prove-usecase)

## Cost Note

This demo creates ~50 records with properties and relationships. With RushDB's free tier (100K KU/month), this uses approximately:

- ~50 records × 0.5 KU = 25 KU
- ~150 properties × 1 KU = 150 KU
- ~60 relationships × 0.25 KU = 15 KU
- ~15 vector embeddings × 5 KU = 75 KU

**Total: ~265 KU** — well within free tier limits. Reads are always free.
