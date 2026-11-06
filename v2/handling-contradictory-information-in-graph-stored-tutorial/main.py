"""
Handling Contradictory Information in Graph-Stored Knowledge

This tutorial demonstrates how RushDB's property graph model naturally handles
contradictory information in knowledge bases.

Key patterns demonstrated:
1. Modeling contradictions as first-class relationships
2. Querying for contradicting facts
3. Tracing contradictions back to sources
4. Resolving conflicts with evidence weights
5. Using graph traversal for deep analysis
"""

import os
from collections import defaultdict
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
or api_key:
    raise ValueError("RUSHDB_API_KEY environment variable is not set")

db = RushDB(api_key)


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f" {title}")
    print('=' * 70)


def print_subheader(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def get_all_sources():
    """Retrieve all sources from the graph."""
    result = db.records.find({"labels": ["SOURCE"]})
    return result.data


def get_all_facts():
    """Retrieve all facts from the graph."""
    result = db.records.find({"labels": ["FACT"]})
    return result.data


def get_facts_by_domain():
    """Group facts by their domain."""
    facts = get_all_facts()
    by_domain = defaultdict(list)
    for fact in facts:
        domain = fact.data.get("domain", "unknown")
        by_domain[domain].append(fact)
    return by_domain


def find_contradictions():
    """
    Find all pairs of contradicting facts.
    
    Uses RushDB's graph traversal to find CONTRADICTS relationships.
    """
    facts = get_all_facts()
    contradictions = []
    seen_pairs = set()
    
    for fact in facts:
        # Get facts that this one contradicts
        contradicted = db.records.find({
            "labels": ["FACT"],
            "where": {
                "FACT": {
                    "$relation": {"type": "CONTRADICTS", "direction": "out"},
                    "__id": {"$ne": fact.id}
                }
            }
        })
        
        for other in contradicted.data:
            # Avoid duplicate pairs (A-B and B-A)
            pair_key = tuple(sorted([fact.id, other.id]))
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                contradictions.append({
                    "fact_a": fact,
                    "fact_b": other,
                    "topic": fact.data.get("contradiction_topic", "Unknown topic")
                })
    
    return contradictions


def get_sources_for_fact(fact_id: str):
    """Get all sources that asserted a given fact."""
    sources = db.records.find({
        "labels": ["SOURCE"],
        "where": {
            "FACT": {
                "$relation": {"type": "ASSERTED_BY", "direction": "in"},
                "__id": fact_id
            }
        }
    })
    return sources.data


def get_contradiction_evidence(fact_a, fact_b):
    """
    Get supporting evidence for a pair of contradicting facts.
    Returns source information with reliability scores.
    """
    sources_a = get_sources_for_fact(fact_a.id)
    sources_b = get_sources_for_fact(fact_b.id)
    
    return {
        "fact_a": {
            "claim": fact_a.data.get("claim"),
            "confidence": fact_a.data.get("confidence_level"),
            "sources": [{
                "name": s.data["name"],
                "type": s.data["type"],
                "reliability": s.data.get("reliability_score", 0)
            } for s in sources_a]
        },
        "fact_b": {
            "claim": fact_b.data.get("claim"),
            "confidence": fact_b.data.get("confidence_level"),
            "sources": [{
                "name": s.data["name"],
                "type": s.data["type"],
                "reliability": s.data.get("reliability_score", 0)
            } for s in sources_b]
        }
    }


def calculate_source_weight(sources):
    """Calculate weighted average reliability of sources."""
    if not sources:
        return 0.0
    return sum(s.get("reliability", 0) for s in sources) / len(sources)


def demonstrate_resolution(fact_a, fact_b):
    """
    Demonstrate how to resolve a contradiction.
    
    This shows the process of:
    1. Comparing source reliability
    2. Selecting the more credible position
    3. Recording the resolution
    """
    print_subheader("Contradiction Resolution Process")
    
    evidence = get_contradiction_evidence(fact_a, fact_b)
    
    print(f"Topic: {fact_a.data.get('contradiction_topic')}")
    print(f"\nFact A: {evidence['fact_a']['claim']}")
    print(f"  Confidence: {evidence['fact_a']['confidence']}")
    for src in evidence['fact_a']['sources']:
        print(f"  - {src['name']} (reliability: {src['reliability']:.0%})")
    
    print(f"\nFact B: {evidence['fact_b']['claim']}")
    print(f"  Confidence: {evidence['fact_b']['confidence']}")
    for src in evidence['fact_b']['sources']:
        print(f"  - {src['name']} (reliability: {src['reliability']:.0%})")
    
    # Calculate weights
    weight_a = calculate_source_weight(evidence['fact_a']['sources'])
    weight_b = calculate_source_weight(evidence['fact_b']['sources'])
    
    print(f"\nEvidence Weight Analysis:")
    print(f"  Fact A weighted reliability: {weight_a:.2%}")
    print(f"  Fact B weighted reliability: {weight_b:.2%}")
    
    # Determine winner
    winner = "A" if weight_a > weight_b else "B"
    print(f"\n→ Resolution: Fact {winner} is more credible based on source reliability.")
    
    return winner, max(weight_a, weight_b)


def main():
    """Main demonstration function."""
    print("\n" + "=" * 70)
    print(" HANDLING CONTRADICTORY INFORMATION IN GRAPH-STORED KNOWLEDGE")
    print("=" * 70)
    print("\nThis tutorial demonstrates RushDB's native graph capabilities")
    print("for modeling, discovering, and resolving contradictory information.")
    
    # =========================================================================
    # SECTION 1: Database Status
    # =========================================================================
    print_header("1. Database Status")
    
    all_sources = get_all_sources()
    all_facts = get_all_facts()
    
    print(f"\nTotal Sources: {len(all_sources)}")
    print(f"Total Facts: {len(all_facts)}")
    
    # Count relationships
    contradictions = find_contradictions()
    print(f"Contradiction Pairs: {len(contradictions)}")
    
    # =========================================================================
    # SECTION 2: All Sources
    # =========================================================================
    print_header("2. Knowledge Sources in the Graph")
    
    print("\nSources are stored as nodes with reliability metadata:")
    for source in all_sources:
        print(f"\n  [{source.data['type'].upper()}] {source.data['name']}")
        print(f"    Reliability: {source.data.get('reliability_score', 'N/A'):.0%}")
        print(f"    URL: {source.data.get('url', 'N/A')}")
    
    # =========================================================================
    # SECTION 3: Domain Analysis
    # =========================================================================
    print_header("3. Facts by Domain")
    
    facts_by_domain = get_facts_by_domain()
    
    for domain, facts in sorted(facts_by_domain.items()):
        print(f"\n  {domain.upper()} ({len(facts)} facts)")
        for fact in facts:
            has_contradiction = "🔄" if fact.data.get("contradiction_topic") else "  "
            confidence = fact.data.get("confidence_level", "unknown")
            print(f"    {has_contradiction} {confidence:8s} | {fact.data['claim'][:60]}...")
    
    # =========================================================================
    # SECTION 4: Contradiction Pairs
    # =========================================================================
    print_header("4. Contradiction Analysis")
    
    print(f"\nFound {len(contradictions)} pairs of contradicting facts:\n")
    
    for i, contradiction in enumerate(contradictions, 1):
        fact_a = contradiction["fact_a"]
        fact_b = contradiction["fact_b"]
        
        print(f"\n  [{i}] {contradiction['topic']}")
        print(f"      A: {fact_a.data['claim'][:70]}...")
        print(f"      B: {fact_b.data['claim'][:70]}...")
    
    # =========================================================================
    # SECTION 5: Deep Evidence Analysis
    # =========================================================================
    print_header("5. Evidence Analysis for Contradictions")
    
    # Pick one contradiction for detailed analysis
    sample = contradictions[0]
    fact_a = sample["fact_a"]
    fact_b = sample["fact_b"]
    
    print_subheader(f"Detailed Evidence: {sample['topic']}")
    
    evidence = get_contradiction_evidence(fact_a, fact_b)
    
    print(f"\n  CLAIM A ({evidence['fact_a']['confidence']} confidence):")
    print(f"  \"{evidence['fact_a']['claim']}\"")
    print(f"  Sources:")
    for src in evidence['fact_a']['sources']:
        print(f"    • {src['name']} ({src['type']}, reliability: {src['reliability']:.0%})")
    
    print(f"\n  CLAIM B ({evidence['fact_b']['confidence']} confidence):")
    print(f"  \"{evidence['fact_b']['claim']}\"")
    print(f"  Sources:")
    for src in evidence['fact_b']['sources']:
        print(f"    • {src['name']} ({src['type']}, reliability: {src['reliability']:.0%})")
    
    # =========================================================================
    # SECTION 6: Resolution Demo
    # =========================================================================
    print_header("6. Demonstrating Conflict Resolution")
    
    winner, confidence = demonstrate_resolution(fact_a, fact_b)
    
    print("\n" + "-" * 50)
    print("In a real system, this resolution would be stored as:")
    
    resolution_data = {
        "resolved_topic": sample['topic'],
        "winning_claim": evidence[f'fact_{winner.lower()}']['claim'],
        "confidence": confidence,
        "resolution_date": "2024-01-15",
        "method": "source_reliability_weighting"
    }
    
    print(f"\n  Record type: RESOLUTION")
    for key, value in resolution_data.items():
        print(f"  {key}: {value}")
    
    # =========================================================================
    # SECTION 7: Confidence Ranking
    # =========================================================================
    print_header("7. Facts Ranked by Source Reliability")
    
    print("\nRanking all facts by the weighted reliability of their sources:\n")
    
    fact_weights = []
    for fact in all_facts:
        sources = get_sources_for_fact(fact.id)
        sources_info = [{
            "name": s.data["name"],
            "reliability": s.data.get("reliability_score", 0)
        } for s in sources]
        weight = calculate_source_weight(sources_info)
        fact_weights.append({
            "fact": fact,
            "weight": weight,
            "sources": sources_info
        })
    
    # Sort by weight
    fact_weights.sort(key=lambda x: x["weight"], reverse=True)
    
    for i, item in enumerate(fact_weights[:10], 1):
        fact = item["fact"]
        print(f"  {i}. [{item['weight']:.0%}] {fact.data['claim'][:55]}...")
        for src in item["sources"]:
            print(f"       └─ {src['name']}: {src['reliability']:.0%}")
    
    # =========================================================================
    # SECTION 8: Key Takeaways
    # =========================================================================
    print_header("8. Key Takeaways")
    
    takeaways = [
        ("Graph Native", "Contradictions are first-class relationships, not complex join queries"),
        ("Source Attribution", "Every fact links to its sources, enabling evidence-based resolution"),
        ("Traversal Power", "Finding contradictions is O(1) relationship lookup, not table scans"),
        ("Weighted Resolution", "Source reliability metadata enables systematic conflict resolution"),
        ("Flexible Schema", "Add new attributes like 'contradiction_topic' without migrations"),
    ]
    
    for title, description in takeaways:
        print(f"\n  ✓ {title}")
        print(f"    {description}")
    
    print("\n" + "=" * 70)
    print(" TUTORIAL COMPLETE")
    print("=" * 70)
    print("\nLearn more: https://docs.rushdb.com")
    print("GitHub: https://github.com/rush-db/examples")


if __name__ == "__main__":
    main()
