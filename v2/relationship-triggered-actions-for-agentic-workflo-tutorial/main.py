"""
Relationship-Triggered Actions for Agentic Workflow Automation
=================================================================

This module demonstrates how RushDB's graph capabilities enable intelligent
agentic workflows. The core pattern: observe relationship changes in the graph
and automatically trigger downstream actions.

The WorkflowEngine class orchestrates:
1. Task creation and dependency management
2. Agent capability matching
3. Relationship-triggered notifications
4. Cascading completion propagation
"""

import os
import sys
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from rushdb import RushDB
from workflow_engine import WorkflowEngine

load_dotenv()


def get_db() -> RushDB:
    """Initialize RushDB client with environment configuration."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found. Copy .env.example to .env and add your API key."
        )
    
    url = os.getenv("RUSHDB_URL")
    if url:
        return RushDB(api_key, url=url)
    return RushDB(api_key)


def setup_database(db: RushDB) -> None:
    """
    Initialize the database with sample agents.
    
    Creates three agents with different capabilities that will be used
    to handle tasks in our workflow demo.
    """
    print("\n" + "=" * 60)
    print("PHASE 1: Database Setup")
    print("=" * 60)
    
    # Check if agents already exist
    existing_agents = db.records.find({"labels": ["AGENT"]})
    if existing_agents:
        print(f"\n✓ Found {len(existing_agents)} existing agents. Skipping seed.")
        return
    
    print("\nCreating sample agents with distinct capabilities...")
    
    agents = [
        {
            "name": "Alice",
            "capability": "code",
            "status": "available",
            "skills": ["python", "typescript", "react"]
        },
        {
            "name": "Bob",
            "capability": "review",
            "status": "available",
            "skills": ["security", "performance", "code-quality"]
        },
        {
            "name": "Charlie",
            "capability": "deploy",
            "status": "available",
            "skills": ["kubernetes", "ci-cd", "aws"]
        },
    ]
    
    created = []
    with db.transactions.begin() as tx:
        for agent_data in agents:
            agent = db.records.create(
                label="AGENT",
                data=agent_data,
                transaction=tx
            )
            created.append(agent)
            print(f"  ✓ Created agent: {agent_data['name']} ({agent_data['capability']})")
    
    print(f"\n✓ Created {len(created)} agents")


def run_workflow_demo(db: RushDB) -> None:
    """
    Execute a complete workflow demonstrating relationship-triggered actions.
    
    We create a deployment workflow with interdependent tasks:
    - Task A: Build artifacts (no dependencies)
    - Task B: Security review (depends on A)
    - Task C: Integration tests (depends on A)
    - Task D: Deploy to production (depends on B and C)
    
    As tasks complete, the engine automatically:
    1. Activates dependent tasks
    2. Notifies capable agents
    3. Records all actions in the graph
    """
    print("\n" + "=" * 60)
    print("PHASE 2: Workflow Execution")
    print("=" * 60)
    
    engine = WorkflowEngine(db)
    
    # Step 1: Create a new deployment workflow
    print("\n[1] Creating deployment workflow...")
    workflow = engine.create_workflow(
        name="Deploy v2.4.0",
        description="Production deployment for version 2.4.0"
    )
    print(f"  ✓ Workflow created: {workflow.id}")
    
    # Step 2: Create tasks with dependencies
    print("\n[2] Creating task dependency graph...")
    tasks = [
        {"title": "Build artifacts", "capability": "code", "depends_on": []},
        {"title": "Security review", "capability": "review", "depends_on": [0]},
        {"title": "Integration tests", "capability": "code", "depends_on": [0]},
        {"title": "Deploy to production", "capability": "deploy", "depends_on": [1, 2]},
    ]
    
    created_tasks = []
    for task_def in tasks:
        task = engine.create_task(
            workflow=workflow,
            title=task_def["title"],
            capability=task_def["capability"]
        )
        created_tasks.append(task)
        
        # Attach dependencies if any
        for dep_idx in task_def["depends_on"]:
            engine.add_dependency(task, created_tasks[dep_idx])
        
        print(f"  ✓ Created task: {task_def['title']}")
    
    # Step 3: Start the workflow engine
    print("\n[3] Starting workflow engine...")
    engine.process_ready_tasks()
    
    # Step 4: Simulate task completion and observe cascade
    print("\n[4] Simulating task completions...")
    
    # Complete first task (build artifacts)
    build_task = created_tasks[0]
    print(f"\n  Completing: {build_task['title']}")
    engine.complete_task(build_task)
    
    # Complete second task (security review)
    review_task = created_tasks[1]
    print(f"\n  Completing: {review_task['title']}")
    engine.complete_task(review_task)
    
    # Complete third task (integration tests)
    test_task = created_tasks[2]
    print(f"\n  Completing: {test_task['title']}")
    engine.complete_task(test_task)
    
    # Step 5: Show final state
    print("\n" + "=" * 60)
    print("PHASE 3: Results")
    print("=" * 60)
    
    show_workflow_state(db, workflow)


def show_workflow_state(db: RushDB, workflow) -> None:
    """Display the final state of the workflow and all related records."""
    print(f"\n{'Task':<30} {'Status':<15} {'Assigned To':<20} {'Completed At':<25}")
    print("-" * 95)
    
    # Find all tasks in this workflow
    tasks = db.records.find({
        "labels": ["TASK"],
        "where": {"WORKFLOW": {"$id": workflow.id}},
        "orderBy": {"created_at": "asc"}
    })
    
    for task in tasks:
        status = task.data.get("status", "unknown")
        assigned = task.data.get("assigned_to", "-")
        completed = task.data.get("completed_at", "-")
        title = task.data.get("title", "Untitled")
        print(f"{title:<30} {status:<15} {assigned:<20} {completed:<25}")
    
    # Show action log
    print("\n\nAction Log (relationship-triggered events):")
    print("-" * 60)
    
    actions = db.records.find({
        "labels": ["ACTION_LOG"],
        "orderBy": {"timestamp": "desc"},
        "limit": 10
    })
    
    for action in actions:
        action_type = action.data.get("type", "unknown")
        agent = action.data.get("agent_name", "-")
        task = action.data.get("task_title", "-")
        ts = action.data.get("timestamp", "")
        print(f"[{ts}] {action_type}: {agent} → {task}")


def cleanup_demo_data(db: RushDB) -> None:
    """Remove demo workflow and tasks (for clean re-runs)."""
    print("\n\nCleaning up demo data...")
    
    # Delete workflows (cascade handles related tasks)
    db.records.delete({"labels": ["WORKFLOW"], "where": {}})
    db.records.delete({"labels": ["ACTION_LOG"], "where": {}})
    
    print("✓ Cleanup complete")


def main():
    """Main entry point with command-line interface."""
    print("\n" + "=" * 60)
    print("Relationship-Triggered Actions for Agentic Workflows")
    print("=" * 60)
    
    db = get_db()
    
    # Parse command-line arguments
    if "--setup" in sys.argv:
        setup_database(db)
        return
    
    if "--cleanup" in sys.argv:
        cleanup_demo_data(db)
        return
    
    # Default: run full demo
    try:
        setup_database(db)
        run_workflow_demo(db)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Copied .env.example to .env")
        print("  2. Added your RUSHDB_API_KEY")
        print("  3. Run `python main.py --setup` at least once")
        raise


if __name__ == "__main__":
    main()
