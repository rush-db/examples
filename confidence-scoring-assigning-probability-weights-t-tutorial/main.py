"""
RushDB Confidence Scoring Tutorial

Demonstrates how to:
- Store confidence/probability weights on graph facts
- Query facts filtered by confidence threshold
- Traverse relationships to compute aggregate confidence
- Use vector similarity scores as confidence indicators

Run: python main.py
"""

import os
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def compute_aggregate_confidence(base_confidence, source_reliabilities):
    """
    Compute aggregate confidence given base confidence and supporting sources.
    
    Formula: aggregate = base * (1 - product of (1 - reliability))
    This models the probability that at least one reliable source is correct.
    
    Args:
        base_confidence: Base confidence of the fact (0.0 to 1.0)
        source_reliabilities: List of reliability scores for supporting sources
    
    Returns:
        Aggregated confidence score (0.0 to 1.0)
    """
    if not source_reliabilities:
        return base_confidence
    
    # Combined source reliability (probability that at least one source is correct)
    # Using: 1 - (1-s1)(1-s2)...(1-sn)
    combined = 1.0
    for reliability in source_reliabilities:
        combined *= (1 - reliability)
    
    source_weight = 1 - combined
    
    # Blend base confidence with source reliability
    aggregate = base_confidence * (0.3 + 0.7 * source_weight)
    return min(aggregate, 1.0)


def get_sources_for_fact(fact):
    """
    Get all sources supporting a fact via graph traversal.
    
    Args:
        fact: Record object representing a FACT
    
    Returns:
        List of source Record objects
    """
    # Find all FACT records that are SUPPORTED_BY the given fact
    # (Actually, we want sources linked FROM the fact)
    related_sources = db.records.find({
        "labels": ["SOURCE"],
        "where": {
            "FACT": {
                "$relation": {"type": "SUPPORTED_BY", "direction": "in"},
                "$id": {"$eq": fact.id}
            }
        }
    })
    return related_sources.data


def format_confidence(score):
    """Format confidence score as percentage with color indicator."""
    pct = score * 100
    if pct >= 90:
        indicator = "🟢"
    elif pct >= 60:
        indicator = "🟡"
    elif pct >= 30:
        indicator = "🟠"
    else:
        indicator = "🔴"
    return f"{pct:5.1f}% {indicator}"


# =============================================================================
# TUTORIAL DEMONSTRATIONS
# =============================================================================

def demo_basic_confidence_queries():
    """
    DEMO 1: Basic confidence queries
    
    Show how to filter facts by confidence threshold.
    """
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Confidence Queries")
    print("=" * 70)
    
    # Get all facts
    all_facts = db.records.find({"labels": ["FACT"]})
    
    print(f"\nTotal facts in database: {len(all_facts.data)}\n")
    print(f"{'Statement':<45} {'Confidence':<12} {'Category'}")
    print("-" * 75)
    
    for fact in all_facts.data:
        statement = fact["statement"][:42] + "..." if len(fact["statement"]) > 42 else fact["statement"]
        conf = format_confidence(fact["confidence"])
        cat = fact.get("category", "unknown")
        print(f"{statement:<45} {conf:<12} {cat}")

    # High confidence facts (>= 0.9)
    print("\n\n--- High Confidence Facts (>= 90%) ---")
    high_conf = db.records.find({
        "labels": ["FACT"],
        "where": {
            "confidence": {"$gte": 0.9}
        },
        "orderBy": {"confidence": "desc"}
    })
    for fact in high_conf.data:
        print(f"  • {fact['statement']} ({fact['confidence']:.1%})")

    # Low confidence facts (< 0.5)
    print("\n--- Low Confidence Facts (< 50%) ---")
    low_conf = db.records.find({
        "labels": ["FACT"],
        "where": {
            "confidence": {"$lt": 0.5}
        },
        "orderBy": {"confidence": "asc"}
    })
    for fact in low_conf.data:
        print(f"  • {fact['statement']} ({fact['confidence']:.1%})")


def demo_aggregate_confidence():
    """
    DEMO 2: Aggregate Confidence via Graph Traversal
    
    Show how to compute confidence by combining base confidence
    with source reliability scores.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Aggregate Confidence via Graph Traversal")
    print("=" * 70)
    print("\nFormula: aggregate = base * (0.3 + 0.7 * source_weight)")
    print("Where source_weight = 1 - ∏(1 - reliability)\n")
    
    # Get all facts with their supporting sources
    facts = db.records.find({"labels": ["FACT"]})
    
    print(f"{'Statement':<38} {'Base':<10} {'Sources':<30} {'Aggregate'}")
    print("-" * 95)
    
    for fact in facts.data:
        sources = get_sources_for_fact(fact)
        source_names = ", ".join([s["name"] for s in sources])[:28]
        
        if sources:
            reliabilities = [s["reliability"] for s in sources]
            aggregate = compute_aggregate_confidence(fact["confidence"], reliabilities)
        else:
            reliabilities = []
            aggregate = fact["confidence"]
        
        base_str = f"{fact['confidence']:.1%}"
        sources_str = f"[{len(sources)}] {source_names}"
        
        print(f"{fact['statement'][:36]:<38} {base_str:<10} {sources_str:<30} {format_confidence(aggregate)}")


def demo_source_reliability_impact():
    """
    DEMO 3: Source Reliability Impact
    
    Show how changing source reliability affects aggregate confidence.
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Source Reliability Impact Analysis")
    print("=" * 70)
    
    # Pick a fact with multiple sources
    test_fact = db.records.find({
        "labels": ["FACT"],
        "where": {"confidence": {"$gte": 0.8}},
        "limit": 1
    }).data[0]
    
    sources = get_sources_for_fact(test_fact)
    
    print(f"\nAnalyzing: \"{test_fact['statement']}\"")
    print(f"Base confidence: {test_fact['confidence']:.1%}")
    print(f"\nSupporting sources:")
    
    for source in sources:
        print(f"  • {source['name']:<20} (reliability: {source['reliability']:.0%})")
    
    # Show how aggregate changes with different source configurations
    print("\n--- Aggregate Confidence by Source Combination ---")
    
    reliabilities = [s["reliability"] for s in sources]
    
    for i in range(len(reliabilities) + 1):
        subset = reliabilities[:i] if i > 0 else []
        agg = compute_aggregate_confidence(test_fact["confidence"], subset)
        sources_used = f"{i}/{len(reliabilities)}" if i > 0 else "none"
        print(f"  {sources_used} source(s): {format_confidence(agg)}")


def demo_confidence_by_category():
    """
    DEMO 4: Confidence Distribution by Category
    
    Show average confidence per fact category.
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Confidence Distribution by Category")
    print("=" * 70)
    
    facts = db.records.find({"labels": ["FACT"]})
    
    # Group by category
    categories = {}
    for fact in facts.data:
        cat = fact.get("category", "uncategorized")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(fact["confidence"])
    
    print(f"\n{'Category':<15} {'Count':<8} {'Avg Confidence':<20} {'Range'}")
    print("-" * 60)
    
    for cat, confidences in sorted(categories.items(), key=lambda x: -sum(x[1])/len(x[1])):
        avg = sum(confidences) / len(confidences)
        min_c = min(confidences)
        max_c = max(confidences)
        range_str = f"{min_c:.0%} - {max_c:.0%}"
        print(f"{cat:<15} {len(confidences):<8} {format_confidence(avg):<20} {range_str}")


def demo_find_uncertain_facts():
    """
    DEMO 5: Finding Facts Needing Verification
    
    Identify facts with low confidence or weak source support
    that should be verified.
    """
    print("\n" + "=" * 70)
    print("DEMO 5: Facts Needing Verification")
    print("=" * 70)
    
    facts = db.records.find({"labels": ["FACT"]})
    
    uncertain_facts = []
    
    for fact in facts.data:
        sources = get_sources_for_fact(fact)
        
        # A fact is "uncertain" if:
        # - Base confidence < 0.7, OR
        # - No sources, OR
        # - All sources have reliability < 0.5
        base_low = fact["confidence"] < 0.7
        no_sources = len(sources) == 0
        weak_sources = sources and all(s["reliability"] < 0.5 for s in sources)
        
        if base_low or no_sources or weak_sources:
            reasons = []
            if base_low:
                reasons.append(f"low base ({fact['confidence']:.0%})")
            if no_sources:
                reasons.append("no sources")
            if weak_sources:
                reasons.append("weak sources")
            
            uncertain_facts.append({
                "fact": fact,
                "sources": sources,
                "reasons": reasons
            })
    
    print(f"\nFound {len(uncertain_facts)} facts needing verification:\n")
    
    for item in uncertain_facts:
        fact = item["fact"]
        reasons_str = ", ".join(item["reasons"])
        print(f"  ⚠️  \"{fact['statement']}\"")
        print(f"      Confidence: {fact['confidence']:.1%} | Category: {fact.get('category', 'unknown')}")
        print(f"      Issues: {reasons_str}")
        if item["sources"]:
            src_list = ", ".join([s["name"] for s in item["sources"]])
            print(f"      Sources: {src_list}")
        print()


def demo_confidence_update():
    """
    DEMO 6: Updating Confidence Scores
    
    Show how to update a fact's confidence when new evidence arrives.
    """
    print("\n" + "=" * 70)
    print("DEMO 6: Updating Confidence Scores")
    print("=" * 70)
    
    # Find a fact to update
    fact_to_update = db.records.find({
        "labels": ["FACT"],
        "where": {"confidence": {"$lt": 0.5}},
        "limit": 1
    }).data
    
    if not fact_to_update:
        print("\nNo low-confidence facts to demonstrate updates.")
        return
    
    fact = fact_to_update[0]
    old_conf = fact["confidence"]
    
    print(f"\nOriginal fact: \"{fact['statement']}\"")
    print(f"Original confidence: {old_conf:.1%}")
    
    # Simulate adding a reliable source (improves confidence)
    new_confidence = min(old_conf + 0.15, 1.0)
    
    print(f"\nNew evidence received! Updating confidence...")
    print(f"New confidence: {new_confidence:.1%}")
    print(f"Change: +{(new_confidence - old_conf) * 100:.0f}%")
    
    # Demonstrate the update (commented out to preserve demo data)
    # db.records.update(record_id=fact.id, data={"confidence": new_confidence})
    # print("\n✓ Updated in RushDB")
    
    print("\n[Note: Update skipped to preserve demo data]")


def demo_confidence_scoring_relationships():
    """
    DEMO 7: Relationship-Based Confidence Scoring
    
    Show how to calculate confidence based on relationship patterns.
    """
    print("\n" + "=" * 70)
    print("DEMO 7: Relationship-Based Confidence Analysis")
    print("=" * 70)
    
    # Count facts by number of supporting sources
    facts = db.records.find({"labels": ["FACT"]})
    
    by_source_count = {0: [], 1: [], 2: [], 3: []}
    
    for fact in facts.data:
        sources = get_sources_for_fact(fact)
        count = min(len(sources), 3)
        by_source_count[count].append(fact)
    
    print("\n--- Facts by Number of Supporting Sources ---\n")
    
    for count in sorted(by_source_count.keys()):
        facts_list = by_source_count[count]
        if facts_list:
            print(f"{count} source(s): {len(facts_list)} fact(s)")
            for f in facts_list:
                avg_src_rel = 0.0
                sources = get_sources_for_fact(f)
                if sources:
                    avg_src_rel = sum(s["reliability"] for s in sources) / len(sources)
                print(f"    • \"{f['statement'][:50]}\"")
                print(f"      base={f['confidence']:.0%}, avg source reliability={avg_src_rel:.0%}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run all confidence scoring demonstrations."""
    print("\n" + "=" * 70)
    print("RUSHDB CONFIDENCE SCORING TUTORIAL")
    print("Assigning Probability Weights to Graph-Retrieved Facts")
    print("=" * 70)
    
    # Run all demos
    demo_basic_confidence_queries()
    demo_aggregate_confidence()
    demo_source_reliability_impact()
    demo_confidence_by_category()
    demo_find_uncertain_facts()
    demo_confidence_update()
    demo_confidence_scoring_relationships()
    
    print("\n" + "=" * 70)
    print("TUTORIAL COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Store confidence as a property on fact records")
    print("  • Use graph traversal to find supporting sources")
    print("  • Compute aggregate confidence by combining base + source reliability")
    print("  • Filter facts by confidence threshold for downstream use")
    print("  • Update confidence when new evidence arrives")
    print("\nLearn more: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
