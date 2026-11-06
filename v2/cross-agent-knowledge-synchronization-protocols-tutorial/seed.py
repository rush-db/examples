"""
Seed script for Cross-Agent Knowledge Synchronization demo.

Creates sample agents, knowledge contexts, and sync events.
Safe to run multiple times - uses upsert patterns for idempotency.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Verify API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)

def seed_agents():
    """Create agent identity records."""
    print("\n🌱 Seeding Agent Registry...")
    
    agents = [
        {
            "agentId": "agent-001",
            "name": "Synthesis-Alpha",
            "role": "knowledge-synthesizer",
            "capabilities": ["reasoning", "summarization", "cross-reference"],
            "status": "active",
            "lastHeartbeat": datetime.utcnow().isoformat()
        },
        {
            "agentId": "agent-002", 
            "name": "Analysis-Beta",
            "role": "pattern-analyzer",
            "capabilities": ["classification", "anomaly-detection", "prediction"],
            "status": "active",
            "lastHeartbeat": datetime.utcnow().isoformat()
        },
        {
            "agentId": "agent-003",
            "name": "Coordination-Gamma",
            "role": "sync-coordinator",
            "capabilities": ["conflict-resolution", "state-management", "routing"],
            "status": "active",
            "lastHeartbeat": datetime.utcnow().isoformat()
        }
    ]
    
    created = []
    for agent_data in agents:
        agent = db.records.upsert(
            label="AGENT",
            data=agent_data,
            options={"mergeBy": ["agentId"]}
        )
        created.append(agent)
        print(f"  ✓ Agent: {agent_data['name']}")
    
    return created


def seed_knowledge_contexts(agents):
    """Create shared knowledge contexts."""
    print("\n🌱 Seeding Knowledge Contexts...")
    
    contexts = [
        {
            "contextId": "ctx-ml-pipeline",
            "name": "ML Pipeline Design",
            "domain": "machine-learning",
            "description": "Shared knowledge about ML pipeline architecture and best practices",
            "version": 1,
            "contributorCount": len(agents)
        },
        {
            "contextId": "ctx-data-quality",
            "name": "Data Quality Standards",
            "domain": "data-engineering",
            "description": "Data validation and quality assurance protocols",
            "version": 1,
            "contributorCount": 2
        },
        {
            "contextId": "ctx-api-design",
            "name": "API Design Guidelines",
            "domain": "backend",
            "description": "RESTful API conventions and versioning strategies",
            "version": 1,
            "contributorCount": 1
        }
    ]
    
    created = []
    for ctx_data in contexts:
        ctx = db.records.upsert(
            label="KNOWLEDGE_CONTEXT",
            data=ctx_data,
            options={"mergeBy": ["contextId"]}
        )
        created.append(ctx)
        print(f"  ✓ Context: {ctx_data['name']}")
    
    # Link agents to contexts they contribute to
    for i, agent in enumerate(agents):
        if i < 2:  # First two agents contribute to ML context
            db.records.attach(
                source=agent,
                target=created[0],
                options={"type": "CONTRIBUTES_TO", "direction": "out"}
            )
    
    return created


def seed_knowledge_items(agents, contexts):
    """Create sample knowledge items."""
    print("\n🌱 Seeding Knowledge Items...")
    
    knowledge_items = [
        {
            "itemId": "ki-001",
            "title": "Distributed Training Architecture",
            "content": "Use parameter server pattern for gradients aggregation in multi-GPU setups. Data parallelism offers better scalability for large batch sizes.",
            "category": "architecture",
            "version": 2,
            "sourceAgent": agents[0].id,
            "contextId": contexts[0].data["contextId"]
        },
        {
            "itemId": "ki-002",
            "title": "Feature Engineering Pipeline",
            "content": "Implement automated feature selection using mutual information. Store feature schemas in a registry for reproducibility.",
            "category": "data-processing",
            "version": 1,
            "sourceAgent": agents[1].id,
            "contextId": contexts[0].data["contextId"]
        },
        {
            "itemId": "ki-003",
            "title": "Model Versioning Strategy",
            "content": "Use semantic versioning for models. Store model artifacts with their training dataset hash for full reproducibility.",
            "category": "mlops",
            "version": 1,
            "sourceAgent": agents[0].id,
            "contextId": contexts[0].data["contextId"]
        },
        {
            "itemId": "ki-004",
            "title": "Data Validation Rules",
            "content": "Define schema validation at ingestion time. Use Great Expectations or similar for comprehensive data testing.",
            "category": "quality",
            "version": 1,
            "sourceAgent": agents[1].id,
            "contextId": contexts[1].data["contextId"]
        }
    ]
    
    created = []
    for ki_data in knowledge_items:
        ki = db.records.upsert(
            label="KNOWLEDGE_ITEM",
            data=ki_data,
            options={"mergeBy": ["itemId"]}
        )
        created.append(ki)
        print(f"  ✓ Knowledge: {ki_data['title'][:40]}...")
    
    # Link knowledge items to their source agents
    for ki in created:
        source_agent_id = ki.data.get("sourceAgent")
        if source_agent_id:
            source_agent = db.records.find_by_id(source_agent_id)
            if source_agent:
                db.records.attach(
                    source=source_agent,
                    target=ki,
                    options={"type": "AUTHORED", "direction": "out"}
                )
    
    return created


def seed_sync_events(agents, contexts):
    """Create sample sync events."""
    print("\n🌱 Seeding Sync Events...")
    
    sync_events = [
        {
            "eventId": "sync-001",
            "type": "bidirectional-merge",
            "direction": "both",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "participants": [agents[0].id, agents[1].id],
            "contextId": contexts[0].data["contextId"]
        },
        {
            "eventId": "sync-002",
            "type": "pull",
            "direction": "in",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "participants": [agents[2].id],
            "contextId": contexts[1].data["contextId"]
        }
    ]
    
    created = []
    for se_data in sync_events:
        se = db.records.upsert(
            label="SYNC_EVENT",
            data=se_data,
            options={"mergeBy": ["eventId"]}
        )
        created.append(se)
        print(f"  ✓ Sync: {se_data['type']} ({se_data['status']})")
    
    return created


def main():
    print("=" * 60)
    print("Cross-Agent Knowledge Sync - Database Seeder")
    print("=" * 60)
    
    # Seed all data
    agents = seed_agents()
    contexts = seed_knowledge_contexts(agents)
    knowledge_items = seed_knowledge_items(agents, contexts)
    sync_events = seed_sync_events(agents, contexts)
    
    print("\n" + "=" * 60)
    print("✅ Seeding complete!")
    print(f"   • {len(agents)} agents")
    print(f"   • {len(contexts)} knowledge contexts")
    print(f"   • {len(knowledge_items)} knowledge items")
    print(f"   • {len(sync_events)} sync events")
    print("=" * 60)
    print("\nRun 'python main.py' to execute the sync protocol demo.")


if __name__ == "__main__":
    main()
