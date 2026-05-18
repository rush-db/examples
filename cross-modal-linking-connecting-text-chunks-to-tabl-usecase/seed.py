#!/usr/bin/env python3
"""
Seed script for Cross-Modal Linking example.

Generates a realistic Q3 2024 Quarterly Report document with:
- Text sections discussing financial performance
- Tables with structured data (revenue by segment, quarterly results)
- Figures/charts that visualize table data (some figures "replace" tables)
- Explicit graph relationships between modalities

This data demonstrates the difference between:
- Naive RAG: chunk everything, embed everything, lose structure
- Graph+RAG: preserve relationships, query structured data, link visualizations

Run: python seed.py
"""

import os
import random
from typing import List, Dict, Any
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

from rushdb import RushDB

# Initialize RushDB client
db = RushDB(API_KEY)

# Initialize embedding model (all-MiniLM-L6-v2 is fast and good quality)
print("Loading embedding model (all-MiniLM-L6-v2)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
EMBEDDING_DIM = 384


def create_embedding(text: str) -> List[float]:
    """Generate embedding vector for text."""
    return embedder.encode(text, normalize_embeddings=True).tolist()


def seed_if_needed():
    """Check if data already exists, seed if not."""
    existing = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if existing.total > 0:
        print(f"✓ Found {existing.total} existing DOCUMENT(s) — skipping seed")
        print("  (Run `python main.py --clear` first to reset, or delete records manually)")
        return False
    return True


def create_document_structure():
    """
    Create a realistic Q3 2024 Quarterly Report with cross-modal structure.
    
    Document structure:
    - Section 1: Executive Summary
    - Section 2: Financial Highlights (contains TABLE: Quarterly_Results)
    - Section 3: Revenue Analysis (contains TABLE: Revenue_By_Segment)
    - Section 4: Outlook
    
    Relationships:
    - CONTAINS: Document→Section, Section→Content
    - PRECEDES: Section ordering
    - DISCUSSES: Text→Table (evidence linking)
    - REPLACES: Figure→Table (revised docs replace flat tables)
    - REFERENCES: Text→Figure
    - VISUALIZES: Figure→Table
    """
    
    print("\n=== SEEDING CROSS-MODAL DOCUMENT GRAPH ===\n")
    
    # ====================================================================
    # 1. Create the root DOCUMENT
    # ====================================================================
    
    document = db.records.create(
        label="DOCUMENT",
        data={
            "title": "Q3 2024 Quarterly Report",
            "type": "quarterly_report",
            "period": "Q3 2024",
            "version": "revised",
            "publishedAt": "2024-10-15"
        }
    )
    print(f"✓ Created DOCUMENT: {document['title']} (id: {document.id[:16]}...)")
    
    # ====================================================================
    # 2. Create SECTIONS
    # ====================================================================
    
    sections_data = [
        {
            "title": "Executive Summary",
            "order": 1,
            "summary": "Q3 marked our strongest quarter with record revenue and improved margins."
        },
        {
            "title": "Financial Highlights",
            "order": 2,
            "summary": "Total revenue reached $2.4M, representing 23% YoY growth."
        },
        {
            "title": "Revenue Analysis",
            "order": 3,
            "summary": "Enterprise segment drove growth with 34% increase, now comprising 52% of revenue."
        },
        {
            "title": "Outlook",
            "order": 4,
            "summary": "Strong pipeline and seasonal tailwinds position us well for Q4."
        }
    ]
    
    sections = []
    for i, section_data in enumerate(sections_data):
        section = db.records.create(
            label="SECTION",
            data=section_data,
            vectors=[{"propertyName": "summary", "vector": create_embedding(section_data["summary"])}]
        )
        sections.append(section)
        
        # Link: Document CONTAINS Section
        db.records.attach(
            source=document,
            target=section,
            options={"type": "CONTAINS"}
        )
        
        # Link: Section PRECEDES next section (except last)
        if i > 0:
            db.records.attach(
                source=section,
                target=sections[i - 1],
                options={"type": "PRECEDES"}
            )
    
    print(f"✓ Created {len(sections)} SECTIONS with CONTAINS/PRECEDES relationships")
    
    # ====================================================================
    # 3. Create TEXT CHUNKS with claims
    # ====================================================================
    
    text_chunks_data = [
        {
            "sectionIndex": 0,
            "content": "Q3 2024 delivered exceptional results with total revenue of $2.4 million, up 23% year-over-year. This represents our strongest quarterly performance to date.",
            "role": "headline_claim"
        },
        {
            "sectionIndex": 0,
            "content": "Operating margins improved to 31% from 27% in Q3 2023, driven by operating leverage and continued discipline in cost management.",
            "role": "supporting_claim"
        },
        {
            "sectionIndex": 1,
            "content": "Enterprise segment revenue reached $1.25 million, growing 34% year-over-year and now representing 52% of total revenue.",
            "role": "headline_claim"
        },
        {
            "sectionIndex": 1,
            "content": "The SMB segment contributed $720,000 with 12% growth, while Consumer maintained stable performance at $430,000.",
            "role": "supporting_claim"
        },
        {
            "sectionIndex": 2,
            "content": "Geographic expansion contributed meaningfully with APAC growing 45% and EMEA growing 28%.",
            "role": "supporting_claim"
        },
        {
            "sectionIndex": 2,
            "content": "Customer acquisition costs decreased 18% while retention rates improved to 94%, reflecting product-market fit.",
            "role": "supporting_claim"
        },
        {
            "sectionIndex": 3,
            "content": "We enter Q4 with a robust pipeline of $3.8 million and expect continued momentum through the holiday season.",
            "role": "outlook_claim"
        },
        {
            "sectionIndex": 3,
            "content": "Based on current trajectory and seasonal patterns, we are raising full-year guidance to $9.2-9.5 million in revenue.",
            "role": "headline_claim"
        }
    ]
    
    text_chunks = []
    for i, chunk_data in enumerate(text_chunks_data):
        section = sections[chunk_data["sectionIndex"]]
        
        chunk = db.records.create(
            label="TEXT_CHUNK",
            data={
                "content": chunk_data["content"],
                "role": chunk_data["role"],
                "order": i
            },
            vectors=[{"propertyName": "content", "vector": create_embedding(chunk_data["content"])}]
        )
        text_chunks.append(chunk)
        
        # Link: Section CONTAINS Text_Chunk
        db.records.attach(
            source=section,
            target=chunk,
            options={"type": "CONTAINS"}
        )
        
        # Link: Chunk PRECEDES next chunk (within section)
        if i > 0 and text_chunks[i-1].data.get("sectionIndex") == chunk_data["sectionIndex"]:
            db.records.attach(
                source=chunk,
                target=text_chunks[i-1],
                options={"type": "PRECEDES"}
            )
    
    print(f"✓ Created {len(text_chunks)} TEXT_CHUNKs with embeddings")
    
    # ====================================================================
    # 4. Create TABLES (structured, NOT embedded)
    # ====================================================================
    
    # Tables are stored as structured data, NOT embedded as text.
    # This is the key insight: tables are queryable, not embeddable.
    
    quarterly_results = {
        "name": "Quarterly_Results",
        "description": "Revenue and margin by quarter",
        "columns": ["Quarter", "Revenue", "YoY_Growth", "Margin", "Customers", "ARPU"],
        "rows": [
            {"Quarter": "Q1 2024", "Revenue": 1800000, "YoY_Growth": 0.18, "Margin": 0.28, "Customers": 4200, "ARPU": 429},
            {"Quarter": "Q2 2024", "Revenue": 2100000, "YoY_Growth": 0.21, "Margin": 0.29, "Customers": 4600, "ARPU": 457},
            {"Quarter": "Q3 2024", "Revenue": 2400000, "YoY_Growth": 0.23, "Margin": 0.31, "Customers": 5100, "ARPU": 471},
            {"Quarter": "Q4 2024E", "Revenue": 2700000, "YoY_Growth": 0.25, "Margin": 0.32, "Customers": 5600, "ARPU": 482}
        ]
    }
    
    revenue_by_segment = {
        "name": "Revenue_By_Segment",
        "description": "Revenue breakdown by customer segment",
        "columns": ["Segment", "Q3_Revenue", "Q3_Growth", "Q2_Revenue", "YoY_Growth"],
        "rows": [
            {"Segment": "Enterprise", "Q3_Revenue": 1250000, "Q3_Growth": 0.34, "Q2_Revenue": 1080000, "YoY_Growth": 0.38},
            {"Segment": "SMB", "Q3_Revenue": 720000, "Q3_Growth": 0.12, "Q2_Revenue": 680000, "YoY_Growth": 0.14},
            {"Segment": "Consumer", "Q3_Revenue": 430000, "Q3_Growth": 0.03, "Q2_Revenue": 420000, "YoY_Growth": 0.02},
            {"Segment": "Total", "Q3_Revenue": 2400000, "Q3_Growth": 0.23, "Q2_Revenue": 2180000, "YoY_Growth": 0.24}
        ]
    }
    
    tables = []
    for table_data in [quarterly_results, revenue_by_segment]:
        table = db.records.create(
            label="TABLE",
            data={
                "name": table_data["name"],
                "description": table_data["description"],
                "columns": table_data["columns"]
            }
        )
        tables.append(table)
        
        # Create TABLE_ROW records for each row
        # This allows structured queries: "get Q3 rows where Revenue > 2M"
        for row in table_data["rows"]:
            row_record = db.records.create(
                label="TABLE_ROW",
                data={
                    "tableName": table_data["name"],
                    **row
                }
            )
            
            # Link: Table HAS_ROW → Row
            db.records.attach(
                source=table,
                target=row_record,
                options={"type": "HAS_ROW"}
            )
            
            # Embed the row data for semantic search
            row_text = f"{row}"  # e.g., "{'Quarter': 'Q3 2024', 'Revenue': 2400000, ...}"
            row_record = db.records.create(
                label="TABLE_ROW",
                data={
                    "tableName": table_data["name"],
                    "rowData": row,
                    "searchText": f"{table_data['name']}: " + ", ".join([f"{k}={v}" for k, v in row.items()])
                },
                vectors=[{"propertyName": "searchText", "vector": create_embedding(f"{table_data['name']} {' '.join([str(v) for v in row.values()])} ")}]
            )
            db.records.attach(
                source=table,
                target=row_record,
                options={"type": "HAS_ROW"}
            )
    
    print(f"✓ Created {len(tables)} TABLEs with {sum(len(t['columns']) for t in [quarterly_results, revenue_by_segment])} columns total")
    
    # ====================================================================
    # 5. Create FIGURES (charts that visualize tables)
    # ====================================================================
    
    figures_data = [
        {
            "title": "Revenue Trend Chart",
            "figureNumber": 7,
            "caption": "Quarterly revenue showing consistent YoY growth trajectory",
            "type": "line_chart",
            "tableName": "Quarterly_Results",
            "note": "This chart replaces the flat tabular data in the revised investor presentation"
        },
        {
            "title": "Segment Mix Pie Chart",
            "figureNumber": 8,
            "caption": "Revenue distribution by segment: Enterprise now majority at 52%",
            "type": "pie_chart",
            "tableName": "Revenue_By_Segment",
            "note": "Visualization makes segment shift immediately apparent"
        }
    ]
    
    figures = []
    for figure_data in figures_data:
        figure = db.records.create(
            label="FIGURE",
            data={
                "title": figure_data["title"],
                "figureNumber": figure_data["figureNumber"],
                "type": figure_data["type"],
                "note": figure_data["note"]
            },
            vectors=[{"propertyName": "title", "vector": create_embedding(figure_data["title"])}]
        )
        figures.append(figure)
        
        # Create caption record
        caption = db.records.create(
            label="FIGURE_CAPTION",
            data={"text": figure_data["caption"]},
            vectors=[{"propertyName": "text", "vector": create_embedding(figure_data["caption"])}]
        )
        
        # Link: Figure HAS_CAPTION → Caption
        db.records.attach(
            source=figure,
            target=caption,
            options={"type": "HAS_CAPTION"}
        )
        
        # Link: Figure VISUALIZES → Table (key relationship!)
        table = db.records.find({
            "labels": ["TABLE"],
            "where": {"name": figure_data["tableName"]}
        }).data[0]
        
        db.records.attach(
            source=figure,
            target=table,
            options={"type": "VISUALIZES"}
        )
        
        # Link: Figure REPLACES → Table (chart replaces table in revised doc)
        # This is crucial for "show me the new chart that replaced the table" queries
        db.records.attach(
            source=figure,
            target=table,
            options={"type": "REPLACES"}
        )
    
    print(f"✓ Created {len(figures)} FIGUREs with REPLACES/VISUALIZES relationships to tables")
    
    # ====================================================================
    # 6. Link TEXT to TABLES and FIGURES with semantic relationships
    # ====================================================================
    
    # This is where the magic happens:
    # - Text claims that "revenue increased 23%" link to the table with 23% growth
    # - This gives us provenance: claim → evidence
    
    chunk_to_evidence_links = [
        # Chunk: "Q3 revenue of $2.4 million, up 23% year-over-year"
        (0, "Quarterly_Results", "DISCUSSES", "Revenue claims in Q3"),
        # Chunk: "Operating margins improved to 31%"
        (1, "Quarterly_Results", "DISCUSSES", "Margin improvements"),
        # Chunk: "Enterprise segment revenue reached $1.25 million, growing 34%"
        (2, "Revenue_By_Segment", "DISCUSSES", "Enterprise segment growth"),
        # Chunk: "SMB segment contributed $720,000 with 12% growth"
        (3, "Revenue_By_Segment", "DISCUSSES", "SMB segment performance"),
    ]
    
    chunk_to_figure_links = [
        # Chunk 0 "revenue increased 23%" → Figure 7 "Revenue Trend Chart"
        (0, 0, "REFERENCES", "Revenue trend chart supports growth claim"),
        # Chunk 2 "Enterprise 34%" → Figure 8 "Segment Mix Pie Chart"
        (2, 1, "REFERENCES", "Segment mix visualization supports claim"),
    ]
    
    for chunk_idx, table_name, rel_type, justification in chunk_to_evidence_links:
        table = db.records.find({
            "labels": ["TABLE"],
            "where": {"name": table_name}
        }).data[0]
        
        db.records.attach(
            source=text_chunks[chunk_idx],
            target=table,
            options={"type": rel_type}
        )
        
        print(f"  → LINK: Chunk {chunk_idx} --DISCUSSES--> {table_name}")
    
    for chunk_idx, figure_idx, rel_type, justification in chunk_to_figure_links:
        db.records.attach(
            source=text_chunks[chunk_idx],
            target=figures[figure_idx],
            options={"type": rel_type}
        )
        print(f"  → LINK: Chunk {chunk_idx} --REFERENCES--> Figure {figure_idx}")
    
    print(f"\n✓ Created semantic links from text claims to supporting evidence")
    
    # ====================================================================
    # 7. Create vector index for semantic search
    # ====================================================================
    
    # Create index for text chunk content
    try:
        db.ai.indexes.create({
            "label": "TEXT_CHUNK",
            "propertyName": "content",
            "sourceType": "external",
            "dimensions": EMBEDDING_DIM
        })
        print(f"✓ Created vector index for TEXT_CHUNK.content")
    except Exception as e:
        print(f"  (Index may already exist: {str(e)[:50]}...)")
    
    # ====================================================================
    # Summary
    # ====================================================================
    
    print("\n=== SEED COMPLETE ===")
    print(f"Created:")
    print(f"  - 1 DOCUMENT")
    print(f"  - 4 SECTIONS")
    print(f"  - 8 TEXT_CHUNKs with embeddings")
    print(f"  - 2 TABLEs with structured data")
    print(f"  - 8 TABLE_ROWs (queryable, not embedded)")
    print(f"  - 2 FIGUREs (charts)")
    print(f"  - 2 FIGURE_CAPTIONs")
    print(f"\nRelationships:")
    print(f"  - CONTAINS (document→sections, sections→chunks)")
    print(f"  - PRECEDES (section ordering, chunk ordering)")
    print(f"  - DISCUSSES (text→table: claims to evidence)")
    print(f"  - REFERENCES (text→figure: claims to visualizations)")
    print(f"  - VISUALIZES (figure→table: chart shows table data)")
    print(f"  - REPLACES (figure→table: chart replaces table)")
    
    return {
        "document": document,
        "sections": sections,
        "text_chunks": text_chunks,
        "tables": tables,
        "figures": figures
    }


if __name__ == "__main__":
    print("=" * 60)
    print("CROSS-MODAL LINKING SEED SCRIPT")
    print("=" * 60)
    
    if seed_if_needed():
        create_document_structure()
    else:
        print("\nSkipping seed. Data already exists.")
        print("To reset, either:")
        print("  1. Delete records in the RushDB dashboard, or")
        print("  2. Clear via API, then re-run this script")
