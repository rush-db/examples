#!/usr/bin/env python3
"""
Cross-Modal Linking Demonstration

This script demonstrates how RushDB's graph structure solves cross-modal retrieval
in document pipelines where naive chunking destroys structural relationships.

Query: "Show me data supporting the revenue claims in Q3"

Expected behavior:
1. Vector search finds text chunks discussing "Q3 revenue claims"
2. Graph traversal follows DISCUSSES edges to linked tables
3. Structured query pulls specific Q3 rows from those tables
4. Cross-reference finds REPLACES edge → chart that visualizes this table
5. Returns: Text quote + table data + chart reference + document context

Run: python main.py
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

from rushdb import RushDB

db = RushDB(API_KEY)


def find_text_chunks_discussing(query: str, limit: int = 3):
    """
    Step 1: Find text chunks that discuss the query topic.
    
    Uses vector similarity search on TEXT_CHUNK.content.
    Returns chunks with their DISCUSSES relationships for next step.
    """
    print(f"\n[STEP 1] Searching for text chunks discussing: \"{query}\"")
    print("-" * 60)
    
    results = db.ai.search({
        "propertyName": "content",
        "query": query,
        "labels": ["TEXT_CHUNK"],
        "limit": limit
    })
    
    chunks = []
    for i, chunk in enumerate(results.data):
        print(f"\n  [{i+1}] Score: {chunk.score:.3f}")
        print(f"      Text: \"{chunk['content'][:100]}...\"")
        print(f"      Role: {chunk['role']}")
        chunks.append(chunk)
    
    return chunks


def find_tables_discussed_by(chunks: list):
    """
    Step 2: For each text chunk, find tables it DISCUSSES.
    
    This is the key difference from naive RAG:
    - Naive RAG: embed tables as text, lose structure
    - Graph approach: explicit edge = strong provenance
    """
    print(f"\n[STEP 2] Finding tables linked via DISCUSSES relationships")
    print("-" * 60)
    
    tables = []
    for chunk in chunks:
        # Find tables that this chunk discusses
        table_results = db.records.find({
            "labels": ["TABLE"],
            "where": {
                "TEXT_CHUNK": {
                    "$relation": {"type": "DISCUSSES", "direction": "in"},
                    "$id": {"$in": [chunk.id]}
                }
            },
            "limit": 5
        })
        
        if table_results.data:
            for table in table_results.data:
                print(f"\n  ✓ Chunk discusses: {table['name']}")
                print(f"    Description: {table['description']}")
                print(f"    Columns: {table['columns']}")
                tables.append(table)
        else:
            print(f"\n  ○ Chunk has no DISCUSSES links (unverified claim)")
    
    return tables


def query_table_rows(table, filter_fn=None):
    """
    Step 3: Query table rows with structured data.
    
    Unlike naive RAG which returns the whole table as text,
    we can do structured queries: "show me rows where Revenue > 2M"
    """
    print(f"\n[STEP 3] Querying table rows from: {table['name']}")
    print("-" * 60)
    
    # Get all rows for this table
    rows = db.records.find({
        "labels": ["TABLE_ROW"],
        "where": {
            "TABLE": {
                "$relation": {"type": "HAS_ROW", "direction": "in"},
                "$id": {"$in": [table.id]}
            }
        }
    })
    
    print(f"\n  Found {rows.total} rows:")
    print(f"  {table['columns']}")
    
    for row in rows.data:
        row_data = row.get("rowData", {})
        if row_data:
            values = [str(row_data.get(col, "")) for col in table['columns']]
            print(f"  {values}")
    
    return rows.data


def find_figures_referencing_tables(tables: list):
    """
    Step 4: Find figures that VISUALIZE or REPLACE these tables.
    
    This answers: "What chart shows this table's data?"
    """
    print(f"\n[STEP 4] Finding figures that visualize/replace tables")
    print("-" * 60)
    
    figures = []
    for table in tables:
        # Find figures that VISUALIZE this table
        visualize_results = db.records.find({
            "labels": ["FIGURE"],
            "where": {
                "TABLE": {
                    "$relation": {"type": "VISUALIZES", "direction": "in"},
                    "$id": {"$in": [table.id]}
                }
            }
        })
        
        # Find figures that REPLACE this table
        replace_results = db.records.find({
            "labels": ["FIGURE"],
            "where": {
                "TABLE": {
                    "$relation": {"type": "REPLACES", "direction": "in"},
                    "$id": {"$in": [table.id]}
                }
            }
        })
        
        for figure in visualize_results.data:
            print(f"\n  ✓ FIGURE {figure['figureNumber']}: {figure['title']}")
            print(f"    Type: {figure['type']}")
            print(f"    Relationship: VISUALIZES {table['name']}")
            figures.append(figure)
        
        for figure in replace_results.data:
            if figure not in figures:
                print(f"\n  ✓ FIGURE {figure['figureNumber']}: {figure['title']}")
                print(f"    Type: {figure['type']}")
                print(f"    Relationship: REPLACES {table['name']}")
                print(f"    Note: {figure.get('note', '')[:60]}...")
                figures.append(figure)
    
    return figures


def get_document_context(chunks: list):
    """
    Step 5: Get document context for the found chunks.
    
    Follow CONTAINS relationship: Chunk → Section → Document
    """
    print(f"\n[STEP 5] Building document context")
    print("-" * 60)
    
    for chunk in chunks:
        # Find section that contains this chunk
        section_results = db.records.find({
            "labels": ["SECTION"],
            "where": {
                "TEXT_CHUNK": {
                    "$relation": {"type": "CONTAINS", "direction": "in"},
                    "$id": {"$in": [chunk.id]}
                }
            }
        })
        
        if section_results.data:
            section = section_results.data[0]
            print(f"\n  Chunk belongs to Section: \"{section['title']}\"")
            print(f"    Order: {section['order']}")
            
            # Find document that contains this section
            doc_results = db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "SECTION": {
                        "$relation": {"type": "CONTAINS", "direction": "in"},
                        "$id": {"$in": [section.id]}
                    }
                }
            })
            
            if doc_results.data:
                doc = doc_results.data[0]
                print(f"  Part of Document: \"{doc['title']}\"")
                print(f"    Version: {doc['version']}, Period: {doc['period']}")


def assemble_answer(chunks: list, tables: list, figures: list):
    """
    Step 6: Assemble the complete answer with full provenance.
    
    This demonstrates the advantage over naive RAG:
    - We have explicit links: claim → table → chart
    - We have structured data, not embedded blobs
    - We have document context
    """
    print(f"\n{'='*60}")
    print("ASSEMBLED ANSWER")
    print(f"{'='*60}")
    
    print(f"""
Query: "Show me data supporting the revenue claims in Q3"

ANSWER ASSEMBLY:
─────────────────────────────────────────────────────────────────────

1. SOURCE CLAIMS:
   Found {len(chunks)} text chunk(s) discussing Q3 revenue:
""")
    
    for i, chunk in enumerate(chunks):
        print(f'   [{i+1}] "{chunk["content"]}"')
    
    print(f"""
2. SUPPORTING DATA:
   Found {len(tables)} table(s) providing evidence:
""")
    
    for table in tables:
        print(f"   • {table['name']}: {table['description']}")
        print(f"     Columns: {', '.join(table['columns'])}")
    
    print(f"""
3. VISUALIZATIONS:
   Found {len(figures)} figure(s) that present this data:
""")
    
    for figure in figures:
        print(f"   • Figure {figure['figureNumber']}: {figure['title']} ({figure['type']})")
        print(f"     Caption: {figure.get('note', 'N/A')}")
    
    print(f"""
4. DOCUMENT CONTEXT:
   Claims originate from: Q3 2024 Quarterly Report (revised version)
   All links verified through graph traversal.

─────────────────────────────────────────────────────────────────────

KEY INSIGHT: The graph structure gives us:
  ✓ Provenance: claim → table → chart (explicit edges)
  ✓ Structure: tables queried, not embedded as text blobs
  ✓ Completeness: we return the CHART that REPLACES the table
  ✓ Context: we know the document, section, and relationship types
""")


def main():
    print("=" * 60)
    print("CROSS-MODAL LINKING DEMONSTRATION")
    print("Query: \"Show me data supporting the revenue claims in Q3\"")
    print("=" * 60)
    
    # Check for data
    existing = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if existing.total == 0:
        print("\n❌ No data found. Run `python seed.py` first!")
        return
    
    # Step 1: Find relevant text chunks
    chunks = find_text_chunks_discussing(
        query="revenue Q3 claims data supporting evidence",
        limit=3
    )
    
    if not chunks:
        print("\n❌ No relevant chunks found.")
        return
    
    # Step 2: Find tables discussed by those chunks
    tables = find_tables_discussed_by(chunks)
    
    # Step 3: Query table rows (structured data, not embedded blobs)
    all_rows = []
    for table in tables:
        rows = query_table_rows(table)
        all_rows.extend(rows)
    
    # Step 4: Find figures that visualize/replace the tables
    figures = find_figures_referencing_tables(tables)
    
    # Step 5: Get document context
    get_document_context(chunks)
    
    # Step 6: Assemble complete answer
    assemble_answer(chunks, tables, figures)
    
    # Bonus: Demonstrate graph traversal query that naive RAG can't do
    print(f"\n{'='*60}")
    print("BONUS: GRAPH-ONLY QUERIES (not possible in naive RAG)")
    print(f"{'='*60}")
    
    print("""
Query: "Show me charts that replaced tables in the revised document"
""")
    
    # Find all REPLACES relationships
    replace_figures = db.records.find({
        "labels": ["FIGURE"],
        "where": {
            "TABLE": {
                "$relation": {"type": "REPLACES", "direction": "in"}
            }
        }
    })
    
    print(f"Found {replace_figures.total} figures with REPLACES relationships:")
    for fig in replace_figures.data:
        print(f"  • Figure {fig['figureNumber']}: {fig['title']}")
        print(f"    Note: {fig.get('note', 'N/A')}")
    
    print("""
Query: "Show me unverified claims (text chunks with no DISCUSSES link)"
""")
    
    # Find chunks without DISCUSSES links
    all_chunks = db.records.find({"labels": ["TEXT_CHUNK"], "limit": 100})
    unverified = []
    
    for chunk in all_chunks.data:
        linked_tables = db.records.find({
            "labels": ["TABLE"],
            "where": {
                "TEXT_CHUNK": {
                    "$relation": {"type": "DISCUSSES", "direction": "in"},
                    "$id": {"$in": [chunk.id]}
                }
            }
        })
        if linked_tables.total == 0:
            unverified.append(chunk)
    
    print(f"Found {len(unverified)} unverified claims (no supporting table):")
    for chunk in unverified:
        print(f"  • \"{chunk['content'][:80]}...\"")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("""
The graph structure enables:
1. Cross-modal retrieval: text → table → figure traversal
2. Relationship-aware search: DISCUSSES, REFERENCES, REPLACES, VISUALIZES
3. Structured queries on tables (not just semantic search)
4. Provenance tracking: claim → evidence → visualization
5. Verification: find unverified claims (chunks without evidence links)

This is fundamentally different from naive chunking where:
- Tables embedded as text lose structure
- Images reduced to captions lose context
- No way to link claims to evidence
- No way to return "the chart that replaced this table"
""")


if __name__ == "__main__":
    main()
