#!/usr/bin/env python3
"""
Multi-Turn Conversation Demo: Session Context Stores

This script demonstrates RushDB's property graph model for storing and querying
multi-turn conversations as connected subgraphs.

Key patterns covered:
1. Session creation with metadata
2. Message threading via relationship chains
3. Context retrieval (recent turns)
4. Conversation traversal by relationship type
5. Semantic search across message content
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError(
        "RUSHDB_API_KEY not found. Copy .env.example to .env and add your API key."
    )

db = RushDB(API_KEY)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def print_record(record, indent=2):
    """Pretty print a record's key fields."""
    prefix = " " * indent
    print(f"{prefix}id: {record.id}")
    print(f"{prefix}label: {record.label}")
    for key, value in record.data.items():
        if not key.startswith("__"):  # Skip system fields
            # Truncate long content
            if isinstance(value, str) and len(value) > 60:
                value = value[:57] + "..."
            print(f"{prefix}{key}: {value}")


# =============================================================================
# 1. LIST ALL SESSIONS
# =============================================================================
def list_sessions():
    print_section("1. All Conversation Sessions")

    result = db.records.find({
        "labels": ["SESSION"],
        "orderBy": {"created_at": "desc"}
    })
    sessions = result.data if hasattr(result, 'data') else result

    print(f"\nFound {len(sessions)} sessions:\n")
    for session in sessions:
        print(f"  📋 Session: {session.data.get('title', 'Untitled')}")
        print(f"     Status: {session.data.get('status', 'unknown')} | "
              f"Channel: {session.data.get('channel', 'unknown')}")
        print(f"     ID: {session.id}")
        print()


# =============================================================================
# 2. MESSAGE CHAINS: SHOW CONVERSATION FLOW
# =============================================================================
def show_message_chains():
    print_section("2. Message Chains (Conversation Flow)")

    # Get all sessions
    result = db.records.find({
        "labels": ["SESSION"],
        "limit": 3
    })
    sessions = result.data if hasattr(result, 'data') else result

    for session in sessions:
        print(f"\n  📝 Session: {session.data.get('title', 'Untitled')}")
        print("-" * 50)

        # Find messages in this session via CONTAINS relationship
        messages_result = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "SESSION": {
                    "$relation": {"type": "CONTAINS", "direction": "in"},
                    "title": session.data.get('title')
                }
            },
            "orderBy": {"turn": "asc"}
        })
        messages = messages_result.data if hasattr(messages_result, 'data') else messages_result

        if not messages:
            print("     (No messages found)")
            continue

        for msg in messages[:5]:  # Show first 5 messages
            role_icon = "👤" if msg.data.get("role") == "user" else "🤖"
            print(f"\n     Turn {msg.data.get('turn', '?')}: {role_icon} {msg.data.get('role', 'unknown')}")
            content = msg.data.get("content", "")
            # Truncate for display
            if len(content) > 80:
                content = content[:77] + "..."
            print(f"     {content}")


# =============================================================================
# 3. CONTEXT WINDOWS: GET RECENT TURNS
# =============================================================================
def show_context_windows():
    print_section("3. Context Windows (Last 3 Turns per Session)")

    # Get all sessions
    result = db.records.find({
        "labels": ["SESSION"],
        "limit": 3
    })
    sessions = result.data if hasattr(result, 'data') else result

    for session in sessions:
        session_title = session.data.get('title', 'Untitled')

        # Get the last 3 messages (context window)
        messages_result = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "SESSION": {
                    "$relation": {"type": "CONTAINS", "direction": "in"},
                    "title": session_title
                }
            },
            "orderBy": {"turn": "desc"},
            "limit": 3
        })
        messages = messages_result.data if hasattr(messages_result, 'data') else messages_result

        # Reverse to show in chronological order
        messages = list(reversed(messages))

        print(f"\n  📚 Context Window for: {session_title}")
        print("-" * 50)
        for msg in messages:
            print(f"  [Turn {msg.data.get('turn', '?')}] {msg.data.get('content', '')[:65]}...")


# =============================================================================
# 4. CONVERSATION TRAVERSAL: FOLLOW THE CHAIN
# =============================================================================
def traverse_conversation():
    print_section("4. Conversation Traversal (Following Message Chains)")

    # Get a session to start from
    result = db.records.find({
        "labels": ["SESSION"],
        "limit": 1
    })
    sessions = result.data if hasattr(result, 'data') else result

    if not sessions:
        print("\n  No sessions found. Run seed.py first.")
        return

    session = sessions[0]
    print(f"\n  Starting from session: {session.data.get('title', 'Untitled')}")

    # Find first message in this session (turn 1)
    first_msg_result = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "SESSION": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "title": session.data.get('title')
            },
            "turn": 1
        },
        "limit": 1
    })
    first_msgs = first_msg_result.data if hasattr(first_msg_result, 'data') else first_msg_result

    if not first_msgs:
        print("  No messages found in session.")
        return

    current_msg = first_msgs[0]
    print(f"\n  Starting message (Turn 1):")
    print(f"  " + current_msg.data.get('content', '')[:70] + "...")

    # Follow the FOLLOWS chain (simulate traversal)
    print("\n  Following message chain via FOLLOWS relationships:")
    print("-" * 50)

    depth = 0
    max_depth = 5
    visited = set()

    while depth < max_depth:
        # Find messages that follow this one
        next_result = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "MESSAGE": {
                    "$relation": {"type": "FOLLOWS", "direction": "in"}
                }
            }
        })
        all_next = next_result.data if hasattr(next_result, 'data') else next_result

        # Filter for messages that follow current
        following = [m for m in all_next if current_msg.id in [r.id for r in getattr(current_msg, '_outgoing', [])]]

        # Alternative: Get directly via relationship pattern
        # For simplicity, we'll find the next message by turn number
        current_turn = current_msg.data.get('turn', 0)

        next_turn_result = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "SESSION": {
                    "$relation": {"type": "CONTAINS", "direction": "in"},
                    "title": session.data.get('title')
                },
                "turn": current_turn + 1
            },
            "limit": 1
        })
        next_msgs = next_turn_result.data if hasattr(next_turn_result, 'data') else next_turn_result

        if not next_msgs:
            break

        current_msg = next_msgs[0]
        depth += 1
        role_icon = "👤" if current_msg.data.get("role") == "user" else "🤖"
        content = current_msg.data.get('content', '')[:60]
        print(f"\n  → Turn {current_msg.data.get('turn', '?')}: {role_icon} {content}...")


# =============================================================================
# 5. AUTHOR STATISTICS
# =============================================================================
def show_author_stats():
    print_section("5. Author Statistics (Messages per Participant)")

    # Get all participants
    result = db.records.find({
        "labels": ["PARTICIPANT"]
    })
    participants = result.data if hasattr(result, 'data') else result

    print("\n  Message counts by author:\n")
    for participant in participants:
        name = participant.data.get('name', 'Unknown')
        role = participant.data.get('role', 'unknown')

        # Count authored messages
        msgs_result = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "PARTICIPANT": {
                    "$relation": {"type": "AUTHORED", "direction": "out"},
                    "name": name
                }
            }
        })
        messages = msgs_result.data if hasattr(msgs_result, 'data') else msgs_result

        icon = "👤" if role == "customer" else "🤖"
        print(f"  {icon} {name} ({role}): {len(messages)} messages")


# =============================================================================
# 6. CREATE NEW SESSION AND MESSAGE
# =============================================================================
def create_new_conversation():
    print_section("6. Creating a New Conversation")

    # Create a new session with a transaction
    print("\n  Creating new session with atomic transaction...")

    with db.transactions.begin() as tx:
        # Create session
        new_session = db.records.create(
            label="SESSION",
            data={
                "session_id": f"new-session-{int(time.time())}",
                "title": "Demo: New conversation created via SDK",
                "status": "active",
                "channel": "demo",
                "priority": "medium",
                "created_at": datetime.now().isoformat(),
            },
            transaction=tx
        )
        print(f"  ✓ Created session: {new_session.id}")

        # Create participant
        new_participant = db.records.create(
            label="PARTICIPANT",
            data={
                "participant_id": "demo-user-001",
                "name": "Demo User",
                "role": "customer",
            },
            transaction=tx
        )
        print(f"  ✓ Created participant: {new_participant.id}")

        # Create messages
        messages = [
            {"turn": 1, "content": "Hello, this is a demo message created via the RushDB SDK.", "role": "user", "sentiment": "neutral"},
            {"turn": 2, "content": "Welcome! This demonstrates how transactions ensure atomic graph creation.", "role": "agent", "sentiment": "positive"},
            {"turn": 3, "content": "Everything was created in a single transaction, ensuring data consistency.", "role": "agent", "sentiment": "positive"},
        ]

        prev_msg = None
        for msg_data in messages:
            message = db.records.create(
                label="MESSAGE",
                data=msg_data,
                transaction=tx
            )

            # Link to session
            db.records.attach(
                source=new_session,
                target=message,
                options={"type": "CONTAINS"},
                transaction=tx
            )

            # Link to author
            db.records.attach(
                source=new_participant,
                target=message,
                options={"type": "AUTHORED"},
                transaction=tx
            )

            # Link to previous message
            if prev_msg:
                db.records.attach(
                    source=prev_msg,
                    target=message,
                    options={"type": "FOLLOWS"},
                    transaction=tx
                )

            prev_msg = message
            print(f"  ✓ Created message (Turn {msg_data['turn']})")

        # Note: tx.commit() is handled automatically by context manager
        print("\n  ✓ Transaction committed — all records created atomically!")


# =============================================================================
# 7. SEMANTIC SEARCH (if vector index exists)
# =============================================================================
def search_conversations():
    print_section("7. Semantic Search Across Conversations")

    # Check for existing vector index on MESSAGE.content
    indexes = db.ai.indexes.find()
    index_list = indexes.data if hasattr(indexes, 'data') else indexes

    message_index = None
    for idx in index_list:
        if idx.get('label') == 'MESSAGE' and idx.get('propertyName') == 'content':
            message_index = idx
            break

    if not message_index:
        print("\n  No vector index found on MESSAGE.content.")
        print("  Creating index for semantic search demonstration...")
        print("  (In production, this would be created during setup)\n")

        # Create an external index for demonstration
        # Note: In production, you would use a managed index or pre-compute embeddings
        try:
            db.ai.indexes.create({
                "label": "MESSAGE",
                "propertyName": "content",
                "sourceType": "external",
                "dimensions": 768,
                "similarityFunction": "cosine"
            })
            print("  ✓ Index created. Note: vectors must be supplied externally for full search.")
        except Exception as e:
            print(f"  Note: {str(e)[:80]}...")

        print("\n  For full semantic search, you would need to:")
        print("  1. Generate embeddings for message content using your ML pipeline")
        print("  2. Upsert vectors using db.ai.indexes.upsert_vectors()")
        print("  3. Query using db.ai.search()")
        return

    # Perform semantic search
    print("\n  Searching for conversations about pricing...")
    try:
        results = db.ai.search({
            "propertyName": "content",
            "query": "pricing cost subscription",
            "labels": ["MESSAGE"],
            "limit": 5
        })

        print(f"\n  Found {len(results.data) if hasattr(results, 'data') else len(results)} relevant messages:\n")

        for result in (results.data if hasattr(results, 'data') else results):
            score = getattr(result, 'score', None) or result.data.get('__score', 0)
            content = result.data.get('content', '')[:80]
            turn = result.data.get('turn', '?')
            role = result.data.get('role', 'unknown')
            print(f"  [Score: {score:.3f}] Turn {turn} ({role})")
            print(f"     {content}...")
            print()

    except Exception as e:
        print(f"\n  Search note: {str(e)[:100]}...")
        print("  (This is expected if vectors haven't been populated)")


# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    print("\n" + "=" * 60)
    print("  RushDB Multi-Turn Conversation Tutorial")
    print("  Session Context Stores & Connected Subgraphs")
    print("=" * 60)

    # Check if data exists
    result = db.records.find({
        "labels": ["SESSION"],
        "limit": 1
    })
    sessions = result.data if hasattr(result, 'data') else result

    if not sessions:
        print("\n⚠ No demo data found!")
        print("  Please run 'python seed.py' first to create sample conversations.\n")
        return

    print(f"\n✓ Found {len(sessions)} existing sessions to demonstrate with.")

    # Run all demonstrations
    list_sessions()
    show_message_chains()
    show_context_windows()
    traverse_conversation()
    show_author_stats()
    create_new_conversation()
    search_conversations()

    print_section("Summary")
    print("""
  This tutorial demonstrated RushDB's property graph model for conversations:

  ✓ Sessions as root nodes with metadata
  ✓ Messages linked to sessions via CONTAINS relationships
  ✓ Message chains linked via FOLLOWS relationships
  ✓ Participants linked via AUTHORED relationships
  ✓ Transactions for atomic subgraph creation
  ✓ Semantic search readiness for conversation discovery

  Key benefits of this graph model:
  • Natural representation of conversation structure
  • Efficient traversal via typed relationships
  • Flexible queries across sessions and participants
  • Schema-free: add metadata without migrations

  Next steps:
  → Explore relationship filtering in queries
  → Add vector embeddings for semantic search
  → Implement context windows for LLM prompts
  → Build conversation analytics dashboards
  """)


if __name__ == "__main__":
    main()
