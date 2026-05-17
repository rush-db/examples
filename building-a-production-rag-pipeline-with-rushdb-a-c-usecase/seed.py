#!/usr/bin/env python3
"""
Seed script for the RAG Pipeline demo.

Loads policies, authors, teams, and relationships into RushDB.
Creates a vector index on Policy.body for semantic search.

Run this once before main.py to populate the database.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

from rushdb import RushDB

# ─── Configuration ────────────────────────────────────────────────────────────

API_KEY = os.getenv("RUSHDB_API_KEY")
RUSHDB_URL = os.getenv("RUSHDB_URL")

if not API_KEY:
    print("❌ Error: RUSHDB_API_KEY not found in environment")
    print("   Copy .env.example to .env and add your API key")
    sys.exit(1)

# ─── Initialize Clients ──────────────────────────────────────────────────────

print("\n🚀 Initializing RushDB connection...")
db = RushDB(API_KEY, url=RUSHDB_URL) if RUSHDB_URL else RushDB(API_KEY)
print(f"   Connected to: {RUSHDB_URL or 'RushDB Cloud'}\n")

# Initialize embedding model (all-MiniLM-L6-v2 - fast, good quality)
print("📦 Loading embedding model (all-MiniLM-L6-v2)...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("   Model loaded\n")

# ─── Load Data ────────────────────────────────────────────────────────────────

data_dir = Path(__file__).parent / "data"

print("📂 Loading seed data...")
with open(data_dir / "policies.json") as f:
    policies_data = json.load(f)
with open(data_dir / "authors.json") as f:
    authors_data = json.load(f)
with open(data_dir / "teams.json") as f:
    teams_data = json.load(f)
with open(data_dir / "relationships.json") as f:
    relationships_data = json.load(f)

print(f"   Loaded {len(policies_data)} policies")
print(f"   Loaded {len(authors_data)} authors")
print(f"   Loaded {len(teams_data)} teams")
print(f"   Loaded {len(relationships_data)} relationships\n")

# ─── Clear Existing Data (Idempotent) ─────────────────────────────────────────

print("🧹 Clearing existing demo data...")
for label in ["POLICY", "AUTHOR", "TEAM"]:
    result = db.records.find({"labels": [label], "limit": 1000})
    if result.data:
        db.records.delete({"labels": [label], "where": {}})
        print(f"   Cleared {len(result.data)} {label} records")

# ─── Check for Existing Vector Index ──────────────────────────────────────────

print("\n📊 Checking vector index status...")
existing_indexes = db.ai.indexes.find()
vector_index_exists = any(
    idx.get('label') == 'POLICY' and idx.get('propertyName') == 'body'
    for idx in existing_indexes.data
)

# ─── Step 1: Create Teams (No vectors needed) ─────────────────────────────────

print("\n📁 Creating Teams...")
teams = {}
for team_data in teams_data:
    team = db.records.create(
        label="TEAM",
        data={
            "name": team_data["name"],
            "description": team_data["description"]
        }
    )
    teams[team_data["id"]] = team
    print(f"   ✅ Created Team: {team_data['name']}")

# ─── Step 2: Create Authors ───────────────────────────────────────────────────

print("\n👤 Creating Authors...")
authors = {}
for author_data in authors_data:
    author = db.records.create(
        label="AUTHOR",
        data={
            "name": author_data["name"],
            "role": author_data["role"],
            "email": author_data["email"]
        }
    )
    authors[author_data["id"]] = author
    print(f"   ✅ Created Author: {author_data['name']} ({author_data['role']})")

# ─── Step 3: Create Policies with Embeddings ──────────────────────────────────

print("\n📄 Creating Policies with vector embeddings...")
print("   (This may take a moment for embedding computation)")

policies = {}
body_texts = [p["body"] for p in policies_data]
embeddings = embedder.encode(body_texts, show_progress_bar=True)

for i, policy_data in enumerate(policies_data):
    policy = db.records.create(
        label="POLICY",
        data={
            "title": policy_data["title"],
            "body": policy_data["body"],
            "tags": policy_data["tags"],
            "policy_id": policy_data["id"]
        },
        vectors=[{
            "propertyName": "body",
            "vector": embeddings[i].tolist()
        }]
    )
    policies[policy_data["id"]] = policy
    print(f"   ✅ Created Policy: {policy_data['title']}")

# ─── Step 4: Create Relationships ──────────────────────────────────────────────

print("\n🔗 Creating relationships...")

# Policy → Author (WRITTEN_BY)
for policy_data in policies_data:
    policy = policies[policy_data["id"]]
    author = authors[policy_data["author_id"]]
    
    db.records.attach(
        source=policy,
        target=author,
        options={"type": "WRITTEN_BY", "direction": "out"}
    )
    print(f"   🔗 {policy_data['title']} → WRITTEN_BY → {author.data['name']}")

# Author → Team (MEMBER_OF)
for author_data in authors_data:
    author = authors[author_data["id"]]
    team = teams[author_data["team_id"]]
    
    db.records.attach(
        source=author,
        target=team,
        options={"type": "MEMBER_OF", "direction": "out"}
    )
    print(f"   🔗 {author.data['name']} → MEMBER_OF → {team.data['name']}")

# Policy → Policy (CROSS_REFERENCES)
for rel in relationships_data:
    from_policy = policies[rel["from"]]
    to_policy = policies[rel["to"]]
    
    db.records.attach(
        source=from_policy,
        target=to_policy,
        options={"type": rel["type"], "direction": "out"}
    )
    print(f"   🔗 {from_policy.data['title']} → {rel['type']} → {to_policy.data['title']}")

# ─── Step 5: Create Vector Index (if not exists) ──────────────────────────────

if not vector_index_exists:
    print("\n🔢 Creating vector index on Policy.body...")
    index = db.ai.indexes.create({
        "label": "POLICY",
        "propertyName": "body",
        "sourceType": "external",
        "dimensions": 384,  # all-MiniLM-L6-v2 outputs 384-dim vectors
        "similarityFunction": "cosine"
    })
    print(f"   ✅ Vector index created: {index.data.get('__id')}")
else:
    print("\n   ℹ️  Vector index already exists, skipping creation")

# ─── Summary ──────────────────────────────────────────────────────────────────

print("\n" + "═" * 60)
print("✅ SEEDING COMPLETE!")
print("═" * 60)
print(f"   • {len(policies)} Policies created")
print(f"   • {len(authors)} Authors created")
print(f"   • {len(teams)} Teams created")
print(f"   • {len(policies_data) + len(authors_data) + len(relationships_data)} Relationships established")
print(f"   • Vector index {'created' if not vector_index_exists else 'verified'} on Policy.body")
print("\n   Run `python main.py` to see the RAG pipeline in action!\n")
