"""
main.py - Change Impact Analysis with Semantic Dependency Graph

This script demonstrates the canonical use case for RushDB in AI-augmented code review:

SCENARIO: A PR modifies the shared utility function `format_currency()`.
The agent needs to determine all affected services, tests, and downstream consumers.

DEMONSTRATES:
1. The naive approach (pure vector search) misses structural dependencies
2. RushDB's hybrid query (graph traversal + semantic similarity) finds the full impact chain
3. How to construct the actual RushDB query that connects graph traversal with vector-filtered results
"""

import os
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and fill in your API key")
    exit(1)

db = RushDB(API_KEY)


def print_header(text):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print("=" * 60)


def print_subsection(text):
    """Print a subsection header."""
    print(f"\n--- {text} ---")


def naive_vector_search_approach():
    """
    THE NAIVE APPROACH: Pure vector search.

    Agent interprets the diff, identifies keywords, makes N vector search calls.
    Problem: Misses structural dependencies entirely.
    """
    print_header("NAIVE APPROACH: Pure Vector Search")

    print("""
    Agent sees: diff modifies `format_currency()` in `src/utils/formatters.py`

    Strategy: Search for functions with similar descriptions to "currency formatting"
    """)

    # First search: look for functions mentioning "currency"
    print_subsection("Search 1: Functions mentioning 'currency'")
    results = db.ai.search({
        "propertyName": "description",
        "query": "currency formatting monetary amounts",
        "labels": ["FUNCTION"],
        "limit": 10,
    })

    found_names = []
    for result in results.data:
        print(f"  • {result['name']} (score: {result.score:.3f})")
        found_names.append(result['name'])

    # Second search: look for functions mentioning "format"
    print_subsection("Search 2: Functions mentioning 'format'")
    results2 = db.ai.search({
        "propertyName": "description",
        "query": "format string text output",
        "labels": ["FUNCTION"],
        "limit": 10,
    })

    for result in results2.data:
        if result['name'] not in found_names:
            print(f"  • {result['name']} (score: {result.score:.3f})")

    print("""
    PROBLEM: This approach has critical blind spots:

    ✗ generate_receipt() uses format_currency() but description says "receipt text"
      → Vector search doesn't know about the CALLS relationship

    ✗ orders_endpoint -> generate_receipt -> format_currency chain is invisible
      → Can't trace transitive dependencies through the call graph

    ✗ Tests covering format_currency won't appear in semantic search
      → test_format_currency tests "currency formatting" code but its description
        is just "unit tests for currency formatting function"
    """)


def rushdb_hybrid_query_approach():
    """
    THE RUSHDb APPROACH: Hybrid graph + vector search.

    1. Graph traversal: Find all records that CALL or DEPEND_ON format_currency
    2. Semantic extension: Find structurally similar functions above a threshold
    3. Transitive closure: Walk the dependency graph to find downstream consumers
    """
    print_header("RUSHDb APPROACH: Hybrid Graph + Vector Query")

    # Step 1: Find the target function
    print_subsection("Step 1: Locate the modified function")
    target = db.records.find({
        "labels": ["FUNCTION"],
        "where": {"name": "format_currency", "type": "utility"},
    })

    if not target.data:
        print("  ERROR: format_currency not found. Run `python seed.py` first.")
        return

    target_record = target.data[0]
    print(f"  Found: {target_record['name']}")
    print(f"    File: {target_record['file_path']}")
    print(f"    Signature: {target_record['signature']}")

    # Step 2: Find direct callers (CALLS relationships where target is the target)
    print_subsection("Step 2: Find direct callers via graph traversal")

    # Find all functions that CALL format_currency
    direct_callers = db.records.find({
        "labels": ["FUNCTION"],
        "where": {
            "FUNCTION": {  # Label of the related record
                "$relation": {"type": "CALLS", "direction": "out"},
                "name": "format_currency",
            }
        },
    })

    print(f"  Found {len(direct_callers.data)} direct callers:")
    for caller in direct_callers.data:
        print(f"    → {caller['name']} ({caller['file_path']})")

    # Step 3: Find services that transitively depend on format_currency
    print_subsection("Step 3: Trace transitive dependencies (downstream services)")

    # Find services that CALL functions which CALL format_currency
    downstream_services = db.records.find({
        "labels": ["SERVICE"],
        "where": {
            "FUNCTION": {
                "$relation": {"type": "CALLS", "direction": "out"},
                "FUNCTION": {
                    "$relation": {"type": "CALLS", "direction": "out"},
                    "name": "format_currency",
                }
            }
        },
    })

    print(f"  Found {len(downstream_services.data)} downstream services:")
    for svc in downstream_services.data:
        print(f"    → {svc['name']} ({svc['signature']})")

    # Step 4: Find tests that cover format_currency
    print_subsection("Step 4: Find tests covering the modified function")

    tests_covering = db.records.find({
        "labels": ["TEST"],
        "where": {
            "FUNCTION": {
                "$relation": {"type": "TESTS", "direction": "out"},
                "name": "format_currency",
            }
        },
    })

    print(f"  Found {len(tests_covering.data)} covering tests:")
    for test in tests_covering.data:
        print(f"    → {test['name']} ({test['file_path']})")

    # Step 5: Hybrid query - find similar functions above threshold
    print_subsection("Step 5: Semantic similarity query (hybrid filter)")

    # Search for functions similar to format_currency's description
    # but also ensure they have some structural relationship potential
    similar_functions = db.ai.search({
        "propertyName": "description",
        "query": "format currency monetary string output display",
        "labels": ["FUNCTION"],
        "where": {
            "name": {"$ne": "format_currency"},  # Exclude the target itself
        },
        "limit": 5,
    })

    print("  Functions with high semantic similarity (potential impact):")
    for func in similar_functions.data:
        if func.score >= 0.6:  # Threshold for "structurally relevant"
            print(f"    → {func['name']} (similarity: {func.score:.3f})")
            print(f"      Description: {func['description'][:80]}...")

    # Step 6: Combine - show full impact chain
    print_subsection("Step 6: Full impact chain analysis")

    print("\n  IMPACT SUMMARY for format_currency modification:")
    print("  " + "-" * 50)

    all_affected = []

    # Add direct callers
    for caller in direct_callers.data:
        all_affected.append({"type": "Direct Caller", "name": caller['name'], "file": caller['file_path']})

    # Add downstream services
    for svc in downstream_services.data:
        all_affected.append({"type": "Downstream Service", "name": svc['name'], "file": svc['file_path']})

    # Add covering tests
    for test in tests_covering.data:
        all_affected.append({"type": "Test Coverage", "name": test['name'], "file": test['file_path']})

    # Group by file for cleaner output
    by_file = {}
    for item in all_affected:
        if item["file"] not in by_file:
            by_file[item["file"]] = []
        by_file[item["file"]].append(item)

    for filepath, items in by_file.items():
        print(f"\n  📁 {filepath}")
        for item in items:
            print(f"     • [{item['type']}] {item['name']}")

    print(f"\n  TOTAL: {len(all_affected)} entities need review/regression testing")


def show_actual_query_patterns():
    """
    Show the actual RushDB query patterns used in the hybrid approach.
    """
    print_header("ACTUAL RUSHDb QUERY PATTERNS")

    print("""
    Below are the exact query patterns used in the hybrid approach:
    """)

    print_subsection("Pattern 1: Direct relationship traversal")
    print("""
    Find all FUNCTIONs that CALL format_currency:

    ```sdk
    db.records.find({
        "labels": ["FUNCTION"],
        "where": {
            "FUNCTION": {
                "$relation": {"type": "CALLS", "direction": "out"},
                "name": "format_currency",
            }
        },
    })
    ```
    """)

    print_subsection("Pattern 2: Transitive traversal (2 hops)")
    print("""
    Find SERVICEs that call FUNCTIONs which call format_currency:

    ```sdk
    db.records.find({
        "labels": ["SERVICE"],
        "where": {
            "FUNCTION": {
                "$relation": {"type": "CALLS", "direction": "out"},
                "FUNCTION": {
                    "$relation": {"type": "CALLS", "direction": "out"},
                    "name": "format_currency",
                }
            }
        },
    })
    ```
    """)

    print_subsection("Pattern 3: Tests covering a function")
    print("""
    Find TESTs that TEST a FUNCTION:

    ```sdk
    db.records.find({
        "labels": ["TEST"],
        "where": {
            "FUNCTION": {
                "$relation": {"type": "TESTS", "direction": "out"},
                "name": "format_currency",
            }
        },
    })
    ```
    """)

    print_subsection("Pattern 4: Hybrid search with semantic filtering")
    print("""
    Find FUNCTIONs with high semantic similarity to a query,
    filtered to exclude the target:

    ```sdk
    db.ai.search({
        "propertyName": "description",
        "query": "format currency monetary string",
        "labels": ["FUNCTION"],
        "where": {
            "name": {"$ne": "format_currency"},
        },
        "limit": 5,
    })
    ```
    """)


def demonstrate_schema():
    """
    Show the RushDB schema for this code dependency graph.
    """
    print_header("RUSHDb SCHEMA: Code Dependency Graph")

    print("""
    LABELS (node types):
    ┌─────────────┬─────────────────────────────────────────────────────┐
    │ LABEL       │ Description                                         │
    ├─────────────┼─────────────────────────────────────────────────────┤
    │ FUNCTION    │ Any callable code unit (utility, business logic)   │
    │ SERVICE     │ API endpoints, HTTP handlers, controllers           │
    │ TEST        │ Test files and test functions                       │
    └─────────────┴─────────────────────────────────────────────────────┘

    RELATIONSHIPS (edge types):
    ┌─────────────┬─────────────────────────────────────────────────────┐
    │ TYPE        │ Description                                         │
    ├─────────────┼─────────────────────────────────────────────────────┤
    │ CALLS       │ Direct function invocation (A calls B)             │
    │ TESTS       │ Test coverage relationship (test covers function)  │
    │ DEPENDS_ON  │ Import or include relationship                      │
    └─────────────┴─────────────────────────────────────────────────────┘

    EXAMPLE GRAPH (for format_currency modification):

         ┌─────────────────┐
         │ checkout_endpoint│ ──CALLS──► ┌─────────────────┐
         └─────────────────┘            │ process_payment  │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
         ┌─────────────────┐            │ send_invoice     │
         │ shipping_quote   │ ──CALLS──► │                 │
         └─────────────────┘            └────────┬────────┘
                                               │
         ┌─────────────────┐                   │ CALLS
         │ orders_endpoint │ ──CALLS──► ┌──────┴────────┐
         └─────────────────┘            │ generate_receipt│
                                        └───────┬────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │     CALLS             │
                                    ▼                       ▼
                            ┌──────────────────┐    ┌─────────────────┐
                            │ format_currency  │◄───│ (MODIFIED)      │
                            │ (UTILITY)        │    │                 │
                            └────────┬─────────┘    └─────────────────┘
                                     │
                        ┌─────────────┼─────────────┐
                        │             │             │
                        ▼             ▼             ▼
                 ┌────────────┐ ┌────────────┐ ┌────────────┐
                 │ calculate  │ │ send       │ │ calculate  │
                 │ _shipping  │ │ _invoice   │ │ _order...  │
                 └────────────┘ └────────────┘ └────────────┘
                        │
                        ▼
                 ┌────────────┐
                 │ test       │
                 │ _shipping  │ ──TESTS──► format_currency
                 └────────────┘
    """)


def main():
    print("\n" + "=" * 60)
    print("  CHANGE IMPACT ANALYSIS WITH RUSHDb")
    print("  Semantic Dependency Graph for Code Interpretation")
    print("=" * 60)

    # Check if data exists
    existing = db.records.find({"labels": ["FUNCTION"], "limit": 1})
    if not existing.data:
        print("\n❌ No data found. Run `python seed.py` first to generate test data.")
        return

    # Run demonstrations
    demonstrate_schema()
    naive_vector_search_approach()
    rushdb_hybrid_query_approach()
    show_actual_query_patterns()

    print("\n" + "=" * 60)
    print("  COMPLETE - Run seed.py to reset data, then main.py again")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
