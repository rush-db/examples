#!/usr/bin/env python3
"""
Graph-Based Persona Management Tutorial
========================================

This tutorial demonstrates RushDB's graph capabilities for managing
AI agent personas with personality vectors and relationships.

Key concepts:
- Persona records with personality embeddings
- Hierarchical agent relationships (supervisor/agent)
- User-to-agent service assignments
- Graph traversal queries
- Vector similarity search for persona matching
"""

import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(API_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# Tutorial Sections
# ─────────────────────────────────────────────────────────────────────────────

def section_header(number: int, title: str):
    """Print a formatted section header."""
    print(f"\n{'─' * 60}")
    print(f"  [{number}] {title}")
    print(f"{'─' * 60}")


def demo_find_agent_for_user():
    """
    Demo 1: Find an agent assigned to a specific user.
    
    This uses RushDB's graph traversal to follow the SERVICES relationship
    from USER to PERSONA records.
    """
    section_header(1, "Find Agent for User")
    
    # Find the user record
    users = db.records.find({
        "labels": ["USER"],
        "where": {"email": "alice@example.com"},
    })
    
    if users.total == 0:
        print("  No user found. Run `python seed.py` first.")
        return
    
    alice = users.data[0]
    print(f"  User: {alice['name']} <{alice['email']}>")
    
    # Find agents that service this user
    agents = db.records.find({
        "labels": ["PERSONA"],
        "where": {
            "USER": {  # Filter by related USER record
                "email": "alice@example.com"
            }
        },
    })
    
    # RushDB automatically traverses the SERVICES relationship
    # to find PERSONA records connected to the matching USER
    print(f"  Assigned agents: {agents.total}")
    for agent in agents.data:
        print(f"    → {agent['name']} ({agent['type']})")


def demo_traverse_supervisor_chain():
    """
    Demo 2: Traverse the supervisor hierarchy.
    
    Find Manager-Eve's direct reports using the SUPERVISES relationship.
    """
    section_header(2, "Supervisor Chain Traversal")
    
    # Find the manager
    managers = db.records.find({
        "labels": ["PERSONA"],
        "where": {"type": "manager"},
    })
    
    if managers.total == 0:
        print("  No manager found. Run `python seed.py` first.")
        return
    
    eve = managers.data[0]
    print(f"  Manager: {eve['name']}")
    
    # Find people this manager supervises
    reports = db.records.find({
        "labels": ["PERSONA"],
        "where": {
            "PERSONA": {  # Self-referential through SUPERVISES relationship
                "$relation": {"type": "SUPERVISES", "direction": "in"},
                "type": "manager",
            }
        },
    })
    
    # Alternative: find reports by filtering through the manager
    reports_alt = db.records.find({
        "labels": ["PERSONA"],
        "where": {
            "type": {"$ne": "manager"}  # Exclude managers themselves
        },
    })
    
    # Filter to those supervised by Eve
    supervised = [
        r for r in reports_alt.data
        if db.records.find({
            "labels": ["PERSONA"],
            "where": {
                "PERSONA": {
                    "$relation": {"type": "SUPERVISES", "direction": "out"},
                    "name": eve["name"]
                }
            },
        }).total > 0
    ]
    
    print(f"  Direct reports: {len(supervised)}")
    for report in supervised:
        print(f"    → {report['name']} ({report['type']})")


def demo_find_team_members():
    """
    Demo 3: Find all members of a team.
    
    Uses relationship filtering to find PERSONA records with MEMBER_OF
    connection to a specific TEAM.
    """
    section_header(3, "Team Membership Query")
    
    # Find the Customer Success team
    teams = db.records.find({
        "labels": ["TEAM"],
        "where": {"name": "Customer Success"},
    })
    
    if teams.total == 0:
        print("  No team found. Run `python seed.py` first.")
        return
    
    team = teams.data[0]
    print(f"  Team: {team['name']} ({team['department']})")
    
    # Find team members using relationship traversal
    members = db.records.find({
        "labels": ["PERSONA"],
        "where": {
            "TEAM": {
                "$relation": {"type": "MEMBER_OF", "direction": "in"},
                "name": "Customer Success"
            }
        },
    })
    
    print(f"  Members: {members.total}")
    for member in members.data:
        print(f"    → {member['name']} - {member['description'][:50]}...")


def demo_vector_similarity_search():
    """
    Demo 4: Find similar personas using vector similarity.
    
    This demonstrates RushDB's semantic search on personality trait vectors.
    """
    section_header(4, "Vector Similarity Search")
    
    # Example: A user who needs very empathetic, patient support
    # We want to find agents who match this personality profile
    target_traits = [0.9, 0.1, 0.3, 0.2, 0.95]  # High empathy, low assertiveness, patient
    
    print(f"  Searching for persona similar to traits:")
    print(f"    empathy={target_traits[0]}, assertiveness={target_traits[1]}, ")
    print(f"    technical={target_traits[2]}, creativity={target_traits[3]}, patience={target_traits[4]}")
    
    # First, ensure vector index exists
    try:
        results = db.ai.search({
            "propertyName": "personality_traits",
            "queryVector": target_traits,
            "labels": ["PERSONA"],
            "limit": 3,
        })
        
        print(f"\n  Similar personas found: {len(results.data)}")
        for result in results.data:
            score = result.score or 0
            print(f"    → {result['name']} (similarity: {score:.3f})")
            print(f"      Traits: {result.get('traits', {})}")
            
    except Exception as e:
        print(f"  Note: Vector search requires indexed data.")
        print(f"  Run seed.py to create vectors, or use query-based matching.")
        
        # Fallback: Query-based matching
        all_agents = db.records.find({
            "labels": ["PERSONA"],
            "where": {"type": "support"},
        })
        
        print(f"\n  Fallback: Support agents by empathy score")
        for agent in sorted(all_agents.data, key=lambda x: x.get('traits', {}).get('empathy', 0), reverse=True):
            empathy = agent.get('traits', {}).get('empathy', 0)
            print(f"    → {agent['name']} (empathy: {empathy})")


def demo_build_persona_context():
    """
    Demo 5: Build complete persona context for an LLM.
    
    This shows how to construct a rich system prompt context
    by aggregating a persona's properties, relationships, and traits.
    """
    section_header(5, "Build Persona Context for LLM")
    
    # Find Support-Alice
    agents = db.records.find({
        "labels": ["PERSONA"],
        "where": {"name": "Support-Alice"},
    })
    
    if agents.total == 0:
        print("  No persona found. Run `python seed.py` first.")
        return
    
    alice = agents.data[0]
    
    # Find her supervisor
    supervisors = db.records.find({
        "labels": ["PERSONA"],
        "where": {
            "PERSONA": {
                "$relation": {"type": "SUPERVISES", "direction": "in"},
                "name": "Support-Alice"
            }
        },
    })
    
    supervisor_name = supervisors.data[0]["name"] if supervisors.total > 0 else "None"
    
    # Find her team
    teams = db.records.find({
        "labels": ["TEAM"],
        "where": {
            "PERSONA": {
                "$relation": {"type": "MEMBER_OF", "direction": "in"},
                "name": "Support-Alice"
            }
        },
    })
    
    team_name = teams.data[0]["name"] if teams.total > 0 else "None"
    
    # Find users she serves
    served_users = db.records.find({
        "labels": ["USER"],
        "where": {
            "PERSONA": {
                "$relation": {"type": "SERVICES", "direction": "in"},
                "name": "Support-Alice"
            }
        },
    })
    
    # Build context dictionary
    context = {
        "agent_name": alice["name"],
        "agent_type": alice["type"],
        "description": alice["description"],
        "personality_traits": alice["traits"],
        "team": team_name,
        "supervisor": supervisor_name,
        "served_users": [u["name"] for u in served_users.data],
    }
    
    print("  Persona Context for LLM System Prompt:")
    print(f"  ─────────────────────────────────────────")
    print(f"  Agent: {context['agent_name']}")
    print(f"  Role:  {context['agent_type']}")
    print(f"  Team:  {context['team']}")
    print(f"  Reports to: {context['supervisor']}")
    print(f"  Personality: {context['personality_traits']}")
    print(f"  Serves {len(context['served_users'])} users")
    
    # Format as LLM-ready text
    llm_context = f"""
You are {context['agent_name']}, a {context['agent_type']} agent.
Your team is {context['team']} and you report to {context['supervisor']}.

Your personality traits:
- Empathy: {context['personality_traits']['empathy']:.0%}
- Assertiveness: {context['personality_traits']['assertiveness']:.0%}
- Technical depth: {context['personality_traits']['technical']:.0%}
- Creativity: {context['personality_traits']['creativity']:.0%}
- Patience: {context['personality_traits']['patience']:.0%}

You serve: {', '.join(context['served_users'])}

{context['description']}
"""
    
    print(f"\n  LLM System Prompt:")
    print(f"  {llm_context.strip()}")


def demo_escalation_paths():
    """
    Demo 6: Find escalation paths.
    
    When an agent needs to escalate, who can they reach?
    """
    section_header(6, "Escalation Path Discovery")
    
    # Find an agent who can escalate
    agents = db.records.find({
        "labels": ["PERSONA"],
        "where": {"type": "support"},
    })
    
    if agents.total == 0:
        print("  No agents found. Run `python seed.py` first.")
        return
    
    for agent in agents.data[:2]:
        print(f"\n  {agent['name']} can escalate to:")
        
        escalations = db.records.find({
            "labels": ["PERSONA"],
            "where": {
                "PERSONA": {
                    "$relation": {"type": "ESCALATES_TO", "direction": "in"},
                    "name": agent["name"]
                }
            },
        })
        
        for esc in escalations.data:
            print(f"    → {esc['name']} ({esc['type']})")


def demo_list_all_personas():
    """
    Demo 7: List all personas with their traits.
    
    A comprehensive view of the persona graph.
    """
    section_header(7, "All Personas Overview")
    
    personas = db.records.find({
        "labels": ["PERSONA"],
        "orderBy": {"type": "asc"},
    })
    
    print(f"  Total personas: {personas.total}\n")
    
    for persona in personas.data:
        traits = persona.get("traits", {})
        print(f"  {persona['name']} ({persona['type']})")
        print(f"    Empathy:        {'█' * int(traits.get('empathy', 0) * 10)}{'░' * (10 - int(traits.get('empathy', 0) * 10))} {traits.get('empathy', 0):.1f}")
        print(f"    Assertiveness:  {'█' * int(traits.get('assertiveness', 0) * 10)}{'░' * (10 - int(traits.get('assertiveness', 0) * 10))} {traits.get('assertiveness', 0):.1f}")
        print(f"    Technical:       {'█' * int(traits.get('technical', 0) * 10)}{'░' * (10 - int(traits.get('technical', 0) * 10))} {traits.get('technical', 0):.1f}")
        print(f"    Creativity:      {'█' * int(traits.get('creativity', 0) * 10)}{'░' * (10 - int(traits.get('creativity', 0) * 10))} {traits.get('creativity', 0):.1f}")
        print(f"    Patience:       {'█' * int(traits.get('patience', 0) * 10)}{'░' * (10 - int(traits.get('patience', 0) * 10))} {traits.get('patience', 0):.1f}")
        print()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("  Graph-Based Persona Management Tutorial")
    print("  RushDB SDK Demonstration")
    print("=" * 60)
    
    # Run all demos
    demo_list_all_personas()
    demo_find_agent_for_user()
    demo_traverse_supervisor_chain()
    demo_find_team_members()
    demo_vector_similarity_search()
    demo_build_persona_context()
    demo_escalation_paths()
    
    print("\n" + "=" * 60)
    print("  Tutorial Complete!")
    print("  =")
    print("  Key Takeaways:")
    print("  1. Personas are stored as graph nodes with personality vectors")
    print("  2. Relationships enable supervisor hierarchies & team membership")
    print("  3. Graph traversal finds connected personas efficiently")
    print("  4. Vector search matches users to compatible agents")
    print("  5. Context aggregation builds rich LLM prompts from the graph")
    print("=" * 60)


if __name__ == "__main__":
    main()
