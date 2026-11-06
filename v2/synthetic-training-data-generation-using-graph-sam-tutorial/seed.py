#!/usr/bin/env python3
"""
Seed script for Synthetic Training Data Generation tutorial.

This script creates a realistic conversation graph with:
- 50 users with varied personas
- 200 conversations across different topics
- 800 messages forming conversation trees
- 15 topic categories
- Proper relationships between all entities

The data is designed to represent a customer support/HR assistant domain,
suitable for generating synthetic training data for support LLMs.
"""

import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker

# Load environment variables
load_dotenv()

# Initialize Faker with seed for reproducibility
fake = Faker(['en_US'])
Faker.seed(42)
random.seed(42)

# Import RushDB after env is loaded
from rushdb import RushDB


# =============================================================================
# DATA TEMPLATES
# =============================================================================

TOPICS = [
    "billing",
    "technical_support",
    "account_management",
    "product_inquiry",
    "general_feedback",
    "bug_report",
    "feature_request",
    "security_concern",
    "api_integration",
    "data_export",
    "permissions",
    "onboarding",
    "training_resources",
    "compliance",
    "partnership",
]

USER_PERSONAS = [
    "frustrated_customer",
    "patient_technical_user",
    "confused_beginner",
    "busy_professional",
    "detail_oriented_analyst",
    "friendly_inquirer",
    "escalating_user",
    "new_employee",
    "returning_customer",
    "power_user",
]

MESSAGE_TEMPLATES = {
    "billing": [
        {"role": "user", "templates": [
            "I was charged twice for my last subscription payment.",
            "Can you help me understand my invoice?",
            "I need a refund for the overcharge.",
            "Why did my price go up this month?",
            "Do you offer annual billing discounts?",
            "How do I update my payment method?",
            "I found an incorrect charge on my account.",
            "Can I get an itemized invoice?",
        ]},
        {"role": "agent", "templates": [
            "I apologize for the inconvenience. Let me look into that right away.",
            "I can see the duplicate charge. I'm processing a refund now.",
            "Here's a breakdown of your invoice...",
            "Thank you for bringing this to our attention.",
            "I've adjusted your billing cycle. You should see the change next month.",
            "I can help you update your payment method. What card would you like to use?",
        ]},
    ],
    "technical_support": [
        {"role": "user", "templates": [
            "The application keeps crashing when I try to export data.",
            "I'm getting a 500 error on the dashboard.",
            "How do I clear my cache?",
            "My settings aren't saving properly.",
            "The API is returning authentication errors.",
            "I can't log in after resetting my password.",
            "The mobile app is very slow lately.",
            "Notifications aren't working for me.",
        ]},
        {"role": "agent", "templates": [
            "I'm sorry you're experiencing this issue. Let me help troubleshoot.",
            "Can you tell me what browser and OS you're using?",
            "I've cleared the cache on our end. Please try again.",
            "This appears to be a known issue. Our team is working on a fix.",
            "Let me escalate this to our engineering team.",
            "Have you tried clearing your browser cache and cookies?",
        ]},
    ],
    "account_management": [
        {"role": "user", "templates": [
            "I need to update my company name in the account.",
            "How do I add a new team member?",
            "I want to downgrade my subscription plan.",
            "Can you merge two accounts together?",
            "I accidentally created a duplicate account.",
            "How do I transfer ownership of the account?",
            "I need to update our company address.",
            "How do I delete my account?",
        ]},
        {"role": "agent", "templates": [
            "I can help you update your account settings.",
            "Let me verify a few details before making these changes.",
            "I'll send an email to confirm the ownership transfer.",
            "Here's how you can add team members from your dashboard...",
            "I understand you want to downgrade. Let me explain your options.",
        ]},
    ],
    "product_inquiry": [
        {"role": "user", "templates": [
            "Does your product support SAML SSO?",
            "What's the difference between Pro and Enterprise plans?",
            "Can I use webhooks with the basic plan?",
            "Do you have an on-premise version?",
            "What's your data retention policy?",
            "Does this integrate with Salesforce?",
            "What's your uptime SLA?",
        ]},
        {"role": "agent", "templates": [
            "Great question! Yes, we support SAML SSO on the Enterprise plan.",
            "Let me break down the key differences between our plans...",
            "Webhooks are available on Pro and above. Would you like me to upgrade you?",
            "We offer both cloud and self-hosted options. Here's the comparison...",
            "Our data retention policy allows you to configure retention periods.",
            "Yes, we have a native Salesforce integration. It's easy to set up.",
        ]},
    ],
    "general_feedback": [
        {"role": "user", "templates": [
            "Love the new dashboard design!",
            "The search feature is much better now.",
            "Would be great to have dark mode.",
            "Your support team has been incredibly helpful.",
            "The mobile app needs some work.",
            "I appreciate how fast you respond to issues.",
        ]},
        {"role": "agent", "templates": [
            "Thank you for your feedback! I'm glad you're enjoying the new design.",
            "Dark mode is on our roadmap. I've added your vote to the request.",
            "I appreciate you taking the time to share your thoughts.",
            "Thank you for the kind words! We strive for excellent support.",
        ]},
    ],
}

CLOSING_PHRASES = [
    "Thank you for contacting us!",
    "Is there anything else I can help you with?",
    "Have a great day!",
    "We're here if you need any more assistance.",
    "Pleasure assisting you today.",
]

RESOLUTION_STATUSES = ["resolved", "escalated", "pending", "closed"]


# =============================================================================
# DATA GENERATION HELPERS
# =============================================================================

def generate_user_data(count: int) -> list[dict]:
    """Generate user persona data."""
    users = []
    for i in range(count):
        persona = random.choice(USER_PERSONAS)
        users.append({
            "user_id": f"user_{i:04d}",
            "name": fake.name(),
            "email": fake.email(),
            "company": fake.company() if random.random() > 0.3 else None,
            "persona": persona,
            "tenure_days": random.randint(1, 730),
            "previous_tickets": random.randint(0, 15),
        })
    return users


def generate_conversation_data(users: list[dict], count: int) -> list[dict]:
    """Generate conversation metadata."""
    conversations = []
    base_date = datetime.now() - timedelta(days=90)
    
    for i in range(count):
        user = random.choice(users)
        topic = random.choice(TOPICS)
        created_at = base_date + timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        conversations.append({
            "conversation_id": f"conv_{i:05d}",
            "topic": topic,
            "created_at": created_at.isoformat(),
            "resolution_status": random.choices(
                RESOLUTION_STATUSES,
                weights=[0.7, 0.1, 0.1, 0.1]
            )[0],
            "satisfaction_score": random.randint(1, 5) if random.random() > 0.3 else None,
        })
    return conversations


def generate_message_trees(conversations: list[dict], messages_per_conversation: int = 4) -> list[dict]:
    """Generate message trees for conversations."""
    messages = []
    message_id = 0
    
    for conv in conversations:
        topic = conv["topic"]
        templates = MESSAGE_TEMPLATES.get(topic, MESSAGE_TEMPLATES["general_feedback"])
        num_messages = random.randint(2, messages_per_conversation)
        
        # First message is always user
        user_template = random.choice([t for t in templates if t["role"] == "user"])
        messages.append({
            "message_id": f"msg_{message_id:06d}",
            "conversation_id": conv["conversation_id"],
            "sequence_number": 0,
            "role": "user",
            "content": random.choice(user_template["templates"]),
            "sentiment": random.choice(["frustrated", "neutral", "confused", "calm"]),
        })
        message_id += 1
        
        # Subsequent messages alternate user/agent
        for seq in range(1, num_messages):
            role = "agent" if seq % 2 == 1 else "user"
            role_templates = [t for t in templates if t["role"] == role]
            
            if role_templates and random.random() > 0.2:
                template = random.choice(role_templates)
                messages.append({
                    "message_id": f"msg_{message_id:06d}",
                    "conversation_id": conv["conversation_id"],
                    "sequence_number": seq,
                    "role": role,
                    "content": random.choice(template["templates"]),
                    "sentiment": random.choice(["helpful", "neutral", "apologetic", "professional"]),
                })
            message_id += 1
        
        # Add closing from agent
        if num_messages >= 2 and random.random() > 0.3:
            messages.append({
                "message_id": f"msg_{message_id:06d}",
                "conversation_id": conv["conversation_id"],
                "sequence_number": num_messages,
                "role": "agent",
                "content": random.choice(CLOSING_PHRASES),
                "sentiment": "professional",
            })
    
    return messages


# =============================================================================
# MAIN SEEDING LOGIC
# =============================================================================

def check_existing_data(db: RushDB) -> bool:
    """Check if data already exists in the database."""
    result = db.records.find({"labels": ["USER"], "limit": 1})
    return result.total > 0


def seed_database():
    """Main seeding function."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Please create a .env file with your API key (see .env.example)")
        sys.exit(1)
    
    db = RushDB(api_key)
    
    # Check for existing data
    if check_existing_data(db):
        print("[Seed] Data already exists. Skipping seed (idempotent).")
        print("[Seed] To re-seed, delete existing records first.")
        return
    
    print("[Seeding] Starting database seeding...")
    
    # Generate data
    print("[Seeding] Creating 50 users...")
    users = generate_user_data(50)
    
    print("[Seeding] Creating 200 conversations...")
    conversations = generate_conversation_data(users, 200)
    
    print("[Seeding] Creating ~800 messages...")
    messages = generate_message_trees(conversations)
    
    # Create records in RushDB
    print("[Seeding] Creating USER records...")
    created_users = db.records.create_many(label="USER", data=users)
    print(f"  Created {len(created_users.data)} users")
    
    print("[Seeding] Creating CONVERSATION records...")
    created_conversations = db.records.create_many(label="CONVERSATION", data=conversations)
    print(f"  Created {len(created_conversations.data)} conversations")
    
    print("[Seeding] Creating MESSAGE records...")
    # Process in batches for better performance
    batch_size = 100
    created_messages_count = 0
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i + batch_size]
        db.records.create_many(label="MESSAGE", data=batch)
        created_messages_count += len(batch)
        if (i + batch_size) % 200 == 0:
            print(f"  Created {created_messages_count}/{len(messages)} messages...")
    print(f"  Created {created_messages_count} messages")
    
    print("[Seeding] Creating TOPIC records...")
    topic_data = [{"name": topic, "category": "support"} for topic in TOPICS]
    db.records.create_many(label="TOPIC", data=topic_data)
    print(f"  Created {len(topic_data)} topics")
    
    # Create relationships
    print("[Seeding] Creating relationships...")
    
    # User -> Conversation relationships
    for conv_data in conversations:
        user_data = next(u for u in users if u["user_id"] == conv_data["user_id"])
        conv_record = db.records.find_one({
            "labels": ["CONVERSATION"],
            "where": {"conversation_id": conv_data["conversation_id"]}
        })
        user_record = db.records.find_one({
            "labels": ["USER"],
            "where": {"user_id": user_data["user_id"]}
        })
        if conv_record and user_record:
            db.records.attach(
                source=user_record,
                target=conv_record,
                options={"type": "INITIATED", "direction": "out"}
            )
    
    # Conversation -> Topic relationships
    for conv_data in conversations:
        conv_record = db.records.find_one({
            "labels": ["CONVERSATION"],
            "where": {"conversation_id": conv_data["conversation_id"]}
        })
        topic_record = db.records.find_one({
            "labels": ["TOPIC"],
            "where": {"name": conv_data["topic"]}
        })
        if conv_record and topic_record:
            db.records.attach(
                source=conv_record,
                target=topic_record,
                options={"type": "HAS_TOPIC", "direction": "out"}
            )
    
    # Conversation -> Message relationships (PART_OF)
    messages_batch = db.records.find({"labels": ["MESSAGE"], "limit": 800})
    for msg in messages_batch.data:
        conv_record = db.records.find_one({
            "labels": ["CONVERSATION"],
            "where": {"conversation_id": msg.data["conversation_id"]}
        })
        if conv_record:
            db.records.attach(
                source=msg,
                target=conv_record,
                options={"type": "PART_OF", "direction": "in"}
            )
    
    total_records = len(users) + len(conversations) + len(messages) + len(TOPICS)
    print(f"[Seeding] Done! Created {total_records} records")
    print("[Seeding] Relationships created successfully")


if __name__ == "__main__":
    seed_database()
