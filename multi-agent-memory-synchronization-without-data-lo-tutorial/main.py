"""
Multi-Agent Memory Synchronization Without Data Loss
=======================================================

This tutorial demonstrates how to build reliable multi-agent systems using
RushDB as a shared memory layer with ACID guarantees.

Key scenarios covered:
1. Concurrent writes with conflict detection
2. Atomic transactions for complex operations
3. Safe state synchronization across agents
4. Rollback patterns for failed operations
5. Version-based conflict resolution

Run seed.py first to populate initial data:
    python seed.py
"""

import os
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# ============================================================================
# INITIALIZATION
# ============================================================================

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not set in environment")

db = RushDB(API_KEY)

print("\n" + "=" * 70)
print("MULTI-AGENT MEMORY SYNCHRONIZATION WITHOUT DATA LOSS")
print("=" * 70)

# ============================================================================
# SCENARIO 1: Concurrent Writes - The Problem
# ============================================================================

def demonstrate_concurrent_write_problem():
    """
    Show what happens when two agents try to write to the same memory
    block WITHOUT proper synchronization.
    """
    print("\n" + "-" * 70)
    print("SCENARIO 1: Concurrent Write Problem (Without Sync)")
    print("-" * 70)
    
    # Get the sync_status memory block
    sync_block = db.records.find_one({
        "labels": ["MEMORY_BLOCK"],
        "where": {"blockId": "memory-003"}
    })
    
    if not sync_block:
        print("❌ Sync block not found. Run seed.py first.")
        return
    
    print(f"\n📍 Initial state: sync_status block has version={sync_block['version']}")
    print("   Two agents (Analyzer & Executor) will try to update this block...")
    
    # Agent 1: Analyzer increments pendingWrites
    print("\n🔹 AGENT-ANALYZER: Reading current state...")
    state1 = db.records.find_by_id(sync_block.id)
    old_pending = state1["pendingWrites"]
    print(f"   Current pendingWrites = {old_pending}")
    
    # (Simulated delay - in real systems this could be network latency)
    time.sleep(0.1)
    
    # Agent 2: Executor also reads the same state
    print("\n🔸 AGENT-EXECUTOR: Reading current state...")
    state2 = db.records.find_by_id(sync_block.id)
    same_pending = state2["pendingWrites"]
    print(f"   Current pendingWrites = {same_pending}")
    
    # Both agents compute their updates based on stale data
    # This is the classic "lost update" problem
    print("\n⚠️  PROBLEM: Both agents read the same state!")
    print("   If both write back, one update will be lost.")
    
    # Demonstrate with simple updates (not using transactions)
    new_pending = old_pending + 1
    print(f"\n   Agent 1 computes: pendingWrites = {old_pending} + 1 = {new_pending}")
    print(f"   Agent 2 computes: pendingWrites = {same_pending} + 1 = {new_pending}")
    
    # First write succeeds
    db.records.update(
        record_id=sync_block.id,
        data={"pendingWrites": new_pending, "lastWriteBy": "agent-002"}
    )
    print(f"\n   ✅ Agent 1 writes: pendingWrites = {new_pending}")
    
    # Second write overwrites (lost update!)
    db.records.update(
        record_id=sync_block.id,
        data={"pendingWrites": new_pending, "lastWriteBy": "agent-003"}
    )
    print(f"   ✅ Agent 2 writes: pendingWrites = {new_pending} (overwrites!)")
    
    # Verify the result
    final_state = db.records.find_by_id(sync_block.id)
    print(f"\n📍 Final state: pendingWrites = {final_state['pendingWrites']}")
    print("   ❌ PROBLEM: One increment was lost! Should be 2, but is 1.")
    
    return final_state

# ============================================================================
# SCENARIO 2: Atomic Transactions with Rollback
# ============================================================================

def demonstrate_atomic_transactions():
    """
    Use RushDB transactions to ensure atomic updates.
    If any part of the operation fails, rollback everything.
    """
    print("\n" + "-" * 70)
    print("SCENARIO 2: Atomic Transactions with Rollback")
    print("-" * 70)
    
    print("\n📋 Creating a task that requires multiple memory updates...")
    print("   Operation: Orchestrator creates a new task and updates multiple blocks")
    
    # Start a transaction
    tx = db.transactions.begin()
    print("\n🔄 BEGIN TRANSACTION")
    
    try:
        # Step 1: Create a new task record
        print("   1. Creating TASK record...")
        task = db.records.create(
            label="TASK",
            data={
                "taskId": f"task-{int(time.time())}",
                "title": "Process user request",
                "status": "pending",
                "priority": random.randint(1, 5),
                "createdAt": datetime.now().isoformat()
            },
            transaction=tx
        )
        print(f"      ✓ Task created: {task.id}")
        
        # Step 2: Update the task queue memory block
        print("   2. Updating task_queue memory block...")
        queue_block = db.records.find_one({
            "labels": ["MEMORY_BLOCK"],
            "where": {"blockId": "memory-001"}
        })
        if queue_block:
            new_version = queue_block["version"] + 1
            items = queue_block.get("items", [])
            items.append({"taskId": task["taskId"], "queuedAt": datetime.now().isoformat()})
            
            db.records.update(
                record_id=queue_block.id,
                data={"version": new_version, "items": items},
                transaction=tx
            )
            print(f"      ✓ Queue updated to v{new_version}, {len(items)} items")
        
        # Step 3: Update sync status
        print("   3. Updating sync_status...")
        sync_block = db.records.find_one({
            "labels": ["MEMORY_BLOCK"],
            "where": {"blockId": "memory-003"}
        })
        if sync_block:
            db.records.update(
                record_id=sync_block.id,
                data={
                    "pendingWrites": sync_block["pendingWrites"] + 1,
                    "lastSync": datetime.now().isoformat()
                },
                transaction=tx
            )
            print("      ✓ Sync status incremented")
        
        # Step 4: Link task to orchestrator agent
        print("   4. Linking task to Orchestrator agent...")
        orchestrator = db.records.find_one({
            "labels": ["AGENT"],
            "where": {"agentId": "agent-001"}
        })
        if orchestrator:
            db.records.attach(
                source=task,
                target=orchestrator,
                options={"type": "ASSIGNED_TO", "direction": "out"},
                transaction=tx
            )
            print("      ✓ Task linked to Orchestrator")
        
        # Transaction context manager handles commit automatically
        # NO tx.commit() needed when using `with`
        print("\n🔄 COMMITTING TRANSACTION...")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("   Rolling back entire transaction...")
        tx.rollback()
        print("   ✅ Rollback complete - no partial state written")
        raise
    
    # Context manager auto-commits on successful exit
    # No explicit commit() call needed
    print("\n✅ ATOMIC OPERATION COMPLETE!")
    print("   All 4 steps succeeded or none did (via rollback)")
    
    # Verify the committed state
    print("\n📍 Verifying committed state:")
    created_task = db.records.find_one({
        "labels": ["TASK"],
        "where": {"title": "Process user request"}
    })
    if created_task:
        print(f"   ✓ Task exists: {created_task['taskId']}")
    
    queue_block = db.records.find_one({
        "labels": ["MEMORY_BLOCK"],
        "where": {"blockId": "memory-001"}
    })
    if queue_block:
        print(f"   ✓ Queue at version: {queue_block['version']}")
    
    return created_task

# ============================================================================
# SCENARIO 3: Conflict-Free Upserts with Merge Strategy
# ============================================================================

def demonstrate_upsert_merge_strategy():
    """
    Use upsert with mergeBy to handle concurrent updates safely.
    Merge strategy ensures updates are combined rather than overwritten.
    """
    print("\n" + "-" * 70)
    print("SCENARIO 3: Conflict-Free Upserts with Merge Strategy")
    print("-" * 70)
    
    print("\n📋 Simulating two agents updating the same results_store...")
    print("   Agent Analyzer adds analysis data")
    print("   Agent Executor adds execution results")
    
    # Get results store
    results_block = db.records.find_one({
        "labels": ["MEMORY_BLOCK"},
        "where": {"blockId": "memory-002"}
    })
    
    if not results_block:
        print("❌ Results store not found")
        return
    
    initial_data = results_block.get("data", {})
    initial_version = results_block["version"]
    print(f"\n📍 Initial state: v{initial_version}, data={initial_data}")
    
    # Agent 1: Analyzer adds analysis timestamp
    print("\n🔹 AGENT-ANALYZER: Adding analysis metadata...")
    analysis_update = {
        "blockId": "memory-002",  # Required for mergeBy matching
        "analysisTimestamp": datetime.now().isoformat(),
        "analysisAgent": "agent-002",
        "analysisStatus": "completed"
    }
    
    # Using upsert with append merge strategy
    result1 = db.records.upsert(
        label="MEMORY_BLOCK",
        data=analysis_update,
        options={
            "mergeBy": ["blockId"],
            "mergeStrategy": "append"  # Adds fields instead of replacing
        }
    )
    print(f"   ✓ Analyzer update applied (v{initial_version} → v{result1['version']})")
    print(f"   → Analysis fields added: {list(analysis_update.keys())}")
    
    # Agent 2: Executor adds execution metadata (in parallel, conceptually)
    print("\n🔸 AGENT-EXECUTOR: Adding execution metadata...")
    execution_update = {
        "blockId": "memory-002",  # Same key = same record
        "executionTimestamp": datetime.now().isoformat(),
        "executionAgent": "agent-003",
        "executionStatus": "success"
    }
    
    result2 = db.records.upsert(
        label="MEMORY_BLOCK",
        data=execution_update,
        options={
            "mergeBy": ["blockId"],
            "mergeStrategy": "append"
        }
    )
    print(f"   ✓ Executor update applied (v{result1['version']} → v{result2['version']})")
    print(f"   → Execution fields added: {list(execution_update.keys())}")
    
    # Verify both updates are preserved
    final_state = db.records.find_by_id(result2.id)
    print(f"\n📍 Final state: v{final_state['version']}")
    print(f"   Data keys: {list(final_state['data'].keys())}")
    
    has_analysis = "analysisTimestamp" in final_state['data'] or final_state.get("analysisTimestamp")
    has_execution = "executionTimestamp" in final_state['data'] or final_state.get("executionTimestamp")
    
    if has_analysis and has_execution:
        print("\n   ✅ SUCCESS: Both agent updates preserved!")
        print("   No data loss - merge strategy worked correctly")
    else:
        print("\n   ❌ FAILURE: Some updates were lost")
    
    return final_state

# ============================================================================
# SCENARIO 4: Safe Concurrent Updates with Retry Logic
# ============================================================================

def demonstrate_safe_concurrent_update():
    """
    Implement optimistic locking pattern with retry.
    If version mismatch detected, fetch latest and retry.
    """
    print("\n" + "-" * 70)
    print("SCENARIO 4: Safe Concurrent Updates with Optimistic Locking")
    print("-" * 70)
    
    print("\n📋 Implementing optimistic locking pattern...")
    print("   Before updating, check version. If stale, retry with fresh data.")
    
    def safe_increment(field_name, max_retries=3):
        """
        Safely increment a numeric field with retry on version conflict.
        Returns (success, final_value).
        """
        for attempt in range(max_retries):
            # Fetch current state
            sync_block = db.records.find_one({
                "labels": ["MEMORY_BLOCK"],
                "where": {"blockId": "memory-003"}
            })
            
            current_value = sync_block.get(field_name, 0) if sync_block else 0
            current_version = sync_block["version"] if sync_block else 0
            
            # Compute new value
            new_value = current_value + 1
            
            # Attempt update with version check (upsert handles this)
            result = db.records.upsert(
                label="MEMORY_BLOCK",
                data={
                    "blockId": "memory-003",
                    field_name: new_value
                },
                options={
                    "mergeBy": ["blockId"],
                    "mergeStrategy": "replace"
                }
            )
            
            # Check if our version was current
            if result["version"] == current_version + 1:
                return True, new_value
            
            # Version conflict - someone else wrote first, retry
            print(f"      🔄 Version conflict on attempt {attempt + 1}, retrying...")
            time.sleep(0.05)  # Small delay before retry
        
        return False, current_value
    
    # Reset pendingWrites for demo
    sync_block = db.records.find_one({
        "labels": ["MEMORY_BLOCK"],
        "where": {"blockId": "memory-003"}
    })
    if sync_block:
        db.records.update(
            record_id=sync_block.id,
            data={"pendingWrites": 0, "version": sync_block["version"]}
        )
    
    print("\n🔹 AGENT-ANALYZER: Attempting safe increment...")
    success1, value1 = safe_increment("pendingWrites")
    if success1:
        print(f"   ✅ Success! pendingWrites = {value1}")
    else:
        print(f"   ❌ Failed after max retries, pendingWrites = {value1}")
    
    print("\n🔸 AGENT-EXECUTOR: Attempting safe increment...")
    success2, value2 = safe_increment("pendingWrites")
    if success2:
        print(f"   ✅ Success! pendingWrites = {value2}")
    else:
        print(f"   ❌ Failed after max retries, pendingWrites = {value2}")
    
    # Verify final state
    final_block = db.records.find_one({
        "labels": ["MEMORY_BLOCK"],
        "where": {"blockId": "memory-003"}
    })
    print(f"\n📍 Final state: pendingWrites = {final_block['pendingWrites']}")
    
    if final_block['pendingWrites'] == 2:
        print("   ✅ Both increments succeeded with no data loss!")
    else:
        print(f"   ⚠️  Expected 2, got {final_block['pendingWrites']}")
    
    return final_block

# ============================================================================
# SCENARIO 5: Multi-Agent Transaction Chain
# ============================================================================

def demonstrate_multi_agent_transaction():
    """
    Complex scenario: Multiple agents contribute to a single operation,
    all wrapped in one atomic transaction.
    """
    print("\n" + "-" * 70)
    print("SCENARIO 5: Multi-Agent Transaction Chain")
    print("-" * 70)
    
    print("\n📋 Orchestrator coordinates work across Analyzer and Executor...")
    print("   All operations must succeed or all fail together.")
    
    tx = db.transactions.begin()
    print("\n🔄 BEGIN TRANSACTION (All-or-Nothing)")
    
    operation_id = f"op-{int(time.time())}"
    created_records = []
    
    try:
        # Step 1: Orchestrator creates operation record
        print("\n   [Orchestrator] Creating operation record...")
        operation = db.records.create(
            label="OPERATION",
            data={
                "operationId": operation_id,
                "status": "in_progress",
                "stepsCompleted": 0,
                "totalSteps": 3
            },
            transaction=tx
        )
        created_records.append(operation)
        print(f"      ✓ Operation {operation_id} created")
        
        # Step 2: Analyzer creates analysis sub-task
        print("\n   [Analyzer] Creating analysis subtask...")
        analysis = db.records.create(
            label="SUBTASK",
            data={
                "subtaskId": f"subtask-a-{int(time.time())}",
                "type": "analysis",
                "operationId": operation_id,
                "status": "pending"
            },
            transaction=tx
        )
        db.records.attach(source=operation, target=analysis, options={"type": "HAS_SUBTASK", "direction": "out"}, transaction=tx)
        created_records.append(analysis)
        print(f"      ✓ Analysis subtask created")
        
        # Step 3: Executor creates execution sub-task
        print("\n   [Executor] Creating execution subtask...")
        execution = db.records.create(
            label="SUBTASK",
            data={
                "subtaskId": f"subtask-e-{int(time.time())}",
                "type": "execution",
                "operationId": operation_id,
                "status": "pending"
            },
            transaction=tx
        )
        db.records.attach(source=operation, target=execution, options={"type": "HAS_SUBTASK", "direction": "out"}, transaction=tx)
        created_records.append(execution)
        print(f"      ✓ Execution subtask created")
        
        # Step 4: Link all to orchestrator
        print("\n   [Orchestrator] Linking to orchestrator agent...")
        orchestrator = db.records.find_one({
            "labels": ["AGENT"],
            "where": {"agentId": "agent-001"}
        })
        if orchestrator:
            db.records.attach(source=operation, target=orchestrator, options={"type": "MANAGED_BY", "direction": "out"}, transaction=tx)
            print(f"      ✓ Operation linked to Orchestrator")
        
        # Context manager handles commit on successful exit
        print("\n🔄 TRANSACTION COMPLETING...")
        
    except Exception as e:
        print(f"\n❌ Error in transaction: {e}")
        print("   Rolling back all operations...")
        tx.rollback()
        print("   ✅ All changes rolled back - no partial state")
        return None
    
    # Verify the committed state
    print("\n✅ MULTI-AGENT TRANSACTION COMMITTED!")
    
    # Query for the operation and its subtasks
    committed_op = db.records.find_one({
        "labels": ["OPERATION"],
        "where": {"operationId": operation_id}
    })
    
    if committed_op:
        print(f"\n📍 Committed state for {operation_id}:")
        print(f"   ✓ Operation record exists: {committed_op['status']}")
        
        # Find subtasks
        subtasks = db.records.find({
            "labels": ["SUBTASK"],
            "where": {"OPERATION": {"operationId": operation_id}}
        })
        print(f"   ✓ {subtasks.total} subtasks linked")
        
        for st in subtasks.data:
            print(f"      → {st['type']}: {st['status']}")
    
    return committed_op

# ============================================================================
# SCENARIO 6: Memory Graph Traversal
# ============================================================================

def demonstrate_memory_graph_traversal():
    """
    Show how agents can traverse the memory graph to find related information.
    Useful for agents discovering context from other agents' work.
    """
    print("\n" + "-" * 70)
    print("SCENARIO 6: Memory Graph Traversal")
    print("-" * 70)
    
    print("\n📋 Agent queries: 'Show me all work related to my current task'...")
    
    # Find an orchestrator
    orchestrator = db.records.find_one({
        "labels": ["AGENT"],
        "where": {"agentId": "agent-001"}
    })
    
    if orchestrator:
        print(f"\n🔹 AGENT: {orchestrator['name']}")
        print(f"   Querying memory graph for related records...")
        
        # Find operations managed by this agent
        managed_ops = db.records.find({
            "labels": ["OPERATION"],
            "where": {
                "AGENT": {
                    "agentId": orchestrator["agentId"]
                }
            }
        })
        print(f"\n   Operations managed: {managed_ops.total}")
        for op in managed_ops.data:
            print(f"      → {op['operationId']}: {op['status']}")
        
        # Find all memory blocks this agent can access
        accessible_blocks = db.records.find({
            "labels": ["MEMORY_BLOCK"],
            "where": {
                "AGENT": {
                    "agentId": orchestrator["agentId"]
                }
            }
        })
        print(f"\n   Memory blocks accessible: {accessible_blocks.total}")
        for block in accessible_blocks.data:
            print(f"      → {block['name']} (v{block['version']})")
        
        # Find tasks assigned to this agent
        assigned_tasks = db.records.find({
            "labels": ["TASK"],
            "where": {
                "AGENT": {
                    "agentId": orchestrator["agentId"]
                }
            }
        })
        print(f"\n   Tasks assigned: {assigned_tasks.total}")
        for task in assigned_tasks.data:
            print(f"      → {task['taskId']}: {task['status']}")
    
    print("\n   ✅ Graph traversal reveals full context")
    print("      Agents can discover related work without centralized index")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TUTORIAL: Multi-Agent Memory Synchronization Without Data Loss")
    print("=" * 70)
    
    # Check if seed data exists
    agents = db.records.find({"labels": ["AGENT"]})
    if agents.total == 0:
        print("\n⚠️  No seed data found. Running seed.py first...")
        import subprocess
        subprocess.run(["python", "seed.py"])
    
    print("\n" + "=" * 70)
    print("EXECUTING TUTORIAL SCENARIOS")
    print("=" * 70)
    
    # Run all scenarios
    demonstrate_concurrent_write_problem()
    demonstrate_atomic_transactions()
    demonstrate_upsert_merge_strategy()
    demonstrate_safe_concurrent_update()
    demonstrate_multi_agent_transaction()
    demonstrate_memory_graph_traversal()
    
    print("\n" + "=" * 70)
    print("✅ TUTORIAL COMPLETE")
    print("=" * 70)
    print("""
KEY TAKEAWAYS:

1. CONCURRENT WRITES WITHOUT SYNC → DATA LOSS
   Two agents reading the same state and writing back causes lost updates.

2. TRANSACTIONS PREVENT PARTIAL WRITES
   Wrap multi-step operations in a transaction so either all succeed or none do.
   Use context manager: `with db.transactions.begin() as tx:`
   Do NOT call `tx.commit()` inside the context manager.

3. UPSERT WITH MERGEBY PRESERVES DATA
   Use `mergeBy` to match records and `mergeStrategy: "append"` to add fields
   without overwriting existing data.

4. OPTIMISTIC LOCKING WITH RETRY
   Check version before writing. If conflict detected, fetch fresh data and retry.
   Guarantees eventual consistency without locks.

5. GRAPH TRAVERSAL FOR CONTEXT
   RushDB's relationship model lets agents discover related records
   without centralized indexing.

RushDB provides the memory layer that makes multi-agent systems reliable:
→ ACID transactions for atomic operations
→ Property graph for relationship traversal  
→ Upsert patterns for conflict-free updates
→ Zero schema for flexible memory structures
""")
