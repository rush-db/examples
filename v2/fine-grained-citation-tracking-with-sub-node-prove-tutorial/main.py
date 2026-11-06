"""
Fine-Grained Citation Tracking with Sub-Node Provenance
======================================================

This demo shows how RushDB's graph-based architecture enables fine-grained 
provenance tracking at the field level — solving the common pain where 
traditional databases lose lineage information when data is aggregated or 
transformed.

Key concepts demonstrated:
1. Modeling provenance as first-class graph relationships
2. Creating sub-node records for individual field-level citations
3. Linking derived nodes to provenance sub-nodes
4. Query patterns to reconstruct the provenance chain
"""

import os
import sys
from datetime import datetime
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


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_step(step_num: int, description: str):
    """Print a step header."""
    print(f"\n{step_num}. {description}...")


# =============================================================================
# STEP 1: CREATE SOURCE RECORDS
# =============================================================================

def create_source_records():
    """
    Create source research documents that will be cited.
    
    These represent the original data sources (papers, datasets, reports)
    that form the leaves of our provenance graph.
    """
    print_step(1, "Creating source records")
    
    sources = [
        {
            "title": "Global Economic Survey 2024",
            "type": "survey",
            "publisher": "World Economic Forum",
            "published_date": "2024-01-15",
            "url": "https://example.com/surveys/global-2024",
            "access_date": "2024-03-10T08:00:00Z",
            "license": "CC BY 4.0"
        },
        {
            "title": "Tech Industry Report Q3 2024",
            "type": "industry_report",
            "publisher": "TechAnalytics Corp",
            "published_date": "2024-10-01",
            "url": "https://example.com/reports/tech-q3",
            "access_date": "2024-11-05T14:30:00Z",
            "license": "Proprietary"
        },
        {
            "title": "Regional Market Analysis: APAC 2024",
            "type": "market_research",
            "publisher": "Asia Pacific Research Institute",
            "published_date": "2024-06-20",
            "url": "https://example.com/analysis/regional",
            "access_date": "2024-08-15T09:45:00Z",
            "license": "CC BY-NC 3.0"
        }
    ]
    
    created_sources = []
    for source_data in sources:
        # upsert ensures idempotency - safe to run multiple times
        record = db.records.upsert(
            label="SOURCE",
            data=source_data,
            options={"mergeBy": ["url"]}
        )
        created_sources.append(record)
        print(f"   ✓ Created SOURCE: \"{source_data['title']}\"")
    
    return created_sources


# =============================================================================
# STEP 2: CREATE DERIVED AGGREGATION WITH CITATION SUB-NODES
# =============================================================================

def create_aggregation_with_citations(sources):
    """
    Create a derived aggregation and its citation sub-nodes.
    
    This demonstrates the core pattern:
    - AGGREGATION (derived) → CITES → CITATION (sub-node)
    - CITATION (sub-node) → CITES_FROM → SOURCE (original)
    
    Each CITATION sub-node is a first-class record that tracks:
    - Which field in the aggregation it refers to
    - Which source field it came from
    - Confidence level
    - Access timestamp
    - Optional notes
    """
    print_step(2, "Creating derived aggregation with field-level citations")
    
    # Create the aggregation record
    aggregation_data = {
        "title": "Annual Market Report 2024",
        "created_by": "data_science_team",
        "created_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "description": "Aggregated market metrics from multiple sources",
        # These are derived values that need provenance tracking
        "derived_fields": {
            "total_revenue": 95000000,
            "tech_market_share": 28.5,
            "apac_growth_rate": 4.8
        }
    }
    
    aggregation = db.records.upsert(
        label="AGGREGATION",
        data=aggregation_data,
        options={"mergeBy": ["title", "version"]}
    )
    print(f"   ✓ Created AGGREGATION: \"{aggregation_data['title']}\"")
    
    # Create citation sub-nodes for each derived field
    # Each citation tracks: field, source, confidence, timestamp
    citation_configs = [
        {
            "field_name": "total_revenue",
            "source_field_path": "metrics.total_revenue_global",
            "source_title": "Global Economic Survey 2024",
            "source_url": "https://example.com/surveys/global-2024",
            "confidence": 0.95,
            "accessed_at": "2024-03-15T10:30:00Z",
            "notes": "Primary global revenue figure"
        },
        {
            "field_name": "tech_market_share",
            "source_field_path": "metrics.sector_breakdown.technology",
            "source_title": "Tech Industry Report Q3 2024",
            "source_url": "https://example.com/reports/tech-q3",
            "confidence": 0.88,
            "accessed_at": "2024-11-05T14:30:00Z",
            "notes": "Technology sector share from Q3 report"
        },
        {
            "field_name": "apac_growth_rate",
            "source_field_path": "metrics.growth_rate_avg",
            "source_title": "Regional Market Analysis: APAC 2024",
            "source_url": "https://example.com/analysis/regional",
            "confidence": 0.82,
            "accessed_at": "2024-08-15T09:45:00Z",
            "notes": "Average growth rate across APAC economies"
        }
    ]
    
    print("   ✓ Created CITATION sub-nodes:")
    citations = []
    
    for config in citation_configs:
        # Create the citation as a first-class record
        citation = db.records.create(
            label="CITATION",
            data={
                "field_name": config["field_name"],
                "source_field_path": config["source_field_path"],
                "confidence": config["confidence"],
                "accessed_at": config["accessed_at"],
                "source_url": config["source_url"],
                "notes": config["notes"],
                "provenance_type": "field_level"
            }
        )
        citations.append((citation, config))
        print(f"     - CITATION: {config['field_name']} → {config['source_title']} (confidence: {config['confidence']})")
    
    # Now link everything using relationships
    # This creates the complete provenance graph
    with db.transactions.begin() as tx:
        for citation, config in citations:
            # Find the corresponding source record
            source = next(
                (s for s in sources if s.data.get("title") == config["source_title"]),
                None
            )
            if source:
                # Aggregation CITES Citation (aggregation is the derived data)
                db.records.attach(
                    source=aggregation,
                    target=citation,
                    options={"type": "CITES"},
                    transaction=tx
                )
                # Citation CITES_FROM Source (citation points back to original)
                db.records.attach(
                    source=citation,
                    target=source,
                    options={"type": "CITES_FROM"},
                    transaction=tx
                )
    
    print(f"   ✓ Established provenance relationships")
    return aggregation, citations



# =============================================================================
# STEP 3: QUERY PROVENANCE CHAIN FOR A SPECIFIC FIELD
# =============================================================================


def query_field_provenance(aggregation, field_name: str):
    """
    Reconstruct the provenance chain for a specific derived field.
    
    This query:
    1. Finds the citation sub-node for the specified field
    2. Follows the CITES_FROM relationship to the source
    3. Returns complete provenance information
    
    Query pattern:
    AGGREGATION --CITES--> CITATION --CITES_FROM--> SOURCE
    """
    print_step(3, f"Querying provenance chain for field: {field_name}")
    
    # Find the citation for this specific field
    citation_record = db.records.find({
        "labels": ["CITATION"],
        "where": {
            "field_name": field_name,
            "provenance_type": "field_level"
        }
    })
    
    if not citation_record.data:
        print(f"   ⚠ No citation found for field: {field_name}")
        return None
    
    citation = citation_record.data[0]
    
    # Get the source that this citation points to
    source_records = db.records.find({
        "labels": ["SOURCE"],
        "where": {
            "CITES_FROM": {
                "$relation": {"type": "CITES_FROM", "direction": "in"}}
        }
    })
    
    # Filter to find the source directly connected to our citation
    source = None
    for s in source_records.data:
        # Check if this source is connected to our citation
        connected = db.records.find({
            "labels": ["SOURCE"],
            "where": {
                "CITES_FROM": {
                    "$relation": {"type": "CITES_FROM", "direction": "in"}},
                "__id": s.id
            }
        })
        # Get all citations for the aggregation
        aggregation_citations = db.records.find({
            "labels": ["CITATION"],
            "where": {
                "AGGREGATION": {
                    "$relation": {"type": "CITES", "direction": "in"}},
                "field_name": field_name
            }
        })
        if aggregation_citations.data:
            source = s
            break
    
    print(f"\n   📊 Field: {field_name}")
    print(f"   ├─ Source: {citation.data.get('source_field_path', 'unknown').split('.')[0]}")
    print(f"   ├─ Confidence: {citation.data.get('confidence', 'N/A')}")
    print(f"   ├─ Source URL: {citation.data.get('source_url', 'N/A')}")
    print(f"   └─ Accessed: {citation.data.get('accessed_at', 'N/A')}")
    
    return citation


# =============================================================================
# STEP 4: FULL PROVENANCE TRAVERSAL
# =============================================================================


def full_provenance_traversal(aggregation):
    """
    Reconstruct the complete provenance chain for an aggregation.
    
    This demonstrates traversing the full graph:
    - For each CITATION attached to the aggregation
    - Follow the CITES_FROM relationship to find the source
    - Display the complete lineage for each field
    
    This is the key pattern for audit trails and compliance reporting.
    """
    print_step(4, "Full provenance traversal (all fields)")
    
    # Find all citations for this aggregation
    all_citations = db.records.find({
        "labels": ["CITATION"],
        "where": {
            "AGGREGATION": {
                "$relation": {"type": "CITES", "direction": "in"}}
            }
        }
    })
    
    print(f"\n   📋 AGGREGATION: {aggregation.data.get('title', 'Unknown')}")
    print(f"   │")
    
    # For each citation, trace back to its source
    for citation in all_citations.data:
        field_name = citation.data.get("field_name", "unknown")
        confidence = citation.data.get("confidence", "N/A")
        source_url = citation.data.get("source_url", "N/A")
        
        # Find the source this citation points to
        sources = db.records.find({
            "labels": ["SOURCE"],
            "where": {
                "CITES_FROM": {
                    "$relation": {"type": "CITES_FROM", "direction": "in"}},
                    "CITATION": {
                        "$relation": {"type": "CITES_FROM", "direction": "out"}}
                }
            }
        })
        
        source_title = "Unknown Source"
        for src in sources.data:
            if src.data.get("title"):
                source_title = src.data["title"]
                break
        
        print(f"   ├─ [{field_name}] ──CITES──► {source_title}")
        print(f"   │                 confidence: {confidence}")
        print(f"   │                 source_url: {source_url}")
    
    print(f"   │")
    print(f"   ✓ Complete provenance chain reconstructed!")
    
    return all_citations.data


# =============================================================================
# STEP 5: QUERY ALL DATA WITH PROVENANCE
# =============================================================================

def query_all_data_with_provenance():
    """
    Query all aggregations and their full provenance chains.
    
    This demonstrates the audit trail pattern:
    1. Find all derived records (AGGREGATIONs)
    2. For each, find all attached citations
    3. For each citation, find the original source
    4. Return complete lineage information
    """
    print_step(5, "Querying all data with complete provenance")
    
    # Find all aggregations
    aggregations = db.records.find({
        "labels": ["AGGREGATION"]
    })
    
    if not aggregations.data:
        print("   ⚠ No aggregations found. Run seed.py first!")
        return
    
    print(f"\n   Found {len(aggregations.data)} aggregation(s)\n")
    
    for agg in aggregations.data:
        print(f"   ╔═══ {agg.data.get('title', 'Unknown')} ═══")
        print(f"   ║    Version: {agg.data.get('version', 'N/A')}")
        print(f"   ║    Created: {agg.data.get('created_at', 'N/A')}")
        print(f"   ║    Fields: {list(agg.data.get('derived_fields', {}).keys())}")
        
        # Find citations for this aggregation
        citations = db.records.find({
            "labels": ["CITATION"],
            "where": {
                "AGGREGATION": {
                    "$relation": {"type": "CITES", "direction": "in"}},
                    "__id": {"$in": [c.id for c in db.records.find({"labels": ["CITATION"]}).data]}
                }
            }
        })
        
        print(f"   ║    Citations: {len(citations.data)}")
        for c in citations.data:
            conf = c.data.get('confidence', 'N/A')
            field = c.data.get('field_name', 'N/A')
            print(f"   ║      • {field}: confidence={conf}")
        print(f"   ╚══════════════════════════════════════")


# =============================================================================
# MAIN DEMO
# =============================================================================


def main():
    print("\n" + "╔" + "═"*58 + "╗")
    print("║  FINE-GRAINED CITATION TRACKING DEMO                         ║")
    print("║  RushDB Graph-Based Provenance Architecture                  ║")
    print("╚" + "═"*58 + "╝")
    
    # Step 1: Create source records
    print_header("Step 1: Creating Source Records")
    sources = create_source_records()
    
    if not sources:
        print("\n❌ Failed to create source records.")
        print("   Check your API key and try again.")
        sys.exit(1)
    
    # Step 2: Create derived aggregation with citation sub-nodes
    print_header("Step 2: Creating Derived Aggregation with Citations")
    aggregation, citations = create_aggregation_with_citations(sources)
    
    # Step 3: Query provenance for a specific field
    print_header("Step 3: Querying Provenance Chain")
    query_field_provenance(aggregation, "total_revenue")
    
    # Step 4: Full provenance traversal
    print_header("Step 4: Full Provenance Traversal")
    full_provenance_traversal(aggregation)
    
    # Step 5: Query all data with provenance
    print_header("Step 5: Complete Audit Trail Query")
    query_all_data_with_provenance()
    
    # Summary
    print("\n" + "="*60)
    print("  DEMO COMPLETE")
    print("="*60)
    print("\n✅ Key Takeaways:")
    print("   • Provenance is tracked as first-class graph relationships")
    print("   • Each citation is a sub-node with its own properties")
    print("   • Field-level lineage is preserved, not lost in aggregation")
    print("   • Complete audit trails via graph traversal")
    print("\n📚 Learn more:")
    print("   • Docs: https://docs.rushdb.com")
    print("   • GitHub: https://github.com/rush-db/examples")
    print("\n")


if __name__ == "__main__":
    main()
