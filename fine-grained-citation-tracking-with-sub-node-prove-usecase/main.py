"""
Fine-Grained Citation Tracking with Sub-Node Provenance

Demonstrates RushDB's combined graph + vector strengths for citation tracking:
1. Vector similarity search for finding related sections
2. Graph traversal for citation lineage
3. Re-citation workflow for upstream updates
4. Section-level attribution for insights

Run 'python seed.py' first to populate the database.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)


def demo_vector_search():
    """Demonstrate vector similarity search to find related sections."""
    print("\n" + "=" * 60)
    print("1. VECTOR SIMILARITY SEARCH")
    print("=" * 60)
    
    # Search for sections related to neural networks and attention
    query = "neural networks and attention mechanisms"
    results = db.ai.search({
        "propertyName": "content",
        "query": query,
        "labels": ["SECTION"],
        "limit": 5
    })
    
    if not results.data:
        print("  No results found. Run 'python seed.py' first.")
        return []
    
    print(f"  Query: '{query}'")
    print(f"  Found {len(results.data)} related sections:\n")
    
    for i, section in enumerate(results.data, 1):
        paper = section.get("paper_title", "Unknown")
        score = section.score if hasattr(section, 'score') else section.data.get("__score", 0)
        print(f"  {i}. [{score:.2f}] {section['title']}")
        print(f"     Paper: {paper}")
        print(f"     Type: {section.get('type', 'N/A')}")
        print()
    
    return results.data


def demo_citation_lineage(found_sections):
    """Traverse citation graph to show full lineage."""
    print("\n" + "=" * 60)
    print("2. CITATION LINEAGE TRAVERSAL")
    print("=" * 60)
    
    if not found_sections:
        print("  No sections to analyze. Run vector search first.")
        return
    
    # For each found section, traverse to find:
    # 1. What citations does this section point to? (outgoing)
    # 2. What sections cite this one? (incoming via CITATION)
    
    section = found_sections[0]  # Analyze the top result
    print(f"  Analyzing citations for: '{section['title']}'")
    print()
    
    # Find outgoing citations (what this section cites)
    outgoing = db.records.find({
        "labels": ["CITATION"],
        "where": {
            "SECTION": {
                "$relation": {"type": "CITES", "direction": "out"},
                "$id": section.id
            }
        }
    })
    
    if outgoing.data:
        print(f"  This section CITES {len(outgoing.data)} other sections:")
        for cit in outgoing.data:
            # Find the target section
            targets = db.records.find({
                "labels": ["SECTION"],
                "where": {
                    "CITATION": {
                        "$relation": {"type": "TARGETS", "direction": "in"},
                        "$id": cit.id
                    }
                }
            })
            if targets.data:
                target = targets.data[0]
                print(f"    - '{target['title']}' ({cit['type']}: '{cit['context']}')")
    else:
        print("  This section has no outgoing citations")
    
    print()
    
    # Find incoming citations (what cites this section)
    # This uses a different pattern: find CITATION nodes that TARGET this section
    incoming = db.records.find({
        "labels": ["CITATION"],
        "where": {
            "SECTION": {
                "$relation": {"type": "TARGETS", "direction": "in"},
                "$id": section.id
            }
        }
    })
    
    if incoming.data:
        print(f"  This section is CITED BY {len(incoming.data)} other sections:")
        for cit in incoming.data:
            # Find the citing section
            citers = db.records.find({
                "labels": ["SECTION"],
                "where": {
                    "CITATION": {
                        "$relation": {"type": "CITES", "direction": "out"},
                        "$id": cit.id
                    }
                }
            })
            if citers.data:
                citer = citers.data[0]
                print(f"    - '{citer['title']}' ({cit['type']}: '{cit['context']}')")
    else:
        print("  This section has no incoming citations (it's a source paper)")
    
    # Aggregate citation types
    all_citations = db.records.find({"labels": ["CITATION"], "where": {}})
    type_counts = {}
    for cit in all_citations.data:
        cit_type = cit.get("type", "unknown")
        type_counts[cit_type] = type_counts.get(cit_type, 0) + 1
    
    print(f"\n  All citations in corpus: {all_citations.total}")
    print(f"  Types: {type_counts}")


def demo_insight_provenance():
    """Show how insights link back to specific citation provenance."""
    print("\n" + "=" * 60)
    print("3. INSIGHT PROVENANCE")
    print("=" * 60)
    
    insights = db.records.find({
        "labels": ["INSIGHT"],
        "where": {},
        "limit": 3
    })
    
    if not insights.data:
        print("  No insights found. Run 'python seed.py' first.")
        return
    
    print(f"  Found {insights.total} insights with provenance:\n")
    
    for insight in insights.data:
        print(f"  Insight: \"{insight['text'][:80]}...\")")
        
        # Find citations this insight is sourced from
        citations = db.records.find({
            "labels": ["CITATION"],
            "where": {
                "INSIGHT": {
                    "$relation": {"type": "SOURCED_FROM", "direction": "in"},
                    "$id": insight.id
                }
            }
        })
        
        if citations.data:
            for cit in citations.data:
                # Find the target section (specific sub-node citation)
                targets = db.records.find({
                    "labels": ["SECTION"],
                    "where": {
                        "CITATION": {
                            "$relation": {"type": "TARGETS", "direction": "in"},
                            "$id": cit.id
                        }
                    }
                })
                if targets.data:
                    target = targets.data[0]
                    print(f"    Sourced from: '{target['title']}'")
                    print(f"    Paper: {target.get('paper_title', 'Unknown')}")
                    print(f"    Citation type: {cit.get('type', 'N/A')}")
        else:
            print("    No provenance links (may be newly generated)")
        print()


def demo_recitation_workflow():
    """Show re-citation workflow when upstream data changes."""
    print("\n" + "=" * 60)
    print("4. RE-CITATION WORKFLOW")
    print("=" * 60)
    
    # Get all papers
    papers = db.records.find({"labels": ["PAPER"], "where": {}})
    
    if not papers.data:
        print("  No papers found. Run 'python seed.py' first.")
        return
    
    print(f"  Checking re-citation candidates for {papers.total} papers...\n")
    
    for paper in papers.data[:3]:  # Check first 3 papers
        paper_id = paper.id
        paper_title = paper.get("title", "Unknown")
        
        # Find all citations targeting any section of this paper
        citations_to_this_paper = db.records.find({
            "labels": ["CITATION"],
            "where": {
                "SECTION": {
                    "$relation": {"type": "TARGETS", "direction": "in"},
                    "PAPER": {
                        "$relation": {"type": "CONTAINS", "direction": "out"},
                        "$id": paper_id
                    }
                }
            }
        })
        
        if citations_to_this_paper.data:
            print(f"  Paper: '{paper_title}'")
            print(f"    Downstream citations: {len(citations_to_this_paper.data)}")
            
            # Show some citation details
            for cit in citations_to_this_paper.data[:2]:
                # Find the citing section
                citers = db.records.find({
                    "labels": ["SECTION"],
                    "where": {
                        "CITATION": {
                            "$relation": {"type": "CITES", "direction": "out"},
                            "$id": cit.id
                        }
                    }
                })
                if citers.data:
                    citer = citers.data[0]
                    print(f"    - Cited by: '{citer['title']}' (context: {cit.get('context', 'N/A')})")
            print()


def demo_aggregated_attribution():
    """Show aggregated attribution report for a paper."""
    print("\n" + "=" * 60)
    print("5. AGGREGATED ATTRIBUTION REPORT")
    print("=" * 60)
    
    # Pick a paper to analyze
    papers = db.records.find({"labels": ["PAPER"], "where": {}})
    
    if not papers.data:
        print("  No papers found. Run 'python seed.py' first.")
        return
    
    paper = papers.data[0]
    paper_title = paper.get("title", "Unknown")
    
    print(f"  Analyzing: '{paper_title}'\n")
    
    # Count direct citations (citations this paper's sections make)
    direct_citations = db.records.find({
        "labels": ["CITATION"],
        "where": {
            "SECTION": {
                "$relation": {"type": "CITES", "direction": "out"},
                "PAPER": {
                    "$relation": {"type": "CONTAINS", "direction": "out"},
                    "$id": paper.id
                }
            }
        }
    })
    
    # Count incoming citations (citations others make to this paper)
    incoming_citations = db.records.find({
        "labels": ["CITATION"],
        "where": {
            "SECTION": {
                "$relation": {"type": "TARGETS", "direction": "in"},
                "PAPER": {
                    "$relation": {"type": "CONTAINS", "direction": "out"},
                    "$id": paper.id
                }
            }
        }
    })
    
    # Count sections
    sections = db.records.find({
        "labels": ["SECTION"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "$id": paper.id
            }
        }
    })
    
    # Count insights sourced from this paper
    insights = db.records.find({
        "labels": ["INSIGHT"],
        "where": {
            "CITATION": {
                "$relation": {"type": "SOURCED_FROM", "direction": "out"},
                "SECTION": {
                    "$relation": {"type": "TARGETS", "direction": "in"},
                    "PAPER": {
                        "$relation": {"type": "CONTAINS", "direction": "out"},
                        "$id": paper.id
                    }
                }
            }
        }
    })
    
    print(f"  Sections: {sections.total}")
    print(f"  Direct citations made: {direct_citations.total}")
    print(f"  Incoming citations from others: {incoming_citations.total}")
    print(f"  Insights attributed to this paper: {insights.total}")
    
    # Breakdown by citation type
    print(f"\n  Citation type breakdown (incoming):")
    type_counts = {}
    for cit in incoming_citations.data:
        cit_type = cit.get("type", "unknown")
        type_counts[cit_type] = type_counts.get(cit_type, 0) + 1
    for cit_type, count in type_counts.items():
        print(f"    - {cit_type}: {count}")


def main():
    print("=" * 60)
    print("FINE-GRAINED CITATION TRACKING WITH SUB-NODE PROVENANCE")
    print("=" * 60)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all demonstrations
    found_sections = demo_vector_search()
    demo_citation_lineage(found_sections)
    demo_insight_provenance()
    demo_recitation_workflow()
    demo_aggregated_attribution()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("""
Key Takeaways:

1. VECTOR SEARCH + GRAPH: Semantic search finds related sections,
   then graph traversal retrieves full citation lineage.

2. SUB-NODE PROVENANCE: CITATION nodes track metadata about
   why/how something was cited (context, type, date).

3. SECTION-LEVEL ATTRIBUTION: Insights link to specific sections,
   not just papers, enabling verifiable sourcing.

4. RE-CITATION WORKFLOW: When upstream data changes, find all
   downstream citations via graph traversal.

5. AGGREGATED REPORTS: Combine counts across graph relationships
   for attribution reporting.

For more details, see:
- https://docs.rushdb.com
- https://github.com/rush-db/examples/tree/main/fine-grained-citation-tracking-with-sub-node-prove-usecase
""")


if __name__ == "__main__":
    main()
