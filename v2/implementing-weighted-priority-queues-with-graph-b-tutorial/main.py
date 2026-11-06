"""
Weighted Priority Queue Scheduler with Graph-Based Scheduling.

Demonstrates how to implement a weighted priority queue system using RushDB's
property graph model for task scheduling with dependencies.
"""

import os
from collections import defaultdict, deque
from datetime import datetime
from typing import Optional


from dotenv import load_dotenv

from rushdb import RushDB


class WeightedPriorityScheduler:
    """
    A scheduler that implements weighted priority queues using RushDB's graph model.
    
    Key features:
    - Weighted priority calculation
    - Topological sorting for dependency ordering
    - Graph traversal for dependency resolution
    """
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def calculate_weight(self, task: dict) -> float:
        """
        Calculate task weight based on priority and deadline urgency.
        
        Formula: weight = (priority / 10) * deadline_factor * effort_factor
        """
        priority = task.get("priority", 5)
        deadline_str = task.get("deadline")
        estimated_hours = task.get("estimated_hours", 1)
        
        # Calculate deadline urgency factor
        deadline_factor = 1.0
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                now = datetime.utcnow()
                hours_until = (deadline.replace(tzinfo=None) - now).total_seconds() / 3600
                
                if hours_until < 4:
                    deadline_factor = 2.0
                elif hours_until < 24:
                    deadline_factor = 1.5
            except (ValueError, TypeError):
                pass
        
        # Effort factor (longer tasks weighted slightly higher)
        effort_factor = 1.0 + (estimated_hours / 8.0)
        
        return round((priority / 10.0) * deadline_factor * effort_factor, 2)
    
    def get_dependencies(self, task_id: str) -> list:
        """
        Get all tasks that the given task depends on.
        
        Traverses DEPENDS_ON relationships to find upstream dependencies.
        """
        result = self.db.records.find({
            "labels": ["TASK"],
            "where": {
                "$id": {"$in": [task_id]}
            }
        })
        
        if not result.data:
            return []
        
        task = result.data[0]
        
        # Find tasks this task depends on
        depends_on_result = self.db.records.find({
            "labels": ["TASK"],
            "where": {
                "DEPENDS_ON": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "in"},
                    "$id": task_id
                }
            }
        })
        
        return [t["id"] for t in depends_on_result.data]
    
    def get_task_dependents(self, task_id: str) -> list:
        """
        Get all tasks that depend on the given task.
        
        Traverses DEPENDS_ON relationships to find downstream dependents.
        """
        result = self.db.records.find({
            "labels": ["TASK"],
            "where": {
                "DEPENDS_ON": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "out"},
                    "$id": task_id
                }
            }
        })
        
        return [{"id": t["id"], "name": t["name"]} for t in result.data]
    
    def topological_sort(self) -> list:
        """
        Perform weighted topological sort on the task dependency graph.
        
        Algorithm:
        1. Calculate in-degree for each task (number of unmet dependencies)
        2. Build a weighted ready queue from tasks with zero in-degree
        3. Process highest-weight tasks first
        4. When a task completes, reduce in-degree of its dependents
        5. Add newly-ready tasks to the queue
        
        Returns ordered list of tasks respecting dependencies and priority.
        """
        # Fetch all pending tasks
        all_tasks_result = self.db.records.find({
            "labels": ["TASK"],
            "where": {"status": "pending"}
        })
        
        if not all_tasks_result.data:
            return []
        
        # Build task lookup
        tasks_by_id = {t["id"]: t for t in all_tasks_result.data}
        
        # Calculate in-degree (unmet dependencies) for each task
        in_degree = defaultdict(int)
        dependents_map = defaultdict(list)  # task_id -> list of dependent task_ids
        
        for task in all_tasks_result.data:
            task_id = task["id"]
            dependencies = self.get_dependencies(task_id)
            in_degree[task_id] = len(dependencies)
            
            for dep_id in dependencies:
                dependents_map[dep_id].append(task_id)
        
        # Calculate weights and build priority queue
        task_weights = {}
        for task in all_tasks_result.data:
            task_weights[task["id"]] = self.calculate_weight(task)
        
        # Initialize ready queue with tasks that have no dependencies
        ready_queue = deque([
            (task_weights[t["id"]], t) 
            for t in all_tasks_result.data 
            if in_degree[t["id"]] == 0
        ])
        
        # Sort ready queue by weight (highest first)
        ready_queue = deque(sorted(ready_queue, key=lambda x: -x[0]))
        
        # Process queue
        schedule_order = []
        scheduled_ids = set()
        
        while ready_queue:
            # Pop highest priority task from queue
            _, current_task = ready_queue.popleft()
            task_id = current_task["id"]
            
            if task_id in scheduled_ids:
                continue
            
            schedule_order.append(current_task)
            scheduled_ids.add(task_id)
            
            # Reduce in-degree for dependents
            for dependent_id in dependents_map[task_id]:
                in_degree[dependent_id] -= 1
                
                # If all dependencies met, add to ready queue
                if in_degree[dependent_id] == 0:
                    dependent_task = tasks_by_id[dependent_id]
                    weight = task_weights[dependent_id]
                    ready_queue.append((weight, dependent_task))
            
            # Re-sort queue by weight
            ready_queue = deque(sorted(ready_queue, key=lambda x: -x[0]))
        
        return schedule_order
    
    def get_tasks_by_priority_tier(self, tasks: list) -> dict:
        """Categorize tasks into priority tiers."""
        tiers = {
            "Critical (weight >= 9)": [],
            "High (weight 7-9)": [],
            "Standard (weight < 7)": []
        }
        
        for task in tasks:
            weight = task.get("weight", 0)
            if weight >= 9:
                tiers["Critical (weight >= 9)"].append(task["name"])
            elif weight >= 7:
                tiers["High (weight 7-9)"].append(task["name"])
            else:
                tiers["Standard (weight < 7)"].append(task["name"])
        
        return tiers
    
    def run(self) -> dict:
        """
        Execute the weighted priority queue scheduler.
        
        Returns scheduling results including execution order and statistics.
        """
        # Fetch all pending tasks
        all_tasks = self.db.records.find({
            "labels": ["TASK"],
            "where": {"status": "pending"},
            "orderBy": {"createdAt": "asc"}
        }).data
        
        # Perform weighted topological sort
        schedule = self.topological_sort()
        
        return {
            "all_tasks": all_tasks,
            "schedule": schedule,
            "total_tasks": len(all_tasks),
            "scheduled_tasks": len(schedule)
        }


def display_results(scheduler: WeightedPriorityScheduler, results: dict):
    """Pretty-print scheduling results."""
    
    print("\n" + "=" * 60)
    print("   WEIGHTED PRIORITY QUEUE SCHEDULER RESULTS")
    print("=" * 60)
    
    # Display all tasks
    print("\n📋 All Pending Tasks (as stored):")
    for task in results["all_tasks"]:
        name = task.get("name", "Unnamed")
        priority = task.get("priority", "?")
        weight = task.get("weight", "?")
        category = task.get("category", "?")
        print(f"   • {name}")
        print(f"     Priority: {priority}, Weight: {weight}, Category: {category}")
    
    # Display dependency graph
    print("\n🔗 Dependency Graph:")
    for task in results["all_tasks"]:
        dependents = scheduler.get_task_dependents(task["id"])
        if dependents:
            print(f"   {task['name']} is required by:")
            for dep in dependents:
                print(f"     → {dep['name']}")
    
    # Display scheduled order
    print("\n📊 Scheduled Execution Order (Weighted Topological Sort):")
    for i, task in enumerate(results["schedule"], 1):
        name = task.get("name", "Unnamed")
        weight = task.get("weight", "?")
        deps = scheduler.get_dependencies(task["id"])
        status = "ready" if not deps else "dependencies met"
        print(f"   {i}. {name} (weight={weight}, {status})")
    
    # Display priority tiers
    print("\n📈 Tasks by Priority Tier:")
    tiers = scheduler.get_tasks_by_priority_tier(results["all_tasks"])
    for tier_name, tier_tasks in tiers.items():
        if tier_tasks:
            print(f"   {tier_name}:")
            for task_name in tier_tasks:
                print(f"     • {task_name}")
    
    # Summary
    print("\n" + "-" * 60)
    print(f"Summary: {results['scheduled_tasks']}/{results['total_tasks']} tasks scheduled")
    print("=" * 60)


def demo_graph_traversal(db: RushDB):
    """
    Demonstrate RushDB graph traversal capabilities for scheduling.
    """
    print("\n" + "=" * 60)
    print("   GRAPH TRAVERSAL DEMONSTRATION")
    print("=" * 60)
    
    # Find all tasks with their dependencies
    print("\n🔍 Finding tasks and their upstream dependencies...")
    
    tasks = db.records.find({
        "labels": ["TASK"],
        "where": {"status": "pending"},
        "limit": 5
    }).data
    
    for task in tasks:
        print(f"\n   Task: {task['name']}")
        print(f"   Weight: {task.get('weight', 'N/A')}")
        
        # Find what this task depends on
        deps = db.records.find({
            "labels": ["TASK"],
            "where": {
                "DEPENDS_ON": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "in"},
                    "$id": task["id"]
                }
            }
        })
        
        if deps.data:
            print(f"   Dependencies ({len(deps.data)}):")
            for dep in deps.data:
                print(f"     ← {dep['name']}")
        else:
            print(f"   Dependencies: None (ready to execute)")

        
        # Find tasks that depend on this one
        dependents = db.records.find({
            "labels": ["TASK"],
            "where": {
                "DEPENDS_ON": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "out"},
                    "$id": task["id"]
                }
            }
        })
        
        if dependents.data:
            print(f"   Required by ({len(dependents.data)} tasks):")
            for dep in dependents.data:
                print(f"     → {dep['name']}")


def main():
    """Main entry point for the weighted priority queue scheduler."""
    
    load_dotenv()
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("❌ Error: RUSHDB_API_KEY not found in environment")
        print("   Please copy .env.example to .env and add your API key")
        return
    
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    
    print("\n" + "=" * 60)
    print("   WEIGHTED PRIORITY QUEUE SCHEDULER")
    print("   Using RushDB Graph-Based Scheduling")
    print("=" * 60)
    
    try:
        # Initialize scheduler
        scheduler = WeightedPriorityScheduler(db)
        
        # Run the scheduler
        results = scheduler.run()
        
        if not results["all_tasks"]:
            print("\n⚠️  No pending tasks found.")
            print("   Run 'python seed.py' first to create task data.")
            return
        
        # Display results
        display_results(scheduler, results)
        
        # Demonstrate graph traversal
        demo_graph_traversal(db)
        
        print("\n✨ Scheduling complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
