#!/usr/bin/env python3
"""
Multi-Agent Communication Graphs - Main Demonstration

This script demonstrates key patterns for working with multi-agent
communication graphs in RushDB:

1. Querying agent hierarchies
2. Finding communication patterns
3. Traversing the agent network
4. Analyzing message flows
5. Identifying bottlenecks

Run `python seed.py` first to populate the graph with sample data.
"""

import os
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
or api_key = os.getenv("RUSHDB_TOKEN")

if not api_key:
    raise RuntimeError(
        "RUSHDB_API_KEY not found. "
        "Copy .env.example to .env and add your API key."
    )

db = RushDB(api_key)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'─' * 50}")
    print(f" {title}")
    print(f"{'─' * 50}")


def print_agent(agent, indent=0):
    """Pretty-print an agent record."""
    prefix = "  " * indent
    name = agent.data.get("name", "Unknown")
    role = agent.data.get("role", "unknown")
    caps = agent.data.get("capabilities", [])
    print(f"{prefix}• {name} [{role}]")
    if caps:
        print(f"{prefix}  Capabilities: {', '.join(caps[:3])}")


def demo_network_overview():
    """Display overview of the agent network."""
    print_section("1. Agent Network Overview")
    
    # Get all agents grouped by role
    all_agents = db.records.find({"labels": ["AGENT"]})
    
    coordinators = [a for a in all_agents.data if a.data.get("role") == "coordinator"]
    specialists = [a for a in all_agents.data if a.data.get("role") in ["research", "coding", "planning", "memory"]]
    tools = [a for a in all_agents.data if a.data.get("role") == "tool"]
    
    print(f"\nTotal agents in network: {len(all_agents.data)}")
    print(f"  • Coordinators: {len(coordinators)}")
    print(f"  • Specialists: {len(specialists)}")
    print(f"  • Tools: {len(tools)}")
    
    print("\n📍 Coordinator Hierarchy:")
    for coord in coordinators:
        print_agent(coord)
        
        # Find subordinates
        subordinates = db.records.find({
            "labels": ["AGENT"],
            "where": {
                "COORDINATOR": {"$relation": {"type": "COORDINATES", "direction": "in"}}
            }
        })
        for sub in subordinates.data:
            print_agent(sub, indent=1)


def demo_hierarchical_queries():
    """Query agents by hierarchy relationships."""
    print_section("2. Hierarchical Queries")
    
    # Find all agents that have a coordinator
    print("\n📋 Agents with a coordinator (subordinates):")
    subordinates = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "COORDINATOR": {
                "$relation": {"type": "COORDINATES", "direction": "in"}
            }
        }
    })
    for agent in subordinates.data:
        print_agent(agent)
    
    # Find all agents that use tools
    print("\n🔧 Agents that use tools:")
    tool_users = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "AGENT": {
                "$relation": {"type": "USES_TOOL", "direction": "out"}
            },
            "role": {"$in": ["research", "coding", "planning", "memory"]}
        }
    })
    for agent in tool_users.data:
        print(f"  • {agent.data.get('name')} [{agent.data.get('role')}]")


def demo_communication_patterns():
    """Analyze communication patterns between agents."""
    print_section("3. Communication Pattern Analysis")
    
    # Get all messages
    messages = db.records.find({"labels": ["MESSAGE"]})
    
    # Count by type
    message_types = {}
    for msg in messages.data:
        msg_type = msg.data.get("type", "unknown")
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
    
    print(f"\n📨 Total messages: {len(messages.data)}")
    print("\nMessages by type:")
    for msg_type, count in sorted(message_types.items(), key=lambda x: -x[1]):
        print(f"  • {msg_type}: {count}")
    
    # Count by direction
    outgoing = len([m for m in messages.data if m.data.get("direction") == "outgoing"])
    incoming = len([m for m in messages.data if m.data.get("direction") == "incoming"])
    print(f"\n  Outgoing: {outgoing}")
    print(f"  Incoming: {incoming}")


def demo_path_traversal():
    """Traverse paths through the agent network."""
    print_section("4. Path Traversal: Coordinator → Tool")
    
    # Find a coordinator
    coordinators = db.records.find({
        "labels": ["AGENT"],
        "where": {"role": "coordinator"}
    })
    
    if not coordinators.data:
        print("\n  No coordinators found. Run seed.py first.")
        return
    
    coordinator = coordinators.data[0]
    print(f"\n  Starting from: {coordinator.data.get('name')}")
    
    # Path 1: Coordinator → Specialist (direct communication)
    print("\n  [Path 1] Direct communication links:")
    direct_links = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "AGENT": {
                "$relation": {"type": "COMMUNICATES_WITH", "direction": "in"}
            }
        }
    })
    
    # Find agents that receive communications from coordinator
    # Using the pattern: find agents where (coordinator)-[COMMUNICATES_WITH]->(agent)
    connected = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "AGENT": {
                "$relation": {"type": "COMMUNICATES_WITH", "direction": "in"}
            }
        }
    })
    
    for agent in connected.data[:4]:  # Show first 4
        print(f"    → {agent.data.get('name')}")
    
    # Path 2: Specialist → Tool
    print("\n  [Path 2] Specialist → Tool connections:")
    specialists = db.records.find({
        "labels": ["AGENT"],
        "where": {"role": {"$in": ["research", "coding", "planning", "memory"]}}
    })
    
    for spec in specialists.data[:2]:  # Show first 2
        print(f"\n    {spec.data.get('name')} uses:")
        # Find tools this specialist uses
        tools = db.records.find({
            "labels": ["AGENT"],
            "where": {
                "AGENT": {
                    "$relation": {"type": "USES_TOOL", "direction": "in"}
                }
            }
        })
        for tool in tools.data[:2]:
            print(f"      → {tool.data.get('name')}")


def demo_capability_search():
    """Search agents by their capabilities."""
    print_section("5. Capability-Based Search")
    
    # Find all capability nodes
    capabilities = db.records.find({"labels": ["CAPABILITY"]})
    
    print(f"\n🔍 Total capabilities in network: {len(capabilities.data)}")
    
    # Group by tool type
    by_type = {}
    for cap in capabilities.data:
        cap_type = cap.data.get("tool_type", "generic")
        if cap_type not in by_type:
            by_type[cap_type] = []
        by_type[cap_type].append(cap.data.get("name", "Unknown"))
    
    print("\nCapabilities by type:")
    for cap_type, caps in sorted(by_type.items()):
        print(f"  • {cap_type}: {len(caps)} capabilities")


def demo_bottleneck_detection():
    """Identify potential bottlenecks in the agent network."""
    print_section("6. Bottleneck Detection")
    
    # Get all agents
    all_agents = db.records.find({"labels": ["AGENT"]})
    
    # Find agents that are coordinators (have subordinates)
    coordinators = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "AGENT": {
                "$relation": {"type": "COORDINATES", "direction": "out"}
            }
        }
    })
    
    print("\n⚠️  Potential Bottlenecks (agents with subordinates):")
    
    if coordinators.data:
        coord = coordinators.data[0]
        subordinates = db.records.find({
            "labels": ["AGENT"],
            "where": {
                "COORDINATOR": {
                    "$relation": {"type": "COORDINATES", "direction": "in"}
                }
            }
        })
        print(f"\n  • {coord.data.get('name')} coordinates {len(subordinates.data)} agents")
        if len(subordinates.data) > 3:
            print(f"    ⚠️  High coordination load - may need assistant coordinator")
    
    # Analyze message distribution
    messages = db.records.find({"labels": ["MESSAGE"]})
    
    # Count messages per sender
    sender_counts = {}
    for msg in messages.data:
        sender = msg.data.get("from", "unknown")
        sender_counts[sender] = sender_counts.get(sender, 0) + 1
    
    if sender_counts:
        print("\n  Message distribution:")
        for sender, count in sorted(sender_counts.items(), key=lambda x: -x[1])[:5]:
            indicator = "⚠️" if count > 5 else "  "
            print(f"    {indicator} {sender}: {count} messages")


def demo_agent_status():
    """Query agents by status."""
    print_section("7. Agent Status Analysis")
    
    all_agents = db.records.find({"labels": ["AGENT"]})
    
    # Group by status
    status_counts = {}
    for agent in all_agents.data:
        status = agent.data.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\n📊 Agent Status Distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  • {status}: {count} agents")
    
    # List active agents
    print("\n✅ Currently Active Agents:")
    active = [a for a in all_agents.data if a.data.get("status") == "active"]
    for agent in active[:5]:
        print(f"  • {agent.data.get('name')} ({agent.data.get('role')})")


def main():
    """Main demonstration function."""
    print("\n" + "=" * 50)
    print(" Multi-Agent Communication Graphs")
    print(" Architecture & Implementation Demo")
    print("=" * 50)
    
    # Check if data exists
    all_agents = db.records.find({"labels": ["AGENT"], "limit": 1})
    if len(all_agents.data) == 0:
        print("\n⚠️  No data found. Please run `python seed.py` first to populate the graph.")
        return
    
    # Run all demonstrations
    demo_network_overview()
    demo_hierarchical_queries()
    demo_communication_patterns()
    demo_path_traversal()
    demo_capability_search()
    demo_bottleneck_detection()
    demo_agent_status()
    
    print("\n" + "=" * 50)
    print(" Demo Complete!")
    print("=" * 50)
    print("\n📚 Learn more about RushDB:")
    print("   • Documentation: https://docs.rushdb.com")
    print("   • GitHub: https://github.com/rush-db/examples")


if __name__ == "__main__":
    main()
