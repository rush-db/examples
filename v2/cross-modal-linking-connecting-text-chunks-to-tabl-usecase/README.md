# Cross Modal Linking: Connecting Text Chunks to Tables and Images

## What This Demonstrates

This example shows how a **Graph+Vector architecture** solves cross-modal retrieval in document pipelines where naive chunking destroys structural relationships between text, tables, and images.

## The Problem with Naive RAG

When you chunk a document for RAG:

```
Text chunk 1 → embedding → vector store
Table chunk → embedding → vector store  ❌ Tables aren't meaningful as raw text
Image chunk → embedding → vector store  ❌ Images lose all context
```

Naive approaches:
- Treat tables as text blobs (loses structure)
- Use image captions (loses the data in the table)
- No way to say "this paragraph talks about that table"
- No way to say "this chart replaced that table in the revised doc"

## The Graph Solution

RushDB's property graph lets you model **explicit relationships** between modalities:

```
[Text Chunk] --DISCUSSES--> [Table: Q3 Revenue]
[Text Chunk] --REFERENCES--> [Figure: Revenue Chart]
[Figure] ----REPLACES----> [Table: Q3 Revenue]  (chart replaces flat table)
[Section 3] --CONTAINS--> [Text Chunk]
[Table Row] --AGGREGATES--> [Cell]
```

## Key Insight: Tables Are Queryable, Not Embeddable

Unlike images, tables contain **structured, queryable data**:

| approach | table_as_blob | table_as_graph |
|----------|---------------|----------------|
| Embeddable? | Yes (poorly) | No — query the cells directly |
| Query "Q3 total" | Semantic search | Structured query on rows |
| Join table to text | Metadata string | Explicit edge |
| Show supporting data | Return full blob | Traverse to specific rows |

## End-to-End Scenario

Query: **"Show me data supporting the revenue claims in Q3"**

```
1. Vector search: Find text chunks discussing "Q3 revenue claims"
   ↓
2. Graph traversal: Follow DISCUSSES edges to linked tables
   ↓
3. Structured query: Pull the specific Q3 rows from those tables
   ↓
4. Cross-reference: Find REPLACES edge → chart that visualizes this table
   ↓
5. Return: Text quote + table data + chart reference + original context
```

**Result**: Full provenance from claim → evidence → visualization.

## Project Structure

```
cross-modal-linking/
├── seed.py          # Generate mock quarterly report with text, tables, images
├── main.py          # Demo: create graph, query, traverse relationships
├── requirements.txt # Dependencies
└── .env.example    # Environment variables
```

## Prerequisites

- Python 3.9+
- RushDB account (Free tier works)
- API key from https://app.rushdb.com

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Run

```bash
# Step 1: Seed the database with sample quarterly report data
python seed.py

# Step 2: Run the cross-modal linking demonstration
python main.py
```

## Expected Output

```
=== CROSS-MODAL DOCUMENT GRAPH ===

1. Creating document structure: Q3 2024 Quarterly Report
2. Creating text chunks with semantic embeddings
3. Creating tables with structured rows
4. Creating figure references (charts replacing tables)
5. Linking everything with semantic + spatial relationships

=== QUERY: "revenue claims Q3 data supporting evidence" ===

[Found 2 text chunks discussing Q3 revenue]
  → Chunk 1: "...revenue increased 23% YoY to $2.4M..."
  → Chunk 2: "...Q3 saw our strongest quarter with record margins..."

[Following DISCUSSES relationships → found 1 table]
  → Quarterly_Results: 4 rows × 6 columns
    - Q3: Revenue=$2.4M, Growth=23%, Margin=31%

[Following REPLACES relationships → found visualization]
  → Figure 7: "Revenue Trend Chart" (chart that visualizes Quarterly_Results table)

[Following PRECEDES/CONTAINS → found document context]
  → Section: "Financial Performance"
  → Parent Doc: "Q3 2024 Quarterly Report"

=== ANSWER ASSEMBLY ===
  - Claim source: Section 3.1, paragraph 2
  - Supporting data: Table Quarterly_Results (Q3 row)
  - Visualization: Figure 7 (revenue trend chart)
  - Confidence: High (text→table→chart fully linked)
```

## What Gets Created in RushDB

| Label | Count | Purpose |
|-------|-------|---------|
| DOCUMENT | 1 | Root document record |
| SECTION | 4 | Document sections |
| TEXT_CHUNK | 8 | Paragraph-level text with embeddings |
| TABLE | 2 | Tables (kept as structured data, not embedded) |
| TABLE_ROW | 8 | Rows for querying, not chunking |
| FIGURE | 2 | Charts/figures |
| FIGURE_CAPTION | 2 | Image descriptions |

| Relationship Type | Purpose |
|-------------------|---------|
| CONTAINS | Document → Section, Section → Chunk |
| PRECEDES | Section ordering, Chunk ordering |
| DISCUSSES | Text claims → Supporting tables |
| REPLACES | Revised figures → Original tables |
| REFERENCES | Text → Figures |
| VISUALIZES | Figure → Table |

## GitHub

https://github.com/rush-db/examples/tree/main/cross-modal-linking-connecting-text-chunks-to-tabl-usecase
