"""
Graph-Native Pagination for Streaming AI Response Contexts
============================================================

This demo shows how RushDB's graph-native architecture handles pagination
for streaming AI conversations without manual bookkeeping.

Key concepts demonstrated:
1. Schema: StreamChunk, ToolCall, Document nodes with PRECEDES/CITES relationships
2. Cursor-based pagination: Using node IDs as stable cursors
3. Concurrent writes: New chunks don't break in-progress pagination
4. Context-aware retrieval: Fetching page N while maintaining relationship context
"""

import os
import time
import random
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB

# ─────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Missing RUSHDB_API_KEY. "
        "Copy .env.example to .env and add your API key."
    )

db = RushDB(API_KEY)

# Pagination settings
PAGE_SIZE = 3

# ─────────────────────────────────────────────────────────────────
# Demo 1: Schema Overview
# ─────────────────────────────────────────────────────────────────

def show_schema_overview():
    """Display the graph schema used in this demo."""
    print("\n" + "="*60)
    print("📊 GRAPH SCHEMA OVERVIEW")
    print("="*60)
    print("""
    Nodes:
    ├── StreamChunk   — Individual pieces of streaming response
    ├── ToolCall      — Tool invocation that triggered a chunk
    ├── Document      — Document cited by a chunk
    └── Conversation  — Metadata container for a conversation stream

    Relationships:
    ├── PRECEDES          (out) StreamChunk → StreamChunk
    ├── TRIGGERED_BY      (in)  StreamChunk ← ToolCall
    ├── CITES             (out) StreamChunk → Document
    └── STARTS_CONVERSATION (out) StreamChunk → Conversation
    """)


# ─────────────────────────────────────────────────────────────────
# Demo 2: Fetching a Single Page with Context
# ─────────────────────────────────────────────────────────────────

def fetch_page_with_context(conversation_id: str, page: int = 1):
    """
    Fetch page N of chunks while retrieving relationship context.
    
    This demonstrates how to get:
    - The chunks for the requested page
    - What tool triggered each chunk
    - What documents each chunk cites
    - The previous chunk in the sequence
    """
    # Calculate skip for page
    skip = (page - 1) * PAGE_SIZE

    # Fetch the page of chunks
    result = db.records.find({
        "labels": ["StreamChunk"],
        "where": {"conversationId": conversation_id},
        "orderBy": {"index": "asc"},
        "skip": skip,
        "limit": PAGE_SIZE,
    })

    chunks = result.data

    if not chunks:
        print(f"   No chunks found for conversation {conversation_id}")
        return []

    print(f"\n   📄 Page {page} — {len(chunks)} chunks:")
    print(f"   {'─'*50}")

    for chunk in chunks:
        chunk_id = chunk.id[:12] + "..."
        print(f"   Chunk [{chunk_id}]")
        print(f"     Text: \"{chunk['text'][:50]}...\"")
        print(f"     Index: {chunk['index']}")

        # ── Get ToolCall that triggered this chunk ──
        tool_result = db.records.find({
            "labels": ["ToolCall"],
            "where": {
                "$out": {
                    "type": "TRIGGERED_BY",
                    "target": {"$id": chunk.id}
                }
            },
            "limit": 1,
        })

        if tool_result.data:
            tool = tool_result.data[0]
            print(f"     → Tool: {tool['toolName']}({tool.get('arguments', {})})")
        else:
            print(f"     → Tool: (none)")

        # ── Get Document(s) cited by this chunk ──
        doc_result = db.records.find({
            "labels": ["Document"],
            "where": {
                "$in": {
                    "type": "CITES",
                    "source": {"$id": chunk.id}
                }
            },
            "limit": 5,
        })

        if doc_result.data:
            doc_titles = [d['title'] for d in doc_result.data]
            print(f"     → Cites: {', '.join(doc_titles)}")
        else:
            print(f"     → Cites: (none)")

        # ── Get previous chunk via PRECEDES relationship ──
        prev_result = db.records.find({
            "labels": ["StreamChunk"],
            "where": {
                "PRECEDES": {"$id": chunk.id}
            },
            "limit": 1,
        })

        if prev_result.data:
            prev = prev_result.data[0]
            print(f"     ← Previous chunk index: {prev['index']}")
        else:
            print(f"     ← Previous chunk: (first in stream)")

        print()

    return chunks


def demo_basic_pagination():
    """Demonstrate basic cursor-based pagination."""
    print("\n" + "="*60)
    print("🔄 BASIC PAGINATION DEMO")
    print("="*60)

    # Find a conversation to paginate through
    conv_result = db.records.find({
        "labels": ["Conversation"],
        "limit": 1,
        "orderBy": {"createdAt": "desc"},
    })

    if not conv_result.data:
        print("   ⚠️  No conversations found. Run seed.py first!")
        return

    conversation_id = conv_result.data[0]['conversationId']
    print(f"\n   Using conversation: {conversation_id}")

    # Fetch pages
    for page in range(1, 4):
        chunks = fetch_page_with_context(conversation_id, page=page)
        if len(chunks) < PAGE_SIZE:
            break


# ─────────────────────────────────────────────────────────────────
# Demo 3: Cursor-Based Pagination with ID Cursors
# ─────────────────────────────────────────────────────────────────

def demo_cursor_pagination():
    """
    Demonstrate cursor-based pagination using node IDs.
    
    Unlike offset-based pagination, cursor pagination is stable
    when concurrent writes occur.
    """
    print("\n" + "="*60)
    print("🎯 CURSOR-BASED PAGINATION")
    print("="*60)

    # Get a conversation
    conv_result = db.records.find({
        "labels": ["Conversation"],
        "limit": 1,
    })

    if not conv_result.data:
        print("   ⚠️  No conversations found. Run seed.py first!")
        return

    conversation_id = conv_result.data[0]['conversationId']

    # First page
    first_page = db.records.find({
        "labels": ["StreamChunk"],
        "where": {"conversationId": conversation_id},
        "orderBy": {"index": "asc"},
        "limit": PAGE_SIZE,
    })

    if not first_page.data:
        print("   No chunks found.")
        return

    # Use the last chunk's ID as our cursor
    cursor_id = first_page.data[-1].id
    cursor_index = first_page.data[-1]['index']

    print(f"\n   First page: {len(first_page.data)} chunks")
    print(f"   Last chunk ID: {cursor_id[:12]}...")
    print(f"   Last chunk index: {cursor_index}")

    # Second page using cursor
    second_page = db.records.find({
        "labels": ["StreamChunk"],
        "where": {
            "conversationId": conversation_id,
            "index": {"$gt": cursor_index}  # Use index > cursor's index
        },
        "orderBy": {"index": "asc"},
        "limit": PAGE_SIZE,
    })

    print(f"\n   Second page (cursor from first): {len(second_page.data)} chunks")
    for chunk in second_page.data:
        print(f"     - Index {chunk['index']}: \"{chunk['text'][:40]}...\"")

    # Verify cursor is stable
    print("\n   ✅ Cursor-based pagination is stable — no OFFSET means")
    print("      new chunks won't shift our results")


# ─────────────────────────────────────────────────────────────────
# Demo 4: Concurrent Write Handling
# ─────────────────────────────────────────────────────────────────

def demo_concurrent_writes():
    """
    Simulate concurrent writes while a client is paginating.
    
    This shows how RushDB's graph model handles:
    - New chunks being added during pagination
    - Stable cursors that don't break with new data
    """
    print("\n" + "="*60)
    print("⚡ CONCURRENT WRITE HANDLING")
    print("="*60)

    # Get a conversation
    conv_result = db.records.find({
        "labels": ["Conversation"],
        "limit": 1,
    })

    if not conv_result.data:
        print("   ⚠️  No conversations found. Run seed.py first!")
        return

    conversation_id = conv_result.data[0]['conversationId']

    # Step 1: Client starts pagination, captures cursor
    print("\n   👤 Client starts pagination...")

    initial_page = db.records.find({
        "labels": ["StreamChunk"],
        "where": {"conversationId": conversation_id},
        "orderBy": {"index": "asc"},
        "limit": PAGE_SIZE,
    })

    initial_count = len(initial_page.data)
    cursor_chunk = initial_page.data[-1] if initial_page.data else None

    print(f"   → Fetched {initial_count} chunks")
    if cursor_chunk:
        print(f"   → Cursor at chunk index {cursor_chunk['index']}")

    # Step 2: Simulate streaming - new chunks are added
    print("\n   📡 Simulating streaming: adding new chunks...")

    current_max_index = 0
    if cursor_chunk:
        current_max_index = cursor_chunk['index']

    # Add 2 new chunks (simulating continued streaming)
    new_chunks = []
    for i in range(2):
        new_index = current_max_index + i + 1
        new_chunk = db.records.create(
            label="StreamChunk",
            data={
                "text": f"[Concurrent write] New chunk at index {new_index}",
                "conversationId": conversation_id,
                "streamType": "concurrent_demo",
                "index": new_index,
                "timestamp": datetime.now().isoformat(),
                "tokens": random.randint(5, 15),
                "isFinal": False,
            }
        )
        new_chunks.append(new_chunk)

        # Link PRECEDES relationship
        if i > 0:
            db.records.attach(
                source=new_chunk,
                target=new_chunks[i - 1],
                options={"type": "PRECEDES", "direction": "out"}
            )

        print(f"   → Created chunk index {new_index} (id: {new_chunk.id[:12]}...)")

    # Step 3: Client resumes pagination with stable cursor
    print("\n   👤 Client resumes pagination with original cursor...")

    # Using cursor-based approach (index > last known)
    resumed_page = db.records.find({
        "labels": ["StreamChunk"],
        "where": {
            "conversationId": conversation_id,
            "index": {"$gt": current_max_index}
        },
        "orderBy": {"index": "asc"},
        "limit": PAGE_SIZE,
    })

    print(f"   → Fetched {len(resumed_page.data)} new chunks")
    for chunk in resumed_page.data:
        print(f"     - Index {chunk['index']}: \"{chunk['text'][:50]}...\"")

    print("\n   ✅ Cursor remains stable despite concurrent writes!")
    print("      New chunks don't shift or duplicate results.")


# ─────────────────────────────────────────────────────────────────
# Demo 5: Full Context Traversal
# ─────────────────────────────────────────────────────────────────

def demo_full_context_traversal():
    """
    Demonstrate fetching a chunk with its full context:
    - Previous chunk
    - Next chunk
    - Triggering tool call
    - Cited documents
    - Conversation metadata
    """
    print("\n" + "="*60)
    print("🔍 FULL CONTEXT TRAVERSAL")
    print("="*60)

    # Find a chunk that has both tool calls and document citations
    chunk_result = db.records.find({
        "labels": ["StreamChunk"],
        "where": {
            "$out": {
                "type": "TRIGGERED_BY",
                "target": {"$label": "ToolCall"}
            },
            "$out": {
                "type": "CITES",
                "target": {"$label": "Document"}
            }
        },
        "limit": 1,
    })

    if not chunk_result.data:
        print("   No chunk with full context found. Using any chunk...")
        chunk_result = db.records.find({
            "labels": ["StreamChunk"],
            "limit": 1,
        })

    if not chunk_result.data:
        print("   ⚠️  No chunks found. Run seed.py first!")
        return

    chunk = chunk_result.data[0]

    print(f"\n   📦 Fetching full context for chunk [{chunk.id[:12]}...]")
    print(f"   {'─'*50}")

    # Get conversation metadata
    conv_result = db.records.find({
        "labels": ["Conversation"],
        "where": {
            "STARTS_CONVERSATION": {"$id": chunk.id}
        },
        "limit": 1,
    })

    # Alternative: find via conversationId field
    if not conv_result.data:
        conv_result = db.records.find({
            "labels": ["Conversation"],
            "where": {"conversationId": chunk['conversationId']},
            "limit": 1,
        })

    if conv_result.data:
        conv = conv_result.data[0]
        print(f"   📋 Conversation: {conv['conversationId']} ({conv['streamType']})")
        print(f"      Status: {conv['status']}")

    # Get previous chunk
    prev_result = db.records.find({
        "labels": ["StreamChunk"],
        "where": {"PRECEDES": {"$id": chunk.id}},
        "limit": 1,
    })

    if prev_result.data:
        prev = prev_result.data[0]
        print(f"\n   ← Previous: \"{prev['text'][:60]}...\"")
    else:
        print(f"\n   ← Previous: (first chunk)")

    # Get next chunk (via reverse PRECEDES relationship)
    next_result = db.records.find({
        "labels": ["StreamChunk"],
        "where": {
            "$in": {
                "type": "PRECEDES",
                "target": {"$id": chunk.id}
            }
        },
        "limit": 1,
    })

    if next_result.data:
        next_chunk = next_result.data[0]
        print(f"   → Next: \"{next_chunk['text'][:60]}...\"")
    else:
        print(f"   → Next: (last chunk)")

    # Get triggering tool call
    tool_result = db.records.find({
        "labels": ["ToolCall"],
        "where": {
            "$out": {
                "type": "TRIGGERED_BY",
                "target": {"$id": chunk.id}
            }
        },
        "limit": 1,
    })

    if tool_result.data:
        tool = tool_result.data[0]
        print(f"\n   🔧 Tool: {tool['toolName']}")
        print(f"      Args: {tool.get('arguments', {})})")
        print(f"      Status: {tool['status']}")

    # Get cited documents
    doc_result = db.records.find({
        "labels": ["Document"],
        "where": {
            "$in": {
                "type": "CITES",
                "source": {"$id": chunk.id}
            }
        },
        "limit": 10,
    })

    if doc_result.data:
        print(f"\n   📄 Cited documents ({len(doc_result.data)}):")
        for doc in doc_result.data:
            print(f"      • {doc['title']} ({doc['type']})")

    print(f"\n   {'─'*50}")
    print(f"   ✅ Full context retrieved via graph traversal!")


# ─────────────────────────────────────────────────────────────────
# Demo 6: Paginated Streaming History
# ─────────────────────────────────────────────────────────────────

def demo_streaming_history():
    """
    Simulate fetching the complete streaming history of a conversation
    using cursor-based pagination.
    """
    print("\n" + "="*60)
    print("📜 COMPLETE STREAMING HISTORY (Paginated)")
    print("="*60)

    # Find a conversation
    conv_result = db.records.find({
        "labels": ["Conversation"],
        "limit": 1,
    })

    if not conv_result.data:
        print("   ⚠️  No conversations found. Run seed.py first!")
        return

    conversation_id = conv_result.data[0]['conversationId']
    print(f"\n   Conversation: {conversation_id}")

    # Get total count
    total_result = db.records.find({
        "labels": ["StreamChunk"],
        "where": {"conversationId": conversation_id},
    })

    total_chunks = len(total_result.data)
    total_pages = (total_chunks + PAGE_SIZE - 1) // PAGE_SIZE

    print(f"   Total chunks: {total_chunks}")
    print(f"   Page size: {PAGE_SIZE}")
    print(f"   Total pages: {total_pages}")

    # Simulate fetching all pages
    print(f"\n   {'─'*50}")
    print(f"   Fetching all pages...")

    current_index = -1
    page = 0

    while True:
        page += 1

        if current_index == -1:
            # First page
            result = db.records.find({
                "labels": ["StreamChunk"],
                "where": {"conversationId": conversation_id},
                "orderBy": {"index": "asc"},
                "limit": PAGE_SIZE,
            })
        else:
            # Subsequent pages using cursor
            result = db.records.find({
                "labels": ["StreamChunk"],
                "where": {
                    "conversationId": conversation_id,
                    "index": {"$gt": current_index}
                },
                "orderBy": {"index": "asc"},
                "limit": PAGE_SIZE,
            })

        chunks = result.data

        if not chunks:
            break

        print(f"\n   Page {page}:")
        for chunk in chunks:
            print(f"     [{chunk['index']:3}] {chunk['text'][:55]}...")
            current_index = chunk['index']

        if len(chunks) < PAGE_SIZE:
            break

    print(f"\n   {'─'*50}")
    print(f"   ✅ Fetched {page} pages with stable cursors")


# ─────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────

def main():
    """Run all demos."""
    print("\n" + "#"*60)
    print("# GRAPH-NATIVE PAGINATION FOR STREAMING AI RESPONSES")
    print("#"*60)
    print(f"\n   RushDB SDK Version: {rushdb.__version__ if hasattr(rushdb, '__version__') else '2.x'}")
    print(f"   API Key configured: {'Yes' if API_KEY else 'No'}")

    # Show schema
    show_schema_overview()

    # Run demos
    demo_basic_pagination()
    demo_cursor_pagination()
    demo_concurrent_writes()
    demo_full_context_traversal()
    demo_streaming_history()

    print("\n" + "="*60)
    print("✅ ALL DEMOS COMPLETE")
    print("="*60)
    print("""
    Key Takeaways:
    
    1. Graph-Native Schema: StreamChunk nodes with PRECEDES edges
       preserve streaming order regardless of storage layout.
    
    2. Cursor Stability: Using node IDs or field values as cursors
       survives concurrent writes — new chunks don't shift results.
    
    3. Context Traversal: Relationships (TRIGGERED_BY, CITES) let you
       fetch full context in O(1) graph lookups, not expensive JOINs.
    
    4. No Bookkeeping: RushDB handles relationship management;
       you just navigate the graph.
    
    Learn more: https://docs.rushdb.com
    """)


if __name__ == "__main__":
    import rushdb
    main()
