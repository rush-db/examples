"""
seed.py — Generates mock LLM observability data for debugging tutorials.

This script creates a realistic graph of LLM application traces including:
- Sessions (user conversations)
- Messages (prompts and responses)
- Tool calls (function invocations)
- Errors (exceptions and failures)

All records are linked via RushDB relationships for graph traversal queries.
"""

import os
import random
import time
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv
from rushdb import RushDB

# Initialize Faker for realistic data generation
fake = Faker()
Faker.seed(42)
random.seed(42)

# Load environment variables
load_dotenv()

# Initialize RushDB client
API_TOKEN = os.getenv("RUSHDB_API_TOKEN")
if not API_TOKEN:
    raise ValueError("RUSHDB_API_TOKEN environment variable is required")

db = RushDB(API_TOKEN)

# Data templates for realistic mock data
MODELS = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "gpt-4-turbo"]

TOOL_DEFINITIONS = [
    {
        "name": "search_database",
        "description": "Search a vector database for relevant documents",
        "args_schema": {"query": "string", "limit": "integer"}
    },
    {
        "name": "get_user_context",
        "description": "Retrieve user profile and preferences",
        "args_schema": {"user_id": "string"}
    },
    {
        "name": "execute_code",
        "description": "Execute Python code in a sandboxed environment",
        "args_schema": {"code": "string", "timeout": "integer"}
    },
    {
        "name": "call_external_api",
        "description": "Make authenticated HTTP request to external service",
        "args_schema": {"endpoint": "string", "method": "string", "headers": "object"}
    },
    {
        "name": "format_response",
        "description": "Format data into markdown or structured output",
        "args_schema": {"data": "object", "format": "string"}
    },
    {
        "name": "log_event",
        "description": "Log an event to the analytics system",
        "args_schema": {"event_name": "string", "properties": "object"}
    }
]

ERROR_TEMPLATES = [
    {
        "error_type": "RateLimitError",
        "message": "API rate limit exceeded. Please retry after 60 seconds.",
        "severity": "warning",
        "retryable": True
    },
    {
        "error_type": "TimeoutError",
        "message": "Request to external service timed out after 30 seconds.",
        "severity": "error",
        "retryable": True
    },
    {
        "error_type": "AuthenticationError",
        "message": "Invalid API key or expired authentication token.",
        "severity": "critical",
        "retryable": False
    },
    {
        "error_type": "ValidationError",
        "message": "Tool arguments failed schema validation.",
        "severity": "warning",
        "retryable": False
    },
    {
        "error_type": "ContextOverflowError",
        "message": "Context window exceeded maximum token limit.",
        "severity": "error",
        "retryable": True
    }
]

USER_PROMPTS = [
    "What's the status of my recent order #12345?",
    "Can you help me find products similar to what I bought last month?",
    "Generate a report of my spending for Q3 2024.",
    "Help me troubleshoot why my API integration keeps failing.",
    "What are the best practices for handling authentication errors?",
    "Summarize the latest updates in the changelog.",
    "Create a Python script that processes our user data securely.",
    "Why is the recommendation engine returning unexpected results?"
]

LLM_RESPONSES = [
    "Based on your order history, order #12345 was delivered on [date]. The tracking number is XYZ123456.",
    "I've found 5 products similar to your recent purchases. Let me pull up the details for you.",
    "Here's your spending report for Q3 2024: Total spent: $2,345.67 across 47 transactions.",
    "I see the issue - your API integration is missing the authentication header. Let me walk you through the fix.",
    "For authentication error handling, you should implement exponential backoff and token refresh logic.",
    "The latest changelog includes: improved vector search accuracy, new batch processing API, and bug fixes.",
    "Here's a Python script that securely processes user data with encryption and rate limiting.",
    "The recommendation engine may be returning stale results due to a cache invalidation issue."
]


def cleanup_existing_data():
    """Remove previously seeded data to ensure idempotency."""
    labels_to_clean = ["SESSION", "MESSAGE", "TOOL_CALL", "ERROR"]
    for label in labels_to_clean:
        deleted = db.records.delete_many({
            "labels": [label],
            "where": {}
        })
        print(f"  [cleanup] Removed {deleted} records with label '{label}'")


def create_session(tx=None):
    """Create a user session record."""
    session = db.records.create(
        label="SESSION",
        data={
            "session_id": fake.uuid4(),
            "user_id": f"user_{random.randint(1000, 9999)}",
            "created_at": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
            "ip_address": fake.ipv4(),
            "user_agent": fake.user_agent(),
            "status": random.choice(["active", "completed", "failed"])
        },
        transaction=tx
    )
    return session


def create_message(session, role, content, model, tx=None):
    """Create a message record (prompt or response)."""
    tokens = random.randint(50, 500)
    message = db.records.create(
        label="MESSAGE",
        data={
            "role": role,
            "content": content,
            "model": model,
            "tokens_used": tokens,
            "latency_ms": random.randint(200, 5000),
            "created_at": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat()
        },
        transaction=tx
    )
    
    # Link message to session
    db.records.attach(
        source=session,
        target=message,
        options={"type": "CONTAINS", "direction": "out"},
        transaction=tx
    )
    
    return message


def create_tool_call(message, tx=None):
    """Create a tool call record and link it to a message."""
    tool = random.choice(TOOL_DEFINITIONS)
    
    # Generate realistic arguments based on tool
    args = {}
    if tool["name"] == "search_database":
        args = {"query": fake.sentence(nb_words=6), "limit": random.randint(3, 10)}
    elif tool["name"] == "get_user_context":
        args = {"user_id": f"user_{random.randint(1000, 9999)}"}
    elif tool["name"] == "execute_code":
        args = {"code": "import sys\nprint('hello')", "timeout": 30}
    elif tool["name"] == "call_external_api":
        args = {"endpoint": f"/api/v1/{fake.word()}", "method": "GET", "headers": {}}
    elif tool["name"] == "format_response":
        args = {"data": {"key": "value"}, "format": "markdown"}
    elif tool["name"] == "log_event":
        args = {"event_name": fake.word(), "properties": {"source": "llm_app"}}
    
    tool_call = db.records.create(
        label="TOOL_CALL",
        data={
            "tool_name": tool["name"],
            "tool_description": tool["description"],
            "arguments": args,
            "result": {"success": True, "data": fake.sentence()} if random.random() > 0.3 else None,
            "latency_ms": random.randint(50, 2000),
            "created_at": datetime.now().isoformat()
        },
        transaction=tx
    )
    
    # Link tool call to message (message triggers tool call)
    db.records.attach(
        source=message,
        target=tool_call,
        options={"type": "TRIGGERS", "direction": "out"},
        transaction=tx
    )
    
    return tool_call


def create_error(tool_call, tx=None):
    """"Create an error record and link it to a tool call."""
    error_template = random.choice(ERROR_TEMPLATES)
    
    error = db.records.create(
        label="ERROR",
        data={
            "error_type": error_template["error_type"],
            "message": error_template["message"],
            "severity": error_template["severity"],
            "retryable": error_template["retryable"],
            "stack_trace": f"Traceback (most recent call last):\n  File \"tool_executor.py\", line {random.randint(10, 100)}, in execute\n    {error_template['message']}",
            "occurred_at": datetime.now().isoformat()
        },
        transaction=tx
    )
    
    # Link error to tool call
    db.records.attach(
        source=tool_call,
        target=error,
        options={"type": "HAS_ERROR", "direction": "out"},
        transaction=tx
    )
    
    return error


def seed_observability_data():
    """Generate mock observability data with proper relationships."""
    print("\n[SEED] Generating mock LLM observability data...")
    
    session_count = 3
    messages_per_session = 4  # 2 prompt/response pairs
    tool_calls_per_message = 2
    error_probability = 0.4  # 40% of tool calls have errors
    
    total_sessions = 0
    total_messages = 0
    total_tool_calls = 0
    total_errors = 0
    
    with db.transactions.begin() as tx:
        for session_idx in range(session_count):
            session = create_session(tx=tx)
            total_sessions += 1
            
            if session_idx % 100 == 0:
                print(f"  [progress] Creating session {session_idx + 1}/{session_count}...")
            
            # Create prompt/response pairs
            prev_message = None
            for msg_pair_idx in range(messages_per_session):
                model = random.choice(MODELS)
                
                # User prompt
                prompt_content = random.choice(USER_PROMPTS)
                prompt = create_message(
                    session=session,
                    role="user",
                    content=prompt_content,
                    model=model,
                    tx=tx
                )
                total_messages += 1
                
                # Link to previous response if exists
                if prev_message:
                    db.records.attach(
                        source=prompt,
                        target=prev_message,
                        options={"type": "RESPONDS_TO", "direction": "out"},
                        transaction=tx
                    )
                
                # Model response
                response_content = random.choice(LLM_RESPONSES)
                response = create_message(
                    session=session,
                    role="assistant",
                    content=response_content,
                    model=model,
                    tx=tx
                )
                total_messages += 1
                
                # Response responds to prompt
                db.records.attach(
                    source=response,
                    target=prompt,
                    options={"type": "RESPONDS_TO", "direction": "out"},
                    transaction=tx
                )
                
                # Create tool calls triggered by response
                for tool_idx in range(tool_calls_per_message):
                    tool_call = create_tool_call(message=response, tx=tx)
                    total_tool_calls += 1
                    
                    # Some tool calls have errors
                    if random.random() < error_probability:
                        error = create_error(tool_call=tool_call, tx=tx)
                        total_errors += 1
                    
                    # Also link errors directly to sessions for some
                    if random.random() < 0.2:
                        error = create_error(tool_call=tool_call, tx=tx)
                        # Additional link to session
                        db.records.attach(
                            source=session,
                            target=error,
                            options={"type": "HAS_ERROR", "direction": "out"},
                            transaction=tx
                        )
                        total_errors += 1
                
                prev_message = response
    
    print(f"\n[✓] Seeded successfully:")
    print(f"    - {total_sessions} sessions")
    print(f"    - {total_messages} messages")
    print(f"    - {total_tool_calls} tool calls")
    print(f"    - {total_errors} errors")
    print(f"    - All records linked via graph relationships")


def main():
    """Main entry point for seeding observability data."""
    print("=" * 60)
    print("LLM Observability Data Seeder")
    print("=" * 60)
    
    # Test connection
    print("\n[CONNECTION] Testing RushDB connection...")
    try:
        labels = db.labels.find()
        print(f"[✓] Connected to RushDB")
        print(f"[INFO] Found {len(labels)} existing labels")
    except Exception as e:
        print(f"[✗] Connection failed: {e}")
        return
    
    # Cleanup existing data for idempotency
    print("\n[CLEANUP] Removing existing seeded data...")
    cleanup_existing_data()
    
    # Seed new data
    seed_observability_data()
    
    print("\n[COMPLETE] Seeding finished. Run main.py to analyze the data.")
    print("=" * 60)


if __name__ == "__main__":
    main()
