"""
Conversation History Seed Script

Generates mock conversation data to demonstrate temporal graph queries.
This script creates realistic support conversations with:
- Multiple participants (users and agents)
- Various channels (chat, email, phone)
- Temporal patterns (quick replies, delayed responses)
- Branching scenarios (escalations, handoffs)

The script is idempotent: run it multiple times safely.
"""

import os
import random
import sys
from datetime import datetime, timedelta
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

# Realistic mock data
USERS = [
    {"id": "user_001", "name": "Alice Chen", "email": "alice.chen@techcorp.io"},
    {"id": "user_002", "name": "Bob Martinez", "email": "bob.m@startup.io"},
    {"id": "user_003", "name": "Carol Johnson", "email": "carol.j@enterprise.com"},
    {"id": "user_004", "name": "David Kim", "email": "dkim@agency.net"},
    {"id": "user_005", "name": "Eva Patel", "email": "eva.patel@consulting.co"},
]

AGENTS = [
    {"id": "agent_001", "name": "Sam Support", "specialty": "billing"},
    {"id": "agent_002", "name": "Lisa Tech", "specialty": "technical"},
    {"id": "agent_003", "name": "Mike Manager", "specialty": "escalations"},
]

CHANNELS = ["chat", "email", "phone"]

# Realistic conversation templates
CONVERSATION_TEMPLATES = {
    "billing": {
        "user_messages": [
            "Hi, I have a question about my latest invoice",
            "The amount seems higher than usual",
            "Can you explain the charges?",
            "Thank you for clarifying",
            "That makes sense now, thanks!",
        ],
        "agent_messages": [
            "Hello! I'd be happy to help with your billing question",
            "I can see your invoice #INV-4521. Let me check the details",
            "The increase is due to the plan upgrade you made on the 15th",
            "You're welcome! Is there anything else I can help with?",
            "Glad I could help! Have a great day!",
        ],
    },
    "technical": {
        "user_messages": [
            "I'm getting an error when trying to connect",
            "The error message says 'Connection refused on port 443'",
            "I tried restarting but it didn't help",
            "Now I'm getting a different error",
            "That fixed it! Thank you so much!",
        ],
        "agent_messages": [
            "I'd be happy to help troubleshoot this connection issue",
            "Can you tell me which application you're using?",
            "Let's check your SSL certificate status",
            "I see the issue - your certificate expired yesterday",
            "Great! I'm glad that's resolved. Don't hesitate to reach out if you need more help.",
        ],
    },
    "feature_request": {
        "user_messages": [
            "Is there a way to export data to CSV?",
            "I couldn't find it in the settings",
            "That would be really helpful for our reports",
            "Perfect, I'll wait for that feature then",
        ],
        "agent_messages": [
            "Thanks for reaching out! Let me check our documentation for you",
            "We do have CSV export in the Enterprise plan",
            "I've submitted a feature request to our product team",
            "I'll update you when it's available in your plan!",
        ],
    },
}

ESCALATION_PATTERNS = [
    "I'm escalating this to our technical team",
    "Let me connect you with a specialist",
    "This requires manager approval, one moment",
]

HANDOVERS = [
    "Transferring you to our billing department",
    "I'm handing this over to our email specialist",
]


def clear_existing_data():
    """Remove all existing conversation data (idempotent cleanup)"""
    print("Clearing existing data...")
    try:
        db.records.delete_many({"labels": ["MESSAGE"], "where": {}})
        db.records.delete_many({"labels": ["CONVERSATION"], "where": {}})
        db.records.delete_many({"labels": ["USER"], "where": {}})
        db.records.delete_many({"labels": ["AGENT"], "where": {}})
    except Exception:
        pass  # Tables may not exist yet
    print("✓ Data cleared")



def create_participants():
    """Create user and agent records"""
    print("\nCreating participants...")
    users = []
    agents = []
    
    for user_data in USERS:
        user = db.records.upsert(
            label="USER",
            data={"externalId": user_data["id"], "name": user_data["name"], "email": user_data["email"]},
            options={"mergeBy": ["externalId"]}
        )
        users.append(user)
        if len(users) % 100 == 0:
            print(f"  Created {len(users)} users...")
    
    for agent_data in AGENTS:
        agent = db.records.upsert(
            label="AGENT",
            data={"externalId": agent_data["id"], "name": agent_data["name"], "specialty": agent_data["specialty"]},
            options={"mergeBy": ["externalId"]}
        )
        agents.append(agent)
    
    print(f"✓ Created {len(users)} users and {len(agents)} agents")
    return users, agents


def create_conversation(
    conversation_id: str,
    channel: str,
    start_time: datetime,
    users: list,
    agents: list,
    template_key: str
) -> dict:
    """Create a complete conversation with temporal message links"""
    template = CONVERSATION_TEMPLATES[template_key]
    user = random.choice(users)
    agent = random.choice([a for a in agents if a.data.get("specialty") == {"billing": "billing", "technical": "technical", "feature_request": "escalations"}.get(template_key, "billing")])
    if not agent:
        agent = random.choice(agents)
    
    # Create conversation record
    conversation = db.records.create(
        label="CONVERSATION",
        data={
            "conversationId": conversation_id,
            "channel": channel,
            "startedAt": start_time.isoformat(),
            "status": "closed"
        }
    )
    
    # Link participants
    db.records.attach(source=user, target=conversation, options={"type": "PARTICIPATES_IN"})
    db.records.attach(source=agent, target=conversation, options={"type": "PARTICIPATES_IN"})
    
    # Create messages with temporal links
    prev_message = None
    messages_created = 0
    current_time = start_time
    
    user_msgs = template["user_messages"]
    agent_msgs = template["agent_messages"]
    
    # Interleave messages
    for i in range(max(len(user_msgs), len(agent_msgs))):
        # User message
        if i < len(user_msgs):
            msg = db.records.create(
                label="MESSAGE",
                data={
                    "content": user_msgs[i],
                    "senderId": user.data["externalId"],
                    "senderType": "user",
                    "senderName": user.data["name"],
                    "timestamp": current_time.isoformat(),
                    "conversationId": conversation_id
                }
            )
            
            # Link to conversation
            db.records.attach(source=msg, target=conversation, options={"type": "PART_OF"})
            
            # Temporal links
            if prev_message:
                db.records.attach(source=prev_message, target=msg, options={"type": "NEXT"})
                db.records.attach(source=msg, target=prev_message, options={"type": "PREV"})
            
            prev_message = msg
            messages_created += 1
            current_time += timedelta(minutes=random.randint(1, 5))
        
        # Agent message
        if i < len(agent_msgs):
            msg = db.records.create(
                label="MESSAGE",
                data={
                    "content": agent_msgs[i],
                    "senderId": agent.data["externalId"],
                    "senderType": "agent",
                    "senderName": agent.data["name"],
                    "timestamp": current_time.isoformat(),
                    "conversationId": conversation_id
                }
            )
            
            db.records.attach(source=msg, target=conversation, options={"type": "PART_OF"})
            
            if prev_message:
                db.records.attach(source=prev_message, target=msg, options={"type": "NEXT"})
                db.records.attach(source=msg, target=prev_message, options={"type": "PREV"})
            
            prev_message = msg
            messages_created += 1
            current_time += timedelta(minutes=random.randint(1, 15))
    
    return {"conversation": conversation, "count": messages_created}



def create_escalated_conversation(
    original_conversation_id: str,
    start_time: datetime,
    users: list,
    agents: list
):
    """Create a conversation that branches from an existing one"""
    escalated_id = f"conv_escalated_{original_conversation_id.split('_')[-1]}"
    conversation = db.records.create(
        label="CONVERSATION",
        data={
            "conversationId": escalated_id,
            "channel": "phone",
            "startedAt": start_time.isoformat(),
            "status": "closed",
            "escalatedFrom": original_conversation_id
        }
    )
    
    user = random.choice(users)
    manager = [a for a in agents if a.data.get("specialty") == "escalations"][0]
    if manager:
        db.records.attach(source=user, target=conversation, options={"type": "PARTICIPATES_IN"})
        db.records.attach(source=manager, target=conversation, options={"type": "PARTICIPATES_IN"})
    
    # Link to original conversation
    original = db.records.find({"labels": ["CONVERSATION"], "where": {"conversationId": original_conversation_id}})
    if original.data:
        db.records.attach(source=conversation, target=original.data[0], options={"type": "BRANCHED_FROM"})
    
    # Create escalation messages
    msg1 = db.records.create(
        label="MESSAGE",
        data={
            "content": random.choice(ESCALATION_PATTERNS),
            "senderId": agents[0].data["externalId"],
            "senderType": "agent",
            "senderName": agents[0].data["name"],
            "timestamp": start_time.isoformat(),
            "conversationId": escalated_id
        }
    )
    db.records.attach(source=msg1, target=conversation, options={"type": "PART_OF"})
    
    msg2 = db.records.create(
        label="MESSAGE",
        data={
            "content": "Thank you for escalating this. Let me look into it further.",
            "senderId": manager.data["externalId"] if manager else "unknown",
            "senderType": "agent",
            "senderName": manager.data["name"] if manager else "Manager",
            "timestamp": (start_time + timedelta(minutes=5)).isoformat(),
            "conversationId": escalated_id
        }
    )
    db.records.attach(source=msg2, target=conversation, options={"type": "PART_OF"})
    db.records.attach(source=msg1, target=msg2, options={"type": "NEXT"})
    db.records.attach(source=msg2, target=msg1, options={"type": "PREV"})
    
    return {"conversation": conversation, "count": 2}


def main():
    print("=" * 60)
    print("Conversation History Seed Script")
    print("=" * 60)
    
    # Clear and recreate data
    clear_existing_data()
    
    # Create participants
    users, agents = create_participants()
    
    # Create conversations
    print("\nCreating conversations with temporal links...")
    total_messages = 0
    
    # Generate conversations across different time periods
    base_time = datetime.now() - timedelta(days=90)
    
    for i in range(10):
        conv_id = f"conv_{i+1:03d}"
        channel = CHANNELS[i % len(CHANNELS)]
        template_key = list(CONVERSATION_TEMPLATES.keys())[i % len(CONVERSATION_TEMPLATES)]
        start = base_time + timedelta(days=i * 9)
        
        result = create_conversation(conv_id, channel, start, users, agents, template_key)
        total_messages += result["count"]
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1} conversations ({total_messages} messages)...")
        
        # Add escalation for some conversations
        if i in [2, 5, 8]:
            esc_result = create_escalated_conversation(conv_id, start + timedelta(days=1), users, agents)
            total_messages += esc_result["count"]
    
    print(f"\n✓ Seed complete!")
    print(f"  Total conversations: 10 base + 3 escalated = 13")
    print(f"  Total messages: {total_messages}")
    print(f"  Users: {len(users)}")
    print(f"  Agents: {len(agents)}")
    print("\nYou can now run main.py to explore temporal graph queries!")


if __name__ == "__main__":
    main()
