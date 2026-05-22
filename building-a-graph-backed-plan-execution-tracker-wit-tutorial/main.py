"""
Main demonstration: Graph-backed Plan Execution Tracker

This script showcases RushDB's property graph capabilities for tracking
plans with complex milestone dependencies.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env")

db = RushDB(API_KEY)


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def find_blocked_milestones():
    """
    Find all milestones that have incomplete dependencies.
    These milestones are 'blocked' and cannot proceed.
    """
    print_header("Blocked Milestones (Dependencies Incomplete)")
    
    # Find all milestones
    all_milestones = db.records.find({"labels": ["MILESTONE"]})
    
    blocked = []
    
    for milestone in all_milestones.data:
        # Find dependencies for this milestone
        deps = db.records.find({
            "labels": ["MILESTONE"],
            "where": {
                "DEPENDS_ON": {"$id": {"$in": [milestone.id]}}
            }
        })
        
        if deps.data:
            # Check if any dependency is not completed
            incomplete = [
                d for d in deps.data 
                if d.get('status') not in ['completed', 'n/a']
            ]
            
            if incomplete:
                blocked.append({
                    "milestone": milestone,
                    "blocking_deps": incomplete
                })
    
    if not blocked:
        print("  No blocked milestones found.")
        return []
    
    for item in blocked:
        ms = item["milestone"]
        blocking = [d['name'] for d in item["blocking_deps"]]
        print(f"\n  📌 {ms['name']}")
        print(f"     Plan: {ms.get('plan_name', 'Unknown')}")
        print(f"     Status: {ms.get('status', 'unknown')}")
        print(f"     Blocked by: {', '.join(blocking)}")
    
    return blocked


def find_ready_milestones():
    """
    Find milestones where all dependencies are completed.
    These are ready to execute.
    """
    print_header("Ready to Execute (All Dependencies Met)")
    
    all_milestones = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"status": {"$in": ["pending", "in_progress"]}}
    })
    
    ready = []
    
    for milestone in all_milestones.data:
        # Find what this milestone depends on
        deps = db.records.find({
            "labels": ["MILESTONE"],
            "where": {
                "DEPENDS_ON": {"$id": {"$in": [milestone.id]}}
            }
        })
        
        # Check if all dependencies are completed
        if deps.data:
            all_complete = all(
                d.get('status') == 'completed' 
                for d in deps.data
            )
            if all_complete:
                ready.append(milestone)
        else:
            # No dependencies means it's always ready
            ready.append(milestone)
    
    if not ready:
        print("  No ready milestones found.")
        return []
    
    for ms in ready:
        deps = db.records.find({
            "labels": ["MILESTONE"],
            "where": {
                "DEPENDS_ON": {"$id": {"$in": [ms.id]}}
            }
        })
        
        dep_names = [d['name'] for d in deps.data] if deps.data else ["(none)"]
        
        print(f"\n  ✅ {ms['name']}")
        print(f"     Status: {ms.get('status')}")
        print(f"     Dependencies: {', '.join(dep_names)}")
    
    return ready


def get_dependency_chain(milestone, depth=0):
    """
    Recursively get the full dependency chain for a milestone.
    Returns a tree of dependencies.
    """
    indent = "  " * depth
    
    # Find what this milestone depends on
    deps = db.records.find({
        "labels": ["MILESTONE"],
        "where": {
            "DEPENDS_ON": {"$id": {"$in": [milestone.id]}}
        }
    })
    
    result = {
        "name": milestone['name'],
        "status": milestone.get('status'),
        "depth": depth,
        "children": []
    }
    
    if deps.data:
        for dep in deps.data:
            child = get_dependency_chain(dep, depth + 1)
            result["children"].append(child)
    
    return result


def print_dependency_tree(tree, prefix="", is_last=True):
    """Pretty print a dependency tree."""
    connector = "└── " if is_last else "├── "
    status_icon = {
        "completed": "✅",
        "in_progress": "🔄",
        "pending": "⏳",
        "blocked": "🚫"
    }.get(tree["status"], "❓")
    
    print(f"{prefix}{connector}{status_icon} {tree['name']} ({tree['status']})")
    
    child_prefix = prefix + ("    " if is_last else "│   ")
    for i, child in enumerate(tree["children"]):
        is_last_child = (i == len(tree["children"]) - 1)
        print_dependency_tree(child, child_prefix, is_last_child)


def show_milestone_dependencies():
    """Show full dependency chains for all major milestones."""
    print_header("Full Dependency Chain Analysis")
    
    # Find the API Gateway Development milestone (has multiple dependencies)
    gateway = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"name": "API Gateway Development"}
    })
    
    if gateway.data:
        print("\n  Dependency chain for 'API Gateway Development':")
        tree = get_dependency_chain(gateway.data[0])
        print_dependency_tree(tree)
    
    # Also show the Auth Service (which depends on both API Gateway and Database Migration)
    auth = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"name": "Auth Service Implementation"}
    })
    
    if auth.data:
        print("\n\n  Dependency chain for 'Auth Service Implementation':")
        tree = get_dependency_chain(auth.data[0])
        print_dependency_tree(tree)


def show_plan_progress():
    """Show progress statistics for each plan."""
    print_header("Plan Progress Overview")
    
    plans = db.records.find({"labels": ["PLAN"]})
    
    for plan in plans.data:
        # Get all milestones for this plan
        milestones = db.records.find({
            "labels": ["MILESTONE"],
            "where": {
                "PLAN": {"$id": plan.id}
            },
            "orderBy": {"order": "asc"}
        })
        
        if not milestones.data:
            continue
        
        total = len(milestones.data)
        completed = sum(1 for m in milestones.data if m.get('status') == 'completed')
        in_progress = sum(1 for m in milestones.data if m.get('status') == 'in_progress')
        pending = sum(1 for m in milestones.data if m.get('status') == 'pending')
        
        progress_pct = (completed / total) * 100 if total > 0 else 0
        
        print(f"\n  📋 {plan['name']}")
        print(f"     Status: {plan.get('status')}")
        print(f"     Progress: {progress_pct:.0f}% ({completed}/{total} milestones)")
        print(f"     ├── Completed: {completed}")
        print(f"     ├── In Progress: {in_progress}")
        print(f"     └── Pending: {pending}")
        
        # List milestones with their dependency status
        print(f"\n     Milestone Timeline:")
        for m in milestones.data:
            status_icon = {
                "completed": "✅",
                "in_progress": "🔄",
                "pending": "⏳"
            }.get(m.get('status'), "❓")
            
            # Count dependencies
            deps = db.records.find({
                "labels": ["MILESTONE"],
                "where": {
                    "DEPENDS_ON": {"$id": {"$in": [m.id]}}
                }
            })
            dep_count = len(deps.data) if deps.data else 0
            dep_info = f" (←{dep_count} deps)" if dep_count > 0 else ""
            
            print(f"       {status_icon} [{m.get('order')}] {m['name']}{dep_info}")


def show_tasks_by_assignee():
    """Show task distribution across team members."""
    print_header("Task Distribution by Team Member")
    
    team_members = db.records.find({"labels": ["TEAM"]})
    
    for member in team_members.data:
        # Find tasks assigned to this member
        tasks = db.records.find({
            "labels": ["TASK"],
            "where": {
                "assignee_name": member['name']
            }
        })
        
        if not tasks.data:
            continue
        
        total_hours = sum(t.get('estimated_hours', 0) for t in tasks.data)
        completed = sum(1 for t in tasks.data if t.get('status') == 'completed')
        in_progress = sum(1 for t in tasks.data if t.get('status') == 'in_progress')
        
        print(f"\n  👤 {member['name']} ({member['role']})")
        print(f"     Team: {member.get('team')}")
        print(f"     Tasks: {len(tasks.data)} total | {completed} done | {in_progress} in progress")
        print(f"     Estimated: {total_hours} hours")
        
        for task in tasks.data:
            status_icon = {
                "completed": "✅",
                "in_progress": "🔄",
                "pending": "⏳"
            }.get(task.get('status'), "❓")
            print(f"       {status_icon} {task['name']}")


def update_milestone_status_demo():
    """Demonstrate updating milestone status with upsert."""
    print_header("Status Update Demo (Upsert)")
    
    # Find the Auth Service and mark it as completed
    auth = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"name": "Auth Service Implementation"}
    })
    
    if auth.data:
        print(f"\n  Current status of 'Auth Service Implementation': {auth.data[0].get('status')}")
        
        # Update using upsert
        updated = db.records.upsert(
            label="MILESTONE",
            data={
                "name": "Auth Service Implementation",
                "status": "completed"
            },
            options={"mergeBy": ["name"]}
        )
        
        print(f"  Updated status to: {updated.get('status')}")
        print("\n  💡 Tip: Upsert with 'mergeBy' allows idempotent updates.")
        print("     If the record exists, it updates. If not, it creates.")


def show_critical_path():
    """
    Find the critical path - the longest dependency chain.
    This determines the minimum time to complete the project.
    """
    print_header("Critical Path Analysis")
    
    def get_max_depth(milestone, visited=None):
        if visited is None:
            visited = set()
        
        if milestone.id in visited:
            return 0
        visited.add(milestone.id)
        
        deps = db.records.find({
            "labels": ["MILESTONE"],
            "where": {
                "DEPENDS_ON": {"$id": {"$in": [milestone.id]}}
            }
        })
        
        if not deps.data:
            return 0
        
        max_child_depth = max(get_max_depth(d, visited.copy()) for d in deps.data)
        return 1 + max_child_depth
    
    # Find all root milestones (no dependencies)
    all_milestones = db.records.find({"labels": ["MILESTONE"]})
    
    paths = []
    for ms in all_milestones.data:
        depth = get_max_depth(ms)
        if depth > 0:
            paths.append((ms, depth))
    
    if paths:
        paths.sort(key=lambda x: x[1], reverse=True)
        longest = paths[0]
        
        print(f"\n  Longest dependency chain: {longest[1]} levels deep")
        print(f"  Endpoint: {longest[0]['name']}")
        
        # Show the full chain
        print("\n  Dependency Path:")
        
        def show_chain(milestone, path=[]):
            deps = db.records.find({
                "labels": ["MILESTONE"],
                "where": {
                    "DEPENDS_ON": {"$id": {"$in": [milestone.id]}}
                }
            })
            
            if not deps.data:
                for i, name in enumerate(path):
                    indent = "     " + "  " * i
                    print(f"{indent}└─ {name}")
                return
            
            for dep in deps.data:
                show_chain(dep, path + [milestone['name']])
        
        show_chain(longest[0])
    else:
        print("  No dependency chains found.")


def demonstrate_relationship_traversal():
    """Demonstrate various relationship traversal patterns."""
    print_header("Relationship Traversal Patterns")
    
    # Pattern 1: Find all tasks for a specific milestone
    print("\n  Pattern 1: Tasks for 'API Gateway Development'")
    
    gateway = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"name": "API Gateway Development"}
    })
    
    if gateway.data:
        # Tasks are linked via HAS_TASK (milestone -> task)
        # So we find tasks where MILESTONE matches our gateway
        tasks = db.records.find({
            "labels": ["TASK"],
            "where": {
                "MILESTONE": {"$id": gateway.data[0].id}
            }
        })
        
        print(f"  Found {len(tasks.data)} tasks:")
        for task in tasks.data:
            print(f"    - {task['name']} ({task.get('status')})")
    
    # Pattern 2: Find all milestones that depend on 'Database Migration'
    print("\n  Pattern 2: Milestones depending on 'Database Migration'")
    
    db_migration = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"name": "Database Migration"}
    })
    
    if db_migration.data:
        # Find milestones where DEPENDS_ON includes our DB migration
        dependents = db.records.find({
            "labels": ["MILESTONE"],
            "where": {
                "DEPENDS_ON": {"$id": {"$in": [db_migration.data[0].id]}}
            }
        })
        
        print(f"  Found {len(dependents.data)} dependent milestones:")
        for ms in dependents.data:
            print(f"    - {ms['name']}")
    
    # Pattern 3: Find the parent plan of a milestone
    print("\n  Pattern 3: Parent plan for 'Auth Service Implementation'")
    
    auth = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"name": "Auth Service Implementation"}
    })
    
    if auth.data:
        # Plans link to milestones via HAS_MILESTONE
        plans = db.records.find({
            "labels": ["PLAN"],
            "where": {
                "MILESTONE": {"$id": auth.data[0].id}
            }
        })
        
        if plans.data:
            print(f"  Parent plan: {plans.data[0]['name']}")
            print(f"  Plan status: {plans.data[0].get('status')}")


def main():
    print("\n" + "=" * 60)
    print("  RushDB Graph-Backed Plan Execution Tracker")
    print("  Demonstrating Milestone Dependency Management")
    print("=" * 60)
    
    # Check if data exists
    plans = db.records.find({"labels": ["PLAN"]})
    if not plans.data:
        print("\n⚠️  No data found. Run 'python seed.py' first to populate the database.")
        return
    
    # Run all demonstrations
    show_plan_progress()
    show_milestone_dependencies()
    demonstrate_relationship_traversal()
    find_blocked_milestones()
    find_ready_milestones()
    show_critical_path()
    show_tasks_by_assignee()
    
    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print(" =" * 60)
    print("\n  Key Takeaways:")
    print("  • RushDB models plans, milestones, and tasks as a property graph")
    print("  • Dependencies are first-class relationships (not foreign keys)")
    print("  • Query by related labels to traverse the graph")
    print("  • Upsert enables idempotent status updates")
    print("  • Plan progress is derived from milestone status aggregation")
    print("\n  Learn more: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
