#!/usr/bin/env python3
"""
Hypergraph Representations for Multi-Party Collaborative AI Workflows

This tutorial demonstrates how to use RushDB's property graph as a hypergraph
for modeling complex multi-agent collaborative AI workflows.

Run `python seed.py` first to populate the database with sample data.
"""

import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


from rushdb import RushDB


def initialize_db():
    """Initialize RushDB connection."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError("RUSHDB_API_KEY environment variable not set")
    return RushDB(api_key)


def query_1_find_collaborators_on_task(db: RushDB) -> None:
    """
    HYPERGRAPH QUERY 1: Find All Collaborators on a Task
    
    This demonstrates true hyperedge behavior: a single task can have
    multiple agents collaborating on it. We traverse from TASK to all
    AGENTs connected via COLLABORATES_ON relationships.
    """
    print("\n" + "=" * 60)
    print("HYPERGRAPH QUERY 1: Find All Collaborators on a Task")
    print("=" * 60)
    
    # Find the task "Implement semantic search algorithm"
    task_result = db.records.find_one({
        "labels": ["TASK"],
        "where": {"title": "Implement semantic search algorithm"}
    })
    
    if not task_result:
        print("  Task not found. Run seed.py first.")
        return
    
    task_id = task_result.id
    
    # Find all agents collaborating on this task using relationship filtering
    # The key pattern: filter by related AGENT records
    collaborators = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "TASK": {"$relation": {"type": "COLLABORATES_ON", "direction": "in"}}
        }
    })
    
    print(f"\n  Task: '{task_result['title']}' ({task_id})")
    print(f"  Collaborators ({len(collaborators.data)} total):")
    for agent in collaborators.data:
        print(f"    - {agent['name']} ({agent.id}) — role: {agent['role']}")


def query_2_find_tasks_for_agent(db: RushDB) -> None:
    """
    HYPERGRAPH QUERY 2: Find All Tasks for an Agent
    
    Demonstrates the inverse hyperedge: an agent can work on multiple tasks.
    We traverse from AGENT to all TASKs connected via COLLABORATES_ON.
    """
    print("\n" + "=" * 60)
    print("HYPERGRAPH QUERY 2: Find All Tasks for an Agent")
    print("=" * 60)
    
    # Find Bob Patel
    agent_result = db.records.find_one({
        "labels": ["AGENT"],
        "where": {"name": "Bob Patel"}
    })
    
    if not agent_result:
        print("  Agent not found. Run seed.py first.")
        return
    
    agent_id = agent_result.id
    
    # Find all tasks this agent is working on
    tasks = db.records.find({
        "labels": ["TASK"],
        "where": {
            "AGENT": {"$relation": {"type": "COLLABORATES_ON", "direction": "in"}}
        }
    })
    
    print(f"\n  Agent: '{agent_result['name']}' ({agent_id})")
    print(f"  Tasks assigned ({len(tasks.data)} total):")
    for task in tasks.data:
        print(f"    - '{task['title']}' — priority: {task['priority']}, est. {task['estimated_hours']}h")



def query_3_find_shared_projects_between_agents(db: RushDB) -> None:
    """
    HYPERGRAPH QUERY 3: Find Shared Projects Between Agents
    
    Demonstrates hypergraph path traversal: find projects where two
    or more agents both work, showing collaboration overlap.
    """
    print("\n" + "=" * 60)
    print("HYPERGRAPH QUERY 3: Find Shared Projects Between Agents")
    print("=" * 60)
    
    # Find Alice and Carol
    alice = db.records.find_one({"labels": ["AGENT"], "where": {"name": "Alice Chen"}})
    carol = db.records.find_one({"labels": ["AGENT"], "where": {"name": "Carol Williams"}})
    
    if not alice or not carol:
        print("  Agents not found. Run seed.py first.")
        return
    
    # Find projects Alice works on
    alice_projects = db.records.find({
        "labels": ["PROJECT"],
        "where": {
            "AGENT": {
                "$relation": {"type": "WORKS_ON", "direction": "in"},
                "name": "Alice Chen"
            }
        }
    })
    
    # Find projects Carol works on
    carol_projects = db.records.find({
        "labels": ["PROJECT"],
        "where": {
            "AGENT": {
                "$relation": {"type": "WORKS_ON", "direction": "in"},
                "name": "Carol Williams"
            }
        }
    })
    
    # Find intersection
    alice_project_ids = {p.id for p in alice_projects.data}
    shared = [p for p in carol_projects.data if p.id in alice_project_ids]
    
    print(f"\n  Agents: '{alice['name']}' and '{carol['name']}'")
    print(f"  Shared projects ({len(shared)} total):")
    for project in shared:
        print(f"    - {project['name']} (priority: {project['priority']})")


def query_4_find_artifacts_for_project(db: RushDB) -> None:
    """
    HYPERGRAPH QUERY 4: Find All Artifacts for a Project
    
    Demonstrates hypergraph aggregation: collect all artifacts produced
    through any task within a project.
    """
    print("\n" + "=" * 60)
    print("HYPERGRAPH QUERY 4: Find All Artifacts for a Project")
    print("=" * 60)
    
    # Find Project Alpha
    project = db.records.find_one({
        "labels": ["PROJECT"],
        "where": {"name": "Project Alpha: Semantic Search Engine"}
    })
    
    if not project:
        print("  Project not found. Run seed.py first.")
        return
    
    # Find all tasks in this project
    tasks = db.records.find({
        "labels": ["TASK"],
        "where": {
            "PROJECT": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "name": "Project Alpha: Semantic Search Engine"
            }
        }
    })
    
    # Collect all artifacts from all tasks
    all_artifacts = []
    for task in tasks.data:
        artifacts = db.records.find({
            "labels": ["ARTIFACT"],
            "where": {
                "TASK": {
                    "$relation": {"type": "PRODUCES", "direction": "in"},
                    "title": task["title"]
                }
            }
        })
        all_artifacts.extend(artifacts.data)
    
    print(f"\n  Project: '{project['name']}'")
    print(f"  Artifacts generated ({len(all_artifacts)} total):")
    for artifact in all_artifacts:
        print(f"    - '{artifact['title']}' ({artifact['type']})")


def query_5_trace_collaboration_path(db: RushDB) -> None:
    """
    HYPERGRAPH QUERY 5: Trace Full Collaboration Path
    
    Demonstrates hypergraph path traversal: trace the complete path
    from an agent through their projects, tasks, and final artifacts.
    This shows the end-to-end flow of collaborative work.
    """
    print("\n" + "=" * 60)
    print("HYPERGRAPH QUERY 5: Trace Full Collaboration Path")
    print("=" * 60)
    
    # Find the target artifact
    artifact = db.records.find_one({
        "labels": ["ARTIFACT"],
        "where": {"title": "Final research synthesis"}
    })
    
    if not artifact:
        print("  Artifact not found. Run seed.py first.")
        return
    
    # Trace back: artifact -> task -> project -> agents
    # Step 1: Find the task that produced this artifact
    tasks = db.records.find({
        "labels": ["TASK"],
        "where": {
            "ARTIFACT": {
                "$relation": {"type": "PRODUCES", "direction": "in"},
                "title": "Final research synthesis"
            }
        }
    })
    
    if not tasks.data:
        print("  No task found for this artifact.")
        return
    
    task = tasks.data[0]
    
    # Step 2: Find the project containing this task
    projects = db.records.find({
        "labels": ["PROJECT"],
        "where": {
            "TASK": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "title": task["title"]
            }
        }
    })
    
    # Step 3: Find all agents collaborating on this task
    agents = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "TASK": {
                "$relation": {"type": "COLLABORATES_ON", "direction": "in"},
                "title": task["title"]
            }
        }
    })
    
    # Step 4: Find contributor of the artifact
    contributors = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "ARTIFACT": {
                "$relation": {"type": "CONTRIBUTED", "direction": "out"},
                "title": "Final research synthesis"
            }
        }
    })
    
    print(f"\n  Collaboration path for: '{artifact['title']}'")
    print("\n  Path traversal:")
    for agent in agents.data:
        print(f"    {agent['name']} ({agent['role']})")
    
    if projects.data:
        print(f"      → {projects.data[0]['name']}")
    print(f"        → {task['title']} (task)")
    
    collaborator_names = [a['name'].split()[0] for a in agents.data]
    print(f"          → {', '.join(collaborator_names)} (collaborators)")
    
    for contributor in contributors.data:
        print(f"            ← {contributor['name']} (contributed artifact)")


def show_statistics(db: RushDB) -> None:
    """Show hypergraph statistics."""
    print("\n" + "=" * 60)
    print("HYPERGRAPH STATISTICS")
    print("=" * 60)
    
    # Count all records
    agents = db.records.find({"labels": ["AGENT"]})
    projects = db.records.find({"labels": ["PROJECT"]})
    tasks = db.records.find({"labels": ["TASK"]})
    artifacts = db.records.find({"labels": ["ARTIFACT"]})
    
    print(f"\n  Record counts:")
    print(f"    Agents: {agents.total}")
    print(f"    Projects: {projects.total}")
    print(f"    Tasks: {tasks.total}")
    print(f"    Artifacts: {artifacts.total}")
    
    # Calculate hyperedge statistics
    total_collaborators = 0
    multi_agent_tasks = []
    
    for task in tasks.data:
        collaborators = db.records.find({
            "labels": ["AGENT"],
            "where": {
                "TASK": {"$relation": {"type": "COLLABORATES_ON", "direction": "in"}}
            }
        })
        if collaborators.total > 1:
            multi_agent_tasks.append((task['title'], collaborators.total))
        total_collaborators += collaborators.total
    
    print(f"\n  Hyperedge analysis:")
    print(f"    Total COLLABORATES_ON relationships: {total_collaborators}")
    print(f"    Tasks with 2+ agents (true hyperedges): {len(multi_agent_tasks)}")
    print(f"    Multi-agent tasks:")
    for title, count in multi_agent_tasks:
        print(f"      - {title}: {count} collaborators")



def main():
    """Main tutorial demonstration."""
    print("\n" + "=" * 60)
    print("HYPERGRAPH REPRESENTATIONS FOR MULTI-PARTY")
    print("COLLABORATIVE AI WORKFLOWS")
    print("=" * 60)
    print("\nUsing RushDB's property graph as a hypergraph model")
    print("for multi-agent collaborative AI workflows.")
    
    try:
        db = initialize_db()
    except ValueError as e:
        print(f"\nError: {e}")
        print("Get your API key at https://app.rushdb.com")
        return
    
    # Run all hypergraph queries
    query_1_find_collaborators_on_task(db)
    query_2_find_tasks_for_agent(db)
    query_3_find_shared_projects_between_agents(db)
    query_4_find_artifacts_for_project(db)
    query_5_trace_collaboration_path(db)
    show_statistics(db)
    
    print("\n" + "=" * 60)
    print("TUTORIAL COMPLETE")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  1. RushDB's property graph supports true hypergraph patterns")
    print("  2. Tasks can have multiple collaborating agents (hyperedges)")
    print("  3. Agents can work on multiple projects simultaneously")
    print("  4. Relationship traversal enables complex multi-hop queries")
    print("  5. Transactions ensure atomic hyperedge creation")
    print("\n")


if __name__ == "__main__":
    main()
