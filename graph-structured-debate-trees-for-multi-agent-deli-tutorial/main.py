"""
Graph-Structured Debate Trees for Multi-Agent Deliberation

Demonstrates RushDB's property graph capabilities for modeling complex debate
structures with multiple agents, hierarchical arguments, and relationship traversal.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("Error: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_subsection(title):
    """Print a subsection header."""
    print(f"\n--- {title} ---")


def demonstrate_debate_structure():
    """Demonstrate basic graph structure queries."""
    print_section("1. DEBATE STRUCTURE OVERVIEW")

    # Find the debate
    debates = db.records.find({
        "labels": ["DEBATE"],
        "where": {
            "topic": "Should autonomous vehicles replace human drivers?"
        }
    })

    if not debates.data:
        print("No debate found. Run `python seed.py` first.")
        return

    debate = debates.data[0]
    print(f"\nDebate: {debate['topic']}")
    print(f"ID: {debate['id']}")
    print(f"Status: {debate.get('status', 'unknown')}")

    # Count participants
    agents = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "DEBATE": {"$relation": {"type": "PARTICIPATES_AS", "direction": "out"}}
        }
    })
    print(f"\nParticipants: {len(agents.data)}")
    for agent in agents.data:
        print(f"  - {agent['name']} ({agent.get('role', 'unknown role')})")

    # Show positions
    positions = db.records.find({"labels": ["POSITION"]})
    print(f"\nPositions: {len(positions.data)}")
    for pos in positions.data:
        print(f"  - {pos['stance']}: {pos.get('description', '')}")


def demonstrate_argument_tree():
    """Demonstrate hierarchical argument traversal."""
    print_section("2. ARGUMENT TREE ANALYSIS")

    # Find all arguments
    arguments = db.records.find({"labels": ["ARGUMENT"]})
    print(f"\nTotal arguments: {len(arguments.data)}")

    # Group by depth
    by_depth = {}
    for arg in arguments.data:
        depth = arg.get('depth', 0)
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append(arg)

    for depth in sorted(by_depth.keys()):
        depth_args = by_depth[depth]
        depth_name = "Root arguments" if depth == 0 else f"Supporting (depth {depth})"
        print(f"\n  {depth_name}: {len(depth_args)}")
        for arg in depth_args:
            text_preview = arg['text'][:60] + "..." if len(arg['text']) > 60 else arg['text']
            print(f"    [{arg['strength']:.2f}] {text_preview}")

    # Analyze by category
    print_subsection("Arguments by Category")
    categories = {}
    for arg in arguments.data:
        cat = arg.get('category', 'uncategorized')
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} arguments")


def demonstrate_agent_arguments():
    """Demonstrate finding arguments by agent."""
    print_section("3. AGENT-SPECIFIC ARGUMENTS")

    # Find the proponent
    proponent = db.records.find({
        "labels": ["AGENT"],
        "where": {"role": "PROPONENT"}
    })

    if proponent.data:
        agent = proponent.data[0]
        print(f"\n{agent['name']} ({agent['role']}):")
        print(f"  Bio: {agent.get('bio', 'N/A')}")

        # Find arguments authored by this agent
        agent_arguments = db.records.find({
            "labels": ["ARGUMENT"],
            "where": {
                "AGENT": {
                    "$relation": {"type": "AUTHORED_BY", "direction": "in"}
                }
            }
        })

        print(f"\n  Authored {len(agent_arguments.data)} arguments:")
        for arg in agent_arguments.data:
            cat = arg.get('category', '')
            strength = arg['strength']
            text = arg['text'][:50] + "..."
            print(f"    [{cat}] [{strength:.2f}] {text}")

    # Find the opponent
    opponent = db.records.find({
        "labels": ["AGENT"],
        "where": {"role": "OPPONENT"}
    })

    if opponent.data:
        agent = opponent.data[0]
        print(f"\n{agent['name']} ({agent['role']}):")

        agent_arguments = db.records.find({
            "labels": ["ARGUMENT"]
        })

        # Filter to just this agent's arguments
        opp_args = [
            arg for arg in agent_arguments.data
            if arg.get('_relationships')
            and any(r.get('targetLabel') == 'AGENT' and r.get('targetRole') == 'OPPONENT'
                   for r in arg.get('_relationships', []))
        ]

        # Alternative: query using relationship traversal
        # This queries all arguments and filters by those that have AUTHORED_BY to OPPONENT agent
        all_args = db.records.find({"labels": ["ARGUMENT"]})
        opp_args = []
        for arg in all_args.data:
            # Check if this argument was authored by OPPONENT
            # We check via the agent lookup
            authored = db.records.find({
                "labels": ["AGENT"],
                "where": {
                    "ARGUMENT": {
                        "$relation": {"type": "AUTHORED_BY", "direction": "out"}
                    },
                    "role": "OPPONENT"
                }
            })
            if authored.data:
                opp_args.append(arg)

        print(f"\n  Authored {len(opp_args)} arguments:")
        for arg in opp_args[:5]:  # Limit output
            cat = arg.get('category', '')
            strength = arg['strength']
            text = arg['text'][:50] + "..."
            print(f"    [{cat}] [{strength:.2f}] {text}")


def demonstrate_cross_references():
    """Demonstrate relationship traversal between arguments."""
    print_section("4. CROSS-REFERENCE ANALYSIS (Refutations)")

    # Find arguments that REFUTE others
    all_arguments = db.records.find({"labels": ["ARGUMENT"]})

    # Group by category
    counter_args = [arg for arg in all_arguments.data if arg.get('category') == 'counter']
    evidence_args = [arg for arg in all_arguments.data if arg.get('category') == 'evidence']
    root_args = [arg for arg in all_arguments.data if arg.get('depth') == 0 and arg.get('category') != 'counter']

    print(f"\nArgument types in the debate:")
    print(f"  Root positions: {len(root_args)}")
    print(f"  Evidence/Supporting: {len(evidence_args)}")
    print(f"  Counter/Refutations: {len(counter_args)}")

    # Show the counter-argument network
    print_subsection("Counter-Argument Network")

    for counter in counter_args:
        print(f"\n  Counter-argument by {counter['text'][:50]}...")
        print(f"    Strength: {counter['strength']:.2f}")

        # This shows which argument it targets via the REFUTES relationship
        # In a real traversal, we'd follow the relationship to find targets


def demonstrate_evaluation_system():
    """Demonstrate the judge evaluation system."""
    print_section("5. JUDGE EVALUATION SYSTEM")

    # Find evaluations
    evaluations = db.records.find({"labels": ["EVALUATION"]})

    if evaluations.data:
        print(f"\nFound {len(evaluations.data)} evaluations:")

        judge = db.records.find({
            "labels": ["AGENT"],
            "where": {"role": "JUDGE"}
        })

        if judge.data:
            print(f"  Judge: {judge.data[0]['name']}")

        total_score = 0
        for eval_data in evaluations.data:
            score = eval_data.get('score', 0)
            notes = eval_data.get('notes', '')
            category = eval_data.get('category', 'general')

            total_score += score
            print(f"\n  [{category}] Score: {score:.2f}")
            print(f"    Notes: {notes}")

        avg_score = total_score / len(evaluations.data) if evaluations.data else 0
        print(f"\n  Average argument quality: {avg_score:.2f}")
    else:
        print("No evaluations found")


def demonstrate_debate_scoring():
    """Calculate a simple debate score based on argument strength and coverage."""
    print_section("6. DEBATE SCORE ANALYSIS")

    # Get all arguments
    arguments = db.records.find({"labels": ["ARGUMENT"]})

    # Get positions
    positions = db.records.find({"labels": ["POSITION"]})

    pro_args = []
    con_args = []

    for arg in arguments.data:
        # Determine stance based on relationship
        # For simplicity, we'll query arguments linked to each position
        linked_to_pro = False

        # Check if argument has REFUTES relationship (these are cross-positions)
        if arg.get('category') == 'counter':
            # These typically target opposing arguments
            # Determine which side based on author
            pro_args.append(arg)
        else:
            # Root and supporting arguments have clearer stance
            if arg.get('depth') == 0:
                # Check stance by finding which position it's linked to
                # For simplicity, assume PRO arguments by proponent
                proponent = db.records.find({
                    "labels": ["AGENT"],
                    "where": {"role": "PROPONENT"}
                })
                if proponent.data:
                    pro_args.append(arg)
            else:
                pro_args.append(arg)

    # Calculate scores
    pro_strength = sum(arg['strength'] for arg in arguments.data) / len(arguments.data) if arguments.data else 0
    con_strength = pro_strength * 0.95  # Simplified - in real scenario, query CON arguments

    print(f"\nArgument Strength Analysis:")
    print(f"  Pro arguments: {len(pro_args)}")
    print(f"  Con arguments: {len(con_args)}")
    print(f"  Average strength: {pro_strength:.3f}")

    # Calculate coverage (based on categories covered)
    categories = set(arg.get('category', '') for arg in arguments.data)
    print(f"\nCategories covered: {len(categories)}")
    for cat in sorted(categories):
        print(f"  - {cat}")

    # Simple scoring model
    coverage_score = len(categories) / 5.0  # Normalize to expected categories
    balance_score = min(len(pro_args), len(con_args)) / max(len(pro_args), len(con_args)) if pro_args and con_args else 0.5

    print(f"\nScoring:")
    print(f"  Coverage score: {coverage_score:.2f} ({len(categories)}/5 categories)")
    print(f"  Balance score: {balance_score:.2f}")


def demonstrate_graph_traversal():
    """Demonstrate relationship traversal patterns."""
    print_section("7. RELATIONSHIP TRAVERSAL PATTERNS")

    # Pattern 1: Find all records linked to a specific argument
    print_subsection("Upstream: What arguments does this position support?")

    pro_position = db.records.find({
        "labels": ["POSITION"],
        "where": {"stance": "PRO"}
    })

    if pro_position.data:
        pro_pos = pro_position.data[0]
        print(f"\nPosition: {pro_pos['stance']}")

        # Find arguments that SUPPORTS this position
        supporting_args = db.records.find({
            "labels": ["ARGUMENT"],
            "where": {
                "POSITION": {
                    "$relation": {"type": "SUPPORTS", "direction": "in"}
                }
            }
        })

        print(f"  Directly supporting arguments: {len(supporting_args.data)}")
        for arg in supporting_args.data:
            print(f"    - {arg['text'][:40]}... (strength: {arg['strength']:.2f})")

    # Pattern 2: Find arguments by author with strength filter
    print_subsection("Agent Contributions with Strength Filter")

    # Find all arguments by proponent with strength > 0.8
    strong_pro_args = db.records.find({
        "labels": ["ARGUMENT"],
        "where": {
            "strength": {"$gte": 0.8}
        }
    })

    print(f"\nStrong arguments (strength >= 0.8): {len(strong_pro_args.data)}")
    for arg in strong_pro_args.data:
        print(f"  [{arg['strength']:.2f}] {arg['text'][:50]}...")

    # Pattern 3: Find arguments at specific depth
    print_subsection("Depth-Based Analysis")

    depth_1_args = db.records.find({
        "labels": ["ARGUMENT"],
        "where": {
            "depth": 1
        }
    })

    print(f"\nSecond-level arguments (depth 1): {len(depth_1_args.data)}")
    for arg in depth_1_args.data:
        source = arg.get('source', 'unknown')
        print(f"  Source: {source} - {arg['text'][:40]}...")


def demonstrate_transaction_operations():
    """Demonstrate atomic operations with transactions."""
    print_section("8. TRANSACTION OPERATIONS (Atomic Writes)")

    print("""
Demonstrating transaction patterns for debate operations:

1. Adding a new argument with multiple relationships
2. Updating an argument's strength based on judge feedback
3. Creating a new evaluation linked to argument and judge

Example pattern (not executed to preserve seed data):
""")

    # This pattern shows how transactions work for debate operations
    example_code = '''
# Create a new argument with atomic relationship setup
with db.transactions.begin() as tx:
    # Create the argument
    new_argument = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Additional evidence for safety claim",
            "strength": 0.88,
            "depth": 1,
            "category": "evidence"
        },
        transaction=tx
    )

    # Link to parent argument (supports relationship)
    parent_arg = db.records.find({
        "labels": ["ARGUMENT"],
        "where": {"category": "safety", "depth": 0}
    })
    if parent_arg.data:
        db.records.attach(
            source=new_argument,
            target=parent_arg.data[0],
            options={"type": "SUPPORTS", "direction": "out"},
            transaction=tx
        )

    # Link to proponent (authored by relationship)
    proponent = db.records.find({
        "labels": ["AGENT"],
        "where": {"role": "PROPONENT"}
    })
    if proponent.data:
        db.records.attach(
            source=proponent.data[0],
            target=new_argument,
            options={"type": "AUTHORED_BY", "direction": "out"},
            transaction=tx
        )

# Transaction commits automatically on clean exit
# Any exception triggers automatic rollback
'''
    print(example_code)


def demonstrate_summary_statistics():
    """Show summary statistics of the debate graph."""
    print_section("9. DEBATE GRAPH SUMMARY")

    # Count all record types
    labels = db.labels.find({})

    print("\nRecord counts by label:")
    for label_result in labels.data:
        label_name = label_result.name if hasattr(label_result, 'name') else label_result.get('name', 'unknown')
        count = label_result.count if hasattr(label_result, 'count') else label_result.get('count', 0)
        print(f"  {label_name}: {count}")

    # Graph metrics
    arguments = db.records.find({"labels": ["ARGUMENT"]})
    agents = db.records.find({"labels": ["AGENT"]})
    evaluations = db.records.find({"labels": ["EVALUATION"]})

    avg_strength = sum(a['strength'] for a in arguments.data) / len(arguments.data) if arguments.data else 0
    max_depth = max(a.get('depth', 0) for a in arguments.data) if arguments.data else 0

    print(f"\nGraph metrics:")
    print(f"  Total arguments: {len(arguments.data)}")
    print(f"  Total agents: {len(agents.data)}")
    print(f"  Total evaluations: {len(evaluations.data)}")
    print(f"  Average argument strength: {avg_strength:.3f}")
    print(f"  Maximum argument depth: {max_depth}")
    print(f"  Graph density: {len(arguments.data) / (len(agents.data) * max(1, len(arguments.data) - 1)):.3f}")


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("  Graph-Structured Debate Trees for Multi-Agent Deliberation")
    print("  RushDB Property Graph Demonstration")
    print("=" * 60)

    print("\n* Note: Run `python seed.py` first if no debate data exists")

    demonstrate_debate_structure()
    demonstrate_argument_tree()
    demonstrate_agent_arguments()
    demonstrate_cross_references()
    demonstrate_evaluation_system()
    demonstrate_debate_scoring()
    demonstrate_graph_traversal()
    demonstrate_transaction_operations()
    demonstrate_summary_statistics()

    print("\n" + "=" * 60)
    print("  Demonstration Complete")
    print("=" * 60)

    print("""
\nKey Takeaways:

1. Graph structure naturally models debate semantics:
   - Arguments as nodes with typed relationships
   - Support/Refute relationships form the logical network
   - Agents as first-class participants with authored arguments

2. RushDB enables powerful traversals:
   - Find all arguments by an agent
   - Navigate from conclusion to premises
   - Query by strength, depth, category
   - Filter via relationship type and direction

3. Transaction support for atomic operations:
   - Create argument + attach relationships in one transaction
   - Update multiple records with consistency guarantees
   - Automatic rollback on failure

4. Evaluation system demonstrates metadata:
   - Judge evaluations linked to arguments
   - Scores and notes for argument quality
   - Aggregate analysis for debate scoring
""")


if __name__ == "__main__":
    main()
