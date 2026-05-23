#!/usr/bin/env python3
"""
Seed script for the Goal-Subgoal Decomposition Tracker.

Generates a realistic goal hierarchy with:
- High-level project goals
- Subgoals with dependencies
- Blocker relationships
- Semantic embeddings for all goal descriptions

This script is idempotent: it checks for existing data and skips seeding if present.
"""

import os
import random
from dotenv import load_dotenv

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Initialize embedding model (all-MiniLM-L6-v2 is fast and accurate for this use case)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Seed data - realistic goal hierarchy for a software product launch
GOALS_DATA = [
    # Level 0: Epic goals
    {
        "title": "Launch new SaaS product",
        "description": "Successfully launch our new software-as-a-service product to market with all core features functional and documented.",
        "status": "active",
        "priority": "high",
        "level": 0,
        "children": [
            {
                "title": "Design product architecture",
                "description": "Define the overall system architecture including frontend, backend, database, and third-party integrations.",
                "status": "completed",
                "priority": "high",
                "level": 1,
                "children": [
                    {
                        "title": "Select technology stack",
                        "description": "Evaluate and choose the programming languages, frameworks, and tools for each component of the system.",
                        "status": "completed",
                        "priority": "high",
                    },
                    {
                        "title": "Define database schema",
                        "description": "Design the relational database structure including tables, relationships, and indexes.",
                        "status": "completed",
                        "priority": "medium",
                    },
                    {
                        "title": "Plan API contracts",
                        "description": "Define REST or GraphQL API endpoints, request/response formats, and authentication methods.",
                        "status": "completed",
                        "priority": "high",
                    },
                ],
            },
            {
                "title": "Build user authentication system",
                "description": "Implement secure login, registration, password reset, and session management for the application.",
                "status": "active",
                "priority": "high",
                "level": 1,
                "children": [
                    {
                        "title": "Implement user registration",
                        "description": "Create signup flow with email verification, password requirements, and duplicate prevention.",
                        "status": "completed",
                        "priority": "high",
                    },
                    {
                        "title": "Build login functionality",
                        "description": "Develop secure login with email/password, remember me option, and brute force protection.",
                        "status": "completed",
                        "priority": "high",
                    },
                    {
                        "title": "Add multi-factor authentication",
                        "description": "Integrate TOTP-based two-factor authentication using authenticator apps.",
                        "status": "in_progress",
                        "priority": "medium",
                    },
                    {
                        "title": "Implement social login",
                        "description": "Add OAuth integration for Google, GitHub, and other social authentication providers.",
                        "status": "pending",
                        "priority": "low",
                    },
                ],
            },
            {
                "title": "Develop frontend user interface",
                "description": "Build the client-facing web application with responsive design and accessibility compliance.",
                "status": "active",
                "priority": "high",
                "level": 1,
                "children": [
                    {
                        "title": "Create design system",
                        "description": "Develop reusable UI components, color palette, typography guidelines, and spacing conventions.",
                        "status": "completed",
                        "priority": "medium",
                    },
                    {
                        "title": "Build dashboard view",
                        "description": "Implement the main dashboard with charts, metrics visualization, and interactive widgets.",
                        "status": "in_progress",
                        "priority": "high",
                    },
                    {
                        "title": "Implement settings page",
                        "description": "Create user preferences, account settings, notification configurations, and profile management.",
                        "status": "pending",
                        "priority": "medium",
                    },
                ],
            },
            {
                "title": "Create backend API services",
                "description": "Develop server-side business logic, database operations, and integration endpoints for the application.",
                "status": "active",
                "priority": "high",
                "level": 1,
                "children": [
                    {
                        "title": "Build user management endpoints",
                        "description": "Create CRUD operations for user profiles, preferences, and account management features.",
                        "status": "completed",
                        "priority": "high",
                    },
                    {
                        "title": "Implement billing integration",
                        "description": "Integrate payment processing with Stripe including subscriptions, invoices, and refunds.",
                        "status": "in_progress",
                        "priority": "high",
                    },
                    {
                        "title": "Build notification service",
                        "description": "Develop email and push notification system for alerts, reminders, and user communications.",
                        "status": "pending",
                        "priority": "low",
                    },
                ],
            },
            {
                "title": "Write user documentation",
                "description": "Create comprehensive documentation for users, administrators, and developers.",
                "status": "pending",
                "priority": "medium",
                "level": 1,
                "children": [
                    {
                        "title": "Write user guide",
                        "description": "Create step-by-step instructions for end users covering all application features.",
                        "status": "pending",
                        "priority": "medium",
                    },
                    {
                        "title": "Document API endpoints",
                        "description": "Generate OpenAPI/Swagger documentation for all REST API endpoints with examples.",
                        "status": "pending",
                        "priority": "medium",
                    },
                ],
            },
        ],
    },
    {
        "title": "Optimize system performance",
        "description": "Achieve target response times and throughput for all critical user interactions under expected load.",
        "status": "active",
        "priority": "medium",
        "level": 0,
        "children": [
            {
                "title": "Profile application bottlenecks",
                "description": "Identify performance issues using profiling tools and monitoring in production-like environments.",
                "status": "in_progress",
                "priority": "high",
                "children": [],
            },
            {
                "title": "Implement database query optimization",
                "description": "Reduce query execution time through indexing, query rewriting, and connection pooling.",
                "status": "pending",
                "priority": "high",
            },
        ],
    },
    {
        "title": "Establish security compliance",
        "description": "Meet SOC2 and GDPR requirements with proper encryption, access controls, and audit logging.",
        "status": "pending",
        "priority": "high",
        "level": 0,
        "children": [
            {
                "title": "Implement data encryption",
                "description": "Enable encryption at rest and in transit for all sensitive user data and communications.",
                "status": "pending",
                "priority": "high",
            },
            {
                "title": "Set up audit logging",
                "description": "Configure comprehensive logging of security events, data access, and administrative actions.",
                "status": "pending",
                "priority": "medium",
            },
        ],
    },
]

# Prerequisite and blocker relationships
# Format: (goal_title, prerequisite_title)
PREREQUISITES = [
    ("Build frontend user interface", "Design product architecture"),
    ("Create backend API services", "Design product architecture"),
    ("Implement multi-factor authentication", "Build login functionality"),
    ("Implement social login", "Implement multi-factor authentication"),
    ("Implement billing integration", "Build user management endpoints"),
    ("Write user guide", "Create design system"),
    ("Document API endpoints", "Create backend API services"),
    ("Implement database query optimization", "Profile application bottlenecks"),
    ("Implement data encryption", "Implement social login"),
]

BLOCKERS = [
    ("Implement social login", "Implement multi-factor authentication"),
    ("Implement billing integration", "Build user management endpoints"),
    ("Write user guide", "Create design system"),
]


def get_embedding_model():
    """Load and return the sentence transformer embedding model."""
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts, model):
    """Generate embeddings for a list of texts."""
    return model.encode(texts, show_progress_bar=False)


def create_goal_hierarchy(db, goals_data, parent_record=None, level=0):
    """Recursively create goals and their children."""
    created_goals = []
    
    for i, goal_data in enumerate(goals_data):
        # Prepare description for embedding
        description = goal_data.get("description", "")
        
        # Create the goal record with vector embedding
        goal_record = db.records.create(
            label="GOAL",
            data={
                "title": goal_data["title"],
                "description": description,
                "status": goal_data.get("status", "pending"),
                "priority": goal_data.get("priority", "medium"),
                "level": goal_data.get("level", 0),
            },
            vectors=[{"propertyName": "description", "vector": embed_texts([description], embedding_model)[0].tolist()}]
        )
        created_goals.append((goal_data["title"], goal_record))
        
        # Print progress every 5 goals
        if len(created_goals) % 5 == 0:
            print(f"  Created {len(created_goals)} goals...")
        
        # Link to parent if exists
        if parent_record:
            db.records.attach(
                source=parent_record,
                target=goal_record,
                options={"type": "HAS_SUBGOAL", "direction": "out"}
            )
        
        # Process children recursively
        children = goal_data.get("children", [])
        if children:
            child_goals = create_goal_hierarchy(db, children, goal_record, level + 1)
            created_goals.extend(child_goals)
    
    return created_goals


def establish_prerequisites(db, goals_created):
    """Create prerequisite relationships between goals."""
    goal_map = {title: record for title, record in goals_created}
    
    print("\nEstablishing prerequisite relationships...")
    for goal_title, prereq_title in PREREQUISITES:
        if goal_title in goal_map and prereq_title in goal_map:
            db.records.attach(
                source=goal_map[goal_title],
                target=goal_map[prereq_title],
                options={"type": "PREREQUISITE", "direction": "out"}
            )
    print(f"  Created {len(PREREQUISITES)} prerequisite relationships")


def establish_blockers(db, goals_created):
    """Create blocker relationships between goals."""
    goal_map = {title: record for title, record in goals_created}
    
    print("\nEstablishing blocker relationships...")
    for goal_title, blocker_title in BLOCKERS:
        if goal_title in goal_map and blocker_title in goal_map:
            db.records.attach(
                source=goal_map[goal_title],
                target=goal_map[blocker_title],
                options={"type": "BLOCKS", "direction": "out"}
            )
    print(f"  Created {len(BLOCKERS)} blocker relationships")


def check_existing_data(db):
    """Check if goals already exist in the database."""
    result = db.records.find({"labels": ["GOAL"], "limit": 1})
    return len(result.data) > 0


def clear_existing_data(db):
    """Clear all existing goal data for a clean seed."""
    print("Clearing existing goal data...")
    db.records.delete({"labels": ["GOAL"], "where": {}})


def main():
    """Main seeding function."""
    global embedding_model
    
    # Get API key from environment
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not set in environment")
        print("Copy .env.example to .env and add your API key")
        return
    
    # Optional custom URL
    url = os.getenv("RUSHDB_URL") or None
    
    # Initialize RushDB client
    print("\nConnecting to RushDB...")
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    
    # Check for existing data
    if check_existing_data(db):
        response = input("\nExisting goal data found. Clear and reseed? (y/N): ")
        if response.lower() == 'y':
            clear_existing_data(db)
        else:
            print("Seeding cancelled. Run main.py to see existing data.")
            return
    
    # Create vector index for goal descriptions
    print("\nCreating vector index for GOAL descriptions...")
    try:
        index = db.ai.indexes.create({
            "label": "GOAL",
            "propertyName": "description",
            "sourceType": "external",
            "dimensions": 384,  # all-MiniLM-L6-v2 produces 384-dim vectors
            "similarityFunction": "cosine",
        })
        print(f"  Vector index created: {index.data.get('__id', 'unknown')}")
    except Exception as e:
        # Index might already exist
        print(f"  Index creation skipped: {e}")
    
    # Load embedding model
    print("\nLoading embedding model for seed data...")
    embedding_model = get_embedding_model()
    
    # Create goal hierarchy
    print("\nCreating goal hierarchy...")
    goals_created = create_goal_hierarchy(db, GOALS_DATA)
    print(f"\nTotal goals created: {len(goals_created)}")
    
    # Establish relationships
    establish_prerequisites(db, goals_created)
    establish_blockers(db, goals_created)
    
    print("\n✓ Seeding complete!")
    print(f"  - {len(goals_created)} goals")
    print(f"  - {len(PREREQUISITES)} prerequisite relationships")
    print(f"  - {len(BLOCKERS)} blocker relationships")
    print(f"  - Vector embeddings for all goal descriptions")


if __name__ == "__main__":
    main()
