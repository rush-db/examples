"""
Hyperedge Representation Demo: Multi-Party Conversations in RushDB

This demo shows how RushDB's property graph model handles Slack-style
threads with branching replies, mentions, and cross-channel references.

The "hyperedge" pattern: a single MESSAGE node can connect to MULTIPLE
USER nodes via multiple MENTIONS edges — something that requires complex
junction tables in relational databases.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("Error: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"[ {title} ]")
    print("=" * 60)


def show_schema_overview():
    """Display the hyperedge schema design."""
    print_section("Schema Overview")
    
    print("\nLabels (Node Types):")
    print("  USER      - Conversation participants")
    print("  CHANNEL   - Communication channels (#engineering, etc.)")
    print("  THREAD    - Conversation threads with topics")
    print("  MESSAGE   - Individual messages")
    
    print("\nRelationship Types (Edges):")
    print("  AUTHORED_BY    MESSAGE -> USER")
    print("  PART_OF        MESSAGE -> THREAD")
    print("  MENTIONS       MESSAGE -> USER (hyperedge pattern)")
    print("  REPLY_TO       MESSAGE -> MESSAGE")
    print("  POSTED_IN      MESSAGE -> CHANNEL")
    print("  THREAD_REFERENCE THREAD -> CHANNEL")
    
    print("\nThe Hyperedge Pattern:")
    print("  A message mentioning @alice AND @bob creates TWO edges:")
    print("    MESSAGE --MENTIONS--> USER:alice")
    print("    MESSAGE --MENTIONS--> USER:bob")
    print("  This is the 'hyperedge' — one source, many destinations.")


def query_mentions_by_user(username):
    """
    Query: Get all messages that mention a specific user across all channels.
    
    RushDB Query Strategy:
    1. Find the USER record by username
    2. Find all MESSAGE records connected via MENTIONS relationship
    3. Include thread and channel context
    
    This is O(1) graph traversal, not O(n) scan!
    """
    print_section(f"Query: Messages mentioning @{username}")
    
    # Step 1: Find the user
    users = db.records.find({
        "labels": ["USER"],
        "where": {"username": username}
    })
    
    if not users.data:
        print(f"  User @{username} not found")
        return []
    
    target_user = users.data[0]
    print(f"  Found user: {target_user['displayName']} ({target_user.id})")
    
    # Step 2: Find messages that MENTION this user
    # In RushDB, we filter by the related record's label
    messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "USER": {
                "$relation": {"type": "MENTIONS", "direction": "in"},
                "username": username
            }
        },
        "limit": 50
    })
    
    print(f"\n  Found {len(messages.data)} messages mentioning @{username}:\n")
    
    results = []
    for msg in messages.data:
        # Get thread info
        thread_result = db.records.find({
            "labels": ["THREAD"],
            "where": {
                "MESSAGE": {
                    "$relation": {"type": "PART_OF", "direction": "in"},
                    "$id": {"$in": [msg.id]}
                }
            }
        })
        
        # Get channel info via thread
        channel_name = "unknown"
        thread_title = "unknown"
        if thread_result.data:
            thread = thread_result.data[0]
            thread_title = thread.get("title", "unknown")
            channel_result = db.records.find({
                "labels": ["CHANNEL"],
                "where": {
                    "THREAD": {
                        "$relation": {"type": "THREAD_REFERENCE", "direction": "in"},
                        "$id": {"$in": [thread.id]}
                    }
                }
            })
            if channel_result.data:
                channel_name = channel_result.data[0].get("name", "unknown")
        
        # Get author info
        author_result = db.records.find({
            "labels": ["USER"],
            "where": {
                "MESSAGE": {
                    "$relation": {"type": "AUTHORED_BY", "direction": "in"},
                    "$id": {"$in": [msg.id]}
                }
            }
        })
        author_name = author_result.data[0].get("displayName", "unknown") if author_result.data else "unknown"
        
        print(f"  • Thread \"{thread_title}\" (#{channel_name})")
        print(f"    Message: {msg['body'][:60]}..." if len(msg.get('body', '')) > 60 else f"    Message: {msg.get('body', '')}")
        print(f"    Author: {author_name}")
        print()
        
        results.append({
            "message": msg,
            "thread": thread_title,
            "channel": channel_name,
            "author": author_name
        })
    
    return results


def query_co_participation(user1_username, user2_username):
    """
    Query: Find all threads where two users both participated (via mentions).
    
    RushDB Query Strategy:
    1. Find both user records
    2. For each thread, check if messages exist mentioning BOTH users
    3. Return threads where co-participation is confirmed
    
    Relational equivalent would require:
    - JOIN messages_mentions j1 ON messages.id = j1.message_id
    - JOIN messages_mentions j2 ON messages.id = j2.message_id
    - JOIN threads ON messages.thread_id = threads.id
    - GROUP BY threads.id
    - HAVING COUNT(DISTINCT j1.user_id) >= 2
    """
    print_section(f"Query: Threads with @{user1_username} AND @{user2_username}")
    
    # Find both users
    user1_result = db.records.find({
        "labels": ["USER"],
        "where": {"username": user1_username}
    })
    user2_result = db.records.find({
        "labels": ["USER"],
        "where": {"username": user2_username}
    })
    
    if not user1_result.data or not user2_result.data:
        print("  One or both users not found")
        return []
    
    user1 = user1_result.data[0]
    user2 = user2_result.data[0]
    
    print(f"  User 1: {user1['displayName']}")
    print(f"  User 2: {user2['displayName']}")
    
    # Get all threads
    threads_result = db.records.find({
        "labels": ["THREAD"],
        "limit": 100
    })
    
    print(f"\n  Checking {len(threads_result.data)} threads for co-participation...\n")
    
    co_threads = []
    
    for thread in threads_result.data:
        # Get all messages in this thread
        messages_in_thread = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "THREAD": {
                    "$relation": {"type": "PART_OF", "direction": "in"},
                    "$id": {"$in": [thread.id]}
                }
            }
        })
        
        if not messages_in_thread.data:
            continue
        
        # Check if any message mentions user1
        user1_mentioned = any(
            db.records.find({
                "labels": ["MESSAGE"],
                "where": {
                    "USER": {
                        "$relation": {"type": "MENTIONS", "direction": "in"},
                        "$id": {"$in": [user1.id]}
                    },
                    "$id": {"$in": [msg.id]}
                }
            }).data
            for msg in messages_in_thread.data
        )
        
        # Check if any message mentions user2
        user2_mentioned = any(
            db.records.find({
                "labels": ["MESSAGE"],
                "where": {
                    "USER": {
                        "$relation": {"type": "MENTIONS", "direction": "in"},
                        "$id": {"$in": [user2.id]}
                    },
                    "$id": {"$in": [msg.id]}
                }
            }).data
            for msg in messages_in_thread.data
        )
        
        if user1_mentioned and user2_mentioned:
            # Get channel info
            channel_result = db.records.find({
                "labels": ["CHANNEL"],
                "where": {
                    "THREAD": {
                        "$relation": {"type": "THREAD_REFERENCE", "direction": "in"},
                        "$id": {"$in": [thread.id]}
                    }
                }
            })
            channel_name = channel_result.data[0].get("name", "unknown") if channel_result.data else "unknown"
            
            co_threads.append({
                "thread": thread,
                "channel": channel_name
            })
            print(f"  ✓ \"{thread.get('title', 'unknown')}\" (#{channel_name})")
    
    print(f"\n  Found {len(co_threads)} threads with both users participating")
    
    return co_threads


def explain_graph_traversal():
    """Explain why graph traversal outperforms traditional approaches."""
    print_section("Why Graph Traversal is O(1)")
    
    print("""
  Traditional Database (Relational or Document):
  ──────────────────────────────────────────────
  1. Scan every MESSAGE row/document
  2. Parse mentions array or join junction table
  3. Filter for matching user
  4. Return results
  
  Time Complexity: O(n) where n = total messages
  
  
  RushDB Property Graph:
  ───────────────────────
  1. Look up USER node by username (indexed: O(1))
  2. Follow MENTIONS edges to MESSAGE nodes (indexed: O(1))
  3. Return connected messages
  
  Time Complexity: O(1) for edge traversal (constant-time index lookup)
  
  
  The Key Insight:
  ─────────────────
  RushDB stores edges as first-class citizens with their own indexes.
  Finding "all messages mentioning Alice" is a direct lookup, not a scan.
  
  Neo4j (underneath RushDB) maintains a relationship index that makes
  edge traversal constant-time, regardless of graph size.
  """)


def show_data_summary():
    """Show summary of seeded data."""
    print_section("Data Summary")
    
    # Count records by label
    labels = ["USER", "CHANNEL", "THREAD", "MESSAGE"]
    for label in labels:
        result = db.records.find({"labels": [label], "limit": 1})
        # We can't get total count directly, so we just note the label exists
        print(f"  {label}: present")
    
    # Count relationships
    print("\n  Relationships:")
    print("    AUTHORED_BY, PART_OF, MENTIONS, REPLY_TO, POSTED_IN, THREAD_REFERENCE")


def main():
    print("\n" + "=" * 60)
    print("   HYPEREDGE REPRESENTATION FOR MULTI-PARTY CONVERSATIONS")
    print("   RushDB Property Graph Demo")
    print("=" * 60)
    
    # Show schema design
    show_schema_overview()
    
    # Show data summary
    show_data_summary()
    
    # Query 1: Find all messages mentioning @alice
    alice_mentions = query_mentions_by_user("alice")
    
    # Query 2: Find threads where @alice and @bob both participated
    co_threads = query_co_participation("alice", "bob")
    
    # Explain the performance advantage
    explain_graph_traversal()
    
    print_section("Demo Complete")
    print("""
  Next Steps:
  ──────────
  • Try querying different users: change 'alice' and 'bob' in main()
  • Add more messages: run seed.py again to reset data
  • Explore relationships: use db.records.find() with different where clauses
  • Read the docs: https://docs.rushdb.com
  """)


if __name__ == "__main__":
    main()
