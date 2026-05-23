"""
Seed script for Graph-Structured Debate Trees.

Creates a complete debate graph with:
- One DEBATE on autonomous vehicles
- Four AGENTs (Proponent, Opponent, Judge, Moderator)
- Multiple POSITIONs (Pro, Con)
- A hierarchical ARGUMENT tree with support/refutation relationships

Idempotent: safe to run multiple times. Detects existing data and skips creation.
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

# Check for existing debate to make seed idempotent
def check_existing_debate():
    """Check if debate data already exists."""
    existing = db.records.find({
        "labels": ["DEBATE"],
        "where": {
            "topic": "Should autonomous vehicles replace human drivers?"
        }
    })
    return existing.data if existing else []

def create_debate_graph():
    """Create the complete debate graph structure."""
    print("\n=== Creating Debate Graph ===\n")

    # Create the main debate
    debate = db.records.create(
        label="DEBATE",
        data={
            "topic": "Should autonomous vehicles replace human drivers?",
            "description": "A deliberation on the safety, ethics, and economic implications of autonomous vehicle adoption",
            "status": "active"
        }
    )
    print(f"Created DEBATE: {debate.id}")

    # Create agents with different roles
    agents = {}
    agent_defs = [
        ("PROPONENT", "Alex Chen", "Advocate for autonomous vehicle adoption based on safety and efficiency data"),
        ("OPPONENT", "Jordan Rivera", "Skeptic concerned with job displacement and edge case failures"),
        ("JUDGE", "Dr. Samira Okonkwo", "Neutral arbiter evaluating argument quality and evidence"),
        ("MODERATOR", "Chris Park", "Facilitates discussion and tracks rule violations")
    ]

    for role, name, bio in agent_defs:
        agent = db.records.create(
            label="AGENT",
            data={
                "name": name,
                "role": role,
                "bio": bio
            }
        )
        agents[role] = agent
        print(f"  Created AGENT: {name} ({role})")

        # Link agent to debate
        db.records.attach(
            source=agent,
            target=debate,
            options={"type": "PARTICIPATES_AS", "direction": "out"}
        )

    # Create positions
    positions = {}
    position_defs = [
        ("PRO", agents["PROPONENT"], "In favor of autonomous vehicle adoption"),
        ("CON", agents["OPPONENT"], "Against autonomous vehicle adoption")
    ]

    for pos_label, agent, description in position_defs:
        position = db.records.create(
            label="POSITION",
            data={
                "stance": pos_label,
                "description": description
            }
        )
        positions[pos_label] = position
        print(f"  Created POSITION: {pos_label}")

        # Link position to debate and agent
        db.records.attach(source=position, target=debate, options={"type": "BELONGS_TO", "direction": "out"})
        db.records.attach(source=agent, target=position, options={"type": "HOLDS", "direction": "out"})

    print("\n  Creating argument tree...")

    # Argument tree structure:
    # Root arguments (depth 0) -> Supporting arguments (depth 1) -> Evidence (depth 2)

    arguments = {}

    # === PRO SIDE ARGUMENTS ===

    # Root argument: Safety statistics show autonomous vehicles are safer
    safety_root = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Autonomous vehicles have demonstrated superior safety records compared to human drivers, with 94% of accidents caused by human error.",
            "strength": 0.9,
            "depth": 0,
            "category": "safety"
        }
    )
    arguments["pro_safety_root"] = safety_root
    db.records.attach(source=safety_root, target=positions["PRO"], options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["PROPONENT"], target=safety_root, options={"type": "AUTHORED_BY", "direction": "out"})
    print(f"    Created ARGUMENT (depth 0): Safety statistics")

    # Supporting: Waymo data
    waymo_evidence = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Waymo's 2024 safety report shows 0.19 injuries per million miles compared to 1.47 for human drivers.",
            "strength": 0.95,
            "depth": 1,
            "category": "evidence",
            "source": "Waymo Safety Report 2024"
        }
    )
    arguments["pro_waymo"] = waymo_evidence
    db.records.attach(source=waymo_evidence, target=safety_root, options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["PROPONENT"], target=waymo_evidence, options={"type": "AUTHORED_BY", "direction": "out"})
    print(f"      Created ARGUMENT (depth 1): Waymo evidence")

    # Supporting: Tesla FSD data
    tesla_evidence = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Tesla's FSD Beta shows 76% reduction in collisions after 12 months of usage.",
            "strength": 0.85,
            "depth": 1,
            "category": "evidence",
            "source": "Tesla Safety Analysis Q4 2023"
        }
    )
    arguments["pro_tesla"] = tesla_evidence
    db.records.attach(source=tesla_evidence, target=safety_root, options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["PROPONENT"], target=tesla_evidence, options={"type": "AUTHORED_BY", "direction": "out"})

    # Root argument: Economic benefits
    economic_root = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Autonomous vehicles will create net economic benefits through reduced insurance costs, optimized routing, and increased productivity during commutes.",
            "strength": 0.8,
            "depth": 0,
            "category": "economic"
        }
    )
    arguments["pro_economic_root"] = economic_root
    db.records.attach(source=economic_root, target=positions["PRO"], options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["PROPONENT"], target=economic_root, options={"type": "AUTHORED_BY", "direction": "out"})
    print(f"    Created ARGUMENT (depth 0): Economic benefits")

    # Supporting: Insurance cost reduction
    insurance_evidence = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Industry analysis projects 40% reduction in auto insurance premiums with full autonomous adoption.",
            "strength": 0.75,
            "depth": 1,
            "category": "evidence"
        }
    )
    arguments["pro_insurance"] = insurance_evidence
    db.records.attach(source=insurance_evidence, target=economic_root, options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["PROPONENT"], target=insurance_evidence, options={"type": "AUTHORED_BY", "direction": "out"})

    # === OPPONENT ARGUMENTS ===

    # Root argument: Job displacement
    jobs_root = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Autonomous vehicles will displace 4.3 million professional drivers in the US alone, causing massive economic disruption to working-class communities.",
            "strength": 0.85,
            "depth": 0,
            "category": "social"
        }
    )
    arguments["con_jobs_root"] = jobs_root
    db.records.attach(source=jobs_root, target=positions["CON"], options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["OPPONENT"], target=jobs_root, options={"type": "AUTHORED_BY", "direction": "out"})
    print(f"    Created ARGUMENT (depth 0): Job displacement")

    # Supporting: Trucking industry data
    trucking_evidence = db.records.create(
        label="ARGUMENT",
        data={
            "text": "The American Trucking Associations reports 3.5 million truck drivers, representing 1.7% of all employed Americans.",
            "strength": 0.9,
            "depth": 1,
            "category": "evidence"
        }
    )
    arguments["con_trucking"] = trucking_evidence
    db.records.attach(source=trucking_evidence, target=jobs_root, options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["OPPONENT"], target=trucking_evidence, options={"type": "AUTHORED_BY", "direction": "out"})
    print(f"      Created ARGUMENT (depth 1): Trucking evidence")

    # Root argument: Edge case failures
    edge_case_root = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Current autonomous systems fail catastrophically in edge cases that human drivers handle routinely, making them unsafe for public roads.",
            "strength": 0.8,
            "depth": 0,
            "category": "safety"
        }
    )
    arguments["con_edge_root"] = edge_case_root
    db.records.attach(source=edge_case_root, target=positions["CON"], options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["OPPONENT"], target=edge_case_root, options={"type": "AUTHORED_BY", "direction": "out"})
    print(f"    Created ARGUMENT (depth 0): Edge case failures")

    # Supporting: Specific incident
    incident_evidence = db.records.create(
        label="ARGUMENT",
        data={
            "text": "The 2023 Cruise robotaxi incident in San Francisco demonstrated how autonomous systems can freeze in ambiguous situations, blocking emergency vehicles.",
            "strength": 0.75,
            "depth": 1,
            "category": "evidence",
            "source": "SF DMV Investigation Report"
        }
    )
    arguments["con_incident"] = incident_evidence
    db.records.attach(source=incident_evidence, target=edge_case_root, options={"type": "SUPPORTS", "direction": "out"})
    db.records.attach(source=agents["OPPONENT"], target=incident_evidence, options={"type": "AUTHORED_BY", "direction": "out"})

    # === CROSS-REFERENCES: Proponent refutes Opponent ===

    # Proponent responds to job displacement
    response_to_jobs = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Historical data from the agricultural and manufacturing revolutions shows that technological displacement creates more jobs than it eliminates, with roles shifting to supervision and maintenance.",
            "strength": 0.78,
            "depth": 0,
            "category": "counter"
        }
    )
    arguments["pro_counter_jobs"] = response_to_jobs
    db.records.attach(source=response_to_jobs, target=jobs_root, options={"type": "REFUTES", "direction": "out"})
    db.records.attach(source=agents["PROPONENT"], target=response_to_jobs, options={"type": "AUTHORED_BY", "direction": "out"})
    print(f"    Created ARGUMENT (cross-ref): Proponent refutes job displacement")

    # Proponent responds to edge cases
    response_to_edge = db.records.create(
        label="ARGUMENT",
        data={
            "text": "The incident cited was a fleet management failure, not an autonomous system failure. Waymo's geofenced approach shows the technology can be deployed safely.",
            "strength": 0.72,
            "depth": 0,
            "category": "counter"
        }
    )
    arguments["pro_counter_edge"] = response_to_edge
    db.records.attach(source=response_to_edge, target=edge_case_root, options={"type": "REFUTES", "direction": "out"})
    db.records.attach(source=agents["PROPONENT"], target=response_to_edge, options={"type": "AUTHORED_BY", "direction": "out"})

    # === CROSS-REFERENCES: Opponent refutes Proponent ===

    # Opponent responds to safety statistics
    rebuttal_safety = db.records.create(
        label="ARGUMENT",
        data={
            "text": "The Waymo data covers geofenced, optimally-mapped routes. Generalizing to all road conditions is statistically invalid — comparing apples to orchards.",
            "strength": 0.82,
            "depth": 0,
            "category": "counter"
        }
    )
    arguments["con_rebuttal_safety"] = rebuttal_safety
    db.records.attach(source=rebuttal_safety, target=safety_root, options={"type": "REFUTES", "direction": "out"})
    db.records.attach(source=agents["OPPONENT"], target=rebuttal_safety, options={"type": "AUTHORED_BY", "direction": "out"})
    print(f"    Created ARGUMENT (cross-ref): Opponent refutes safety claim")

    # Opponent responds to economic claims
    rebuttal_economic = db.records.create(
        label="ARGUMENT",
        data={
            "text": "Insurance cost reductions ignore the massive infrastructure investment required, including dedicated lanes, smart roads, and V2X communication systems.",
            "strength": 0.7,
            "depth": 0,
            "category": "counter"
        }
    )
    arguments["con_rebuttal_economic"] = rebuttal_economic
    db.records.attach(source=rebuttal_economic, target=economic_root, options={"type": "REFUTES", "direction": "out"})
    db.records.attach(source=agents["OPPONENT"], target=rebuttal_economic, options={"type": "AUTHORED_BY", "direction": "out"})

    # === JUDGE EVALUATIONS ===

    # Judge evaluates safety argument
    judge_eval_safety = db.records.create(
        label="EVALUATION",
        data={
            "score": 0.85,
            "notes": "Well-sourced claim with specific data points. Deduction for generalization beyond study scope.",
            "category": "evidence_quality"
        }
    )
    db.records.attach(source=judge_eval_safety, target=safety_root, options={"type": "EVALUATES", "direction": "out"})
    db.records.attach(source=agents["JUDGE"], target=judge_eval_safety, options={"type": "AUTHORED_BY", "direction": "out"})

    # Judge evaluates job displacement
    judge_eval_jobs = db.records.create(
        label="EVALUATION",
        data={
            "score": 0.9,
            "notes": "Strong historical parallel. Minor deduction for not addressing retraining timeline.",
            "category": "logic_coherence"
        }
    )
    db.records.attach(source=judge_eval_jobs, target=jobs_root, options={"type": "EVALUATES", "direction": "out"})
    db.records.attach(source=agents["JUDGE"], target=judge_eval_jobs, options={"type": "AUTHORED_BY", "direction": "out"})

    print("\n✓ Debate graph created successfully!")
    return debate


def main():
    print("=" * 60)
    print("Graph-Structured Debate Trees - Data Seeding")
    print("=" * 60)

    # Check for existing data
    existing = check_existing_debate()
    if existing:
        print(f"\n✓ Found existing debate with {len(existing)} record(s)")
        print("  Skipping seed - data already exists (idempotent)")
        print("  To re-seed, delete existing debate records first")
    else:
        create_debate_graph()

    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("Run `python main.py` to explore the debate graph")
    print("=" * 60)


if __name__ == "__main__":
    main()
