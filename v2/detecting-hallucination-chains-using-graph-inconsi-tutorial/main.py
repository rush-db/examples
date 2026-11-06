"""
Main execution script for hallucination detection tutorial.
Demonstrates RushDB's graph-based approach to detecting hallucination chains.
"""

import os
from dotenv import load_dotenv

from rushdb import RushDB
from detector import HallucinationDetector, InconsistencyReport

load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env")

db = RushDB(API_KEY)
detector = HallucinationDetector(db)


def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'#'*70}")
    print(f"  {title}")
    print(f"#{' '*68}#")


def demonstrate_basic_detection():
    """Demonstrate basic hallucination detection on seeded entities."""
    print_header("HALLUCINATION DETECTION - GRAPH INCONSISTENCY SCORING")
    
    print("\nAnalyzing claims for hallucination indicators...\n")
    
    # Analyze each entity we know has data
    entities_to_analyze = [
        "Apple Inc.",
        "Tesla", 
        "Python Programming Language",
        "Moon Landing"
    ]
    
    all_reports = []
    
    for entity_name in entities_to_analyze:
        report = detector.detect_hallucination(entity_name)
        all_reports.append(report)
        
        # Print formatted report
        print(detector.generate_report(report))
    
    return all_reports


def demonstrate_semantic_search():
    """Show how semantic search can find similar claims for comparison."""
    print_header("SEMANTIC SEARCH FOR SIMILAR CLAIMS")
    
    print("\nSearching for claims similar to 'company founding date'...")
    
    # Note: Semantic search requires vector indexes to be set up
    # This demonstrates the pattern even if indexes aren't configured
    try:
        similar_claims = db.ai.search({
            "propertyName": "text",
            "query": "founded year establishment date",
            "labels": ["CLAIM"],
            "limit": 5
        })
        
        if similar_claims.data:
            print(f"\nFound {len(similar_claims.data)} semantically similar claims:")
            for i, claim in enumerate(similar_claims.data, 1):
                print(f"  {i}. {claim.data.get('text', '')[:60]}...")
                print(f"     Entity: {claim.data.get('entity', 'Unknown')}")
                print(f"     Factual: {claim.data.get('factual', 'Unknown')}")
        else:
            print("\nNo similar claims found (vector index may not be configured).")
            print("To enable semantic search, create an index:")
            print("  db.ai.indexes.create({'label': 'CLAIM', 'propertyName': 'text'})")
            
    except Exception as e:
        print(f"\nSemantic search not available: {e}")
        print("This is expected if vector indexes haven't been configured.")


def demonstrate_graph_traversal():
    """Show how to traverse the graph to understand claim relationships."""
    print_header("GRAPH TRAVERSAL - CLAIM RELATIONSHIPS")
    
    # Get a specific claim and explore its relationships
    claims = db.records.find({"labels": ["CLAIM"], "limit": 1})
    
    if claims:
        sample_claim = claims[0]
        print(f"\nSample claim: {sample_claim.data.get('text', '')[:60]}...")
        print(f"Entity: {sample_claim.data.get('entity', 'Unknown')}")
        
        # Find what this claim contradicts
        contradicts = db.records.find({
            "labels": ["CLAIM"],
            "where": {
                "CONTRADICTS_CLAIM": {"$id": sample_claim.id}
            }
        })
        
        if contradicts:
            print(f"\nThis claim contradicts {len(contradicts)} other claim(s):")
            for c in contradicts:
                print(f"  - {c.data.get('text', '')[:60]}...")
        else:
            print("\nThis claim has no contradictions.")
        
        # Find what this claim supports
        supports = db.records.find({
            "labels": ["CLAIM"],
            "where": {
                "SUPPORTS_CLAIM": {"$id": sample_claim.id}
            }
        })
        
        if supports:
            print(f"\nThis claim supports {len(supports)} other claim(s):")
            for s in supports:
                print(f"  - {s.data.get('text', '')[:60]}...")


def summarize_results(reports: list):
    """Print a summary of all detected hallucination risks."""
    print_header("SUMMARY - HALLUCINATION RISK ASSESSMENT")
    
    print("\nEntity Risk Ranking:")
    print("-"*50)
    
    # Sort by inconsistency score descending
    sorted_reports = sorted(reports, key=lambda r: r.inconsistency_score, reverse=True)
    
    for rank, report in enumerate(sorted_reports, 1):
        risk = detector._score_to_risk_level(report.inconsistency_score)
        risk_indicator = {
            "LOW": "✓",
            "MEDIUM": "⚠", 
            "HIGH": "⚡",
            "CRITICAL": "☠"
        }.get(risk, "?")
        
        print(f"  {rank}. {report.entity_name}")
        print(f"     Score: {report.inconsistency_score:.2f} | Risk: {risk} {risk_indicator}")
        print(f"     Claims: {report.total_claims} | Contradictions: {report.contradiction_count}")
        
        if report.hallucination_chains:
            print(f"     Hallucination chains: {len(report.hallucination_chains)}")
        print()


def show_example_workflow():
    """Demonstrate the complete workflow for hallucination detection."""
    print_header("EXAMPLE WORKFLOW - DETECTING HALLUCINATION IN NEW TEXT")
    
    print("""
    When you receive new LLM-generated content, follow this workflow:
    
    1. EXTRACT CLAIMS
       Parse the text and create CLAIM records for each statement.
       
    2. LINK TO ENTITIES  
       Attach claims to existing ENTITY records or create new ones.
       
    3. COMPARE SIMILAR CLAIMS
       Use semantic search to find existing claims about the same topic.
       
    4. IDENTIFY CONTRADICTIONS
       Check for CONTRADICTS relationships between new and existing claims.
       
    5. CALCULATE INCONSISTENCY
       Score the entity based on contradiction/support ratio.
       
    6. FLAG HALLUCINATION CHAINS
       Report any paths of contradictory claims.
    """)
    
    # Show example: check if a new claim contradicts existing data
    print("\nExample: Checking a new claim against existing knowledge")
    print("-"*50)
    
    new_claim_text = "Apple Inc. was founded in 1984"
    
    # Find existing claims about Apple
    existing_claims = detector.get_entity_claims("Apple Inc.")
    
    print(f"\nNew claim: \"{new_claim_text}\"")
    print(f"Existing claims about Apple: {len(existing_claims)}")
    
    # Check for contradictions in the graph
    has_contradiction = False
    for claim in existing_claims:
        contradicts = db.records.find({
            "labels": ["CLAIM"],
            "where": {
                "CONTRADICTS_CLAIM": {"$id": claim.id}
            }
        })
        
        for other in contradicts:
            if other.data.get("text"):
                print(f"\n  CONFLICT DETECTED!")
                print(f"  Existing: \"{claim.data.get('text', '')[:50]}...\")")
                print(f"  New claim contradicts this!")
                has_contradiction = True
                break
        
        if has_contradiction:
            break
    
    if not has_contradiction:
        print("\n  No direct contradictions found in the graph.")
        print("  However, manual verification is still recommended.")


def main():
    """Run the complete hallucination detection demonstration."""
    
    print("\n" + "="*70)
    print("  RUSHDB HALLUCINATION DETECTION TUTORIAL")
    print("  Detecting hallucination chains using graph inconsistency scoring")
    print("="*70)
    
    # Run demonstrations
    reports = demonstrate_basic_detection()
    summarize_results(reports)
    demonstrate_semantic_search()
    demonstrate_graph_traversal()
    show_example_workflow()
    
    print("\n" + "="*70)
    print("  Tutorial complete! View README.md for next steps.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
