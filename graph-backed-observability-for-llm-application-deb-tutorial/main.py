"""
main.py — Graph-backed Observability for LLM Application Debugging

This script demonstrates how RushDB's property graph model enables powerful
observability and debugging for LLM applications.

We query the observability graph to answer questions like:
1. What happened in a specific session?
2. Which tool calls failed and why?
3. What are the error correlation patterns?
4. How do I reconstruct a full execution trace?
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
API_TOKEN = os.getenv("RUSHDB_API_TOKEN")
if not API_TOKEN:
    raise ValueError("RUSHDB_API_TOKEN environment variable is required")


db = RushDB(API_TOKEN)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print("=" * 60)


def query_1_session_trace():
    """
    Query 1: Reconstruct a complete session trace.
    
    Get all messages in a session, ordered by creation time,
    and show the tool calls each response triggered.
    """
    print_section("QUERY 1: Session Trace Reconstruction")
    print("Finding messages in the most recent session...")
    
    # Find the most recent session
    sessions = db.records.find({
        "labels": ["SESSION"],
        "orderBy": {"created_at": "desc"},
        "limit": 1
    })
    
    if not sessions:
        print("  [EMPTY] No sessions found. Run seed.py first.")
        return
    
    session = sessions[0]
    print(f"\n  Session ID: {session.data.get('session_id')}")
    print(f"  User ID: {session.data.get('user_id')}")
    print(f"  Status: {session.data.get('status')}")
    print(f"  Created: {session.data.get('created_at')}")
    
    # Find all messages in this session via graph traversal
    # RushDB automatically traverses CONTAINS relationship
    messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "SESSION": {"$id": session.id}
        },
        "orderBy": {"created_at": "asc"}
    })
    
    print(f"\n  Messages ({len(messages)} total):")
    for msg in messages:
        role = msg.data.get('role', 'unknown').upper()
        content_preview = msg.data.get('content', '')[:60] + "..."
        model = msg.data.get('model', 'unknown')
        tokens = msg.data.get('tokens_used', 0)
        latency = msg.data.get('latency_ms', 0)
        
        print(f"\n    [{role}]")
        print(f"      Content: {content_preview}")
        print(f"      Model: {model} | Tokens: {tokens} | Latency: {latency}ms")
        
        # Find tool calls triggered by this message
        tool_calls = db.records.find({
            "labels": ["TOOL_CALL"],
            "where": {
                "MESSAGE": {"$id": msg.id}
            }
        })
        
        if tool_calls:
            print(f"      Tool Calls:")
            for tc in tool_calls:
                tool_name = tc.data.get('tool_name', 'unknown')
                tc_latency = tc.data.get('latency_ms', 0)
                
                # Check if this tool call has an error
                errors = db.records.find({
                    "labels": ["ERROR"],
                    "where": {
                        "TOOL_CALL": {"$id": tc.id}
                    }
                })
                
                status = "✓" if not errors else "✗ ERROR"
                print(f"        - {tool_name} ({tc_latency}ms) {status}")


def query_2_error_analysis():
    """
    Query 2: Error Analysis — Find all errors and correlate with tool calls.
    
    This demonstrates graph traversal for debugging: error → tool → message → session.
    """
    print_section("QUERY 2: Error Analysis & Correlation")
    print("Finding all errors and tracing back to their source...")
    
    # Find all errors
    errors = db.records.find({
        "labels": ["ERROR"],
        "orderBy": {"occurred_at": "desc"}
    })
    
    if not errors:
        print("  [EMPTY] No errors found.")
        return
    
    print(f"\n  Found {len(errors)} errors total:")
    
    for idx, error in enumerate(errors[:5], 1):  # Show first 5
        print(f"\n  --- Error #{idx} ---")
        print(f"      Type: {error.data.get('error_type')}")
        print(f"      Severity: {error.data.get('severity')}")
        print(f"      Message: {error.data.get('message')}")
        print(f"      Retryable: {error.data.get('retryable')}")
        print(f"      Time: {error.data.get('occurred_at')}")
        
        # Trace back: Error → Tool Call → Message → Session
        # Find the tool call that caused this error
        tool_calls = db.records.find({
            "labels": ["TOOL_CALL"],
            "where": {
                "ERROR": {"$id": error.id}
            }
        })
        
        if tool_calls:
            tool_call = tool_calls[0]
            print(f"\n      ← Caused by Tool: {tool_call.data.get('tool_name')}")
            print(f"        Arguments: {tool_call.data.get('arguments')}")
            
            # Find the message that triggered this tool
            triggering_messages = db.records.find({
                "labels": ["MESSAGE"],
                "where": {
                    "TOOL_CALL": {"$id": tool_call.id}
                }
            })
            
            if triggering_messages:
                msg = triggering_messages[0]
                print(f"\n      ← Triggered by Message (role: {msg.data.get('role')})")
                
                # Find the session
                sessions = db.records.find({
                    "labels": ["SESSION"],
                    "where": {
                        "MESSAGE": {"$id": msg.id}
                    }
                })
                
                if sessions:
                    session = sessions[0]
                    print(f"\n      ← Part of Session: {session.data.get('session_id')}")
                    print(f"        User: {session.data.get('user_id')}")


def query_3_tool_call_chains():
    """
    Query 3: Tool Call Chain Analysis.
    
    Find which tool call patterns are most common and which ones fail.
    This helps identify problematic tool combinations.
    """
    print_section("QUERY 3: Tool Call Pattern Analysis")
    print("Analyzing tool call patterns and success rates...")
    
    # Find all tool calls
    tool_calls = db.records.find({
        "labels": ["TOOL_CALL"]
    })
    
    if not tool_calls:
        print("  [EMPTY] No tool calls found.")
        return
    
    # Group by tool name and calculate failure rate
    tool_stats = {}
    for tc in tool_calls:
        tool_name = tc.data.get('tool_name', 'unknown')
        if tool_name not in tool_stats:
            tool_stats[tool_name] = {"total": 0, "errors": 0}
        
        tool_stats[tool_name]["total"] += 1
        
        # Check for errors
        errors = db.records.find({
            "labels": ["ERROR"],
            "where": {
                "TOOL_CALL": {"$id": tc.id}
            }
        })
        if errors:
            tool_stats[tool_name]["errors"] += 1
    
    print(f"\n  Tool Call Statistics:")
    print(f"  {'Tool Name':<25} {'Total':<10} {'Errors':<10} {'Fail Rate':<10}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10}")
    
    for tool_name, stats in sorted(tool_stats.items(), key=lambda x: x[1]['errors'], reverse=True):
        fail_rate = (stats['errors'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {tool_name:<25} {stats['total']:<10} {stats['errors']:<10} {fail_rate:.1f}%")
    
    # Show average latency per tool
    print(f"\n  Average Latency (ms):")
    tool_latencies = {}
    for tc in tool_calls:
        tool_name = tc.data.get('tool_name', 'unknown')
        latency = tc.data.get('latency_ms', 0)
        if tool_name not in tool_latencies:
            tool_latencies[tool_name] = []
        tool_latencies[tool_name].append(latency)
    
    for tool_name, latencies in sorted(tool_latencies.items()):
        avg_latency = sum(latencies) / len(latencies)
        print(f"    {tool_name:<25} {avg_latency:.0f}ms (n={len(latencies)})")


def query_4_latency_analysis():
    """
    Query 4: Latency Analysis.
    
    Find messages with high latency and trace back to root cause.
    """
    print_section("QUERY 4: High Latency Analysis")
    print("Finding messages with high latency to identify bottlenecks...")
    
    # Find messages with latency > 2000ms
    slow_messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "latency_ms": {"$gt": 2000}
        },
        "orderBy": {"latency_ms": "desc"},
        "limit": 5
    })
    
    if not slow_messages:
        print("  [EMPTY] No slow messages found (>2000ms threshold).")
        return
    
    print(f"\n  Found {len(slow_messages)} slow messages:")
    
    for msg in slow_messages:
        print(f"\n  Message (ID: {msg.id[:16]}...)")
        print(f"    Role: {msg.data.get('role')}")
        print(f"    Model: {msg.data.get('model')}")
        print(f"    Latency: {msg.data.get('latency_ms')}ms")
        print(f"    Tokens: {msg.data.get('tokens_used')}")
        
        # Find associated tool calls and their latencies
        tool_calls = db.records.find({
            "labels": ["TOOL_CALL"],
            "where": {
                "MESSAGE": {"$id": msg.id}
            }
        })
        
        if tool_calls:
            total_tool_latency = sum(tc.data.get('latency_ms', 0) for tc in tool_calls)
            print(f"    Tool Calls: {len(tool_calls)} (total: {total_tool_latency}ms)")
            for tc in tool_calls:
                print(f"      - {tc.data.get('tool_name')}: {tc.data.get('latency_ms')}ms")


def query_5_semantic_error_search():
    """
    Query 5: Semantic Search for Similar Errors.
    
    This demonstrates how RushDB's vector search can help find related errors.
    We create a temporary vector index on error messages and search for similar patterns.
    
    Note: This requires the AI/embedding feature enabled on your RushDB account.
    """
    print_section("QUERY 5: Semantic Error Search")
    print("Using vector search to find similar error patterns...")
    print("\n  [INFO] This query requires RushDB's AI search feature enabled.")
    print("  [INFO] Checking if vector indexes are available...")
    
    try:
        indexes = db.ai.indexes.find()
        print(f"\n  Found {len(indexes)} existing indexes:")
        for idx in indexes:
            print(f"    - {idx['label']}.{idx['propertyName']} ({idx['status']})")
    except Exception as e:
        print(f"  [SKIP] Could not query indexes: {e}")
        print("  [INFO] Proceeding with label-based error search instead.")
        
        # Fallback: Search errors by severity
        critical_errors = db.records.find({
            "labels": ["ERROR"],
            "where": {
                "severity": "critical"
            }
        })
        
        if critical_errors:
            print(f"\n  Found {len(critical_errors)} CRITICAL errors:")
            for err in critical_errors:
                print(f"    - {err.data.get('error_type')}: {err.data.get('message')}")
        else:
            print("  [EMPTY] No critical errors found.")


def query_6_cross_session_analysis():
    """
    Query 6: Cross-Session Pattern Analysis.
    
    Find sessions that share similar error patterns or tool call sequences.
    This helps identify systemic issues affecting multiple users.
    """
    print_section("QUERY 6: Cross-Session Pattern Analysis")
    print("Finding error patterns across multiple sessions...")
    
    # Find sessions that have errors
    sessions_with_errors = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "status": "failed"
        }
    })
    
    # Also find sessions that contain errors via CONTAINS relationship
    all_sessions = db.records.find({
        "labels": ["SESSION"]
    })
    
    sessions_with_direct_errors = []
    for session in all_sessions:
        errors = db.records.find({
            "labels": ["ERROR"],
            "where": {
                "SESSION": {"$id": session.id}
            }
        })
        if errors:
            sessions_with_direct_errors.append((session, errors))
    
    print(f"\n  Sessions with failed status: {len(sessions_with_errors)}")
    print(f"  Sessions with linked errors: {len(sessions_with_direct_errors)}")
    
    # Group errors by type
    error_types = {}
    all_errors = db.records.find({"labels": ["ERROR"]})
    
    for error in all_errors:
        error_type = error.data.get('error_type', 'unknown')
        if error_type not in error_types:
            error_types[error_type] = {"count": 0, "severity": error.data.get('severity')}
        error_types[error_type]["count"] += 1
    
    print(f"\n  Error Type Distribution:")
    for error_type, stats in sorted(error_types.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"    {error_type:<25} {stats['count']} occurrences (severity: {stats['severity']})")


def main():
    """"Run all observability queries."""
    print("=" * 60)
    print("Graph-backed Observability for LLM Application Debugging")
    print("=" * 60)
    print("\nThis demo shows how RushDB's property graph model enables")
    print("powerful observability queries for LLM applications.")
    
    # Test connection
    print("\n[CONNECTION] Testing RushDB connection...")
    try:
        labels = db.labels.find()
        print(f"[✓] Connected successfully!")
        print(f"[INFO] Found {len(labels)} labels in workspace")
    except Exception as e:
        print(f"[✗] Connection failed: {e}")
        print("\nPlease ensure:")
        print("  1. RUSHDB_API_TOKEN is set in .env")
        print("  2. You've run seed.py to populate test data")
        return
    
    # Run all queries
    query_1_session_trace()
    query_2_error_analysis()
    query_3_tool_call_chains()
    query_4_latency_analysis()
    query_5_semantic_error_search()
    query_6_cross_session_analysis()
    
    # Summary
    print_section("SUMMARY: Why Graph-backed Observability?")
    print("""
  Traditional logging gives you flat timelines. RushDB gives you structure:
  
  1. RELATIONSHIPS instead of manual ID correlation
     - "Find all errors in this session" is a single graph query
     - No need to parse JSON logs and match request IDs
  
  2. TRAVERSAL instead of filtering
     - "Trace this error back to its root cause" walks the graph
     - Error → Tool → Message → Session in one connected chain
  
  3. LABELS enable semantic queries
     - All tool calls share the same properties across records
     - Find "all RateLimitError instances" across your entire history
  
  4. VECTOR SEARCH for similarity
     - Find similar error messages semantically
     - Identify patterns across seemingly unrelated failures
  
  QUICK COMMANDS:
    - Run 'python seed.py' to regenerate test data
    - Check RushDB dashboard to visualize the graph
    - See docs.rushdb.com for API reference
    """)
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
