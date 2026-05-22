# Relationship-Triggered Actions for Agentic Workflow Automation

A practical guide demonstrating how to build intelligent agentic workflows using RushDB's relationship graph. This example shows how AI agents can observe relationship changes and automatically trigger downstream actions.

## What This Tutorial Demonstrates

- **Graph-based workflow modeling** — Represent workflows, agents, and tasks as interconnected graph nodes
- **Relationship-triggered automation** — Detect when relationships change and automatically invoke actions
- **Agent coordination** — Route tasks to appropriate agents based on capabilities and availability
- **Transactional workflows** — Ensure atomicity when creating records, attaching relationships, and triggering actions

## The Scenario: Intelligent Task Routing

We model a multi-agent task system where:

1. **Tasks** are created and linked to specific workflow contexts
2. **Agents** have distinct capabilities (code, review, deploy)
3. When a task becomes `ready`, agents with matching capabilities are automatically notified
4. When an agent completes a task, dependent tasks are automatically activated
5. The entire graph propagates completion signals through relationship chains

```
Workflow
    └── Task A (depends_on: []) → ready → triggers → Agent notified
            └── Task B (depends_on: [A]) → blocked
            └── Task C (depends_on: [A]) → blocked
                    └── Task D (depends_on: [B, C]) → blocked

Agent completes Task A → Task B & C become ready → Agents notified → ...
```

## Prerequisites

- Python 3.10+
- A RushDB account (free tier works)
- RushDB Python SDK (`rushdb>=2.0.0`)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Initialize the database:**
   ```bash
   python main.py --setup
   ```
   This creates the necessary labels and optionally seeds sample data.

4. **Run the demo:**
   ```bash
   python main.py
   ```

## Project Structure

```
.
├── main.py          # Core workflow engine with relationship-triggered actions
├── workflow_engine.py  # Orchestrates tasks, agents, and automation logic
├── .env.example     # Environment variable template
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Key Patterns

### 1. Creating Related Records with Transactions

When creating a workflow with initial tasks, wrap everything in a transaction:

```sdk
with db.transactions.begin() as tx:
    workflow = db.records.create(
        label="WORKFLOW",
        data={"name": "Deploy v2.1", "status": "active"},
        transaction=tx
    )
    task = db.records.create(
        label="TASK",
        data={"title": "Build artifacts", "status": "ready"},
        transaction=tx
    )
    db.records.attach(source=workflow, target=task, options={"type": "CONTAINS"}, transaction=tx)
```

### 2. Querying by Relationship

Find all tasks in a workflow that have a specific status:

```sdk
ready_tasks = db.records.find({
    "labels": ["TASK"],
    "where": {
        "WORKFLOW": {"name": "Deploy v2.1"},
        "status": "ready"
    }
})
```

### 3. Attaching Tasks to Agents

When assigning a task to an agent, create the relationship:

```sdk
agent = db.records.find_one({"labels": ["AGENT"], "where": {"capability": "deploy"}})
task = db.records.find_one({"labels": ["TASK"], "where": {"title": "Deploy to production"}})
db.records.attach(source=agent, target=task, options={"type": "ASSIGNED_TO"})
```

### 4. Triggering Actions on Relationship Changes

The workflow engine monitors relationship changes and triggers actions:

```python
def on_task_assigned(agent, task):
    """Triggered when an agent is assigned to a task."""
    print(f"📬 Agent {agent['name']} assigned to {task['title']}")
    
    # Update task status
    task.update({"status": "in_progress", "assigned_at": datetime.now().isoformat()})
    
    # Record the notification
    db.records.create(label="ACTION_LOG", data={
        "type": "task_assigned",
        "agent_id": agent.id,
        "task_id": task.id,
        "timestamp": datetime.now().isoformat()
    })
```

## Expected Output

Running `python main.py` produces output showing:

1. **Database initialization** — Labels and sample data creation
2. **Workflow execution** — Tasks being created and routed to agents
3. **Relationship propagation** — Dependencies resolved and tasks activated
4. **Action logging** — All triggered actions recorded in the graph

## How It Works

### Phase 1: Setup
- Creates `WORKFLOW`, `TASK`, `AGENT`, and `ACTION_LOG` labels
- Seeds sample agents with different capabilities

### Phase 2: Workflow Execution
- Creates a deployment workflow with 4 interdependent tasks
- Tasks are linked via `DEPENDS_ON` relationships
- Workflow engine monitors task completion and activates dependents

### Phase 3: Agent Notification
- When a task becomes `ready`, finds agents with matching capability
- Creates `NOTIFIED` relationship to log the trigger
- Updates task with `assigned_to` and `assigned_at`

## Extending This Pattern

To adapt this for your use case:

1. **Custom triggers** — Modify `WorkflowEngine.on_task_completed()` to handle domain-specific events
2. **Agent selection** — Implement intelligent routing in `_select_agent_for_task()` based on load, expertise, or availability
3. **Escalation** — Add timeout-based escalation in `_check_pending_tasks()`
4. **Multi-workflow** — Run multiple `WorkflowEngine` instances for parallel workflow processing

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/relationship-triggered-actions-for-agentic-workflo-tutorial)
- [Python SDK Reference](https://docs.rushdb.com/sdk/python)
