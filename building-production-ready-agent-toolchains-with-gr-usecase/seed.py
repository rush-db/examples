#!/usr/bin/env python3
"""
Seed script: Populates the support tool knowledge base with vector embeddings.

This creates SUPPORT_TOOL records with descriptions that will be embedded
and indexed for semantic search. Run this once before main.py.

The script is idempotent — running it twice won't create duplicates.
It checks for existing tools before creating new ones.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

from rushdb import RushDB

# Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions, fast, good quality
INDEX_LABEL = "SUPPORT_TOOL"
INDEX_PROPERTY = "description"

# Support tools for the knowledge base
SUPPORT_TOOLS = [
    {
        "name": "password_reset",
        "description": "Guides user through password reset flow. Handles expired tokens, invalid email formats, and account verification steps. Creates temporary bypass codes for verified users.",
        "category": "authentication",
        "priority": "high"
    },
    {
        "name": "account_lockout_unlock",
        "description": "Unlocks user accounts locked due to suspicious activity or too many failed login attempts. Verifies user identity via secondary email or phone before resetting lock status.",
        "category": "authentication",
        "priority": "high"
    },
    {
        "name": "email_verification_issues",
        "description": "Resolves issues with email verification links not being received, links expiring, or email going to spam folder. Resends verification emails and checks email service status.",
        "category": "authentication",
        "priority": "medium"
    },
    {
        "name": "two_factor_auth_troubleshoot",
        "description": "Helps users with 2FA setup problems including authenticator app sync issues, backup codes not working, and device time zone mismatches affecting TOTP codes.",
        "category": "authentication",
        "priority": "medium"
    },
    {
        "name": "subscription_billing_cycle",
        "description": "Explains billing cycles, upcoming charges, and renewal dates. Provides invoices and payment receipts. Clarifies proration calculations for plan changes mid-cycle.",
        "category": "billing",
        "priority": "medium"
    },
    {
        "name": "payment_method_update",
        "description": "Assists users in updating credit cards, bank accounts, or other payment methods. Handles failed payment updates and validates new payment information before saving.",
        "category": "billing",
        "priority": "high"
    },
    {
        "name": "refund_request_processing",
        "description": "Processes refund requests for recent purchases. Checks refund eligibility window, verifies payment method, and creates refund tickets for finance team processing.",
        "category": "billing",
        "priority": "medium"
    },
    {
        "name": "invoice_retrieval",
        "description": "Locates and resends invoices for past transactions. Generates duplicate invoices for expense reporting. Handles international invoice format requests.",
        "category": "billing",
        "priority": "low"
    },
    {
        "name": "data_export_request",
        "description": "Processes GDPR and CCPA data export requests. Generates comprehensive data packages including user data, activity logs, and stored content within the legally required timeframe.",
        "category": "compliance",
        "priority": "high"
    },
    {
        "name": "account_deletion",
        "description": "Handles account deletion requests including data retention compliance. Provides waiting period information and confirms deletion completion. Reverses deletion within grace period.",
        "category": "compliance",
        "priority": "medium"
    },
    {
        "name": "data_privacy_settings",
        "description": "Helps users configure data sharing preferences, third-party app permissions, and marketing communication settings. Explains how data is used for personalization.",
        "category": "compliance",
        "priority": "low"
    },
    {
        "name": "notification_preferences",
        "description": "Updates email, SMS, and push notification preferences. Handles notification frequency settings, quiet hours configuration, and channel-specific mute options.",
        "category": "preferences",
        "priority": "low"
    },
    {
        "name": "profile_information_update",
        "description": "Assists with updating display names, profile photos, bio text, and contact information. Validates email changes and handles username availability checks.",
        "category": "preferences",
        "priority": "low"
    },
    {
        "name": "connected_apps_management",
        "description": "Reviews and revokes third-party app connections. Explains what data each connected app can access. Helps users understand OAuth scope implications.",
        "category": "preferences",
        "priority": "low"
    },
    {
        "name": "api_key_management",
        "description": "Creates, rotates, and revokes API keys. Sets permissions and rate limits on API keys. Explains API key usage patterns and helps debug authentication errors.",
        "category": "developer",
        "priority": "high"
    },
    {
        "name": "webhook_configuration",
        "description": "Helps configure webhooks for event notifications. Tests webhook deliveries, verifies endpoint signatures, and troubleshoots failed delivery issues.",
        "category": "developer",
        "priority": "medium"
    },
    {
        "name": "rate_limit_exceeded",
        "description": "Explains API rate limiting, quota usage, and request throttling. Identifies which endpoints are being throttled and provides guidance on implementing backoff strategies.",
        "category": "developer",
        "priority": "medium"
    },
    {
        "name": "feature_flags_debugging",
        "description": "Helps debug why feature flags aren't working for a specific user. Checks user segments, overrides, and rollout percentages. Explains flag evaluation logic.",
        "category": "developer",
        "priority": "low"
    },
    {
        "name": "session_token_issues",
        "description": "Resolves JWT token validation failures, session expiration problems, and cross-origin request issues. Explains token refresh flow and handles token rotation.",
        "category": "authentication",
        "priority": "high"
    },
    {
        "name": "account_merge_request",
        "description": "Processes requests to merge duplicate accounts. Verifies ownership of both accounts, explains what data will be combined, and handles conflicting information resolution.",
        "category": "account",
        "priority": "medium"
    }
]


def check_existing_tools(db: RushDB) -> set:
    """Check which tools already exist in the database."""
    existing = db.records.find({"labels": [INDEX_LABEL]})
    return {record.data.get("name") for record in existing}


def create_vector_index(db: RushDB) -> str:
    """Create the vector index for support tool descriptions."""
    print("\n📊 Creating vector index for support tools...")
    
    # Check if index already exists
    try:
        existing_indexes = db.ai.indexes.find()
        for idx in existing_indexes:
            if idx.get("label") == INDEX_LABEL and idx.get("propertyName") == INDEX_PROPERTY:
                print(f"  ✓ Vector index already exists (ID: {idx.get('__id')})")
                return idx.get("__id")
    except Exception:
        pass
    
    # Create new index
    index = db.ai.indexes.create({
        "label": INDEX_LABEL,
        "propertyName": INDEX_PROPERTY,
        "sourceType": "external",  # We supply pre-computed vectors
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    index_id = index.data.get("__id")
    print(f"  ✓ Created vector index (ID: {index_id})")
    return index_id


def generate_embeddings() -> dict:
    """Generate embeddings for all tool descriptions using sentence-transformers."""
    print("\n🧠 Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    embeddings = {}
    print(f"  Embedding {len(SUPPORT_TOOLS)} tool descriptions...")
    
    for i, tool in enumerate(SUPPORT_TOOLS):
        desc = tool["description"]
        vector = model.encode(desc).tolist()
        embeddings[tool["name"]] = vector
        
        if (i + 1) % 5 == 0:
            print(f"    Processed {i + 1}/{len(SUPPORT_TOOLS)} tools...")
    
    print(f"  ✓ Generated {len(embeddings)} embeddings (384 dimensions each)")
    return embeddings


def upsert_tools_with_vectors(db: RushDB, embeddings: dict) -> list:
    """Upsert support tools with their vector embeddings."""
    print("\n📝 Upserting support tools with vector embeddings...")
    
    created = []
    for i, tool in enumerate(SUPPORT_TOOLS):
        name = tool["name"]
        vector = embeddings[name]
        
        # Upsert by name (idempotent)
        record = db.records.upsert(
            label=INDEX_LABEL,
            data=tool,
            options={"mergeBy": ["name"]},
            vectors=[{"propertyName": INDEX_PROPERTY, "vector": vector}]
        )
        created.append(record)
        
        if (i + 1) % 5 == 0:
            print(f"    Upserted {i + 1}/{len(SUPPORT_TOOLS)} tools...")
    
    print(f"  ✓ Upserted {len(created)} support tools")
    return created


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RushDB Support Tool Knowledge Base Seeder")
    print("=" * 60)
    
    # Initialize RushDB client
    api_token = os.getenv("RUSHDb_API_TOKEN")
    if not api_token:
        print("\n❌ Error: RUSHDb_API_TOKEN not found in .env")
        print("   Copy .env.example to .env and add your API token.")
        sys.exit(1)
    
    print(f"\n🔗 Connecting to RushDB...")
    db = RushDB(api_token)
    print("  ✓ Connected")
    
    # Check for existing tools
    existing = check_existing_tools(db)
    print(f"\n📋 Found {len(existing)} existing tools in database")
    
    # Filter out already existing tools for re-seeding check
    new_tools = [t for t in SUPPORT_TOOLS if t["name"] not in existing]
    
    if len(new_tools) == 0:
        print("\n✓ All tools already exist. Creating vector index only...")
    else:
        print(f"\n🔄 Seeding {len(new_tools)} new tools...")
    
    start_time = time.time()
    
    # Step 1: Create vector index
    index_id = create_vector_index(db)
    
    # Step 2: Generate embeddings
    embeddings = generate_embeddings()
    
    # Step 3: Upsert tools with vectors
    tools = upsert_tools_with_vectors(db, embeddings)
    
    elapsed = time.time() - start_time
    
    # Verify the index
    print("\n📈 Verifying vector index...")
    try:
        stats = db.ai.indexes.stats(index_id)
        print(f"  ✓ Index stats: {stats.data.get('indexedRecords', 0)} records indexed")
    except Exception as e:
        print(f"  ⚠ Could not fetch index stats: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Seeding complete in {elapsed:.2f}s")
    print(f"   • {len(tools)} support tools indexed")
    print(f"   • Vector dimensions: 384")
    print(f"   • Similarity metric: cosine")
    print("=" * 60)
    print("\n🚀 Run 'python main.py' to execute the agent demo")


if __name__ == "__main__":
    main()
