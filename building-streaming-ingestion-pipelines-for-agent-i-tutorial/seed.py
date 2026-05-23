"""
Seed script for generating historical agent interaction data.

This script creates a batch of realistic agent interaction sessions
for testing and demonstration purposes. It's idempotent and can
be run multiple times safely.
"""
import os
from dotenv import load_dotenv

from rushdb import RushDB
from simulator import EventSimulator


def seed_data(session_count: int = 5) -> None:
    """
    Seed RushDB with historical agent interaction data.
    
    Args:
        session_count: Number of sessions to generate
    """
    # Load environment
    load_dotenv()
    
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        raise ValueError("RUSHDB_API_TOKEN not found in environment")
    
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_token, url=url) if url else RushDB(api_token)
    
    print(f"[SEED] Starting data seeding...")
    print(f"[SEED] Target sessions: {session_count}")
    
    # Create simulator
    simulator = EventSimulator(agent_count=2, events_per_session=(20, 40))
    
    # Count existing data
    existing = db.records.find({"labels": ["SESSION"]})
    existing_count = len(existing.data) if existing.data else 0
    print(f"[SEED] Existing sessions in database: {existing_count}")
    
    # Track created sessions for bulk operations
    sessions = []
    messages = []
    tool_calls = []
    tool_results = []
    
    # Generate all events first
    print(f"[SEED] Generating events...")
    for i, session in enumerate(simulator.generate_sessions(session_count)):
        agent = next(a for a in simulator.agents if a.agent_id == session.agent_id)
        
        for event_data in simulator.generate_events_for_session(session, agent):
            label = event_data["label"]
            data = event_data["data"]
            
            if label == "SESSION":
                sessions.append(data)
            elif label == "MESSAGE":
                messages.append(data)
            elif label == "TOOL_CALL":
                tool_calls.append(data)
            elif label == "TOOL_RESULT":
                tool_results.append(data)
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"[SEED] Progress: {i + 1} sessions processed")
    
    print(f"[SEED] Generated {len(sessions)} sessions, {len(messages)} messages, {len(tool_calls)} tool calls")
    
    # Bulk insert with transactions
    print(f"[SEED] Inserting data into RushDB...")
    
    with db.transactions.begin() as tx:
        # Create sessions first
        created_sessions = db.records.create_many(
            label="SESSION",
            data=sessions,
            transaction=tx
        )
        print(f"[SEED] Created {len(created_sessions.data)} sessions")
        
        # Create index for session lookup
        session_map = {
            s.data.get("session_id"): s
            for s in created_sessions.data
            if s.data.get("type") == "session_start"
        }
        
        # Create messages
        if messages:
            created_messages = db.records.create_many(
                label="MESSAGE",
                data=messages,
                transaction=tx
            )
            print(f"[SEED] Created {len(created_messages.data)} messages")
            
            # Link messages to sessions
            for msg in created_messages.data:
                session_id = msg.data.get("session_id")
                if session_id in session_map:
                    db.records.attach(
                        source=msg,
                        target=session_map[session_id],
                        options={"type": "BELONGS_TO"},
                        transaction=tx
                    )
        
        # Create tool calls
        if tool_calls:
            created_tools = db.records.create_many(
                label="TOOL_CALL",
                data=tool_calls,
                transaction=tx
            )
            print(f"[SEED] Created {len(created_tools.data)} tool calls")
            
            # Link tool calls to sessions
            for tool in created_tools.data:
                session_id = tool.data.get("session_id")
                if session_id in session_map:
                    db.records.attach(
                        source=tool,
                        target=session_map[session_id],
                        options={"type": "BELONGS_TO"},
                        transaction=tx
                    )
        
        # Create tool results
        if tool_results:
            created_results = db.records.create_many(
                label="TOOL_RESULT",
                data=tool_results,
                transaction=tx
            )
            print(f"[SEED] Created {len(created_results.data)} tool results")
            
            # Link tool results to sessions
            for result in created_results.data:
                session_id = result.data.get("session_id")
                if session_id in session_map:
                    db.records.attach(
                        source=result,
                        target=session_map[session_id],
                        options={"type": "BELONGS_TO"},
                        transaction=tx
                    )
    
    print(f"[SEED] Data seeding completed successfully!")
    
    # Verify insertion
    print("\n[SEED] Verification:")
    for label in ["SESSION", "MESSAGE", "TOOL_CALL", "TOOL_RESULT"]:
        result = db.records.find({"labels": [label]})
        count = len(result.data) if result.data else 0
        print(f"  {label}: {count} records")


def clear_all_data() -> None:
    """Clear all agent interaction data from RushDB."""
    load_dotenv()
    
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        raise ValueError("RUSHDB_API_TOKEN not found in environment")
    
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_token, url=url) if url else RushDB(api_token)
    
    print("[CLEAR] Deleting all agent interaction records...")
    
    for label in ["TOOL_RESULT", "TOOL_CALL", "MESSAGE", "SESSION"]:
        result = db.records.delete({"labels": [label], "where": {}})
        print(f"[CLEAR] Deleted {label} records")
    
    print("[CLEAR] All data cleared.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed agent interaction data")
    parser.add_argument(
        "--sessions",
        type=int,
        default=5,
        help="Number of sessions to generate (default: 5)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all existing data before seeding"
    )
    
    args = parser.parse_args()
    
    if args.clear:
        confirm = input("This will delete ALL agent interaction records. Continue? (y/N): ")
        if confirm.lower() == "y":
            clear_all_data()
        else:
            print("Cancelled.")
            exit(0)
    
    seed_data(session_count=args.sessions)
