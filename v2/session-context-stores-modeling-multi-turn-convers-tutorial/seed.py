#!/usr/bin/env python3
"""
Seed script for multi-turn conversation tutorial.
Generates realistic conversation data across multiple sessions and participants.

This script is idempotent — it checks for existing data before creating new records.
"""

import os
import random
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

# Demo data: Sessions with realistic conversation flows
SEED_DATA = {
    "sessions": [
        {
            "id": "demo-session-1",
            "title": "Product pricing inquiry",
            "status": "resolved",
            "channel": "support_chat",
            "priority": "high",
        },
        {
            "id": "demo-session-2",
            "title": "Technical integration question",
            "status": "in_progress",
            "channel": "developer_forum",
            "priority": "medium",
        },
        {
            "id": "demo-session-3",
            "title": "Feature request discussion",
            "status": "closed",
            "channel": "feedback_portal",
            "priority": "low",
        },
    ],
    "participants": [
        {"id": "user-alice", "name": "Alice Chen", "role": "customer", "company": "Acme Corp"},
        {"id": "agent-bob", "name": "Bob Support", "role": "support_agent", "department": "Customer Success"},
        {"id": "user-carol", "name": "Carol Martinez", "role": "customer", "company": "TechStart Inc"},
        {"id": "agent-dave", "name": "Dave Engineering", "role": "support_agent", "department": "Engineering"},
        {"id": "user-eve", "name": "Eve Johnson", "role": "customer", "company": "GlobalTech"},
        {"id": "agent-frank", "name": "Frank Technical", "role": "support_agent", "department": "Engineering"},
    ],
    "messages": [
        # Session 1: Product pricing inquiry
        {
            "session_id": "demo-session-1",
            "turn": 1,
            "author_id": "user-alice",
            "role": "user",
            "content": "Hi, I'm interested in your enterprise plan. Can you walk me through the pricing structure? We have about 50 users.",
            "sentiment": "interested",
        },
        {
            "session_id": "demo-session-1",
            "turn": 2,
            "author_id": "agent-bob",
            "role": "agent",
            "content": "Great question, Alice! For 50 users on the enterprise plan, we offer tiered pricing. The base cost is $499/month, with additional users at $8/user/month. That's $899/month total for 50 users. Would you like me to break down what's included in the enterprise tier?",
            "sentiment": "helpful",
        },
        {
            "session_id": "demo-session-1",
            "turn": 3,
            "author_id": "user-alice",
            "role": "user",
            "content": "Yes please, that would be helpful. Also, do you offer annual billing with discounts?",
            "sentiment": "engaged",
        },
        {
            "session_id": "demo-session-1",
            "turn": 4,
            "author_id": "agent-bob",
            "role": "agent",
            "content": "Absolutely! The enterprise tier includes: dedicated support, advanced analytics, SSO integration, unlimited projects, and priority SLA. For annual billing, we offer a 20% discount, bringing your effective cost to $719/month. I can send you a detailed quote if you'd like.",
            "sentiment": "helpful",
        },
        {
            "session_id": "demo-session-1",
            "turn": 5,
            "author_id": "user-alice",
            "role": "user",
            "content": "That sounds perfect. Please send the quote to alice@acmecorp.com and I'll review it with my team.",
            "sentiment": "positive",
        },
        # Session 2: Technical integration question
        {
            "session_id": "demo-session-2",
            "turn": 1,
            "author_id": "user-carol",
            "role": "user",
            "content": "I'm trying to integrate your SDK into our Node.js application. I've followed the documentation but I'm getting authentication errors. Here's my setup code:",
            "sentiment": "frustrated",
        },
        {
            "session_id": "demo-session-2",
            "turn": 2,
            "author_id": "agent-dave",
            "role": "agent",
            "content": "Thanks for reaching out, Carol. The authentication error is typically caused by one of three issues: expired API key, incorrect environment variable, or missing CORS configuration. Can you share the error message you're seeing and which SDK version you're using?",
            "sentiment": "helpful",
        },
        {
            "session_id": "demo-session-2",
            "turn": 3,
            "author_id": "user-carol",
            "role": "user",
            "content": "I'm using SDK v2.3.1 and the error is: 'Authentication failed: Invalid token format'. I've verified the API key is correct.",
            "sentiment": "concerned",
        },
        {
            "session_id": "demo-session-2",
            "turn": 4,
            "author_id": "agent-dave",
            "role": "agent",
            "content": "Found it! With SDK v2.3.1, we changed the token format from Bearer to direct API key authentication. Update your initialization from 'Authorization: Bearer <token>' to just passing the key directly. Example: `RushDB.init({ apiKey: 'your_key' })`. This was a breaking change in v2.0 that wasn't fully documented.",
            "sentiment": "resolved",
        },
        {
            "session_id": "demo-session-2",
            "turn": 5,
            "author_id": "user-carol",
            "role": "user",
            "content": "That worked! Thank you for the quick fix. It would be great if the migration guide mentioned this explicitly.",
            "sentiment": "grateful",
        },
        {
            "session_id": "demo-session-2",
            "turn": 6,
            "author_id": "agent-dave",
            "role": "agent",
            "content": "I'm glad that resolved your issue, Carol. I've noted your feedback about the migration guide — I'll pass that to our documentation team. Feel free to reach out if you run into anything else during integration.",
            "sentiment": "helpful",
        },
        # Session 3: Feature request discussion
        {
            "session_id": "demo-session-3",
            "turn": 1,
            "author_id": "user-eve",
            "role": "user",
            "content": "I'd like to request a feature for bulk operations. We frequently need to update thousands of records at once and the current API doesn't support batching.",
            "sentiment": "neutral",
        },
        {
            "session_id": "demo-session-3",
            "turn": 2,
            "author_id": "agent-frank",
            "role": "agent",
            "content": "Thank you for the feature request, Eve. Bulk operations is a frequently requested feature. Can you tell me more about your use case? Specifically, what operations do you need to perform on these bulk records — create, update, or delete?",
            "sentiment": "interested",
        },
        {
            "session_id": "demo-session-3",
            "turn": 3,
            "author_id": "user-eve",
            "content": "Mainly update and delete. We're migrating data from an old system and need to sync about 10,000 records daily. Currently we have to make individual API calls which is slow.",
            "sentiment": "neutral",
        },
        {
            "session_id": "demo-session-3",
            "turn": 4,
            "author_id": "agent-frank",
            "role": "agent",
            "content": "I understand the pain point. We're actually working on a batch API that should launch in Q2. It will support up to 1,000 operations per request with transactional guarantees. I'll add your use case to our beta testing list — would you be interested in early access?",
            "sentiment": "positive",
        },
        {
            "session_id": "demo-session-3",
            "turn": 5,
            "author_id": "user-eve",
            "role": "user",
            "content": "Absolutely, we'd love to participate in the beta! Please notify me when it's available.",
            "sentiment": "positive",
        },
        {
            "session_id": "demo-session-3",
            "turn": 6,
            "author_id": "agent-frank",
            "role": "agent",
            "content": "Done! I've added eve@globaltech.com to our beta notification list. I'll follow up with more details as we get closer to release. Is there anything else regarding bulk operations you'd like to discuss?",
            "sentiment": "helpful",
        },
        {
            "session_id": "demo-session-3",
            "turn": 7,
            "author_id": "user-eve",
            "role": "user",
            "content": "No, that's all for now. Thank you for the quick response!",
            "sentiment": "positive",
        },
    ],
}


def check_existing_data():
    """Check if demo data already exists."""
    result = db.records.find({
        "labels": ["SESSION"],
        "where": {"session_id": {"$in": [s["id"] for s in SEED_DATA["sessions"}]}}
    })
    existing = result.data if hasattr(result, 'data') else result
    return len(existing) > 0


def seed_data():
    """Create the full conversation subgraph."""
    print("\n=== Seeding Multi-Turn Conversation Data ===\n")

    # Check for existing data
    if check_existing_data():
        print("✓ Demo data already exists. Skipping seed.")
        print("  To re-seed, delete existing records first or use a different session_id prefix.")
        return

    # Track created records for relationship linking
    created = {
        "sessions": {},
        "participants": {},
        "messages": {},
    }

    print("Creating sessions...")
    for session_data in SEED_DATA["sessions"]:
        session = db.records.create(
            label="SESSION",
            data={
                "session_id": session_data["id"],
                "title": session_data["title"],
                "status": session_data["status"],
                "channel": session_data["channel"],
                "priority": session_data["priority"],
                "created_at": datetime.now().isoformat(),
            }
        )
        created["sessions"][session_data["id"]] = session
        print(f"  ✓ Session: {session_data['title']}")

    print("\nCreating participants...")
    for participant_data in SEED_DATA["participants"]:
        participant = db.records.create(
            label="PARTICIPANT",
            data={
                "participant_id": participant_data["id"],
                "name": participant_data["name"],
                "role": participant_data["role"],
                "company": participant_data.get("company"),
                "department": participant_data.get("department"),
            }
        )
        created["participants"][participant_data["id"]] = participant
        print(f"  ✓ Participant: {participant_data['name']} ({participant_data['role']})")

    print("\nCreating messages and linking into conversation chains...")
    prev_message = None
    session_message_count = {}

    for i, msg_data in enumerate(SEED_DATA["messages"]):
        # Track turn sequence within session
        session_id = msg_data["session_id"]
        if session_id not in session_message_count:
            session_message_count[session_id] = 0
        session_message_count[session_id] += 1

        # Create the message
        message = db.records.create(
            label="MESSAGE",
            data={
                "content": msg_data["content"],
                "turn": msg_data["turn"],
                "role": msg_data["role"],
                "sentiment": msg_data["sentiment"],
                "timestamp": (datetime.now() - timedelta(minutes=len(SEED_DATA["messages"]) - i)).isoformat(),
            }
        )
        msg_key = f"{session_id}-{msg_data['turn']}"
        created["messages"][msg_key] = message

        # Link to session
        session = created["sessions"][session_id]
        db.records.attach(
            source=session,
            target=message,
            options={"type": "CONTAINS"}
        )

        # Link to author
        author = created["participants"][msg_data["author_id"]]
        db.records.attach(
            source=author,
            target=message,
            options={"type": "AUTHORED"}
        )

        # Link to previous message (FOLLOWS relationship)
        if prev_message and prev_message.data.get("session_id") == session_id:
            db.records.attach(
                source=prev_message,
                target=message,
                options={"type": "FOLLOWS"}
            )
        elif session_message_count[session_id] > 1:
            # Find the previous message in this session
            for check_key, check_msg in created["messages"].items():
                if check_key.startswith(session_id) and check_msg.data.get("turn") == msg_data["turn"] - 1:
                    db.records.attach(
                        source=check_msg,
                        target=message,
                        options={"type": "FOLLOWS"}
                    )
                    break

        prev_message = message

        if (i + 1) % 5 == 0:
            print(f"  ✓ Created {i + 1}/{len(SEED_DATA['messages'])} messages...")

    print(f"\n✓ Seed complete: {len(SEED_DATA['sessions'])} sessions, "
          f"{len(SEED_DATA['participants'])} participants, "
          f"{len(SEED_DATA['messages'])} messages")


if __name__ == "__main__":
    print("=" * 60)
    print("RushDB Multi-Turn Conversation Seeder")
    print("=" * 60)
    seed_data()
    print("\nRun 'python main.py' to see the demo in action!\n")
