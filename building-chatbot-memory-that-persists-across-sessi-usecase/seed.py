"""
Seed script for chatbot memory demo.

Creates realistic mock data:
- 2 users (Alice and Bob)
- 4 sessions per user
- ~50 messages with varied topics
- Extracted entities (pet names, preferences, context facts)

Idempotent: safe to run multiple times. Skips if data already exists.
"""

import os
import sys
import hashlib
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")

if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key, url=url) if url else RushDB(api_key)


def generate_embedding(text: str) -> list[float]:
    """
    Generate a deterministic 384-dimensional vector from text.
    
    This is a demo-quality embedding using hash-based sampling.
    For production, use OpenAI embeddings or Sentence Transformers.
    """
    # Use SHA-256 for deterministic, well-distributed values
    hash_bytes = hashlib.sha256(text.encode()).digest()
    
    # Convert to 384 floats by sampling the hash in chunks
    vector = []
    for i in range(384):
        # Take 4 bytes starting at position (i * 4) % len(hash_bytes)
        start = (i * 4) % len(hash_bytes)
        chunk = hash_bytes[start:start + 4]
        # Convert to float in range [-1, 1]
        value = int.from_bytes(chunk, "big", signed=True) / (2 ** 31)
        vector.append(value)
    
    return vector


def check_data_exists() -> bool:
    """Check if seed data already exists."""
    result = db.records.find({"labels": ["User"], "limit": 1})
    return result.total > 0


def create_vector_index():
    """Create vector index for Message content if it doesn't exist."""
    existing = db.ai.indexes.find()
    
    for idx in existing.data:
        if idx["label"] == "Message" and idx["propertyName"] == "content":
            print("Vector index already exists")
            return
    
    print("Creating vector index for Message.content...")
    db.ai.indexes.create({
        "label": "Message",
        "propertyName": "content",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    print("Vector index created")


def seed_users():
    """Create demo users."""
    print("\n--- Creating Users ---")
    
    users_data = [
        {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "preferredLanguage": "en"
        },
        {
            "name": "Bob Smith",
            "email": "bob@example.com",
            "preferredLanguage": "en"
        }
    ]
    
    users = {}
    for user_data in users_data:
        # Check if user exists by email
        existing = db.records.find({
            "labels": ["User"],
            "where": {"email": user_data["email"]}
        })
        
        if existing.total > 0:
            users[user_data["email"]] = existing.data[0]
            print(f"User {user_data['name']} already exists")
        else:
            user = db.records.create(
                label="User",
                data={**user_data, "createdAt": datetime.now().isoformat()}
            )
            users[user_data["email"]] = user
            print(f"Created user: {user_data['name']}")
    
    return users


def seed_sessions_and_messages(users: dict):
    """Create sessions and messages for each user."""
    print("\n--- Creating Sessions and Messages ---")
    
    # Conversation templates for realistic data
    conversations = {
        "greeting": [
            {"role": "user", "content": "Hi there! I need some help getting started."},
            {"role": "assistant", "content": "Hello! I'd be happy to help you get started. What would you like to know?"},
            {"role": "user", "content": "Can you walk me through the basic setup process?"},
            {"role": "assistant", "content": "Sure! First, you'll want to create an account and verify your email. Then you can start exploring the dashboard."},
            {"role": "user", "content": "Great, thanks for the quick response!"},
            {"role": "assistant", "content": "You're welcome! Let me know if you have any other questions."}
        ],
        "technical": [
            {"role": "user", "content": "I'm having trouble connecting to the API. Getting a 401 error."},
            {"role": "assistant", "content": "A 401 error typically means there's an authentication issue. Can you check if your API key is valid and not expired?"},
            {"role": "user", "content": "I regenerated the key but still getting the same error."},
            {"role": "assistant", "content": "Try clearing your browser cache and cookies, then attempt the connection again. Also ensure you're sending the key in the correct header format."},
            {"role": "user", "content": "That worked! I was missing the Authorization header prefix."},
            {"role": "assistant", "content": "Excellent! Yes, it needs to be 'Bearer <your-key>'. Is there anything else I can help with?"}
        ],
        "personal": [
            {"role": "user", "content": "Hey, quick question - do you remember what I named my cat?"},
            {"role": "assistant", "content": "Yes, you mentioned your cat's name is Luna. She's a tabby, right?"},
            {"role": "user", "content": "That's right! She just turned 3 years old last week."},
            {"role": "assistant", "content": "Happy birthday to Luna! Would you like me to set a reminder for her next checkup?"},
            {"role": "user", "content": "That would be great, actually."}
        ],
        "preferences": [
            {"role": "user", "content": "I prefer dark mode in the settings. Can you confirm that's what I have?"},
            {"role": "assistant", "content": "Yes, your account is set to dark mode. I can also update your notification preferences if you'd like."},
            {"role": "user", "content": "Actually, could you turn off email notifications? I get too many."},
            {"role": "assistant", "content": "Done! I've disabled email notifications for your account. You can always re-enable them in settings."}
        ]
    }
    
    session_count = 0
    message_count = 0
    
    for email, user in users.items():
        for i, (topic, messages) in enumerate(conversations.items()):
            # Check if session exists
            existing_session = db.records.find({
                "labels": ["Session"],
                "where": {
                    "title": f"{topic.capitalize()} Chat - Session {i+1}",
                    "userId": user.id
                }
            })
            
            if existing_session.total > 0:
                print(f"Session for {user['name']}: {topic} already exists, skipping")
                continue
            
            # Create session
            session = db.records.create(
                label="Session",
                data={
                    "title": f"{topic.capitalize()} Chat - Session {i+1}",
                    "topic": topic,
                    "status": "completed",
                    "startedAt": (datetime.now() - timedelta(days=i*2)).isoformat(),
                    "endedAt": (datetime.now() - timedelta(days=i*2 - 1)).isoformat(),
                    "userId": user.id,
                    "ttl_expires_at": (datetime.now() + timedelta(days=30)).isoformat()
                }
            )
            
            # Link user to session
            db.records.attach(
                source=user,
                target=session,
                options={"type": "HAS_SESSION", "direction": "out"}
            )
            
            session_count += 1
            
            # Create messages with embeddings in a transaction
            with db.transactions.begin() as tx:
                for j, msg_data in enumerate(messages):
                    embedding = generate_embedding(msg_data["content"])
                    
                    message = db.records.create(
                        label="Message",
                        data={
                            **msg_data,
                            "createdAt": (datetime.now() - timedelta(days=i*2, hours=j)).isoformat(),
                            "sessionIndex": j
                        },
                        vectors=[{"propertyName": "content", "vector": embedding}],
                        transaction=tx
                    )
                    
                    # Link session to message
                    db.records.attach(
                        source=session,
                        target=message,
                        options={"type": "CONTAINS", "direction": "out"},
                        transaction=tx
                    )
                    
                    message_count += 1
                    
                    if message_count % 10 == 0:
                        print(f"  Created {message_count} messages...")
            
            print(f"Created session '{session.data['title']}' with {len(messages)} messages")
    
    print(f"\nTotal: {session_count} sessions, {message_count} messages created")
    return session_count, message_count


def seed_entities(users: dict):
    """Create extracted entities for each user."""
    print("\n--- Creating Extracted Entities ---")
    
    entities_data = {
        "alice@example.com": [
            {"type": "pet", "category": "cat", "name": "Luna", "value": "cat named Luna", "detail": "tabby, 3 years old"},
            {"type": "preference", "category": "theme", "name": "dark_mode", "value": "dark mode", "detail": "enabled"},
            {"type": "notification", "category": "email", "name": "email_notifications", "value": "disabled", "detail": "turned off by user request"}
        ],
        "bob@example.com": [
            {"type": "pet", "category": "dog", "name": "Max", "value": "dog named Max", "detail": "golden retriever, 5 years old"},
            {"type": "preference", "category": "language", "name": "english", "value": "English", "detail": "preferred language"}
        ]
    }
    
    entity_count = 0
    
    for email, entities in entities_data.items():
        user = users[email]
        
        for entity_data in entities:
            # Check if entity already exists
            existing = db.records.find({
                "labels": ["ExtractedEntity"],
                "where": {
                    "name": entity_data["name"],
                    "User": {"$relation": {"type": "KNOWS_ABOUT", "direction": "in"}, "id": user.id}
                }
            })
            
            if existing.total > 0:
                print(f"Entity '{entity_data['name']}' for {user['name']} already exists, skipping")
                continue
            
            entity = db.records.create(
                label="ExtractedEntity",
                data={
                    **entity_data,
                    "extractedAt": datetime.now().isoformat(),
                    "confidence": 0.95
                }
            )
            
            # Link user to entity
            db.records.attach(
                source=user,
                target=entity,
                options={"type": "KNOWS_ABOUT", "direction": "out"}
            )
            
            entity_count += 1
            print(f"Created entity: {entity_data['value']} for {user['name']}")
    
    print(f"\nTotal: {entity_count} entities created")
    return entity_count


def main():
    print("=" * 60)
    print("RushDB Chatbot Memory - Seed Script")
    print("=" * 60)
    
    # Check for existing data
    if check_data_exists():
        print("\nSeed data already exists! Skipping...")
        print("Run cleanup first if you want to reseed.")
        
        # Still verify index exists
        create_vector_index()
        return
    
    print("No existing data found. Starting seed...")
    
    # Create vector index
    create_vector_index()
    
    # Seed users
    users = seed_users()
    
    # Seed sessions and messages
    seed_sessions_and_messages(users)
    
    # Seed entities
    seed_entities(users)
    
    print("\n" + "=" * 60)
    print("Seed complete!")
    print("=" * 60)
    print("\nRun 'python main.py' to see the demo in action.")


if __name__ == "__main__":
    main()
