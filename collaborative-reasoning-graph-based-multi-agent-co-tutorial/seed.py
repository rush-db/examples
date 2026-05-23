"""
Seed script for collaborative reasoning demo.

This script creates a sample consensus graph with pre-existing
agent identities, reasoning traces, and evidence chains.

Run this before main.py to have historical context, or skip it
to start fresh (main.py will create agents from scratch).

Usage: python seed.py
"""

import os
import random
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHB_API_KEY not found in environment")

db = RushDB(API_KEY)

# Sample diagnostic agents
AGENTS = [
    {"agentId": "agent-alpha", "name": "Agent Alpha", "specialty": "diagnostic", "confidence": 0.9},
    {"agentId": "agent-beta", "name": "Agent Beta", "specialty": "performance", "confidence": 0.85},
    {"agentId": "agent-gamma", "name": "Agent Gamma", "specialty": "security", "confidence": 0.88},
]

# Sample evidence with causal relationships
EVIDENCE_CHAIN = [
    {"evidenceId": "ev-001", "type": "memory_pressure", "severity": 0.8, "description": "High memory utilization detected"},
    {"evidenceId": "ev-002", "type": "swap_activity", "severity": 0.7, "description": "Increased swap file activity"},
    {"evidenceId": "ev-003", "type": "cpu_spike", "severity": 0.6, "description": "CPU usage spike to 95%"},
    {"evidenceId": "ev-004", "type": "response_latency", "severity": 0.9, "description": "Response time increased 3x"},
    {"evidenceId": "ev-005", "type": "security_alert", "severity": 0.75, "description": "Unauthorized access attempt logged"},
]

# Hypotheses agents might propose
HYPOTHESES = [
    {"hypothesisId": "h-001", "type": "memory_leak", "description": "Application memory leak causing pressure", "initial_support": 0},
    {"hypothesisId": "h-002", "type": "disk_io_bottleneck", "description": "Disk I/O bottleneck causing slowdowns", "initial_support": 0},
    {"hypothesisId": "h-003", "type": "security_breach", "description": "Security incident causing system stress", "initial_support": 0},
]


def seed_agents():
    """Create agent identity records."""
    print("[1] Seeding Agent Identities...")
    created_agents = []
    
    for agent_data in AGENTS:
        # Check if agent already exists
        existing = db.records.find({
            "labels": ["AGENT"],
            "where": {"agentId": agent_data["agentId"]}
        })
        
        if existing.data:
            print(f"    → {agent_data['name']} already exists, skipping")
            created_agents.append(existing.data[0])
        else:
            agent = db.records.create(
                label="AGENT",
                data=agent_data
            )
            created_agents.append(agent)
            print(f"    ✓ Created {agent_data['name']}")
    
    return created_agents


def seed_evidence(agents):
    """Create evidence records and link them in causal chains."""
    print("[2] Seeding Evidence Chain...")
    evidence_records = []
    
    for ev_data in EVIDENCE_CHAIN:
        existing = db.records.find({
            "labels": ["EVIDENCE"],
            "where": {"evidenceId": ev_data["evidenceId"]}
        })
        
        if existing.data:
            print(f"    → Evidence {ev_data['evidenceId']} exists, skipping")
            evidence_records.append(existing.data[0])
        else:
            evidence = db.records.create(
                label="EVIDENCE",
                data=ev_data
            )
            evidence_records.append(evidence)
            print(f"    ✓ Created evidence: {ev_data['type']}")
    
    # Create causal relationships between evidence
    print("[3] Creating causal links...")
    for i in range(len(evidence_records) - 1):
        source = evidence_records[i]
        target = evidence_records[i + 1]
        
        # Link to a random agent as the discoverer
        discoverer = random.choice(agents)
        db.records.attach(
            source=source,
            target=discoverer,
            options={"type": "DISCOVERED_BY"}
        )
        
        # Link evidence causally
        db.records.attach(
            source=source,
            target=target,
            options={"type": "CAUSES"}
        )
        
        print(f"    ✓ Linked: {source.data['type']} → {target.data['type']}")
    
    return evidence_records


def seed_hypotheses(agents, evidence_records):
    """Create hypotheses with agent support votes."""
    print("[4] Seeding Hypotheses and Votes...")
    
    for hyp_data in HYPOTHESES:
        existing = db.records.find({
            "labels": ["HYPOTHESIS"],
            "where": {"hypothesisId": hyp_data["hypothesisId"]}
        })
        
        if existing.data:
            print(f"    → Hypothesis {hyp_data['hypothesisId']} exists, skipping")
            continue
            
        hypothesis = db.records.create(
            label="HYPOTHESIS",
            data=hyp_data
        )
        
        # Randomly assign support votes from agents
        supporting_agents = random.sample(agents, random.randint(1, len(agents)))
        
        for agent in supporting_agents:
            vote = db.records.create(
                label="VOTE",
                data={
                    "voterId": agent.data["agentId"],
                    "weight": random.uniform(0.5, 1.0),
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            )
            
            db.records.attach(
                source=agent,
                target=vote,
                options={"type": "CASTS"}
            )
            db.records.attach(
                source=vote,
                target=hypothesis,
                options={"type": "SUPPORTS"}
            )
            
            print(f"    ✓ {agent.data['name']} supports {hyp_data['type']}")
        
        # Link hypothesis to relevant evidence
        relevant_evidence = random.sample(evidence_records, 2)
        for ev in relevant_evidence:
            db.records.attach(
                source=ev,
                target=hypothesis,
                options={"type": "SUPPORTS"}
            )


def main():
    print("=" * 60)
    print("Collaborative Reasoning: Seeding Database")
    print("=" * 60)
    print()
    
    agents = seed_agents()
    print()
    
    evidence = seed_evidence(agents)
    print()
    
    seed_hypotheses(agents, evidence)
    print()
    
    print("=" * 60)
    print("Seeding complete! Run 'python main.py' to explore the graph.")
    print("=" * 60)


if __name__ == "__main__":
    main()
