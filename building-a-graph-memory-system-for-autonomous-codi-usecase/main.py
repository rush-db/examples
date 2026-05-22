#!/usr/bin/env python3
"""
Graph Memory System for Autonomous Coding Agents - Main Demo

This script demonstrates how a graph-memory system solves the context-window
overflow problem for autonomous coding agents.

Key concepts shown:
1. Why context windows fail for long-horizon tasks
2. How a graph structure lets the agent traverse 'what was I working on'
3. A bug-hunting agent that remembers what was already investigated
4. Why graph edges beat flat vector retrieval for code understanding
5. RushDB queries for dependency chain traversal
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# RushDB SDK
from rushdb import RushDB


def load_env():
    """Load environment variables."""
    load_dotenv()
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found in environment.\n"
            "Get your free API key at: https://app.rushdb.com\n"
            "Then add it to .env or export RUSHDB_API_KEY=your_key"
        )
    return api_key


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print a formatted subsection header."""
    print(f"\n📌 {title}")
    print("-" * 50)


def demonstrate_context_window_failure():
    """
    DEMO 1: Why Context Windows Fail
    
    Shows how a naive agent wastes tokens repeatedly re-explaining context.
    """
    print_header("DEMO 1: The Context Window Failure Problem")
    
    print("""
Imagine an autonomous agent working on a complex bug that spans 50 files.
Each time the agent resumes work (new session, new API call), it must:

1. Re-explain the bug context: "We're fixing BUG-1001 where auth fails..."
2. Re-describe the codebase structure: "The auth folder contains..."
3. Re-list files already checked: "We already ruled out middleware.ts..."

This is what happens WITHOUT a persistent memory:
""")
    
    # Simulate token waste
    tokens_per_session = [
        ("Session 1", 2000),
        ("Session 2", 2400),  # +400 for re-explaining previous context
        ("Session 3", 2800),  # +400 more
        ("Session 4", 3200),  # +400 more
        ("Session 5", 3600),  # +400 more (context window pressure!)
    ]
    
    print("\n   Naive Agent - Token Usage per Session:")
    print("   " + "-" * 45)
    total_wasted = 0
    for session, tokens in tokens_per_session:
        wasted = tokens - tokens_per_session[0][1]
        total_wasted += wasted
        bar = "█" * min(wasted // 100, 30)
        print(f"   {session}: {tokens:,} tokens [{bar}] +{wasted:,} wasted")
    
    print(f"""
   Total wasted across 5 sessions: {total_wasted:,} tokens
   
   💡 By session 5, the agent is spending {total_wasted / (tokens_per_session[0][1] * 5) * 100:.0f}% 
   of its context just re-explaining what it already "knew"!


With a GRAPH MEMORY system, the agent can:
   - Query "what files were already checked?" → instant answer
   - Traverse dependency chains → understand relationships
   - Remember "why this file was ruled out" → avoid repeating mistakes
""")


def demonstrate_graph_memory_queries(db: RushDB):
    """
    DEMO 2: Graph Memory Queries
    
    Shows how to query the graph for investigation state.
    """
    print_header("DEMO 2: Querying the Graph Memory")
    
    # Query 1: Find a bug by ID
    print_subheader("Query 2.1: Find a Specific Bug")
    print("Query: Find BUG-1001 and see its details")
    
```sdk
bugs = db.records.find({
    "labels": ["BUG"],
    "where": {"id": "BUG-1001"}
})
bug = bugs.data[0]
print(f"Bug: {bug['title']}")
print(f"Severity: {bug['severity']}")
```
    
    bugs = db.records.find({
        "labels": ["BUG"],
        "where": {"id": "BUG-1001"}
    })
    
    if bugs.data:
        bug = bugs.data[0]
        print(f"\n✅ Result:")
        print(f"   Bug: {bug['title']}")
        print(f"   Severity: {bug['severity']}")
        print(f"   Description: {bug['description'][:80]}...")
    else:
        print("\n⚠️  No bug found. Run 'python seed.py' first to populate the database.")
        return
    
    # Query 2: Find the root cause file
    print_subheader("Query 2.2: Find the Root Cause File")
    print("Query: What file contains the root cause of BUG-1001?")
    
```sdk
# Use RushDB's relationship query to find the root cause file
root_cause_files = db.records.find({
    "labels": ["FILE"],
    "where": {
        "BUG": {
            "$relation": {"type": "ROOT_CAUSE_IN", "direction": "in"},
            "id": "BUG-1001"
        }
    }
})
```
    
    root_cause_files = db.records.find({
        "labels": ["FILE"],
        "where": {
            "BUG": {
                "$relation": {"type": "ROOT_CAUSE_IN", "direction": "in"},
                "id": "BUG-1001"
            }
        }
    })
    
    if root_cause_files.data:
        root_file = root_cause_files.data[0]
        print(f"\n✅ Result:")
        print(f"   Root cause file: {root_file['path']}")
        print(f"   Type: {root_file['type']}")
        print(f"   Directory: {root_file['dir']}")
        
        # Also find the function
        root_functions = db.records.find({
            "labels": ["FUNCTION"],
            "where": {
                "FILE": {
                    "$relation": {"type": "DEFINED_IN", "direction": "in"}},
                "file": root_file['path']
            }
        })
        if root_functions.data:
            func = root_functions.data[0]
            print(f"   Root cause function: {func['name']}")
            print(f"   Summary: {func['summary']}")
    else:
        print("\n⚠️  No root cause file found.")



def demonstrate_investigation_trail(db: RushDB):
    """
    DEMO 3: Investigation Trail (Ruled-Out Files)
    
    Shows how the agent remembers what was already checked.
    """
    print_header("DEMO 3: Investigation Trail - What Was Already Checked")
    
    print("Query: What files were already investigated for BUG-1001, and why?")
    
```sdk
# Find the investigation for BUG-1001
investigations = db.records.find({
    "labels": ["INVESTIGATION"],
    "where": {"bug_id": "BUG-1001"}
})

# Find files investigated during this investigation
investigated_files = db.records.find({
    "labels": ["FILE"],
    "where": {
        "INVESTIGATION": {
            "$relation": {"type": "INVESTIGATED", "direction": "in"},
            "bug_id": "BUG-1001"
        }
    }
})
```
    
    investigations = db.records.find({
        "labels": ["INVESTIGATION"],
        "where": {"bug_id": "BUG-1001"}
    })
    
    if not investigations.data:
        print("\n⚠️  No investigation found. Run 'python seed.py' first.")
        return
    
    investigation = investigations.data[0]
    
    # Find files that were investigated
    investigated_files = db.records.find({
        "labels": ["FILE"],
        "where": {
            "INVESTIGATION": {
                "$relation": {"type": "INVESTIGATED", "direction": "in"},
                "bug_id": "BUG-1001"
            }
        }
    })
    
    # Find the findings
    findings = db.records.find({
        "labels": ["INVESTIGATION_FINDING"],
        "where": {"investigation_id": investigation.id}
    })
    
    print(f"\n✅ Investigation Trail for BUG-1001:")
    print(f"   Status: {investigation['status']}")
    print(f"\n   Files investigated ({len(investigated_files.data)} total):")
    
    for finding in findings.data:
        status_emoji = "❌" if finding["result"] == "ruled_out" else "🎯"
        status_text = "RULED OUT" if finding["result"] == "ruled_out" else "ROOT CAUSE"
        print(f"\n   {status_emoji} {finding['file']}")
        print(f"      Status: {status_text}")
        print(f"      Reason: {finding['reason']}")
        if "function" in finding:
            print(f"      Function: {finding['function']} (line {finding['line']})")
            print(f"      Issue: {finding['issue_description'][:100]}...")
    
    print(f"""
   💡 With graph memory, the agent can instantly answer:
       "What files did we already check for BUG-1001?"
       "Why was /auth/middleware/authMiddleware.ts ruled out?"
   
   No need to re-read all those files or re-explain the context!
""")


def demonstrate_dependency_chain(db: RushDB):
    """
    DEMO 4: Dependency Chain Traversal
    
    Shows how to traverse the dependency graph to understand code relationships.
    """
    print_header("DEMO 4: Dependency Chain Traversal")
    
    print("Query: Show the dependency chain from the root cause file")
    
    # Find the root cause file for BUG-1001
    root_cause_files = db.records.find({
        "labels": ["FILE"],
        "where": {
            "BUG": {
                "$relation": {"type": "ROOT_CAUSE_IN", "direction": "in"},
                "id": "BUG-1001"
            }
        }
    })
    
    if not root_cause_files.data:
        print("\n⚠️  No root cause file found. Run 'python seed.py' first.")
        return
    
    root_file = root_cause_files.data[0]
    
    print(f"\n   Root cause: {root_file['path']}")
    print(f"\n   Dependency chain:")
    print(f"   " + "-" * 50)
    print(f"\n   📁 {root_file['path']}")
    
    # Find functions defined in this file
    functions = db.records.find({
        "labels": ["FUNCTION"],
        "where": {
            "FILE": {
                "$relation": {"type": "DEFINED_IN", "direction": "in"}},
            "file": root_file['path']
        }
    })
    
    if functions.data:
        for func in functions.data:
            print(f"      └── 📄 {func['name']}()")
            
            # Find what this function calls
            called_funcs = db.records.find({
                "labels": ["FUNCTION"],
                "where": {
                    "FUNCTION": {
                        "$relation": {"type": "CALLS", "direction": "in"}},
                    "name": func['name']
                }
            })
            
            if called_funcs.data:
                for called in called_funcs.data:
                    print(f"          └── 📄 {called['name']}()")
    
    # Find what OTHER files depend on this root cause file
    print(f"\n   📦 Files that depend on {root_file['path']}:")
    
    dependent_files = db.records.find({
        "labels": ["FILE"],
        "where": {
            "FUNCTION": {
                "$relation": {"type": "DEFINED_IN", "direction": "in"}},
        }
    })
    
    # This is a simplified query - in a real system we'd track dependencies
    all_funcs = db.records.find({"labels": ["FUNCTION"], "limit": 100})
    
    if all_funcs.data:
        calling_files = set()
        for func in all_funcs.data:
            if func.get("file") != root_file['path']:
                # Check if any function in other file calls functions in root file
                called = db.records.find({
                    "labels": ["FUNCTION"],
                    "where": {
                        "FUNCTION": {
                            "$relation": {"type": "CALLS", "direction": "in"}},
                        "name": func['name']
                    }
                })
                if called.data:
                    for c in called.data:
                        if c.get("file") == root_file['path']:
                            calling_files.add(func['file'])
        
        for file_path in sorted(calling_files)[:5]:
            print(f"      └── 📁 {file_path}")
    
    print(f"""
   💡 This query would be impossible with flat vector retrieval:
       Vector search: "Find files similar to authentication token validation"
       Graph query: "Find all files that call validateToken(), which lives in the root cause file"
   
   Graph traversal gives you EXACT dependency relationships, not just semantic similarity.
""")


def demonstrate_graph_vs_vector():
    """
    DEMO 5: Graph vs. Vector Search Comparison
    
    Shows why graph edges are more useful than flat vector retrieval for code.
    """
    print_header("DEMO 5: Why Graph Edges Beat Flat Vector Retrieval")
    
    print("""
Consider this scenario:
   Bug: "Authentication fails for expired tokens"
   Root cause file: /auth/jwt/tokenValidator.ts
   Root cause function: validateToken()

Let's compare how different approaches answer key questions:
""")
    
    print_subheader("Question 1: What was already checked for this bug?")
    print("""
   ❌ Vector Search:
      "Find documents similar to 'authentication middleware checked'
      Problem: Can't remember WHAT WAS CHECKED - only what's semantically similar
      
   ✅ Graph Memory:
      "Find all FILE records linked via INVESTIGATED edge to BUG-1001"
      Result: [authMiddleware.ts, jwtService.ts, sessionManager.ts, ..., tokenValidator.ts]
      Plus: Each record has the REASON it was ruled out!
""")
    
    print_subheader("Question 2: What depends on the root cause file?")
    print("""
   ❌ Vector Search:
      "Find documents similar to 'token validation depends on'
      Problem: Semantic similarity ≠ actual dependency relationship
      
   ✅ Graph Memory:
      "Traverse CALLS edges from all FUNCTIONs to find those pointing to tokenValidator.ts"
      Result: [authenticateRequest(), chargePayment()] - TRUE dependencies
""")
    
    print_subheader("Question 3: Why was this file ruled out?")
    print("""
   ❌ Vector Search:
      "Find documents similar to 'middleware ruled out'
      Problem: You get similar documents, not the actual reason
      
   ✅ Graph Memory:
      "Look up INVESTIGATION_FINDING record with ruled_out reason"
      Result: "Middleware correctly passes tokens to validator - issue not here"
""")
    
    print_subheader("Question 4: Show the dependency chain for this bug")
    print("""
   ❌ Vector Search:
      "Find documents similar to 'dependency chain authentication'
      Problem: Returns unrelated documents, not actual call graph
      
   ✅ Graph Memory:
      "Traverse: BUG → ROOT_CAUSE_IN → FILE → DEFINED_IN → FUNCTION → CALLS → ..."
      Result: validateToken() → verifySignature() → decodeHeader()
""")
    
    print(f"""
   ╔══════════════════════════════════════════════════════════════════════╗
   ║                       SUMMARY                                         ║
   ╠══════════════════════════════════════════════════════════════════════╣
   ║  Vector Search is great for:          Graph Memory is great for:      ║
   ║  - Finding similar code snippets      - Remembering investigation    ║
   ║  - Semantic code search               - Traversing dependencies       ║
   ║  - Natural language queries           - Answering "why ruled out?"    ║
   ║                                       - Following call chains       ║
   ║                                                                       ║
   ║  They COMPLIMENT each other: Use BOTH in your agent!                  ║
   ╚══════════════════════════════════════════════════════════════════════╝
""")


def demonstrate_autonomous_agent_scenario(db: RushDB):
    """
    DEMO 6: Autonomous Agent Scenario
    
    Simulates how an agent uses the graph memory system.
    """
    print_header("DEMO 6: Autonomous Bug-Hunting Agent with Memory")
    
    print("""
SCENARIO:
An agent starts working on BUG-1002 ("Order processing fails when payment 
timeout occurs"). It uses the graph memory to efficiently investigate.

""")
    
    print_subheader("Step 1: Check if this bug was worked on before")
    print("""
Agent Query: "Find any investigation records for BUG-1002"
""")
    
    past_work = db.records.find({
        "labels": ["INVESTIGATION"],
        "where": {"bug_id": "BUG-1002"}
    })
    
    if past_work.data:
        print(f"✅ Found existing investigation: {past_work.data[0]['bug_id']}")
        print(f"   Status: {past_work.data[0]['status']}")
        
        # Show what was already done
        investigated = db.records.find({
            "labels": ["FILE"],
            "where": {
                "INVESTIGATION": {
                    "$relation": {"type": "INVESTIGATED", "direction": "in"},
                    "bug_id": "BUG-1002"
                }
            }
        })
        print(f"   Files already investigated: {len(investigated.data)}")
    else:
        print("📋 Starting fresh investigation (no prior work found)")
    
    print_subheader("Step 2: Quick dependency chain analysis")
    print("""
Agent Query: "Show the dependency chain from the order processing to payment"
""")
    
    # Find the relevant files
    order_service = db.records.find({
        "labels": ["FUNCTION"],
        "where": {"name": "processOrder"}
    })
    
    if order_service.data:
        func = order_service.data[0]
        print(f"✅ Found: {func['name']}() in {func['file']}")
        
        # Find what it calls
        called = db.records.find({
            "labels": ["FUNCTION"],
            "where": {
                "FUNCTION": {
                    "$relation": {"type": "CALLS", "direction": "in"}},
                "name": "processOrder"
            }
        })
        
        print(f"   Calls: {[f['name'] for f in called.data]}")
    
    print_subheader("Step 3: Check historical patterns")
    print("""
Agent Query: "Have we seen similar bugs before?"
""")
    
    similar_bugs = db.records.find({
        "labels": ["HISTORICAL_INVESTIGATION"],
        "where": {
            "title": {"$contains": "payment"}
        }
    })
    
    if similar_bugs.data:
        print(f"✅ Found {len(similar_bugs.data)} similar historical bugs:")
        for bug in similar_bugs.data:
            print(f"   - {bug['bug_id']}: {bug['root_cause_file']}")
            print(f"     (Fixed in {bug['time_to_fix']}, investigated {bug['files_investigated']} files)")
    else:
        print("📋 No similar historical bugs found")
    
    print(f"""
   ╔══════════════════════════════════════════════════════════════════════╗
   ║  THE AGENT SAVED ~3,000 TOKELS BY QUERYING THE GRAPH MEMORY!         ║
   ║                                                                       ║
   ║  Instead of re-reading files and re-explaining context, it:           ║
   ║  1. Queried what was already done → instant answer                   ║
   ║  2. Traversed dependencies → understood relationships                ║
   ║  3. Learned from history → knew where to look first                  ║
   ╚══════════════════════════════════════════════════════════════════════╝
""")


def main():
    """Main demo function."""
    print("\n" + "🌳" * 35)
    print("   GRAPH MEMORY SYSTEM FOR AUTONOMOUS CODING AGENTS")
    print("   Solving Context Window Overflow with RushDB")
    print("   " + "🌳" * 35)
    
    # Load RushDB connection
    api_key = load_env()
    db = RushDB(api_key)
    
    # Run all demonstrations
    demonstrate_context_window_failure()
    demonstrate_graph_memory_queries(db)
    demonstrate_investigation_trail(db)
    demonstrate_dependency_chain(db)
    demonstrate_graph_vs_vector()
    demonstrate_autonomous_agent_scenario(db)
    
    # Final summary
    print("\n" + "=" * 70)
    print("  WRAP-UP: Key Takeaways")
    print("=" * 70)
    print("""
1. ✅ Context windows fail at scale for long-horizon tasks
      - Agents waste tokens re-explaining context each session

2. ✅ Graph memory enables persistent, queryable knowledge
      - "What was already checked?" → instant answer
      - "Why was this file ruled out?" → stored in the graph

3. ✅ Graph edges beat flat vector retrieval for code understanding
      - "CALLS" relationship ≠ semantic similarity
      - "INVESTIGATED" relationship → remember investigation history

4. ✅ RushDB's labels and relationships model code entities naturally
      - Labels: FILE, FUNCTION, BUG, INVESTIGATION
      - Edges: ROOT_CAUSE_IN, INVESTIGATED, CALLS, DEFINED_IN

5. ✅ The agent can learn from past investigations
      - Historical patterns help prioritize where to look


┌──────────────────────────────────────────────────────────────────────┐
│  Want to build this? Start with:                                    │
│                                                                      │
│  1. Model your code entities as RushDB records with labels           │
│  2. Create relationships between entities (ATTACH)                    │
│  3. Record agent actions as INVESTIGATION records                    │
│  4. Query the graph instead of re-reading files                       │
│                                                                      │
│  Docs: https://docs.rushdb.com                                       │
│  GitHub: https://github.com/rush-db/examples                         │
└──────────────────────────────────────────────────────────────────────┘

Thank you for exploring the graph memory system demo!
""")



if __name__ == "__main__":
    main()
