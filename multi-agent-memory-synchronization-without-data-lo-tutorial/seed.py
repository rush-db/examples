"""
Seed script: Initializes mock multi-agent memory state in RushDB.

This creates baseline data for the tutorial demonstrating:
- Agent definitions
- Shared memory blocks
- Memory access logs
- Version counters

The script is idempotent — safe to run multiple times.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not set in environment")

db = RushDB(API_KEY)

# Define agents for the multi-agent system
AGENTS = [
    {
        "agentId": "agent-001",
        "name": "Orchestrator",
        "role": "coordinator",
        "status": "active",
        "priority": 1
    },
    {
        "agentId": "agent-002",
        "name": "Analyzer",
        "role": "data-processor",
        "status": "active",
        "priority": 2
    },
    {
        "agentId": "agent-003",
        "name": "Executor",
        "role": "action-executor",
        "status": "idle",
        "priority": 3
    }
]

# Shared memory blocks that agents will read/write
MEMORY_BLOCKS = [
    {
        "blockId": "memory-001",
        "name": "task_queue",
        "type": "queue",
        "version": 1,
        "items": []
    },
    {
        "blockId": "memory-002",
        "name": "results_store",
        "type": "dict",
        "version": 1,
        "data": {}
    },
    {
        "blockId": "memory-003",
        "name": "sync_status",
        "type": "state",
        "version": 1,
        "lastSync": None,
        "pendingWrites": 0
    }
]

def seed_agents():
    """Create or update agent records with upsert (idempotent)."""
    print("\n📦 Seeding agent records...")
    created = 0
    for agent in AGENTS:
        record = db.records.upsert(
            label="AGENT",
            data=agent,
            options={"mergeBy": ["agentId"]}
        )
        created += 1
        print(f"  ✓ {agent['name']} ({agent['agentId']})")
    print(f"  → {created} agents seeded")
    return created

def seed_memory_blocks():
    """Create shared memory blocks with version tracking."""
    print("\n📦 Seeding shared memory blocks...")
    created = 0
    for block in MEMORY_BLOCKS:
        record = db.records.upsert(
            label="MEMORY_BLOCK",
            data=block,
            options={"mergeBy": ["blockId"]}
        )
        created += 1
        print(f"  ✓ {block['name']} (v{block['version']})")
    print(f"  → {created} memory blocks seeded")
    return created

def link_agents_to_memory():
    """Create relationship links between agents and their memory blocks."""
    print("\n🔗 Linking agents to memory blocks...")
    
    # Find all agents and memory blocks
    agents = db.records.find({"labels": ["AGENT"]})
    memory_blocks = db.records.find({"labels": ["MEMORY_BLOCK"]})
    
    links_created = 0
    for agent in agents.data:
        # Link each agent to all memory blocks they can access
        for block in memory_blocks.data:
            # Use upsert-like pattern: only create if not exists
            existing = db.records.find({
                "labels": ["AGENT"],
                "where": {
                    "agentId": agent["agentId"],
                    "MEMORY_BLOCK": {
                        "blockId": block["blockId"]
                    }
                }
            })
            
            if existing.total == 0:
                db.records.attach(
                    source=agent,
                    target=block,
                    options={"type": "CAN_ACCESS", "direction": "out"}
                )
                links_created += 1
                print(f"  ✓ {agent['name']} → {block['name']}")
    
    print(f"  → {links_created} access links created")
    return links_created

def main():
    print("=" * 60)
    print("Multi-Agent Memory Synchronization - Seed Script")
    print("=" * 60)
    
    total_agents = seed_agents()
    total_blocks = seed_memory_blocks()
    total_links = link_agents_to_memory()
    
    print("\n" + "=" * 60)
    print("✅ Seeding complete!")
    print(f"   {total_agents} agents")
    print(f"   {total_blocks} memory blocks")
    print(f"   {total_links} access links")
    print("=" * 60)
    print("\nRun 'python main.py' to execute the tutorial.")

if __name__ == "__main__":
    main()
