#!/usr/bin/env python3
"""
Seed script for Real-Time Conversation Summarization Demo.

Generates sample conversations, messages, users, and topics to demonstrate
RushDB's graph-traced reference capabilities.

Run this script to populate the database with realistic mock data.
The script is idempotent — safe to run multiple times.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Sample data
USERS = [
    {"id": "user_alice", "name": "Alice Chen", "role": "tech-lead", "team": "platform"},
    {"id": "user_bob", "name": "Bob Martinez", "role": "senior-engineer", "team": "backend"},
    {"id": "user_carol", "name": "Carol Kim", "role": "product-manager", "team": "product"},
    {"id": "user_david", "name": "David Park", "role": "devops", "team": "infrastructure"},
]

CONVERSATION_TEMPLATES = [
    {
        "id": "proj-deploy-pipeline",
        "title": "Deploy Pipeline Discussion",
        "messages": [
            "Hey team, the new deploy script is ready for testing",
            "Great! I'll set up the staging environment today",
            "Make sure to include the rollback mechanism we discussed",
            "Already added in the latest commit. Ready for review.",
            "@alice can you approve the PR when you get a chance?",
            "Approved! Let's schedule the deployment for tomorrow 10am",
            "I'll prepare the monitoring dashboard before we deploy",
            "Remember to update the runbook in Notion",
            "Done! Added screenshots for each step",
            "Perfect. @david will handle the production migration",
            "Deployment complete! All services healthy",
            "Excellent work everyone. Post-mortem scheduled for Friday",
        ],
        "topics": ["deployment", "pipeline", "rollback", "monitoring"],
        "entities": ["@alice", "@david"],
    },
    {
        "id": "api-design-review",
        "title": "API Design Review",
        "messages": [
            "Let's discuss the new REST endpoints for the user service",
            "I propose we use nested resources for related entities",
            "Should we include filtering parameters in the query string?",
            "Yes, like ?status=active&limit=50&offset=0",
            "Good point. What about sorting? Should we support multiple fields?",
            "Let's stick to single field sorting for v1",
            "@carol do we have bandwidth to implement cursor pagination?",
            "Can we defer that to v1.1? Current offset-based is sufficient",
            "Agreed. We'll revisit pagination in the next sprint",
            "I'll update the API spec document with our decisions",
        ],
        "topics": ["api", "rest", "pagination", "design"],
        "entities": ["@carol"],
    },
    {
        "id": "bug-review-session",
        "title": "Critical Bug Review",
        "messages": [
            "We're seeing intermittent 500 errors in production",
            "The error logs point to the database connection pool",
            "Looks like connections aren't being released properly",
            "I found a leak in the cache invalidation logic",
            "Good catch! Can you share the fix in the ticket?",
            "Done. Added the stack trace and reproduction steps",
            "@bob can you review the fix before EOD?",
            "On it. Will have the review done by 4pm",
            "Deploying hotfix now. All instances should be updated in 10 mins",
            "Hotfix deployed. Error rate back to normal.",
        ],
        "topics": ["bug", "hotfix", "database", "production"],
        "entities": ["@bob"],
    },
]


def check_data_exists(conversation_id: str, db: RushDB) -> bool:
    """Check if conversation already exists in the database."""
    result = db.records.find({
        "labels": ["CONVERSATION"],
        "where": {"conversationId": conversation_id}
    })
    return result.total > 0


def seed_conversations(db: RushDB) -> list:
    """Create conversations with messages and graph-traced references."""
    created = []
    
    for idx, template in enumerate(CONVERSATION_TEMPLATES):
        print(f"\nProcessing conversation {idx + 1}/{len(CONVERSATION_TEMPLATES)}: {template['title']}")
        
        # Check if already exists
        if check_data_exists(template['id'], db):
            print(f"  ✓ Already exists, skipping...")
            continue
        
        with db.transactions.begin() as tx:
            # Create conversation record
            conversation = db.records.create(
                label="CONVERSATION",
                data={
                    "conversationId": template['id'],
                    "title": template['title'],
                    "createdAt": (datetime.now() - timedelta(days=7)).isoformat(),
                    "status": "active",
                },
                transaction=tx
            )
            print(f"  ✓ Created conversation: {conversation.id}")
            
            # Create user participants
            participants = []
            for user in USERS:
                user_record = db.records.create(
                    label="USER",
                    data=user,
                    transaction=tx
                )
                participants.append(user_record)
                db.records.attach(
                    source=conversation,
                    target=user_record,
                    options={"type": "HAS_PARTICIPANT", "direction": "out"},
                    transaction=tx
                )
            print(f"  ✓ Created {len(participants)} participants")
            
            # Create messages with temporal ordering
            for msg_idx, content in enumerate(template['messages']):
                sender = random.choice(participants)
                message = db.records.create(
                    label="MESSAGE",
                    data={
                        "content": content,
                        "timestamp": (datetime.now() - timedelta(
                            days=6,
                            hours=msg_idx * 2,
                            minutes=random.randint(0, 59)
                        )).isoformat(),
                        "index": msg_idx,
                    },
                    transaction=tx
                )
                
                # Link message to conversation (sequence)
                db.records.attach(
                    source=conversation,
                    target=message,
                    options={"type": "CONTAINS", "direction": "out"},
                    transaction=tx
                )
                
                # Link message to sender
                db.records.attach(
                    source=message,
                    target=sender,
                    options={"type": "SENT_BY", "direction": "out"},
                    transaction=tx
                )
            print(f"  ✓ Created {len(template['messages'])} messages")
            
            # Create topics (entity extraction simulation)
            for topic in template['topics']:
                topic_record = db.records.create(
                    label="TOPIC",
                    data={"name": topic, "weight": round(random.uniform(0.5, 1.0), 2)},
                    transaction=tx
                )
                db.records.attach(
                    source=conversation,
                    target=topic_record,
                    options={"type": "DISCUSSES", "direction": "out"},
                    transaction=tx
                )
            print(f"  ✓ Created {len(template['topics'])} topics")
            
            # Create mentioned entities
            for entity in template['entities']:
                entity_record = db.records.create(
                    label="ENTITY",
                    data={"identifier": entity, "type": "user-mention"},
                    transaction=tx
                )
                db.records.attach(
                    source=conversation,
                    target=entity_record,
                    options={"type": "REFERENCES", "direction": "out"},
                    transaction=tx
                )
            print(f"  ✓ Created {len(template['entities'])} entities")
            
            created.append(conversation)
    
    return created


def main():
    """Main seed function."""
    print("=" * 60)
    print("Real-Time Conversation Summarization - Data Seeder")
    print("=" * 60)
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\n❌ ERROR: RUSHDB_API_KEY environment variable not set")
        print("   Please copy .env.example to .env and add your API key")
        return
    
    db = RushDB(api_key)
    print("\n✓ Connected to RushDB")
    
    print("\n📊 Seeding conversations with graph-traced references...")
    created = seed_conversations(db)
    
    if created:
        print(f"\n✓ Successfully seeded {len(created)} conversations")
    else:
        print("\n✓ Data already exists (or no new data to seed)")
    
    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("Run 'python main.py' to execute the demonstration")
    print("=" * 60)


if __name__ == "__main__":
    main()
