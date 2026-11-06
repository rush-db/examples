"""
Dynamic Persona Switching in Multi-Agent Systems

This demo showcases how RushDB can serve as the memory layer for
multi-agent systems that dynamically switch between personas based
on context, task requirements, and conversation flow.

Key features demonstrated:
- Persona creation and management
- Agent-persona relationships via graph edges
- Dynamic switching based on task type
- Context preservation across persona switches
- Conversation history tracking per persona
- State management for active personas
"""

import os
import time
from datetime import datetime, timedelta
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


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_subsection(title):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


# ============================================================================
# SECTION 1: Load Personas and Agents from RushDB
# ============================================================================

def load_personas_and_agents():
    """Load existing personas and agents from RushDB."""
    print_section("1. Loading Personas and Agents from RushDB")
    
    # Fetch all personas
    personas_result = db.records.find({"labels": ["PERSONA"], "limit": 100})
    personas = personas_result.data
    
    print(f"\nFound {len(personas)} personas in RushDB:")
    for persona in personas:
        name = persona.get("name", "Unknown")
        domain = persona.get("domain", "N/A")
        caps = persona.get("capabilities", [])
        print(f"  • {name} ({domain})")
        print(f"    Capabilities: {', '.join(caps)}")
    
    # Fetch all agents
    agents_result = db.records.find({"labels": ["AGENT"], "limit": 100})
    agents = agents_result.data
    
    print(f"\nFound {len(agents)} agents in RushDB:")
    for agent in agents:
        name = agent.get("name", "Unknown")
        agent_type = agent.get("type", "N/A")
        model = agent.get("model", "N/A")
        print(f"  • {name} (type: {agent_type}, model: {model})")
    
    return personas, agents


# ============================================================================
# SECTION 2: Demonstrate Dynamic Persona Switching
# ============================================================================

def demonstrate_persona_switching(agents, personas):
    """Demonstrate dynamic persona switching based on task context."""
    print_section("2. Dynamic Persona Switching Demonstration")
    
    if not agents:
        print("\n⚠ No agents found. Run `python seed.py` first.")
        return
    
    if not personas:
        print("\n⚠ No personas found. Run `python seed.py` first.")
        return
    
    # Select an agent for demonstration
    agent = agents[0]
    print(f"\nSelected agent: {agent['name']}")
    
    # Define task scenarios that trigger persona switches
    task_scenarios = [
        {
            "task": "Write a technical blog post about microservices",
            "required_capability": "content_writing",
            "preferred_persona": "Creative Writer",
            "context": "marketing_blog"
        },
        {
            "task": "Debug a memory leak in the production cluster",
            "required_capability": "debugging",
            "preferred_persona": "Technical Expert",
            "context": "production_incident"
        },
        {
            "task": "Analyze Q4 revenue data and create a report",
            "required_capability": "data_analysis",
            "preferred_persona": "Data Scientist",
            "context": "quarterly_review"
        },
        {
            "task": "Handle customer complaint about billing",
            "required_capability": "customer_support",
            "preferred_persona": "Support Assistant",
            "context": "customer_complaint"
        }
    ]
    
    print_subsection("Task-Based Persona Switching")
    
    # Use a transaction to demonstrate atomic persona switch
    with db.transactions.begin() as tx:
        for i, scenario in enumerate(task_scenarios):
            # Find the appropriate persona
            target_persona = next(
                (p for p in personas if p["name"] == scenario["preferred_persona"]),
                None
            )
            
            if not target_persona:
                print(f"\n⚠ Persona '{scenario['preferred_persona']}' not found, skipping")
                continue
            
            # Create a context record for this task
            context = db.records.create(
                label="TASK_CONTEXT",
                data={
                    "task": scenario["task"],
                    "required_capability": scenario["required_capability"],
                    "context_type": scenario["context"],
                    "started_at": datetime.now().isoformat()
                },
                transaction=tx
            )
            
            # Create persona switch record
            switch_record = db.records.create(
                label="PERSONA_SWITCH",
                data={
                    "from_persona": None,  # First switch, no previous
                    "to_persona": target_persona["name"],
                    "trigger": scenario["context"],
                    "timestamp": datetime.now().isoformat()
                },
                transaction=tx
            )
            
            # Attach switch to agent
            db.records.attach(
                source=agent,
                target=switch_record,
                options={"type": "INITIATED_SWITCH", "direction": "out"},
                transaction=tx
            )
            
            # Attach context to switch
            db.records.attach(
                source=switch_record,
                target=context,
                options={"type": "EXECUTING_TASK", "direction": "out"},
                transaction=tx
            )
            
            print(f"\n  [{i + 1}] Task: {scenario['task'][:50]}...")
            print(f"      Switched to: {target_persona['name']}")
            print(f"      Trigger: {scenario['context']}")
            print(f"      Traits: analytical={target_persona.get('traits', {}).get('analytical', 'N/A')}")
            
            # Small delay to ensure distinct timestamps
            time.sleep(0.1)
    
    print("\n✓ All persona switches recorded in RushDB transaction")


# ============================================================================
# SECTION 3: Track and Query Persona History
# ============================================================================

def demonstrate_persona_history_tracking():
    """Show how to query persona switch history."""
    print_section("3. Persona Switch History Tracking")
    
    # Query all persona switches
    switches = db.records.find({
        "labels": ["PERSONA_SWITCH"],
        "orderBy": {"timestamp": "desc"},
        "limit": 10
    })
    
    print(f"\nFound {switches.total} persona switch records:")
    for switch in switches.data:
        to_persona = switch.get("to_persona", "Unknown")
        trigger = switch.get("trigger", "N/A")
        timestamp = switch.get("timestamp", "N/A")
        print(f"  → Switched to '{to_persona}' (trigger: {trigger}, time: {timestamp})")
    
    # Query task contexts
    contexts = db.records.find({"labels": ["TASK_CONTEXT"]})
    print(f"\nFound {contexts.total} task context records")


# ============================================================================
# SECTION 4: Demonstrate Conversation Context Preservation
# ============================================================================

def demonstrate_conversation_context(personas, agents):
    """Show how conversations maintain persona context across switches."""
    print_section("4. Conversation Context Preservation")
    
    if not agents or not personas:
        print("\n⚠ Skipping: no agents or personas found")
        return
    
    print_subsection("Creating Multi-Persona Conversation")
    
    agent = agents[0]
    
    # Create a conversation that spans multiple personas
    conversation = db.records.create(
        label="CONVERSATION",
        data={
            "title": "Product Launch Discussion",
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
    )
    
    # Attach agent to conversation
    db.records.attach(
        source=agent,
        target=conversation,
        options={"type": "PARTICIPATED_IN", "direction": "out"}
    )
    
    print(f"\n  Created conversation: {conversation['title']}")
    print(f"  Agent: {agent['name']}")
    
    # Add conversation segments with different personas
    segments = [
        {
            "persona": "Support Assistant",
            "message": "Hi! I see you're interested in our enterprise plan.",
            "direction": "outbound"
        },
        {
            "persona": "Business Analyst",
            "message": "Let me prepare the ROI analysis for you.",
            "direction": "outbound"
        },
        {
            "persona": "Technical Expert",
            "message": "Here's how our API integrates with your stack.",
            "direction": "outbound"
        },
        {
            "persona": "Creative Writer",
            "message": "Let me craft a compelling proposal for your team.",
            "direction": "outbound"
        }
    ]
    
    print("\n  Conversation segments:")
    for i, seg in enumerate(segments):
        persona = next((p for p in personas if p["name"] == seg["persona"]), None)
        if not persona:
            continue
            
        segment = db.records.create(
            label="CONVERSATION_SEGMENT",
            data={
                "message": seg["message"],
                "direction": seg["direction"],
                "persona_name": seg["persona"],
                "timestamp": datetime.now().isoformat(),
                "sequence": i + 1
            }
        )
        
        # Attach segment to conversation
        db.records.attach(
            source=conversation,
            target=segment,
            options={"type": "HAS_SEGMENT", "direction": "out"}
        )
        
        # Attach segment to persona
        db.records.attach(
            source=segment,
            target=persona,
            options={"type": "SENT_FROM", "direction": "out"}
        )
        
        print(f"    [{i + 1}] {seg['persona']}: \"{seg['message'][:40]}...\"")
    
    print("\n  ✓ All conversation segments linked to personas")


# ============================================================================
# SECTION 5: Graph Traversal - Find All Conversations for a Persona
# ============================================================================

def demonstrate_graph_traversal(personas):
    """Demonstrate RushDB's graph traversal for finding related data."""
    print_section("5. Graph Traversal - Persona Activity")
    
    if not personas:
        print("\n⚠ Skipping: no personas found")
        return
    
    print_subsection("Finding All Activity for 'Technical Expert' Persona")
    
    # Find the Technical Expert persona
    tech_expert = next((p for p in personas if p["name"] == "Technical Expert"), None)
    if not tech_expert:
        print("\n⚠ Technical Expert persona not found")
        return
    
    # Query conversations involving this persona
    tech_conversations = db.records.find({
        "labels": ["CONVERSATION"],
        "where": {
            "TECH_EXPERT": {"$relation": {"type": "PARTICIPATED_IN", "direction": "in"}}
        }
    })
    
    print(f"\n  Found {tech_conversations.total} conversations involving Technical Expert")
    
    # Query persona switch records
    switch_to_tech = db.records.find({
        "labels": ["PERSONA_SWITCH"],
        "where": {
            "to_persona": "Technical Expert"
        }
    })
    
    print(f"  Found {switch_to_tech.total} persona switches to Technical Expert")
    
    # Query conversation segments from this persona
    tech_segments = db.records.find({
        "labels": ["CONVERSATION_SEGMENT"],
        "where": {
            "persona_name": "Technical Expert"
        }
    })
    
    print(f"  Found {tech_segments.total} conversation segments from Technical Expert")
    
    print_subsection("Agent Activity Summary")
    
    # Get all agents and their switch history
    agents = db.records.find({"labels": ["AGENT"]})
    for agent in agents.data:
        agent_switches = db.records.find({
            "labels": ["PERSONA_SWITCH"],
            "where": {
                "AGENT": {
                    "$relation": {"type": "INITIATED_SWITCH", "direction": "in"},
                    "name": agent["name"]
                }
            }
        })
        print(f"\n  Agent '{agent['name']}':")
        print(f"    Total persona switches: {agent_switches.total}")
        
        if agent_switches.total > 0:
            # Get the current (most recent) persona
            latest_switch = agent_switches.data[0]  # Already ordered desc
            print(f"    Current persona: {latest_switch.get('to_persona', 'Unknown')}")


# ============================================================================
# SECTION 6: Simulate Real-Time Persona Switching
# ============================================================================

def simulate_realtime_switching(agents, personas):
    """Simulate a real-time conversation where persona switches dynamically."""
    print_section("6. Real-Time Persona Switching Simulation")
    
    if not agents or not personas:
        print("\n⚠ Skipping: no agents or personas found")
        return
    
    agent = agents[0]
    
    print_subsection("Multi-Turn Conversation with Dynamic Switching")
    print("\n  (Simulating a user conversation that triggers different personas)")
    
    conversation_turns = [
        {
            "user_input": "I need help with my account setup",
            "detected_intent": "onboarding",
            "expected_persona": "Support Assistant",
            "simulated_response": "Welcome! Let me guide you through the setup process..."
        },
        {
            "user_input": "Actually, can you help me integrate with Slack?",
            "detected_intent": "integration",
            "expected_persona": "Technical Expert",
            "simulated_response": "Our Slack integration uses OAuth 2.0. Here's the setup guide..."
        },
        {
            "user_input": "That sounds great! Can you create a demo video script?",
            "detected_intent": "content_creation",
            "expected_persona": "Creative Writer",
            "simulated_response": "I'd love to help! Let me craft an engaging script for your demo..."
        },
        {
            "user_input": "What analytics will I get from this integration?",
            "detected_intent": "analytics",
            "expected_persona": "Data Scientist",
            "simulated_response": "You'll have access to engagement metrics, conversion rates, and..."
        }
    ]
    
    # Create a transaction for the entire simulation
    with db.transactions.begin() as tx:
        # Create simulation session
        session = db.records.create(
            label="SWITCHING_SESSION",
            data={
                "agent_name": agent["name"],
                "started_at": datetime.now().isoformat(),
                "total_turns": len(conversation_turns)
            },
            transaction=tx
        )
        
        print(f"\n  Created switching session: {session.id}")
        
        for i, turn in enumerate(conversation_turns):
            # Find the target persona
            target_persona = next(
                (p for p in personas if p["name"] == turn["expected_persona"]),
                None
            )
            
            if not target_persona:
                continue
            
            # Create turn record
            turn_record = db.records.create(
                label="CONVERSATION_TURN",
                data={
                    "turn_number": i + 1,
                    "user_input": turn["user_input"],
                    "detected_intent": turn["detected_intent"],
                    "active_persona": turn["expected_persona"],
                    "simulated_response": turn["simulated_response"],
                    "timestamp": datetime.now().isoformat()
                },
                transaction=tx
            )
            
            # Link to session
            db.records.attach(
                source=session,
                target=turn_record,
                options={"type": "CONTAINS_TURN", "direction": "out"},
                transaction=tx
            )
            
            # Link to persona
            db.records.attach(
                source=turn_record,
                target=target_persona,
                options={"type": "RESPONDED_AS", "direction": "out"},
                transaction=tx
            )
            
            print(f"\n  Turn {i + 1}: {turn['detected_intent'].upper()}")
            print(f"    User: {turn['user_input']}")
            print(f"    Persona: {turn['expected_persona']}")
            print(f"    Response: {turn['simulated_response'][:50]}...")
            
            time.sleep(0.05)
    
    print("\n  ✓ Real-time switching simulation complete")


# ============================================================================
# SECTION 7: Query and Display Full Context Graph
# ============================================================================

def display_context_graph():
    """Query and display the complete context graph."""
    print_section("7. Complete Context Graph Overview")
    
    # Query all record counts by label
    labels_to_check = ["PERSONA", "AGENT", "TASK_CONTEXT", "PERSONA_SWITCH", 
                       "CONVERSATION", "CONVERSATION_SEGMENT", "SWITCHING_SESSION", 
                       "CONVERSATION_TURN"]
    
    print("\n  Record counts by label:")
    for label in labels_to_check:
        result = db.records.find({"labels": [label], "limit": 1})
        count = result.total
        print(f"    {label}: {count} records")
    
    # Display ontology
    print_subsection("RushDB Ontology Snapshot")
    try:
        ontology = db.ai.getOntology()
        print(f"\n  Total labels in database: {len(ontology.get('labels', []))}")
        print(f"  Total properties: {len(ontology.get('properties', []))}")
    except Exception as e:
        print(f"  Could not fetch ontology: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main demo function."""
    print("\n" + "=" * 60)
    print(" DYNAMIC PERSONA SWITCHING IN MULTI-AGENT SYSTEMS")
    print(" Using RushDB as the Memory Layer")
    print("=" * 60)
    
    # Load existing data
    personas, agents = load_personas_and_agents()
    
    if not personas and not agents:
        print("\n" + "=" * 60)
        print(" No data found in RushDB.")
        print(" Please run `python seed.py` first to create sample data.")
        print("=" * 60)
        return
    
    # Demonstrate persona switching
    demonstrate_persona_switching(agents, personas)
    
    # Track and query history
    demonstrate_persona_history_tracking()
    
    # Demonstrate conversation context
    demonstrate_conversation_context(personas, agents)
    
    # Demonstrate graph traversal
    demonstrate_graph_traversal(personas)
    
    # Simulate real-time switching
    simulate_realtime_switching(agents, personas)
    
    # Display context graph
    display_context_graph()
    
    print("\n" + "=" * 60)
    print(" DEMO COMPLETE")
    print("=" * 60)
    print("\nYou've seen how RushDB enables:")
    print("  • Structured persona management")
    print("  • Dynamic switching based on task context")
    print("  • Conversation history across personas")
    print("  • Graph-based relationship tracking")
    print("  • Real-time state management")
    print("\nLearn more: https://docs.rushdb.com")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
