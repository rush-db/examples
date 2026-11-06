#!/usr/bin/env python3
"""
Real-Time Conversation Summarization with Graph-Traced References

A demonstration of RushDB's capabilities for:
- Storing conversation threads as property graph nodes
- Creating vector-embedded summaries for semantic search
- Graph-traced entity references across conversations
- Real-time message ingestion and querying

This example simulates a Slack-like messaging system with automatic
summarization and entity tracking capabilities.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer


# =============================================================================
# Configuration
# =============================================================================

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_DIMENSIONS = int(os.getenv("VECTOR_DIMENSIONS", "384"))
INDEX_LABEL = "MESSAGE"
INDEX_PROPERTY = "content"


# =============================================================================
# Helper Functions
# =============================================================================

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_step(step_num: int, message: str):
    """Print a numbered step with visual indicator."""
    print(f"\n[{step_num}] {message}")


def get_or_create_vector_index(db: RushDB) -> str:
    """Get existing index or create a new one for message embeddings."""
    # Check for existing indexes
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx['label'] == INDEX_LABEL and idx['propertyName'] == INDEX_PROPERTY:
            print(f"  ✓ Using existing vector index: {idx['__id']}")
            return idx['__id']
    
    # Create new index
    print(f"  ✓ Creating vector index for {INDEX_LABEL}.{INDEX_PROPERTY}...")
    result = db.ai.indexes.create({
        "label": INDEX_LABEL,
        "propertyName": INDEX_PROPERTY,
        "sourceType": "external",
        "dimensions": VECTOR_DIMENSIONS,
    })
    index_id = result.data["__id"]
    print(f"  ✓ Created index: {index_id}")
    return index_id


# =============================================================================
# Step 1: Create Conversations and Messages
# =============================================================================

def create_conversation_with_messages(db: RushDB, title: str, messages: list) -> dict:
    """
    Create a conversation thread with messages.
    Demonstrates: Record creation, relationship attachment, transactions.
    """
    print_section("Step 1: Creating Conversations and Messages")
    
    conversation_data = {
        "conversationId": f"conv_{datetime.now().timestamp()}",
        "title": title,
        "status": "active",
        "createdAt": datetime.now().isoformat(),
    }
    
    with db.transactions.begin() as tx:
        # Create the conversation record
        conversation = db.records.create(
            label="CONVERSATION",
            data=conversation_data,
            transaction=tx
        )
        print(f"  ✓ Created conversation: {title}")
        
        # Create each message and link to conversation
        message_records = []
        for idx, content in enumerate(messages):
            message = db.records.create(
                label="MESSAGE",
                data={
                    "content": content,
                    "index": idx,
                    "timestamp": datetime.now().isoformat(),
                },
                transaction=tx
            )
            
            # Link message to conversation
            db.records.attach(
                source=conversation,
                target=message,
                options={"type": "CONTAINS", "direction": "out"},
                transaction=tx
            )
            message_records.append(message)
        
        print(f"  ✓ Added {len(messages)} messages to conversation")
    
    return {
        "conversation": conversation,
        "messages": message_records
    }


# =============================================================================
# Step 2: Create Vector-Embedded Summaries
# =============================================================================

def generate_and_index_summary(
    db: RushDB,
    index_id: str,
    conversation_id: str,
    summary_text: str
) -> dict:
    """
    Generate a summary with vector embedding and index it.
    Demonstrates: External embedding generation, vector upsert.
    """
    print_section("Step 2: Creating Vector-Embedded Summary")
    
    # Load embedding model
    print(f"  ✓ Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Generate embedding
    print(f"  ✓ Generating embedding for summary...")
    embedding = model.encode(summary_text).tolist()
    print(f"  ✓ Embedding dimensions: {len(embedding)}")
    
    # Create summary record with inline vector
    summary = db.records.create(
        label="SUMMARY",
        data={
            "text": summary_text,
            "conversationId": conversation_id,
            "generatedAt": datetime.now().isoformat(),
            "model": EMBEDDING_MODEL,
        },
        vectors=[{"propertyName": "text", "vector": embedding}]
    )
    print(f"  ✓ Created summary record: {summary.id}")
    
    # Upsert vector to index
    print(f"  ✓ Upserting vector to index...")
    db.ai.indexes.upsert_vectors(index_id, {
        "items": [{
            "recordId": summary.id,
            "vector": embedding
        }]
    })
    
    return summary


# =============================================================================
# Step 3: Graph-Traced References
# =============================================================================

def find_graph_traced_references(db: RushDB, conversation_id: str) -> dict:
    """
    Query graph-traced references from a conversation.
    Demonstrates: Relationship traversal, record filtering by related records.
    """
    print_section("Step 3: Graph-Traced Reference Queries")
    
    results = {}
    
    # Find all messages in conversation via graph traversal
    # Using the relationship filter to find messages linked to conversation
    messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "CONVERSATION": {
                "conversationId": conversation_id
            }
        },
        "orderBy": {"index": "asc"}
    })
    results["messages"] = messages.data
    print(f"  ✓ Found {len(messages.data)} messages via graph traversal")
    
    # Find entities referenced in conversation
    entities = db.records.find({
        "labels": ["ENTITY"],
        "where": {
            "CONVERSATION": {
                "conversationId": conversation_id
            }
        }
    })
    results["entities"] = entities.data
    print(f"  ✓ Found {len(entities.data)} referenced entities: {[e.get('identifier') for e in entities.data]}")
    
    # Find topics discussed
    topics = db.records.find({
        "labels": ["TOPIC"],
        "where": {
            "CONVERSATION": {
                "conversationId": conversation_id
            }
        }
    })
    results["topics"] = topics.data
    print(f"  ✓ Found {len(topics.data)} topics: {[t.get('name') for t in topics.data]}")
    
    return results


# =============================================================================
# Step 4: Real-Time Semantic Search
# =============================================================================

def search_messages_semantically(db: RushDB, index_id: str, query: str, limit: int = 5) -> list:
    """
    Perform semantic search on messages using pre-computed vectors.
    Demonstrates: Vector-based semantic search, relevance scoring.
    """
    print_section("Step 4: Real-Time Semantic Search")
    
    # Load model and encode query
    print(f"  ✓ Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    print(f"  ✓ Encoding query: '{query}'")
    query_vector = model.encode(query).tolist()
    
    # Perform semantic search with pre-computed vector
    print(f"  ✓ Searching vector index...")
    search_results = db.ai.search({
        "propertyName": INDEX_PROPERTY,
        "queryVector": query_vector,
        "labels": [INDEX_LABEL],
        "limit": limit
    })
    
    print(f"  ✓ Found {len(search_results.data)} semantically relevant messages")
    
    # Display results with scores
    for i, result in enumerate(search_results.data, 1):
        score = result.score or result.get("__score", 0.0)
        content = result.get("content", "")
        msg_id = result.id[:20] + "..." if len(result.id) > 20 else result.id
        print(f"\n    [{i}] Score: {score:.4f}")
        print(f"        ID: {msg_id}")
        print(f"        Content: \"{content[:80]}...\"" if len(content) > 80 else f"        Content: \"{content}\"")
    
    return search_results.data


# =============================================================================
# Step 5: Conversation Graph Traversal
# =============================================================================

def traverse_conversation_graph(db: RushDB) -> dict:
    """
    Traverse the conversation graph to find related summaries.
    Demonstrates: Multi-hop graph traversal, aggregation.
    """
    print_section("Step 5: Conversation Graph Traversal")
    
    # Find all active conversations
    conversations = db.records.find({
        "labels": ["CONVERSATION"],
        "where": {"status": "active"}
    })
    print(f"  ✓ Found {conversations.total} active conversations")
    
    # For each conversation, get linked summaries
    conversation_summaries = []
    for conv in conversations.data:
        summaries = db.records.find({
            "labels": ["SUMMARY"],
            "where": {
                "CONVERSATION": {
                    "conversationId": conv.get("conversationId")
                }
            }
        })
        if summaries.data:
            conversation_summaries.append({
                "conversation": conv,
                "summaries": summaries.data
            })
    
    print(f"  ✓ Found {len(conversation_summaries)} conversations with summaries")
    
    # Display summary connections
    for item in conversation_summaries:
        conv_title = item["conversation"].get("title", "Unknown")
        summary_count = len(item["summaries"])
        print(f"\n    📋 {conv_title}")
        print(f"       Summaries: {summary_count}")
        for summary in item["summaries"]:
            text = summary.get("text", "")[:60]
            print(f"       • {text}...")
    
    return {
        "conversations": conversations.data,
        "conversation_summaries": conversation_summaries
    }


# =============================================================================
# Step 6: Real-Time Message Ingestion
# =============================================================================

def ingest_realtime_message(
    db: RushDB,
    conversation_id: str,
    content: str,
    sender: str
) -> dict:
    """
    Simulate real-time message ingestion.
    Demonstrates: Atomic record creation, relationship linking.
    """
    print_section("Step 6: Real-Time Message Ingestion")
    
    with db.transactions.begin() as tx:
        # Create the message record
        message = db.records.create(
            label="MESSAGE",
            data={
                "content": content,
                "sender": sender,
                "timestamp": datetime.now().isoformat(),
                "isRealtime": True,
            },
            transaction=tx
        )
        print(f"  ✓ Ingested message from {sender}")
        
        # Find the conversation and link
        conversation = db.records.find({
            "labels": ["CONVERSATION"],
            "where": {"conversationId": conversation_id}
        })
        
        if conversation.data:
            db.records.attach(
                source=conversation.data[0],
                target=message,
                options={"type": "CONTAINS", "direction": "out"},
                transaction=tx
            )
            print(f"  ✓ Linked message to conversation: {conversation_id}")
        
        # Generate and attach entities (simplified extraction)
        words = content.lower().split()
        for word in words:
            if word.startswith("@") or word.startswith("#"):
                entity = db.records.create(
                    label="ENTITY",
                    data={
                        "identifier": word,
                        "type": "realtime-mention",
                        "timestamp": datetime.now().isoformat()
                    },
                    transaction=tx
                )
                db.records.attach(
                    source=message,
                    target=entity,
                    options={"type": "MENTIONS", "direction": "out"},
                    transaction=tx
                )
        
        mentions = [w for w in words if w.startswith("@") or w.startswith("#")]
        if mentions:
            print(f"  ✓ Extracted entities: {mentions}")
    
    return message


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Run the complete demonstration."""
    print("\n" + "=" * 60)
    print("  REAL-TIME CONVERSATION SUMMARIZATION")
    print("  with Graph-Traced References")
    print("=" * 60)
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\n❌ ERROR: RUSHDB_API_KEY environment variable not set")
        print("   Please copy .env.example to .env and add your API key")
        return
    
    print("\n✓ Initializing RushDB client...")
    db = RushDB(api_key)
    print("✓ Connected to RushDB")
    
    # Initialize vector index
    index_id = get_or_create_vector_index(db)
    
    # Sample conversation data
    sample_messages = [
        "Team, we need to discuss the deployment pipeline for v2.0",
        "I've prepared a detailed runbook for the rollback procedure",
        "@alice can you review the CI/CD configuration changes?",
        "The staging environment is ready for integration testing",
        "Let's schedule a walkthrough for the new monitoring setup",
        "All tests are passing on the feature branch",
        "Deployment to production scheduled for Friday 3pm",
        "Remember to update the documentation for the API changes",
    ]
    
    conversation_title = "Deployment Planning for Q4 Release"
    
    # Step 1: Create conversations and messages
    print_step(1, "Creating conversation thread with messages...")
    result = create_conversation_with_messages(db, conversation_title, sample_messages)
    conversation = result["conversation"]
    conversation_id = conversation.get("conversationId")
    print(f"  ✓ Conversation ID: {conversation_id}")
    
    # Step 2: Create vector-embedded summary
    print_step(2, "Generating summary with vector embedding...")
    summary_text = (
        "Team discussed deployment pipeline for v2.0 release. "
        "Runbook prepared for rollback procedure. CI/CD config changes pending review from Alice. "
        "Staging environment ready for integration testing. "
        "Deployment to production scheduled for Friday at 3pm."
    )
    summary = generate_and_index_summary(db, index_id, conversation_id, summary_text)
    
    # Link summary to conversation
    db.records.attach(
        source=conversation,
        target=summary,
        options={"type": "HAS_SUMMARY", "direction": "out"}
    )
    print("  ✓ Linked summary to conversation")
    
    # Step 3: Query graph-traced references
    print_step(3, "Querying graph-traced references...")
    references = find_graph_traced_references(db, conversation_id)
    
    # Step 4: Semantic search
    print_step(4, "Performing semantic search...")
    search_query = "deployment pipeline configuration"
    search_results = search_messages_semantically(db, index_id, search_query, limit=5)
    
    # Step 5: Graph traversal
    print_step(5, "Traversing conversation graph...")
    graph_data = traverse_conversation_graph(db)
    
    # Step 6: Real-time message ingestion
    print_step(6, "Ingesting real-time message...")
    realtime_msg = ingest_realtime_message(
        db,
        conversation_id,
        "Just verified the rollback script @alice - ready for production deploy #deployment",
        "bob"
    )
    print(f"  ✓ Real-time message ID: {realtime_msg.id}")
    
    # Summary statistics
    print_section("Summary Statistics")
    print(f"  • Conversation created: {conversation_id}")
    print(f"  • Messages indexed: {len(sample_messages)}")
    print(f"  • Summary with embedding: {summary.id}")
    print(f"  • Semantic search results: {len(search_results)}")
    print(f"  • Graph-traced references: {len(references.get('entities', []))} entities, {len(references.get('topics', []))} topics")
    print(f"  • Real-time messages ingested: 1")
    
    print("\n" + "=" * 60)
    print("  ✓ Demo Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  • Run 'python seed.py' to populate more test data")
    print("  • Check RushDB dashboard for graph visualization")
    print("  • Review docs.rushdb.com for advanced features")


if __name__ == "__main__":
    main()
