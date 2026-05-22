#!/usr/bin/env python3
"""
Graph-Enhanced Code Review Assistant - Tutorial Main Script

Demonstrates RushDB property graph capabilities for code review workflows:
- Finding PRs by author with relationship traversal
- Tracking reviewer patterns and co-reviewer relationships
- Identifying slow-to-review PRs
- Building reviewer expertise profiles
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify API key is available
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    exit(1)

from rushdb import RushDB

# Initialize client
db = RushDB(api_key)


def query_1_find_prs_by_author(username):
    """
    Query 1: Find all PRs authored by a specific developer.
    
    Demonstrates:
    - Using `where` with label-based filtering
    - Accessing related record properties
    """
    print(f"\n--- Query 1: Find PRs by author ---")
    print(f"Looking for PRs by: {username}\n")
    
    # Find the author first
    authors = db.records.find({
        "labels": ["AUTHOR"],
        "where": {"username": username}
    })
    
    if not authors.data:
        print(f"  No author found with username: {username}")
        return
    
    author = authors.data[0]
    
    # Find all PRs authored by this author
    # The AUTHOR label in the where clause filters by related AUTHOR record
    prs = db.records.find({
        "labels": ["PULL_REQUEST"],
        "where": {
            "AUTHOR": {
                "$relation": {"type": "AUTHORED_BY", "direction": "in"},
                "username": username
            }
        },
        "orderBy": {"number": "desc"}
    })
    
    print(f"Found {len(prs.data)} PRs by {username}:")
    for pr in prs.data:
        print(f"  PR #{pr['number']}: \"{pr['title']}\" ({pr['status']})")


def query_2_top_reviewers():
    """
    Query 2: Find developers with the most approvals.
    
    Demonstrates:
    - Aggregating relationship counts
    - Transaction handling for complex queries
    """
    print(f"\n--- Query 2: Find reviewers with most approvals ---")
    
    # Find all approved reviews
    reviews = db.records.find({
        "labels": ["REVIEW"],
        "where": {"status": "APPROVED"}
    })
    
    # Count approvals per reviewer
    approval_counts = defaultdict(int)
    
    for review in reviews.data:
        # Find the reviewer who authored this review
        reviewer_records = db.records.find({
            "labels": ["REVIEW"],
            "where": {
                "AUTHOR": {"$relation": {"type": "REVIEWED_BY", "direction": "out"}}
            }
        })
        
        # Alternative approach: Find AUTHOR records connected to REVIEW records
        # Using the correct relationship direction
        connected_authors = db.records.find({
            "labels": ["AUTHOR"],
            "where": {
                "REVIEW": {"$relation": {"type": "REVIEWED_BY", "direction": "in"}}
            }
        })
        
    # More efficient: find all authors, then check their review connections
    all_authors = db.records.find({"labels": ["AUTHOR"]})
    
    reviewer_data = []
    for author in all_authors.data:
        # Count APPROVED reviews where this author is the reviewer
        reviews_by_author = db.records.find({
            "labels": ["REVIEW"],
            "where": {
                "status": "APPROVED",
                "AUTHOR": {
                    "$relation": {"type": "REVIEWED_BY", "direction": "in"},
                    "username": author["username"]
                }
            }
        })
        
        if reviews_by_author.data:
            reviewer_data.append({
                "username": author["username"],
                "name": author["name"],
                "approval_count": len(reviews_by_author.data)
            })
    
    # Sort by approval count descending
    reviewer_data.sort(key=lambda x: x["approval_count"], reverse=True)
    
    print(f"Top reviewers:")
    for reviewer in reviewer_data[:5]:
        print(f"  - {reviewer['username']}: {reviewer['approval_count']} approvals")


def query_3_prs_needing_review(repo_name):
    """
    Query 3: Find PRs in a repository that need review.
    
    Demonstrates:
    - Multi-hop relationship traversal (REPO -> PR -> REVIEW)
    - Filtering by status
    """
    print(f"\n--- Query 3: Find PRs in repository with pending reviews ---")
    print(f"Repository: {repo_name}\n")
    
    # Find the repository
    repos = db.records.find({
        "labels": ["REPOSITORY"],
        "where": {"name": repo_name}
    })
    
    if not repos.data:
        print(f"  No repository found: {repo_name}")
        return
    
    repo = repos.data[0]
    
    # Find OPEN PRs in this repository
    open_prs = db.records.find({
        "labels": ["PULL_REQUEST"],
        "where": {
            "status": "OPEN",
            "REPOSITORY": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"},
                "name": repo_name
            }
        },
        "orderBy": {"number": "desc"}
    })
    
    print(f"PRs needing review in {repo_name}:")
    for pr in open_prs.data:
        # Find reviewers who have been requested
        reviewers = db.records.find({
            "labels": ["REVIEWER"],
            "where": {
                "PULL_REQUEST": {
                    "$relation": {"type": "REQUESTED_REVIEW_FROM", "direction": "in"},
                    "number": pr["number"]
                }
            }
        })
        
        reviewer_names = [r["username"] for r in reviewers.data] if reviewers.data else ["(none requested)"]
        print(f"  PR #{pr['number']}: \"{pr['title']}\" ({pr['status']})")
        print(f"    Reviewers: {reviewer_names}")


def query_4_slow_prs(threshold_days=3):
    """
    Query 4: Find PRs that have been open longer than threshold without approval.
    
    Demonstrates:
    - Date-based filtering
    - Status checking across relationships
    """
    print(f"\n--- Query 4: Find slow-to-review PRs ---")
    print(f"Threshold: {threshold_days}+ days open without approval\n")
    
    now = datetime.now()
    threshold_date = now - timedelta(days=threshold_days)
    
    # Find all OPEN PRs
    open_prs = db.records.find({
        "labels": ["PULL_REQUEST"],
        "where": {"status": "OPEN"}
    })
    
    slow_prs = []
    
    for pr in open_prs.data:
        created_at = datetime.fromisoformat(pr["createdAt"])
        days_open = (now - created_at).days
        
        if days_open >= threshold_days:
            # Check if there's an approved review
            reviews = db.records.find({
                "labels": ["REVIEW"],
                "where": {
                    "PULL_REQUEST": {
                        "$relation": {"type": "HAS_REVIEW", "direction": "in"},
                        "number": pr["number"]
                    },
                    "status": "APPROVED"
                }
            })
            
            if not reviews.data:
                slow_prs.append({
                    "pr": pr,
                    "days_open": days_open
                })
    
    # Sort by days open descending
    slow_prs.sort(key=lambda x: x["days_open"], reverse=True)
    
    print(f"PRs open > {threshold_days} days without approval:")
    for item in slow_prs:
        pr = item["pr"]
        print(f"  PR #{pr['number']}: {item['days_open']} days - \"{pr['title']}\"")


def query_5_co_reviewers():
    """
    Query 5: Find pairs of developers who frequently review together.
    
    Demonstrates:
    - Building co-occurrence matrices
    - Cross-record correlation
    """
    print(f"\n--- Query 5: Find co-reviewer patterns ---")
    
    # Get all authors
    authors = db.records.find({"labels": ["AUTHOR"]})
    
    # Map username to ID
    author_map = {author["username"]: author.id for author in authors.data}
    
    # For each PR, find all reviewers
    prs = db.records.find({"labels": ["PULL_REQUEST"]})
    
    co_review_count = defaultdict(int)
    
    for pr in prs.data:
        # Find all reviews for this PR
        reviews = db.records.find({
            "labels": ["REVIEW"],
            "where": {
                "PULL_REQUEST": {
                    "$relation": {"type": "HAS_REVIEW", "direction": "in"},
                    "number": pr["number"]
                }
            }
        })
        
        if len(reviews.data) >= 2:
            # Find reviewers for this PR
            pr_reviewers = []
            for review in reviews.data:
                # Find the reviewer (AUTHOR connected via REVIEWED_BY)
                reviewer_connections = db.records.find({
                    "labels": ["AUTHOR"],
                    "where": {
                        "REVIEW": {
                            "$relation": {"type": "REVIEWED_BY", "direction": "in"}
                        }
                    }
                })
                for r in reviewer_connections.data:
                    if r["username"] not in pr_reviewers:
                        pr_reviewers.append(r["username"])
            
            # Count co-reviewer pairs
            for i, reviewer1 in enumerate(pr_reviewers):
                for reviewer2 in pr_reviewers[i + 1:]:
                    pair = tuple(sorted([reviewer1, reviewer2]))
                    co_review_count[pair] += 1
    
    # Sort by co-review count
    top_pairs = sorted(co_review_count.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print(f"Developers who frequently review together:")
    for pair, count in top_pairs:
        if count > 0:
            print(f"  {pair[0]} and {pair[1]} reviewed {count} PRs together")


def query_6_author_expertise():
    """
    Query 6: Build expertise profiles by analyzing file changes.
    
    Demonstrates:
    - Traversal through multiple relationships
    - Aggregating properties across related records
    """
    print(f"\n--- Query 6: Find author expertise by file patterns ---")
    
    # Get all authors
    authors = db.records.find({"labels": ["AUTHOR"]})
    
    for author in authors.data:
        username = author["username"]
        
        # Find files in PRs authored by this developer
        files = db.records.find({
            "labels": ["FILE"],
            "where": {
                "PULL_REQUEST": {
                    "$relation": {"type": "CHANGES", "direction": "in"},
                    "AUTHOR": {
                        "$relation": {"type": "AUTHORED_BY", "direction": "in"},
                        "username": username
                    }
                }
            }
        })
        
        if files.data:
            # Aggregate expertise tags
            expertise_counts = defaultdict(int)
            for file in files.data:
                if "expertise" in file:
                    expertise_counts[file["expertise"]] += 1
            
            # Sort by frequency and show top expertise areas
            sorted_expertise = sorted(expertise_counts.items(), key=lambda x: x[1], reverse=True)
            top_expertise = [exp for exp, count in sorted_expertise[:3]]
            
            print(f"  {username} specializes in: {top_expertise}")
        else:
            print(f"  {username}: no file changes found")



def demo_upsert_pattern():
    """
    Demo: Using upsert for idempotent data management.
    
    Demonstrates:
    - mergeBy option for upsert
    - Handling both create and update cases
    """
    print(f"\n--- Demo: Upsert Pattern ---")
    
    # This creates a new record
    pr1 = db.records.upsert(
        label="PULL_REQUEST",
        data={
            "number": 999,
            "title": "Demo PR",
            "status": "DRAFT",
            "repo": "demo-repo"
        },
        options={"mergeBy": ["number", "repo"]}
    )
    print(f"Created PR: #{pr1.data['number']} - {pr1.data['title']}")
    
    # This updates the existing record
    pr2 = db.records.upsert(
        label="PULL_REQUEST",
        data={
            "number": 999,
            "title": "Demo PR - Updated",
            "status": "OPEN",
            "repo": "demo-repo"
        },
        options={"mergeBy": ["number", "repo"]}
    )
    print(f"Updated PR: #{pr2.data['number']} - {pr2.data['title']} (status: {pr2.data['status']})")
    
    # Clean up demo record
    db.records.delete(record_id=pr1.id)
    print("Cleaned up demo PR")


def demo_transaction_pattern():
    """
    Demo: Transaction patterns for atomic operations.
    
    Demonstrates:
    - Context manager for transactions
    - Atomic creation of related records
    """
    print(f"\n--- Demo: Transaction Pattern ---")
    
    # Create a new review with transaction
    print("Creating a review atomically with relationships...")
    
    with db.transactions.begin() as tx:
        # Create review record
        review = db.records.create(
            label="REVIEW",
            data={
                "status": "COMMENTED",
                "summary": "Transactional demo review"
            },
            transaction=tx
        )
        
        # Find a PR to attach to
        prs = db.records.find({
            "labels": ["PULL_REQUEST"],
            "where": {"status": "OPEN"},
            "limit": 1
        })
        
        if prs.data:
            pr = prs.data[0]
            db.records.attach(
                source=pr,
                target=review,
                options={"type": "HAS_REVIEW"},
                transaction=tx
            )
            print(f"  Attached review to PR #{pr['number']}")
        
        # Find an author to attach as reviewer
        authors = db.records.find({"labels": ["AUTHOR"], "limit": 1})
        if authors.data:
            author = authors.data[0]
            db.records.attach(
                source=review,
                target=author,
                options={"type": "REVIEWED_BY"},
                transaction=tx
            )
            print(f"  Attached reviewer: {author['username']}")
        
        # Transaction commits automatically on clean exit
        print("  Transaction committed!")
    
    # Clean up the demo review
    db.records.delete(record_id=review.id)
    print("Cleaned up demo review")


def main():
    """"Main tutorial execution."""
    print("\n" + "=" * 55)
    print("=== Graph-Enhanced Code Review Assistant ===")
    print("=" * 55)
    
    # Core graph queries
    query_1_find_prs_by_author("alice")
    query_2_top_reviewers()
    query_3_prs_needing_review("api-service")
    query_4_slow_prs(threshold_days=3)
    query_5_co_reviewers()
    query_6_author_expertise()
    
    # Pattern demonstrations
    demo_upsert_pattern()
    demo_transaction_pattern()
    
    print("\n" + "=" * 55)
    print("=== Tutorial Complete ===")
    print("=" * 55)
    print("\nNext steps:")
    print("  - Try modifying the queries for your own use case")
    print("  - Add vector embeddings for code similarity search")
    print("  - Build a reviewer recommendation engine")
    print()


if __name__ == "__main__":
    main()
