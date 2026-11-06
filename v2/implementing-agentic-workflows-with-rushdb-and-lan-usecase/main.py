"""
Implementing Agentic Workflows with RushDB and LangChain

This example demonstrates how RushDB's unified graph+vector architecture
replaces the "Pinecone + Neo4j + Redis" stack that LangChain agents typically require.

Key concepts demonstrated:
1. Agent loop: plan → tool call → retrieve context → update memory → decide
2. Atomic transactions for consistent state
3. Graph traversal for relationship-aware queries
4. Vector search with relationship filtering
5. Unified memory (no separate vector DB + graph DB + cache needed)
"""

import os
import time
from datetime import datetime
from typing import Any
from dotenv import load_dotenv

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")

if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment variables. "
                     "Copy .env.example to .env and add your API key.")

db = RushDB(api_key, url=url) if url else RushDB(api_key)

# Initialize embedding model (local, no OpenAI needed)
print("Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')


def generate_embedding(text: str) -> list:
    """Generate vector embedding for text using local model."""
    return embedder.encode(text).tolist()


def ensure_vector_indexes():
    """Ensure required vector indexes exist."""
    try:
        existing = db.ai.indexes.find()
        index_labels = [idx['label'] for idx in existing.data]
    except Exception:
        index_labels = []
    
    # Create CONVERSATION_TURN index if missing
    if "CONVERSATION_TURN" not in index_labels:
        try:
            db.ai.indexes.create({
                "label": "CONVERSATION_TURN",
                "propertyName": "content",
                "sourceType": "external",
                "dimensions": 384,
                "similarityFunction": "cosine"
            })
            print("  Created CONVERSATION_TURN vector index")
        except Exception:
            pass  # Index may already exist
    
    # Create TOOL_CALL index if missing
    if "TOOL_CALL" not in index_labels:
        try:
            db.ai.indexes.create({
                "label": "TOOL_CALL",
                "propertyName": "output",
                "sourceType": "external",
                "dimensions": 384,
                "similarityFunction": "cosine"
            })
            print("  Created TOOL_CALL vector index")
        except Exception:
            pass  # Index may already exist
    
    time.sleep(1)  # Allow index creation to propagate


# =============================================================================
# AGENTIC WORKFLOW DEMONSTRATION
# =============================================================================

def run_agentic_workflow():
    """
    Demonstrates a complete agentic workflow with RushDB.
    
    The workflow simulates an agent that:
    1. Plans its next action
    2. Calls a tool
    3. Retrieves context from memory
    4. Updates its memory atomically
    5. Decides on next steps
    """
    print("\n" + "=" * 70)
    print(" AGENTIC WORKFLOW WITH RUSHDB ")
    print("=" * 70)
    
    # =========================================================================
    # PHASE 1: Create a new agent session
    # =========================================================================
    print("\n[1] Creating agent session...")
    
    with db.transactions.begin() as tx:
        session = db.records.create(
            label="SESSION",
            data={
                "task": "user_analytics_review",
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "confidence_score": 0.0
            },
            transaction=tx
        )
        
        # Store initial agent state as a related node
        agent_state = db.records.create(
            label="AGENT_STATE",
            data={
                "thinking": "Initializing analysis",
                "step": 0,
                "tools_used": [],
                "context_collected": []
            },
            transaction=tx
        )
        
        # Link session to its state
        db.records.attach(
            source=session,
            target=agent_state,
            options={"type": "HAS_STATE", "direction": "out"},
            transaction=tx
        )
    
    print(f"      Session created: {session.id}")
    print(f"      Initial state: {agent_state.data['thinking']}")
    
    # =========================================================================
    # PHASE 2: Agent loop - execute multiple steps
    # =========================================================================
    print("\n[2] Executing agent loop...")
    
    steps = [
        {
            "step": 1,
            "plan": "Search knowledge base for relevant context",
            "tool": "search_knowledge_base",
            "tool_input": "user behavior analysis patterns",
            "expected_output": "Retrieve documentation on user analytics"
        },
        {
            "step": 2,
            "plan": "Execute analysis code",
            "tool": "execute_python",
            "tool_input": "Calculate cohort retention metrics",
            "expected_output": "Return retention data for visualization"
        },
        {
            "step": 3,
            "plan": "Retrieve similar past sessions for context",
            "tool": "retrieve_context",
            "tool_input": "cohort analysis sessions",
            "expected_output": "Find related conversation history"
        }
    ]
    
    for step_info in steps:
        print(f"\n      Step {step_info['step']}: {step_info['plan']}")
        
        # Simulate tool execution
        tool_output = simulate_tool_execution(
            step_info['tool'],
            step_info['tool_input']
        )
        print(f"      Tool result: {tool_output[:60]}...")
        
        # Store tool call in RushDB with atomic transaction
        with db.transactions.begin() as tx:
            tool_call = db.records.create(
                label="TOOL_CALL",
                data={
                    "tool": step_info['tool'],
                    "input": step_info['tool_input'],
                    "output": tool_output,
                    "step": step_info['step'],
                    "success": True,
                    "executed_at": datetime.now().isoformat()
                },
                vectors=[{"propertyName": "output", "vector": generate_embedding(tool_output)}],
                transaction=tx
            )
            
            # Link tool call to session
            db.records.attach(
                source=session,
                target=tool_call,
                options={"type": "INITIATED", "direction": "out"},
                transaction=tx
            )
            
            # Update agent state
            current_state = agent_state.data
            current_state['step'] = step_info['step']
            current_state['thinking'] = f"Completed {step_info['tool']}"
            current_state['tools_used'].append(step_info['tool'])
            current_state['context_collected'].append(tool_output[:100])
            
            agent_state.update(current_state)
        
        time.sleep(0.2)  # Brief pause for readability
    
    # =========================================================================
    # PHASE 3: Graph traversal - find related conversation turns
    # =========================================================================
    print("\n[3] Demonstrating graph traversal...")
    
    # Find all tool calls for this session that used 'search' or 'retrieve'
    related_tool_calls = db.records.find({
        "labels": ["TOOL_CALL"],
        "where": {
            "SESSION": {"$relation": {"type": "INITIATED", "direction": "in"}},
            "tool": {"$in": ["search_knowledge_base", "retrieve_context"]}
        },
        "limit": 10
    })
    
    print(f"      Found {related_tool_calls.total} tool calls matching 'search/retrieve' pattern")
    
    # Find conversation turns in sessions that completed similar tasks
    related_conversations = db.records.find({
        "labels": ["CONVERSATION_TURN"],
        "where": {
            "SESSION": {
                "$relation": {"type": "PART_OF", "direction": "in"},
                "task": {"$contains": "user"}
            }
        },
        "limit": 5
    })
    
    print(f"      Found {related_conversations.total} conversation turns from 'user' related sessions")
    
    # =========================================================================
    # PHASE 4: Vector search with relationship filtering
    # =========================================================================
    print("\n[4] Demonstrating hybrid search (vector + graph filter)...")
    
    # This is the key differentiator: we can filter vector search by relationships
    # Not just "find similar content" but "find similar content in THIS session"
    
    search_query = "analysis patterns cohort retention"
    
    # Pure vector search (baseline)
    pure_vector_results = db.ai.search({
        "propertyName": "content",
        "query": search_query,
        "labels": ["CONVERSATION_TURN"],
        "limit": 3
    })
    
    print(f"      Pure vector search found: {len(pure_vector_results.data)} results")
    
    # Hybrid search: vector similarity filtered by session relationship
    hybrid_results = db.ai.search({
        "propertyName": "content",
        "query": search_query,
        "labels": ["CONVERSATION_TURN"],
        "where": {
            "SESSION": {"$id": session.id}  # Filter to current session only
        },
        "limit": 3
    })
    
    print(f"      Hybrid search (session-filtered) found: {len(hybrid_results.data)} results")
    
    if hybrid_results.data:
        top_result = hybrid_results.data[0]
        print(f"      Top result: \"{top_result.data.get('content', '')[:50]}...\"")
        print(f"      Similarity score: {top_result.score:.3f}" if top_result.score else "")
    
    # =========================================================================
    # PHASE 5: Atomic memory update
    # =========================================================================
    print("\n[5] Updating agent memory atomically...")
    
    # This demonstrates the atomic transaction: all-or-nothing updates
    # In a real agent, you'd want to ensure state consistency
    
    final_state = {
        "thinking": "Analysis complete, preparing final report",
        "step": 3,
        "tools_used": ["search_knowledge_base", "execute_python", "retrieve_context"],
        "context_collected": ["User behavior docs", "Retention metrics", "Historical sessions"],
        "confidence_score": 0.85,
        "completed_at": datetime.now().isoformat()
    }
    
    with db.transactions.begin() as tx:
        # Update the session status
        session.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "confidence_score": 0.85
        })
        
        # Create final summary node
        summary = db.records.create(
            label="SESSION_SUMMARY",
            data={
                "findings": "User retention analysis complete",
                "metrics_calculated": True,
                "context_used": 3,
                "confidence": 0.85
            },
            transaction=tx
        )
        
        # Link summary to session
        db.records.attach(
            source=session,
            target=summary,
            options={"type": "HAS_SUMMARY", "direction": "out"},
            transaction=tx
        )
        
        # Update agent state
        agent_state.update(final_state)
    
    print(f"      Session status: completed")
    print(f"      Confidence score: {final_state['confidence_score']}")
    print(f"      Tools used: {len(final_state['tools_used'])}")
    print(f"      All operations committed in single transaction")
    
    return session


def simulate_tool_execution(tool_name: str, tool_input: str) -> str:
    """
    Simulates tool execution for demonstration purposes.
    In a real LangChain agent, this would call actual tools.
    """
    # Simulated tool outputs based on input
    outputs = {
        "search_knowledge_base": f"Found documentation on user behavior patterns, retention cohorts, and funnel analysis techniques for: {tool_input}",
        "execute_python": f"Python script executed successfully. Calculated cohort retention: Week 1: 68%, Week 2: 45%, Week 4: 32%, Week 8: 18%",
        "retrieve_context": f"Retrieved 3 similar historical sessions discussing {tool_input}. Average session length: 12 minutes. Common outcomes: feature recommendations, bug reports.",
    }
    
    return outputs.get(tool_name, f"Executed {tool_name} with input: {tool_input}")


# =============================================================================
# LANGCHAIN INTEGRATION DEMONSTRATION
# =============================================================================

def demonstrate_langchain_pattern():
    """
    Shows how RushDB integrates with LangChain's agent patterns.
    
    In a typical LangChain setup with memory:
    - You need a ChatMessageHistory
    - You need a Memory store for longer context
    - You might use a VectorStore for RAG
    - You might track conversation state separately
    
    With RushDB, all of these become one unified store.
    """
    print("\n" + "-" * 70)
    print(" LANGCHAIN INTEGRATION PATTERN ")
    print("-" * 70)
    
    print("""
    Typical LangChain agent with multiple backends:
    
        LangChain Agent
            ├── ChatMessageHistory (Redis)     <- short-term conversation
            ├── BufferMemory (Redis)           <- recent context
            ├── VectorStoreRetriever (Pinecone) <- semantic retrieval
            └── Custom callbacks (Neo4j)        <- conversation graph
            
    Pain points:
    - 4 different APIs to manage
    - Serialization overhead between systems
    - Partial failures when one system succeeds
    - Expensive: 4 services × 4× operational complexity
    
    With RushDB, this becomes:
    
        LangChain Agent
            └── RushDB Memory Store (single backend)
                ├── CONVERSATION_TURN (chat history)
                ├── AGENT_STATE (memory buffer)
                └── Vector search (semantic retrieval)
    """)
    
    # Show the RushDB pattern
    print("\n    RushDB pattern (pseudo-code):")
    print("""
    # Initialize once
    db = RushDB(api_key)
    
    # Store conversation turns (replaces ChatMessageHistory)
    db.records.create(label="CONVERSATION_TURN", data={
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update agent memory (replaces BufferMemory)
    agent_state.update({
        "recent_context": [...],
        "short_term_memory": {...}
    })
    
    # Retrieve context with vector search (replaces VectorStoreRetriever)
    relevant = db.ai.search({
        "propertyName": "content",
        "query": user_query,
        "labels": ["CONVERSATION_TURN"],
        "where": {"SESSION": {"$id": current_session.id}},
        "limit": 5
    })
    """)
    
    return True


# =============================================================================
    # MAIN EXECUTION
# =============================================================================

def main():
    """Run the complete agentic workflow demonstration."""
    print("\n" + "#" * 70)
    print("# RUSHDB: UNIFIED MEMORY FOR AGENTIC AI")
    print("#" * 70)
    
    print("""
    This example demonstrates how RushDB replaces the "Pinecone + Neo4j + Redis" 
    stack that LangChain agents typically require.
    
    What you'll see:
    1. Creating agent sessions with state in a single transaction
    2. Storing tool outputs as JSON properties
    3. Graph traversal to find related conversation turns
    4. Vector search filtered by session relationships
    5. Atomic updates that keep state consistent
    """)
    
    # Ensure vector indexes exist
    print("\nEnsuring vector indexes exist...")
    ensure_vector_indexes()
    
    # Run the main workflow
    final_session = run_agentic_workflow()
    
    # Show LangChain integration pattern
    demonstrate_langchain_pattern()
    
    # Final summary
    print("\n" + "=" * 70)
    print(" WORKFLOW COMPLETE ")
    print("=" * 70)
    
    print(f"""
    Key takeaways:
    
    1. SINGLE API: Instead of 3 systems (Pinecone + Neo4j + Redis),
       RushDB provides graph traversal + vector search + state management.
    
    2. ATOMIC OPERATIONS: Tool calls, session state, and relationships
       are written together. No partial failures.
    
    3. RELATIONSHIP FILTERING: Vector search isn't just "find similar" -
       it's "find similar content IN this session" or "from this user".
    
    4. GRAPH QUERIES: Navigate from sessions → tool calls → outcomes
       to understand what happened and why.
    
    Final session ID: {final_session.id}
    
    Learn more: https://docs.rushdb.com
    """)
    
    return final_session


if __name__ == "__main__":
    main()
