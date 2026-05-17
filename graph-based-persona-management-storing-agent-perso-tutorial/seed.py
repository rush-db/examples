#!/usr/bin/env python3
"""
Seed script for Graph-Based Persona Management tutorial.

This script creates sample agent personas with personality vectors
and establishes relationships between them.

Run this once before main.py to populate RushDB with demo data.
Idempotent: safe to run multiple times.
"""

import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

# Personality trait vectors (5-dimensional for simplicity)
# Format: [empathy, assertiveness, technical, creativity, patience]
PERSONAITY_VECTORS = {
    "support_alice": [0.9, 0.2, 0.4, 0.3, 0.95],  # Highly empathetic, patient
    "support_bob": [0.7, 0.5, 0.6, 0.4, 0.8],      # Balanced support
    "sales_carol": [0.6, 0.9, 0.3, 0.7, 0.5],      # Assertive, creative closer
    "assistant_dan": [0.8, 0.1, 0.5, 0.6, 0.9],   # Friendly, creative assistant
    "manager_eve": [0.5, 0.95, 0.8, 0.5, 0.6],     # Technical leader
}

# ─────────────────────────────────────────────────────────────────────────────
# Database Connection
# ─────────────────────────────────────────────────────────────────────────────

db = RushDB(API_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def cleanup_existing_data():
    """Remove previously seeded data for clean re-seeding."""
    labels_to_clean = ["PERSONA", "USER", "TEAM"]
    
    for label in labels_to_clean:
        try:
            db.records.delete_many({"labels": [label], "where": {}})
            print(f"  Cleaned existing {label} records")
        except Exception as e:
            print(f"  Warning cleaning {label}: {e}")


def create_vector_index_if_needed():
    """Create vector index for persona personality vectors."""
    try:
        # Check if index exists
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            if idx.get("label") == "PERSONA" and idx.get("propertyName") == "personality_traits":
                print("  Vector index already exists")
                return
        
        # Create managed index (RushDB handles embedding)
        db.ai.indexes.create({
            "label": "PERSONA",
            "propertyName": "personality_traits",
            "dimensions": 5,  # Our trait vector size
        })
        print("  Created vector index for PERSONA.personality_traits")
    except Exception as e:
        print(f"  Warning creating index: {e}")


def seed_personas():
    """Create agent persona records with personality vectors."""
    print("\n[2] Creating personas with personality vectors...")
    
    personas_data = [
        {
            "name": "Support-Alice",
            "type": "support",
            "description": "Senior support agent specializing in empathetic customer care",
            "traits": {
                "empathy": 0.9,
                "assertiveness": 0.2,
                "technical": 0.4,
                "creativity": 0.3,
                "patience": 0.95,
            },
            "personality_traits": "High empathy, extremely patient, gentle approach",
        },
        {
            "name": "Support-Bob",
            "type": "support",
            "description": "Technical support agent with balanced communication style",
            "traits": {
                "empathy": 0.7,
                "assertiveness": 0.5,
                "technical": 0.6,
                "creativity": 0.4,
                "patience": 0.8,
            },
            "personality_traits": "Balanced support, technical proficiency, friendly",
        },
        {
            "name": "Sales-Carol",
            "type": "sales",
            "description": "High-energy sales agent with creative closing techniques",
            "traits": {
                "empathy": 0.6,
                "assertiveness": 0.9,
                "technical": 0.3,
                "creativity": 0.7,
                "patience": 0.5,
            },
            "personality_traits": "Assertive closer, creative solutions, energetic",
        },
        {
            "name": "Assistant-Dan",
            "type": "assistant",
            "description": "Helpful assistant combining friendliness with creative problem-solving",
            "traits": {
                "empathy": 0.8,
                "assertiveness": 0.1,
                "technical": 0.5,
                "creativity": 0.6,
                "patience": 0.9,
            },
            "personality_traits": "Friendly helper, creative, very patient",
        },
        {
            "name": "Manager-Eve",
            "type": "manager",
            "description": "Team manager with technical expertise and leadership skills",
            "traits": {
                "empathy": 0.5,
                "assertiveness": 0.95,
                "technical": 0.8,
                "creativity": 0.5,
                "patience": 0.6,
            },
            "personality_traits": "Technical leader, decisive, strategic thinker",
        },
    ]
    
    personas = {}
    for i, persona_data in enumerate(personas_data):
        key = persona_data["name"].lower().replace("-", "_")
        vector = PERSONAITY_VECTORS.get(key, [0.5] * 5)
        
        record = db.records.create(
            label="PERSONA",
            data=persona_data,
            vectors=[{"propertyName": "personality_traits", "vector": vector}],
        )
        personas[key] = record
        print(f"  Created {persona_data['name']} with traits {vector}")
    
    return personas


def seed_users():
    """Create sample user records."""
    print("\n[3] Creating user records...")
    
    users_data = [
        {"email": "alice@example.com", "name": "Alice Smith", "tier": "premium"},
        {"email": "bob@example.com", "name": "Bob Jones", "tier": "standard"},
        {"email": "carol@example.com", "name": "Carol White", "tier": "enterprise"},
        {"email": "dave@example.com", "name": "Dave Brown", "tier": "standard"},
    ]
    
    users = {}
    for user_data in users_data:
        record = db.records.create(label="USER", data=user_data)
        users[user_data["email"]] = record
        print(f"  Created user: {user_data['name']} <{user_data['email']}>")
    
    return users


def seed_teams():
    """Create team records."""
    print("\n[4] Creating team records...")
    
    teams_data = [
        {"name": "Customer Success", "department": "support"},
        {"name": "Sales", "department": "sales"},
        {"name": "General Assistance", "department": "assistance"},
    ]
    
    teams = {}
    for team_data in teams_data:
        record = db.records.create(label="TEAM", data=team_data)
        teams[team_data["name"]] = record
        print(f"  Created team: {team_data['name']}")
    
    return teams


def create_relationships(personas, users, teams):
    """Establish relationships between personas, users, and teams."""
    print("\n[5] Creating relationships...")
    
    # ─── Supervisor Hierarchy ───
    # Manager-Eve supervises Support-Bob and Sales-Carol
    manager = personas["manager_eve"]
    support_bob = personas["support_bob"]
    sales_carol = personas["sales_carol"]
    
    db.records.attach(source=manager, target=support_bob, options={"type": "SUPERVISES"})
    print("  Manager-Eve supervises Support-Bob")
    
    db.records.attach(source=manager, target=sales_carol, options={"type": "SUPERVISES"})
    print("  Manager-Eve supervises Sales-Carol")
    
    # ─── Team Membership ───
    # Support team: Support-Alice, Support-Bob
    support_team = teams["Customer Success"]
    db.records.attach(source=support_alice := personas["support_alice"], target=support_team, options={"type": "MEMBER_OF"})
    db.records.attach(source=support_bob, target=support_team, options={"type": "MEMBER_OF"})
    print("  Support-Alice and Support-Bob joined Customer Success team")
    
    # Sales team: Sales-Carol
    sales_team = teams["Sales"]
    db.records.attach(source=sales_carol, target=sales_team, options={"type": "MEMBER_OF"})
    print("  Sales-Carol joined Sales team")
    
    # General assistance: Assistant-Dan
    assistant_team = teams["General Assistance"]
    db.records.attach(source=personas["assistant_dan"], target=assistant_team, options={"type": "MEMBER_OF"})
    print("  Assistant-Dan joined General Assistance team")
    
    # ─── Agent-User Assignments ───
    # Alice -> Support-Alice (premium support)
    db.records.attach(source=support_alice, target=users["alice@example.com"], options={"type": "SERVICES"})
    print("  Support-Alice assigned to alice@example.com")
    
    # Bob -> Support-Bob
    db.records.attach(source=support_bob, target=users["bob@example.com"], options={"type": "SERVICES"})
    print("  Support-Bob assigned to bob@example.com")
    
    # Carol -> Enterprise clients
    db.records.attach(source=sales_carol, target=users["carol@example.com"], options={"type": "SERVICES"})
    print("  Sales-Carol assigned to carol@example.com")
    
    # Dan serves everyone
    for email, user in users.items():
        db.records.attach(source=personas["assistant_dan"], target=user, options={"type": "SERVICES"})
    print("  Assistant-Dan available to all users")
    
    # ─── Escalation Paths ───
    # Support can escalate to Manager
    db.records.attach(source=support_alice, target=manager, options={"type": "ESCALATES_TO"})
    db.records.attach(source=support_bob, target=manager, options={"type": "ESCALATES_TO"})
    print("  Support agents can escalate to Manager-Eve")
    
    print("\n  All relationships created successfully!")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("Persona Management - Seed Script")
    print("=" * 60)
    
    print("\n[1] Cleaning up existing data...")
    cleanup_existing_data()
    
    # Create vector index for personality search
    create_vector_index_if_needed()
    
    # Seed all data
    personas = seed_personas()
    users = seed_users()
    teams = seed_teams()
    create_relationships(personas, users, teams)
    
    print("\n" + "=" * 60)
    print("Seeding complete! Run `python main.py` to see the demo.")
    print("=" * 60)


if __name__ == "__main__":
    main()
