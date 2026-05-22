"""
Workflow Engine - Relationship-Triggered Actions Core Implementation
======================================================================

This module implements the core pattern for agentic workflow automation using RushDB.
The key insight: relationships in the graph are first-class citizens that can trigger
downstream actions.

Pattern Overview:
---------------
1. Create records (workflows, tasks, agents)
2. Attach relationships (DEPENDS_ON, CONTAINS, ASSIGNED_TO)
3. Query relationships to find ready tasks
4. Trigger actions when relationships are created/modified
5. Propagate changes through the graph
"""

from datetime import datetime
from typing import List, Optional
from rushdb import RushDB
from rushdb.models import Record


class WorkflowEngine:
    """
    Orchestrates workflow execution by monitoring relationships and triggering actions.
    
    The engine observes:
    - TASK → WORKFLOW relationships (task belongs to workflow)
    - TASK → TASK relationships (task depends on another)
    - AGENT → TASK relationships (agent assigned to task)
    
    When these relationships change, the engine triggers appropriate actions.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def create_workflow(self, name: str, description: str = "") -> Record:
        """
        Create a new workflow with timestamp metadata.
        
        Args:
            name: Workflow identifier
            description: Optional description
            
        Returns:
            Created workflow Record
        """
        return self.db.records.create(
            label="WORKFLOW",
            data={
                "name": name,
                "description": description,
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
        )
    
    def create_task(
        self,
        workflow: Record,
        title: str,
        capability: str,
        priority: int = 1
    ) -> Record:
        """
        Create a task within a workflow context.
        
        The task is automatically attached to the workflow via a CONTAINS
        relationship. Initial status is 'pending' unless no dependencies,
        in which case it's 'ready'.
        
        Args:
            workflow: Parent workflow record
            title: Task name/description
            capability: Required agent capability (code, review, deploy)
            priority: Task priority (1 = highest)
            
        Returns:
            Created task Record with CONTAINS relationship to workflow
        """
        # Create task record
        task = self.db.records.create(
            label="TASK",
            data={
                "title": title,
                "capability": capability,
                "priority": priority,
                "status": "pending",  # Will be updated to 'ready' if no dependencies
                "created_at": datetime.now().isoformat()
            }
        )
        
        # Attach task to workflow
        self.db.records.attach(
            source=workflow,
            target=task,
            options={"type": "CONTAINS"}
        )
        
        # Check if task has any dependencies
        dependencies = self.db.records.find({
            "labels": ["TASK"],
            "where": {
                "TASK": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "in"},
                    "__id": task.id
                }
            }
        })
        
        # If no dependencies, mark as ready immediately
        if not dependencies:
            self._activate_task(task)
        
        return task
    
    def add_dependency(self, task: Record, depends_on: Record) -> None:
        """
        Add a dependency relationship between tasks.
        
        Creates a DEPENDS_ON relationship from task to depends_on.
        If depends_on is completed, triggers activation of task.
        
        Args:
            task: The dependent task (will be blocked until depends_on completes)
            depends_on: The task that must complete first
        """
        self.db.records.attach(
            source=task,
            target=depends_on,
            options={"type": "DEPENDS_ON"}
        )
        print(f"    └── → depends on: {depends_on['title']}")
    
    def complete_task(self, task: Record) -> None:
        """
        Mark a task as completed and trigger downstream actions.
        
        This is where the relationship-triggered magic happens:
        1. Update task status to 'completed'
        2. Find all tasks that depend on this one
        3. Check if those tasks are now ready (all dependencies met)
        4. Activate ready tasks and notify agents
        
        Args:
            task: Task to mark as completed
        """
        # Update task status
        task.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        })
        
        print(f"    ✓ Marked as completed")
        
        # Find and activate dependent tasks
        self._propagate_completion(task)
        
        # Notify assigned agent
        if task.data.get("assigned_to"):
            self._log_action(
                action_type="task_completed",
                agent_name=task.data.get("assigned_to"),
                task_title=task.data.get("title")
            )
    
    def _propagate_completion(self, completed_task: Record) -> None:
        """
        Find tasks that depend on the completed task and check if they're ready.
        
        This implements the cascading completion pattern:
        - When Task A completes
        - Find all tasks that DEPEND_ON Task A
        - Check if ALL their dependencies are complete
        - If yes, activate the task
        """
        # Find tasks that depend on this one
        dependent_tasks = self.db.records.find({
            "labels": ["TASK"],
            "where": {
                "TASK": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "in"},
                    "__id": completed_task.id
                }
            }
        })
        
        for dependent in dependent_tasks:
            if self._are_all_dependencies_met(dependent):
                print(f"\n  → All dependencies met for: {dependent['title']}")
                self._activate_task(dependent)
    
    def _are_all_dependencies_met(self, task: Record) -> bool:
        """
        Check if all tasks this task depends on are completed.
        
        Uses RushDB's relationship querying to traverse the DEPENDS_ON edges.
        """
        # Find all tasks this one depends on
        dependencies = self.db.records.find({
            "labels": ["TASK"],
            "where": {
                "TASK": {
                    "$relation": {"type": "DEPENDS_ON", "direction": "out"},
                    "__id": task.id
                }
            }
        })
        
        # All dependencies must be completed
        return all(dep.data.get("status") == "completed" for dep in dependencies)
    
    def _activate_task(self, task: Record) -> None:
        """
        Activate a task: update status to 'ready' and notify an agent.
        
        This is the primary relationship-triggered action.
        When a task becomes ready, we:
        1. Update its status
        2. Find an agent with matching capability
        3. Assign the task to the agent
        4. Log the notification action
        """
        task.update({"status": "ready"})
        print(f"    ✓ Activated (status: ready)")
        
        # Find and assign an agent
        agent = self._select_agent_for_task(task)
        if agent:
            self._notify_agent(agent, task)
    
    def _select_agent_for_task(self, task: Record) -> Optional[Record]:
        """
        Find an available agent with the required capability.
        
        Uses RushDB's property-based querying to find agents by capability.
        In a real system, this would also consider agent load, availability, etc.
        """
        agents = self.db.records.find({
            "labels": ["AGENT"],
            "where": {
                "capability": task.data.get("capability"),
                "status": "available"
            },
            "limit": 1
        })
        
        if agents:
            return agents[0]
        
        # Fallback: any available agent
        any_agent = self.db.records.find({
            "labels": ["AGENT"],
            "where": {"status": "available"},
            "limit": 1
        })
        
        return any_agent[0] if any_agent else None
    
    def _notify_agent(self, agent: Record, task: Record) -> None:
        """
        Assign task to agent and log the notification.
        
        This creates an ASSIGNED_TO relationship and records the
        relationship-triggered action in the graph.
        """
        # Create assignment relationship
        self.db.records.attach(
            source=agent,
            target=task,
            options={"type": "ASSIGNED_TO"}
        )
        
        # Update task with assignment info
        task.update({
            "assigned_to": agent.data.get("name"),
            "assigned_at": datetime.now().isoformat()
        })
        
        # Log the action
        self._log_action(
            action_type="agent_notified",
            agent_name=agent.data.get("name"),
            task_title=task.data.get("title")
        )
        
        print(f"    → Notified agent: {agent.data.get('name')} (capability: {agent.data.get('capability')})")
    
    def _log_action(self, action_type: str, agent_name: str, task_title: str) -> None:
        """
        Record an action in the graph for audit and debugging.
        
        ACTION_LOG records capture the relationship-triggered events
        that drive the workflow. This provides visibility into the
        automation logic.
        """
        self.db.records.create(
            label="ACTION_LOG",
            data={
                "type": action_type,
                "agent_name": agent_name,
                "task_title": task_title,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def process_ready_tasks(self) -> None:
        """
        Process all tasks currently in 'ready' status.
        
        This scans for ready tasks and ensures agents are assigned.
        Useful for catching any tasks that became ready but weren't processed.
        """
        ready_tasks = self.db.records.find({
            "labels": ["TASK"],
            "where": {"status": "ready"}
        })
        
        for task in ready_tasks:
            if not task.data.get("assigned_to"):
                agent = self._select_agent_for_task(task)
                if agent:
                    self._notify_agent(agent, task)
