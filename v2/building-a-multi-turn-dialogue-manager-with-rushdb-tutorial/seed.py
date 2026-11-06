"""
Seed script that generates realistic multi-turn conversation data.
This script creates sample users, sessions, messages, and context data
to demonstrate the dialogue manager's capabilities.

Run this once to populate the database with sample data, or to reset
the demo environment.
"""

import os
import random
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize Faker for realistic data generation
fake = Faker()

# Domain-specific intents and entities for demonstration
INTENTS = [
    "greeting", "product_inquiry", "order_status", "return_request",
    "technical_support", "billing_question", "feedback", "closing"
]

PRODUCTS = [
    ("wireless headphones", "TECH-001"),
    ("smart watch", "TECH-002"),
    ("laptop stand", "TECH-003"),
    ("mechanical keyboard", "TECH-004"),
    ("webcam HD", "TECH-005"),
]

CUSTOMER_NAMES = [
    "Alice Chen", "Bob Martinez", "Carol Williams", "David Kim",
    "Emma Thompson", "Frank Garcia", "Grace Lee", "Henry Patel"
]


def create_user(db):
    """Create a user record."""
    name = random.choice(CUSTOMER_NAMES)
    email = f"{name.lower().replace(' ', '.')}@example.com"
    
    user = db.records.create(
        label="User",
        data={
            "name": name,
            "email": email,
            "tier": random.choice(["basic", "premium", "enterprise"]),
            "preferredLanguage": random.choice(["en", "es", "fr"]),
            "createdAt": fake.date_time_between(start_date="-1y", end_date="now").isoformat()
        }
    )
    return user


def create_session(db, user, session_id_str):
    """Create a conversation session with metadata."""
    now = datetime.now()
    started_at = now - timedelta(minutes=random.randint(5, 120))
    
    session = db.records.create(
        label="Session",
        data={
            "sessionId": session_id_str,
            "channel": random.choice(["web", "mobile", "api"]),
            "status": "active",
            "startedAt": started_at.isoformat(),
            "lastActivityAt": now.isoformat(),
            "turnCount": 0,
            "userAgent": fake.user_agent(),
            "locale": random.choice(["en-US", "en-GB", "es-ES"])
        }
    )
    
    # Link session to user
    db.records.attach(
        source=user,
        target=session,
        options={"type": "HAS_SESSION"}
    )
    
    return session


def create_message(db, session, role, content, timestamp, turn_num):
    """Create a message within a session."""
    intent = random.choice(INTENTS) if role == "user" else None
    
    message_data = {
        "role": role,
        "content": content,
        "timestamp": timestamp.isoformat(),
        "turnNumber": turn_num,
        "messageId": fake.uuid4()
    }
    
    if role == "user":
        message_data["detectedIntent"] = intent
        message_data["entities"] = {
            "product": random.choice(PRODUCTS) if random.random() > 0.3 else None,
            "date": (timestamp + timedelta(days=random.randint(1, 14))).date().isoformat()
        }
    
    message = db.records.create(
        label="Message",
        data=message_data
    )
    
    # Link message to session
    db.records.attach(
        source=session,
        target=message,
        options={"type": "CONTAINS"}
    )
    
    return message


def create_context(db, message, context_type, data):
    """Create context metadata for a message."""
    context = db.records.create(
        label="Context",
        data={
            "type": context_type,
            "data": data,
            "createdAt": datetime.now().isoformat()
        }
    )
    
    # Link context to message
    db.records.attach(
        source=message,
        target=context,
        options={"type": "HAS_CONTEXT"}
    )
    
    return context


def generate_conversation_turns():
    """Generate realistic conversation turn pairs."""
    templates = [
        {
            "user": "Hi, I need help with my recent order.",
            "assistant": "Hello! I'd be happy to help you with your order. Could you please provide your order number or the email associated with your account?"
        },
        {
            "user": "I'm looking at the {product} you have in stock.",
            "assistant": "Great choice! The {product} is one of our best sellers. We currently have availability and can ship within 2-3 business days. Would you like me to check the exact delivery estimate for your location?"
        },
        {
            "user": "What's the status of order #{order_id}?",
            "assistant": "Let me look that up for you. Your order #{order_id} is currently being processed and is expected to ship by {date}. You'll receive a tracking number via email once it ships."
        },
        {
            "user": "I'd like to return an item from my last order.",
            "assistant": "I can help you with a return. Our return policy allows items to be returned within 30 days of delivery. Could you tell me which item you'd like to return and the reason for the return?"
        },
        {
            "user": "Can you explain the billing on my last invoice?",
            "assistant": "Of course! I can see your recent invoice. You have a base charge of $49.99 plus any additional usage. Would you like me to break down the specific charges in detail?"
        },
        {
            "user": "The product I received isn't working correctly.",
            "assistant": "I'm sorry to hear that. Let's get this resolved for you. Could you describe the issue you're experiencing? If it's a technical problem, I can help troubleshoot or initiate a replacement if needed."
        },
        {
            "user": "Thanks for your help today!",
            "assistant": "You're welcome! It was my pleasure assisting you. If you have any other questions in the future, don't hesitate to reach out. Have a great day!"
        }
    ]
    return templates


def seed_database():
    """Main seeding function - creates sample data in RushDB."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Please copy .env.example to .env and add your API key")
        return False
    
    print("Connecting to RushDB...")
    db = RushDB(api_key)
    
    # Check if data already exists
    existing_users = db.records.find({"labels": ["User"], "limit": 1})
    if existing_users.data:
        response = input("Database already contains data. Re-seed? (y/n): ")
        if response.lower() != 'y':
            print("Seeding cancelled.")
            return True
        print("Clearing existing data...")
        db.records.delete_many({"labels": ["Context"]})
        db.records.delete_many({"labels": ["Message"]})
        db.records.delete_many({"labels": ["Session"]})
        db.records.delete_many({"labels": ["User"]})
    
    print("\nSeeding database with sample conversation data...")
    
    # Create sample users
    num_users = 5
    users = []
    for i in range(num_users):
        user = create_user(db)
        users.append(user)
        print(f"  Created user: {user['name']}")
    
    # Create sessions and conversations for each user
    num_sessions_per_user = 2
    turns = generate_conversation_turns()
    
    total_created = 0
    for user in users:
        for s_idx in range(num_sessions_per_user):
            session_id = f"SES-{fake.uuid4()[:8].upper()}"
            session = create_session(db, user, session_id)
            
            # Random number of conversation turns
            num_turns = random.randint(4, 8)
            start_time = datetime.now() - timedelta(minutes=random.randint(30, 180))
            
            for turn in range(num_turns):
                turn_time = start_time + timedelta(minutes=turn * 2)
                
                # Alternate between user and assistant
                if turn % 2 == 0:
                    # User message
                    template = random.choice(turns)
                    content = template["user"].format(
                        product=random.choice(PRODUCTS)[0],
                        order_id=fake.numerify(text="#####"),
                        date=(turn_time + timedelta(days=3)).strftime("%B %d")
                    )
                    message = create_message(db, session, "user", content, turn_time, turn)
                else:
                    # Assistant message
                    template = turns[min(turn // 2, len(turns) - 1)]
                    content = template["assistant"].format(
                        product=random.choice(PRODUCTS)[0],
                        order_id=fake.numerify(text="#####"),
                        date=(turn_time + timedelta(days=3)).strftime("%B %d")
                    )
                    message = create_message(db, session, "assistant", content, turn_time, turn)
                    
                    # Add some context to assistant responses
                    if random.random() > 0.5:
                        create_context(
                            db, message, "sentiment",
                            {"polarity": random.choice(["positive", "neutral", "helpful"])}
                        )
                
                total_created += 1
                
                # Update session turn count
                session.data["turnCount"] = turn + 1
                session.data["lastActivityAt"] = turn_time.isoformat()
            
            print(f"  Created session {session_id} with {num_turns} turns")
            
            # Progress indicator
            if total_created % 100 == 0:
                print(f"  ... {total_created} messages created")
    
    print(f"\n✓ Seeding complete! Created:")
    print(f"  - {len(users)} users")
    print(f"  - {len(users) * num_sessions_per_user} sessions")
    print(f"  - {total_created} messages")
    
    return True


if __name__ == "__main__":
    success = seed_database()
    exit(0 if success else 1)
