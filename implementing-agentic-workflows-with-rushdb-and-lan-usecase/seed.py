"""
Seed script for agentic workflow example.

Creates realistic mock data:
- Agent sessions with varying states
- Tool calls with realistic outputs
- Conversation turns connected via graph relationships
- Vector embeddings for semantic search

This data demonstrates RushDB's ability to handle complex, interrelated
agent memory patterns without requiring separate systems.
"""

import os
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment variables")

db = RushDB(api_key)

# Initialize embedding model
print("Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Sample data for realistic agent sessions
AGENT_TASKS = [
    "analyze_user_data",
    "generate_report",
    "debug_production_issue",
    "research_competitor_features",
    "optimize_database_queries"
]

TOOLS = [
    {"name": "search_knowledge_base", "description": "Search internal documentation"},
    {"name": "execute_python", "description": "Run Python code safely"},
    {"name": "query_database", "description": "Query the main database"},
    {"name": "fetch_api_data", "description": "Fetch data from external APIs"},
    {"name": "format_response", "description": "Format output for user"},
]

TOOL_OUTPUTS = {
    "search_knowledge_base": [
        "Found 3 relevant documents about async Python patterns",
        "Retrieved 5 articles on database optimization techniques",
        "Found no matches for query, suggesting broader search terms",
        "Located 2 recent papers on distributed systems design"
    ],
    "execute_python": [
        "Code executed successfully, returned 42 results",
        "Executed in 0.23s, memory usage: 128MB",
        "Function returned None, checking logic...",
        "Error: Division by zero, handled gracefully"
    ],
    "query_database": [
        "Query returned 1,247 rows in 0.45s",
        "No results found for the given filters",
        "Query timeout after 30s, suggests adding indexes",
        "Aggregation complete: avg=123.45, count=5000"
    ],
    "fetch_api_data": [
        "Fetched 50 records from external API, cached for 5 minutes",
        "API rate limited, used cached response from 10 minutes ago",
        "Successfully authenticated and retrieved user profile",
        "API returned 404, endpoint may have changed"
    ],
    "format_response": [
        "Response formatted as markdown table with 6 columns",
        "Generated JSON output with proper schema validation",
        "Created visualization data for 3 charts",
        "Formatted as plain text with bullet points"
    ]
}

CONVERSATION_TURNS = [
    {"role": "user", "content": "Can you analyze the user signup funnel?", "intent": "data_analysis"},
    {"role": "assistant", "content": "I'll query the database for signup data and analyze conversion rates.", "intent": "planning"},
    {"role": "assistant", "content": "Found 12,450 signups this month. Conversion rate is 23.4%.", "intent": "data_reporting"},
    {"role": "user", "content": "What about the drop-off points?", "intent": "data_analysis"},
    {"role": "assistant", "content": "The main drop-off is at the payment step. 67% of users abandon there.", "intent": "data_analysis"},
    {"role": "user", "content": "Can you run a Python script to calculate LTV?", "intent": "code_execution"},
    {"role": "assistant", "content": "Running the LTV calculation script now...", "intent": "code_execution"},
    {"role": "assistant", "content": "Average LTV is $847. Top 20% of users have LTV > $2000.", "intent": "data_reporting"},
    {"role": "user", "content": "Search the docs for similar issues in the past.", "intent": "documentation_search"},
    {"role": "assistant", "content": "Found 3 similar issues from last quarter. Two were resolved by adding indexes.", "intent": "documentation_search"},
    {"role": "user", "content": "Generate a report on Q4 performance.", "intent": "report_generation"},
    {"role": "assistant", "content": "Compiling Q4 metrics from multiple data sources...", "intent": "report_generation"},
    {"role": "assistant", "content": "Report generated: 45 pages, includes charts and recommendations.", "intent": "report_generation"},
    {"role": "user", "content": "Debug why the recommendation engine is slow.", "intent": "debugging"},
    {"role": "assistant", "content": "Running profiling tools on the recommendation service...", "intent": "debugging"},
    {"role": "assistant", "content": "Found bottleneck: N+1 query in user preferences lookup.", "intent": "debugging"},
]


def generate_embedding(text: str) -> list:
    """Generate vector embedding for text."""
    return embedder.encode(text).tolist()


def check_data_exists() -> bool:
    """Check if seed data already exists."""
    result = db.records.find({"labels": ["SESSION"], "limit": 1})
    return result.total > 0


def clear_existing_data():
    """Clear existing seed data for clean re-seed."""
    print("Clearing existing seed data...")
    db.records.delete({"labels": ["SESSION"], "where": {}})
    db.records.delete({"labels": ["TOOL_CALL"], "where": {}})
    db.records.delete({"labels": ["CONVERSATION_TURN"], "where": {}})
    time.sleep(1)  # Allow deletion to propagate


def create_vector_indexes():
    """Create vector indexes for semantic search."""
    print("Creating vector indexes...")
    
    # Check if indexes already exist
    try:
        existing = db.ai.indexes.find()
        index_labels = [idx['label'] for idx in existing.data]
    except Exception:
        index_labels = []
    
    # Create CONVERSATION_TURN index
    if "CONVERSATION_TURN" not in index_labels:
        try:
            db.ai.indexes.create({
                "label": "CONVERSATION_TURN",
                "propertyName": "content",
                "sourceType": "external",
                "dimensions": 384,
                "similarityFunction": "cosine"
            })
            print("  Created CONVERSATION_TURN vector index")
        except Exception as e:
            print(f"  Index may already exist: {e}")
    
    # Create TOOL_CALL index
    if "TOOL_CALL" not in index_labels:
        try:
            db.ai.indexes.create({
                "label": "TOOL_CALL",
                "propertyName": "output",
                "sourceType": "external",
                "dimensions": 384,
                "similarityFunction": "cosine"
            })
            print("  Created TOOL_CALL vector index")
        except Exception as e:
            print(f"  Index may already exist: {e}")


def seed_sessions():
    """Create agent sessions with tool calls and conversation turns."""
    print("\nSeeding agent sessions...")
    
    # Create 3 sessions with different states
    sessions_data = []
    for i in range(3):
        task = random.choice(AGENT_TASKS)
        status = random.choice(["completed", "in_progress", "failed", "completed"])
        
        session_data = {
            "task": task,
            "status": status,
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat(),
            "confidence_score": round(random.uniform(0.7, 0.99), 2)
        }
        sessions_data.append(session_data)
    
    # Create sessions in a transaction for atomicity
    sessions = []
    with db.transactions.begin() as tx:
        for i, session_data in enumerate(sessions_data):
            session = db.records.create(
                label="SESSION",
                data=session_data,
                transaction=tx
            )
            sessions.append(session)
            print(f"  Created session {i+1}: {session_data['task']} ({session_data['status']})")
    
    return sessions


def seed_tool_calls(sessions: list):
    """Create tool calls for each session with relationships."""
    print("\nSeeding tool calls...")
    
    all_tool_calls = []
    
    for session_idx, session in enumerate(sessions):
        # Create 3-6 tool calls per session
        num_calls = random.randint(3, 6)
        session_tool_calls = []
        
        with db.transactions.begin() as tx:
            for call_idx in range(num_calls):
                tool = random.choice(TOOLS)
                output = random.choice(TOOL_OUTPUTS.get(tool["name"], ["Operation completed"]))
                
                tool_call_data = {
                    "tool": tool["name"],
                    "tool_description": tool["description"],
                    "input": f"Query #{call_idx + 1} for {session.data['task']}",
                    "output": output,
                    "execution_time_ms": random.randint(50, 5000),
                    "success": random.random() > 0.1  # 90% success rate
                }
                
                tool_call = db.records.create(
                    label="TOOL_CALL",
                    data=tool_call_data,
                    vectors=[{"propertyName": "output", "vector": generate_embedding(output)}],
                    transaction=tx
                )
                
                # Attach to session with relationship
                db.records.attach(
                    source=session,
                    target=tool_call,
                    options={"type": "INITIATED", "direction": "out"},
                    transaction=tx
                )
                
                # Link consecutive tool calls
                if session_tool_calls:
                    db.records.attach(
                        source=session_tool_calls[-1],
                        target=tool_call,
                        options={"type": "FOLLOWED_BY", "direction": "out"},
                        transaction=tx
                    )
                
                session_tool_calls.append(tool_call)
                all_tool_calls.append(tool_call)
        
        print(f"  Session {session_idx + 1}: Created {len(session_tool_calls)} tool calls")
    
    return all_tool_calls


def seed_conversation_turns(sessions: list):
    """Create conversation turns linked to sessions."""
    print("\nSeeding conversation turns...")
    
    all_turns = []
    
    for session_idx, session in enumerate(sessions):
        # Select random subset of conversation turns for this session
        session_turns = random.sample(CONVERSATION_TURNS, min(len(CONVERSATION_TURNS), random.randint(4, 8)))
        session_turn_objects = []
        
        with db.transactions.begin() as tx:
            for turn_idx, turn_data in enumerate(session_turns):
                turn = db.records.create(
                    label="CONVERSATION_TURN",
                    data={
                        "role": turn_data["role"],
                        "content": turn_data["content"],
                        "intent": turn_data["intent"],
                        "turn_number": turn_idx + 1,
                        "timestamp": (datetime.now() - timedelta(
                            days=random.randint(1, 5),
                            hours=random.randint(0, 12)
                        )).isoformat()
                    },
                    vectors=[{"propertyName": "content", "vector": generate_embedding(turn_data["content"])}],
                    transaction=tx
                )
                
                # Link to session
                db.records.attach(
                    source=turn,
                    target=session,
                    options={"type": "PART_OF", "direction": "out"},
                    transaction=tx
                )
                
                # Link consecutive turns
                if session_turn_objects:
                    db.records.attach(
                        source=session_turn_objects[-1],
                        target=turn,
                        options={"type": "PRECEDES", "direction": "out"},
                        transaction=tx
                    )
                
                session_turn_objects.append(turn)
                all_turns.append(turn)
        
        print(f"  Session {session_idx + 1}: Created {len(session_turn_objects)} conversation turns")
    
    return all_turns


def create_cross_session_relationships(tool_calls: list):
    """Create relationships between tool calls across sessions for interesting graph traversals."""
    print("\nCreating cross-session relationships...")
    
    # Find similar tool calls (same tool name) and create SUBSEQUENT_OF relationships
    tool_groups = {}
    for tc in tool_calls:
        tool_name = tc.data.get("tool")
        if tool_name not in tool_groups:
            tool_groups[tool_name] = []
        tool_groups[tool_name].append(tc)
    
    with db.transactions.begin() as tx:
        for tool_name, calls in tool_groups.items():
            if len(calls) > 1:
                # Link first occurrence to later ones as similar patterns
                for i in range(1, min(len(calls), 3)):
                    db.records.attach(
                        source=calls[0],
                        target=calls[i],
                        options={"type": "SIMILAR_TO", "direction": "out"},
                        transaction=tx
                    )
    
    print(f"  Created cross-session relationships for {len(tool_groups)} tool types")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Agentic Workflow Seed Data Generator")
    print("=" * 60)
    
    # Check if data already exists
    if check_data_exists():
        response = input("\nSeed data already exists. Clear and reseed? (y/N): ")
        if response.lower() != 'y':
            print("Seeding cancelled.")
            return
        clear_existing_data()
    
    # Create vector indexes
    create_vector_indexes()
    
    # Seed data
    sessions = seed_sessions()
    tool_calls = seed_tool_calls(sessions)
    conversation_turns = seed_conversation_turns(sessions)
    create_cross_session_relationships(tool_calls)
    
    # Wait for vectors to be indexed
    print("\nWaiting for vector indexes to propagate...")
    time.sleep(2)
    
    # Summary
    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"  Sessions created: {len(sessions)}")
    print(f"  Tool calls created: {len(tool_calls)}")
    print(f"  Conversation turns created: {len(conversation_turns)}")
    print("\nThe database is now seeded with realistic agent memory data.")
    print("Run 'python main.py' to see the agentic workflow in action.")


if __name__ == "__main__":
    main()
