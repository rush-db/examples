"""
Main entry point for the streaming ingestion pipeline demo.

This script demonstrates:
1. Running the streaming pipeline to ingest events
2. Querying the ingested data for analysis
3. Building insights from agent interaction logs
"""
import os
import argparse
from dotenv import load_dotenv

from rushdb import RushDB
from pipeline import StreamingPipeline


def analyze_logs(db: RushDB) -> None:
    """
    Run analysis queries on the ingested agent interaction logs.
    
    Demonstrates various RushDB query patterns for log analysis.
    """
    print("\n" + "=" * 60)
    print("[ANALYSIS] Running log analysis queries...")
    print("=" * 60)
    
    # 1. Count records by label
    print("\n[1] Record Counts by Label:")
    for label in ["SESSION", "MESSAGE", "TOOL_CALL", "TOOL_RESULT"]:
        result = db.records.find({"labels": [label]})
        count = len(result.data) if result.data else 0
        print(f"  {label}: {count}")
    
    # 2. Session statistics
    print("\n[2] Session Statistics:")
    sessions = db.records.find({"labels": ["SESSION"]})
    if sessions.data:
        total_sessions = len(sessions.data)
        active = sum(1 for s in sessions.data if s.data.get("status") == "active")
        completed = sum(1 for s in sessions.data if s.data.get("status") == "completed")
        print(f"  Total Sessions: {total_sessions}")
        print(f"  Active: {active}, Completed: {completed}")
    
    # 3. Tool usage analysis
    print("\n[3] Tool Usage Analysis:")
    tool_calls = db.records.find({"labels": ["TOOL_CALL"]})
    if tool_calls.data:
        tool_counts: dict = {}
        for call in tool_calls.data:
            tool_name = call.data.get("tool_name", "unknown")
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
        print("  Top Tools:")
        for tool, count in sorted_tools[:5]:
            print(f"    {tool}: {count} calls")
    
    # 4. Message type distribution
    print("\n[4] Message Type Distribution:")
    messages = db.records.find({"labels": ["MESSAGE"]})
    if messages.data:
        user_msgs = sum(1 for m in messages.data if m.data.get("type") == "user_message")
        assistant_msgs = sum(1 for m in messages.data if m.data.get("type") == "assistant_message")
        print(f"  User Messages: {user_msgs}")
        print(f"  Assistant Messages: {assistant_msgs}")
    
    # 5. Agent activity
    print("\n[5] Agent Activity:")
    agents_result = db.records.find({"labels": ["MESSAGE"]})
    if agents_result.data:
        agent_counts: dict = {}
        for msg in agents_result.data:
            agent_id = msg.data.get("agent_id", "unknown")
            agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
        
        for agent, count in agent_counts.items():
            print(f"  {agent}: {count} messages")
    
    # 6. Tool result status
    print("\n[6] Tool Result Status:")
    results = db.records.find({"labels": ["TOOL_RESULT"]})
    if results.data:
        success = sum(1 for r in results.data if r.data.get("status") == "success")
        error = sum(1 for r in results.data if r.data.get("status") == "error")
        print(f"  Success: {success}")
        print(f"  Errors: {error}")
        
        # Average execution time
        times = [
            r.data.get("execution_time_ms", 0)
            for r in results.data
            if r.data.get("execution_time_ms")
        ]
        if times:
            avg_time = sum(times) / len(times)
            print(f"  Average Execution Time: {avg_time:.2f}ms")
    
    # 7. Session timeline (latest events)
    print("\n[7] Recent Sessions:")
    recent_sessions = db.records.find({
        "labels": ["SESSION"],
        "orderBy": {"timestamp": "desc"},
        "limit": 5
    })
    if recent_sessions.data:
        for session in recent_sessions.data:
            print(f"  {session.data.get('session_id')}: {session.data.get('status')}")
    
    print("\n" + "=" * 60)
    print("[ANALYSIS] Complete")
    print("=" * 60)


def demonstrate_query_patterns(db: RushDB) -> None:
    """
    Demonstrate advanced RushDB query patterns for log analysis.
    """
    print("\n" + "-" * 60)
    print("[DEMO] Advanced Query Patterns")
    print("-" * 60)
    
    # Pattern 1: Find all events for a specific session
    print("\n[Pattern 1] Events for a specific session:")
    sessions = db.records.find({"labels": ["SESSION"], "limit": 1})
    if sessions.data:
        session_id = sessions.data[0].data.get("session_id")
        print(f"  Querying session: {session_id}")
        
        events = db.records.find({
            "labels": ["MESSAGE", "TOOL_CALL", "TOOL_RESULT"],
            "where": {"session_id": session_id},
            "orderBy": {"timestamp": "asc"}
        })
        print(f"  Found {len(events.data)} events")
    
    # Pattern 2: Find events via relationship traversal
    print("\n[Pattern 2] Events via relationship (BELONGS_TO):")
    if sessions.data:
        session_record = sessions.data[0]
        related = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "SESSION": {"$id": session_record.id}
            }
        })
        print(f"  Found {len(related.data)} related messages")
    
    # Pattern 3: Filter by tool name
    print("\n[Pattern 3] Tool calls for specific tool:")
    tool_calls = db.records.find({
        "labels": ["TOOL_CALL"],
        "where": {"tool_name": "web_search"}
    })
    print(f"  web_search calls: {len(tool_calls.data)}")
    
    # Pattern 4: Pagination
    print("\n[Pattern 4] Paginated messages (limit 5, skip 0):")
    paginated = db.records.find({
        "labels": ["MESSAGE"],
        "limit": 5,
        "skip": 0,
        "orderBy": {"timestamp": "desc"}
    })
    print(f"  Page 1: {len(paginated.data)} messages")
    
    paginated2 = db.records.find({
        "labels": ["MESSAGE"],
        "limit": 5,
        "skip": 5,
        "orderBy": {"timestamp": "desc"}
    })
    print(f"  Page 2: {len(paginated2.data)} messages")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Agent Interaction Log Streaming Pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["all", "ingest", "analyze"],
        default="all",
        help="Execution mode: all (default), ingest only, or analyze only"
    )
    parser.add_argument(
        "--events",
        type=int,
        default=None,
        help="Number of events to generate (overrides DEMO_EVENT_COUNT env var)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Batch size for writes (overrides BATCH_SIZE env var)"
    )
    
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    # Validate API token
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("ERROR: RUSHDB_API_TOKEN not found in environment")
        print("Please create a .env file with your RushDB API token.")
        print("See .env.example for reference.")
        return 1
    
    # Initialize RushDB client
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_token, url=url) if url else RushDB(api_token)
    
    print("=" * 60)
    print("Agent Interaction Log Streaming Pipeline")
    print("=" * 60)
    
    # Run ingestion if requested
    if args.mode in ["all", "ingest"]:
        # Configuration from args or environment
        batch_size = args.batch_size or int(os.getenv("BATCH_SIZE", "10"))
        stream_delay = float(os.getenv("STREAM_DELAY", "0.1"))
        
        if args.events:
            session_count = args.events // 15
        else:
            session_count = int(os.getenv("DEMO_EVENT_COUNT", "50")) // 15
        
        print(f"\n[CONFIG] Batch size: {batch_size}, Sessions: {session_count}")
        print(f"[CONFIG] API URL: {url or 'https://api.rushdb.com'}")
        
        # Create and run pipeline
        pipeline = StreamingPipeline(
            api_token=api_token,
            url=url,
            batch_size=batch_size,
            stream_delay=stream_delay,
        )
        
        stats = pipeline.ingest_stream(session_count=session_count)
        
        print(f"\n[STATS] Pipeline Statistics:")
        print(f"  Events processed: {stats['events_processed']}")
        print(f"  Batches committed: {stats['batches_committed']}")
        print(f"  Errors: {stats.get('errors', 0)}")
        print(f"  Duration: {stats.get('duration_seconds', 0):.2f}s")
    
    # Run analysis if requested
    if args.mode in ["all", "analyze"]:
        analyze_logs(db)
        demonstrate_query_patterns(db)
    
    return 0


if __name__ == "__main__":
    exit(main())
