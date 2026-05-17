"""
Seed script for the "5 RAG Developer Pain Points" demo.

Creates a customer support scenario in RushDB with:
- 3 users with support history
- 6 tickets across 3 software releases
- 3 issues with fixes
- Semantic embeddings on descriptions

Run: python seed.py
"""

import os
import time
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")

if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(api_key, url=url) if url else RushDB(api_key)

# Embedding model for vector storage
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text):
    """Generate embedding vector for text."""
    return model.encode(text).tolist()

def wait_for_index(index_id, timeout=30):
    """Poll until index is ready."""
    start = time.time()
    while time.time() - start < timeout:
        stats = db.ai.indexes.stats(index_id)
        if stats.data.get("status") == "ready":
            return
        time.sleep(1)
    raise TimeoutError(f"Index {index_id} did not become ready in {timeout}s")

def seed():
    print("\n" + "=" * 60)
    print("SEEDING RUSHDb - Customer Support Memory Scenario")
    print("=" * 60)

    # Clean up existing data
    print("\n[1/6] Cleaning existing records...")
    for label in ["USER", "TICKET", "ISSUE", "RELEASE", "FIX", "API"]:
        db.records.delete({"labels": [label], "where": {}})
    print("  ✓ Cleared existing data")

    # Create vector indexes
    print("\n[2/6] Creating vector indexes...")
    ticket_index = db.ai.indexes.create({
        "label": "TICKET",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384
    })
    issue_index = db.ai.indexes.create({
        "label": "ISSUE",
        "propertyName": "summary",
        "sourceType": "external",
        "dimensions": 384
    })
    print(f"  ✓ Ticket index: {ticket_index.data.get('__id')}")
    print(f"  ✓ Issue index: {issue_index.data.get('__id')}")

    # Create users
    print("\n[3/6] Creating users...")
    users = []
    users_data = [
        {
            "email": "alice@example.com",
            "name": "Alice Johnson",
            "tier": "premium",
            "joinedAt": "2023-01-15"
        },
        {
            "email": "bob@techcorp.io",
            "name": "Bob Chen",
            "tier": "enterprise",
            "joinedAt": "2022-11-20"
        },
        {
            "email": "carol@startup.co",
            "name": "Carol Martinez",
            "tier": "standard",
            "joinedAt": "2023-06-01"
        }
    ]
    for u in users_data:
        record = db.records.create(label="USER", data=u)
        users.append(record)
        print(f"  ✓ User: {u['email']}")
    alice, bob, carol = users

    # Create releases
    print("\n[4/6] Creating releases...")
    releases_data = [
        {"version": "v2.2", "releasedAt": "2024-02-15", "codename": "Falcon"},
        {"version": "v2.3", "releasedAt": "2024-04-20", "codename": "Eagle"},
        {"version": "v2.4", "releasedAt": "2024-06-10", "codename": "Hawk"}
    ]
    releases = []
    for r in releases_data:
        record = db.records.create(label="RELEASE", data=r)
        releases.append(record)
        print(f"  ✓ Release: {r['version']}")
    v22, v23, v24 = releases

    # Create APIs (for entity disambiguation)
    print("\n[5/6] Creating API components...")
    apis_data = [
        {"name": "BillingAPI_v1", "context": "v2.2", "purpose": "payment processing"},
        {"name": "BillingAPI_v2", "context": "v2.3", "purpose": "invoice handling"},
        {"name": "AuthAPI_v1", "context": "v2.2", "purpose": "jwt token generation"},
        {"name": "AuthAPI_v2", "context": "v2.4", "purpose": "oauth2 integration"}
    ]
    apis = []
    for a in apis_data:
        record = db.records.create(label="API", data=a)
        apis.append(record)
        print(f"  ✓ API: {a['name']}")

    # Create issues and fixes
    print("\n[6/6] Creating issues, fixes, and tickets...")
    
    # Issue 1: Billing issue in v2.2, fixed in v2.3
    billing_issue = db.records.create(label="ISSUE", data={
        "summary": "Billing API timeout on large transactions",
        "severity": "high",
        "component": "BillingAPI",
        "reportedIn": "v2.2"
    })
    billing_fix = db.records.create(label="FIX", data={
        "description": "Increased timeout to 30s and added retry logic",
        "releasedIn": "v2.3",
        "patch": "billing-fix-001"
    })
    db.records.attach(source=billing_issue, target=billing_fix, options={"type": "RESOLVED_BY"})
    db.records.attach(source=billing_fix, target=v23, options={"type": "RELEASED_IN"})
    db.records.attach(source=billing_issue, target=apis[0], options={"type": "AFFECTS"})
    print(f"  ✓ Issue: {billing_issue['summary'][:40]}...")

    # Issue 2: Auth issue in v2.3, fixed in v2.4
    auth_issue = db.records.create(label="ISSUE", data={
        "summary": "Auth token refresh failing silently",
        "severity": "critical",
        "component": "AuthAPI",
        "reportedIn": "v2.3"
    })
    auth_fix = db.records.create(label="FIX", data={
        "description": "Fixed token refresh endpoint and added error logging",
        "releasedIn": "v2.4",
        "patch": "auth-fix-002"
    })
    db.records.attach(source=auth_issue, target=auth_fix, options={"type": "RESOLVED_BY"})
    db.records.attach(source=auth_fix, target=v24, options={"type": "RELEASED_IN"})
    db.records.attach(source=auth_issue, target=apis[2], options={"type": "AFFECTS"})
    print(f"  ✓ Issue: {auth_issue['summary'][:40]}...")

    # Issue 3: Search issue in v2.4
    search_issue = db.records.create(label="ISSUE", data={
        "summary": "Search index stale after bulk operations",
        "severity": "medium",
        "component": "SearchAPI",
        "reportedIn": "v2.4"
    })
    print(f"  ✓ Issue: {search_issue['summary'][:40]}...")

    # Create tickets and attach to graph
    tickets_data = [
        # Alice's tickets
        {
            "ticketId": "T001",
            "description": "Payment processing timeout when handling orders over $1000",
            "status": "resolved",
            "priority": "high"
        },
        {
            "ticketId": "T002",
            "description": "Invoice generation producing incorrect amounts for subscription renewals",
            "status": "resolved",
            "priority": "high"
        },
        # Bob's tickets
        {
            "ticketId": "T003",
            "description": "Auth tokens expiring earlier than configured TTL causing sudden logout",
            "status": "resolved",
            "priority": "critical"
        },
        {
            "ticketId": "T004",
            "description": "Batch payment processing silently failing on weekends",
            "status": "open",
            "priority": "high"
        },
        # Carol's ticket
        {
            "ticketId": "T005",
            "description": "Search results not updating after new product additions",
            "status": "investigating",
            "priority": "medium"
        }
    ]

    # User mapping for ticket attachment
    user_map = {
        "T001": alice,
        "T002": alice,
        "T003": bob,
        "T004": bob,
        "T005": carol
    }
    release_map = {
        "T001": v22,
        "T002": v23,
        "T003": v23,
        "T004": v24,
        "T005": v24
    }
    issue_map = {
        "T001": billing_issue,
        "T002": billing_issue,
        "T003": auth_issue,
        "T004": None,  # new issue
        "T005": search_issue
    }

    tickets = []
    vectors_for_index = []

    for i, t_data in enumerate(tickets_data):
        ticket = db.records.create(label="TICKET", data=t_data)
        tickets.append(ticket)

        # Attach to user
        user = user_map[t_data["ticketId"]]
        db.records.attach(source=user, target=ticket, options={"type": "SUBMITTED"})

        # Attach to release
        release = release_map[t_data["ticketId"]]
        db.records.attach(source=ticket, target=release, options={"type": "REPORTED_IN"})

        # Attach to issue if exists
        issue = issue_map[t_data["ticketId"]]
        if issue:
            db.records.attach(source=ticket, target=issue, options={"type": "TRACKS"})

        # Store vector for later indexing
        vectors_for_index.append({
            "recordId": ticket.id,
            "vector": embed(t_data["description"])
        })

        print(f"  ✓ Ticket: {t_data['ticketId']} - {t_data['description'][:50]}...")

    # Wait for indexes to be ready
    print("\n  Waiting for indexes to become ready...")
    ticket_idx_id = db.ai.indexes.find().data[0].get("__id")
    wait_for_index(ticket_idx_id)

    # Upsert vectors
    print("\n  Indexing ticket descriptions...")
    db.ai.indexes.upsert_vectors(ticket_idx_id, {"items": vectors_for_index})

    # Also index issues
    issue_idx_id = db.ai.indexes.find().data[1].get("__id")
    wait_for_index(issue_idx_id)
    issue_vectors = [
        {"recordId": billing_issue.id, "vector": embed(billing_issue["summary"])}
    ]
    db.ai.indexes.upsert_vectors(issue_idx_id, {"items": issue_vectors})

    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"  • 3 users")
    print(f"  • 5 tickets")
    print(f"  • 3 issues")
    print(f"  • 3 releases (v2.2, v2.3, v2.4)")
    print(f"  • 4 API components")
    print(f"  • 2 fixes")
    print(f"\nAll relationships linked. Vectors indexed.")
    print(f"\nRun: python main.py")

if __name__ == "__main__":
    seed()
