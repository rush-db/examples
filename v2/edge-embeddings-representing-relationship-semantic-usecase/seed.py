#!/usr/bin/env python3
"""
Seed script for Edge Embeddings Demo.

Creates agents, PRs, and typed edges with semantic embeddings.
Idempotent: safe to run multiple times.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Embedding model for semantic search on edges
# Using all-MiniLM-L6-v2: fast, high quality, 384 dimensions
MODEL_NAME = "all-MiniLM-L6-v2"


def embed_texts(model, texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def get_or_create_label(db: RushDB, label: str) -> list:
    """Check if records with this label exist; return them if so."""
    result = db.records.find({"labels": [label], "limit": 1})
    return result.data


def seed():
    print("🚀 Starting seed process...")
    print(f"   Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("   ✓ Model loaded")

    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "RUSHDB_API_KEY not found. Copy .env.example to .env and add your key."
        )

    db = RushDB(api_key)
    print("   ✓ Connected to RushDB")

    # Check for existing data
    existing_agents = get_or_create_label(db, "AGENT")
    existing_prs = get_or_create_label(db, "PR")

    if existing_agents and existing_prs:
        print("\n📦 Data already exists — skipping seed (idempotent check)")
        print(f"   Found {len(existing_agents)} agents, {len(existing_prs)} PRs")
        return

    print("\n📝 Seeding fresh data...")

    # ─────────────────────────────────────────────────────────────────
    # CREATE NODES: AGENTS
    # ─────────────────────────────────────────────────────────────────
    agents_data = [
        {"name": "Alice Chen", "role": "frontend-dev", "team": "web-platform"},
        {"name": "Bob Martinez", "role": "backend-dev", "team": "core-services"},
        {"name": "Carol Davis", "role": "security-engineer", "team": "security"},
        {"name": "Dave Wilson", "role": "tech-lead", "team": "web-platform"},
        {"name": "Eve Thompson", "role": "devops", "team": "infrastructure"},
    ]

    print("\n  Creating AGENT records...")
    agents = []
    for i, data in enumerate(agents_data):
        agent = db.records.create(label="AGENT", data=data)
        agents.append(agent)
        if (i + 1) % 100 == 0:
            print(f"    ✓ Created {i + 1} agents...")
    print(f"    ✓ Created {len(agents)} agents")

    # ─────────────────────────────────────────────────────────────────
    # CREATE NODES: PULL REQUESTS
    # ─────────────────────────────────────────────────────────────────
    prs_data = [
        {
            "title": "Add user authentication module",
            "description": "New login system with JWT tokens and refresh token rotation",
            "repo": "acme/web-app",
            "priority": "high",
        },
        {
            "title": "Fix pagination bug in search results",
            "description": "Pagination resets to page 1 when filters change",
            "repo": "acme/web-app",
            "priority": "medium",
        },
        {
            "title": "Implement webhook delivery retry system",
            "description": "Adds exponential backoff for failed webhook deliveries",
            "repo": "acme/api-gateway",
            "priority": "high",
        },
        {
            "title": "Refactor database connection pooling",
            "description": "Migrate from Sequelize to native pg pool for performance",
            "repo": "acme/api-gateway",
            "priority": "medium",
        },
        {
            "title": "Add audit logging for admin actions",
            "description": "Track all admin panel actions for compliance",
            "repo": "acme/admin-panel",
            "priority": "high",
        },
        {
            "title": "Update dependencies to latest versions",
            "description": "Security patches for 12 packages",
            "repo": "acme/shared-libs",
            "priority": "low",
        },
    ]

    print("\n  Creating PR records...")
    prs = []
    for i, data in enumerate(prs_data):
        pr = db.records.create(label="PR", data=data)
        prs.append(pr)
        if (i + 1) % 100 == 0:
            print(f"    ✓ Created {i + 1} PRs...")
    print(f"    ✓ Created {len(prs)} PRs")

    # ─────────────────────────────────────────────────────────────────
    # CREATE EDGES: Reviews with semantic reasons
    # ─────────────────────────────────────────────────────────────────
    # Each edge has:
    #   - reason: natural language (used for semantic embedding)
    #   - securityReviewed: boolean
    #   - timestamp: ISO string

    reviews = [
        # Alice: fast, casual approvals (no security review)
        {
            "source_idx": 0,  # Alice
            "target_idx": 0,  # PR-101
            "type": "APPROVED",
            "reason": "Quick pass, seemed fine",
            "securityReviewed": False,
            "timestamp": "2024-01-15T10:30:00Z",
        },
        {
            "source_idx": 0,  # Alice
            "target_idx": 1,  # PR-102
            "type": "REVIEWED",
            "reason": "Moderate changes, well documented, LGTM",
            "securityReviewed": False,
            "timestamp": "2024-01-16T14:22:00Z",
        },
        {
            "source_idx": 0,  # Alice
            "target_idx": 4,  # PR-105
            "type": "APPROVED",
            "reason": "LGTM, nice cleanup",
            "securityReviewed": False,
            "timestamp": "2024-01-20T09:15:00Z",
        },

        # Bob: minimal effort approvals (no security review)
        {
            "source_idx": 1,  # Bob
            "target_idx": 0,  # PR-101
            "type": "APPROVED",
            "reason": "Looks okay, good enough",
            "securityReviewed": False,
            "timestamp": "2024-01-15T11:00:00Z",
        },
        {
            "source_idx": 1,  # Bob
            "target_idx": 1,  # PR-102
            "type": "APPROVED",
            "reason": "Looks fine to me, passing along",
            "securityReviewed": False,
            "timestamp": "2024-01-16T15:00:00Z",
        },
        {
            "source_idx": 1,  # Bob
            "target_idx": 2,  # PR-103
            "type": "APPROVED",
            "reason": "Standard feature work, no issues",
            "securityReviewed": False,
            "timestamp": "2024-01-17T16:45:00Z",
        },
        {
            "source_idx": 1,  # Bob
            "target_idx": 3,  # PR-104
            "type": "APPROVED",
            "reason": "Seems straightforward",
            "securityReviewed": False,
            "timestamp": "2024-01-18T10:30:00Z",
        },

        # Carol: thorough, flags security issues (security review done)
        {
            "source_idx": 2,  # Carol
            "target_idx": 0,  # PR-101
            "type": "FLAGGED",
            "reason": "Potential SQL injection in login handler",
            "securityReviewed": True,
            "timestamp": "2024-01-15T12:00:00Z",
        },
        {
            "source_idx": 2,  # Carol
            "target_idx": 1,  # PR-102
            "type": "FLAGGED",
            "reason": "Potential injection vulnerability in webhook parser",
            "securityReviewed": True,
            "timestamp": "2024-01-16T16:30:00Z",
        },
        {
            "source_idx": 2,  # Carol
            "target_idx": 2,  # PR-103
            "type": "FLAGGED",
            "reason": "Incomplete error handling, critical path missing validation",
            "securityReviewed": True,
            "timestamp": "2024-01-17T17:00:00Z",
        },
        {
            "source_idx": 2,  # Carol
            "target_idx": 4,  # PR-105
            "type": "REVIEWED",
            "reason": "Audit logging implemented correctly, approved",
            "securityReviewed": True,
            "timestamp": "2024-01-20T14:00:00Z",
        },

        # Dave: acknowledges concerns but approves anyway (no security review)
        {
            "source_idx": 3,  # Dave
            "target_idx": 0,  # PR-101
            "type": "APPROVED",
            "reason": "Alice already approved, looks good",
            "securityReviewed": False,
            "timestamp": "2024-01-15T13:30:00Z",
        },
        {
            "source_idx": 3,  # Dave
            "target_idx": 2,  # PR-103
            "type": "APPROVED",
            "reason": "Acknowledging Carol's concerns but moving forward",
            "securityReviewed": False,
            "timestamp": "2024-01-17T18:00:00Z",
        },
        {
            "source_idx": 3,  # Dave
            "target_idx": 5,  # PR-106
            "type": "APPROVED",
            "reason": "Dependency updates are routine, no concerns",
            "securityReviewed": False,
            "timestamp": "2024-01-21T11:00:00Z",
        },

        # Eve: security-focused reviews (security review done)
        {
            "source_idx": 4,  # Eve
            "target_idx": 1,  # PR-102
            "type": "REVIEWED",
            "reason": "Webhook security looks solid, proper sanitization",
            "securityReviewed": True,
            "timestamp": "2024-01-16T17:30:00Z",
        },
        {
            "source_idx": 4,  # Eve
            "target_idx": 3,  # PR-104
            "type": "REVIEWED",
            "reason": "Connection pooling is safe, verified edge cases",
            "securityReviewed": True,
            "timestamp": "2024-01-18T14:00:00Z",
        },
        {
            "source_idx": 4,  # Eve
            "target_idx": 4,  # PR-105
            "type": "APPROVED",
            "reason": "Admin audit trail meets compliance requirements",
            "securityReviewed": True,
            "timestamp": "2024-01-20T15:30:00Z",
        },
    ]

    print("\n  Creating typed edge relationships with embeddings...")

    # Create vector index for edge reasons (external, 384 dimensions)
    index = db.ai.indexes.create({
        "label": "EDGE_REVIEW",
        "propertyName": "reason",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine",
    })
    index_id = index.data["__id"]
    print(f"    ✓ Created vector index for EDGE_REVIEW.reason: {index_id}")

    # Prepare all edge reasons for batch embedding
    edge_reasons = [r["reason"] for r in reviews]
    print(f"    Generating embeddings for {len(edge_reasons)} edges...")
    vectors = embed_texts(model, edge_reasons)
    print(f"    ✓ Generated {len(vectors)} embeddings (dim={len(vectors[0])})")

    # Create edges with inline vectors
    edges_created = 0
    for i, review in enumerate(reviews):
        agent = agents[review["source_idx"]]
        pr = prs[review["target_idx"]]

        edge_data = {
            "reason": review["reason"],
            "type": review["type"],
            "securityReviewed": review["securityReviewed"],
            "timestamp": review["timestamp"],
            # Store the agent and PR IDs for queries
            "agentId": agent.id,
            "prId": pr.id,
            "agentName": agent["name"],
            "prTitle": pr["title"],
        }

        edge = db.records.create(
            label="EDGE_REVIEW",
            data=edge_data,
            vectors=[{"propertyName": "reason", "vector": vectors[i]}],
        )

        # Attach as a relationship
        db.records.attach(
            source=agent,
            target=pr,
            options={"type": review["type"]},
        )

        edges_created += 1
        if edges_created % 100 == 0:
            print(f"    ✓ Created {edges_created} edges...")

    print(f"    ✓ Created {edges_created} typed edges with embeddings")

    # Create a node-level index for PR descriptions (for completeness)
    pr_index = db.ai.indexes.create({
        "label": "PR",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine",
    })
    pr_index_id = pr_index.data["__id"]

    pr_descriptions = [pr["description"] for pr in prs_data]
    pr_vectors = embed_texts(model, pr_descriptions)

    db.ai.indexes.upsert_vectors(pr_index_id, {
        "items": [
            {"recordId": prs[i].id, "vector": pr_vectors[i]}
            for i in range(len(prs))
        ]
    })

    print(f"    ✓ Created and populated PR description index")

    print("\n✅ Seed complete!")
    print(f"   • {len(agents)} agents")
    print(f"   • {len(prs)} PRs")
    print(f"   • {len(reviews)} typed edges with semantic embeddings")


if __name__ == "__main__":
    seed()
