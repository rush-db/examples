"""
Building Conversation Memory Chains with Time-Decay Relationship Weights
============================================================================

This tutorial demonstrates how to build intelligent conversation memory 
systems using RushDB's property graph model.

Key concepts:
1. Conversation chain modeling as directed graphs
2. Time-decay weighting for relationship strength
3. Context retrieval using weighted relationship traversal
4. Memory prioritization based on temporal relevance

Run: python main.py
Requires: RUSHDB_API_TOKEN in environment or .env file
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB


# ==============================================================================
# Time-Decay Utilities
# ==============================================================================

def calculate_decay_weight(timestamp: datetime, half_life_days: float = 7, base: float = 2) -> float:
    """
    Calculate relationship weight based on exponential time decay.
    
    Formula: weight = base^(-days_since / half_life)
    
    Args:
        timestamp: datetime of the relationship/event
        half_life_days: days until weight is 50% (default: 7 days)
        base: decay base - higher = faster decay (default: 2)
    
    Returns:
        float: weight between 0 and 1, where 1 = now
    
    Example:
        weight = 0.5  (50%) after 7 days with half_life=7
        weight = 0.25 after 14 days with half_life=7
    """
    now = datetime.utcnow()
    days_since = (now - timestamp).total_seconds() / (24 * 3600)
    
    if days_since < 0:
        # Future timestamp - give maximum weight
        return 1.0
    
    return base ** (-days_since / half_life_days)



def create_decay_table(half_life_days: float = 7, max_days: int = 14) -> list:
    """Generate a reference table of decay weights by day."""
    now = datetime.utcnow()
    table = []
    
    for day in range(max_days + 1):
        timestamp = now - timedelta(days=day)
        weight = calculate_decay_weight(timestamp, half_life_days)
        table.append({
            "day": day,
            "weight": round(weight, 4),
            "percentage": round(weight * 100, 1)
        })
    
    return table


# ==============================================================================
# RushDB Operations
# ==============================================================================

def initialize_rushdb():
    """Initialize RushDB client from environment."""
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("Error: RUSHDB_API_TOKEN not found in environment")
        print("Please add your API key to .env or export RUSHDB_API_TOKEN")
        sys.exit(1)
    
    api_url = os.getenv("RUSHDB_URL")
    db = RushDB(api_token, url=api_url) if api_url else RushDB(api_token)
    
    print(f"[+] Connected to RushDB")
    return db


def create_sample_conversation(db: RushDB) -> tuple:
    """
    Create a sample conversation with linked messages demonstrating
    the conversation chain concept.
    """
    print("\n[1] Creating sample conversation history...")
    
    # Create conversation
    conversation = db.records.create(
        label="CONVERSATION",
        data={
            "title": "API Architecture Review",
            "channel": "engineering",
            "started_at": (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z",
            "participants": ["alice@example.com", "bob@example.com", "charlie@example.com"]
        }
    )
    print(f'    ✓ Created conversation "{conversation.data["title"]}"')
    
    # Create sequential messages
    messages_data = [
        ("What's the current status of the API gateway migration?", "alice@example.com", 5),
        ("Gateway is running smoothly in staging. Planning production cutover for Friday.", "bob@example.com", 4),
        ("Have we validated the SSL certificate renewal process?", "charlie@example.com", 3),
        ("Yes, certificates are validated and installed on all instances.", "bob@example.com", 2),
        ("Great! What's the rollback plan if issues arise during cutover?", "alice@example.com", 1),
        ("Full rollback documented - can revert in under 5 minutes if needed.", "bob@example.com", 0),
    ]
    
    messages = []
    previous_message = None
    
    for content, author, days_ago in messages_data:
        timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=random_hour())
        
        message = db.records.create(
            label="MESSAGE",
            data={
                "content": content,
                "author": author,
                "timestamp": timestamp.isoformat() + "Z",
                "type": "text"
            }
        )
        messages.append(message)
        
        # Link to conversation
        db.records.attach(
            source=message,
            target=conversation,
            options={"type": "PART_OF"}
        )
        
        # Link to previous message (conversation chain)
        if previous_message:
            db.records.attach(
                source=message,
                target=previous_message,
                options={"type": "REPLY_TO"}
            )
        
        previous_message = message
    
    print(f'    ✓ Created {len(messages)} messages in conversation')
    
    return conversation, messages


def random_hour() -> int:
    """Generate a random hour for message timestamps."""
    import random
    return random.randint(9, 17)


def assign_time_decay_weights(db: RushDB, messages: list) -> list:
    """
    Assign time-decay weighted relationships between messages.
    
    Newer messages serve as context for current discussion.
    Older relevant messages have lower weights based on time elapsed.
    """
    print("\n[2] Calculating time-decay weights for context links...")
    
    now = datetime.utcnow()
    decay_table = create_decay_table(half_life_days=7, max_days=7)
    
    print("    Context Link weights (oldest → newest):")
    for entry in reversed(decay_table):
        print(f'      Day {entry["day"]:2d}: weight = {entry["weight"]:.3f} ({entry["percentage"]:.1f}%)')
    
    # Link recent messages as context with time-decay weights
    current_message = messages[-1]  # Most recent
    context_links = []
    
    for i, past_message in enumerate(messages[:-1]):
        past_time = datetime.fromisoformat(past_message.data["timestamp"].replace("Z", ""))
        weight = calculate_decay_weight(past_time, half_life_days=7)
        
        # Create contextually-linked relationship with weight
        db.records.attach(
            source=current_message,
            target=past_message,
            options={
                "type": "CONTEXTUALLY_LINKED",
                "properties": {
                    "weight": round(weight, 4),
                    "decay_half_life_days": 7,
                    "decay_base": 2,
                    "calculated_at": now.isoformat() + "Z"
                }
            }
        )
        
        context_links.append({
            "message": past_message,
            "weight": weight,
            "content": past_message.data["content"][:50] + "..."
        })
    
    print(f'    ✓ Created {len(context_links)} context links with time-decay weights')
    
    return context_links


def query_weighted_context(db: RushDB, conversation) -> list:
    """
    Query conversation history and retrieve messages with weighted context.
    
    This demonstrates how to fetch relevant past context, sorted by
    time-decay weight to prioritize recent relevant information.
    """
    print("\n[3] Querying weighted context for new message...")
    
    # Find messages with CONTEXTUALLY_LINKED relationships
    contexts = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "CONVERSATION": {
                "$relation": {"type": "PART_OF", "direction": "in"},
                "title": "API Architecture Review"
            }
        },
        "limit": 10
    })
    
    # Get the most recent message
    messages = sorted(contexts.data, key=lambda m: m.get("timestamp", ""), reverse=True)
    
    if not messages:
        print("    [!] No messages found")
        return []
    
    # Filter to contextually linked ones with weights
    print("    Context Relevance Scores:")
    results = []
    
    for msg in messages[:5]:
        timestamp = datetime.fromisoformat(msg.get("timestamp", "").replace("Z", ""))
        weight = calculate_decay_weight(timestamp, half_life_days=7)
        days_elapsed = (datetime.utcnow() - timestamp).total_seconds() / (24 * 3600)
        
        print(f'    [{weight:.2f}] "{msg.get("content", "")[:45]}..." ({int(days_elapsed)} days ago)')
        results.append({"message": msg, "weight": weight})
    
    return results


def query_user_conversation_history(db: RushDB, user_email: str) -> dict:
    """
    Query all conversations a user has participated in, with message counts.
    
    Demonstrates relationship traversal with filtering by properties.
    """
    print(f"\n[4] Querying conversation history for {user_email}...")
    
    # Find all messages by this user
    user_messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "author": user_email
        },
        "limit": 100
    })
    
    if not user_messages.data:
        print(f"    [!] No messages found for {user_email}")
        return {"user": user_email, "messages": 0, "conversations": []}
    
    # Extract unique conversation IDs
    conversation_ids = set()
    message_count = len(user_messages.data)
    
    for msg in user_messages.data:
        # Find which conversation this message belongs to
        convs = db.records.find({
            "labels": ["CONVERSATION"],
            "where": {
                "MESSAGE": {
                    "$relation": {"type": "PART_OF", "direction": "out"},
                    "author": user_email
                }
            },
            "limit": 10
        })
        for c in convs.data:
            conversation_ids.add(c.get("__id"))
    
    print(f"    Found {message_count} messages from {user_email} across {len(conversation_ids)} conversations")
    
    return {
        "user": user_email,
        "messages": message_count,
        "conversations": len(conversation_ids)
    }


def demonstrate_graph_traversal(db: RushDB) -> None:
    """
    Demonstrate complex graph traversal with time-decay weights.
    
    This shows how to:
    1. Start from a recent message
    2. Traverse CONTEXTUALLY_LINKED relationships
    3. Collect weighted context with decaying relevance
    4. Build a prioritized context stack
    """
    print("\n[5] Demonstrating weighted graph traversal...")
    
    # Find a conversation with context links
    conversations = db.records.find({
        "labels": ["CONVERSATION"],
        "where": {
            "channel": "engineering"
        },
        "limit": 5
    })
    
    if not conversations.data:
        print("    [!] No engineering conversations found")
        return
    
    # Get messages from first conversation
    conv = conversations.data[0]
    messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "CONVERSATION": {
                "$relation": {"type": "PART_OF", "direction": "in"},
                "title": conv.get("title")
            }
        },
        "orderBy": {"timestamp": "asc"}
    })
    
    if not messages.data:
        print("    [!] No messages in conversation")
        return
    
    print(f'    Building context stack from "{conv.get("title")}"')
    
    # Build weighted context stack
    context_stack = []
    now = datetime.utcnow()
    
    for msg in messages.data:
        timestamp = datetime.fromisoformat(msg.get("timestamp", "").replace("Z", ""))
        weight = calculate_decay_weight(timestamp, half_life_days=7)
        days_elapsed = (now - timestamp).total_seconds() / (24 * 3600)
        
        if weight >= 0.3:  # Only include somewhat relevant context
            context_stack.append({
                "content": msg.get("content", ""),
                "author": msg.get("author", ""),
                "weight": weight,
                "days_ago": round(days_elapsed, 1),
                "priority": "HIGH" if weight > 0.7 else "MEDIUM" if weight > 0.4 else "LOW"
            })
    
    print(f"    Context stack: {len(context_stack)} relevant messages")
    print("    Priority breakdown:")
    
    priorities = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for ctx in context_stack:
        priorities[ctx["priority"]].append(ctx)
    
    for priority in ["HIGH", "MEDIUM", "LOW"]:
        count = len(priorities[priority])
        print(f"      {priority}: {count} messages")
    
    # Show top priority message
    if context_stack:
        top = max(context_stack, key=lambda x: x["weight"])
        print(f'\n    Top context: "{top["content"][:60]}..."')
        print(f'    Weight: {top["weight"]:.2f} ({top["days_ago"]} days ago)')



# ==============================================================================
# Main Execution
# ==============================================================================

def main():
    """"Main demonstration function."""
    print("=" * 60)
    print("BUILDING CONVERSATION MEMORY CHAINS WITH TIME-DECAY")
    print("=" * 60)
    
    # Initialize RushDB
    db = initialize_rushdb()
    
    # Create sample conversation
    conversation, messages = create_sample_conversation(db)
    
    # Assign time-decay weighted relationships
    context_links = assign_time_decay_weights(db, messages)
    
    # Query weighted context
    query_weighted_context(db, conversation)
    
    # Query user history
    query_user_conversation_history(db, "alice@example.com")
    
    # Demonstrate graph traversal
    demonstrate_graph_traversal(db)
    
    print("\n" + "=" * 60)
    print("SUCCESS - Time-decay conversation memory chains demonstrated!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  • Relationships can carry weighted properties")
    print("  • Time-decay creates automatic relevance prioritization")
    print("  • Graph traversal preserves context across conversation history")
    print("  • RushDB's property graph model excels at weighted relationship queries")


if __name__ == "__main__":
    main()
