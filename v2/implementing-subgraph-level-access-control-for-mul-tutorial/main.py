"""
Multi-Tenant AI Application with Subgraph-Level Access Control

This example demonstrates how to implement secure multi-tenant data isolation
using RushDB. Each tenant's data forms an isolated subgraph, and all queries
respect tenant boundaries through workspaceId filtering.

Key concepts demonstrated:
1. Tenant isolation via workspaceId property
2. Role-based access control (ADMIN, MEMBER, VIEWER)
3. Subgraph-scoped queries (documents, sessions, messages)
4. Secure relationship traversal
5. Permission validation before mutations
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


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def print_subsection(title):
    """Print a subsection header."""
    print(f"\n--- {title} ---")


def demo_tenant_isolation():
    """Demonstrate that tenants cannot see each other's data."""
    print_section("DEMO 1: Tenant Isolation via Subgraph Filtering")

    # Get all workspaces
    workspaces = db.records.find({"labels": ["WORKSPACE"]})
    print(f"\nFound {len(workspaces)} workspaces in the database")

    for workspace in workspaces:
        tenant_id = workspace.data.get("tenantId")
        print(f"\n  Tenant: {workspace.data.get('name')} (ID: {tenant_id})")

        # Query documents for THIS tenant only
        tenant_docs = db.records.find({
            "labels": ["DOCUMENT"],
            "where": {"workspaceId": tenant_id}
        })
        print(f"    Documents: {len(tenant_docs)}")
        for doc in tenant_docs:
            print(f"      - {doc.data.get('title')}")

        # Query sessions for THIS tenant only
        tenant_sessions = db.records.find({
            "labels": ["SESSION"],
            "where": {"workspaceId": tenant_id}
        })
        print(f"    Sessions: {len(tenant_sessions)}")

        # Query users for THIS tenant only
        tenant_users = db.records.find({
            "labels": ["USER"],
            "where": {"workspaceId": tenant_id}
        })
        print(f"    Users: {len(tenant_users)}")
        for user in tenant_users:
            print(f"      - {user.data.get('name')} ({user.data.get('role')})")


def demo_cross_tenant_query_prevention():
    """Demonstrate that querying without workspaceId returns no results."""
    print_section("DEMO 2: Cross-Tenant Query Prevention")

    # Try to query documents without tenant filter
    print("\nAttempting to query all documents (no workspaceId filter)...")
    all_docs = db.records.find({"labels": ["DOCUMENT"], "where": {}})
    print(f"  Total documents across ALL tenants: {len(all_docs)}")

    # Without workspaceId, we might get all documents - this is a security concern
    # In production, you'd want to middleware to enforce workspaceId on all queries
    print("\n  ⚠️  Note: In production, always enforce workspaceId at the API/middleware layer")
    print("  to prevent accidental cross-tenant data exposure.")

    # Safe query with workspaceId
    print("\nSafe query with workspaceId filter:")
    alpha_docs = db.records.find({
        "labels": ["DOCUMENT"],
        "where": {"workspaceId": "alphacorp"}
    })
    print(f"  AlphaCorp documents: {len(alpha_docs)}")
    print(f"  BetaInc documents: {len(db.records.find({'labels': ['DOCUMENT'], 'where': {'workspaceId': 'betainc'}}))}")
    print(f"  GammaLtd documents: {len(db.records.find({'labels': ['DOCUMENT'], 'where': {'workspaceId': 'gammaltd'}}))}")


def demo_role_based_access():
    """Demonstrate role-based access control within a tenant."""
    print_section("DEMO 3: Role-Based Access Control")

    tenant_id = "alphacorp"
    print(f"\nExamining roles within {tenant_id}:")

    users = db.records.find({
        "labels": ["USER"],
        "where": {"workspaceId": tenant_id}
    })

    for user in users:
        role = user.data.get("role")
        name = user.data.get("name")
        email = user.data.get("email")

        print(f"\n  User: {name}")
        print(f"    Email: {email}")
        print(f"    Role: {role}")

        # Define permissions based on role
        if role == "ADMIN":
            permissions = [
                "Create/update/delete documents",
                "Manage users",
                "View all sessions",
                "Manage workspace settings",
            ]
        elif role == "MEMBER":
            permissions = [
                "Create/update own documents",
                "View documents",
                "Participate in sessions",
            ]
        else:  # VIEWER
            permissions = [
                "View documents (read-only)",
                "View own session history",
            ]

        print(f"    Permissions:")
        for perm in permissions:
            print(f"      ✓ {perm}")


def demo_permission_check():
    """Demonstrate a permission check before a mutation."""
    print_section("DEMO 4: Permission Check Before Mutation")

    def can_delete_document(user_id, document_id):
        """Check if a user has permission to delete a document."""
        user = db.records.find_by_id(user_id)
        if not user.exists:
            return False, "User not found"

        role = user.data.get("role")

        # Only ADMIN and MEMBER can delete
        if role not in ["ADMIN", "MEMBER"]:
            return False, f"Role '{role}' cannot delete documents"

        # Check workspace ownership
        document = db.records.find_by_id(document_id)
        if not document.exists:
            return False, "Document not found"

        if user.data.get("workspaceId") != document.data.get("workspaceId"):
            return False, "Cannot delete documents from other workspaces"

        return True, "Permission granted"

    # Get a document and users
    docs = db.records.find({"labels": ["DOCUMENT"], "where": {"workspaceId": "alphacorp"}})
    users = db.records.find({"labels": ["USER"], "where": {"workspaceId": "alphacorp"}})

    if docs and users:
        doc = docs[0]
        print(f"\nDocument: {doc.data.get('title')} (ID: {doc.id})")

        for user in users:
            can_delete, message = can_delete_document(user.id, doc.id)
            status = "✓ ALLOWED" if can_delete else "✗ DENIED"
            print(f"\n  {user.data.get('name')} ({user.data.get('role')}): {status}")
            print(f"    Reason: {message}")


def demo_subgraph_traversal():
    """Demonstrate safe traversal within a tenant subgraph."""
    print_section("DEMO 5: Subgraph Traversal with Tenant Isolation")

    tenant_id = "alphacorp"
    print(f"\nTraversing {tenant_id} subgraph...")

    # Get admin user
    admin = db.records.find({
        "labels": ["USER"],
        "where": {"workspaceId": tenant_id, "role": "ADMIN"}
    })

    if admin:
        admin_user = admin[0]
        print(f"\n  Admin user: {admin_user.data.get('name')}")

        # Find sessions created by this admin
        user_sessions = db.records.find({
            "labels": ["SESSION"],
            "where": {"CREATED_BY": {"$id": admin_user.id}}
        })
        print(f"  Sessions created by admin: {len(user_sessions)}")

        # For each session, get messages (within same tenant)
        for session in user_sessions:
            messages = db.records.find({
                "labels": ["MESSAGE"],
                "where": {
                    "sessionId": session.id,
                    "workspaceId": tenant_id  # Enforce tenant context
                }
            })
            print(f"\n    Session: {session.data.get('title')}")
            print(f"      Messages: {len(messages)}")
            for msg in messages[:2]:  # Show first 2 messages
                role = msg.data.get("role")
                content = msg.data.get("content", "")[:50]
                print(f"        [{role}] {content}...")


def demo_secure_document_creation():
    """Demonstrate secure document creation with workspace validation."""
    print_section("DEMO 6: Secure Document Creation")

    def create_document_secure(user_id, title, content):
        """Create a document with workspace validation."""
        user = db.records.find_by_id(user_id)
        if not user.exists:
            raise ValueError("User not found")

        workspace_id = user.data.get("workspaceId")
        role = user.data.get("role")

        # Check permission based on role
        if role == "VIEWER":
            raise PermissionError("Viewers cannot create documents")

        # Create document with workspaceId
        doc = db.records.create(
            label="DOCUMENT",
            data={
                "title": title,
                "content": content,
                "workspaceId": workspace_id,
                "createdBy": user_id,
                "accessLevel": "internal",
            }
        )

        print(f"  Created document: {title}")
        print(f"    Workspace: {workspace_id}")
        print(f"    Creator: {user.data.get('name')} ({role})")

        return doc

    # Get users of different roles
    users = db.records.find({
        "labels": ["USER"],
        "where": {"workspaceId": "alphacorp"}
    })

    print("\nAttempting document creation with different roles:")

    for user in users:
        role = user.data.get("role")
        print(f"\n  User: {user.data.get('name')} (Role: {role})")

        try:
            doc = create_document_secure(
                user_id=user.id,
                title=f"Test Document by {user.data.get('name')}",
                content="This is a test document."
            )
            print(f"    Result: ✓ Created successfully")

            # Cleanup: delete the test document
            db.records.delete(record_id=doc.id)
            print(f"    Cleanup: Test document deleted")

        except PermissionError as e:
            print(f"    Result: ✗ {e}")
        except Exception as e:
            print(f"    Result: ✗ Error - {e}")


def demo_workspace_context_manager():
    """Demonstrate a context manager pattern for workspace isolation."""
    print_section("DEMO 7: Workspace Context Manager Pattern")

    class WorkspaceContext:
        """Context manager for workspace-scoped operations."""

        def __init__(self, db, workspace_id):
            self.db = db
            self.workspace_id = workspace_id

        def find(self, labels, where=None):
            """Scoped find query."""
            query = {
                "labels": labels,
                "where": where or {}
            }
            # Always inject workspaceId
            query["where"]["workspaceId"] = self.workspace_id
            return self.db.records.find(query)

        def create(self, label, data):
            """Scoped create with workspaceId injection."""
            data["workspaceId"] = self.workspace_id
            return self.db.records.create(label=label, data=data)

    print("\nUsing WorkspaceContext for tenant-scoped operations:")

    # Create context for AlphaCorp
    alpha_ctx = WorkspaceContext(db, "alphacorp")

    # Query documents (workspaceId auto-injected)
    docs = alpha_ctx.find(["DOCUMENT"])
    print(f"\n  AlphaCorp documents (via context): {len(docs)}")

    # Query users (workspaceId auto-injected)
    users = alpha_ctx.find(["USER"])
    print(f"  AlphaCorp users (via context): {len(users)}")

    # Create new session (workspaceId auto-injected)
    session = alpha_ctx.create("SESSION", {
        "title": "Context Manager Test Session",
        "status": "active"
    })
    print(f"  Created session: {session.data.get('title')}")
    print(f"    workspaceId automatically set to: {session.data.get('workspaceId')}")

    # Cleanup
    db.records.delete(record_id=session.id)
    print("  Cleanup: Test session deleted")


def demo_ai_search_with_tenant_isolation():
    """Demonstrate AI semantic search within tenant context."""
    print_section("DEMO 8: AI Search with Tenant Isolation")

    tenant_id = "alphacorp"
    print(f"\nSearching within {tenant_id} subgraph...")

    # Note: In production, you would need to create a vector index first
    # db.ai.indexes.create({"label": "DOCUMENT", "propertyName": "content"})

    # For this demo, we'll show the pattern (actual search requires indexed data)
    print("\n  AI search pattern for tenant isolation:")
    print("  " + "-" * 50)
    print("""
    search_results = db.ai.search({
        "propertyName": "content",
        "query": "quarterly strategy",
        "labels": ["DOCUMENT"],
        "where": {
            "workspaceId": "alphacorp"  # Tenant isolation enforced
        },
        "limit": 5
    })
    """)

    # Demonstrate that searching without tenant filter would search all tenants
    print("\n  ⚠️  Without 'where' filter, AI search spans ALL tenants!")
    print("  Always include workspaceId in production AI searches.")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  MULTI-TENANT ACCESS CONTROL DEMONSTRATION")
    print("  Using RushDB for Subgraph-Level Data Isolation")
    print("=" * 60)

    # Demo 1: Tenant isolation via subgraph filtering
    demo_tenant_isolation()

    # Demo 2: Cross-tenant query prevention
    demo_cross_tenant_query_prevention()

    # Demo 3: Role-based access control
    demo_role_based_access()

    # Demo 4: Permission check before mutation
    demo_permission_check()

    # Demo 5: Subgraph traversal with tenant isolation
    demo_subgraph_traversal()

    # Demo 6: Secure document creation
    demo_secure_document_creation()

    # Demo 7: Workspace context manager pattern
    demo_workspace_context_manager()

    # Demo 8: AI search with tenant isolation
    demo_ai_search_with_tenant_isolation()

    print("\n" + "=" * 60)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  1. Always filter queries by workspaceId for tenant isolation")
    print("  2. Use role-based permission checks before mutations")
    print("  3. Validate relationship endpoints belong to same tenant")
    print("  4. Consider a context manager to enforce workspace scope")
    print("  5. AI searches also need workspaceId filter for isolation")
    print("\n")


if __name__ == "__main__":
    main()
