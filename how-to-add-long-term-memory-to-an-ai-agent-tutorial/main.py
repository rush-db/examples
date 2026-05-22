"""
AI Agent with Long-Term Memory using RushDB

This demo shows how to build persistent memory into an AI agent:
1. Store experiences and learned facts
2. Search memories semantically
3. Retrieve relevant context for responses
4. Use transactions for atomic operations

The agent simulates having a conversation while maintaining
awareness of past interactions through RushDB.
"""

import os
import time
from datetime import datetime
from typing import Optional

from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from rushdb import RushDB

# Load environment
load_dotenv()

# Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MEMORY_LABEL = "MEMORY"
AGENT_LABEL = "AGENT"


class MemoryEntry:
    """Represents a stored memory in the system."""
    
    def __init__(self, record):
        self.id = record.id
        self.content = record.get("content", "")
        self.memory_type = record.get("type", "unknown")
        self.importance = record.get("importance", 0.5)
        self.timestamp = record.get("timestamp", "")
        self.score = record.score if hasattr(record, 'score') else None
    
    def __repr__(self):
        return f"Memory({self.memory_type}, score={self.score:.3f}): {self.content[:60]}..."


class AgentMemory:
    """Manages the agent's long-term memory using RushDB."""
    
    def __init__(self, api_key: str):
        self.db = RushDB(api_key)
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.index_id = None
        self.agent_id = None
        self._initialize()
    
    def _initialize(self):
        """Set up the memory system."""
        print("Initializing AI Agent with Long-Term Memory...\n")
        
        # Ensure vector index exists
        self._ensure_vector_index()
        
        # Ensure agent record exists
        self._ensure_agent()
        
        print("Memory system ready.\n")
    
    def _ensure_vector_index(self):
        """Create or verify the vector index exists."""
        try:
            indexes = self.db.ai.indexes.find()
            for idx in indexes:
                if idx.get("label") == MEMORY_LABEL and idx.get("propertyName") == "content":
                    self.index_id = idx.get("__id")
                    print(f"Using existing vector index: {self.index_id}")
                    return
        except Exception:
            pass
        
        # Create new index
        print("Creating vector index for memory storage...")
        response = self.db.ai.indexes.create({
            "label": MEMORY_LABEL,
            "propertyName": "content",
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine"
        })
        self.index_id = response.data.get("__id")
        print(f"Created vector index: {self.index_id}")
    
    def _ensure_agent(self):
        """Create or fetch the agent identity."""
        existing = self.db.records.find({
            "labels": [AGENT_LABEL],
            "where": {"name": "assistant"},
            "limit": 1
        })
        
        if existing:
            self.agent_id = existing[0].id
            print(f"Agent identity: {self.agent_id}")
        else:
            agent = self.db.records.create(
                label=AGENT_LABEL,
                data={
                    "name": "assistant",
                    "created_at": datetime.now().isoformat() + "Z",
                    "version": "1.0"
                }
            )
            self.agent_id = agent.id
            print(f"Created new agent identity: {self.agent_id}")
    
    def store_memory(
        self,
        content: str,
        memory_type: str = "conversation",
        importance: float = 0.7,
        attach_to_agent: bool = True
    ) -> MemoryEntry:
        """
        Store a new memory with vector embedding.
        
        Args:
            content: The memory text to store
            memory_type: Category (conversation, preference, fact, skill)
            importance: Relevance score 0-1
            attach_to_agent: Whether to link this memory to the agent
        
        Returns:
            MemoryEntry object for the stored memory
        """
        # Generate embedding
        embedding = self.embedder.encode(content).tolist()
        
        # Store with vector in a transaction
        with self.db.transactions.begin() as tx:
            memory = self.db.records.create(
                label=MEMORY_LABEL,
                data={
                    "content": content,
                    "type": memory_type,
                    "importance": importance,
                    "timestamp": datetime.now().isoformat() + "Z"
                },
                vectors=[{"propertyName": "content", "vector": embedding}],
                transaction=tx
            )
            
            if attach_to_agent:
                agent_record = self.db.records.find_by_id(self.agent_id)
                self.db.records.attach(
                    source=agent_record,
                    target=memory,
                    options={"type": "KNOWS"},
                    transaction=tx
                )
        
        return MemoryEntry(memory)
    
    def recall_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> list[MemoryEntry]:
        """
        Search for relevant memories using semantic similarity.
        
        Args:
            query: Text to search for
            memory_type: Optional filter by memory type
            limit: Maximum number of results
        
        Returns:
            List of MemoryEntry objects ranked by relevance
        """
        search_params = {
            "propertyName": "content",
            "query": query,
            "labels": [MEMORY_LABEL],
            "limit": limit
        }
        
        if memory_type:
            search_params["where"] = {"type": memory_type}
        
        results = self.db.ai.search(search_params)
        
        return [MemoryEntry(record) for record in results]
    
    def get_all_memories(self, limit: int = 20) -> list[MemoryEntry]:
        """Retrieve all stored memories, most recent first."""
        results = self.db.records.find({
            "labels": [MEMORY_LABEL],
            "limit": limit,
            "orderBy": {"timestamp": "desc"}
        })
        return [MemoryEntry(r) for r in results]
    
    def get_memory_stats(self) -> dict:
        """Get statistics about stored memories."""
        all_memories = self.db.records.find({"labels": [MEMORY_LABEL], "limit": 1000})
        
        type_counts = {}
        total_importance = 0
        
        for memory in all_memories:
            m_type = memory.get("type", "unknown")
            type_counts[m_type] = type_counts.get(m_type, 0) + 1
            total_importance += memory.get("importance", 0)
        
        return {
            "total": len(all_memories),
            "by_type": type_counts,
            "avg_importance": total_importance / len(all_memories) if all_memories else 0
        }


class AIAgent:
    """
    AI Agent with memory capabilities.
    
    This demonstrates how an agent uses RushDB for persistent memory,
    retrieving relevant context to inform responses.
    """
    
    def __init__(self, api_key: str):
        self.memory = AgentMemory(api_key)
        self.conversation_history = []
    
    def think(self, query: str, store_interaction: bool = True) -> str:
        """
        Process a query using long-term memory context.
        
        Args:
            query: User's input
            store_interaction: Whether to store this exchange
        
        Returns:
            Agent's response
        """
        # Step 1: Retrieve relevant memories
        relevant_memories = self.memory.recall_memories(query, limit=3)
        
        # Step 2: Build context from memories
        context_parts = []
        if relevant_memories:
            context_parts.append(f"Relevant memories ({len(relevant_memories)} found):")
            for mem in relevant_memories:
                context_parts.append(f"  - [{mem.memory_type}] {mem.content}")
        
        # Step 3: Generate response
        response = self._generate_response(query, relevant_memories)
        
        # Step 4: Store the interaction
        if store_interaction:
            summary = f"User asked about: {query[:50]}... Response referenced {len(relevant_memories)} past context(s)"
            self.memory.store_memory(
                content=summary,
                memory_type="conversation",
                importance=0.6
            )
        
        # Track conversation
        self.conversation_history.append({"query": query, "response": response})
        
        return response
    
    def _generate_response(self, query: str, memories: list[MemoryEntry]) -> str:
        """
        Generate a response informed by retrieved memories.
        
        In a real implementation, this would call an LLM with the
        retrieved context. Here we simulate the response.
        """
        if not memories:
            return f"I don't have relevant memories for that query. Let me note this for future reference."
        
        # Simulate context-informed response
        memory_refs = [f"'{m.content[:30]}...'" for m in memories[:2]]
        return f"Based on our past interactions, I recall {', '.join(memory_refs)}. This helps me provide more context-aware assistance."
    
    def learn_preference(self, preference: str, importance: float = 0.8):
        """Store a user preference."""
        return self.memory.store_memory(
            content=preference,
            memory_type="preference",
            importance=importance
        )
    
    def learn_fact(self, fact: str, importance: float = 0.7):
        """Store a learned fact."""
        return self.memory.store_memory(
            content=fact,
            memory_type="fact",
            importance=importance
        )


def print_separator():
    print("\n" + "=" * 60 + "\n")


def demo_basic_memory():
    """Demonstrate storing and retrieving memories."""
    print_separator()
    print("DEMO: Basic Memory Operations")
    print("-" * 40)
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not set")
        return
    
    agent = AIAgent(api_key)
    
    # Store some initial memories
    print("\n[1] Storing initial memories...")
    
    memories = [
        ("User prefers detailed technical explanations with code examples", "preference", 0.9),
        ("Working on a Python Flask project with PostgreSQL database", "fact", 0.8),
        ("User is familiar with async/await patterns in Python", "skill", 0.7),
        ("Discussed authentication implementation with JWT tokens", "conversation", 0.6),
    ]
    
    for content, m_type, importance in memories:
        agent.learn_preference(content) if m_type == "preference" else \
        agent.learn_fact(content) if m_type == "fact" else \
        agent.memory.store_memory(content, m_type, importance)
    
    print(f"   Stored {len(memories)} memories")
    
    # Retrieve memories
    print("\n[2] Searching for relevant memories...")
    
    queries = [
        "What are the user's technical preferences?",
        "What project is the user working on?",
        "Python async patterns"
    ]
    
    for query in queries:
        results = agent.memory.recall_memories(query, limit=2)
        print(f"   Query: '{query}'")
        print(f"   Found: {len(results)} memories")
        for mem in results:
            print(f"      - {mem.content[:50]}... (score: {mem.score:.3f})")
        print()


def demo_contextual_response():
    """Demonstrate using memories for contextual responses."""
    print_separator()
    print("DEMO: Contextual Response Generation")
    print("-" * 40)
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not set")
        return
    
    agent = AIAgent(api_key)
    
    # Simulate conversation
    queries = [
        "Can you explain how decorators work in Python?",
        "What's the best way to structure a Flask application?",
        "How do I implement authentication in my project?",
    ]
    
    print("\nAgent processing queries with memory context:\n")
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}] User: {query}")
        response = agent.think(query, store_interaction=True)
        print(f"    Agent: {response}")
        
        # Show context retrieved
        memories = agent.memory.recall_memories(query, limit=2)
        if memories:
            print(f"    (Retrieved {len(memories)} relevant memory/memories)")
        print()


def demo_memory_stats():
    """Show memory system statistics."""
    print_separator()
    print("DEMO: Memory Statistics")
    print("-" * 40)
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not set")
        return
    
    memory = AgentMemory(api_key)
    
    stats = memory.get_memory_stats()
    
    print(f"\nTotal memories stored: {stats['total']}")
    print(f"Average importance: {stats['avg_importance']:.2f}")
    print("\nBy type:")
    for mem_type, count in stats["by_type"].items():
        print(f"  - {mem_type}: {count}")
    
    # Show recent memories
    recent = memory.get_all_memories(limit=5)
    print(f"\nMost recent memories:")
    for mem in recent:
        print(f"  [{mem.memory_type}] {mem.content[:60]}...")


def demo_transactional_memory():
    """Demonstrate atomic memory operations with transactions."""
    print_separator()
    print("DEMO: Transactional Memory Operations")
    print("-" * 40)
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not set")
        return
    
    db = RushDB(api_key)
    
    print("\nStoring multiple related memories atomically...")
    
    # Store related memories in a transaction
    with db.transactions.begin() as tx:
        # Create a task-related memory cluster
        task_memory = db.records.create(
            label=MEMORY_LABEL,
            data={
                "content": "User needs to implement file upload feature",
                "type": "task",
                "importance": 0.9,
                "timestamp": datetime.now().isoformat() + "Z"
            },
            transaction=tx
        )
        
        # Store related context
        sub_memory1 = db.records.create(
            label=MEMORY_LABEL,
            data={
                "content": "Consider using multipart/form-data encoding",
                "type": "skill",
                "importance": 0.7,
                "timestamp": datetime.now().isoformat() + "Z"
            },
            transaction=tx
        )
        
        sub_memory2 = db.records.create(
            label=MEMORY_LABEL,
            data={
                "content": "Validate file types server-side for security",
                "type": "skill",
                "importance": 0.8,
                "timestamp": datetime.now().isoformat() + "Z"
            },
            transaction=tx
        )
        
        # Link related memories
        db.records.attach(
            source=task_memory,
            target=sub_memory1,
            options={"type": "CONTEXT_FOR"},
            transaction=tx
        )
        db.records.attach(
            source=task_memory,
            target=sub_memory2,
            options={"type": "CONTEXT_FOR"},
            transaction=tx
        )
    
    print("   Created 3 memories with relationships in one transaction")
    print("   All-or-nothing: either all succeed or all rollback")


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("AI AGENT WITH LONG-TERM MEMORY")
    print("Using RushDB as the memory store")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\nERROR: RUSHDB_API_KEY not found in environment")
        print("Please copy .env.example to .env and add your API key")
        print("Get your API key at: https://dash.rushdb.com")
        return
    
    # Check for seed data
    try:
        db = RushDB(api_key)
        existing = db.records.find({"labels": ["MEMORY"], "limit": 1})
        if not existing:
            print("\nNOTE: No memory records found. Run 'python seed.py' first")
            print("to populate the database with demo data.\n")
    except Exception as e:
        print(f"\nError connecting to RushDB: {e}")
        return
    
    # Run demonstrations
    demo_basic_memory()
    demo_contextual_response()
    demo_memory_stats()
    demo_transactional_memory()
    
    print_separator()
    print("DEMONSTRATION COMPLETE")
    print("-" * 40)
    print("\nThe agent now has persistent memory that survives sessions.")
    print("Run 'python main.py' again to continue building the memory.")
    print("\nKey takeaways:")
    print("  - Memories are stored with vector embeddings for semantic search")
    print("  - Relevant context is retrieved based on query similarity")
    print("  - Transactions ensure atomic operations")
    print("  - Read operations are always FREE in RushDB")
    print()


if __name__ == "__main__":
    main()
