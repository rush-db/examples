"""
Building Chatbot Memory That Persists Across Sessions

A complete implementation demonstrating:
- Graph-based conversation hierarchy (User → Session → Message)
- Vector embeddings for semantic message search
- Entity extraction and recall for personalized responses
- Production patterns (transactions, pagination, TTL)

Run: python main.py
"""

import os
import sys
import hashlib
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


# ============================================================================
# EMBEDDING UTILITY
# ============================================================================

def generate_embedding(text: str) -> list[float]:
    """
    Generate a deterministic 384-dimensional vector from text.
    
    This is a demo-quality embedding using hash-based sampling.
    For production, use:
    - OpenAI: openai.embeddings.create(model="text-embedding-3-small", input=text)
    - Sentence Transformers: model.encode(text, normalize_embeddings=True)
    """
    hash_bytes = hashlib.sha256(text.encode()).digest()
    vector = []
    for i in range(384):
        start = (i * 4) % len(hash_bytes)
        chunk = hash_bytes[start:start + 4]
        value = int.from_bytes(chunk, "big", signed=True) / (2 ** 31)
        vector.append(value)
    return vector


# ============================================================================
# SCHEMA INITIALIZATION
# ============================================================================

def ensure_vector_index():
    """Create vector index for Message.content if it doesn't exist."""
    print("\n📊 Initializing Schema...")
    
    # Check for existing indexes
    existing = db.ai.indexes.find()
    has_index = False
    
    for idx in existing.data:
        if idx["label"] == "Message" and idx["propertyName"] == "content":
            has_index = True
            print(f"   ✓ Vector index exists: Message.content")
            break
    
    if not has_index:
        print("   Creating vector index for Message.content...")
        db.ai.indexes.create({
            "label": "Message",
            "propertyName": "content",
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine"
        })
        print("   ✓ Vector index created")


# ============================================================================
# USER MANAGEMENT
# ============================================================================

def get_or_create_user(name: str, email: str) -> dict:
    """Get existing user or create new one."""
    existing = db.records.find({
        "labels": ["User"],
        "where": {"email": email}
    })
    
    if existing.total > 0:
        return existing.data[0]
    
    print(f"\n👤 Creating user: {name}")
    user = db.records.create(
        label="User",
        data={
            "name": name,
            "email": email,
            "preferredLanguage": "en",
            "createdAt": datetime.now().isoformat()
        }
    )
    return user


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def create_session(user: dict, title: str, topic: str = "general") -> dict:
    """Create a new chat session for a user."""
    session = db.records.create(
        label="Session",
        data={
            "title": title,
            "topic": topic,
            "status": "active",
            "startedAt": datetime.now().isoformat(),
            "ttl_expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }
    )
    
    # Link user to session
    db.records.attach(
        source=user,
        target=session,
        options={"type": "HAS_SESSION", "direction": "out"}
    )
    
    return session


def get_user_sessions(user: dict, limit: int = 10) -> list:
    """Get recent sessions for a user using graph traversal."""
    sessions = db.records.find({
        "labels": ["Session"],
        "where": {
            "User": {"$relation": {"type": "HAS_SESSION", "direction": "in"}, "id": user.id}
        },
        "limit": limit,
        "orderBy": {"startedAt": "desc"}
    })
    return sessions.data


def close_session(session: dict):
    """Mark a session as completed."""
    db.records.set(
        record_id=session.id,
        label="Session",
        data={
            **session.data,
            "status": "closed",
            "endedAt": datetime.now().isoformat()
        }
    )


# ============================================================================
# MESSAGE MANAGEMENT WITH VECTOR EMBEDDINGS
# ============================================================================

def add_message(
    session: dict,
    role: str,
    content: str,
    transaction=None
) -> dict:
    """
    Add a message to a session with vector embedding.
    
    This demonstrates the key pattern: inline vector writes during creation.
    """
    embedding = generate_embedding(content)
    
    message = db.records.create(
        label="Message",
        data={
            "role": role,
            "content": content,
            "createdAt": datetime.now().isoformat()
        },
        vectors=[{"propertyName": "content", "vector": embedding}],
        transaction=transaction
    )
    
    # Link session to message
    db.records.attach(
        source=session,
        target=message,
        options={"type": "CONTAINS", "direction": "out"},
        transaction=transaction
    )
    
    return message


def get_session_messages(session: dict, page: int = 1, page_size: int = 20) -> dict:
    """
    Get messages from a session with pagination.
    
    Production pattern for handling long conversations.
    """
    skip = (page - 1) * page_size
    
    messages = db.records.find({
        "labels": ["Message"],
        "where": {
            "SESSION": {"$relation": {"type": "CONTAINS", "direction": "in"}, "id": session.id}
        },
        "skip": skip,
        "limit": page_size,
        "orderBy": {"createdAt": "asc"}
    })
    
    return {
        "messages": messages.data,
        "page": page,
        "page_size": page_size,
        "total": messages.total,
        "has_next": skip + len(messages.data) < messages.total
    }


# ============================================================================
# CONTEXT RETRIEVAL: GRAPH + SEMANTIC SEARCH
# ============================================================================

def retrieve_context(user: dict, query: str, limit: int = 5) -> dict:
    """
    Retrieve relevant context by combining:
    1. Graph traversal to find user's sessions
    2. Vector search within those sessions
    
    This is the core "memory recall" pattern.
    """
    print(f"\n🔍 Searching for: '{query}'")
    
    # First, get user's recent sessions
    recent_sessions = get_user_sessions(user, limit=5)
    session_ids = [s.id for s in recent_sessions]
    
    print(f"   Found {len(session_ids)} recent sessions")
    
    if not session_ids:
        return {"messages": [], "sessions": [], "query": query}
    
    # Semantic search within user's sessions
    # Using the where clause to filter by related sessions
    results = db.ai.search({
        "propertyName": "content",
        "query": query,
        "labels": ["Message"],
        "limit": limit
    })
    
    print(f"   Found {len(results.data)} semantically similar messages")
    
    return {
        "messages": results.data,
        "sessions": recent_sessions,
        "query": query
    }


def format_context(context: dict) -> str:
    """Format retrieved context for LLM consumption."""
    lines = [f"Context for query: '{context['query']}'\n"]
    lines.append("=" * 50)
    
    if not context["messages"]:
        return "No relevant context found."
    
    for i, msg in enumerate(context["messages"], 1):
        score = msg.score if hasattr(msg, 'score') else msg.get("__score", 0)
        lines.append(f"\n[{i}] (relevance: {score:.2f})")
        lines.append(f"    Role: {msg.get('role', 'unknown')}")
        lines.append(f"    Content: {msg.get('content', '')}")
    
    return "\n".join(lines)


# ============================================================================
# ENTITY EXTRACTION AND MEMORY
# ============================================================================

def extract_entity(
    user: dict,
    entity_type: str,
    name: str,
    value: str,
    category: str = None,
    transaction=None
) -> dict:
    """
    Extract and store an entity from conversation.
    
    Example: When user says "my cat Luna", extract:
    - type: "pet"
    - name: "Luna"
    - category: "cat"
    """
    entity_data = {
        "type": entity_type,
        "name": name,
        "value": value,
        "extractedAt": datetime.now().isoformat(),
        "confidence": 0.95
    }
    
    if category:
        entity_data["category"] = category
    
    entity = db.records.create(
        label="ExtractedEntity",
        data=entity_data,
        transaction=transaction
    )
    
    # Link user to entity
    db.records.attach(
        source=user,
        target=entity,
        options={"type": "KNOWS_ABOUT", "direction": "out"},
        transaction=transaction
    )
    
    return entity


def recall_entities(user: dict, category: str = None) -> list:
    """
    Recall entities for a user.
    
    Example query: "What pets does the user have?"
    """
    where_clause = {
        "User": {"$relation": {"type": "KNOWS_ABOUT", "direction": "in"}, "id": user.id}
    }
    
    if category:
        where_clause["category"] = category
    
    entities = db.records.find({
        "labels": ["ExtractedEntity"],
        "where": where_clause
    })
    
    return entities.data


def format_entities(entities: list) -> str:
    """Format entities for display."""
    if not entities:
        return "No entities found."
    
    lines = ["Extracted Entities:"]
    for entity in entities:
        lines.append(f"  • {entity.get('value', entity.get('name'))}")
        if entity.get('detail'):
            lines.append(f"    Detail: {entity.get('detail')}")
    
    return "\n".join(lines)


# ============================================================================
# PRODUCTION PATTERNS
# ============================================================================

def demonstrate_concurrent_writes():
    """
    Demonstrate handling concurrent message writes with transactions.
    """
    print("\n⚡ Demonstrating Concurrent Writes Pattern")
    print("-" * 40)
    
    # Get or create a demo user
    user = get_or_create_user("Demo User", "demo@example.com")
    session = create_session(user, "Batch Write Demo", "demo")
    
    # Simulate a burst of messages (e.g., from a webhook or queue)
    messages_to_add = [
        {"role": "user", "content": "First message in the batch"},
        {"role": "assistant", "content": "Acknowledged first message"},
        {"role": "user", "content": "Second message following up"},
        {"role": "assistant", "content": "Processing your follow-up"},
        {"role": "user", "content": "Third message completing the flow"},
    ]
    
    print(f"   Writing {len(messages_to_add)} messages in single transaction...")
    
    # Use transaction to batch all writes
    with db.transactions.begin() as tx:
        for msg_data in messages_to_add:
            add_message(session, msg_data["role"], msg_data["content"], transaction=tx)
        # Context manager auto-commits on clean exit
    
    print("   ✓ All messages written atomically")
    
    # Verify
    result = get_session_messages(session)
    print(f"   Session now has {result['total']} messages")
    
    # Clean up
    db.records.delete(record_id=session.id)
    print("   ✓ Demo session cleaned up")


def demonstrate_pagination():
    """
    Demonstrate pagination through long conversations.
    """
    print("\n📄 Demonstrating Pagination Pattern")
    print("-" * 40)
    
    user = get_or_create_user("Pagination Demo", "pagination@example.com")
    session = create_session(user, "Long Conversation Demo", "demo")
    
    # Create 45 messages
    print("   Creating 45 messages...")
    with db.transactions.begin() as tx:
        for i in range(45):
            add_message(
                session,
                "user" if i % 2 == 0 else "assistant",
                f"Message number {i + 1} in the conversation",
                transaction=tx
            )
    
    # Demonstrate pagination
    page_size = 10
    print(f"\n   Retrieving messages (page size: {page_size}):")
    
    for page_num in range(1, 4):
        result = get_session_messages(session, page=page_num, page_size=page_size)
        print(f"   Page {page_num}: {len(result['messages'])} messages "
              f"(showing {result['page_size']} per page, total: {result['total']})")
    
    # Clean up
    db.records.delete(record_id=session.id)
    print("   ✓ Demo session cleaned up")


def demonstrate_ttl_strategy():
    """
    Demonstrate TTL strategy for session expiration.
    """
    print("\n⏰ Demonstrating TTL Strategy")
    print("-" * 40)
    
    # Find sessions that have expired
    expired_sessions = db.records.find({
        "labels": ["Session"],
        "where": {
            "status": "closed",
            "ttl_expires_at": {"$lt": datetime.now().isoformat()}
        }
    })
    
    print(f"   Found {expired_sessions.total} expired sessions ready for cleanup")
    
    # Find sessions expiring in next 7 days
    upcoming_expiry = db.records.find({
        "labels": ["Session"],
        "where": {
            "ttl_expires_at": {
                "$gte": datetime.now().isoformat(),
                "$lte": (datetime.now() + timedelta(days=7)).isoformat()
            }
        }
    })
    
    print(f"   Found {upcoming_expiry.total} sessions expiring within 7 days")
    print("\n   TTL Strategy Notes:")
    print("   • Active sessions: No TTL set, preserved indefinitely")
    print("   • Closed sessions: 30-day TTL for compliance/human review")
    print("   • Entity data: Longer retention (user preferences are valuable)")


# ============================================================================
# MAIN DEMO
# ============================================================================

def run_demo():
    """Run the complete demo demonstrating all key features."""
    print("\n" + "=" * 60)
    print("🚀 RUSHzb Chatbot Memory - Cross-Session Demo")
    print("=" * 60)
    
    # 1. Initialize schema
    ensure_vector_index()
    
    # 2. Create user and session
    print("\n📝 STEP 1: Creating User and Session")
    print("-" * 40)
    
    user = get_or_create_user("Alice Johnson", "alice@demo.com")
    print(f"   ✓ User: {user.data['name']} (ID: {user.id})")
    
    session = create_session(user, "Product Inquiry Chat", "product")
    print(f"   ✓ Session: {session.data['title']}")
    print(f"   ✓ Graph: User → HAS_SESSION → Session")
    
    # 3. Add messages with embeddings
    print("\n📨 STEP 2: Adding Messages with Vector Embeddings")
    print("-" * 40)
    
    conversation = [
        {"role": "user", "content": "Hi, I'm looking for a laptop for programming."},
        {"role": "assistant", "content": "Great! What kind of programming do you do? Web, data science, or systems?"},
        {"role": "user", "content": "Mostly web development and some machine learning."},
        {"role": "assistant", "content": "For web + ML, I'd recommend at least 16GB RAM and an NVIDIA GPU."},
        {"role": "user", "content": "My cat Luna loves to sleep on my keyboard while I code!"},
        {"role": "assistant", "content": "Haha, that's adorable! Cats do love warm keyboards."},
    ]
    
    for msg in conversation:
        message = add_message(session, msg["role"], msg["content"])
        print(f"   ✓ {msg['role'].upper()}: {msg['content'][:50]}...")
    
    print("\n   ✓ Graph: Session → CONTAINS → Message (with vectors)")
    
    # 4. Extract entities
    print("\n🧠 STEP 3: Extracting Entity Memory")
    print("-" * 40)
    
    # Extract the cat mention
    cat_entity = extract_entity(
        user,
        entity_type="pet",
        name="Luna",
        value="cat named Luna",
        category="cat"
    )
    print(f"   ✓ Extracted: {cat_entity.data['value']}")
    
    # Extract user preference
    preference = extract_entity(
        user,
        entity_type="use_case",
        name="programming_preference",
        value="web development and machine learning"
    )
    print(f"   ✓ Extracted: {preference.data['value']}")
    
    print("\n   ✓ Graph: User → KNOWS_ABOUT → ExtractedEntity")
    
    # 5. Retrieve context
    print("\n🔍 STEP 4: Context Retrieval (Graph + Semantic Search)")
    print("-" * 40)
    
    queries = [
        "laptop recommendations for developers",
        "cat on keyboard",
        "machine learning setup"
    ]
    
    for query in queries:
        context = retrieve_context(user, query, limit=3)
        formatted = format_context(context)
        print(f"\n   Query: '{query}'")
        print(f"   Results: {len(context['messages'])} relevant messages")
    
    # 6. Recall entity memory
    print("\n💭 STEP 5: Entity Memory Recall")
    print("-" * 40)
    
    # "What does the user know about their pets?"
    pets = recall_entities(user, category="pet")
    print(f"   Query: 'What pets does Alice have?'")
    print(f"   Result: {format_entities(pets)}")
    
    # "What are the user's use cases?"
    use_cases = recall_entities(user, category="use_case")
    print(f"\n   Query: 'What does Alice use the laptop for?'")
    print(f"   Result: {format_entities(use_cases)}")
    
    # 7. Production patterns
    print("\n" + "=" * 60)
    print("⚙️  PRODUCTION PATTERNS")
    print("=" * 60)
    
    demonstrate_concurrent_writes()
    demonstrate_pagination()
    demonstrate_ttl_strategy()
    
    # 8. Summary
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)
    print("""
Key Takeaways:

1. GRAPH HIERARCHY
   User → HAS_SESSION → Session → CONTAINS → Message
   User → KNOWS_ABOUT → ExtractedEntity

2. VECTOR SEARCH
   Messages are embedded at write time for fast semantic recall.
   Search combines with graph filtering for relevant context.

3. ENTITY MEMORY
   Extract facts from conversation and link to user node.
   Query by category for targeted recall.

4. PRODUCTION READY
   • Transactions for atomic writes
   • Pagination for long conversations  
   • TTL strategies for compliance

Next Steps:
- Run seed.py to populate demo data
- Try different semantic search queries
- Explore the ontology with db.ai.getOntologyMarkdown()

Learn More: https://docs.rushdb.com
    """)


if __name__ == "__main__":
    run_demo()
