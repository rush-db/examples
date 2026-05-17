"""
Seed script for Dynamic Persona Switching tutorial.

Creates sample personas, agents, and initial conversation context
to demonstrate multi-agent persona management with RushDB.

This script is idempotent - safe to run multiple times.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")

if url:
    db = RushDB(api_key, url=url)
else:
    db = RushDB(api_key)

# Sample persona definitions
PERSONAS = [
    {
        "name": "Technical Expert",
        "description": "Deep technical specialist for code, architecture, and system design",
        "traits": {
            "analytical": 0.95,
            "problem_solving": 0.9,
            "creativity": 0.5,
            "verbosity": "detailed"
        },
        "capabilities": ["code_review", "architecture", "debugging", "performance_optimization"],
        "communication_style": "technical",
        "domain": "Software Engineering",
        "active_hours": "24/7"
    },
    {
        "name": "Creative Writer",
        "description": "Creative content generator for marketing, documentation, and storytelling",
        "traits": {
            "creativity": 0.95,
            "empathy": 0.85,
            "analytical": 0.4,
            "verbosity": "expressive"
        },
        "capabilities": ["content_writing", "storytelling", "copywriting", "documentation"],
        "communication_style": "creative",
        "domain": "Content & Marketing",
        "active_hours": "business_hours"
    },
    {
        "name": "Business Analyst",
        "description": "Strategic thinking for business requirements, metrics, and decision making",
        "traits": {
            "analytical": 0.85,
            "strategic": 0.9,
            "communication": 0.85,
            "verbosity": "concise"
        },
        "capabilities": ["requirements", "data_analysis", "reporting", "stakeholder_management"],
        "communication_style": "professional",
        "domain": "Business Operations",
        "active_hours": "business_hours"
    },
    {
        "name": "Support Assistant",
        "description": "Helpful and empathetic support for customer inquiries and troubleshooting",
        "traits": {
            "empathy": 0.95,
            "patience": 0.9,
            "problem_solving": 0.75,
            "verbosity": "friendly"
        },
        "capabilities": ["customer_support", "troubleshooting", "faq_responses", "ticket_management"],
        "communication_style": "friendly",
        "domain": "Customer Success",
        "active_hours": "24/7"
    },
    {
        "name": "Data Scientist",
        "description": "ML/AI specialist for data analysis, modeling, and insights",
        "traits": {
            "analytical": 0.9,
            "mathematical": 0.9,
            "creativity": 0.7,
            "verbosity": "technical"
        },
        "capabilities": ["data_analysis", "machine_learning", "statistical_modeling", "visualization"],
        "communication_style": "technical",
        "domain": "Data Science & ML",
        "active_hours": "flexible"
    }
]

# Sample agent definitions
AGENTS = [
    {
        "name": "assistant-alpha",
        "type": "general-purpose",
        "specialization": ["technical", "support"],
        "max_concurrent_personas": 2,
        "model": "gpt-4-turbo"
    },
    {
        "name": "assistant-beta",
        "type": "specialized",
        "specialization": ["creative", "content"],
        "max_concurrent_personas": 3,
        "model": "gpt-4"
    },
    {
        "name": "assistant-gamma",
        "type": "analytical",
        "specialization": ["data", "business"],
        "max_concurrent_personas": 1,
        "model": "claude-3-opus"
    }
]


def check_existing_data():
    """Check if data already exists to avoid duplicates."""
    existing_personas = db.records.find({"labels": ["PERSONA"], "limit": 1})
    existing_agents = db.records.find({"labels": ["AGENT"], "limit": 1})
    
    return existing_personas.total > 0 or existing_agents.total > 0


def seed_personas():
    """Create persona records in RushDB."""
    print("\n[Seeding Personas]")
    
    created_personas = []
    for i, persona_data in enumerate(PERSONAS):
        # Check if persona already exists
        existing = db.records.find({
            "labels": ["PERSONA"],
            "where": {"name": persona_data["name"]}
        })
        
        if existing.total > 0:
            print(f"  → Persona '{persona_data['name']}' already exists, skipping")
            created_personas.append(existing.data[0])
        else:
            persona = db.records.create(
                label="PERSONA",
                data=persona_data
            )
            created_personas.append(persona)
            print(f"  + Created persona: {persona_data['name']}")
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1} personas...")
    
    return created_personas


def seed_agents():
    """Create agent records in RushDB."""
    print("\n[Seeding Agents]")
    
    created_agents = []
    for agent_data in AGENTS:
        existing = db.records.find({
            "labels": ["AGENT"],
            "where": {"name": agent_data["name"]}
        })
        
        if existing.total > 0:
            print(f"  → Agent '{agent_data['name']}' already exists, skipping")
            created_agents.append(existing.data[0])
        else:
            agent = db.records.create(
                label="AGENT",
                data=agent_data
            )
            created_agents.append(agent)
            print(f"  + Created agent: {agent_data['name']}")
    
    return created_agents


def seed_sample_conversations(personas, agents):
    """Create sample conversations to demonstrate persona switching."""
    print("\n[Seeding Sample Conversations]")
    
    if not personas or not agents:
        print("  ⚠ Skipping conversations: no personas or agents found")
        return
    
    technical_persona = next((p for p in personas if p["name"] == "Technical Expert"), None)
    creative_persona = next((p for p in personas if p["name"] == "Creative Writer"), None)
    support_persona = next((p for p in personas if p["name"] == "Support Assistant"), None)
    agent = agents[0]
    
    if not all([technical_persona, creative_persona, support_persona, agent]):
        print("  ⚠ Skipping conversations: missing personas or agent")
        return
    
    conversations = [
        {
            "agent_name": agent["name"],
            "persona_name": support_persona["name"],
            "topic": "user_onboarding",
            "user_message": "Hi, I just signed up. How do I get started?",
            "response": "Welcome! Let's get you set up. First, complete your profile...",
            "sentiment": "positive",
            "resolution_status": "resolved"
        },
        {
            "agent_name": agent["name"],
            "persona_name": technical_persona["name"],
            "topic": "debugging",
            "user_message": "My code is throwing a null pointer exception",
            "response": "Let me help you debug this. First, check if the variable is initialized...",
            "sentiment": "frustrated",
            "resolution_status": "in_progress"
        },
        {
            "agent_name": agent["name"],
            "persona_name": creative_persona["name"],
            "topic": "content_creation",
            "user_message": "I need a blog post about API design best practices",
            "response": "Great topic! Let me craft an engaging piece that balances technical depth with readability...",
            "sentiment": "neutral",
            "resolution_status": "completed"
        }
    ]
    
    for conv in conversations:
        existing = db.records.find({
            "labels": ["CONVERSATION"],
            "where": {
                "agent_name": conv["agent_name"],
                "topic": conv["topic"]
            }
        })
        
        if existing.total > 0:
            print(f"  → Conversation '{conv['topic']}' already exists, skipping")
        else:
            conversation = db.records.create(
                label="CONVERSATION",
                data=conv
            )
            print(f"  + Created conversation: {conv['topic']}")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Dynamic Persona Switching - Data Seeding")
    print("=" * 60)
    
    # Check for existing data
    if check_existing_data():
        print("\n⚠ Data already exists. Skipping seed to avoid duplicates.")
        print("  To reseed, first delete existing PERSONA and AGENT records.")
        
        # Still try to return existing data for the main script
        personas = db.records.find({"labels": ["PERSONA"]})
        agents = db.records.find({"labels": ["AGENT"]})
        print(f"\nFound {personas.total} personas and {agents.total} agents in database.")
        return
    
    # Seed personas
    personas = seed_personas()
    
    # Seed agents
    agents = seed_agents()
    
    # Seed sample conversations
    seed_sample_conversations(personas, agents)
    
    print("\n" + "=" * 60)
    print("Seeding complete! Run `python main.py` to see the demo.")
    print("=" * 60)


if __name__ == "__main__":
    main()
