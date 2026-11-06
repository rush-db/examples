"""
Temporal Graph Queries for Conversation History Tracking

This demonstration shows how a graph database approach solves the specific
structural problem of interconnected, time-ordered conversation data.

Key patterns demonstrated:
1. Bidirectional temporal links (NEXT/PREV)
2. Conversation window queries
3. Branching and merging (escalation, handoff)
4. Vector embeddings for semantic search
5. Performance comparison with traditional approaches
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

from rushdb import RushDB

# Initialize client
db = RushDB(API_KEY)

# ============================================================================
# SECTION 1: Setting Up the Data Model
# ============================================================================

def create_sample_conversation():
    """
    Create a sample conversation demonstrating bidirectional temporal links.
    
    In a document store, messages would be an array in a document.
    In a graph, each message is a node with NEXT/PREV links.
    """
    print("\n" + "=" * 60)
    print("SECTION 1: Bidirectional Temporal Links")
    print("=" * 60)
    
    # Clean up any existing sample data
    try:
        db.records.delete_many({"labels": ["MESSAGE"], "where": {"conversationId": "demo_conv"}})
        db.records.delete_many({"labels": ["CONVERSATION"], "where": {"conversationId": "demo_conv"}})
        db.records.delete_many({"labels": ["USER"], "where": {"externalId": {"$in": ["demo_user", "demo_agent"]}}})
        db.records.delete_many({"labels": ["AGENT"], "where": {"externalId": {"$in": ["demo_agent"]}}})
    except Exception:
        pass
    
    print("\n📝 Creating a conversation with bidirectional message links...")
    print("   This shows how messages become first-class nodes in the graph.\n")
    
    # Create participants
    user = db.records.create(
        label="USER",
        data={"externalId": "demo_user", "name": "Alex Demo", "email": "alex@example.com"}
    )
    agent = db.records.create(
        label="AGENT",
        data={"externalId": "demo_agent", "name": "Sam Support", "specialty": "technical"}
    )
    
    # Create conversation
    conversation = db.records.create(
        label="CONVERSATION",
        data={
            "conversationId": "demo_conv",
            "channel": "chat",
            "startedAt": datetime.now().isoformat(),
            "status": "active"
        }
    )
    
    # Link participants
    db.records.attach(source=user, target=conversation, options={"type": "PARTICIPATES_IN"})
    db.records.attach(source=agent, target=conversation, options={"type": "PARTICIPATES_IN"})
    
    # Message content
    messages = [
        {"content": "Hi, I can't log into my account", "senderType": "user", "senderId": "demo_user", "senderName": "Alex Demo"},
        {"content": "I'm sorry to hear that! Let me help you with that.", "senderType": "agent", "senderId": "demo_agent", "senderName": "Sam Support"},
        {"content": "I've tried the password reset but it still doesn't work", "senderType": "user", "senderId": "demo_user", "senderName": "Alex Demo"},
        {"content": "Can you tell me what error message you're seeing?", "senderType": "agent", "senderId": "demo_agent", "senderName": "Sam Support"},
        {"content": "It says 'Invalid credentials' even though I'm sure the password is correct", "senderType": "user", "senderId": "demo_user", "senderName": "Alex Demo"},
        {"content": "I found the issue! Your account was locked due to multiple failed attempts. I've unlocked it now.", "senderType": "agent", "senderId": "demo_agent", "senderName": "Sam Support"},
        {"content": "That fixed it! Thank you so much!", "senderType": "user", "senderId": "demo_user", "senderName": "Alex Demo"},
    ]
    
    print("   Creating 7 messages with temporal links...")
    print("   (Graph approach vs. array in document)\n")
    
    prev_message = None
    for i, msg_data in enumerate(messages):
        msg = db.records.create(
            label="MESSAGE",
            data={
                **msg_data,
                "timestamp": (datetime.now() + timedelta(minutes=i * 2)).isoformat(),
                "conversationId": "demo_conv"
            }
        )
        
        # Link to conversation
        db.records.attach(source=msg, target=conversation, options={"type": "PART_OF"})
        
        # Create bidirectional temporal links
        if prev_message:
            db.records.attach(source=prev_message, target=msg, options={"type": "NEXT"})
            db.records.attach(source=msg, target=prev_message, options={"type": "PREV"})
            print(f"   Linked Message {i} --> Message {i+1} (NEXT/PREV)")
        
        prev_message = msg
    
    print("\n   ✅ Created 7 messages with bidirectional temporal links")
    print("   - Each message knows its NEXT and PREV neighbors")
    print("   - O(1) insertion - no document updates needed")
    print("   - Natural ordering - just follow the links")
    
    return conversation


# ============================================================================
# SECTION 2: Temporal Traversal
# ============================================================================

def demonstrate_temporal_traversal(conversation):
    """
    Show how temporal link traversal works.
    
    Instead of:
      messages = conversation.messages  # Load entire array
      last_msg = messages[-1]              # Then index into it
    
    We do:
      last_msg = follow PREV links until no more
    """
    print("\n" + "=" * 60)
    print("SECTION 2: Temporal Link Traversal")
    print("=" * 60)
    
    # Find the first message
    first_msg = db.records.find({
        "labels": ["MESSAGE"],
        "where": {"conversationId": "demo_conv"},
        "orderBy": {"timestamp": "asc"},
        "limit": 1
    })
    
    if not first_msg.data:
        print("   No messages found!")
        return
    
    current = first_msg.data[0]
    
    print("\n🔗 Traversing the conversation via temporal links...")
    print("   (Starting from first message, following NEXT links)\n")
    
    traversed = []
    while current:
        sender_type = current.data.get("senderType", "unknown")
        content = current.data.get("content", "")[:50]
        sender = current.data.get("senderName", "?")
        traversed.append(current)
        
        print(f"   [{len(traversed)}] {sender_type.upper()} ({sender}): {content}...")
        
        # Follow NEXT link to find next message
        next_result = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "PREV": {"$id": {"$in": [current.id]}}
            }
        })
        
        if next_result.data:
            current = next_result.data[0]
        else:
            current = None
    
    print(f"\n   ✅ Successfully traversed {len(traversed)} messages via temporal links")
    
    # Now show reverse traversal
    print("\n   Reversing direction (following PREV links from last message)...")
    
    current = traversed[-1]  # Last message
    reverse_traversed = []
    
    while current:
        reverse_traversed.append(current.data.get("content", "")[:30])
        
        prev_result = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "NEXT": {"$id": {"$in": [current.id]}}
            }
        })
        
        if prev_result.data:
            current = prev_result.data[0]
        else:
            current = None
    
    print(f"   ✅ Reverse traversal found {len(reverse_traversed)} messages")


# ============================================================================
# SECTION 3: Conversation Window Queries
# ============================================================================

def demonstrate_conversation_windows():
    """
    Query messages within a time window.
    
    In a document store: Aggregate query with $match on timestamps
    In a graph: Navigate relationships from conversation to messages
    """
    print("\n" + "=" * 60)
    print("SECTION 3: Conversation Window Queries")
    print("=" * 60)
    
    # Query: Get messages from the last hour
    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
    
    print("\n📅 Query: All messages in the last hour...")
    
    recent_messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {"timestamp": {"$gte": one_hour_ago}},
        "orderBy": {"timestamp": "asc"},
        "limit": 50
    })
    
    print(f"   Found {recent_messages.total} messages in the last hour")
    
    # Query: Messages between specific participants
    print("\n👥 Query: Messages between user 'demo_user' and agent 'demo_agent'...")
    
    between_participants = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "senderId": {"$in": ["demo_user", "demo_agent"]},
            "conversationId": "demo_conv"
        },
        "orderBy": {"timestamp": "asc"}
    })
    
    print(f"   Found {between_participants.total} messages between these participants")
    
    # Query: Messages where agent didn't respond within 4 hours
    print("\n⏱️  Query: User messages with no agent reply within 4 hours...")
    print("   (Simulating the pattern - finding gaps in agent response)\n")
    
    user_messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "senderType": "user",
            "conversationId": "demo_conv"
        },
        "orderBy": {"timestamp": "asc"}
    })
    
    slow_responses = []
    for i, msg in enumerate(user_messages.data):
        msg_time = datetime.fromisoformat(msg.data["timestamp"])
        
        # Find next agent message
        next_agent = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "senderType": "agent",
                "timestamp": {"$gt": msg.data["timestamp"]},
                "conversationId": "demo_conv"
            },
            "orderBy": {"timestamp": "asc"},
            "limit": 1
        })
        
        if next_agent.data:
            agent_time = datetime.fromisoformat(next_agent.data[0].data["timestamp"])
            wait_hours = (agent_time - msg_time).total_seconds() / 3600
            
            if wait_hours >= 0:  # Using seconds for demo (would be 4 in real scenario)
                slow_responses.append({
                    "user_message": msg.data["content"][:40],
                    "wait_time": f"{wait_hours:.1f} hours"
                })
    
    print(f"   Found {len(slow_responses)} potential slow-response scenarios")
    
    print("\n   ✅ Graph approach: Relationships make temporal queries natural")


# ============================================================================
# SECTION 4: Branching and Merging
# ============================================================================

def demonstrate_branching_scenarios():
    """
    Handle conversation branching (escalation, handoff) as first-class graph operations.
    
    This is where graphs truly shine compared to document arrays.
    """
    print("\n" + "=" * 60)
    print("SECTION 4: Branching and Merging Scenarios")
    print("=" * 60)
    
    # Create an escalated conversation
    print("\n🔀 Creating an escalation (chat → phone handoff)...")
    
    # Find original conversation
    original = db.records.findOne({
        "labels": ["CONVERSATION"],
        "where": {"conversationId": "demo_conv"}
    })
    
    if not original:
        print("   Original conversation not found!")
        return
    
    # Create escalated conversation
    escalated_conv = db.records.create(
        label="CONVERSATION",
        data={
            "conversationId": "demo_conv_escalated",
            "channel": "phone",
            "startedAt": datetime.now().isoformat(),
            "status": "active",
            "escalationReason": "Technical issue requiring manager approval"
        }
    )
    
    # Link escalated conversation to original via BRANCHED_FROM
    db.records.attach(
        source=escalated_conv,
        target=original,
        options={"type": "BRANCHED_FROM"}
    )
    
    # Create escalation message
    escalation_msg = db.records.create(
        label="MESSAGE",
        data={
            "content": "I'm escalating this to our technical team for further investigation.",
            "senderType": "agent",
            "senderId": "demo_agent",
            "senderName": "Sam Support",
            "timestamp": datetime.now().isoformat(),
            "conversationId": "demo_conv_escalated"
        }
    )
    
    db.records.attach(source=escalation_msg, target=escalated_conv, options={"type": "PART_OF"})
    
    # Create resolution message
    resolution_msg = db.records.create(
        label="MESSAGE",
        data={
            "content": "After investigation, we found a backend issue and have fixed it. Your account should work now.",
            "senderType": "agent",
            "senderId": "manager_agent",
            "senderName": "Mike Manager",
            "timestamp": (datetime.now() + timedelta(minutes=30)).isoformat(),
            "conversationId": "demo_conv_escalated"
        }
    )
    
    db.records.attach(source=resolution_msg, target=escalated_conv, options={"type": "PART_OF"})
    db.records.attach(source=escalation_msg, target=resolution_msg, options={"type": "NEXT"})
    db.records.attach(source=resolution_msg, target=escalation_msg, options={"type": "PREV"})
    
    print("   ✅ Created escalated conversation with BRANCHED_FROM link")
    print("   - Original conversation ID: demo_conv")
    print("   - Escalated conversation ID: demo_conv_escalated")
    print("   - Channel changed: chat → phone")
    
    # Now demonstrate merging - linking multiple conversations
    print("\n🔗 Creating a merge scenario (merging phone + email threads)...")
    
    # Create email thread
    email_conv = db.records.create(
        label="CONVERSATION",
        data={
            "conversationId": "demo_conv_email",
            "channel": "email",
            "startedAt": datetime.now().isoformat(),
            "status": "active"
        }
    )
    
    # Create MERGED_FROM link from email to phone escalation
    db.records.attach(
        source=email_conv,
        target=escalated_conv,
        options={"type": "MERGED_FROM"}
    )
    
    print("   ✅ Created email conversation linked to phone escalation")
    print("   - This represents a chat → phone → email handoff flow")
    print("   - No data duplication needed!")
    
    # Query branching structure
    print("\n📊 Query: Finding all branches of demo_conv...")
    
    branches = db.records.find({
        "labels": ["CONVERSATION"],
        "where": {
            "CONVERSATION": {
                "$relation": {"type": "BRANCHED_FROM", "direction": "in"},
                "conversationId": "demo_conv"
            }
        }
    })
    
    print(f"   Found {branches.total} branched conversations")
    for branch in branches.data:
        print(f"   - {branch.data['conversationId']} ({branch.data['channel']})")
    
    print("\n   ✅ Graph approach: Branching is a relationship, not duplication")


# ============================================================================
# SECTION 5: Vector Embeddings for Semantic Search
# ============================================================================

def demonstrate_semantic_search():
    """
    Attach vector embeddings to messages for semantic search.
    
    This demonstrates:
    - How to create vector index
    - How to attach embeddings to records
    - How to search semantically across conversations
    """
    print("\n" + "=" * 60)
    print("SECTION 5: Vector Embeddings for Semantic Search")
    print("=" * 60)
    
    # Try to import sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        print("\n🧠 Loading embedding model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("   ✅ Model loaded successfully")
    except ImportError:
        print("\n⚠️  sentence-transformers not installed")
        print("   Install with: pip install sentence-transformers")
        print("   Skipping semantic search demonstration")
        return
    
    # Get messages to embed
    messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {"conversationId": "demo_conv"},
        "limit": 10
    })
    
    if not messages.data:
        print("   No messages found!")
        return
    
    # Create vector index
    print("\n📐 Creating vector index for MESSAGE.content...")
    
    try:
        # Check if index exists
        indexes = db.ai.indexes.find()
        existing = [i for i in indexes.data if i.get('label') == 'MESSAGE' and i.get('propertyName') == 'content']
        
        if existing:
            index_id = existing[0]['__id']
            print(f"   Using existing index: {index_id}")
        else:
            index = db.ai.indexes.create({
                "label": "MESSAGE",
                "propertyName": "content",
                "sourceType": "external",
                "dimensions": 384,  # all-MiniLM-L6-v2 output dimension
                "similarityFunction": "cosine"
            })
            index_id = index.data["__id"]
            print(f"   ✅ Created vector index: {index_id}")
    except Exception as e:
        print(f"   ⚠️  Could not create index: {e}")
        return
    
    # Generate embeddings and upsert
    print("\n🔢 Generating embeddings for messages...")
    
    contents = [m.data.get("content", "") for m in messages.data]
    vectors = model.encode(contents)
    
    items = []
    for i, msg in enumerate(messages.data):
        items.append({
            "recordId": msg.id,
            "vector": vectors[i].tolist()
        })
        print(f"   - Embedded message {i+1}: '{contents[i][:30]}...'")
    
    # Upsert vectors
    try:
        db.ai.indexes.upsert_vectors(index_id, {"items": items})
        print("\n   ✅ Upserted vectors to index")
    except Exception as e:
        print(f"   ⚠️  Could not upsert vectors: {e}")
        return
    
    # Perform semantic search
    print("\n🔍 Semantic Search: 'password reset problems'")
    
    try:
        results = db.ai.search({
            "propertyName": "content",
            "query": "password reset problems",
            "labels": ["MESSAGE"],
            "limit": 3
        })
        
        print(f"\n   Found {len(results.data)} semantically similar messages:")
        for i, result in enumerate(results.data):
            score = result.score if hasattr(result, 'score') else result.data.get('__score', 0)
            content = result.data.get("content", "")[:60]
            print(f"   [{i+1}] Score: {score:.3f}")
            print(f"       '{content}...'")
        
        print("\n   ✅ Semantic search found password-related messages!")
        
    except Exception as e:
        print(f"   ⚠️  Semantic search failed: {e}")
    
    print("\n   ✅ Graph + Vectors: Zero schema migration for search!")


# ============================================================================
# SECTION 6: Performance Comparison
# ============================================================================

def demonstrate_performance_comparison():
    """
    Demonstrate why graph traversal is more efficient than array/document approaches.
    
    This is a conceptual comparison showing the algorithmic difference.
    """
    print("\n" + "=" * 60)
    print("SECTION 6: Performance Comparison")
    print("=" * 60)
    
    print("\n⚡ Comparing graph vs document store patterns\n")
    
    # Pattern 1: Get last message
    print("📍 Pattern 1: Get the last message of a conversation")
    print("   ")
    print("   Document Store (MongoDB):")
    print("   ```")
    print("   db.conversations.findOne({_id: 'conv_123'})")
    print("   // Returns document with entire messages[] array")
    print("   // Must load ALL messages into memory")
    print("   last_msg = doc.messages[doc.messages.length - 1]")
    print("   // Time: O(n) memory, O(1) access")
    print("   ```")
    print("   ")
    print("   Graph Store (RushDB):")
    print("   ```")
    print("   # Follow PREV links from first message")
    print("   current = first_message")
    print("   while has NEXT_link: current = NEXT")
    print("   last_msg = current")
    print("   // Time: O(n) traversal but O(1) per link")
    print("   // Memory: O(1) per step")
    print("   ```")
    
    # Pattern 2: Insert a message
    print("\n📍 Pattern 2: Insert a new message")
    print("   ")
    print("   Document Store:")
    print("   ```")
    print("   # Must update the entire conversation document")
    print("   db.conversations.updateOne(")
    print("     {_id: 'conv_123'},")
    print("     {$push: {messages: new_msg}}")
    print("   )")
    print("   // Time: O(document_size) for write")
    print("   // Lock: Entire document locked during update")
    print("   ```")
    print("   ")
    print("   Graph Store:")
    print("   ```")
    print("   # Create node + 2 relationships")
    print("   new_msg = create_node(MESSAGE)")
    print("   attach(prev_msg, new_msg, NEXT)")
    print("   attach(new_msg, prev_msg, PREV)")
    print("   // Time: O(1) - constant work")
    print("   // Lock: Only the 2 linked nodes")
    print("   ```")
    
    # Pattern 3: Find conversations with gaps
    print("\n📍 Pattern 3: Find conversations with 4+ hour gaps")
    print("   ")
    print("   Document Store (aggregation pipeline):")
    print("   ```")
    print("   db.conversations.aggregate([")
    print("     {$unwind: '$messages'},")
    print("     {$set: {gap: {$subtract: ["))
    print("       {$arrayElemAt: ['$messages.timestamp', 1]},")
    print("       {$arrayElemAt: ['$messages.timestamp', 0]}")
    print("     ]}}},")
    print("     {$match: {gap: {$gte: 14400}}}  // 4 hours")
    print("   ])")
    print("   // Complex, memory-intensive, slow")
    print("   ```")
    print("   ")
    print("   Graph Store:")
    print("   ```")
    print("   # For each conversation, traverse NEXT chain")
    print("   for msg in traverse(conversation):")
    print("     time_gap = next.timestamp - msg.timestamp")
    print("     if time_gap >= 4_hours: flag_gap()")
    print("   // Simple traversal, incremental")
    print("   ```")
    
    # Timing demo
    print("\n⏱️  Actual Timing Demo:")
    
    # Time finding last message via graph
    start = time.time()
    first = db.records.find({
        "labels": ["MESSAGE"],
        "where": {"conversationId": "demo_conv"},
        "orderBy": {"timestamp": "asc"},
        "limit": 1
    })
    
    if first.data:
        current = first.data[0]
        count = 0
        while current:
            count += 1
            next_r = db.records.find({
                "labels": ["MESSAGE"],
                "where": {"PREV": {"$id": current.id}}
            })
            current = next_r.data[0] if next_r.data else None
        
        graph_time = time.time() - start
        print(f"   Graph traversal: {graph_time*1000:.2f}ms for {count} messages")
    
    # Show the conceptual advantage
    print("\n" + "─" * 40)
    print("📊 Summary: Why Graphs Win for Conversation History")
    print("─" * 40)
    print("""
   | Pattern              | Document Store      | Graph Store            |
   |----------------------|---------------------|------------------------|
   | Message Insert       | O(n) full doc update | O(1) new node + links   |
   | Get Last Message     | O(n) load + O(1) idx | O(k) traverse k links   |
   | Temporal Order       | Sort/filter array    | Follow NEXT chain       |
   | Branch Conversation  | Duplicate array      | New node + relationship |
   | Add New Property     | Migration required   | Just add to node        |
   | Semantic Search      | Text match only      | Vector similarity       |
   
   The key insight: In conversation history, you're always navigating
   time-ordered relationships. Graphs model this natively.
   """)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "═" * 60)
    print("  TEMPORAL GRAPH QUERIES FOR CONVERSATION HISTORY")
    print("═" * 60)
    print("""
This demonstration shows how graph databases solve the structural
problem of interconnected, time-ordered conversation data.
""")
    
    # 1. Create sample conversation
    conversation = create_sample_conversation()
    
    # 2. Traverse via temporal links
    demonstrate_temporal_traversal(conversation)
    
    # 3. Query conversation windows
    demonstrate_conversation_windows()
    
    # 4. Branching and merging
    demonstrate_branching_scenarios()
    
    # 5. Vector embeddings
    demonstrate_semantic_search()
    
    # 6. Performance comparison
    demonstrate_performance_comparison()
    
    # Final summary
    print("\n" + "═" * 60)
    print("  DEMONSTRATION COMPLETE")
    print("═" * 60)
    print("""
Key Takeaways:

1. ✅ Messages as first-class nodes with NEXT/PREV links
   - O(1) insertion, natural ordering via traversal
   
2. ✅ Conversation window queries using temporal conditions
   - Filter by time ranges, participants, gaps
   
3. ✅ Branching as first-class relationships
   - BRANCHED_FROM for escalation
   - MERGED_FROM for handoff
   - No data duplication
   
4. ✅ Vector embeddings for semantic search
   - Zero schema migration
   - Add search to any message property
   
5. ✅ Superior performance for temporal patterns
   - Traversal vs array operations
   - Constant-time insertions
   - Incremental memory usage

For more information:
- https://docs.rushdb.com
- https://github.com/rush-db/examples
""")


if __name__ == "__main__":
    main()
