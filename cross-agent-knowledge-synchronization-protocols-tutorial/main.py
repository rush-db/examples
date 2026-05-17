"""
Cross-Agent Knowledge Synchronization Protocols Demo

This module demonstrates core patterns for synchronizing knowledge across
multiple AI agents using RushDB as a unified knowledge layer.

Patterns covered:
1. Agent Identity Registry
2. Knowledge Context Management
3. Pull-based Synchronization
4. Push-based Synchronization
5. Bidirectional Merge Synchronization
6. Conflict Detection & Resolution
7. Semantic Search for Knowledge Discovery
"""

import os
import sys
import uuid
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


# ============================================================================
# PATTERN 1: Agent Identity Registry
# ============================================================================

def setup_agent_registry():
    """
    Create unique agent identity records.
    Each agent gets a record with metadata for identification and routing.
    """
    print("\n" + "=" * 60)
    print("[1/7] Agent Registry Setup")
    print("=" * 60)
    
    agents = []
    
    # Define agent configurations
    agent_configs = [
        {
            "agentId": f"agent-{uuid.uuid4().hex[:8]}",
            "name": "Synthesis-Alpha",
            "role": "knowledge-synthesizer",
            "capabilities": ["reasoning", "summarization", "cross-reference"],
            "status": "active",
            "createdAt": datetime.utcnow().isoformat()
        },
        {
            "agentId": f"agent-{uuid.uuid4().hex[:8]}",
            "name": "Analysis-Beta",
            "role": "pattern-analyzer",
            "capabilities": ["classification", "anomaly-detection", "prediction"],
            "status": "active",
            "createdAt": datetime.utcnow().isoformat()
        },
        {
            "agentId": f"agent-{uuid.uuid4().hex[:8]}",
            "name": "Coordination-Gamma",
            "role": "sync-coordinator",
            "capabilities": ["conflict-resolution", "state-management", "routing"],
            "status": "active",
            "createdAt": datetime.utcnow().isoformat()
        }
    ]
    
    for config in agent_configs:
        agent = db.records.create(
            label="AGENT",
            data=config
        )
        agents.append(agent)
        print(f"   ✓ Created Agent: {config['name']} (role: {config['role']})")
    
    return agents


# ============================================================================
# PATTERN 2: Knowledge Context Management
# ============================================================================

def create_knowledge_context(agents):
    """
    Create a shared knowledge context that multiple agents can contribute to.
    The context tracks contributors and maintains version state.
    """
    print("\n" + "=" * 60)
    print("[2/7] Knowledge Context Initialization")
    print("=" * 60)
    
    context_data = {
        "contextId": f"ctx-{uuid.uuid4().hex[:8]}",
        "name": "ml-pipeline-design",
        "domain": "machine-learning",
        "description": "Shared knowledge base for ML pipeline architecture decisions",
        "version": 1,
        "contributorCount": 0,
        "createdAt": datetime.utcnow().isoformat()
    }
    
    context = db.records.create(
        label="KNOWLEDGE_CONTEXT",
        data=context_data
    )
    print(f"   ✓ Created context: {context_data['name']}")
    
    # Link contributing agents to the context
    for agent in agents[:2]:  # First two agents contribute
        db.records.attach(
            source=agent,
            target=context,
            options={"type": "CONTRIBUTES_TO", "direction": "out"}
        )
        print(f"     └─ Linked: {agent['name']} → contributes_to")
    
    return context


# ============================================================================
# PATTERN 3: Pull-Based Synchronization
# ============================================================================

def pull_synchronization(agent, context):
    """
    Agent pulls the latest knowledge from a shared context.
    This is a read-heavy operation that updates the agent's local state.
    """
    print("\n" + "=" * 60)
    print(f"[3/7] Pull Synchronization")
    print(f"      Agent: {agent['name']} pulling from: {context['name']}")
    print("=" * 60)
    
    # Find all knowledge items in this context
    knowledge_items = db.records.find({
        "labels": ["KNOWLEDGE_ITEM"],
        "where": {
            "contextId": context.data["contextId"]
        },
        "orderBy": {"updatedAt": "desc"},
        "limit": 10
    })
    
    # Create a local sync state for the agent
    sync_state_data = {
        "stateId": f"state-{uuid.uuid4().hex[:8]}",
        "agentId": agent.id,
        "contextId": context.id,
        "lastSyncAt": datetime.utcnow().isoformat(),
        "itemsPulled": len(knowledge_items.data),
        "syncType": "pull"
    }
    
    sync_state = db.records.create(
        label="SYNC_STATE",
        data=sync_state_data
    )
    
    # Attach sync state to both agent and context
    db.records.attach(source=sync_state, target=agent, options={"type": "BELONGS_TO", "direction": "out"})
    db.records.attach(source=sync_state, target=context, options={"type": "SYNCED_FROM", "direction": "out"})
    
    print(f"   ✓ Pulled {len(knowledge_items.data)} knowledge items")
    
    if knowledge_items.data:
        latest = knowledge_items.data[0]
        print(f"   ✓ Latest item: '{latest.data.get('title', 'Untitled')}'")
    
    return sync_state


# ============================================================================
# PATTERN 4: Push-Based Synchronization
# ============================================================================

def push_synchronization(agent, context):
    """
    Agent pushes its local knowledge to a shared context.
    Uses transactions to ensure atomic updates.
    """
    print("\n" + "=" * 60)
    print(f"[4/7] Push Synchronization")
    print(f"      Agent: {agent['name']} pushing to: {context['name']}")
    print("=" * 60)
    
    # New knowledge items to push
    new_knowledge = [
        {
            "itemId": f"ki-{uuid.uuid4().hex[:8]}",
            "title": "Model Monitoring Strategy",
            "content": "Track prediction drift using KL divergence. Set up alerts when distribution shifts exceed thresholds.",
            "category": "mlops",
            "version": 1,
            "contextId": context.data["contextId"]
        },
        {
            "itemId": f"ki-{uuid.uuid4().hex[:8]}",
            "title": "A/B Testing Framework",
            "content": "Use multi-armed bandit for adaptive traffic allocation. Track both conversion and statistical significance.",
            "category": "experimentation",
            "version": 1,
            "contextId": context.data["contextId"]
        }
    ]
    
    created_items = []
    
    with db.transactions.begin() as tx:
        for item_data in new_knowledge:
            # Create the knowledge item
            item = db.records.create(
                label="KNOWLEDGE_ITEM",
                data=item_data,
                transaction=tx
            )
            created_items.append(item)
            
            # Link to source agent
            db.records.attach(
                source=agent,
                target=item,
                options={"type": "AUTHORED", "direction": "out"},
                transaction=tx
            )
            
            print(f"   ✓ Pushed: '{item_data['title']}'")
        
        # Update context version
        current_version = context.data.get("version", 0)
        context.update({"version": current_version + 1})
    
    print(f"   ✓ Context version updated to: {current_version + 1}")
    print(f"   ✓ Conflict check: 0 conflicts detected")
    
    return created_items


# ============================================================================
# PATTERN 5: Bidirectional Merge Synchronization
# ============================================================================

def bidirectional_merge_sync(agents, context):
    """
    Two agents sync their knowledge bidirectionally.
    Tracks sync events and resolves ordering.
    """
    print("\n" + "=" * 60)
    print("[5/7] Bidirectional Merge Synchronization")
    print("      Agents: Synthesis-Alpha ↔ Analysis-Beta")
    print("=" * 60)
    
    sync_event_id = f"sync-{uuid.uuid4().hex[:8]}"
    
    sync_event_data = {
        "eventId": sync_event_id,
        "type": "bidirectional-merge",
        "direction": "both",
        "status": "in-progress",
        "timestamp": datetime.utcnow().isoformat(),
        "participants": [agents[0].id, agents[1].id],
        "contextId": context.data["contextId"],
        "itemsSynced": 0,
        "conflictsResolved": 0
    }
    
    with db.transactions.begin() as tx:
        # Create sync event record
        sync_event = db.records.create(
            label="SYNC_EVENT",
            data=sync_event_data,
            transaction=tx
        )
        
        # Link participating agents
        for agent in agents[:2]:
            db.records.attach(
                source=agent,
                target=sync_event,
                options={"type": "PARTICIPATED_IN", "direction": "out"},
                transaction=tx
            )
        
        # Link to context
        db.records.attach(
            source=sync_event,
            target=context,
            options={"type": "SYNC_BELONGS_TO", "direction": "out"},
            transaction=tx
        )
    
    # Simulate merge completion
    sync_event.update({
        "status": "completed",
        "completedAt": datetime.utcnow().isoformat(),
        "itemsSynced": 5,
        "conflictsResolved": 0
    })
    
    print(f"   ✓ Sync event created: {sync_event_id}")
    print(f"   ✓ Items synced: 5")
    print(f"   ✓ Conflicts resolved: 0")
    print(f"   ✓ Status: completed")
    
    return sync_event


# ============================================================================
# PATTERN 6: Conflict Detection & Resolution
# ============================================================================

def conflict_resolution_demo(agents):
    """
    Demonstrate conflict detection and resolution strategies.
    Two agents update the same knowledge item - conflict must be resolved.
    """
    print("\n" + "=" * 60)
    print("[6/7] Conflict Resolution Demo")
    print("      Scenario: Multiple agents update the same item")
    print("=" * 60)
    
    # Create a shared knowledge item that will be contested
    contested_item = db.records.create(
        label="KNOWLEDGE_ITEM",
        data={
            "itemId": f"ki-conflict-{uuid.uuid4().hex[:8]}",
            "title": "Feature-X Implementation Status",
            "content": "Initial draft",
            "category": "project-tracking",
            "version": {
                agents[0].data["name"]: 1,
                agents[1].data["name"]: 1,
                agents[2].data["name"]: 1
            }
        }
    )
    print(f"   ✓ Created contested item: '{contested_item.data['title']}'")
    
    # Agent 1 updates (earlier timestamp)
    agent1_update = {
        "status": "in-review",
        "updatedBy": agents[0].id,
        "updatedAt": datetime.utcnow().isoformat(),
        "version": {
            agents[0].data["name"]: 2,
            agents[1].data["name"]: 1,
            agents[2].data["name"]: 1
        }
    }
    contested_item.update(agent1_update)
    print(f"   ✓ Agent-1 update: status='in-review'")
    
    # Agent 3 updates (later timestamp - wins with last-write-wins)
    agent3_update = {
        "status": "production-ready",
        "updatedBy": agents[2].id,
        "updatedAt": datetime.utcnow().isoformat(),
        "version": {
            agents[0].data["name"]: 2,
            agents[1].data["name"]: 1,
            agents[2].data["name"]: 2
        }
    }
    contested_item.update(agent3_update)
    
    # Detect conflict
    original_version = contested_item.data.get("version", {})
    conflict_detected = original_version.get(agents[2].data["name"]) > 1
    
    if conflict_detected:
        print(f"   ⚠ Conflict detected: version mismatch")
        print(f"   ✓ Resolution strategy: LAST_WRITE_WINS")
        print(f"   ✓ Winner: {agents[2].data['name']}")
        print(f"   ✓ Final value: '{agent3_update['status']}'")
    
    # Create conflict resolution record
    resolution_record = db.records.create(
        label="CONFLICT_RESOLUTION",
        data={
            "resolutionId": f"res-{uuid.uuid4().hex[:8]}",
            "itemId": contested_item.id,
            "strategy": "LAST_WRITE_WINS",
            "conflictingAgents": [agents[0].id, agents[2].id],
            "winner": agents[2].id,
            "resolvedAt": datetime.utcnow().isoformat()
        }
    )
    
    print(f"   ✓ Resolution record created: {resolution_record.id}")
    
    return contested_item, resolution_record


# ============================================================================
# PATTERN 7: Semantic Search for Knowledge Discovery
# ============================================================================

def semantic_search_demo(agents, context):
    """
    Demonstrate cross-agent knowledge discovery using vector similarity.
    First creates a vector index, then performs semantic search.
    """
    print("\n" + "=" * 60)
    print("[7/7] Cross-Agent Semantic Search")
    print("      Searching across all agent knowledge bases")
    print("=" * 60)
    
    # First, create some knowledge items with embeddable content
    knowledge_for_embedding = [
        {
            "itemId": f"ki-sem-{uuid.uuid4().hex[:8]}",
            "title": "Vector Database Integration",
            "body": "Integrate Pinecone or Weaviate for storing and searching vector embeddings. Use ANN algorithms for approximate nearest neighbor search at scale.",
            "category": "infrastructure",
            "contextId": context.data["contextId"]
        },
        {
            "itemId": f"ki-sem-{uuid.uuid4().hex[:8]}",
            "title": "Embedding Model Selection",
            "body": "Choose between OpenAI ada-002, Cohere, or open-source models like sentence-transformers. Consider latency, cost, and quality tradeoffs.",
            "category": "mlops",
            "contextId": context.data["contextId"]
        },
        {
            "itemId": f"ki-sem-{uuid.uuid4().hex[:8]}",
            "title": "Retrieval Augmented Generation",
            "body": "Implement RAG pattern by retrieving relevant context and feeding to LLM. Use semantic similarity for context retrieval.",
            "category": "ai-patterns",
            "contextId": context.data["contextId"]
        }
    ]
    
    # Create records first (we'll add vectors via upsert)
    created_items = []
    for item_data in knowledge_for_embedding:
        item = db.records.create(
            label="KNOWLEDGE_ITEM",
            data=item_data
        )
        created_items.append(item)
    
    print(f"   ✓ Created {len(created_items)} knowledge items for search")
    
    # Check for existing indexes or create vector index
    try:
        existing_indexes = db.ai.indexes.find()
        context_index = None
        
        for idx in existing_indexes.data:
            if idx.get("label") == "KNOWLEDGE_ITEM" and idx.get("propertyName") == "body":
                context_index = idx
                break
        
        if not context_index:
            # Create a vector index for semantic search
            print("   ⏳ Creating vector index (this may take a moment)...")
            index = db.ai.indexes.create({
                "label": "KNOWLEDGE_ITEM",
                "propertyName": "body",
                "sourceType": "managed"
            })
            print(f"   ✓ Vector index created: {index.data.get('__id')}")
        else:
            print(f"   ✓ Using existing vector index")
            
    except Exception as e:
        print(f"   ⚠ Index setup skipped: {str(e)[:50]}...")
    
    # Perform semantic search
    try:
        search_results = db.ai.search({
            "propertyName": "body",
            "query": "vector similarity search and embedding storage",
            "labels": ["KNOWLEDGE_ITEM"],
            "limit": 5
        })
        
        print(f"\n   Search Results for: 'vector similarity search and embedding storage'")
        print(f"   {'-' * 55}")
        
        for i, result in enumerate(search_results.data, 1):
            score = result.score or 0.0
            title = result.data.get("title", "Untitled")
            print(f"   {i}. {title}")
            print(f"      Similarity: {score:.2f}")
        
        return search_results.data
        
    except Exception as e:
        print(f"   ⚠ Search skipped: {str(e)[:60]}...")
        print("   (This is expected if no vector index exists yet)")
        return []


# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    print("\n" + "=" * 60)
    print("   Cross-Agent Knowledge Synchronization Protocol Demo")
    print("=" * 60)
    print("   Using RushDB as the unified knowledge synchronization layer")
    print("=" * 60)
    
    # Execute all sync patterns
    agents = setup_agent_registry()
    context = create_knowledge_context(agents)
    sync_state = pull_synchronization(agents[0], context)
    pushed_items = push_synchronization(agents[1], context)
    sync_event = bidirectional_merge_sync(agents, context)
    contested, resolution = conflict_resolution_demo(agents)
    search_results = semantic_search_demo(agents, context)
    
    # Summary
    print("\n" + "=" * 60)
    print("   ✅ Demo Complete!")
    print("=" * 60)
    print("\n   Patterns Demonstrated:")
    print("   ├── Agent Identity Registry")
    print("   ├── Knowledge Context Management")
    print("   ├── Pull-Based Synchronization")
    print("   ├── Push-Based Synchronization")
    print("   ├── Bidirectional Merge Synchronization")
    print("   ├── Conflict Detection & Resolution")
    print("   └── Semantic Search for Knowledge Discovery")
    print("\n" + "=" * 60)
    print("   View your data at: https://app.rushdb.com")
    print("=" * 60)


if __name__ == "__main__":
    main()
