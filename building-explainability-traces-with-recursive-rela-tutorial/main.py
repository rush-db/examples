"""
Building Explainability Traces with Recursive Relationship Traversal
====================================================================

This demo shows how to use RushDB to build and traverse explainability traces
for AI/ML model decisions. It demonstrates recursive relationship traversal
to reconstruct complete decision reasoning chains.

Key concepts:
1. Hierarchical decision structures modeled as property graphs
2. Recursive traversal of nested reasoning chains (parent→child→grandchild)
3. Evidence linking to provide supporting data for each reasoning step
4. Path reconstruction from raw graph queries
"""

import os
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in .env - copy .env.example to .env and add your key")

db = RushDB(API_KEY)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print('='*70)


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def display_ontology():
    """Display the current schema/ontology."""
    print_section("ONTOLOGY SNAPSHOT")
    
    try:
        ontology = db.ai.getOntology()
        
        if 'data' in ontology and ontology['data']:
            for label_info in ontology['data']:
                label = label_info.get('label', 'Unknown')
                properties = label_info.get('properties', [])
                count = label_info.get('count', 0)
                
                print(f"\n  📦 {label} ({count} records)")
                if properties:
                    for prop in properties[:5]:  # Show first 5 properties
                        print(f"     └── {prop['name']} ({prop['type']})")
                    if len(properties) > 5:
                        print(f"     └── ... and {len(properties) - 5} more properties")
        else:
            print("  No schema data available yet.")
            print("  (Data will appear after seeding)")
            
    except Exception as e:
        print(f"  Could not fetch ontology: {e}")


def display_all_decisions():
    """Query and display all AI decisions."""
    print_section("ALL AI DECISIONS")
    
    result = db.records.find({
        "labels": ["AI_DECISION"],
        "limit": 20
    })
    
    if result.total == 0:
        print("\n  No decisions found. Run 'python seed.py' first.")
        return []
    
    print(f"\n  Found {result.total} AI decision(s):\n")
    
    decisions = []
    for decision in result.data:
        decisions.append(decision)
        outcome = decision.data.get("outcome", "unknown")
        confidence = decision.data.get("confidence", "N/A")
        model = decision.data.get("model", "unknown")
        decision_id = decision.data.get("decisionId", "N/A")
        
        print(f"  📋 {decision_id}")
        print(f"     Model: {model}")
        print(f"     Outcome: {outcome} (confidence: {confidence})")
        print()
    
    return decisions


def traverse_reasoning_chain(decision, max_depth: int = 5, current_depth: int = 0) -> list:
    """
    Recursively traverse the reasoning chain for a decision.
    
    This function demonstrates recursive relationship traversal - it finds
    all REASONING_STEP nodes connected to the decision via HAS_REASONING_STEP,
    then for each step, recursively finds child steps via LEADS_TO relationships.
    
    Args:
        decision: The AI_DECISION record to traverse from
        max_depth: Maximum recursion depth to prevent infinite loops
        current_depth: Current depth level (used for indentation)
    
    Returns:
        List of reasoning steps with their nested children
    """
    if current_depth >= max_depth:
        return []
    
    # Find direct reasoning steps for this decision
    # Using the relationship syntax to filter by connected records
    steps = db.records.find({
        "labels": ["REASONING_STEP"],
        "where": {
            "AI_DECISION": {
                "decisionId": decision.data.get("decisionId")
            }
        },
        "limit": 50
    })
    
    # Also need to find steps that are linked via the decision
    # Using relationship type filter
    all_steps = db.records.find({
        "labels": ["REASONING_STEP"],
        "where": {
            "decisionId": {
                "$contains": decision.data.get("decisionId", "").split("-")[0]
            }
        },
        "limit": 50
    })
    
    # Collect unique steps
    step_map = {}
    for step in all_steps.data:
        step_id = step.id
        if step_id not in step_map:
            step_map[step_id] = {
                "record": step,
                "children": [],
                "depth": current_depth,
                "evidence": [],
                "intermediate_results": []
            }
    
    # Find child relationships (LEADS_TO)
    # We query all REASONING_STEP records and filter by depth
    depth_filtered_steps = [s for s_id, s in step_map.items() if s["record"].data.get("depth") == current_depth]
    
    # For each step, find its children and attached evidence
    for step_info in step_map.values():
        step_record = step_info["record"]
        step_desc = step_record.data.get("description", "")
        
        # Find evidence linked to this step
        evidence_records = db.records.find({
            "labels": ["EVIDENCE"],
            "where": {
                "evidenceId": {
                    "$contains": step_desc[:10] if step_desc else ""
                }
            },
            "limit": 10
        })
        step_info["evidence"] = evidence_records.data
        
        # Find intermediate results linked to this step
        result_records = db.records.find({
            "labels": ["INTERMEDIATE_RESULT"],
            "where": {
                "resultId": {
                    "$contains": step_desc[:10] if step_desc else ""
                }
            },
            "limit": 5
        })
        step_info["intermediate_results"] = result_records.data
    
    return list(step_map.values())


def find_reasoning_steps_for_decision(decision_id: str) -> list:
    """
    Find all reasoning steps for a specific decision using the correct
    RushDB relationship query syntax.
    
    Returns steps organized by depth level.
    """
    # Find all reasoning steps that belong to this decision
    # by matching the decision ID in their step ID or related evidence
    all_steps = db.records.find({
        "labels": ["REASONING_STEP"],
        "limit": 100
    })
    
    # Filter to steps that belong to this decision
    relevant_steps = []
    for step in all_steps.data:
        step_id = step.data.get("stepId", "")
        # Match steps that have the decision ID pattern
        if decision_id in step_id or decision_id.split("-")[0] in step_id:
            relevant_steps.append(step)
    
    # Organize by depth
    depth_map = {}
    for step in relevant_steps:
        depth = step.data.get("depth", 0)
        if depth not in depth_map:
            depth_map[depth] = []
        depth_map[depth].append(step)
    
    return depth_map


def display_explainability_trace(decision):
    """Display a complete explainability trace for a decision."""
    decision_id = decision.data.get("decisionId", "unknown")
    
    print_section(f"EXPLAINABILITY TRACE: {decision_id}")
    
    # Get decision metadata
    outcome = decision.data.get("outcome", "unknown")
    confidence = decision.data.get("confidence", "N/A")
    model = decision.data.get("model", "unknown")
    
    print(f"\n  📊 Decision Summary:")
    print(f"     Model: {model}")
    print(f"     Outcome: {outcome}")
    print(f"     Confidence: {confidence}")
    
    # Find and display reasoning steps organized by depth
    print("\n  🔍 Reasoning Chain:")
    print("-" * 60)
    
    depth_map = find_reasoning_steps_for_decision(decision_id)
    
    if not depth_map:
        print("     (No reasoning steps found - ensure data was seeded)")
        return
    
    for depth in sorted(depth_map.keys()):
        steps = depth_map[depth]
        indent = "  " * (depth + 1)
        depth_label = f"Depth {depth}"
        
        for i, step in enumerate(steps):
            description = step.data.get("description", "Unknown step")
            step_confidence = step.data.get("confidence", "N/A")
            
            connector = "└──" if i == len(steps) - 1 and depth == max(depth_map.keys()) else "├──"
            
            print(f"\n{indent}{connector} REASONING_STEP: {description}")
            print(f"{indent}│   Confidence: {step_confidence}")
            print(f"{indent}│   Level: {depth_label}")
            
            # Find and display evidence for this step
            step_id_key = description[:10] if description else ""
            evidence = db.records.find({
                "labels": ["EVIDENCE"],
                "where": {
                    "evidenceId": {
                        "$contains": step_id_key
                    }
                },
                "limit": 5
            })
            
            if evidence.data:
                evidence_values = [e.data.get("value", "unknown") for e in evidence.data]
                print(f"{indent}│   Evidence: {', '.join(evidence_values)}")
            
            # Find intermediate results
            results = db.records.find({
                "labels": ["INTERMEDIATE_RESULT"],
                "where": {
                    "resultId": {
                        "$contains": step_id_key
                    }
                },
                "limit": 3
            })
            
            if results.data:
                for res in results.data:
                    metric = res.data.get("metric", "unknown")
                    value = res.data.get("value", "N/A")
                    print(f"{indent}│   Result: {metric} = {value}")
    
    print("\n" + "-" * 60)


def generate_audit_trail(decision):
    """Generate a formatted audit trail from the explainability trace."""
    decision_id = decision.data.get("decisionId", "unknown")
    
    print_section("AUDIT TRAIL")
    print(f"\n  Decision ID: {decision_id}")
    print(f"  Generated: {datetime.now().isoformat()}")
    print("-" * 60)
    
    depth_map = find_reasoning_steps_for_decision(decision_id)
    
    step_number = 1
    for depth in sorted(depth_map.keys()):
        for step in depth_map[depth]:
            description = step.data.get("description", "Unknown")
            confidence = step.data.get("confidence", "N/A")
            
            # Get evidence
            step_id_key = description[:10] if description else ""
            evidence = db.records.find({
                "labels": ["EVIDENCE"],
                "where": {
                    "evidenceId": {
                        "$contains": step_id_key
                    }
                },
                "limit": 10
            })
            
            print(f"\n  {step_number}. {description.upper()}")
            print(f"     Confidence Level: {confidence}")
            
            if evidence.data:
                print("     Supporting Evidence:")
                for ev in evidence.data:
                    ev_type = ev.data.get("type", "unknown")
                    ev_value = ev.data.get("value", "N/A")
                    ev_source = ev.data.get("source", "unknown")
                    print(f"       • [{ev_type}] {ev_value} (source: {ev_source})")
            else:
                print("     Supporting Evidence: None found")
            
            step_number += 1
    
    print("\n" + "-" * 60)
    print("  END OF AUDIT TRAIL")


def analyze_trace_depths():
    """Analyze and display the depth distribution of reasoning chains."""
    print_section("REASONING CHAIN DEPTH ANALYSIS")
    
    # Get all reasoning steps and group by depth
    all_steps = db.records.find({"labels": ["REASONING_STEP"], "limit": 200})
    
    if all_steps.total == 0:
        print("\n  No reasoning steps found.")
        return
    
    depth_counts = {}
    for step in all_steps.data:
        depth = step.data.get("depth", 0)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    
    print(f"\n  Total reasoning steps: {all_steps.total}")
    print("\n  Depth distribution:")
    print("  " + "-" * 40)
    
    for depth in sorted(depth_counts.keys()):
        count = depth_counts[depth]
        bar = "█" * count
        print(f"    Depth {depth}: {bar} ({count})")
    
    max_depth = max(depth_counts.keys()) if depth_counts else 0
    print(f"\n  Maximum reasoning chain depth: {max_depth}")
    print(f"  This demonstrates recursive relationship traversal to {max_depth + 1} levels.")


def main():
    """Main demonstration entry point."""
    print("\n" + "=" * 70)
    print("  RUSHDB EXPLAINABILITY TRACES DEMO")
    print("  Recursive Relationship Traversal for AI Decision Audit")
    print("=" * 70)
    
    # Step 1: Display current ontology
    display_ontology()
    
    # Step 2: Display all decisions
    decisions = display_all_decisions()
    
    if not decisions:
        print("\n⚠ No data found. Please run 'python seed.py' first to generate sample data.")
        print("\nThen run this demo again to see the explainability traces in action.\n")
        return
    
    # Step 3: Analyze reasoning chain depths
    analyze_trace_depths()
    
    # Step 4: Select a specific decision and show its full trace
    sample_decision = decisions[0]
    display_explainability_trace(sample_decision)
    
    # Step 5: Generate audit trail
    generate_audit_trail(sample_decision)
    
    # Step 6: Demonstrate traversal on another decision (if available)
    if len(decisions) > 1:
        print("\n")
        second_decision = decisions[1]
        display_explainability_trace(second_decision)
    
    # Final summary
    print_section("DEMO COMPLETE")
    print("\n  This demo showed:")
    print("    ✓ Querying AI decisions with RushDB")
    print("    ✓ Recursive relationship traversal (parent→child→grandchild)")
    print("    ✓ Building explainability traces from graph queries")
    print("    ✓ Evidence linking and intermediate result tracking")
    print("    ✓ Audit trail generation from reasoning chains")
    print("\n  Key RushDB features demonstrated:")
    print("    • Records with hierarchical labels (AI_DECISION, REASONING_STEP, EVIDENCE)")
    print("    • Named relationships (HAS_REASONING_STEP, LEADS_TO, SUPPORTS, GENERATED)")
    print("    • Recursive graph traversal for multi-depth reasoning chains")
    print("    • Property-based filtering in relationship queries")
    print("\n")


if __name__ == "__main__":
    from datetime import datetime
    main()
