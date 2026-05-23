"""
Seed script: Generates realistic streaming AI conversation data.

This script creates:
- 3 conversation streams with realistic AI responses
- StreamChunk nodes linked by PRECEDES relationships
- ToolCall nodes that trigger certain chunks
- Document nodes that are cited by chunks

The data demonstrates graph-native pagination patterns.
"""

import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
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

# ─────────────────────────────────────────────────────────────────
# Mock Data Definitions
# ─────────────────────────────────────────────────────────────────

# Realistic streaming responses across different conversation types
STREAM_TEMPLATES = {
    "general": [
        "I'm analyzing your request...",
        "Let me search through the available data...",
        "Based on my analysis, ",
        "The key findings are: first, ",
        "second, the data shows ",
        "and third, there's a clear pattern indicating ",
        "To summarize, the most important takeaway is ",
        "Would you like me to elaborate on any specific point?",
    ],
    "code_review": [
        "Looking at the code structure...",
        "I notice this function could be optimized...",
        "The current implementation uses ",
        "A more efficient approach would be to ",
        "I've identified a potential edge case around line ",
        "The type safety could be improved by ",
        "Overall, this is a solid implementation with ",
        "Recommended refactor: ",
    ],
    "data_analysis": [
        "Loading the dataset...",
        "Initial scan complete. Found ",
        "rows with ",
        "missing values detected in columns: ",
        "Generating summary statistics...",
        "Mean: ",
        "Median: ",
        "Standard deviation: ",
    ],
}

TOOL_CALLS = [
    {"name": "web_search", "args": {"query": "latest trends"}},
    {"name": "execute_code", "args": {"language": "python", "code": "import pandas as pd"}},
    {"name": "read_file", "args": {"path": "/data/config.json"}},
    {"name": "database_query", "args": {"sql": "SELECT * FROM users"}},
    {"name": "api_call", "args": {"endpoint": "/v1/analyze"}},
    {"name": "get_weather", "args": {"location": "San Francisco"}},
    {"name": "calculate", "args": {"expression": "sqrt(144)"}},
]

DOCUMENTS = [
    {"title": "API Documentation", "type": "reference", "content": "REST API v2 specification"},
    {"title": "Architecture Guide", "type": "guide", "content": "Microservices pattern documentation"},
    {"title": "Code Style Guide", "type": "standard", "content": "PEP 8 and company conventions"},
    {"title": "Weather API Docs", "type": "reference", "content": "OpenWeatherMap API reference"},
    {"title": "Data Schema", "type": "specification", "content": "Database entity relationships"},
    {"title": "User Research Report", "type": "analysis", "content": "Q4 2024 user behavior study"},
]

CONVERSATION_IDS = ["conv_abc123", "conv_def456", "conv_ghi789"]

# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def check_data_exists(conversation_id: str) -> bool:
    """Check if data for this conversation already exists."""
    result = db.records.find({
        "labels": ["StreamChunk"],
        "where": {"conversationId": conversation_id},
        "limit": 1
    })
    return len(result.data) > 0


def create_stream_chunks(conversation_id: str, stream_type: str, num_chunks: int = 8):
    """Create a chain of stream chunks with PRECEDES relationships."""
    template = STREAM_TEMPLATES[stream_type]
    chunks = []
    previous_chunk = None

    for i, base_text in enumerate(template[:num_chunks]):
        # Add variability to make it feel like real streaming
        text = base_text + str(random.randint(10, 999)) if random.random() > 0.5 else base_text

        # Create the chunk
        chunk_data = {
            "text": text,
            "conversationId": conversation_id,
            "streamType": stream_type,
            "index": i,
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
            "tokens": random.randint(5, 25),
            "isFinal": i == len(template[:num_chunks]) - 1,
        }

        chunk = db.records.create(
            label="StreamChunk",
            data=chunk_data
        )
        chunks.append(chunk)

        # Link to previous chunk with PRECEDES relationship
        if previous_chunk:
            db.records.attach(
                source=chunk,
                target=previous_chunk,
                options={"type": "PRECEDES", "direction": "out"}
            )
        else:
            # First chunk - mark conversation start
            conversation_record = db.records.find({
                "labels": ["Conversation"],
                "where": {"conversationId": conversation_id}
            })
            if conversation_record.data:
                db.records.attach(
                    source=chunk,
                    target=conversation_record.data[0],
                    options={"type": "STARTS_CONVERSATION", "direction": "out"}
                )

        previous_chunk = chunk

        # Progress indicator every 100 chunks
        if (i + 1) % 100 == 0:
            print(f"   ... {i + 1} chunks created")

    return chunks


def attach_tool_calls(chunks: list, tool_calls: list):
    """Attach ToolCall nodes to specific chunks (random selection)."""
    # Attach tool calls to roughly 30% of chunks
    selected_indices = random.sample(
        range(len(chunks)),
        k=min(len(chunks) // 3, len(tool_calls))
    )

    for idx, tool in zip(selected_indices, tool_calls):
        # Create the tool call record
        tool_record = db.records.create(
            label="ToolCall",
            data={
                "toolName": tool["name"],
                "arguments": tool["args"],
                "status": random.choice(["pending", "executing", "completed", "failed"]),
                "startedAt": (datetime.now() - timedelta(minutes=random.randint(1, 30))).isoformat(),
            }
        )

        # Link chunk to tool call
        db.records.attach(
            source=chunks[idx],
            target=tool_record,
            options={"type": "TRIGGERED_BY", "direction": "in"}
        )


def attach_document_citations(chunks: list, documents: list):
    """Attach Document nodes that chunks cite (random selection)."""
    # Roughly 40% of chunks cite a document
    selected_indices = random.sample(
        range(len(chunks)),
        k=int(len(chunks) * 0.4)
    )

    for idx in selected_indices:
        doc = random.choice(documents)

        # Create the document record
        doc_record = db.records.create(
            label="Document",
            data={
                "title": doc["title"],
                "type": doc["type"],
                "content": doc["content"],
            }
        )

        # Link chunk to document with CITES relationship
        db.records.attach(
            source=chunks[idx],
            target=doc_record,
            options={"type": "CITES", "direction": "out"}
        )


def create_conversation_metadata(conversation_id: str, stream_type: str):
    """Create metadata record for the conversation."""
    return db.records.create(
        label="Conversation",
        data={
            "conversationId": conversation_id,
            "streamType": stream_type,
            "createdAt": datetime.now().isoformat(),
            "status": random.choice(["active", "completed", "archived"]),
            "messageCount": 0,  # Will be updated after chunks are created
        }
    )


# ─────────────────────────────────────────────────────────────────
# Main Seeding Logic
# ─────────────────────────────────────────────────────────────────

def seed_all():
    """Seed all mock data."""
    print("\n🌱 Starting data seeding...\n")

    stream_types = ["general", "code_review", "data_analysis"]

    for i, conv_id in enumerate(CONVERSATION_IDS):
        stream_type = stream_types[i]

        # Check if already seeded
        if check_data_exists(conv_id):
            print(f"  ⏭️  Skipping {conv_id} - already seeded")
            continue

        print(f"  📝 Seeding conversation {conv_id} ({stream_type})...")
        start = time.time()

        # Create conversation metadata
        create_conversation_metadata(conv_id, stream_type)

        # Create stream chunks
        chunks = create_stream_chunks(conv_id, stream_type, num_chunks=8)

        # Attach tool calls to some chunks
        attach_tool_calls(chunks, TOOL_CALLS)

        # Attach document citations to some chunks
        attach_document_citations(chunks, DOCUMENTS)

        elapsed = time.time() - start
        print(f"     ✓ Created {len(chunks)} chunks in {elapsed:.2f}s")

    print("\n✅ Seeding complete!\n")


# ─────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db = RushDB(API_KEY)
    seed_all()
