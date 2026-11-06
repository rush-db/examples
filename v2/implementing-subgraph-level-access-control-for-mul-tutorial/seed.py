"""
Seed script for multi-tenant AI app example.

This script creates:
- 3 tenants (workspaces): AlphaCorp, BetaInc, GammaLtd
- Users with different roles (ADMIN, MEMBER, VIEWER) per tenant
- Documents and AI sessions for each tenant
- Messages within sessions

Run this script to populate the database with realistic mock data.
It is idempotent — running multiple times is safe.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)

# Tenant configurations
TENANTS = [
    {
        "tenantId": "alphacorp",
        "name": "AlphaCorp",
        "plan": "enterprise",
        "users": [
            {"email": "alice@alphacorp.com", "name": "Alice Chen", "role": "ADMIN"},
            {"email": "bob@alphacorp.com", "name": "Bob Martinez", "role": "MEMBER"},
            {"email": "carol@alphacorp.com", "name": "Carol White", "role": "VIEWER"},
        ],
        "documents": [
            {"title": "Q1 2024 Strategy", "accessLevel": "internal"},
            {"title": "Product Roadmap 2024", "accessLevel": "restricted"},
            {"title": "Engineering Best Practices", "accessLevel": "public"},
        ],
        "sessions": [
            {"title": "Q1 Planning Discussion"},
            {"title": "Feature Prioritization"},
        ],
    },
    {
        "tenantId": "betainc",
        "name": "BetaInc",
        "plan": "pro",
        "users": [
            {"email": "david@betainc.com", "name": "David Kim", "role": "ADMIN"},
            {"email": "emma@betainc.com", "name": "Emma Johnson", "role": "MEMBER"},
        ],
        "documents": [
            {"title": "Marketing Campaign 2024", "accessLevel": "internal"},
            {"title": "Customer Research Summary", "accessLevel": "restricted"},
        ],
        "sessions": [
            {"title": "Campaign Strategy Review"},
        ],
    },
    {
        "tenantId": "gammaltd",
        "name": "GammaLtd",
        "plan": "starter",
        "users": [
            {"email": "frank@gammaltd.com", "name": "Frank Thompson", "role": "ADMIN"},
        ],
        "documents": [
            {"title": "Getting Started Guide", "accessLevel": "public"},
        ],
        "sessions": [
            {"title": "Onboarding Support"},
        ],
    },
]

MESSAGE_TEMPLATES = [
    {"role": "user", "content": "What are the key priorities for this quarter?"},
    {"role": "assistant", "content": "Based on the documents, the main priorities are: 1) Market expansion, 2) Product innovation, 3) Customer retention."},
    {"role": "user", "content": "Can you elaborate on the market expansion strategy?"},
    {"role": "assistant", "content": "The market expansion focuses on entering two new geographic regions. This involves local partnerships and localized product offerings."},
    {"role": "user", "content": "What's the timeline for this expansion?"},
    {"role": "assistant", "content": "The expansion is planned in phases: Phase 1 (Q2) covers region A, Phase 2 (Q4) covers region B. Total timeline is approximately 9 months."},
]


def cleanup_existing_data():
    """Remove all existing records with our test labels."""
    print("Cleaning up existing data...")
    labels_to_clean = ["MESSAGE", "SESSION", "DOCUMENT", "USER", "WORKSPACE"]
    for label in labels_to_clean:
        db.records.delete_many({"labels": [label], "where": {}})
    print("Cleanup complete.")


def create_workspace(tenant_config):
    """Create a workspace record for a tenant."""
    workspace = db.records.upsert(
        label="WORKSPACE",
        data={
            "tenantId": tenant_config["tenantId"],
            "name": tenant_config["name"],
            "plan": tenant_config["plan"],
            "createdAt": "2024-01-01T00:00:00Z",
        },
        options={"mergeBy": ["tenantId"]},
    )
    return workspace


def create_users(workspace, users_config, tenant_id):
    """Create user records for a workspace."""
    users = []
    for user_config in users_config:
        user = db.records.upsert(
            label="USER",
            data={
                "email": user_config["email"],
                "name": user_config["name"],
                "role": user_config["role"],
                "workspaceId": tenant_id,
                "active": True,
            },
            options={"mergeBy": ["email"]},
        )
        # Link user to workspace
        db.records.attach(source=user, target=workspace, options={"type": "BELONGS_TO"})
        users.append(user)
        print(f"  Created user: {user_config['name']} ({user_config['role']})")
    return users


def create_documents(users, documents_config, tenant_id):
    """Create document records for a workspace."""
    admin_user = users[0]  # First user is admin
    documents = []
    for i, doc_config in enumerate(documents_config):
        doc = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc_config["title"],
                "content": f"This is the content for {doc_config['title']}. It contains important information relevant to {tenant_id}.",
                "accessLevel": doc_config["accessLevel"],
                "workspaceId": tenant_id,
                "createdBy": admin_user.id,
                "version": 1,
            },
        )
        documents.append(doc)
        print(f"  Created document: {doc_config['title']}")
    return documents


def create_sessions(users, sessions_config, tenant_id):
    """Create AI chat sessions for a workspace."""
    sessions = []
    for session_config in sessions_config:
        session = db.records.create(
            label="SESSION",
            data={
                "title": session_config["title"],
                "workspaceId": tenant_id,
                "status": "active",
                "createdAt": "2024-01-15T10:00:00Z",
            },
        )
        # Link session to creator (first user)
        db.records.attach(source=session, target=users[0], options={"type": "CREATED_BY"})
        sessions.append(session)
        print(f"  Created session: {session_config['title']}")
    return sessions


def create_messages(sessions, tenant_id):
    """Create messages within sessions."""
    for session in sessions:
        for msg_template in MESSAGE_TEMPLATES:
            msg = db.records.create(
                label="MESSAGE",
                data={
                    "role": msg_template["role"],
                    "content": msg_template["content"],
                    "workspaceId": tenant_id,
                    "sessionId": session.id,
                },
            )
            db.records.attach(source=msg, target=session, options={"type": "BELONGS_TO"})
        print(f"  Created {len(MESSAGE_TEMPLATES)} messages for session: {session.data.get('title', session.id)}")


def main():
    print("\n" + "=" * 60)
    print("MULTI-TENANT SEED SCRIPT")
    print("=" * 60 + "\n")

    # Cleanup existing data
    cleanup_existing_data()

    for i, tenant in enumerate(TENANTS):
        print(f"\n[{i+1}/{len(TENANTS)}] Creating tenant: {tenant['name']}")
        print("-" * 40)

        # Create workspace
        workspace = create_workspace(tenant)
        print(f"  Created workspace: {tenant['name']}")

        # Create users
        users = create_users(workspace, tenant["users"], tenant["tenantId"])

        # Create documents
        documents = create_documents(users, tenant["documents"], tenant["tenantId"])

        # Create sessions
        sessions = create_sessions(users, tenant["sessions"], tenant["tenantId"])

        # Create messages
        create_messages(sessions, tenant["tenantId"])

    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"\nCreated {len(TENANTS)} workspaces with users, documents, and sessions.")
    print("\nYou can now run 'python main.py' to see the access control demo.")


if __name__ == "__main__":
    main()
