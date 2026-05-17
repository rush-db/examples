"""
Seed script: Generates mock conversation history for the context window demo.

This creates realistic agent conversation data to demonstrate how RushDB
manages long-horizon interactions. The data represents a multi-session
project planning conversation.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(api_key)

# Initialize embedding model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Mock conversation data representing a multi-session project planning
CONVERSATIONS = [
    {
        "session_id": "session_001",
        "title": "Initial Project Planning",
        "date": (datetime.now() - timedelta(days=14)).isoformat(),
        "messages": [
            {"role": "user", "content": "We need to plan the Q2 product launch. Can you help outline the key milestones?"},
            {"role": "assistant", "content": "Of course! Let's start by identifying the main phases: discovery, development, QA, and launch. What are your team constraints?"},
            {"role": "user", "content": "We have 8 weeks, a team of 5 engineers, and a fixed budget of $150K. Marketing needs 2 weeks lead time before launch."},
            {"role": "assistant", "content": "Got it. Based on that, I'd recommend: Week 1-2 discovery and architecture, Week 3-5 development, Week 6 QA and staging, Week 7 final polish, Week 8 launch."},
            {"role": "user", "content": "That timeline seems tight. Can we reduce scope?"},
            {"role": "assistant", "content": "We could cut either the mobile app (saving 2 weeks) or delay the internationalization feature. Which is more important for Q2?"},
        ],
        "summary": "Initial planning session establishing 8-week timeline for Q2 launch with $150K budget and 5 engineers. Core debate around scope reduction options."
    },
    {
        "session_id": "session_002",
        "title": "Technical Architecture Discussion",
        "date": (datetime.now() - timedelta(days=10)).isoformat(),
        "messages": [
            {"role": "user", "content": "Let's discuss the technical stack. We're leaning towards microservices but our team has limited K8s experience."},
            {"role": "assistant", "content": "That's a valid concern. You have three options: 1) Full microservices with training, 2) Modular monolith to start with planned extraction, 3) Serverless approach. Option 2 is lowest risk for your timeline."},
            {"role": "user", "content": "What about database choices? We need to handle 10K concurrent users."},
            {"role": "assistant", "content": "PostgreSQL should handle that easily with proper indexing. For reads, consider Redis caching. I'd avoid MongoDB unless you have complex nested queries."},
            {"role": "user", "content": "We need real-time features for the dashboard. Recommendations?"},
            {"role": "assistant", "content": "WebSocket via Socket.io or native. For scaling, consider Redis pub/sub as a message broker. This is well-tested for your scale."},
        ],
        "summary": "Technical stack decision-making. Team leaning towards modular monolith architecture with PostgreSQL and Redis for caching. Real-time dashboard via WebSocket with Redis pub/sub."
    },
    {
        "session_id": "session_003",
        "title": "Budget and Resource Allocation",
        "date": (datetime.now() - timedelta(days=7)).isoformat(),
        "messages": [
            {"role": "user", "content": "Finance approved our budget. But we need to account for $20K in third-party services."},
            {"role": "assistant", "content": "That leaves $130K for internal resources. For 5 engineers over 8 weeks, that's approximately $32.5K per engineer including all costs."},
            {"role": "user", "content": "Should we hire contractors for the QA phase?"},
            {"role": "assistant", "content": "Recommended. Budget $15K for 2 contractors for 3 weeks during QA. This gives you 7 person-weeks of QA coverage without long-term commitment."},
            {"role": "user", "content": "What about cloud infrastructure costs?"},
            {"role": "assistant", "content": "Estimate $8K for 8 weeks on AWS with proper auto-scaling. Use reserved instances for base load, on-demand for spikes. Include $2K for monitoring tools."},
        ],
        "summary": "Budget allocation finalized. $150K total: $20K third-party services, $120K internal, $8K cloud infra, $2K tools. Contractors recommended for QA phase."
    }
]

def seed_conversations():
    """Seed conversation history into RushDB."""
    print("\n=== Seeding Conversation History ===\n")
    
    # Check if already seeded
    existing = db.records.find({"labels": ["CONVERSATION"], "limit": 1})
    if existing.total > 0:
        print(f"Found {existing.total} existing conversation(s). Skipping seed.")
        return existing.data
    
    created = []
    for i, convo in enumerate(CONVERSATIONS):
        # Create conversation record
        conversation = db.records.create(
            label="CONVERSATION",
            data={
                "sessionId": convo["session_id"],
                "title": convo["title"],
                "date": convo["date"],
                "messageCount": len(convo["messages"]),
                "messages": convo["messages"],
                "summary": convo["summary"]
            }
        )
        created.append(conversation)
        print(f"  Created: {convo['title']}")
        
        if (i + 1) % 100 == 0:
            print(f"  ... {i + 1} conversations seeded")
    
    print(f"\n✅ Seeded {len(created)} conversations")
    return created

def create_chunks():
    """Create semantic chunks from conversation content."""
    print("\n=== Creating Semantic Chunks ===\n")
    
    # Check if already chunked
    existing = db.records.find({"labels": ["CHUNK"], "limit": 1})
    if existing.total > 0:
        print(f"Found {existing.total} existing chunks. Skipping chunk creation.")
        return
    
    conversations = db.records.find({"labels": ["CONVERSATION"]})
    chunk_data = []
    
    for convo in conversations.data:
        messages = convo.get("messages", [])
        
        # Create chunks from message pairs (context window friendly)
        for i in range(0, len(messages) - 1, 2):
            pair = messages[i:i + 2]
            chunk_text = " ".join([f"{m['role']}: {m['content']}" for m in pair])
            
            # Create embeddings
            embedding = model.encode(chunk_text).tolist()
            
            chunk_data.append({
                "text": chunk_text,
                "embedding": embedding,
                "sessionId": convo.get("sessionId"),
                "chunkIndex": i // 2
            })
    
    # Batch create chunks with vectors
    for chunk in chunk_data:
        db.records.create(
            label="CHUNK",
            data={
                "text": chunk["text"],
                "sessionId": chunk["sessionId"],
                "chunkIndex": chunk["chunkIndex"]
            },
            vectors=[{"propertyName": "text", "vector": chunk["embedding"]}]
        )
    
    print(f"✅ Created {len(chunk_data)} semantic chunks")

def main():
    print("Starting seed process...")
    
    # Seed conversations
    conversations = seed_conversations()
    
    # Create semantic chunks with embeddings
    create_chunks()
    
    print("\n=== Seed Complete ===")

if __name__ == "__main__":
    main()
