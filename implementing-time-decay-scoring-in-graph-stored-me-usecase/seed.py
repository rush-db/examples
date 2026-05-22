#!/usr/bin/env python3
"""
Seed Script: Generate Conversational Memory Data

Creates realistic conversational memory data for a chatbot agent,
including:
- Conversation memories with timestamps
- User entities
- Topic entities  
- Graph relationships between entities and memories
- Vector embeddings for semantic search

This script is idempotent: safe to run multiple times.
It checks for existing data and skips seeding if data already exists.
"""

import os
import sys
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize Faker for realistic data
fake = Faker()
Faker.seed(42)
random.seed(42)

# Configuration
DECAY_LAMBDA = float(os.getenv('DECAY_LAMBDA', '0.1'))
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')


def get_or_create_label(db: RushDB, name: str, description: str = "") -> dict:
    """Get existing label or create it."""
    labels = db.labels.find()
    label_names = [l.name for l in labels.data] if hasattr(labels, 'data') else [l['name'] for l in labels]
    
    if name in label_names:
        return {'name': name}
    
    # Create a record with this label to establish it
    record = db.records.create(label=name, data={'description': description})
    db.records.delete(record_id=record.id)
    return {'name': name}


def check_data_exists(db: RushDB) -> bool:
    """Check if seed data already exists."""
    result = db.records.find({'labels': ['USER'], 'limit': 1})
    if hasattr(result, 'data'):
        return len(result.data) > 0
    return False


def generate_conversation_content(topic: str, user_name: str, days_ago: int) -> dict:
    """Generate realistic conversation content based on topic."""
    templates = {
        'technical_support': [
            f"Hey {user_name}, I'm having trouble with the API authentication flow. Getting 401s randomly.",
            f"Thanks for the help earlier. The token refresh fixed the issue.",
            f"Can you explain how the rate limiting works again?"
        ],
        'billing': [
            f"Hi, I noticed a charge on my account that looks incorrect.",
            f"The refund went through, thanks!",
            f"Can you send me the invoice for last month?"
        ],
        'feature_request': [
            f"Would it be possible to add batch export functionality?",
            f"Love the new dashboard! The charts are really helpful.",
            f"Any plans for a mobile app?"
        ],
        'data_analysis': [
            f"I'm trying to analyze user behavior patterns from last quarter.",
            f"The CSV export is missing some columns, can you check?",
            f"How do I filter by date range in the analytics view?"
        ],
        'account': [
            f"I need to update my company name in the account settings.",
            f"How do I add a team member to my workspace?",
            f"Can you help me transfer ownership of a project?"
        ]
    }
    
    category = random.choice(list(templates.keys()))
    messages = random.sample(templates[category], k=min(3, len(templates[category])))
    
    return {
        'topic': topic,
        'category': category,
        'user_message': messages[0],
        'agent_response': messages[1] if len(messages) > 1 else "I'll look into that for you.",
        'resolution': 'resolved' if random.random() > 0.3 else 'pending'
    }


def create_vector_index(db: RushDB) -> str:
    """Create a vector index for memory content."""
    try:
        # Check for existing index
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            if idx.get('label') == 'MEMORY' and idx.get('propertyName') == 'content':
                return idx['__id']
        
        # Create new index
        index = db.ai.indexes.create({
            'label': 'MEMORY',
            'propertyName': 'content',
            'sourceType': 'external',
            'dimensions': 384,
            'similarityFunction': 'cosine'
        })
        return index.data['__id']
    except Exception as e:
        print(f"Index creation warning (may already exist): {e}")
        return None


def main():
    """Main seeding function."""
    print("=" * 60)
    print("CONVERSATIONAL MEMORY SEED SCRIPT")
    print("=" * 60)
    
    # Initialize RushDB
    api_key = os.getenv('RUSHDB_API_KEY')
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not set in environment")
        sys.exit(1)
    
    db = RushDB(api_key, url=os.getenv('RUSHDB_URL'))
    
    # Check for existing data
    if check_data_exists(db):
        print("\n✓ Seed data already exists. Skipping seeding.")
        print("  To re-seed, delete existing data first or use a fresh project.")
        return
    
    print(f"\n1. Setting up labels...")
    labels = ['USER', 'MEMORY', 'TOPIC', 'TOOL', 'SESSION']
    for label in labels:
        get_or_create_label(db, label)
    print(f"   Created labels: {', '.join(labels)}")
    
    # Initialize embedding model
    print(f"\n2. Loading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("   Model loaded successfully")
    
    # Create vector index
    print("\n3. Creating vector index...")
    index_id = create_vector_index(db)
    print(f"   Index ID: {index_id}")
    
    # Generate users
    print("\n4. Generating users...")
    users = []
    user_data = [
        {'name': 'Alice Chen', 'email': 'alice.chen@techcorp.io', 'company': 'TechCorp', 'role': 'Engineering Lead'},
        {'name': 'Bob Martinez', 'email': 'bob.martinez@startup.co', 'company': 'StartupCo', 'role': 'CTO'},
        {'name': 'Carol Singh', 'email': 'carol.singh@enterprise.com', 'company': 'EnterpriseInc', 'role': 'Data Analyst'},
        {'name': 'David Kim', 'email': 'david.kim@analytics.io', 'company': 'AnalyticsPro', 'role': 'Product Manager'},
        {'name': 'Emma Wilson', 'email': 'emma.wilson@ai.company', 'company': 'AIResearch', 'role': 'Research Scientist'},
    ]
    
    for i, udata in enumerate(user_data):
        user = db.records.create(label='USER', data=udata)
        users.append(user)
        if (i + 1) % 100 == 0:
            print(f"   Created {i + 1} users...")
    print(f"   Created {len(users)} users total")
    
    # Generate topics
    print("\n5. Generating topics...")
    topics = []
    topic_data = [
        'API Authentication', 'Rate Limiting', 'Billing', 'Data Export',
        'Team Management', 'Webhooks', 'Analytics', 'Machine Learning',
        'Security', 'Integrations', 'Performance', 'Documentation'
    ]
    for topic in topic_data:
        topic_record = db.records.create(label='TOPIC', data={'name': topic})
        topics.append(topic_record)
    print(f"   Created {len(topics)} topics")
    
    # Generate tools used
    print("\n6. Generating tools...")
    tools = []
    tool_data = [
        {'name': 'api_diagnostics', 'description': 'Debug API issues'},
        {'name': 'billing_lookup', 'description': 'Check billing status'},
        {'name': 'data_exporter', 'description': 'Export data in various formats'},
        {'name': 'user_manager', 'description': 'Manage team members'},
        {'name': 'analytics_dashboard', 'description': 'View usage analytics'},
    ]
    for tool in tool_data:
        tool_record = db.records.create(label='TOOL', data=tool)
        tools.append(tool_record)
    print(f"   Created {len(tools)} tools")
    
    # Generate memory records with graph relationships and vectors
    print("\n7. Generating memory records...")
    
    # Time range: from 60 days ago to now
    now = datetime.now()
    base_time = now - timedelta(days=60)
    
    memories_created = 0
    vector_items = []
    
    for user in users:
        # Each user has 8-15 conversations
        num_conversations = random.randint(8, 15)
        
        for conv_idx in range(num_conversations):
            # Random timestamp with more recent bias
            days_ago = random.expovariate(1/15)  # Exponential distribution
            days_ago = min(days_ago, 60)  # Cap at 60 days
            
            timestamp = base_time + timedelta(
                days=60-days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Generate conversation content
            topic = random.choice(topics)
            content_data = generate_conversation_content(
                topic.data.get('name', 'General'),
                user.data.get('name', 'User'),
                int(days_ago)
            )
            
            # Combined content for embedding
            content = f"Topic: {content_data['topic']}. Category: {content_data['category']}. " \
                      f"User: {content_data['user_message']} Agent: {content_data['agent_response']}"
            
            # Create memory record
            memory = db.records.create(label='MEMORY', data={
                'content': content,
                'topic': content_data['topic'],
                'category': content_data['category'],
                'user_message': content_data['user_message'],
                'agent_response': content_data['agent_response'],
                'resolution': content_data['resolution'],
                'timestamp': timestamp.isoformat(),
                'days_ago': int(days_ago),
            })
            
            # Attach relationships (graph edges)
            db.records.attach(source=memory, target=user, options={'type': 'BELONGS_TO'})
            db.records.attach(source=memory, target=topic, options={'type': 'ABOUT'})
            
            # Link to tools used (random subset)
            used_tools = random.sample(tools, k=random.randint(1, 3))
            for tool in used_tools:
                db.records.attach(source=memory, target=tool, options={'type': 'USED_TOOL'})
            
            # Prepare vector for indexing
            embedding = model.encode(content).tolist()
            vector_items.append({
                'recordId': memory.id,
                'vector': embedding
            })
            
            memories_created += 1
            
            if memories_created % 20 == 0:
                print(f"   Created {memories_created} memory records...")
    
    print(f"   Created {memories_created} memory records total")
    
    # Upsert vectors to index
    print("\n8. Indexing vectors...")
    if index_id and vector_items:
        batch_size = 100
        for i in range(0, len(vector_items), batch_size):
            batch = vector_items[i:i+batch_size]
            db.ai.indexes.upsert_vectors(index_id, {'items': batch})
            print(f"   Indexed {min(i+batch_size, len(vector_items))}/{len(vector_items)} vectors...")
    print("   Vector indexing complete")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"  Users:     {len(users)}")
    print(f"  Topics:    {len(topics)}")
    print(f"  Tools:     {len(tools)}")
    print(f"  Memories:  {memories_created}")
    print(f"  Vectors:   {len(vector_items)}")
    print("\nYou can now run `python main.py` to demonstrate time-decay scoring.")
    print("=" * 60)


if __name__ == '__main__':
    main()
