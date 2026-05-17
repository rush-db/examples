# Fine-Grained Citation Tracking with Sub-Node Provenance

This project demonstrates how RushDB's graph-based architecture enables fine-grained provenance tracking at the field level — solving the common pain where traditional databases lose lineage information when data is aggregated or transformed.

## The Problem

In traditional databases, when you aggregate data from multiple sources, you lose field-level lineage:

```
┌─────────────────────────────────────────────────────┐
│  TRADITIONAL DB: Flat metadata (loses detail)        │
│                                                      │
│  derived_record = {                                  │
│    "total_revenue": 1500000,                        │
│    "citation": "paper_2024"  ← just a string!      │
│  }                                                   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  RUSHD B: Sub-node provenance (retains everything)  │
│                                                      │
│  DERIVED_RECORD ──CITES──> CITATION_SUB_NODE        │
│                            │                         │
│                            ├── field: "revenue_q1"   │
│                            ├── source: PAPER_2024   │
│                            ├── confidence: 0.95     │
│                            └── accessed_at: "..."   │
└─────────────────────────────────────────────────────┘
```

## What This Demo Shows

1. **Source Records** — Research papers, datasets, and APIs with full metadata
2. **Derived Records** — Aggregations or analyses that combine multiple sources
3. **Citation Sub-Nodes** — First-class records tracking *which field* came from *which source*
4. **Provenance Queries** — Reconstructing the complete lineage chain for any data point

## Architecture Overview

```
┌──────────────┐         CITES          ┌─────────────────────┐
│  PAPER_2024  │◄───────────────────────│  CITATION           │
│  (source)    │                         │  - field: "revenue" │
└──────────────┘                         │  - confidence: 0.9  │
      ▲                                  │  - source_url: "..." │
      │                                  └──────────┬──────────┘
      │                                             │
      │                  DERIVED_FROM               │
      │  ┌──────────────┐◄──────────────────────────┘
      │  │  AGGREGATION │
      │  │  (derived)   │
      │  └──────────────┘
```

## Prerequisites

- Python 3.10+
- A RushDB API key ([get one free](https://app.rushdb.com))

## Setup

```bash
# Clone the examples repo
git clone https://github.com/rush-db/examples.git
cd fine-grained-citation-tracking-with-sub-node-provenance

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Demo

```bash
# First, seed the database with mock research data
python seed.py

# Run the main demonstration
python main.py
```

## Expected Output

```
╔══════════════════════════════════════════════════════════════════╗
║  FINE-GRAINED CITATION TRACKING DEMO                              ║
║  RushDB Graph-Based Provenance Architecture                       ║
╚══════════════════════════════════════════════════════════════════╝

1. Creating source records...
   ✓ Created SOURCE: "Global Economic Survey 2024"
   ✓ Created SOURCE: "Tech Industry Report Q3"
   ✓ Created SOURCE: "Regional Market Analysis"

2. Creating derived aggregation with field-level citations...
   ✓ Created AGGREGATION: "Annual Market Report 2024"
   ✓ Created CITATION sub-nodes:
     - CITATION: revenue → Global Economic Survey (confidence: 0.95)
     - CITATION: market_share → Tech Industry Report Q3 (confidence: 0.88)
     - CITATION: growth_rate → Regional Market Analysis (confidence: 0.82)

3. Querying provenance chain for a specific field...
   📊 Field: revenue
   ├─ Source: Global Economic Survey 2024
   ├─ Confidence: 0.95
   ├─ Source URL: https://example.com/surveys/global-2024
   └─ Accessed: 2024-03-15T10:30:00Z

4. Full provenance traversal (all fields)...
   📋 AGGREGATION: Annual Market Report 2024
   │
   ├─ [revenue] ──CITES──► Global Economic Survey 2024
   │                    confidence: 0.95
   │                    source_url: https://example.com/surveys/global-2024
   │
   ├─ [market_share] ──CITES──► Tech Industry Report Q3
   │                      confidence: 0.88
   │                      source_url: https://example.com/reports/tech-q3
   │
   └─ [growth_rate] ──CITES──► Regional Market Analysis
                       confidence: 0.82
                       source_url: https://example.com/analysis/regional
```

## Key Takeaways

| Traditional DB Approach | RushDB Graph Approach |
|------------------------|----------------------|
| Citation as a string field | Citation as a first-class record |
| Lost when aggregated | Preserved at field level |
| No confidence scores | Full metadata (confidence, URL, timestamp) |
| Manual audit tables | Automatic graph traversal |

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/fine-grained-citation-tracking-with-sub-node-prove-tutorial)
- [RushDB Pricing](https://rushdb.com/pricing) — Reads are always free!
