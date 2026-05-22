"""
Seed script for security-considerations-for-graph-stored-agent-mem-tutorial.

This script generates realistic mock data for demonstrating security patterns
in graph-stored agent memories. It creates agents, memory records, permission
relationships, and existing audit logs.

Run this script once before main.py to populate the database with sample data.
It is idempotent and safe to run multiple times.
"""

import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
db = RushDB(
    os.getenv("RUSHDB_TOKEN"),
    url=os.getenv("RUSHDB_URL") if os.getenv("RUSHDB_URL") else None
)

# Sample data
AGENT_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
MEMORY_TYPES = ["conversational", "factual", "preference", "sensitive", "contextual"]

# Memory content templates by type
MEMORY_TEMPLATES = {
    "conversational": [
        "User asked about product pricing for enterprise tier",
        "Customer complained about slow response times",
        "User requested feature comparison between Basic and Pro plans",
        "Customer provided feedback on new dashboard UI",
        "User inquired about bulk discount options",
    ],
    "factual": [
        "User is John Smith, employee ID 12345, department Engineering",
        "Customer company: Acme Corp, account tier: Enterprise",
        "User preferences: dark mode, timezone UTC-5",
        "User's last login was 2024-01-15 at 09:32 UTC",
        "Customer has 5 active projects in the system",
    ],
    "preference": [
        "User prefers concise responses under 100 words",
        "Customer likes to be CC'd on all email notifications",
        "User prefers code examples over documentation links",
        "Customer wants weekly summary reports on Mondays",
        "User is comfortable with technical jargon in responses",
    ],
    "sensitive": [
        "User credit card ends in 4242 - DO NOT store full number",
        "Customer API keys should be rotated every 90 days",
        "User SSN stored in encrypted vault, reference: vault-789",
        "Customer executive contacts are confidential",
        "User medical information accessed via HIPAA-compliant endpoint",
    ],
    "contextual": [
        "User is currently working on the payment integration module",
        "Customer's sprint ends on Friday - prioritize blocking issues",
        "User was troubleshooting API authentication errors",
        "Customer is evaluating competitors: Stripe, PayPal",
        "User context: emergency maintenance window tonight",
    ],
}


def clear_existing_data():
    """Remove existing test data to ensure clean state."""
    print("Clearing existing data...")
    
    # Delete audit logs first (referenced by other records)
    try:
        db.records.delete_many({"labels": ["AUDIT_LOG"], "where": {}})
    except Exception:
        pass
    
    # Delete permission relationships
    try:
        db.records.delete_many({"labels": ["PERMISSION"], "where": {}})
    except Exception:
        pass
    
    # Delete memories
    try:
        db.records.delete_many({"labels": ["MEMORY"], "where": {}})
    except Exception:
        pass
    
    # Delete agent memory associations
    try:
        db.records.delete_many({"labels": ["AGENT_MEMORY"], "where": {}})
    except Exception:
        pass
    
    # Delete agents
    try:
        db.records.delete_many({"labels": ["AGENT"], "where": {}})
    except Exception:
        pass
    
    # Delete workspaces
    try:
        db.records.delete_many({"labels": ["WORKSPACE"], "where": {}})
    except Exception:
        pass
    
    print("Existing data cleared.\n")


def create_agents():
    """Create agent records with workspaces."""
    print("Creating agents and workspaces...")
    agents = []
    
    for i, name in enumerate(AGENT_NAMES):
        # Create workspace for agent
        workspace = db.records.create(
            label="WORKSPACE",
            data={
                "name": f"{name}'s Workspace",
                "created_at": datetime.utcnow().isoformat(),
                "tier": "secure" if i % 2 == 0 else "standard",
            }
        )
        
        # Create agent
        agent = db.records.create(
            label="AGENT",
            data={
                "name": name,
                "role": "admin" if name in ["Alice", "Bob"] else "user",
                "email": f"{name.lower()}@example.com",
                "active": True,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        
        # Link agent to workspace
        db.records.attach(
            source=agent,
            target=workspace,
            options={"type": "OWNS", "direction": "out"}
        )
        
        agents.append(agent)
        
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} agents...")
    
    print(f"  Created {len(agents)} agents with workspaces")
    return agents


def create_memories(agents):
    """Create memory records for agents."""
    print("\nCreating memories...")
    total_memories = 0
    
    for i, agent in enumerate(agents):
        memories_created = 0
        
        for mem_type in MEMORY_TYPES:
            # Create 2-5 memories per type per agent
            num_memories = random.randint(2, 5)
            
            for j in range(num_memories):
                content = random.choice(MEMORY_TEMPLATES[mem_type])
                
                # Vary sensitivity based on memory type
                is_sensitive = mem_type == "sensitive"
                classification = "restricted" if is_sensitive else "internal"
                
                memory = db.records.create(
                    label="MEMORY",
                    data={
                        "content": content,
                        "type": mem_type,
                        "classification": classification,
                        "sensitive": is_sensitive,
                        "created_at": (datetime.utcnow() - timedelta(
                            days=random.randint(0, 30),
                            hours=random.randint(0, 23)
                        )).isoformat(),
                        "version": 1,
                    }
                )
                
                # Link memory to agent
                db.records.attach(
                    source=agent,
                    target=memory,
                    options={"type": "STORED", "direction": "out"}
                )
                
                # Create AGENT_MEMORY association for access control
                agent_memory = db.records.create(
                    label="AGENT_MEMORY",
                    data={
                        "access_level": "read_write" if agent.data.get("role") == "admin" else "read",
                        "assigned_at": datetime.utcnow().isoformat(),
                    }
                )
                
                db.records.attach(
                    source=agent,
                    target=agent_memory,
                    options={"type": "CAN_ACCESS", "direction": "out"}
                )
                
                db.records.attach(
                    source=agent_memory,
                    target=memory,
                    options={"type": "REFERENCES", "direction": "out"}
                )
                
                memories_created += 1
                total_memories += 1
        
        if (i + 1) % 100 == 0:
            print(f"  Created memories for {i + 1} agents ({total_memories} total memories)...")
    
    print(f"  Created {total_memories} memories total")
    return total_memories


def create_permissions(agents):
    """Create permission records for agents."""
    print("\nCreating permission records...")
    permissions_created = 0
    
    for agent in agents:
        # Each agent gets permissions for different memory types
        for mem_type in random.sample(MEMORY_TYPES, random.randint(2, 4)):
            permission = db.records.create(
                label="PERMISSION",
                data={
                    "memory_type": mem_type,
                    "access_level": "admin" if agent.data.get("role") == "admin" else "user",
                    "granted_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                }
            )
            
            db.records.attach(
                source=agent,
                target=permission,
                options={"type": "GRANTED", "direction": "out"}
            )
            
            permissions_created += 1
            
            if permissions_created % 100 == 0:
                print(f"  Created {permissions_created} permissions...")
    
    print(f"  Created {permissions_created} permission records")
    return permissions_created


def create_audit_logs(agents):
    """Create sample audit log entries."""
    print("\nCreating audit logs...")
    audit_logs = 0
    operations = ["CREATE", "READ", "UPDATE", "DELETE"]
    
    # Get all memories for audit logging
    memories = db.records.find({"labels": ["MEMORY"], "limit": 100}).data
    
    for i, agent in enumerate(agents):
        # Create 5-10 audit entries per agent
        num_logs = random.randint(5, 10)
        
        for j in range(num_logs):
            memory = random.choice(memories) if memories else None
            operation = random.choice(operations)
            
            audit_log = db.records.create(
                label="AUDIT_LOG",
                data={
                    "operation": operation,
                    "actor_id": agent.id,
                    "actor_name": agent.data.get("name"),
                    "resource_id": memory.id if memory else None,
                    "resource_type": "MEMORY",
                    "timestamp": (datetime.utcnow() - timedelta(
                        hours=random.randint(0, 72),
                        minutes=random.randint(0, 59)
                    )).isoformat(),
                    "ip_address": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                    "success": random.choice([True, True, True, False]),  # 75% success rate
                    "details": f"{operation} operation on memory resource",
                }
            )
            
            # Link audit log to the agent who performed the action
            db.records.attach(
                source=agent,
                target=audit_log,
                options={"type": "PERFORMED", "direction": "out"}
            )
            
            audit_logs += 1
            
            if audit_logs % 100 == 0:
                print(f"  Created {audit_logs} audit logs...")
    
    print(f"  Created {audit_logs} audit log entries")
    return audit_logs


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Security Tutorial - Mock Data Seeding")
    print("=" * 60)
    print()
    
    # Clear existing data for clean state
    clear_existing_data()
    
    # Create entities
    agents = create_agents()
    memories = create_memories(agents)
    permissions = create_permissions(agents)
    audit_logs = create_audit_logs(agents)
    
    print()
    print("=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"  Agents created: {len(agents)}")
    print(f"  Memories created: {memories}")
    print(f"  Permissions created: {permissions}")
    print(f"  Audit logs created: {audit_logs}")
    print()
    print("You can now run `python main.py` to demonstrate security patterns.")


if __name__ == "__main__":
    main()
