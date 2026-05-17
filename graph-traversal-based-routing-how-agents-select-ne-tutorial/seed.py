"""
Seed script for Graph-Traversal-Based Routing demo.

Creates a sample agent routing graph with:
- States: IDLE, RESEARCHING, WRITING, REVIEWING, COMPLETE
- Tasks: Various tasks with priorities and dependencies
- Actions: Available actions with preconditions and outcomes
- Relationships linking everything together

This script is idempotent - running it twice will clear existing data and reseed.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB


def clear_existing_data(db: RushDB) -> None:
    """Remove all records used in this demo to ensure clean state."""
    print("Clearing existing demo data...")
    
    # Delete in reverse dependency order to avoid constraint issues
    labels_to_clear = ["ACTION_EXECUTION", "TASK", "ACTION", "STATE", "AGENT", "PROJECT"]
    
    for label in labels_to_clear:
        result = db.records.find({"labels": [label], "limit": 1000})
        if result.data:
            ids = [record.id for record in result.data]
            # Delete in batches
            for i in range(0, len(ids), 50):
                batch = ids[i:i + 50]
                try:
                    db.records.delete_many({"labels": [label], "where": {"__id": {"$in": batch}}})
                except Exception:
                    pass  # Some may already be deleted
    
    print("Existing data cleared.")


def seed_graph(db: RushDB) -> dict:
    """Create the agent routing graph and return references to key nodes."""
    print("\nSeeding graph...")
    
    # ============================================
    # Create States
    # ============================================
    print("  Creating states...")
    
    states = {}
    state_definitions = [
        {"name": "IDLE", "description": "Agent is waiting for tasks"},
        {"name": "RESEARCHING", "description": "Agent is gathering information"},
        {"name": "WRITING", "description": "Agent is composing content"},
        {"name": "REVIEWING", "description": "Agent is checking and refining"},
        {"name": "COMPLETE", "description": "Task has been completed"},
    ]
    
    for i, state_def in enumerate(state_definitions):
        state = db.records.create(label="STATE", data=state_def)
        states[state_def["name"]] = state
        if (i + 1) % 100 == 0:
            print(f"    Created {i + 1} states...")
    
    print(f"    Created {len(states)} states")
    
    # ============================================
    # Create Project
    # ============================================
    print("  Creating project...")
    
    project = db.records.create(label="PROJECT", data={
        "name": "Q4 Product Launch",
        "deadline": "2026-03-15",
        "priority": "high"
    })
    
    # ============================================
    # Create Agent
    # ============================================
    print("  Creating agent...")
    
    agent = db.records.create(label="AGENT", data={
        "name": "research_agent",
        "capabilities": ["research", "writing", "review"],
        "current_state": "IDLE",
        "efficiency_score": 0.85
    })
    
    # Agent starts in IDLE state
    db.records.attach(
        source=agent,
        target=states["IDLE"],
        options={"type": "CURRENTLY_IN", "direction": "out"}
    )
    
    # ============================================
    # Create Actions
    # ============================================
    print("  Creating actions...")
    
    actions = {}
    action_definitions = [
        # IDLE state actions
        {
            "name": "analyze_task",
            "action_type": "analysis",
            "preconditions": ["IDLE"],
            "outcome_state": "IDLE",
            "next_states": ["RESEARCHING", "WRITING"]
        },
        {
            "name": "begin_research",
            "action_type": "research",
            "preconditions": ["IDLE", "RESEARCHING"],
            "outcome_state": "RESEARCHING",
            "next_states": ["WRITING", "REVIEWING"]
        },
        {
            "name": "fetch_context",
            "action_type": "context",
            "preconditions": ["IDLE"],
            "outcome_state": "IDLE",
            "next_states": ["RESEARCHING"]
        },
        # RESEARCHING state actions
        {
            "name": "read_source",
            "action_type": "research",
            "preconditions": ["RESEARCHING"],
            "outcome_state": "RESEARCHING",
            "next_states": ["RESEARCHING", "WRITING"]
        },
        {
            "name": "extract_key_points",
            "action_type": "analysis",
            "preconditions": ["RESEARCHING"],
            "outcome_state": "RESEARCHING",
            "next_states": ["RESEARCHING", "WRITING"]
        },
        {
            "name": "synthesize_findings",
            "action_type": "synthesis",
            "preconditions": ["RESEARCHING"],
            "outcome_state": "WRITING",
            "next_states": ["WRITING", "REVIEWING"]
        },
        # WRITING state actions
        {
            "name": "draft_content",
            "action_type": "writing",
            "preconditions": ["WRITING"],
            "outcome_state": "WRITING",
            "next_states": ["WRITING", "REVIEWING"]
        },
        {
            "name": "revise_draft",
            "action_type": "writing",
            "preconditions": ["WRITING", "REVIEWING"],
            "outcome_state": "WRITING",
            "next_states": ["WRITING", "REVIEWING"]
        },
        # REVIEWING state actions
        {
            "name": "review_content",
            "action_type": "review",
            "preconditions": ["REVIEWING"],
            "outcome_state": "REVIEWING",
            "next_states": ["WRITING", "COMPLETE"]
        },
        {
            "name": "approve_content",
            "action_type": "approval",
            "preconditions": ["REVIEWING"],
            "outcome_state": "COMPLETE",
            "next_states": ["COMPLETE"]
        },
        # COMPLETE state actions
        {
            "name": "archive_task",
            "action_type": "cleanup",
            "preconditions": ["COMPLETE"],
            "outcome_state": "IDLE",
            "next_states": ["IDLE"]
        },
    ]
    
    for i, action_def in enumerate(action_definitions):
        preconditions = action_def.pop("preconditions")
        outcome_state = action_def.pop("outcome_state")
        next_states = action_def.pop("next_states")
        
        action = db.records.create(label="ACTION", data=action_def)
        actions[action_def["name"]] = action
        
        # Link preconditions (which states allow this action)
        for state_name in preconditions:
            db.records.attach(
                source=states[state_name],
                target=action,
                options={"type": "ENABLES", "direction": "out"}
            )
        
        # Link outcome state (what state this action leads to)
        db.records.attach(
            source=action,
            target=states[outcome_state],
            options={"type": "LEADS_TO", "direction": "out"}
        )
        
        # Link next valid states
        for next_state in next_states:
            db.records.attach(
                source=action,
                target=states[next_state],
                options={"type": "CAN_TRANSITION_TO", "direction": "out"}
            )
        
        if (i + 1) % 100 == 0:
            print(f"    Created {i + 1} actions...")
    
    print(f"    Created {len(actions)} actions")
    
    # ============================================
    # Create Tasks
    # ============================================
    print("  Creating tasks...")
    
    tasks = {}
    task_definitions = [
        {
            "name": "research_agent_report",
            "description": "Comprehensive research on market trends",
            "priority": "high",
            "status": "pending",
            "dependencies": []
        },
        {
            "name": "design_ui",
            "description": "Design user interface mockups",
            "priority": "high",
            "status": "pending",
            "dependencies": []
        },
        {
            "name": "build_prototype",
            "description": "Build functional prototype",
            "priority": "medium",
            "status": "pending",
            "dependencies": ["design_ui"]
        },
        {
            "name": "write_tests",
            "description": "Write comprehensive test suite",
            "priority": "medium",
            "status": "pending",
            "dependencies": ["design_ui"]
        },
        {
            "name": "create_documentation",
            "description": "Write technical documentation",
            "priority": "low",
            "status": "pending",
            "dependencies": ["research_agent_report"]
        },
    ]
    
    # First pass: create all tasks
    for i, task_def in enumerate(task_definitions):
        dependencies = task_def.pop("dependencies")
        
        task = db.records.create(label="TASK", data=task_def)
        tasks[task_def["name"]] = task
        
        # Assign to project
        db.records.attach(
            source=project,
            target=task,
            options={"type": "CONTAINS", "direction": "out"}
        )
        
        task_def["dependencies"] = dependencies  # Restore for second pass
    
    # Second pass: create dependencies
    for task_name, task_def in [(n, t) for n, t in [(n, tasks[n].data) for n in tasks]]:
        for dep_name in task_def.get("dependencies", []):
            if dep_name in tasks:
                db.records.attach(
                    source=tasks[task_name],
                    target=tasks[dep_name],
                    options={"type": "BLOCKED_BY", "direction": "out"}
                )
    
    print(f"    Created {len(tasks)} tasks")
    
    # ============================================
    # Assign Tasks to Agent
    # ============================================
    print("  Assigning tasks to agent...")
    
    assigned_tasks = ["research_agent_report", "create_documentation"]
    for task_name in assigned_tasks:
        db.records.attach(
            source=agent,
            target=tasks[task_name],
            options={"type": "ASSIGNED_TO", "direction": "out"}
        )
    
    print(f"    Assigned {len(assigned_tasks)} tasks")
    
    print("\nGraph seeding complete!")
    
    return {
        "states": states,
        "actions": actions,
        "tasks": tasks,
        "agent": agent,
        "project": project
    }


def main():
    """Main entry point for seeding the graph."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    api_url = os.environ.get("RUSHDB_URL")
    
    if not api_key:
        print("ERROR: RUSHDB_API_KEY environment variable not set.")
        print("Please copy .env.example to .env and add your API key.")
        sys.exit(1)
    
    print("=" * 60)
    print("Graph-Traversal-Based Routing - Data Seeder")
    print("=" * 60)
    
    # Initialize RushDB client
    if api_url:
        db = RushDB(api_key, url=api_url)
    else:
        db = RushDB(api_key)
    
    print(f"\nConnected to RushDB")
    
    # Clear and reseed
    clear_existing_data(db)
    graph_data = seed_graph(db)
    
    # Verify the graph
    print("\nVerifying graph integrity...")
    
    agent = graph_data["agent"]
    agent_record = db.records.find_by_id(agent.id)
    print(f"  Agent: {agent_record['name']} (ID: {agent_record.id})")
    print(f"  Current state: {agent_record['current_state']}")
    
    states_count = db.records.find({"labels": ["STATE"], "limit": 100})
    actions_count = db.records.find({"labels": ["ACTION"], "limit": 100})
    tasks_count = db.records.find({"labels": ["TASK"], "limit": 100})
    
    print(f"  States: {states_count.total}")
    print(f"  Actions: {actions_count.total}")
    print(f"  Tasks: {tasks_count.total}")
    
    print("\n" + "=" * 60)
    print("Seeding complete! You can now run `python main.py`")
    print("=" * 60)


if __name__ == "__main__":
    main()
