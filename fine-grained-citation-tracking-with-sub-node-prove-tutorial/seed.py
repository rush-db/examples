"""
Seed script for the Fine-Grained Citation Tracking demo.

This script creates mock research data representing:
- Source documents (papers, datasets, reports)
- Derived aggregations
- Citation sub-nodes linking fields to sources

The data models a realistic research platform scenario where
data is aggregated from multiple sources with full provenance tracking.

Run this once before main.py to populate the database.
It is idempotent — safe to run multiple times.
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Initialize the RushDB client
api_key = os.environ.get("RUSHDB_API_KEY")
if not api_key:
    print("❌ Error: RUSHDB_API_KEY not found in environment")
    print("   Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)


def seed_sources():
    """Create source research documents."""
    print("\n📚 Seeding source records...")
    
    sources = [
        {
            "title": "Global Economic Survey 2024",
            "type": "survey",
            "publisher": "World Economic Forum",
            "published_date": "2024-01-15",
            "url": "https://example.com/surveys/global-2024",
            "access_date": "2024-03-10T08:00:00Z",
            "license": "CC BY 4.0",
            "metrics": {
                "total_revenue_global": 98000000,
                "sector_breakdown": {
                    "technology": 28.5,
                    "finance": 24.2,
                    "healthcare": 18.1,
                    "other": 29.2
                }
            }
        },
        {
            "title": "Tech Industry Report Q3 2024",
            "type": "industry_report",
            "publisher": "TechAnalytics Corp",
            "published_date": "2024-10-01",
            "url": "https://example.com/reports/tech-q3",
            "access_date": "2024-11-05T14:30:00Z",
            "license": "Proprietary",
            "metrics": {
                "tech_sector_revenue": 4800000,
                "market_share_top5": 67.8,
                "growth_rate_yoy": 12.4
            }
        },
        {
            "title": "Regional Market Analysis: APAC 2024",
            "type": "market_research",
            "publisher": "Asia Pacific Research Institute",
            "published_date": "2024-06-20",
            "url": "https://example.com/analysis/regional",
            "access_date": "2024-08-15T09:45:00Z",
            "license": "CC BY-NC 3.0",
            "metrics": {
                "apac_gdp_share": 36.2,
                "growth_rate_avg": 4.8,
                "digital_adoption": 72.5
            }
        },
        {
            "title": "Healthcare Sector Financials 2023-2024",
            "type": "financial_report",
            "publisher": "HealthEconomics Analytics",
            "published_date": "2024-02-28",
            "url": "https://example.com/reports/healthcare",
            "access_date": "2024-04-01T11:00:00Z",
            "license": "CC BY 4.0",
            "metrics": {
                "total_expenditure": 12400000,
                "r_and_d_spending": 1890000,
                "market_growth": 6.7
            }
        }
    ]
    
    created = []
    for i, source_data in enumerate(sources):
        try:
            record = db.records.upsert(
                label="SOURCE",
                data=source_data,
                options={"mergeBy": ["url"]}
            )
            created.append(record)
            print(f"   ✓ SOURCE [{i+1}/{len(sources)}]: {source_data['title']}")
        except Exception as e:
            print(f"   ⚠ Warning creating source {source_data['title']}: {e}")
    
    return created


def seed_aggregations(sources):
    """Create derived aggregation with citation tracking."""
    print("\n📊 Seeding derived aggregations with citations...")
    
    # Create an aggregation record
    aggregation_data = {
        "title": "Annual Market Report 2024",
        "created_by": "automated_pipeline",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "derived_fields": {
            "total_revenue": 95000000,
            "tech_market_share": 28.5,
            "apac_growth_rate": 4.8,
            "healthcare_expenditure": 12400000
        }
    }
    
    try:
        aggregation = db.records.upsert(
            label="AGGREGATION",
            data=aggregation_data,
            options={"mergeBy": ["title", "version"]}
        )
        print(f"   ✓ AGGREGATION: {aggregation_data['title']}")
    except Exception as e:
        print(f"   ⚠ Warning creating aggregation: {e}")
        return None
    
    # Find the relevant source records
    source_records = db.records.find({
        "labels": ["SOURCE"],
        "orderBy": {"published_date": "asc"}
    })
    
    # Create citation sub-nodes for each derived field
    citations = [
        {
            "derived_label": "AGGREGATION",
            "derived_field": "total_revenue",
            "source_title": "Global Economic Survey 2024",
            "source_field": "total_revenue_global",
            "confidence": 0.95,
            "accessed_at": "2024-03-15T10:30:00Z",
            "notes": "Primary source for global revenue figures"
        },
        {
            "derived_label": "AGGREGATION",
            "derived_field": "tech_market_share",
            "source_title": "Global Economic Survey 2024",
            "source_field": "sector_breakdown.technology",
            "confidence": 0.88,
            "accessed_at": "2024-03-15T10:31:00Z",
            "notes": "Derived from sector breakdown percentages"
        },
        {
            "derived_label": "AGGREGATION",
            "derived_field": "apac_growth_rate",
            "source_title": "Regional Market Analysis: APAC 2024",
            "source_field": "growth_rate_avg",
            "confidence": 0.82,
            "accessed_at": "2024-08-15T09:45:00Z",
            "notes": "Average growth rate across APAC region"
        },
        {
            "derived_label": "AGGREGATION",
            "derived_field": "healthcare_expenditure",
            "source_title": "Healthcare Sector Financials 2023-2024",
            "source_field": "total_expenditure",
            "confidence": 0.91,
            "accessed_at": "2024-04-01T11:00:00Z",
            "notes": "Total sector expenditure including public and private"
        }
    ]
    
    created_citations = []
    for i, citation_data in enumerate(citations):
        try:
            citation = db.records.create(
                label="CITATION",
                data={
                    "field_name": citation_data["derived_field"],
                    "source_field_path": citation_data["source_field"],
                    "confidence": citation_data["confidence"],
                    "accessed_at": citation_data["accessed_at"],
                    "notes": citation_data["notes"],
                    "provenance_type": "field_level"
                }
            )
            created_citations.append((citation, citation_data))
            print(f"   ✓ CITATION [{i+1}/{len(citations)}]: {citation_data['derived_field']} → {citation_data['source_title']}")
        except Exception as e:
            print(f"   ⚠ Warning creating citation: {e}")
    
    # Attach citations to the aggregation
    with db.transactions.begin() as tx:
        for citation, cdata in created_citations:
            # Get the source record for this citation
            source = next((s for s in sources if s.data.get("title") == cdata["source_title"]), None)
            if source:
                # Link citation to aggregation
                db.records.attach(
                    source=aggregation,
                    target=citation,
                    options={"type": "CITES"},
                    transaction=tx
                )
                # Link citation to source
                db.records.attach(
                    source=citation,
                    target=source,
                    options={"type": "CITES_FROM"},
                    transaction=tx
                )
    
    print(f"   ✓ Attached {len(created_citations)} citation relationships")
    return aggregation, created_citations


def cleanup_existing():
    """"Remove existing demo data (idempotent cleanup)."""
    print("\n🧹 Cleaning up any existing demo data...")
    
    # Find and delete existing aggregations
    existing = db.records.find({
        "labels": ["AGGREGATION"],
        "where": {"title": {"$contains": "Annual Market Report"}}
    })
    
    if existing.data:
        for record in existing.data:
            db.records.delete(record_id=record.id)
        print(f"   ✓ Removed {len(existing.data)} existing aggregation(s)")
    
    # Find and delete existing citations
    existing_citations = db.records.find({
        "labels": ["CITATION"],
        "where": {"provenance_type": "field_level"}
    })
    
    if existing_citations.data:
        for record in existing_citations.data:
            db.records.delete(record_id=record.id)
        print(f"   ✓ Removed {len(existing_citations.data)} existing citation(s)")


def main():
    print("="*60)
    print("  SEED SCRIPT: Fine-Grained Citation Tracking Demo")
    print("="*60)
    
    # Clean up first for idempotency
    cleanup_existing()
    
    # Create source records
    sources = seed_sources()
    
    if not sources:
        print("\n❌ Failed to create source records. Check your API key and try again.")
        sys.exit(1)
    
    # Create aggregations with citations
    result = seed_aggregations(sources)
    
    print("\n" + "="*60)
    print("  ✅ SEED COMPLETE")
    print("="*60)
    print("\nRun `python main.py` to see the provenance tracking in action!")


if __name__ == "__main__":
    main()
