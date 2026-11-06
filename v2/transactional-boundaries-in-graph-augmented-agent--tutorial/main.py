"""
Graph-Augmented Agent: Transactional Boundaries Tutorial

This script demonstrates how RushDB's ACID transactions provide reliable
execution boundaries for graph-augmented AI agents.

Each scenario shows a different transactional pattern used in agent workflows:
1. Explicit transaction with commit/rollback
2. Simulated failure showing rollback behavior
3. Context manager for automatic transaction handling
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHD_API_KEY")
API_URL = os.getenv("RUSHD_API_URL")

if not API_KEY:
    raise ValueError(
        "RUSHD_API_KEY not found. Copy .env.example to .env and add your API key."
    )

# Initialize RushDB client
db = RushDB(API_KEY, url=API_URL) if API_URL else RushDB(API_KEY)


def cleanup_existing_demo_data():
    """Remove any existing demo records to start fresh."""
    labels_to_clean = ["AGENT", "GOAL", "TASK", "SUBTASK", "BELIEF", "RESEARCH_SESSION", "TASK_PLAN"]
    
    for label in labels_to_clean:
        try:
            db.records.delete({"labels": [label], "where": {}})
        except Exception:
            pass  # Ignore if no records exist

    print("\n[Cleanup] Removed any existing demo records.")


def scenario_1_explicit_transaction_commit():
    """
    Scenario 1: Successful atomic planning
    
    An agent receives a research goal and must:
    - Create the goal record
    - Plan multiple tasks atomically
    - Attach tasks to the goal
    - Record the agent's initial belief state
    
    All operations succeed together or none are persisted.
    """
    print("\n" + "=" * 50)
    print("SCENARIO 1: Explicit Transaction with Commit")
    print("=" * 50)
    print("\nSimulating: Agent receives research goal, plans tasks atomically\n")
    
    tx = db.transactions.begin()
    
    try:
        # Step 1: Create the agent record
        agent = db.records.create(
            label="AGENT",
            data={
                "agentId": "research-agent-001",
                "name": "DataResearchAgent",
                "status": "planning",
                "createdAt": "2024-01-15T09:30:00Z"
            },
            transaction=tx
        )
        print(f"✓ Created AGENT: {agent.id}")
        
        # Step 2: Create the research goal
        goal = db.records.create(
            label="GOAL",
            data={
                "title": "Research graph transaction patterns",
                "priority": "high",
                "context": "Need to understand RushDB transaction boundaries for agent workflows"
            },
            transaction=tx
        )
        print(f"✓ Created GOAL: {goal.id}")
        
        # Step 3: Create multiple task records atomically
        tasks = []
        task_definitions = [
            {"title": "Understand ACID properties", "order": 1},
            {"title": "Map RushDB transaction patterns", "order": 2},
            {"title": "Implement agent workflow demo", "order": 3}
        ]
        
        for task_def in task_definitions:
            task = db.records.create(
                label="TASK",
                data={
                    "title": task_def["title"],
                    "status": "pending",
                    "plannedOrder": task_def["order"]
                },
                transaction=tx
            )
            tasks.append(task)
        
        print(f"✓ Created {len(tasks)} TASK records atomically")
        
        # Step 4: Attach tasks to goal with relationships
        for task in tasks:
            db.records.attach(
                source=goal,
                target=task,
                options={"type": "HAS_TASK", "direction": "out"},
                transaction=tx
            )
        print("✓ All tasks attached to goal via HAS_TASK relationships")
        
        # Step 5: Attach goal to agent
        db.records.attach(
            source=agent,
            target=goal,
            options={"type": "PURSUING", "direction": "out"},
            transaction=tx
        )
        print("✓ Goal attached to agent via PURSUING relationship")
        
        # Step 6: Record initial belief state
        belief = db.records.create(
            label="BELIEF",
            data={
                "content": "Transactions are essential for consistent agent state",
                "confidence": 0.9,
                "source": "agent-experience"
            },
            transaction=tx
        )
        db.records.attach(
            source=agent,
            target=belief,
            options={"type": "HOLDS_BELIEF", "direction": "out"},
            transaction=tx
        )
        print("✓ Initial belief state recorded")
        
        # Commit the transaction
        tx.commit()
        print("\n✓✓✓ Transaction committed successfully!")
        print("   All 6 operations atomically persisted to the graph.\n")
        
        return agent, goal, tasks
        
    except Exception as e:
        tx.rollback()
        print(f"✗ Transaction rolled back: {e}")
        raise


def scenario_2_transaction_rollback_on_failure():
    """
    Scenario 2: Failure recovery with rollback
    
    An agent attempts to create a complex plan but encounters a failure
    mid-way. The transaction ensures no partial data is persisted.
    
    This demonstrates RushDB's ACID guarantees:
    - Atomicity: All-or-nothing commits
    - Consistency: Graph remains valid
    - Isolation: Other operations don't see partial state
    - Durability: Committed data survives failures
    """
    print("\n" + "=" * 50)
    print("SCENARIO 2: Transaction Rollback on Failure")
    print("=" * 50)
    print("\nSimulating: Agent plan with simulated failure\n")
    
    tx = db.transactions.begin()
    
    try:
        # Step 1: Create agent session
        session_agent = db.records.create(
            label="AGENT",
            data={
                "agentId": "research-agent-002",
                "name": "FailingAgent",
                "status": "active"
            },
            transaction=tx
        )
        print(f"✓ Created AGENT: {session_agent.id}")
        
        # Step 2: Create initial task
        initial_task = db.records.create(
            label="TASK",
            data={
                "title": "Initial setup task",
                "status": "in_progress"
            },
            transaction=tx
        )
        print(f"✓ Created initial TASK: {initial_task.id}")
        
        # Step 3: Simulate a failure condition (e.g., API timeout, validation error)
        print("\n⚠ Simulating failure condition...")
        simulated_failure = True
        if simulated_failure:
            raise Exception("SIMULATED_FAILURE: External API timeout during task planning")
        
        # This code never executes due to the failure above
        dependent_task = db.records.create(
            label="SUBTASK",
            data={"title": "This won't be created"},
            transaction=tx
        )
        print(f"✗ This line should not be reached")
        
        tx.commit()
        
    except Exception as e:
        # Critical: Rollback ensures no partial state
        tx.rollback()
        print(f"\n✓✓✓ Transaction rolled back successfully!")
        print("   No partial data persisted. Graph remains consistent.\n")
        print(f"   Failure reason: {str(e)}")
        print("   Agent can retry the entire operation cleanly.\n")
        return None


def scenario_3_context_manager_pattern():
    """
    Scenario 3: Context manager for automatic transaction handling
    
    Using Python's context manager (`with` statement) provides:
    - Automatic commit on successful exit
    - Automatic rollback on any exception
    - Cleaner, more readable code
    - No risk of forgetting to commit or rollback
    
    This is the preferred pattern for agent workflows.
    """
    print("\n" + "=" * 50)
    print("SCENARIO 3: Context Manager Pattern")
    print("=" * 50)
    print("\nSimulating: Research session with nested planning\n")
    
    # Context manager handles begin/commit/rollback automatically
    with db.transactions.begin() as tx:
        
        # Create a research session
        session = db.records.create(
            label="RESEARCH_SESSION",
            data={
                "sessionId": "session-abc123",
                "startedAt": "2024-01-15T14:00:00Z",
                "topic": "Agent transaction patterns"
            },
            transaction=tx
        )
        print(f"✓ Created RESEARCH_SESSION: {session.id}")
        
        # Create task plan (nested structure)
        plan = db.records.create(
            label="TASK_PLAN",
            data={
                "planId": "plan-xyz789",
                "steps": ["research", "implement", "test"],
                "estimatedDuration": "2 hours"
            },
            transaction=tx
        )
        print(f"✓ Created TASK_PLAN: {plan.id}")
        
        # Create individual steps
        steps = []
        for i, step_name in enumerate(["research", "implement", "test"], 1):
            step = db.records.create(
                label="SUBTASK",
                data={
                    "stepName": step_name,
                    "sequence": i,
                    "status": "planned"
                },
                transaction=tx
            )
            steps.append(step)
            print(f"  └─ Created step {i}: {step_name}")
        
        # Attach plan to session
        db.records.attach(
            source=session,
            target=plan,
            options={"type": "HAS_PLAN", "direction": "out"},
            transaction=tx
        )
        print(f"✓ Plan attached to session via HAS_PLAN")
        
        # Attach steps to plan
        for step in steps:
            db.records.attach(
                source=plan,
                target=step,
                options={"type": "INCLUDES_STEP", "direction": "out"},
                transaction=tx
            )
        print(f"✓ All {len(steps)} steps attached to plan")
        
        # Create agent record
        agent = db.records.create(
            label="AGENT",
            data={
                "agentId": "research-agent-003",
                "name": "ContextManagerAgent",
                "status": "planning"
            },
            transaction=tx
        )
        print(f"✓ Created AGENT: {agent.id}")
        
        # Attach agent to session
        db.records.attach(
            source=agent,
            target=session,
            options={"type": "RUNNING_SESSION", "direction": "out"},
            transaction=tx
        )
        print(f"✓ Agent linked to session via RUNNING_SESSION")
        
    # Context manager automatically commits here on success
    # Or automatically rolls back if any exception was raised
    
    print("\n✓✓✓ Context manager transaction completed!")
    print("   No explicit commit() called - context manager handled it.\n")
    
    return session, plan, agent


def scenario_4_agent_memory_workflow():
    """
    Scenario 4: Full agent memory workflow
    
    This demonstrates a complete agent workflow using transactions
    to maintain consistent memory state:
    
    1. Agent receives observation
    2. Updates belief state
    3. Plans next action
    4. Records intent
    
    All changes atomic to prevent belief/action inconsistency.
    """
    print("\n" + "=" * 50)
    print("SCENARIO 4: Complete Agent Memory Workflow")
    print("=" * 50)
    print("\nSimulating: Agent processes observation and updates memory atomically\n")
    
    with db.transactions.begin() as tx:
        
        # Create agent with initial state
        agent = db.records.create(
            label="AGENT",
            data={
                "agentId": "memory-agent-001",
                "name": "MemoryAgent",
                "state": "idle"
            },
            transaction=tx
        )
        print(f"✓ Agent created: {agent.id}")
        
        # Record observation (external input)
        observation = db.records.create(
            label="OBSERVATION",
            data={
                "content": "RushDB supports ACID transactions for agent workflows",
                "timestamp": "2024-01-15T15:00:00Z",
                "source": "user-input"
            },
            transaction=tx
        )
        print(f"✓ Observation recorded: {observation.id}")
        
        # Update agent belief based on observation
        belief = db.records.create(
            label="BELIEF",
            data={
                "content": "RushDB transactions enable reliable agent state management",
                "confidence": 0.85,
                "derivedFrom": [observation.id]
            },
            transaction=tx
        )
        db.records.attach(
            source=agent,
            target=belief,
            options={"type": "HOLDS_BELIEF", "direction": "out"},
            transaction=tx
        )
        print(f"✓ Belief derived from observation: {belief.id}")
        
        # Agent plans next action based on belief
        intent = db.records.create(
            label="INTENT",
            data={
                "action": "demonstrate-transaction-patterns",
                "reasoning": "Belief confirms RushDB is suitable for agent memory",
                "priority": "high"
            },
            transaction=tx
        )
        db.records.attach(
            source=agent,
            target=intent,
            options={"type": "GENERATED", "direction": "out"},
            transaction=tx
        )
        print(f"✓ Intent generated: {intent.id}")
        
        # Link observation to belief
        db.records.attach(
            source=observation,
            target=belief,
            options={"type": "INFORMED", "direction": "out"},
            transaction=tx
        )
        print(f"✓ Observation linked to belief")
        
    # Auto-commit on success
    
    print("\n✓✓✓ Agent memory workflow completed!")
    print("   Observation → Belief → Intent all recorded atomically.\n")
    print("   Agent can now execute the planned action consistently.\n")
    
    return agent


def verify_graph_state():
    """Verify the graph state after all scenarios."""
    print("\n" + "=" * 50)
    print("VERIFICATION: Querying Graph State")
    print("=" * 50)
    
    # Count records by label
    labels = ["AGENT", "GOAL", "TASK", "SUBTASK", "BELIEF", "RESEARCH_SESSION", "TASK_PLAN", "OBSERVATION", "INTENT"]
    
    print("\nRecord counts:")
    for label in labels:
        try:
            result = db.labels.find({"where": {}})
            count = sum(1 for l in result.data if l.name == label)
            # Use find to get actual count
            records = db.records.find({"labels": [label], "limit": 1000})
            print(f"  • {label}: {len(records.data) if records.data else 0} records")
        except Exception:
            print(f"  • {label}: 0 records")
    
    # Sample some relationships
    print("\nSample graph traversal (AGENT → GOAL via PURSUING):")
    agents = db.records.find({"labels": ["AGENT"], "limit": 5})
    for agent in agents.data:
        if agent.data.get("agentId") == "research-agent-001":
            print(f"  Agent: {agent.id}")
            goals = db.records.find({
                "labels": ["GOAL"],
                "where": {"AGENT": {"$relation": {"type": "PURSUING", "direction": "in"}}}
            })
            print(f"    → Has {len(goals.data)} goal(s) via PURSUING relationship")
            for goal in goals.data:
                tasks = db.records.find({
                    "labels": ["TASK"],
                    "where": {"GOAL": {"$relation": {"type": "HAS_TASK", "direction": "in"}}}
                })
                print(f"      → Goal has {len(tasks.data)} task(s) via HAS_TASK")


def main():
    """Run all scenarios demonstrating transactional boundaries."""
    print("\n" + "=" * 60)
    print("  Graph-Augmented Agent: Transactional Boundaries Tutorial")
    print("  RushDB SDK Demo")
    print("=" * 60)
    
    try:
        # Clean up before starting
        cleanup_existing_demo_data()
        
        # Run all scenarios
        scenario_1_explicit_transaction_commit()
        scenario_2_transaction_rollback_on_failure()
        scenario_3_context_manager_pattern()
        scenario_4_agent_memory_workflow()
        
        # Verify the resulting graph state
        verify_graph_state()
        
        print("\n" + "=" * 60)
        print("  ✓ All scenarios completed successfully!")
        print("=" * 60)
        print("\nKey takeaways:")
        print("  • Use transactions for any multi-record operations")
        print("  • Context manager is preferred for simple workflows")
        print("  • Explicit begin/commit/rollback for complex error handling")
        print("  • Rollback prevents partial state corruption")
        print("\nLearn more: https://docs.rushdb.com/features/transactions")
        print()
        
    except Exception as e:
        print(f"\n✗ Tutorial failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
