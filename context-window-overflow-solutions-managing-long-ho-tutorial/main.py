"""
Context Window Overflow Solutions: Managing Long-Horizon Agent Interactions

This demo shows how to use RushDB as an external memory layer to handle
context window overflow in AI agent applications.

Key patterns demonstrated:
1. Storing conversation history in RushDB
2. Semantic chunking of long interactions
3. Summarization and fact extraction
4. Vector-based context retrieval
5. Intelligent memory pruning
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(api_key)

# Initialize embedding model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')


def section_header(title: str):
    """Print a section header."""
    print(f"\n[{title}]")
    print("-" * 50)


def step_complete(action: str, details: str = ""):
    """Print completion message."""
    symbol = "✅"
    print(f"{symbol} {action}")
    if details:
        print(f"   {details}")


# =============================================================================
# PATTERN 1: Storing Conversation History
# =============================================================================

def store_conversation(session_id: str, title: str, messages: list, metadata: dict = None):
    """
    Store a complete conversation session as a record.
    
    This is the foundation of external memory — every interaction gets persisted
    so we never need to rely on context window for history.
    """
    conversation = db.records.create(
        label="CONVERSATION",
        data={
            "sessionId": session_id,
            "title": title,
            "date": datetime.now().isoformat(),
            "messages": messages,
            "messageCount": len(messages),
            "metadata": metadata or {}
        }
    )
    return conversation


# =============================================================================
# PATTERN 2: Semantic Chunking
# =============================================================================

def create_chunks(conversation_id: str, content: str, max_tokens: int = 500):
    """
    Break long content into semantically coherent chunks.
    
    This reduces token count while preserving meaning. For production,
    you'd use smarter splitting (sentence boundaries, paragraph breaks).
    """
    # Simple chunking by sentences for demo
    sentences = content.split(". ")
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += ". " + sentence if current_chunk else sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Store each chunk with vector embedding
    for i, chunk_text in enumerate(chunks):
        embedding = model.encode(chunk_text).tolist()
        
        chunk = db.records.create(
            label="CHUNK",
            data={
                "text": chunk_text,
                "index": i,
                "conversationId": conversation_id,
                "createdAt": datetime.now().isoformat()
            },
            vectors=[{"propertyName": "text", "vector": embedding}]
        )
    
    return chunks


# =============================================================================
# PATTERN 3: Summarization and Fact Extraction
# =============================================================================

def extract_and_store_facts(conversation_id: str, content: str):
    """
    Extract key facts from conversation for compressed storage.
    
    In production, you'd use an LLM to extract structured facts.
    For demo, we simulate by identifying key entities and commitments.
    """
    # Simulated extraction - in production, use LLM
    facts = []
    
    # Extract what looks like commitments/decisions
    key_phrases = [
        "deadline", "budget", "approved", "committed", 
        "will do", "need to", "must", "should", "agreed"
    ]
    
    sentences = content.split(". ")
    for sentence in sentences:
        lower = sentence.lower()
        if any(phrase in lower for phrase in key_phrases):
            facts.append({
                "type": "commitment",
                "content": sentence.strip(),
                "conversationId": conversation_id,
                "extractedAt": datetime.now().isoformat()
            })
    
    # Store each fact
    for fact in facts:
        db.records.create(
            label="FACT",
            data=fact
        )
    
    return facts


# =============================================================================
# PATTERN 4: Vector-Based Context Retrieval
# =============================================================================

def retrieve_relevant_context(query: str, limit: int = 3, exclude_session: str = None):
    """
    Use semantic search to retrieve only relevant past context.
    
    This is the key to avoiding context window overflow — we only fetch
    what's semantically relevant to the current query, not all history.
    """
    results = db.ai.search({
        "propertyName": "text",
        "query": query,
        "labels": ["CHUNK"],
        "limit": limit
    })
    
    relevant_chunks = []
    for result in results.data:
        # Skip chunks from same session for diversity
        if exclude_session and result.get("sessionId") == exclude_session:
            continue
        relevant_chunks.append({
            "text": result["text"],
            "score": result.score,
            "sessionId": result.get("sessionId")
        })
    
    return relevant_chunks


def build_context_prompt(retrieved_context: list, current_query: str) -> str:
    """
    Build a context prompt using retrieved memories.
    
    This is what you'd feed to the LLM — relevant context + current query,
    never exceeding context window limits.
    """
    context_parts = ["=== Relevant Historical Context ==="]
    
    for i, ctx in enumerate(retrieved_context, 1):
        context_parts.append(f"\n[{i}] (relevance: {ctx['score']:.2f})")
        context_parts.append(f"    From session: {ctx['sessionId']}")
        context_parts.append(f"    {ctx['text']}")
    
    context_parts.append(f"\n=== Current Query ===\n{current_query}")
    context_parts.append("\n=== Answer ===")
    
    return "\n".join(context_parts)


# =============================================================================
# PATTERN 5: Memory Pruning
# =============================================================================

def prune_old_context(days_threshold: int = 30, preserve_facts: bool = True):
    """
    Remove obsolete chunks while preserving important facts.
    
    Memory pruning prevents unlimited growth. We keep facts (high-value)
    but remove old raw chunks that are superseded by summaries.
    """
    threshold_date = datetime.now() - timedelta(days=days_threshold)
    
    # Find old chunks
    old_chunks = db.records.find({
        "labels": ["CHUNK"],
        "where": {
            "createdAt": {"$lt": threshold_date.isoformat()}
        }
    })
    
    deleted_count = 0
    for chunk in old_chunks.data:
        db.records.delete(record_id=chunk.id)
        deleted_count += 1
    
    return deleted_count


def get_memory_stats():
    """Get current memory statistics."""
    stats = {
        "conversations": db.records.find({"labels": ["CONVERSATION"]}).total,
        "chunks": db.records.find({"labels": ["CHUNK"]}).total,
        "facts": db.records.find({"labels": ["FACT"]}).total
    }
    return stats


# =============================================================================
# DEMO EXECUTION
# =============================================================================

def run_demo():
    """Execute all patterns demonstrating context window solutions."""
    
    print("\n" + "=" * 60)
    print("Context Window Overflow Solutions: Managing Long-Horizon Agents")
    print("=" * 60)
    
    # Initialize vector index for semantic search
    print("\nInitializing vector index...")
    try:
        db.ai.indexes.create({
            "label": "CHUNK",
            "propertyName": "text",
            "sourceType": "external",
            "dimensions": 384,  # all-MiniLM-L6-v2 output dimension
            "similarityFunction": "cosine"
        })
        print("  Created new index")
    except Exception as e:
        # Index might already exist
        print(f"  Index ready (or already exists)")
    
    # --- PATTERN 1: Store Conversation History ---
    section_header("1) Storing Conversation History")
    
    # Simulate a new conversation
    new_messages = [
        {"role": "user", "content": "What's our current project status?"},
        {"role": "assistant", "content": "Based on our records: Phase 1 is complete, Phase 2 is 60% done with the backend API finished. The frontend team is working on the dashboard components."},
        {"role": "user", "content": "Any blockers?"},
        {"role": "assistant", "content": "Yes, we're waiting on the design team for the mobile app mockups. Also, the QA headcount request is still pending approval from finance."},
    ]
    
    conversation = store_conversation(
        session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        title="Status Check Conversation",
        messages=new_messages,
        metadata={"context": "project_status_check"}
    )
    
    stats = get_memory_stats()
    step_complete(
        "Created new conversation record",
        f"Total conversations: {stats['conversations']}"
    )
    
    # --- PATTERN 2: Semantic Chunking ---
    section_header("2) Semantic Chunking")
    
    # Create chunks from the conversation content
    combined_content = " ".join([f"{m['role']}: {m['content']}" for m in new_messages])
    chunks = create_chunks(conversation.id, combined_content)
    
    step_complete(
        f"Created {len(chunks)} semantic chunks",
        f"Each chunk is ~500 chars for optimal embedding"
    )
    
    # --- PATTERN 3: Summarization and Fact Extraction ---
    section_header("3) Summarization and Fact Extraction")
    
    facts = extract_and_store_facts(conversation.id, combined_content)
    
    step_complete(
        f"Extracted {len(facts)} key facts",
        f"Facts include commitments, deadlines, and decisions"
    )
    
    # Show sample fact
    if facts:
        print(f"   Sample fact: \"{facts[0]['content'][:60]}...\"")
    
    # --- PATTERN 4: Vector-Based Context Retrieval ---
    section_header("4) Context Retrieval (Semantic Search)")
    
    # Query that should retrieve relevant historical context
    query = "What are the project blockers and timeline commitments?"
    print(f"\n🔍 Query: \"{query}\"\n")
    
    relevant_context = retrieve_relevant_context(query, limit=3)
    
    if relevant_context:
        print("   Retrieved relevant contexts:")
        for ctx in relevant_context:
            print(f"   [{ctx['score']:.3f}] {ctx['text'][:80]}...")
        
        # Build context prompt
        context_prompt = build_context_prompt(relevant_context, query)
        step_complete(
            "Built context prompt",
            f"{len(context_prompt)} chars (safe for context window)"
        )
    else:
        print("   No relevant context found yet. Run seed.py first to populate history.")
    
    # --- PATTERN 5: Memory Pruning ---
    section_header("5) Memory Pruning")
    
    # Show current stats
    stats_before = get_memory_stats()
    print(f"   Before pruning:")
    print(f"     - Conversations: {stats_before['conversations']}")
    print(f"     - Chunks: {stats_before['chunks']}")
    print(f"     - Facts: {stats_before['facts']}")
    
    # Demonstrate pruning (in real usage, this would target old data)
    pruned = prune_old_context(days_threshold=0, preserve_facts=True)
    print(f"\n   Pruned {pruned} obsolete chunks")
    
    stats_after = get_memory_stats()
    print(f"   After pruning:")
    print(f"     - Chunks: {stats_after['chunks']} (facts preserved: {stats_after['facts']})")
    
    # --- FINAL SUMMARY ---
    section_header("Summary")
    
    print("\nKey Takeaways:")
    print("  1. Store everything → Never lose context")
    print("  2. Chunk semantically → Optimal retrieval granularity")
    print("  3. Extract facts → Compressed high-value information")
    print("  4. Vector search → Only retrieve relevant context")
    print("  5. Prune wisely → Prevent unlimited growth")
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("=" * 60)
    
    return {
        "conversations": stats_after['conversations'],
        "chunks": stats_after['chunks'],
        "facts": stats_after['facts']
    }


if __name__ == "__main__":
    run_demo()
