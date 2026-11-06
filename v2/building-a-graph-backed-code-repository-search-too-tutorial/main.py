"""
Building a Graph-Backed Code Repository Search Tool

This example demonstrates how to use RushDB's property graph model
to build a powerful code search engine for repositories.

The graph model:
- REPOSITORY: Top-level container for a code project
- FILE: Source files within a repository
- FUNCTION: Functions defined in files
- CLASS: Classes defined in files

Relationships:
- REPOSITORY --CONTAINS--> FILE
- FILE --DEFINES--> FUNCTION
- FILE --DEFINES--> CLASS
- CLASS --METHOD--> FUNCTION
- FILE --IMPORTS--> FILE (cross-file dependencies)
- FUNCTION --CALLS--> FUNCTION (function dependencies)
- REPOSITORY --IMPORTS--> REPOSITORY (cross-repo dependencies)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB


def get_client():
    """Initialize RushDB client from environment."""
    api_key = os.getenv("RUSHDB_API_KEY")
    url = os.getenv("RUSHDB_URL")
    
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found. "
            "Get one at https://app.rushdb.com/settings/api-keys"
        )
    
    return RushDB(api_key, url=url) if url else RushDB(api_key)


def demo_basic_queries(db):
    """Demonstrate basic label-based queries."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Label-Based Queries")
    print("=" * 60)
    
    # Find all repositories
    repos = db.records.find({"labels": ["REPOSITORY"], "limit": 10})
    print(f"\n[Repositories] Found {len(repos.data)} repositories:")
    for repo in repos.data:
        print(f"  - {repo['name']} ({repo['stars']} stars)")
    
    # Find all Python files
    files = db.records.find({
        "labels": ["FILE"],
        "where": {"extension": ".py"},
        "limit": 10
    })
    print(f"\n[Python Files] Found {len(files.data)} .py files:")
    for f in files.data:
        print(f"  - {f['path']}")
    
    # Find test files specifically
    test_files = db.records.find({
        "labels": ["FILE"],
        "where": {"type": "test"},
        "limit": 5
    })
    print(f"\n[Test Files] Found {len(test_files.data)} test files:")
    for f in test_files.data:
        print(f"  - {f['path']}")


def demo_relationship_traversal(db):
    """Demonstrate relationship traversal to find related entities."""
    print("\n" + "=" * 60)
    print("DEMO 2: Relationship Traversal")
    print("=" * 60)
    
    # Get a sample file
    files = db.records.find({"labels": ["FILE"], "where": {"type": "module"}, "limit": 1})
    
    if not files.data:
        print("No files found. Run `python seed.py` first.")
        return
    
    sample_file = files.data[0]
    print(f"\n[Sample File] {sample_file['path']}")
    
    # Find files that import this file
    imported_by = db.records.find({
        "labels": ["FILE"],
        "where": {
            "FILE": {
                "$relation": {"type": "IMPORTS", "direction": "in"},
                "$id": {"$in": [sample_file.id]}
            }
        }
    })
    print(f"\n[Imported By] {len(imported_by.data)} files import this file:")
    for f in imported_by.data[:5]:
        print(f"  - {f['path']}")
    
    # Find files this file imports
    imports = db.records.find({
        "labels": ["FILE"],
        "where": {
            "FILE": {
                "$relation": {"type": "IMPORTS", "direction": "out"},
                "$id": {"$in": [sample_file.id]}
            }
        }
    })
    print(f"\n[Imports] This file imports {len(imports.data)} files:")
    for f in imports.data[:5]:
        print(f"  - {f['path']}")
    
    # Find functions defined in this file
    functions = db.records.find({
        "labels": ["FUNCTION"],
        "where": {
            "FILE": {
                "$relation": {"type": "DEFINES", "direction": "in"},
                "$id": {"$in": [sample_file.id]}
            },
            "is_method": {"$ne": True}  # Exclude class methods
        }
    })
    print(f"\n[Functions] Found {len(functions.data)} functions:")
    for func in functions.data[:5]:
        print(f"  - {func['name']}({', '.join(func.get('params', []))})")


def demo_nested_traversal(db):
    """Demonstrate multi-hop graph traversal."""
    print("\n" + "=" * 60)
    print("DEMO 3: Multi-Hop Graph Traversal")
    print("=" * 60)
    
    # Find repositories that contain files with functions
    # This traverses: REPOSITORY -> FILE -> FUNCTION
    repos_with_functions = db.records.find({
        "labels": ["REPOSITORY"],
        "where": {
            "FILE": {
                "FUNCTION": {"lines": {"$gte": 20}}
            }
        }
    })
    print(f"\n[Repositories] With functions > 20 lines: {len(repos_with_functions.data)}")
    for repo in repos_with_functions.data:
        print(f"  - {repo['name']}")
    
    # Find all classes and their methods via multi-hop traversal
    classes = db.records.find({
        "labels": ["CLASS"],
        "limit": 5
    })
    print(f"\n[Classes] Found {len(classes.data)} classes:")
    
    for cls in classes.data[:3]:
        print(f"\n  Class: {cls['name']}")
        print(f"  Doc: {cls.get('doc', 'No docstring')[:60]}...")
        
        # Find methods of this class
        methods = db.records.find({
            "labels": ["FUNCTION"],
            "where": {
                "CLASS": {
                    "$relation": {"type": "METHOD", "direction": "in"},
                    "$id": {"$in": [cls.id]}
                }
            }
        })
        print(f"  Methods ({len(methods.data)}):")
        for method in methods.data[:4]:
            print(f"    - {method['name']}()")


def demo_cross_repo_dependencies(db):
    """Find dependencies between repositories."""
    print("\n" + "=" * 60)
    print("DEMO 4: Cross-Repository Dependencies")
    print("=" * 60)
    
    # Find all cross-repo dependencies
    # REPOSITORY --IMPORTS--> REPOSITORY
    dependencies = db.records.find({
        "labels": ["REPOSITORY"],
        "where": {
            "REPOSITORY": {
                "$relation": {"type": "IMPORTS", "direction": "out"}
            }
        }
    })
    
    print(f"\n[Dependencies] {len(dependencies.data)} repositories have dependencies:")
    for repo in dependencies.data:
        # Find what they depend on
        deps = db.records.find({
            "labels": ["REPOSITORY"],
            "where": {
                "REPOSITORY": {
                    "$relation": {"type": "IMPORTS", "direction": "out"},
                    "$id": {"$in": [repo.id]}
                }
            }
        })
        dep_names = [d['name'] for d in deps.data]
        print(f"  - {repo['name']} imports: {', '.join(dep_names)}")


def demo_search_by_pattern(db):
    """Search files and functions by name patterns."""
    print("\n" + "=" * 60)
    print("DEMO 5: Search by Pattern")
    print("=" * 60)
    
    # Find files with 'auth' in the path
    auth_files = db.records.find({
        "labels": ["FILE"],
        "where": {
            "path": {"$contains": "auth"}
        }
    })
    print(f"\n[Auth Files] Found {len(auth_files.data)} files with 'auth' in path:")
    for f in auth_files.data:
        print(f"  - {f['path']}")
    
    # Find functions related to authentication
    auth_funcs = db.records.find({
        "labels": ["FUNCTION"],
        "where": {
            "$or": [
                {"name": {"$contains": "auth"}},
                {"name": {"$contains": "token"}},
                {"name": {"$contains": "password"}}
            ]
        },
        "limit": 10
    })
    print(f"\n[Auth Functions] Found {len(auth_funcs.data)} auth-related functions:")
    for func in auth_funcs.data:
        print(f"  - {func['name']}({', '.join(func.get('params', []))})")
        if func.get('doc'):
            print(f"    {func['doc'][:70]}...")


def demo_call_graph(db):
    """Analyze function call relationships."""
    print("\n" + "=" * 60)
    print("DEMO 6: Function Call Graph Analysis")
    print("=" * 60)
    
    # Find functions that call other functions
    callers = db.records.find({
        "labels": ["FUNCTION"],
        "where": {
            "FUNCTION": {
                "$relation": {"type": "CALLS", "direction": "out"}
            }
        },
        "limit": 10
    })
    
    print(f"\n[Callers] {len(callers.data)} functions have outgoing calls:")
    for caller in callers.data[:5]:
        # Find what this function calls
        callees = db.records.find({
            "labels": ["FUNCTION"],
            "where": {
                "FUNCTION": {
                    "$relation": {"type": "CALLS", "direction": "out"},
                    "$id": {"$in": [caller.id]}
                }
            }
        })
        callee_names = [c['name'] for c in callees.data]
        print(f"  - {caller['name']} calls: {', '.join(callee_names[:3])}")
    
    # Find the most-called functions (high in-degree)
    all_funcs = db.records.find({"labels": ["FUNCTION"], "limit": 50})
    
    callee_counts = {}
    for func in all_funcs.data:
        callers_of = db.records.find({
            "labels": ["FUNCTION"],
            "where": {
                "FUNCTION": {
                    "$relation": {"type": "CALLS", "direction": "out"},
                    "$id": {"$in": [func.id]}
                }
            }
        })
        if callers_of.data:
            callee_counts[func['name']] = len(callers_of.data)
    
    if callee_counts:
        top_called = sorted(callee_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n[Most Called Functions]")
        for name, count in top_called:
            print(f"  - {name}: called by {count} functions")


def demo_semantic_search(db):
    """Demonstrate semantic search on function documentation."""
    print("\n" + "=" * 60)
    print("DEMO 7: Semantic Code Search (Concept-Level)")
    print("=" * 60)
    
    # Check if we have an index for function documentation
    indexes = db.ai.indexes.find()
    
    # Look for an index on FUNCTION.doc
    doc_index = None
    for idx in indexes.data:
        if idx.get('label') == 'FUNCTION' and idx.get('propertyName') == 'doc':
            doc_index = idx
            break
    
    if not doc_index:
        print("\n[Note] No vector index on FUNCTION.doc found.")
        print("      Semantic search requires creating an index first.")
        print("      This would be done with:")
        print("        db.ai.indexes.create({")
        print("            'label': 'FUNCTION',")
        print("            'propertyName': 'doc'")
        print("        })")
        print("\n      Here's a preview of function docs for context:")
        
        funcs = db.records.find({"labels": ["FUNCTION"], "limit": 5})
        for func in funcs.data:
            doc = func.get('doc', 'No docstring')
            print(f"  - {func['name']}: {doc[:60]}...")
        return
    
    # Perform semantic search
    print("\n[Semantic Search] Query: 'authentication and token validation'")
    results = db.ai.search({
        "propertyName": "doc",
        "query": "authentication and token validation",
        "labels": ["FUNCTION"],
        "limit": 5
    })
    
    print(f"\n[Results] Found {len(results.data)} semantically similar functions:")
    for result in results.data:
        print(f"  [{result.score:.3f}] {result['name']}")
        print(f"          {result.get('doc', '')[:60]}...")


def demo_complex_graph_query(db):
    """Demonstrate complex queries combining multiple hops."""
    print("\n" + "=" * 60)
    print("DEMO 8: Complex Graph Query")
    print("=" * 60)
    
    # Find: Repositories containing files that have functions
    # which are called by other functions
    # This requires multi-hop traversal through the graph
    
    # First, find functions that have callers
    called_funcs = db.records.find({
        "labels": ["FUNCTION"],
        "where": {
            "FUNCTION": {
                "$relation": {"type": "CALLS", "direction": "in"}
            }
        },
        "limit": 20
    })
    
    print(f"\n[Popular Functions] {len(called_funcs.data)} functions are called by others:")
    
    for func in called_funcs.data[:5]:
        # Find the file containing this function
        containing_files = db.records.find({
            "labels": ["FILE"],
            "where": {
                "FUNCTION": {
                    "$relation": {"type": "DEFINES", "direction": "in"},
                    "$id": {"$in": [func.id]}
                }
            }
        })
        
        if containing_files.data:
            file_path = containing_files.data[0]['path']
            # Find the repository containing this file
            repos = db.records.find({
                "labels": ["REPOSITORY"],
                "where": {
                    "FILE": {
                        "$relation": {"type": "CONTAINS", "direction": "in"},
                        "$id": {"$in": [containing_files.data[0].id]}
                    }
                }
            })
            
            repo_name = repos.data[0]['name'] if repos.data else 'unknown'
            print(f"  - {func['name']} in {file_path} ({repo_name})")


def demo_transactional_import(db):
    """Demonstrate transactional import of complex nested data."""
    print("\n" + "=" * 60)
    print("DEMO 9: Transactional Data Import")
    print("=" * 60)
    
    # Demonstrate creating a complete file with its functions in one transaction
    with db.transactions.begin() as tx:
        # Create a new repository for testing
        test_repo = db.records.create(
            label="REPOSITORY",
            data={
                "name": "test-repo",
                "description": "Repository created in transaction demo",
                "language": "python",
                "stars": 0,
            },
            transaction=tx
        )
        
        # Create a file in this repository
        test_file = db.records.create(
            label="FILE",
            data={
                "path": "test_repo/demo.py",
                "name": "demo.py",
                "extension": ".py",
                "type": "module"
            },
            transaction=tx
        )
        
        # Link file to repository
        db.records.attach(
            source=test_repo,
            target=test_file,
            options={"type": "CONTAINS"},
            transaction=tx
        )
        
        # Create functions in the file
        for i in range(3):
            func = db.records.create(
                label="FUNCTION",
                data={
                    "name": f"transactional_function_{i}",
                    "doc": f"Function {i} created in a transaction",
                    "params": ["arg1", "arg2"],
                    "lines": 15 + i * 5,
                },
                transaction=tx
            )
            
            db.records.attach(
                source=test_file,
                target=func,
                options={"type": "DEFINES"},
                transaction=tx
            )
    
    print("\n[Transaction] Successfully created in single transaction:")
    print("  - 1 repository: 'test-repo'")
    print("  - 1 file: 'test_repo/demo.py'")
    print("  - 3 functions: 'transactional_function_0/1/2'")
    print("  - All relationships created atomically")
    
    # Verify the data was created
    test_repo_check = db.records.find({
        "labels": ["REPOSITORY"],
        "where": {"name": "test-repo"}
    })
    print(f"\n[Verification] Found {len(test_repo_check.data)} test-repo")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("RUSHDB GRAPH-BACKED CODE REPOSITORY SEARCH TOOL")
    print("=" * 60)
    print("\nThis tool demonstrates RushDB's property graph model")
    print("for building powerful code search and analysis tools.")
    
    try:
        db = get_client()
        print("\n[OK] Connected to RushDB")
    except Exception as e:
        print(f"\n[ERROR] Failed to connect: {e}")
        return
    
    # Run all demos
    demo_basic_queries(db)
    demo_relationship_traversal(db)
    demo_nested_traversal(db)
    demo_cross_repo_dependencies(db)
    demo_search_by_pattern(db)
    demo_call_graph(db)
    demo_semantic_search(db)
    demo_complex_graph_query(db)
    demo_transactional_import(db)
    
    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Explore more queries using db.records.find()")
    print("  2. Create vector indexes for semantic search")
    print("  3. Build your own search UI on top of this graph")
    print("\nLearn more: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
