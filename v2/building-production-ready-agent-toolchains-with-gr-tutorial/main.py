#!/usr/bin/env python3
"""
Building Production-Ready Agent Toolchains with Graph-Native Orchestration

This tutorial demonstrates how to build production-grade agent toolchains using
RushDB's property graph and vector search capabilities.

The tutorial covers:
1. Graph schema design for tools, agents, and tasks
2. Semantic tool routing using vector search
3. Graph traversal orchestration
4. Failure handling with checkpoint retry
5. Execution trace analysis
"""

import os
import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(API_KEY)

# Vector index configuration
INDEX_LABEL = "TOOL"
INDEX_PROPERTY = "description"
EMBEDDING_DIMENSIONS = 384  # Default for all-MiniLM-L6-v2


# ============================================================================
# PHASE 1: GRAPH SCHEMA SETUP
# ============================================================================

def phase1_schema_setup():
    """
    Create the graph schema for agent toolchains.
    
    Node types:
    - TOOL: Executable functions with descriptions
    - AGENT: Autonomous entities with intents
    - TASK: Units of work to be executed
    - CATEGORY: Grouping for tools
    - EXECUTION_TRACE: Historical execution records
    - CHECKPOINT: Recovery points for failed executions
    
    Relationship types:
    - CAN_USE: Agent -> Tool (capability mapping)
    - ASSIGNED_TO: Task -> Agent
    - DEPENDS_ON: Task -> Task (execution order)
    - HAS_TRACE: Task -> EXECUTION_TRACE
    - PART_OF_CATEGORY: Tool -> CATEGORY
    """
    print("\n" + "="*60)
    print("PHASE 1: Graph Schema Setup")
    print("="*60)
    
    # Check if data already exists
    existing_tools = db.records.find({"labels": ["TOOL"], "limit": 1})
    existing_agents = db.records.find({"labels": ["AGENT"], "limit": 1})
    existing_tasks = db.records.find({"labels": ["TASK"], "limit": 1})
    
    if existing_tools.data:
        print(f"✓ Found {len(existing_tools.data)} TOOL nodes (reusing existing data)")
    else:
        print("✗ No TOOL nodes found. Run 'python seed.py' first.")
        return False
    
    if existing_agents.data:
        print(f"✓ Found {len(existing_agents.data)} AGENT nodes")
    
    if existing_tasks.data:
        print(f"✓ Found {len(existing_tasks.data)} TASK nodes")
    
    # Count total relationships
    tools = db.records.find({"labels": ["TOOL"], "limit": 1000})
    agents = db.records.find({"labels": ["AGENT"], "limit": 1000})
    tasks = db.records.find({"labels": ["TASK"], "limit": 1000})
    
    print(f"\n✓ Graph schema ready:")
    print(f"  - {len(tools.data)} TOOL nodes")
    print(f"  - {len(agents.data)} AGENT nodes")
    print(f"  - {len(tasks.data)} TASK nodes")
    print(f"  - Relationships: CAN_USE, ASSIGNED_TO, DEPENDS_ON, HAS_TRACE")
    
    return True


# ============================================================================
# PHASE 2: VECTOR INDEX FOR SEMANTIC SEARCH
# ============================================================================

def phase2_vector_index():
    """
    Create a vector index on tool descriptions for semantic search.
    
    This enables finding relevant tools by matching natural language
    queries against tool descriptions - the foundation of semantic routing.
    """
    print("\n" + "="*60)
    print("PHASE 2: Vector Index for Semantic Tool Routing")
    print("="*60)
    
    # Check for existing indexes
    existing_indexes = db.ai.indexes.find()
    
    # Find our tool description index
    tool_index = None
    for idx in existing_indexes.data:
        if idx.get("label") == INDEX_LABEL and idx.get("propertyName") == INDEX_PROPERTY:
            tool_index = idx
            break
    
    if tool_index:
        print(f"✓ Found existing vector index: {tool_index.get('__id')}")
        print(f"  Status: {tool_index.get('status')}")
        stats = db.ai.indexes.stats(tool_index.get("__id"))
        print(f"  Indexed records: {stats.data.get('indexedRecords', 0)}")
    else:
        print(f"Creating vector index on {INDEX_LABEL}.{INDEX_PROPERTY}...")
        
        # Create index with external source (we provide vectors)
        index_response = db.ai.indexes.create({
            "label": INDEX_LABEL,
            "propertyName": INDEX_PROPERTY,
            "sourceType": "external",
            "dimensions": EMBEDDING_DIMENSIONS,
            "similarityFunction": "cosine",
        })
        
        tool_index = index_response.data
        index_id = tool_index.get("__id")
        print(f"✓ Created vector index: {index_id}")
        
        # Get all tools and generate embeddings
        print("\nGenerating embeddings for tool descriptions...")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            tools = db.records.find({"labels": [INDEX_LABEL], "limit": 1000})
            
            items = []
            for i, tool in enumerate(tools.data):
                description = tool.data.get(INDEX_PROPERTY, "")
                if description:
                    embedding = model.encode(description).tolist()
                    items.append({
                        "recordId": tool.id,
                        "vector": embedding,
                    })
                
                if (i + 1) % 5 == 0:
                    print(f"  Generated {i + 1}/{len(tools.data)} embeddings...")
            
            # Upsert vectors in batches
            db.ai.indexes.upsert_vectors(index_id, {"items": items})
            print(f"✓ Indexed {len(items)} tool descriptions")
            
        except ImportError:
            print("⚠ sentence-transformers not installed. Vector search will use server-side embedding.")
            print("  Install with: pip install sentence-transformers")
    
    return True


# ============================================================================
# PHASE 3: SEMANTIC TOOL ROUTING
# ============================================================================

def phase3_semantic_routing():
    """
    Demonstrate semantic tool routing using vector search.
    
    Given a natural language query (agent intent), find the most
    relevant tools by comparing query embedding against tool descriptions.
    """
    print("\n" + "="*60)
    print("PHASE 3: Semantic Tool Routing")
    print("="*60)
    
    # Example queries from different agents
    queries = [
        {
            "agent": "customer_insights_agent",
            "query": "I need to analyze customer sentiment from reviews",
        },
        {
            "agent": "data_pipeline_agent",
            "query": "Extract data from APIs and transform it for storage",
        },
        {
            "agent": "notification_agent", 
            "query": "Monitor events and send alerts to users",
        },
    ]
    
    for q in queries:
        print(f"\nAgent: {q['agent']}")
        print(f"Query: \"{q['query']}\"")
        
        # Semantic search for relevant tools
        results = db.ai.search({
            "propertyName": INDEX_PROPERTY,
            "query": q["query"],
            "labels": [INDEX_LABEL],
            "limit": 5,
        })
        
        print("\nTop 5 relevant tools:")
        for i, result in enumerate(results.data, 1):
            score = result.score or result.data.get("__score", 0)
            name = result.data.get("name", "unknown")
            desc = result.data.get("description", "")[:60]
            print(f"  {i}. [{score:.2f}] {name}")
            print(f"     {desc}...")
    
    # Also demonstrate filtered search by category
    print("\n" + "-"*40)
    print("Filtered search: NLP tools only")
    print("-"*40)
    
    nlp_results = db.ai.search({
        "propertyName": INDEX_PROPERTY,
        "query": "text analysis and processing",
        "labels": [INDEX_LABEL],
        "where": {"category": "nlp"},
        "limit": 5,
    })
    
    print("\nTop NLP tools:")
    for i, result in enumerate(nlp_results.data, 1):
        score = result.score or result.data.get("__score", 0)
        name = result.data.get("name", "unknown")
        print(f"  {i}. [{score:.2f}] {name}")
    
    return True


# ============================================================================
# PHASE 4: ORCHESTRATED EXECUTION
# ============================================================================

def phase4_orchestrated_execution():
    """
    Orchestrate tool execution by traversing the graph.
    
    This demonstrates:
    - Resolving task dependencies from graph structure
    - Executing tools in correct order
    - Recording results back to the graph
    """
    print("\n" + "="*60)
    print("PHASE 4: Orchestrated Execution")
    print("="*60)
    
    # Find a task with dependencies
    pending_tasks = db.records.find({
        "labels": ["TASK"],
        "where": {"status": "pending"},
        "limit": 1,
    })
    
    if not pending_tasks.data:
        print("No pending tasks found. Skipping execution demo.")
        return True
    
    task = pending_tasks.data[0]
    task_name = task.data.get("name", "unknown")
    
    print(f"\nExecuting task: {task_name}")
    
    # Find dependencies (tasks this task depends on)
    depends_on_query = db.records.find({
        "labels": ["TASK"],
        "where": {
            "TASK": {
                "$relation": {"type": "DEPENDS_ON", "direction": "in"},
                "name": task_name,
            }
        },
    })
    
    dependencies = []
    for dep in depends_on_query.data:
        dependencies.append({
            "name": dep.data.get("name"),
            "status": dep.data.get("status"),
            "result": dep.data.get("result"),
        })
    
    print(f"Dependencies: {[d['name'] for d in dependencies]}")
    
    # Simulate execution chain
    execution_chain = ["fetch_data", "process_data", "generate_insights", "send_notification"]
    print(f"\nExecution chain: {execution_chain}")
    
    execution_results = []
    
    with db.transactions.begin() as tx:
        for i, tool_name in enumerate(execution_chain):
            # Simulate tool execution
            time.sleep(0.1)  # Simulate work
            
            # Generate mock results
            if tool_name == "fetch_data":
                result = {"records_fetched": random.randint(100, 500)}
            elif tool_name == "process_data":
                result = {"records_processed": random.randint(50, 200)}
            elif tool_name == "generate_insights":
                result = {"insights_generated": random.randint(5, 20)}
            else:
                result = {"notification_sent": random.randint(1, 10)}
            
            # Create execution trace
            trace = db.records.create(
                label="EXECUTION_TRACE",
                data={
                    "tool_name": tool_name,
                    "task_name": task_name,
                    "status": "success",
                    "result": result,
                    "duration_ms": random.randint(50, 500),
                    "timestamp": datetime.now().isoformat(),
                    "step": i + 1,
                },
                transaction=tx,
            )
            
            execution_results.append({
                "tool": tool_name,
                "result": result,
                "trace_id": trace.id,
            })
            
            print(f"  ✓ {tool_name}: {result}")
    
    # Update task status
    db.records.update(
        record_id=task.id,
        data={
            "status": "completed",
            "result": f"Chain executed: {len(execution_results)} steps",
            "updated_at": datetime.now().isoformat(),
        }
    )
    
    print(f"\n✓ Executed {len(execution_results)} tools in sequence")
    print(f"✓ Task updated to completed status")
    
    return True


# ============================================================================
# PHASE 5: FAILURE HANDLING & RECOVERY
# ============================================================================

class ExecutionError(Exception):
    """Simulated execution failure."""
    pass


def phase5_failure_recovery():
    """
    Demonstrate failure handling and checkpoint-based recovery.
    
    The graph structure allows resuming from any checkpoint,
    not just the beginning of execution.
    """
    print("\n" + "="*60)
    print("PHASE 5: Failure Handling & Recovery")
    print("="*60)
    
    # Find existing checkpoints
    checkpoints = db.records.find({
        "labels": ["CHECKPOINT"],
        "limit": 10,
    })
    
    if not checkpoints.data:
        print("No checkpoints found. Creating a sample checkpoint...")
        
        # Find a task to checkpoint
        tasks = db.records.find({"labels": ["TASK"], "limit": 1})
        if tasks.data:
            task = tasks.data[0]
            
            checkpoint = db.records.create(
                label="CHECKPOINT",
                data={
                    "task_name": task.data.get("name"),
                    "checkpoint_at": "data_loaded",
                    "state": {
                        "records_loaded": 150,
                        "checksum": "abc123",
                    },
                    "created_at": datetime.now().isoformat(),
                }
            )
            print(f"✓ Created checkpoint: {checkpoint.id}")
    
    print("\nListing available checkpoints:")
    checkpoints = db.records.find({"labels": ["CHECKPOINT"], "limit": 10})
    
    for cp in checkpoints.data:
        print(f"  - {cp.data.get('task_name')} @ {cp.data.get('checkpoint_at')}")
        print(f"    State: {cp.data.get('state')}")
    
    # Simulate failure and recovery
    print("\n" + "-"*40)
    print("Simulating failure and recovery...")
    print("-"*40)
    
    execution_steps = ["fetch_data", "process_data", "generate_insights", "send_notification"]
    failure_at_step = 2  # Simulate failure at "generate_insights"
    
    print(f"\nExecution steps: {execution_steps}")
    print(f"Simulated failure at: {execution_steps[failure_at_step]}")
    
    # Save checkpoint before failure
    checkpoint_data = {
        "task_name": "recoverable_task",
        "checkpoint_at": execution_steps[failure_at_step - 1],
        "state": {
            "records_processed": 198,
            "checkpoint_time": datetime.now().isoformat(),
        },
        "completed_steps": execution_steps[:failure_at_step],
    }
    
    checkpoint = db.records.create(
        label="CHECKPOINT",
        data=checkpoint_data,
    )
    print(f"\n✓ Checkpoint saved: {checkpoint.id}")
    print(f"  Resume from: {checkpoint_data['checkpoint_at']}")
    print(f"  Completed steps: {checkpoint_data['completed_steps']}")
    
    # Simulate recovery
    remaining_steps = execution_steps[failure_at_step:]
    print(f"\nRecovery: Resuming with remaining steps: {remaining_steps}")
    
    with db.transactions.begin() as tx:
        for step in remaining_steps:
            # Simulate execution
            trace = db.records.create(
                label="EXECUTION_TRACE",
                data={
                    "tool_name": step,
                    "task_name": checkpoint_data["task_name"],
                    "status": "success",
                    "recovered_from_checkpoint": checkpoint.id,
                    "timestamp": datetime.now().isoformat(),
                },
                transaction=tx,
            )
            print(f"  ✓ {step} completed (recovered)")
    
    print("\n✓ Recovery successful!")
    print("  The graph structure allows resuming from any checkpoint,")
    print("  not just the beginning of execution.")
    
    return True


# ============================================================================
# PHASE 6: EXECUTION TRACE ANALYSIS
# ============================================================================

def phase6_trace_analysis():
    """
    Query execution history to understand agent decision-making.
    
    RushDB's graph structure makes it easy to analyze:
    - Tool usage patterns
    - Success/failure rates
    - Execution timing
    - Dependency resolution
    """
    print("\n" + "="*60)
    print("PHASE 6: Execution Trace Analysis")
    print("="*60)
    
    # Get all execution traces
    traces = db.records.find({
        "labels": ["EXECUTION_TRACE"],
        "orderBy": {"field": "timestamp", "direction": "desc"},
        "limit": 50,
    })
    
    print(f"\nFound {len(traces.data)} execution traces")
    
    # Analyze tool usage patterns
    tool_usage = {}
    for trace in traces.data:
        tool_name = trace.data.get("tool_name", "unknown")
        status = trace.data.get("status", "unknown")
        
        if tool_name not in tool_usage:
            tool_usage[tool_name] = {"total": 0, "success": 0, "failed": 0}
        
        tool_usage[tool_name]["total"] += 1
        if status == "success":
            tool_usage[tool_name]["success"] += 1
        else:
            tool_usage[tool_name]["failed"] += 1
    
    print("\nTool Usage Analysis:")
    print("-"*50)
    print(f"{'Tool':<25} {'Total':>8} {'Success':>10} {'Failed':>8}")
    print("-"*50)
    
    for tool, stats in sorted(tool_usage.items(), key=lambda x: -x[1]["total"]):
        success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"{tool:<25} {stats['total']:>8} {stats['success']:>10} {stats['failed']:>8}")
    
    # Analyze recent activity
    print("\n" + "-"*50)
    print("Recent Activity (last 24 hours):")
    print("-"*50)
    
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    recent_traces = db.records.find({
        "labels": ["EXECUTION_TRACE"],
        "where": {
            "timestamp": {"$gte": yesterday}
        },
        "limit": 100,
    })
    
    print(f"  Traces in last 24h: {len(recent_traces.data)}")
    
    # Group by hour
    hourly_counts = {}
    for trace in recent_traces.data:
        ts = trace.data.get("timestamp", "")
        if ts:
            hour = ts[:13]  # Get hour portion
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
    
    print("\n  Hourly distribution:")
    for hour in sorted(hourly_counts.keys())[-5:]:
        print(f"    {hour}:00 - {hourly_counts[hour]} traces")
    
    # Find failed executions for analysis
    print("\n" + "-"*50)
    print("Failed Executions (for root cause analysis):")
    print("-"*50)
    
    failed = db.records.find({
        "labels": ["EXECUTION_TRACE"],
        "where": {"status": "failed"},
        "limit": 10,
    })
    
    if failed.data:
        for f in failed.data:
            print(f"  - {f.data.get('tool_name')}: {f.data.get('error', 'Unknown error')}")
    else:
        print("  No failed executions found (all tools working correctly!)")
    
    # Analyze agent productivity
    print("\n" + "-"*50)
    print("Agent Productivity:")
    print("-"*50)
    
    agents = db.records.find({"labels": ["AGENT"], "limit": 10})
    
    for agent in agents.data:
        agent_name = agent.data.get("name")
        
        # Find tasks assigned to this agent
        agent_tasks = db.records.find({
            "labels": ["TASK"],
            "where": {"AGENT": {"$relation": {"type": "ASSIGNED_TO", "direction": "in"}}},
        })
        
        # Count tasks for this agent
        task_count = 0
        for task in agent_tasks.data:
            if "AGENT" in task.data:
                assigned_agent = task.data.get("AGENT", {})
                if isinstance(assigned_agent, dict) and assigned_agent.get("name") == agent_name:
                    task_count += 1
        
        print(f"  {agent_name}: {task_count} tasks assigned")
    
    return True


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute all tutorial phases."""
    print("\n" + "="*60)
    print("  Building Production-Ready Agent Toolchains")
    print("  with Graph-Native Orchestration")
    print("="*60)
    print("\nThis tutorial demonstrates RushDB features for building")
    print("production-grade agent toolchains.")
    
    try:
        # Phase 1: Schema setup
        if not phase1_schema_setup():
            print("\n⚠ Please run 'python seed.py' first to populate the database.")
            return
        
        # Phase 2: Vector index
        phase2_vector_index()
        
        # Phase 3: Semantic routing
        phase3_semantic_routing()
        
        # Phase 4: Orchestrated execution
        phase4_orchestrated_execution()
        
        # Phase 5: Failure recovery
        phase5_failure_recovery()
        
        # Phase 6: Trace analysis
        phase6_trace_analysis()
        
        print("\n" + "="*60)
        print("  Tutorial Complete!")
        print("="*60)
        print("\nYou've learned how to:")
        print("  ✓ Design graph schemas for agent toolchains")
        print("  ✓ Create vector indexes for semantic tool routing")
        print("  ✓ Route tools by intent using vector similarity")
        print("  ✓ Orchestrate execution via graph traversal")
        print("  ✓ Handle failures with checkpoint-based recovery")
        print("  ✓ Analyze execution traces for insights")
        print("\nNext steps:")
        print("  - Experiment with different agent intents")
        print("  - Add custom tools to the graph")
        print("  - Implement your own execution engine")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("  1. Your RUSHDB_API_KEY is valid")
        print("  2. You've run 'python seed.py' to populate data")
        print("  3. You have an active internet connection")
        raise


if __name__ == "__main__":
    main()
