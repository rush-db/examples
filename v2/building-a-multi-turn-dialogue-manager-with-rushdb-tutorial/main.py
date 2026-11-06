"""
Building a Multi-Turn Dialogue Manager with RushDB State Tracking

This example demonstrates how to build a production-ready dialogue manager
that maintains conversation state across multiple turns. It showcases RushDB's
capabilities for storing and querying conversation data as a property graph.

Key Features Demonstrated:
1. Session management (create, track, query sessions)
2. Message history (store exchanges with full metadata)
3. State tracking (intents, entities, conversation context)
4. Multi-turn context retrieval (load relevant history)
5. Relationship-based queries (traverse conversation graph)
6. Transaction safety (atomic operations)
"""

import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()


class DialogueManager:
    """
    A multi-turn dialogue manager that uses RushDB for stateful conversation management.
    
    This class demonstrates best practices for:
    - Creating and managing conversation sessions
    - Storing message history with relationships
    - Tracking conversation state (context, entities, intents)
    - Retrieving multi-turn context for intelligent responses
    """
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def create_session(self, user_id: str, channel: str = "web") -> object:
        """
        Create a new conversation session.
        
        Args:
            user_id: External user identifier
            channel: Communication channel (web, mobile, api)
        
        Returns:
            Session record with attached user relationship
        """
        session_id = f"SES-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now()
        
        # Use transaction to atomically create session and link to user
        with self.db.transactions.begin() as tx:
            # Create the session record
            session = self.db.records.create(
                label="Session",
                data={
                    "sessionId": session_id,
                    "channel": channel,
                    "status": "active",
                    "startedAt": now.isoformat(),
                    "lastActivityAt": now.isoformat(),
                    "turnCount": 0,
                    "metadata": {
                        "timezone": "UTC",
                        "locale": "en-US"
                    }
                },
                transaction=tx
            )
            
            # If user exists, attach relationship
            # In production, you'd look up the user first
            existing_users = self.db.records.find({
                "labels": ["User"],
                "limit": 1
            })
            if existing_users.data:
                self.db.records.attach(
                    source=existing_users.data[0],
                    target=session,
                    options={"type": "HAS_SESSION"},
                    transaction=tx
                )
        
        print(f"\n✓ Created session: {session_id}")
        return session
    
    def add_message(
        self,
        session,
        role: str,
        content: str,
        metadata: dict = None
    ) -> object:
        """
        Add a message to a session with automatic state tracking.
        
        Args:
            session: Session record to add message to
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional message metadata
        
        Returns:
            Message record with relationships
        """
        now = datetime.now()
        turn_number = session.data.get("turnCount", 0) + 1
        
        message_data = {
            "role": role,
            "content": content,
            "timestamp": now.isoformat(),
            "turnNumber": turn_number,
            "messageId": str(uuid.uuid4())
        }
        
        # Add metadata if provided
        if metadata:
            message_data["metadata"] = metadata
        
        with self.db.transactions.begin() as tx:
            # Create message
            message = self.db.records.create(
                label="Message",
                data=message_data,
                transaction=tx
            )
            
            # Link message to session
            self.db.records.attach(
                source=session,
                target=message,
                options={"type": "CONTAINS"},
                transaction=tx
            )
            
            # Update session state
            session.data["turnCount"] = turn_number
            session.data["lastActivityAt"] = now.isoformat()
            session.data["lastMessageRole"] = role
        
        return message
    
    def track_state(
        self,
        session,
        state_type: str,
        state_data: dict
    ) -> object:
        """
        Track conversation state (intents, entities, flags).
        
        This creates a Context record linked to the session,
        allowing for stateful conversation management.
        
        Args:
            session: Session to track state for
            state_type: Type of state (intent, entities, flags, etc.)
            state_data: State data to store
        
        Returns:
            Context record linked to session
        """
        context = self.db.records.create(
            label="Context",
            data={
                "type": state_type,
                "data": state_data,
                "createdAt": datetime.now().isoformat(),
                "sessionId": session.data["sessionId"]
            }
        )
        
        # Link context to session
        self.db.records.attach(
            source=session,
            target=context,
            options={"type": "HAS_STATE"}
        )
        
        return context
    
    def get_conversation_history(
        self,
        session,
        limit: int = 20
    ) -> list:
        """
        Retrieve conversation history for a session.
        
        Args:
            session: Session to get history for
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of Message records ordered by turn number
        """
        messages = self.db.records.find({
            "labels": ["Message"],
            "where": {
                "Session": {
                    "$relation": {"type": "CONTAINS", "direction": "in"},
                    "sessionId": session.data["sessionId"]
                }
            },
            "limit": limit,
            "orderBy": {"turnNumber": "asc"}
        })
        
        return messages.data
    
    def get_session_context(self, session) -> dict:
        """
        Retrieve all tracked state for a session.
        
        Args:
            session: Session to get context for
        
        Returns:
            Dictionary of context types and their data
        """
        contexts = self.db.records.find({
            "labels": ["Context"],
            "where": {
                "Session": {
                    "$relation": {"type": "HAS_STATE", "direction": "in"},
                    "sessionId": session.data["sessionId"]
                }
            }
        })
        
        # Organize by type
        organized = {}
        for ctx in contexts.data:
            ctx_type = ctx.get("type", "unknown")
            if ctx_type not in organized:
                organized[ctx_type] = []
            organized[ctx_type].append(ctx.get("data", {}))
        
        return organized
    
    def find_user_sessions(
        self,
        user_name: str = None,
        status: str = "active",
        limit: int = 10
    ) -> list:
        """
        Find sessions for a user, optionally filtered by status.
        
        Args:
            user_name: Filter by user name (optional)
            status: Filter by session status
            limit: Maximum sessions to return
        
        Returns:
            List of Session records
        """
        where_clause = {"status": status}
        
        if user_name:
            where_clause["User"] = {"name": user_name}
        
        sessions = self.db.records.find({
            "labels": ["Session"],
            "where": where_clause,
            "limit": limit,
            "orderBy": {"lastActivityAt": "desc"}
        })
        
        return sessions.data
    
    def end_session(self, session) -> object:
        """
        Mark a session as ended with final metadata.
        
        Args:
            session: Session to end
        
        Returns:
            Updated session record
        """
        now = datetime.now()
        started = datetime.fromisoformat(session.data["startedAt"])
        duration = (now - started).total_seconds()
        
        # Update session with end metadata
        self.db.records.set(
            target=session,
            label="Session",
            data={
                **session.data,
                "status": "ended",
                "endedAt": now.isoformat(),
                "durationSeconds": duration,
                "finalTurnCount": session.data.get("turnCount", 0)
            }
        )
        
        # Refresh session data
        return self.db.records.find_by_id(session.id)


def run_demo():
    """Run the complete dialogue manager demonstration."""
    
    print("=" * 60)
    print("Multi-Turn Dialogue Manager with RushDB State Tracking")
    print("=" * 60)
    
    # Initialize RushDB connection
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\n❌ Error: RUSHDB_API_KEY not found")
        print("Please copy .env.example to .env and add your API key")
        return
    
    db = RushDB(api_key)
    manager = DialogueManager(db)
    
    print("\n✓ Connected to RushDB")
    
    # =========================================================================
    # DEMO SECTION 1: Create a new session
    # =========================================================================
    print("\n" + "-" * 60)
    print("DEMO 1: Creating a New Conversation Session")
    print("-" * 60)
    
    session = manager.create_session(
        user_id="user-123",
        channel="web"
    )
    print(f"  Session ID: {session.data['sessionId']}")
    print(f"  Channel: {session.data['channel']}")
    print(f"  Started: {session.data['startedAt']}")
    
    # =========================================================================
    # DEMO SECTION 2: Simulate a conversation
    # =========================================================================
    print("\n" + "-" * 60)
    print("DEMO 2: Simulating Multi-Turn Conversation")
    print("-" * 60)
    
    conversation = [
        {
            "role": "user",
            "content": "Hi, I want to check on my recent order.",
            "intent": "order_inquiry"
        },
        {
            "role": "assistant",
            "content": "Hello! I'd be happy to help. What's your order number?"
        },
        {
            "role": "user",
            "content": "It's ORDER-12345.",
            "intent": "provide_order_id",
            "entities": {"orderId": "ORDER-12345"}
        },
        {
            "role": "assistant",
            "content": "I found it. Your order is being processed and will ship in 2 days."
        },
        {
            "role": "user",
            "content": "Great, can you give me a tracking number when it ships?",
            "intent": "request_tracking"
        },
        {
            "role": "assistant",
            "content": "Absolutely! You'll receive an email with tracking info once it ships."
        }
    ]
    
    for turn in conversation:
        metadata = {}
        if "intent" in turn:
            metadata["intent"] = turn["intent"]
        if "entities" in turn:
            metadata["entities"] = turn["entities"]
        
        message = manager.add_message(
            session=session,
            role=turn["role"],
            content=turn["content"],
            metadata=metadata if metadata else None
        )
        
        prefix = "👤" if turn["role"] == "user" else "🤖"
        print(f"  {prefix} [{turn['role']}]: {turn['content'][:50]}...")
    
    # =========================================================================
    # DEMO SECTION 3: Track conversation state
    # =========================================================================
    print("\n" + "-" * 60)
    print("DEMO 3: Tracking Conversation State")
    print("-" * 60)
    
    # Track detected intents
    manager.track_state(
        session=session,
        state_type="intent_sequence",
        state_data={
            "intents": ["order_inquiry", "provide_order_id", "request_tracking"],
            "confirmed_order": "ORDER-12345"
        }
    )
    print("  ✓ Tracked intent sequence")
    
    # Track entities
    manager.track_state(
        session=session,
        state_type="entities",
        state_data={
            "order_id": "ORDER-12345",
            "user_requested_tracking": True
        }
    )
    print("  ✓ Tracked extracted entities")
    
    # Track flags
    manager.track_state(
        session=session,
        state_type="flags",
        state_data={
            "awaiting_tracking": True,
            "customer_satisfied": True
        }
    )
    print("  ✓ Tracked conversation flags")
    
    # =========================================================================
    # DEMO SECTION 4: Retrieve conversation context
    # =========================================================================
    print("\n" + "-" * 60)
    print("DEMO 4: Retrieving Multi-Turn Context")
    print("-" * 60)
    
    # Get conversation history
    history = manager.get_conversation_history(session)
    print(f"\n  Conversation History ({len(history)} messages):")
    for msg in history:
        role_icon = "👤" if msg.get("role") == "user" else "🤖"
        print(f"    {role_icon} Turn {msg.get('turnNumber')}: {msg.get('content')[:40]}...")
    
    # Get all tracked state
    print("\n  Tracked State:")
    context = manager.get_session_context(session)
    for state_type, state_items in context.items():
        print(f"    • {state_type}: {len(state_items)} entries")
    
    # =========================================================================
    # DEMO SECTION 5: Query sessions across the database
    # =========================================================================
    print("\n" + "-" * 60)
    print("DEMO 5: Querying Sessions Across Database")
    print("-" * 60)
    
    # Find all active sessions
    active_sessions = manager.find_user_sessions(status="active", limit=5)
    print(f"\n  Active Sessions Found: {len(active_sessions)}")
    for sess in active_sessions:
        print(f"    • {sess.data['sessionId']} - {sess.data['turnCount']} turns")
    
    # =========================================================================
    # DEMO SECTION 6: End session and view final state
    # =========================================================================
    print("\n" + "-" * 60)
    print("DEMO 6: Ending Session and Viewing Final State")
    print("-" * 60)
    
    ended_session = manager.end_session(session)
    print(f"\n  Session Ended:")
    print(f"    • Status: {ended_session.data['status']}")
    print(f"    • Total Turns: {ended_session.data.get('finalTurnCount', 0)}")
    print(f"    • Duration: {ended_session.data.get('durationSeconds', 0):.0f} seconds")
    
    # =========================================================================
    # DEMO SECTION 7: Demonstrate context-aware response generation
    # =========================================================================
    print("\n" + "-" * 60)
    print("DEMO 7: Context-Aware Response (Simulated AI)")
    print("-" * 60)
    
    # Simulate loading context for a new user message
    context = manager.get_session_context(session)
    entities = context.get("entities", [{}])[0] if context.get("entities") else {}
    
    user_input = "Can you change the shipping address?"
    
    # Simulated context-aware response logic
    if entities.get("order_id"):
        response = f"I can help with that for order {entities['order_id']}. "
        response += "What is the new shipping address you'd like to use?"
    else:
        response = "I'd be happy to help change the shipping address. "
        response += "Could you provide your order number first?"
    
    print(f"\n  Context-loaded response:")
    print(f"    User: {user_input}")
    print(f"    Assistant: {response}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("✓ Demo Complete!")
    print("=" * 60)
    print("\nThis demonstration showed:")
    print("  • Creating and managing conversation sessions")
    print("  • Storing messages with full metadata")
    print("  • Tracking state (intents, entities, flags)")
    print("  • Retrieving multi-turn conversation history")
    print("  • Relationship-based graph queries")
    print("  • Transaction-safe operations")
    print("\nAll data is stored in RushDB and persists across sessions.")
    print("Run 'python seed.py' to populate with sample data.")


if __name__ == "__main__":
    run_demo()
