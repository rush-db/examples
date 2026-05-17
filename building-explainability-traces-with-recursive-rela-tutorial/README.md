# Building Explainability Traces with Recursive Relationship Traversal

## Overview

This project demonstrates how to use RushDB to build and traverse explainability traces — the hierarchical reasoning chains that explain AI/ML model decisions. It showcases how recursive relationship traversal can reconstruct decision paths, validate reasoning integrity, and provide audit trails for model predictions.

## What It Demonstrates

- **Hierarchical decision structures**: Modeling AI decisions as nested reasoning graphs
- **Recursive relationship traversal**: Navigating parent→child reasoning chains to any depth
- **Evidence linking**: Connecting decisions to supporting data points and intermediate results
- **Path reconstruction**: Rebuilding complete explainability chains from raw graph queries
- **Audit trail generation**: Creating human-readable explanations from graph traversal

## Prerequisites

- Python 3.10+
- A RushDB account ([sign up free](https://rushdb.com))
- RushDB API key

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Seed the database** (creates sample explainability traces):
   ```bash
   python seed.py
   ```
   This generates 15 AI decisions with nested reasoning chains, evidence links, and intermediate results. Safe to run multiple times.

4. **Run the demo**:
   ```bash
   python main.py
   ```

## Expected Output

The demo will:
1. Print the current ontology (labels and properties)
2. Query all AI decisions with their structure
3. Select a specific decision and traverse its full explainability trace
4. Reconstruct the complete reasoning chain with depth indicators
5. Generate a formatted audit trail showing the decision rationale

Sample output:
```
=== AI DECISION: credit-approval-001 ===
Depth 0 │ DECISION (confidence: 0.87)
         │ Reason: Loan application approved
         │
Depth 1 ├─ REASONING_STEP: Income verification
         │   → Evidence: payslip-verified, employment-confirmed
         │
         ├─ REASONING_STEP: Risk assessment
         │   → Evidence: credit-score-high, debt-ratio-low
         │
Depth 2 │   └─ SUB_STEP: Historical pattern analysis
             │       → Evidence: 36-month-stable-income
             │
...

=== AUDIT TRAIL ===
1. INCOME VERIFICATION (Confidence: 0.95)
   Supporting data: payslip-verified, employment-confirmed
   
2. RISK ASSESSMENT (Confidence: 0.82)
   Supporting data: credit-score-high, debt-ratio-low
   
...
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generates sample explainability traces
└── main.py             # Main demo - recursive traversal & trace reconstruction
```

## Data Model

The project uses these RushDB labels:

| Label | Description | Properties |
|-------|-------------|------------|
| `AI_DECISION` | Root node for a model decision | `decisionId`, `model`, `outcome`, `confidence`, `timestamp` |
| `REASONING_STEP` | Individual step in the reasoning chain | `stepId`, `description`, `confidence`, `depth` |
| `EVIDENCE` | Supporting data for a reasoning step | `evidenceId`, `type`, `value`, `source` |
| `INTERMEDIATE_RESULT` | Intermediate computation result | `resultId`, `metric`, `value`, `thresholds` |

**Relationships**:
- `AI_DECISION` → `REASONING_STEP` via `HAS_REASONING_STEP`
- `REASONING_STEP` → `REASONING_STEP` via `LEADS_TO` (recursive)
- `REASONING_STEP` → `EVIDENCE` via `SUPPORTS`
- `REASONING_STEP` → `INTERMEDIATE_RESULT` via `GENERATED`

## Key Concepts

### Recursive Traversal

The core technique uses RushDB's graph traversal to navigate nested `LEADS_TO` relationships. Each `REASONING_STEP` can point to child steps, creating arbitrarily deep reasoning chains. The traversal reconstructs these chains by following relationships and collecting nodes at each depth level.

### Explainability Trace Reconstruction

By traversing the graph and collecting:
- The initial decision and its confidence
- All reasoning steps with their individual confidences
- Evidence attached to each step
- Intermediate results that influenced step outcomes

...we can rebuild a complete, human-readable explanation of any AI decision.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Modeling](https://docs.rushdb.com/concepts/property-graph)
- [Relationship Traversal](https://docs.rushdb.com/api/records#find)

## License

MIT