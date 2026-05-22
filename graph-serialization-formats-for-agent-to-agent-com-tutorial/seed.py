"""
Seed script for agent-to-agent communication graph data.

This script creates a realistic multi-agent system with:
- Agent profiles (with capabilities and status)
- Messages exchanged between agents
- Shared context and knowledge artifacts
- Intent chains showing agent reasoning

Run this once before executing main.py to populate the database.
"""

import os
import random
from dotenv import load_dotenv
from faker import Faker
from rushdb import RushDB

load_dotenv()

fake = Faker()
Faker.seed(42)
random.seed(42)

AGENT_NAMES = [
    "Orchestrator", "Research", "Coder", "Reviewer", "Deployer"
]

AGENT_CAPABILITIES = {
    "Orchestrator": ["planning", "delegation", "coordination"],
    "Research": ["web_search", "data_analysis", "fact_checking"],
    "Coder": ["code_generation", "refactoring", "debugging"],
    "Reviewer": ["code_review", "testing", "quality_assurance"],
    "Deployer": ["ci_cd", "infrastructure", "monitoring"]
}

MESSAGE_TYPES = ["request", "response", "notification", "status_update"]
INTENT_TYPES = ["gather_info", "execute_task", "validate_result", "coordinate"]


def check_data_exists(db: RushDB) -> bool:
    """Check if we already have agent data seeded."""
    result = db.records.find({
        "labels": ["AGENT"],
        "limit": 1
    })
    return len(result.data) > 0


def create_agents(db: RushDB) -> list:
    """Create agent profile records."""
    print("Creating agent profiles...")
    agents = []
    
    for name in AGENT_NAMES:
        agent = db.records.create(
            label="AGENT",
            data={
                "name": name,
                "status": random.choice(["idle", "busy", "available"]),
                "capabilities": AGENT_CAPABILITIES[name],
                "version": "1.0.0",
                "last_heartbeat": fake.iso8601()
            }
        )
        agents.append(agent)
        print(f"  Created agent: {name}")
    
    return agents


def create_messages(db: RushDB, agents: list) -> list:
    """Create message records between agents."""
    print("Creating inter-agent messages...")
    messages = []
    
    # Generate 30 realistic messages
    for i in range(30):
        sender = random.choice(agents)
        # Avoid self-messaging
        receivers = [a for a in agents if a.id != sender.id]
        receiver = random.choice(receivers)
        
        message = db.records.create(
            label="MESSAGE",
            data={
                "type": random.choice(MESSAGE_TYPES),
                "subject": fake.sentence(nb_words=6),
                "body": fake.paragraph(nb_sentences=3),
                "priority": random.choice(["low", "medium", "high"]),
                "timestamp": fake.iso8601(),
                "read": random.choice([True, False])
            }
        )
        messages.append(message)
        
        # Attach sender relationship
        db.records.attach(
            source=sender,
            target=message,
            options={"type": "SENT", "direction": "out"}
        )
        
        # Attach receiver relationship
        db.records.attach(
            source=receiver,
            target=message,
            options={"type": "RECEIVED", "direction": "out"}
        )
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} messages...")
    
    return messages


def create_intents(db: RushDB, agents: list) -> list:
    """Create intent chains showing agent reasoning."""
    print("Creating intent chains...")
    intents = []
    
    for i in range(20):
        agent = random.choice(agents)
        
        intent = db.records.create(
            label="INTENT",
            data={
                "type": random.choice(INTENT_TYPES),
                "description": fake.sentence(nb_words=8),
                "confidence": round(random.uniform(0.5, 1.0), 2),
                "created_at": fake.iso8601()
            }
        )
        intents.append(intent)
        
        db.records.attach(
            source=agent,
            target=intent,
            options={"type": "GENERATED", "direction": "out"}
        )
    
    print(f"  Created {len(intents)} intents")
    return intents


def create_knowledge_artifacts(db: RushDB, agents: list) -> list:
    """Create shared knowledge/context artifacts."""
    print("Creating knowledge artifacts...")
    artifacts = []
    
    artifact_data = [
        {
            "name": "Project Requirements",
            "type": "documentation",
            "content": "Build a scalable microservices architecture with async communication."
        },
        {
            "name": "Architecture Decision",
            "type": "decision",
            "content": "Use event-driven patterns with message queues for service decoupling."
        },
        {
            "name": "Code Review Guidelines",
            "type": "guideline",
            "content": "All PRs require at least 2 approvals and passing CI/CD pipeline."
        },
        {
            "name": "Deployment Runbook",
            "type": "procedure",
            "content": "Staged rollout: 5% -> 25% -> 50% -> 100% with monitoring."
        },
        {
            "name": "Error Handling Policy",
            "type": "policy",
            "content": "Implement circuit breakers with exponential backoff retry strategy."
        }
    ]
    
    for data in artifact_data:
        artifact = db.records.create(
            label="ARTIFACT",
            data=data
        )
        artifacts.append(artifact)
        
        # Link to 1-2 agents
        linked_agents = random.sample(agents, min(2, len(agents)))
        for agent in linked_agents:
            db.records.attach(
                source=agent,
                target=artifact,
                options={"type": "AUTHORED", "direction": "out"}
            )
    
    print(f"  Created {len(artifacts)} artifacts")
    return artifacts


def create_context_chains(db: RushDB, agents: list):
    """Create context chains linking related data."""
    print("Creating context chains...")
    
    # Find agents with intents
    for agent in agents:
        intents = db.records.find({
            "labels": ["INTENT"],
            "where": {
                "AGENT": {"$id": {"$in": [agent.id]}}
            },
            "limit": 5
        })
        
        # Link intents as context chain
        intent_list = list(intents.data)
        for i in range(len(intent_list) - 1):
            db.records.attach(
                source=intent_list[i],
                target=intent_list[i + 1],
                options={"type": "FOLLOWS", "direction": "out"}
            )
    
    print("  Context chains created")


def main():
    """Main seed function."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        return
    
    print("\n=== RushDB Agent Communication Graph Seeder ===\n")
    
    with RushDB(api_key) as db:
        # Check if data already exists
        if check_data_exists(db):
            print("Data already seeded. Skipping...")
            agents = db.records.find({"labels": ["AGENT"], "limit": 10}).data
            print(f"Found {len(agents)} existing agents")
            return
        
        # Create graph structure
        agents = create_agents(db)
        messages = create_messages(db, agents)
        intents = create_intents(db, agents)
        artifacts = create_knowledge_artifacts(db, agents)
        create_context_chains(db, agents)
        
        print("\n=== Seeding Complete ===")
        print(f"Created {len(agents)} agents")
        print(f"Created {len(messages)} messages")
        print(f"Created {len(intents)} intents")
        print(f"Created {len(artifacts)} artifacts")
        print(f"Total relationships established")


if __name__ == "__main__":
    main()
