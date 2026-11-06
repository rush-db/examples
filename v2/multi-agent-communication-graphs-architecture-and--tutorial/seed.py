#!/usr/bin/env python3
"""
Multi-Agent Communication Graphs - Data Seeder

Creates a realistic multi-agent system with:
- Coordinator agent at the top
- Specialist agents (research, coding, planning)
- Tool agents (web fetch, code execution, memory store)
- Communication links between agents
- Sample message records

Run this script before main.py to populate the graph.
Idempotent: safe to run multiple times (checks for existing data).
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
or api_key = os.getenv("RUSHDB_TOKEN")  # Alternative env var name

if not api_key:
    raise RuntimeError(
        "RUSHDB_API_KEY not found in environment. "
        "Copy .env.example to .env and add your API key."
    )

db = RushDB(api_key)


def check_existing_data():
    """Check if data already exists to avoid duplicates."""
    result = db.records.find({"labels": ["AGENT"], "limit": 1})
    return len(result.data) > 0


def create_coordinator_agent():
    """Create the main coordinator agent."""
    coordinator = db.records.create(
        label="AGENT",
        data={
            "name": "Main Coordinator",
            "role": "coordinator",
            "capabilities": ["task_planning", "agent_orchestration", "result_aggregation"],
            "status": "active",
            "max_concurrent_tasks": 5
        }
    )
    return coordinator


def create_specialist_agents(coordinator):
    """Create specialist agents and link them to coordinator."""
    specialists = []
    
    specialist_configs = [
        {
            "name": "Research Agent",
            "role": "research",
            "capabilities": ["web_search", "document_analysis", "fact_checking"],
            "status": "active"
        },
        {
            "name": "Coding Agent",
            "role": "coding",
            "capabilities": ["code_generation", "code_review", "testing"],
            "status": "active"
        },
        {
            "name": "Planning Agent",
            "role": "planning",
            "capabilities": ["task_decomposition", "dependency_analysis", "scheduling"],
            "status": "active"
        },
        {
            "name": "Memory Agent",
            "role": "memory",
            "capabilities": ["knowledge_storage", "context_retrieval", "history_analysis"],
            "status": "active"
        }
    ]
    
    for config in specialist_configs:
        agent = db.records.create(label="AGENT", data=config)
        specialists.append(agent)
        
        # Link to coordinator
        db.records.attach(
            source=coordinator,
            target=agent,
            options={"type": "COORDINATES", "direction": "out"}
        )
        print(f"  Created specialist: {config['name']}")
    
    return specialists


def create_tool_agents(specialists):
    """Create tool agents and link them to specialists."""
    tools = []
    
    tool_configs = [
        # Research tools
        {
            "name": "Web Fetch Tool",
            "role": "tool",
            "tool_type": "web_fetch",
            "capabilities": ["http_get", "html_parsing", "content_extraction"],
            "linked_specialist": specialists[0]  # Research Agent
        },
        {
            "name": "Search API Tool",
            "role": "tool",
            "tool_type": "search_api",
            "capabilities": ["query_execution", "result_ranking"],
            "linked_specialist": specialists[0]  # Research Agent
        },
        
        # Coding tools
        {
            "name": "Code Executor Tool",
            "role": "tool",
            "tool_type": "code_executor",
            "capabilities": ["python_execution", "sandboxed_run", "output_capture"],
            "linked_specialist": specialists[1]  # Coding Agent
        },
        {
            "name": "Test Runner Tool",
            "role": "tool",
            "tool_type": "test_runner",
            "capabilities": ["unit_tests", "integration_tests", "coverage_reporting"],
            "linked_specialist": specialists[1]  # Coding Agent
        },
        
        # Planning tools
        {
            "name": "Scheduler Tool",
            "role": "tool",
            "tool_type": "scheduler",
            "capabilities": ["task_scheduling", "priority_queue", "deadline_tracking"],
            "linked_specialist": specialists[2]  # Planning Agent
        },
        
        # Memory tools
        {
            "name": "Vector Store Tool",
            "role": "tool",
            "tool_type": "vector_store",
            "capabilities": ["embedding_storage", "similarity_search", "retrieval"],
            "linked_specialist": specialists[3]  # Memory Agent
        }
    ]
    
    for config in tool_configs:
        specialist = config.pop("linked_specialist")
        
        tool = db.records.create(label="AGENT", data=config)
        tools.append(tool)
        
        # Link to specialist
        db.records.attach(
            source=specialist,
            target=tool,
            options={"type": "USES_TOOL", "direction": "out"}
        )
        
        # Create capability node
        capability = db.records.create(
            label="CAPABILITY",
            data={
                "name": f"{config['name']} Capability",
                "tool_type": config.get("tool_type", "generic"),
                "provided_by": config["name"]
            }
        )
        
        db.records.attach(
            source=tool,
            target=capability,
            options={"type": "PROVIDES_CAPABILITY", "direction": "out"}
        )
        
        print(f"  Created tool: {config['name']}")
    
    return tools


def create_communication_links(coordinator, specialists, tools):
    """Create communication relationships between all agents."""
    print("\n  Creating communication links...")
    
    # Coordinator communicates with all specialists
    for specialist in specialists:
        db.records.attach(
            source=coordinator,
            target=specialist,
            options={"type": "COMMUNICATES_WITH", "direction": "out"}
        )
    
    # Specialists communicate with each other
    specialist_pairs = [
        (specialists[0], specialists[1], "Research informs Coding"),  # Research → Coding
        (specialists[1], specialists[2], "Coding reports to Planning"),  # Coding → Planning
        (specialists[2], specialists[3], "Planning updates Memory"),  # Planning → Memory
        (specialists[3], specialists[0], "Memory supports Research"),  # Memory → Research
    ]
    
    for source, target, description in specialist_pairs:
        db.records.attach(
            source=source,
            target=target,
            options={"type": "COMMUNICATES_WITH", "direction": "out"}
        )
        print(f"    Linked: {source.data['name']} → {target.data['name']}")
    
    # Tools communicate back to their specialists
    for tool in tools:
        # Find which specialist owns this tool
        tool_type = tool.data.get("tool_type", "")
        if "web" in tool_type or "search" in tool_type:
            linked = specialists[0]  # Research
        elif "code" in tool_type or "test" in tool_type:
            linked = specialists[1]  # Coding
        elif "schedule" in tool_type:
            linked = specialists[2]  # Planning
        else:
            linked = specialists[3]  # Memory
        
        db.records.attach(
            source=tool,
            target=linked,
            options={"type": "REPORTS_TO", "direction": "out"}
        )


def create_sample_messages(coordinator, specialists):
    """Create sample message records to demonstrate communication tracking."""
    print("\n  Creating sample messages...")
    
    message_templates = [
        {"type": "task_request", "priority": "high"},
        {"type": "task_request", "priority": "normal"},
        {"type": "status_update", "status": "in_progress"},
        {"type": "status_update", "status": "completed"},
        {"type": "result_delivery", "format": "json"},
        {"type": "error_report", "severity": "low"},
    ]
    
    # Create messages from coordinator to specialists
    for specialist in specialists[:3]:  # First 3 specialists
        for i in range(3):  # 3 messages each
            template = random.choice(message_templates)
            timestamp = datetime.now() - timedelta(minutes=random.randint(1, 60))
            
            message = db.records.create(
                label="MESSAGE",
                data={
                    "type": template["type"],
                    "priority": template.get("priority", "normal"),
                    "status": template.get("status", "delivered"),
                    "timestamp": timestamp.isoformat(),
                    "direction": "outgoing",
                    "from": coordinator.data["name"],
                    "to": specialist.data["name"]
                }
            )
            
            # Link message to sender and receiver
            db.records.attach(
                source=coordinator,
                target=message,
                options={"type": "SENT_MESSAGE", "direction": "out"}
            )
            db.records.attach(
                source=message,
                target=specialist,
                options={"type": "DELIVERED_TO", "direction": "out"}
            )
    
    # Create responses from specialists back to coordinator
    for specialist in specialists[:3]:
        for i in range(2):  # 2 responses each
            template = random.choice(message_templates)
            timestamp = datetime.now() - timedelta(minutes=random.randint(1, 30))
            
            message = db.records.create(
                label="MESSAGE",
                data={
                    "type": "response",
                    "priority": template.get("priority", "normal"),
                    "status": "delivered",
                    "timestamp": timestamp.isoformat(),
                    "direction": "incoming",
                    "from": specialist.data["name"],
                    "to": coordinator.data["name"],
                    "task_id": f"TASK-{random.randint(1000, 9999)}"
                }
            )
            
            db.records.attach(
                source=specialist,
                target=message,
                options={"type": "SENT_MESSAGE", "direction": "out"}
            )
            db.records.attach(
                source=message,
                target=coordinator,
                options={"type": "DELIVERED_TO", "direction": "out"}
            )
    
    print(f"    Created ~25 message records")


def main():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("Multi-Agent Communication Graph - Data Seeder")
    print("=" * 60)
    
    # Check for existing data
    if check_existing_data():
        print("\n⚠️  Data already exists. Skipping seed to avoid duplicates.")
        print("   Delete existing AGENT records if you want to re-seed.")
        return
    
    print("\n📊 Creating agent network...")
    
    # Create coordinator
    print("\n  [1/5] Creating coordinator agent...")
    coordinator = create_coordinator_agent()
    print(f"    Created: {coordinator.data['name']}")
    
    # Create specialists
    print("\n  [2/5] Creating specialist agents...")
    specialists = create_specialist_agents(coordinator)
    
    # Create tools
    print("\n  [3/5] Creating tool agents...")
    tools = create_tool_agents(specialists)
    
    # Create communication links
    print("\n  [4/5] Creating communication network...")
    create_communication_links(coordinator, specialists, tools)
    
    # Create sample messages
    print("\n  [5/5] Creating sample message records...")
    create_sample_messages(coordinator, specialists)
    
    print("\n" + "=" * 60)
    print("✅ Seeding complete! Agent network ready.")
    print("=" * 60)
    
    # Summary
    all_agents = db.records.find({"labels": ["AGENT"]})
    all_messages = db.records.find({"labels": ["MESSAGE"]})
    all_caps = db.records.find({"labels": ["CAPABILITY"]})
    
    print(f"\n📈 Network Summary:")
    print(f"   • {len(all_agents.data)} agents created")
    print(f"   • {len(all_messages.data)} message records")
    print(f"   • {len(all_caps.data)} capability nodes")
    print(f"\n   Run `python main.py` to explore the graph.")


if __name__ == "__main__":
    main()
