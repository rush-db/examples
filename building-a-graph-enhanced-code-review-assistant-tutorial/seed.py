#!/usr/bin/env python3
"""
Seed script for the Code Review Assistant tutorial.
Creates sample repositories, developers, PRs, reviews, and comments.

This script is idempotent — run it multiple times safely.
"""

import os
import sys
from datetime import datetime, timedelta
from random import randint, choice, sample
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Verify API key is available
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

from rushdb import RushDB

# Initialize client
db = RushDB(api_key)


def clear_existing_data():
    """Remove all existing tutorial data."""
    print("Clearing existing tutorial data...")
    labels_to_clear = ["COMMENT", "FILE", "REVIEW", "PULL_REQUEST", "REVIEWER", "AUTHOR", "REPOSITORY"]
    for label in labels_to_clear:
        try:
            result = db.records.delete_many({"labels": [label], "where": {}})
        except Exception as e:
            print(f"  Warning clearing {label}: {e}")
    print("  Done.")


def create_repositories():
    """Create sample repositories."""
    print("Creating repositories...")
    
    repos_data = [
        {
            "name": "api-service",
            "language": "TypeScript",
            "description": "Core API service with REST endpoints",
            "stars": 234
        },
        {
            "name": "web-frontend",
            "language": "React",
            "description": "Customer-facing web application",
            "stars": 456
        },
        {
            "name": "data-pipeline",
            "language": "Python",
            "description": "ETL and data processing pipeline",
            "stars": 89
        }
    ]
    
    repos = []
    for repo_data in repos_data:
        repo = db.records.upsert(
            label="REPOSITORY",
            data=repo_data,
            options={"mergeBy": ["name"]}
        )
        repos.append(repo)
        print(f"  Created: {repo_data['name']}")
    
    return repos


def create_authors():
    """Create sample developers/authors."""
    print("Creating authors...")
    
    authors_data = [
        {
            "username": "alice",
            "name": "Alice Chen",
            "email": "alice@company.com",
            "expertise": ["backend", "cache", "auth"],
            "joinDate": "2022-01-15"
        },
        {
            "username": "bob",
            "name": "Bob Martinez",
            "email": "bob@company.com",
            "expertise": ["api", "middleware", "performance"],
            "joinDate": "2021-06-20"
        },
        {
            "username": "charlie",
            "name": "Charlie Kim",
            "email": "charlie@company.com",
            "expertise": ["frontend", "react", "css"],
            "joinDate": "2022-03-10"
        },
        {
            "username": "diana",
            "name": "Diana Patel",
            "email": "diana@company.com",
            "expertise": ["data", "python", "sql"],
            "joinDate": "2021-09-05"
        },
        {
            "username": "evan",
            "name": "Evan Wilson",
            "email": "evan@company.com",
            "expertise": ["devops", "infrastructure", "k8s"],
            "joinDate": "2022-07-01"
        },
        {
            "username": "fiona",
            "name": "Fiona Garcia",
            "email": "fiona@company.com",
            "expertise": ["testing", "qa", "automation"],
            "joinDate": "2023-01-20"
        }
    ]
    
    authors = []
    for author_data in authors_data:
        author = db.records.upsert(
            label="AUTHOR",
            data=author_data,
            options={"mergeBy": ["username"]}
        )
        authors.append(author)
        print(f"  Created: {author_data['username']}")
    
    return authors


def create_pull_requests(repos, authors):
    """Create sample pull requests."""
    print("Creating pull requests...")
    
    # Calculate dates relative to now
    now = datetime.now()
    
    prs_data = [
        # Repo 0: api-service
        {"repo_idx": 0, "number": 35, "title": "Update README", "status": "MERGED", "days_ago": 30},
        {"repo_idx": 0, "number": 38, "title": "Fix auth bug", "status": "MERGED", "days_ago": 21},
        {"repo_idx": 0, "number": 42, "title": "Add caching layer", "status": "OPEN", "days_ago": 5},
        {"repo_idx": 0, "number": 43, "title": "Refactor endpoints", "status": "OPEN", "days_ago": 3},
        {"repo_idx": 0, "number": 45, "title": "Add rate limiting", "status": "OPEN", "days_ago": 5},
        # Repo 1: web-frontend
        {"repo_idx": 1, "number": 112, "title": "Update dependency versions", "status": "MERGED", "days_ago": 14},
        {"repo_idx": 1, "number": 115, "title": "Fix responsive layout", "status": "MERGED", "days_ago": 7},
        {"repo_idx": 1, "number": 118, "title": "Add dark mode", "status": "OPEN", "days_ago": 2},
        # Repo 2: data-pipeline
        {"repo_idx": 2, "number": 23, "title": "Optimize batch processing", "status": "MERGED", "days_ago": 45},
        {"repo_idx": 2, "number": 28, "title": "Add error handling", "status": "MERGED", "days_ago": 28},
        {"repo_idx": 2, "number": 31, "title": "Update dependencies", "status": "OPEN", "days_ago": 4},
        {"repo_idx": 2, "number": 33, "title": "Add monitoring metrics", "status": "OPEN", "days_ago": 1}
    ]
    
    prs = []
    for idx, pr_info in enumerate(prs_data):
        created_at = (now - timedelta(days=pr_info["days_ago"])).isoformat()
        pr_data = {
            "number": pr_info["number"],
            "title": pr_info["title"],
            "status": pr_info["status"],
            "createdAt": created_at,
            "repo": repos[pr_info["repo_idx"]].data["name"]
        }
        
        pr = db.records.upsert(
            label="PULL_REQUEST",
            data=pr_data,
            options={"mergeBy": ["number", "repo"]}
        )
        
        # Attach to repository
        db.records.attach(
            source=pr,
            target=repos[pr_info["repo_idx"]],
            options={"type": "BELONGS_TO"}
        )
        
        # Attach author (cycle through authors)
        author = authors[idx % len(authors)]
        db.records.attach(
            source=pr,
            target=author,
            options={"type": "AUTHORED_BY"}
        )
        
        prs.append(pr)
        print(f"  Created: PR #{pr_info['number']} - {pr_info['title']}")
    
    return prs


def create_reviews(prs, authors):
    """Create sample review records."""
    print("Creating reviews...")
    
    # Define review patterns: (pr_idx, reviewer_idx, status, days_ago)
    review_patterns = [
        # PR #35 (idx 0)
        (0, 2, "APPROVED", 28),   # charlie
        (0, 3, "APPROVED", 27),   # diana
        # PR #38 (idx 1)
        (1, 1, "APPROVED", 19),   # bob
        (1, 2, "APPROVED", 18),   # charlie
        # PR #42 (idx 2)
        (2, 2, "APPROVED", 3),    # charlie
        # PR #43 (idx 3)
        (3, 1, "CHANGES_REQUESTED", 2),  # bob
        (3, 2, "COMMENTED", 2),   # charlie
        # PR #45 (idx 4) - No reviews yet!
        # PR #112 (idx 5)
        (5, 2, "APPROVED", 12),   # charlie
        (5, 0, "APPROVED", 11),   # alice
        # PR #115 (idx 6)
        (6, 0, "APPROVED", 5),    # alice
        (6, 2, "APPROVED", 4),    # charlie
        (6, 3, "APPROVED", 4),    # diana
        # PR #118 (idx 7)
        (7, 1, "COMMENTED", 1),   # bob
        # PR #23 (idx 8)
        (8, 3, "APPROVED", 40),   # diana
        (8, 4, "APPROVED", 38),   # evan
        # PR #28 (idx 9)
        (9, 3, "APPROVED", 25),   # diana
        (9, 0, "APPROVED", 24),   # alice
        # PR #31 (idx 10)
        (10, 3, "CHANGES_REQUESTED", 3),  # diana
        # PR #33 (idx 11) - No reviews yet!
    ]
    
    for pr_idx, reviewer_idx, status, days_ago in review_patterns:
        now = datetime.now()
        reviewed_at = (now - timedelta(days=days_ago)).isoformat()
        
        review_data = {
            "status": status,
            "reviewedAt": reviewed_at,
            "summary": f"Reviewed by {authors[reviewer_idx].data['username']}"
        }
        
        review = db.records.create(
            label="REVIEW",
            data=review_data
        )
        
        # Attach review to PR
        db.records.attach(
            source=prs[pr_idx],
            target=review,
            options={"type": "HAS_REVIEW"}
        )
        
        # Attach reviewer to review
        db.records.attach(
            source=review,
            target=authors[reviewer_idx],
            options={"type": "REVIEWED_BY"}
        )
        
        print(f"  Created: Review for PR #{prs[pr_idx].data['number']} by {authors[reviewer_idx].data['username']} ({status})")


def create_comments(prs, authors):
    """Create sample comments."""
    print("Creating comments...")
    
    comment_templates = [
        {"content": "Looks good to me!", "type": "approval"},
        {"content": "Can we add more tests for this edge case?", "type": "request"},
        {"content": "Consider using a constant instead of magic number", "type": "suggestion"},
        {"content": "This might cause a memory leak", "type": "concern"},
        {"content": "Nit: rename variable to be more descriptive", "type": "nit"},
        {"content": "The API contract looks good", "type": "approval"},
        {"content": "We should handle the null case", "type": "suggestion"},
        {"content": "This approach is cleaner", "type": "approval"},
        {"content": "Maybe extract this to a utility function?", "type": "suggestion"},
        {"content": "LGTM!", "type": "approval"},
    ]
    
    now = datetime.now()
    comment_count = 0
    
    for pr_idx, pr in enumerate(prs):
        # Add 2-4 comments per PR
        num_comments = randint(2, 4)
        
        for i in range(num_comments):
            template = choice(comment_templates)
            comment_data = {
                "content": template["content"],
                "type": template["type"],
                "createdAt": (now - timedelta(days=randint(0, pr.data["days_ago"] if "days_ago" in pr.data else 30))).isoformat()
            }
            
            comment = db.records.create(
                label="COMMENT",
                data=comment_data
            )
            
            # Attach comment to PR
            db.records.attach(
                source=pr,
                target=comment,
                options={"type": "HAS_COMMENT"}
            )
            
            # Random author for comment
            comment_author = choice(authors)
            db.records.attach(
                source=comment,
                target=comment_author,
                options={"type": "AUTHORED_BY"}
            )
            
            comment_count += 1
    
    print(f"  Created {comment_count} comments")


def create_files(prs, authors):
    """Create sample file changes."""
    print("Creating file changes...")
    
    file_patterns = [
        # api-service files
        {"path": "src/cache/redis.ts", "type": "modified", "expertise": "cache"},
        {"path": "src/auth/jwt.ts", "type": "modified", "expertise": "auth"},
        {"path": "src/api/endpoints.ts", "type": "modified", "expertise": "api"},
        {"path": "src/middleware/rate-limit.ts", "type": "added", "expertise": "middleware"},
        # web-frontend files
        {"path": "components/DarkMode.tsx", "type": "added", "expertise": "frontend"},
        {"path": "styles/responsive.css", "type": "modified", "expertise": "css"},
        {"path": "hooks/useTheme.ts", "type": "added", "expertise": "react"},
        # data-pipeline files
        {"path": "processors/batch.py", "type": "modified", "expertise": "python"},
        {"path": "utils/error-handler.ts", "type": "added", "expertise": "backend"},
        {"path": "monitors/metrics.py", "type": "added", "expertise": "data"},
    ]
    
    file_count = 0
    
    for pr_idx, pr in enumerate(prs):
        # Add 1-3 files per PR
        num_files = randint(1, 3)
        selected_files = sample(file_patterns, min(num_files, len(file_patterns)))
        
        for file_info in selected_files:
            file_data = {
                "path": file_info["path"],
                "type": file_info["type"],
                "additions": randint(5, 100),
                "deletions": randint(1, 50),
                "expertise": file_info["expertise"]
            }
            
            file_record = db.records.create(
                label="FILE",
                data=file_data
            )
            
            # Attach file to PR
            db.records.attach(
                source=pr,
                target=file_record,
                options={"type": "CHANGES"}
            )
            
            file_count += 1
    
    print(f"  Created {file_count} file changes")



def main():
    """Main seed function."""
    print("\n" + "=" * 50)
    print("Code Review Assistant - Seed Script")
    print("=" * 50 + "\n")
    
    # Clear existing data for clean slate
    clear_existing_data()
    print()
    
    # Create entities
    repos = create_repositories()
    print()
    
    authors = create_authors()
    print()
    
    prs = create_pull_requests(repos, authors)
    print()
    
    create_reviews(prs, authors)
    print()
    
    create_comments(prs, authors)
    print()
    
    create_files(prs, authors)
    print()
    
    print("=" * 50)
    print("Seeding complete!")
    print("=" * 50)
    print("\nRun `python main.py` to explore the graph queries.")
    print()


if __name__ == "__main__":
    main()
