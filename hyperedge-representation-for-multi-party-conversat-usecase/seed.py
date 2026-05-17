"""
Seed script for the hyperedge conversation demo.

Creates a realistic multi-channel conversation dataset demonstrating
how RushDB's graph model handles multi-party threads with mentions.

This script is idempotent — safe to run multiple times.
"""

import os
import sys
from datetime import datetime, timedelta
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


def clear_existing_data():
    """Remove all demo records to ensure clean state."""
    print("Clearing existing demo data...")
    
    labels_to_clear = ["MESSAGE", "THREAD", "CHANNEL", "USER"]
    for label in labels_to_clear:
        try:
            result = db.records.delete_many({
                "labels": [label],
                "where": {}
            })
            if result:
                print(f"  Cleared {label} records")
        except Exception as e:
            # Ignore errors from non-existent labels
            pass

    print("  Done clearing data\n")


def seed_users():
    """Create user records for conversation participants."""
    print("Creating users...")
    
    users_data = [
        {
            "username": "alice",
            "displayName": "Alice Chen",
            "email": "alice@example.com",
            "role": "Engineering Lead"
        },
        {
            "username": "bob",
            "displayName": "Bob Martinez",
            "email": "bob@example.com",
            "role": "Backend Developer"
        },
        {
            "username": "charlie",
            "displayName": "Charlie Kim",
            "email": "charlie@example.com",
            "role": "Frontend Developer"
        },
        {
            "username": "diana",
            "displayName": "Diana Patel",
            "email": "diana@example.com",
            "role": "Product Manager"
        },
        {
            "username": "eve",
            "displayName": "Eve Thompson",
            "email": "eve@example.com",
            "role": "DevOps Engineer"
        }
    ]
    
    users = []
    for user_data in users_data:
        user = db.records.create(label="USER", data=user_data)
        users.append(user)
        print(f"  Created user: @{user['username']}")
    
    return {user['username']: user for user in users}


def seed_channels():
    """Create channel records."""
    print("\nCreating channels...")
    
    channels_data = [
        {
            "name": "engineering",
            "description": "Engineering team discussions",
            "isPrivate": False
        },
        {
            "name": "general",
            "description": "Company-wide announcements and general chat",
            "isPrivate": False
        },
        {
            "name": "ops",
            "description": "Operations and infrastructure",
            "isPrivate": False
        }
    ]
    
    channels = []
    for channel_data in channels_data:
        channel = db.records.create(label="CHANNEL", data=channel_data)
        channels.append(channel)
        print(f"  Created channel: #{channel['name']}")
    
    return {ch['name']: ch for ch in channels}


def seed_threads(users, channels):
    """Create thread records."""
    print("\nCreating threads...")
    
    alice = users["alice"]
    diana = users["diana"]
    eve = users["eve"]
    
    threads_data = [
        {
            "title": "Q4 Planning",
            "createdBy": alice.id,
            "channel": "engineering",
            "priority": "high"
        },
        {
            "title": "Sprint Review",
            "createdBy": diana.id,
            "channel": "general",
            "priority": "medium"
        },
        {
            "title": "Deploy Issues",
            "createdBy": eve.id,
            "channel": "ops",
            "priority": "critical"
        },
        {
            "title": "API v2 Migration",
            "createdBy": alice.id,
            "channel": "engineering",
            "priority": "high"
        }
    ]
    
    threads = []
    for thread_data in threads_data:
        channel_name = thread_data.pop("channel")
        thread = db.records.create(label="THREAD", data=thread_data)
        
        # Link thread to channel
        channel = channels[channel_name]
        db.records.attach(
            source=thread,
            target=channel,
            options={"type": "THREAD_REFERENCE", "direction": "out"}
        )
        
        threads.append(thread)
        print(f"  Created thread: \"{thread['title']}\" in #{channel_name}")
    
    return {t['title']: t for t in threads}


def seed_messages(users, channels, threads):
    """Create message records with proper relationships."""
    print("\nCreating messages with relationships...")
    
    alice = users["alice"]
    bob = users["bob"]
    charlie = users["charlie"]
    diana = users["diana"]
    eve = users["eve"]
    
    engineering = channels["engineering"]
    general = channels["general"]
    ops = channels["ops"]
    
    q4_planning = threads["Q4 Planning"]
    sprint_review = threads["Sprint Review"]
    deploy_issues = threads["Deploy Issues"]
    api_migration = threads["API v2 Migration"]
    
    # Message data with author, mentions, and context
    messages_config = [
        # Q4 Planning thread (engineering)
        {
            "body": "Team, let's discuss our Q4 priorities. I think we should focus on the API migration first.",
            "author": alice,
            "thread": q4_planning,
            "channel": engineering,
            "mentions": [],
            "reply_to": None
        },
        {
            "body": "@alice Agreed! The API v2 work is blocking several features. @bob what do you think?",
            "author": diana,
            "thread": q4_planning,
            "channel": engineering,
            "mentions": [alice, bob],
            "reply_to": None
        },
        {
            "body": "I can take point on the backend changes. Should take about 2 weeks.",
            "author": bob,
            "thread": q4_planning,
            "channel": engineering,
            "mentions": [],
            "reply_to": 1
        },
        {
            "body": "Great! @alice can you review the architecture doc when ready?",
            "author": bob,
            "thread": q4_planning,
            "channel": engineering,
            "mentions": [alice],
            "reply_to": 2
        },
        
        # Sprint Review thread (general)
        {
            "body": "Sprint 42 retrospective: We shipped 15 tickets! @alice @bob great work on the performance improvements.",
            "author": diana,
            "thread": sprint_review,
            "channel": general,
            "mentions": [alice, bob],
            "reply_to": None
        },
        {
            "body": "Thanks! The caching layer really helped. @charlie your frontend optimizations were key too.",
            "author": alice,
            "thread": sprint_review,
            "channel": general,
            "mentions": [charlie],
            "reply_to": 4
        },
        
        # Deploy Issues thread (ops)
        {
            "body": "Production deploy is failing. @eve can you take a look?",
            "author": bob,
            "thread": deploy_issues,
            "channel": ops,
            "mentions": [eve],
            "reply_to": None
        },
        {
            "body": "Looking at it now. Seems like a config mismatch in the staging env.",
            "author": eve,
            "thread": deploy_issues,
            "channel": ops,
            "mentions": [],
            "reply_to": 6
        },
        {
            "body": "@alice this is blocking prod deploys. Can you check if the API changes are compatible?",
            "author": eve,
            "thread": deploy_issues,
            "channel": ops,
            "mentions": [alice],
            "reply_to": 7
        },
        
        # API v2 Migration thread (engineering)
        {
            "body": "Starting the API v2 migration work. Initial analysis shows 3 services need updates.",
            "author": alice,
            "thread": api_migration,
            "channel": engineering,
            "mentions": [],
            "reply_to": None
        },
        {
            "body": "I've mapped out the endpoint changes. @bob @charlie let's sync tomorrow.",
            "author": alice,
            "thread": api_migration,
            "channel": engineering,
            "mentions": [bob, charlie],
            "reply_to": 9
        },
        {
            "body": "Works for me! @bob I'll prep the frontend side.",
            "author": charlie,
            "thread": api_migration,
            "channel": engineering,
            "mentions": [bob],
            "reply_to": 10
        }
    ]
    
    created_messages = []
    
    for idx, msg_config in enumerate(messages_config):
        # Create the message
        message = db.records.create(
            label="MESSAGE",
            data={
                "body": msg_config["body"],
                "timestamp": (datetime.now() - timedelta(hours=len(messages_config) - idx)).isoformat(),
                "index": idx
            }
        )
        
        # Link to author (AUTHORED_BY)
        db.records.attach(
            source=message,
            target=msg_config["author"],
            options={"type": "AUTHORED_BY", "direction": "out"}
        )
        
        # Link to thread (PART_OF)
        db.records.attach(
            source=message,
            target=msg_config["thread"],
            options={"type": "PART_OF", "direction": "out"}
        )
        
        # Link to channel (POSTED_IN)
        db.records.attach(
            source=message,
            target=msg_config["channel"],
            options={"type": "POSTED_IN", "direction": "out"}
        )
        
        # Link to mentioned users (MENTIONS) - the hyperedge pattern!
        for mentioned_user in msg_config["mentions"]:
            db.records.attach(
                source=message,
                target=mentioned_user,
                options={"type": "MENTIONS", "direction": "out"}
            )
        
        # Link to parent message if reply (REPLY_TO)
        if msg_config["reply_to"] is not None:
            parent_message = created_messages[msg_config["reply_to"]]
            db.records.attach(
                source=message,
                target=parent_message,
                options={"type": "REPLY_TO", "direction": "out"}
            )
        
        created_messages.append(message)
        
        # Progress indicator
        if (idx + 1) % 4 == 0:
            print(f"  Created {idx + 1} messages...")
    
    print(f"  Created {len(created_messages)} total messages")
    
    return created_messages


def main():
    print("=" * 60)
    print("Hyperedge Conversation Demo - Data Seeding")
    print("=" * 60 + "\n")
    
    # Clear existing data for clean state
    clear_existing_data()
    
    # Seed data
    users = seed_users()
    channels = seed_channels()
    threads = seed_threads(users, channels)
    messages = seed_messages(users, channels, threads)
    
    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Users:    {len(users)}")
    print(f"  Channels: {len(channels)}")
    print(f"  Threads:  {len(threads)}")
    print(f"  Messages: {len(messages)}")
    print(f"\nRun 'python main.py' to execute hyperedge queries.")


if __name__ == "__main__":
    main()
