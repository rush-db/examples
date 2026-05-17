"""
Seed Script: Initialize Rate Limiting Data

Creates sample rate limit configurations and initial usage data
for the rate limiting demo.

Run this script once to populate RushDB with demo data.
It is idempotent — safe to run multiple times.
"""

import os
import sys
from datetime import datetime, timedelta
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


def seed_rate_limit_rules(db: RushDB) -> dict:
    """
    Create rate limit rule configurations for different client tiers.
    """
    print("\n[1/3] Seeding rate limit rules...")
    
    rules = [
        {
            "client_id": "client_free",
            "max_requests": 100,
            "window_seconds": 60,
            "tier": "free",
            "description": "Free tier: 100 requests per minute"
        },
        {
            "client_id": "client_premium",
            "max_requests": 1000,
            "window_seconds": 60,
            "tier": "premium",
            "description": "Premium tier: 1000 requests per minute"
        },
        {
            "client_id": "client_enterprise",
            "max_requests": 10000,
            "window_seconds": 60,
            "quota_ku": 100000,
            "ku_used": 0,
            "tier": "enterprise",
            "description": "Enterprise tier: Unlimited with KU budget"
        },
        {
            "client_id": "client_trial",
            "max_requests": 20,
            "window_seconds": 60,
            "tier": "trial",
            "description": "Trial tier: 20 requests per minute for testing"
        }
    ]
    
    created = {}
    for rule in rules:
        # Use upsert to make this idempotent
        record = db.records.upsert(
            label="RATE_LIMIT_RULE",
            data=rule,
            options={"mergeBy": ["client_id"]}
        )
        created[rule["client_id"]] = record.id
        print(f"   ✓ {rule['client_id']}: {rule['max_requests']} req/{rule['window_seconds']}s")
    
    return created


def seed_sample_usage(db: RushDB, rules: dict) -> None:
    """
    Create sample request logs to demonstrate usage tracking.
    """
    print("\n[2/3] Seeding sample request logs...")
    
    # Sample recent requests for demo purposes
    now = datetime.utcnow()
    sample_requests = [
        {
            "client_id": "client_free",
            "endpoint": "/api/v1/records/find",
            "method": "POST",
            "ku_cost": 0.5,
            "timestamp": (now - timedelta(seconds=30)).isoformat(),
            "status": "success"
        },
        {
            "client_id": "client_free",
            "endpoint": "/api/v1/records/create",
            "method": "POST",
            "ku_cost": 5.5,
            "timestamp": (now - timedelta(seconds=25)).isoformat(),
            "status": "success"
        },
        {
            "client_id": "client_premium",
            "endpoint": "/api/v1/ai/search",
            "method": "POST",
            "ku_cost": 5.0,
            "timestamp": (now - timedelta(seconds=10)).isoformat(),
            "status": "success"
        }
    ]
    
    for i, req in enumerate(sample_requests):
        db.records.create(label="REQUEST_LOG", data=req)
        print(f"   ✓ Request {i+1}: {req['client_id']} -> {req['endpoint']}")
    
    print(f"   Created {len(sample_requests)} sample request logs")


def verify_seed(db: RushDB) -> None:
    """
    Verify seed data was created successfully.
    """
    print("\n[3/3] Verifying seed data...")
    
    # Check rate limit rules
    rules = db.records.find({"labels": ["RATE_LIMIT_RULE"]})
    print(f"   Rate limit rules: {rules.total}")
    
    # Check request logs
    logs = db.records.find({"labels": ["REQUEST_LOG"]})
    print(f"   Request logs: {logs.total}")
    
    # Check KU usage records
    usage = db.records.find({"labels": ["KU_USAGE"]})
    print(f"   KU usage records: {usage.total}")


def main():
    print("=" * 60)
    print("RushDB Rate Limiting - Seed Data Script")
    print("=" * 60)
    
    # Initialize RushDB client
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    
    print(f"\nConnected to RushDB")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # Seed data
        rules = seed_rate_limit_rules(db)
        seed_sample_usage(db, rules)
        verify_seed(db)
        
        print("\n" + "=" * 60)
        print("Seed completed successfully!")
        print("=" * 60)
        print("\nYou can now run `python main.py` to test the rate limiter.")
        
    except Exception as e:
        print(f"\nERROR during seeding: {e}")
        raise


if __name__ == "__main__":
    main()
