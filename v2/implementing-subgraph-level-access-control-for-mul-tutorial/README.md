# Implementing Subgraph-Level Access Control for Multi-Tenant AI Apps

This example demonstrates how to build a multi-tenant AI application with RushDB, where each tenant has isolated data subspaces (subgraphs) and role-based access control.

## What This Tutorial Covers

- **Tenant isolation** using RushDB workspace/label patterns
- **Subgraph-level access control** — ensuring tenants only access their own data
- **Role-based permissions** within each tenant
- **AI app data model** — documents, embeddings, chat sessions
- **Secure traversal** — querying relationships without cross-tenant data leakage

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RushDB Instance                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Tenant A   │  │  Tenant B   │  │  Tenant C   │         │
│  │  subgraph   │  │  subgraph   │  │  subgraph   │         │
│  │             │  │             │  │             │         │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │         │
│  │ │Documents│ │  │ │Documents│ │  │ │Documents│ │         │
│  │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┤ │         │
│  │ │Sessions │ │  │ │Sessions │ │  │ │Sessions │ │         │
│  │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┤ │         │
│  │ │  Users  │ │  │ │  Users  │ │  │ │  Users  │ │         │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB API key (get one at https://rushdb.com)

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY

# Seed the database with mock data (optional)
python seed.py
```

## Running the Example

```bash
python main.py
```

## Expected Output

The script demonstrates:
1. Creating tenants (WORKSPACE labels)
2. Creating users with roles (ADMIN, MEMBER, VIEWER)
3. Creating AI documents and sessions
4. Verifying tenant isolation with filtered queries
5. Role-based access control patterns

## Key Patterns Demonstrated

### 1. Tenant Isolation via Labels

Every record includes a `workspaceId` property that identifies the tenant:

```sdk
# Creating a tenant-scoped document
doc = db.records.create(
    label="DOCUMENT",
    data={
        "title": "Project Roadmap",
        "workspaceId": "tenant-alpha",  # Tenant identifier
        "createdBy": user.id
    }
)
___SPLIT___
// TypeScript
const doc = await db.records.create({
    label: 'DOCUMENT',
    data: {
        title: 'Project Roadmap',
        workspaceId: 'tenant-alpha',
        createdBy: user.id
    }
})
```

### 2. Filtered Queries for Access Control

Queries always filter by `workspaceId` to ensure tenant isolation:

```sdk
# Query only documents belonging to a specific tenant
documents = db.records.find({
    "labels": ["DOCUMENT"],
    "where": {
        "workspaceId": "tenant-alpha"
    }
})
___SPLIT___
// TypeScript
const documents = await db.records.find({
    labels: ['DOCUMENT'],
    where: {
        workspaceId: 'tenant-alpha'
    }
})
```

### 3. Role-Based Access

Users have roles that determine what operations they can perform:

```sdk
# Check user role before allowing operations
user = db.records.find_by_id(user_id)
if user.data.get("role") == "ADMIN":
    # Allow administrative operations
    pass
___SPLIT___
// TypeScript
const user = await db.records.findById(userId)
if (user.data.role === 'ADMIN') {
    // Allow administrative operations
}
```

## Data Model

| Label | Description | Key Properties |
|-------|-------------|----------------|
| WORKSPACE | Tenant container | `tenantId`, `name`, `plan` |
| USER | User account | `email`, `name`, `role`, `workspaceId` |
| DOCUMENT | AI document/knowledge | `title`, `content`, `workspaceId`, `accessLevel` |
| SESSION | AI chat session | `workspaceId`, `userId`, `status` |
| MESSAGE | Chat message | `content`, `role`, `sessionId` |

## Security Considerations

1. **Always filter by workspaceId** — never expose raw queries without tenant context
2. **Validate relationships** — ensure attached records belong to the same tenant
3. **Role checks before mutations** — verify permissions before create/update/delete
4. **Audit trail** — consider adding `modifiedBy` and `modifiedAt` to sensitive records

## Related Documentation

- [RushDB SDK Reference](https://docs.rushdb.com)
- [Property Graph Modeling](https://docs.rushdb.com/concepts/property-graph)
- [Transactions & Isolation](https://docs.rushdb.com/concepts/transactions)
