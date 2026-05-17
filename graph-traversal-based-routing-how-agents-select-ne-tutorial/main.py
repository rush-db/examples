"""
Graph-Traversal-Based Routing Demo

Demonstrates how AI agents can use RushDB's property graph to:
1. Query available actions based on current state
2. Check action preconditions via relationship traversal
3. Update state transactionally as actions are executed
4. Handle task dependencies in routing decisions
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB


def get_agent(db: RushDB) -> object:
    """Retrieve the demo agent from the database."""
    result = db.records.find({"labels": ["AGENT"], "where": {"name": "research_agent"}})
    if not result.data:
        raise ValueError("Agent 'research_agent' not found. Run seed.py first!")
    return result.data[0]


def get_current_state(db: RushDB, agent: object) -> str:
    """Get the agent's current state from the database."""
    return agent["current_state"]


def get_available_actions(db: RushDB, current_state: str) -> list:
    """
    Find all actions available from the given state.
    
    This uses RushDB's relationship filtering to find actions that are
    enabled by the current state.
    """
    result = db.records.find({
        "labels": ["ACTION"],
        "where": {
            "ENABLES": {
                "$relation": {"type": "ENABLES", "direction": "in"},
                "name": current_state
            }
        }
    })
    return result.data


def get_action_preconditions(db: RushDB, action: object) -> list:
    """
    Get the states that are preconditions for an action.
    
    Returns a list of state names that must be met for this action to be valid.
    """
    result = db.records.find({
        "labels": ["STATE"],
        "where": {
            "ENABLES": {
                "$relation": {"type": "ENABLES", "direction": "out"},
                "$id": action.id
            }
        }
    })
    return [state["name"] for state in result.data]


def get_action_outcome_state(db: RushDB, action: object) -> str:
    """
    Get the state that results from executing an action.
    """
    result = db.records.find({
        "labels": ["STATE"],
        "where": {
            "LEADS_TO": {
                "$relation": {"type": "LEADS_TO", "direction": "in"},
                "$id": action.id
            }
        }
    })
    if result.data:
        return result.data[0]["name"]
    return None


def check_task_preconditions(db: RushDB, task: object, action: object) -> dict:
    """
    Check if all task-related preconditions are met for an action.
    
    Returns dict with 'valid' bool and 'reason' string.
    """
    task_status = task["status"]
    task_name = task["name"]
    
    # Check if task is blocked by dependencies
    blocking_tasks = db.records.find({
        "labels": ["TASK"],
        "where": {
            "BLOCKED_BY": {
                "$relation": {"type": "BLOCKED_BY", "direction": "in"},
                "$id": task.id
            }
        }
    })
    
    incomplete_blockers = [
        bt["name"] for bt in blocking_tasks.data 
        if bt["status"] not in ["complete", "completed", "COMPLETE"]
    ]
    
    if incomplete_blockers:
        return {
            "valid": False,
            "reason": f"Task blocked by incomplete dependencies: {incomplete_blockers}"
        }
    
    if task_status == "complete":
        return {
            "valid": False,
            "reason": f"Task '{task_name}' is already complete"
        }
    
    return {"valid": True, "reason": "All preconditions met"}


def select_best_action(db: RushDB, agent: object, task: object) -> object:
    """
    Select the next best action for the agent to execute.
    
    Strategy:
    1. Get available actions for current state
    2. Filter by preconditions
    3. Prefer actions that advance towards completion
    """
    current_state = get_current_state(db, agent)
    available_actions = get_available_actions(db, current_state)
    
    if not available_actions:
        return None
    
    # Score actions by how far they advance us
    best_action = None
    best_score = -1
    
    for action in available_actions:
        score = 0
        
        # Base score from action type (prefer research and synthesis early)
        action_type = action["action_type"]
        if action_type == "research" and current_state == "IDLE":
            score += 10
        elif action_type == "synthesis" and current_state == "RESEARCHING":
            score += 10
        elif action_type == "writing" and current_state == "RESEARCHING":
            score += 8
        elif action_type == "review" and current_state in ["WRITING", "REVIEWING"]:
            score += 6
        elif action_type == "approval" and current_state == "REVIEWING":
            score += 10
        elif action_type == "cleanup" and current_state == "COMPLETE":
            score += 5
        
        # Check task preconditions
        precondition_check = check_task_preconditions(db, task, action)
        if precondition_check["valid"]:
            score += 5
        else:
            score = -1  # Disqualify if blocked
        
        if score > best_score:
            best_score = score
            best_action = action
    
    return best_action


def execute_action(db: RushDB, agent: object, task: object, action: object) -> None:
    """
    Execute an action and update state transactionally.
    """
    current_state = get_current_state(db, agent)
    new_state = get_action_outcome_state(db, action)
    
    print(f"\n  Executing action: {action['name']}")
    print(f"    From state: {current_state}")
    print(f"    To state: {new_state}")
    
    # Transactional update
    with db.transactions.begin() as tx:
        # Update agent's current state
        db.records.update(
            record_id=agent.id,
            data={"current_state": new_state},
            transaction=tx
        )
        
        # If this is a significant action, update task status
        action_type = action["action_type"]
        if action_type in ["research", "writing", "review", "approval"]:
            new_task_status = "in_progress" if task["status"] == "pending" else task["status"]
            db.records.update(
                record_id=task.id,
                data={"status": new_task_status},
                transaction=tx
            )
        
        # Link the action execution to the task
        db.records.attach(
            source=task,
            target=action,
            options={"type": "EXECUTED", "direction": "out"},
            transaction=tx
        )
        
        # Create action execution record for audit trail
        db.records.create(
            label="ACTION_EXECUTION",
            data={
                "action_name": action["name"],
                "from_state": current_state,
                "to_state": new_state,
                "timestamp": "auto"
            },
            transaction=tx
        )
    
    print(f"    State updated successfully!")


def get_task_by_name(db: RushDB, name: str) -> object:
    """Retrieve a task by name."""
    result = db.records.find({"labels": ["TASK"], "where": {"name": name}})
    if result.data:
        return result.data[0]
    return None


def check_task_dependencies(db: RushDB, task: object) -> dict:
    """
    Check what dependencies a task has and which are satisfied.
    """
    # Tasks that block this task
    blockers = db.records.find({
        "labels": ["TASK"],
        "where": {
            "BLOCKED_BY": {
                "$relation": {"type": "BLOCKED_BY", "direction": "in"},
                "$id": task.id
            }
        }
    })
    
    blocked_by = []
    blocking_satisfied = []
    
    for blocker in blockers.data:
        if blocker["status"] in ["complete", "completed", "COMPLETE"]:
            blocking_satisfied.append(blocker["name"])
        else:
            blocked_by.append(blocker["name"])
    
    return {
        "blocked_by": blocked_by,
        "blocking_satisfied": blocking_satisfied,
        "can_proceed": len(blocked_by) == 0
    }


def find_valid_action_sequence(db: RushDB, start_state: str, end_state: str) -> list:
    """
    Find a valid sequence of actions from start_state to end_state.
    
    Uses graph traversal to find a path through action transitions.
    """
    path = [start_state]
    current_state = start_state
    max_steps = 20  # Prevent infinite loops
    
    while current_state != end_state and len(path) < max_steps:
        # Get available actions from current state
        actions = get_available_actions(db, current_state)
        
        if not actions:
            break
        
        # Find action that leads to the target state or closer to it
        best_action = None
        best_state = None
        
        state_order = ["IDLE", "RESEARCHING", "WRITING", "REVIEWING", "COMPLETE"]
        
        for action in actions:
            outcome = get_action_outcome_state(db, action)
            if outcome:
                if best_state is None:
                    best_action = action
                    best_state = outcome
                else:
                    # Prefer states closer to target
                    current_idx = state_order.index(current_state) if current_state in state_order else 0
                    best_idx = state_order.index(best_state) if best_state in state_order else 0
                    outcome_idx = state_order.index(outcome) if outcome in state_order else 0
                    target_idx = state_order.index(end_state) if end_state in state_order else len(state_order) - 1
                    
                    if abs(outcome_idx - target_idx) < abs(best_idx - target_idx):
                        best_action = action
                        best_state = outcome
        
        if best_action and best_state:
            path.append(f"{best_action['name']} -> {best_state}")
            current_state = best_state
        else:
            break
    
    path.append(end_state)
    return path


def demo_initial_state(db: RushDB, agent: object) -> None:
    """Demonstrate querying initial agent state and available actions."""
    print("\n--- Initial Agent State ---")
    
    current_state = get_current_state(db, agent)
    available_actions = get_available_actions(db, current_state)
    
    print(f"Agent: {agent['name']}")
    print(f"Current State: {current_state}")
    print(f"Available Actions: {[a['name'] for a in available_actions]}")


def demo_action_selection(db: RushDB, agent: object, task: object) -> None:
    """Demonstrate intelligent action selection."""
    print("\n--- Selecting Next Action ---")
    
    best_action = select_best_action(db, agent, task)
    
    if best_action:
        preconditions = get_action_preconditions(db, best_action)
        print(f"Selected: {best_action['name']}")
        print(f"Action Type: {best_action['action_type']}")
        print(f"Preconditions: {preconditions}")
        print(f"Reason: Valid preconditions met (state={get_current_state(db, agent)}, task={task['status']})")
        
        # Execute the action
        execute_action(db, agent, task, best_action)
        
        # Show new state
        print("\n--- After Action Execution ---")
        updated_agent = db.records.find_by_id(agent.id)
        new_state = get_current_state(db, updated_agent)
        new_actions = get_available_actions(db, new_state)
        
        print(f"Agent: {updated_agent['name']}")
        print(f"Current State: {new_state}")
        print(f"Available Actions: {[a['name'] for a in new_actions]}")
    else:
        print("No valid action found!")


def demo_task_flow(db: RushDB, agent: object, task: object) -> None:
    """Demonstrate completing a task flow through multiple actions."""
    print("\n--- Completing Task Flow ---")
    
    # Simulate a research -> writing -> review flow
    action_sequence = [
        ("begin_research", "RESEARCHING"),
        ("synthesize_findings", "WRITING"),
    ]
    
    print("Executing sequence: begin_research -> synthesize_findings")
    
    for action_name, expected_state in action_sequence:
        # Get current agent state
        current_agent = db.records.find_by_id(agent.id)
        current_state = get_current_state(db, current_agent)
        
        # Find the action
        result = db.records.find({
            "labels": ["ACTION"],
            "where": {"name": action_name}
        })
        
        if result.data:
            action = result.data[0]
            
            # Verify action is available from current state
            available = get_available_actions(db, current_state)
            available_names = [a["name"] for a in available]
            
            if action_name in available_names:
                execute_action(db, current_agent, task, action)
            else:
                print(f"  Skipped {action_name} - not available from {current_state}")
        
        # Small delay to show progression
        current_agent = db.records.find_by_id(agent.id)
    
    # Show final task state
    print("\n--- Final State ---")
    final_task = db.records.find_by_id(task.id)
    final_agent = db.records.find_by_id(agent.id)
    
    print(f"Task: {final_task['name']} (id: {final_task.id[:8]}...)")
    print(f"Status: {final_task['status'].upper()}")
    print(f"Agent State: {final_agent['current_state']}")


def demo_dependency_routing(db: RushDB) -> None:
    """Demonstrate dependency-aware routing."""
    print("\n--- Dependency-Aware Routing ---")
    
    # Check the build_prototype task which depends on design_ui
    task = get_task_by_name(db, "build_prototype")
    if task:
        deps = check_task_dependencies(db, task)
        
        print(f"Task: {task['name']} (priority: {task['priority']})")
        print(f"Blocked by: {deps['blocked_by'] or 'None'}")
        print(f"Dependencies satisfied: {deps['blocking_satisfied'] or 'None'}")
        print(f"Can proceed: {deps['can_proceed']}")
        
        if deps["can_proceed"]:
            print("-> Task can be started immediately")
        else:
            print(f"-> Task must wait for: {deps['blocked_by']}")
    
    # Check the write_tests task
    task2 = get_task_by_name(db, "write_tests")
    if task2:
        deps2 = check_task_dependencies(db, task2)
        
        print(f"\nTask: {task2['name']} (priority: {task2['priority']})")
        print(f"Blocked by: {deps2['blocked_by'] or 'None'}")
        
        # Since design_ui is pending, write_tests is blocked
        if deps2["blocked_by"]:
            print(f"-> Cannot start until: {deps2['blocked_by']}")


def demo_path_finding(db: RushDB) -> None:
    """Demonstrate finding optimal paths through the state machine."""
    print("\n--- Complex Traversal: Finding Optimal Path ---")
    
    path = find_valid_action_sequence(db, "IDLE", "COMPLETE")
    
    print("Path from IDLE to COMPLETE:")
    for i, step in enumerate(path):
        if i == 0:
            print(f"  Start: {step}")
        elif i == len(path) - 1:
            print(f"  End: {step}")
        else:
            print(f"  Step {i}: {step}")


def main():
    """Main entry point for the demo."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    api_url = os.environ.get("RUSHDB_URL")
    
    if not api_key:
        print("ERROR: RUSHDB_API_KEY environment variable not set.")
        print("Please copy .env.example to .env and add your API key.")
        print("\nThen run `python seed.py` to initialize the demo data.")
        sys.exit(1)
    
    print("=" * 60)
    print("Graph-Traversal-Based Routing Demo")
    print("=" * 60)
    
    # Initialize RushDB client
    if api_url:
        db = RushDB(api_key, url=api_url)
    else:
        db = RushDB(api_key)
    
    print("\nConnected to RushDB")
    
    # Get the demo agent
    try:
        agent = get_agent(db)
    except ValueError as e:
        print(f"\nERROR: {e}")
        print("Please run `python seed.py` first to initialize the demo data.")
        sys.exit(1)
    
    # Get the primary task for this demo
    task = get_task_by_name(db, "research_agent_report")
    if not task:
        print("\nERROR: Could not find demo task. Run seed.py first.")
        sys.exit(1)
    
    # Run demonstrations
    demo_initial_state(db, agent)
    demo_action_selection(db, agent, task)
    demo_task_flow(db, agent, task)
    demo_dependency_routing(db)
    demo_path_finding(db)
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    
    # Summary of what we demonstrated
    print("""
Summary of demonstrated patterns:

1. State-Based Action Query
   - Used relationship filtering to find available actions
   - Queried: db.records.find({ where: { ENABLES: { $relation: {...}, name: "IDLE" } } })

2. Precondition Validation
   - Checked both state preconditions AND task dependencies
   - Used graph traversal to find blocking tasks

3. Transactional State Updates
   - Updated agent state and task status atomically
   - Maintained audit trail via ACTION_EXECUTION records

4. Path Finding
   - Traversed action->state edges to find valid sequences
   - Applied heuristics to select optimal paths

These patterns enable agents to make routing decisions by querying
the graph structure rather than hardcoding logic.
""")


if __name__ == "__main__":
    main()
