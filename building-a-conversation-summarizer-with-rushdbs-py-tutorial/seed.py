"""
Seed script for the Conversation Summarizer tutorial.

Generates sample conversation data and stores it in RushDB.
Run this once before main.py if the database is empty or you want fresh data.
"""

import os
import random
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_token = os.getenv("RUSHDBSDK_API_TOKEN")
if not api_token:
    raise ValueError(
        "RUSHDBSDK_API_TOKEN not found. "
        "Copy .env.example to .env and add your API token."
    )

db = RushDB(api_token)

# Sample data
PARTICIPANTS = [
    {"name": "Alice Chen", "email": "alice@example.com", "role": "Engineering Lead"},
    {"name": "Bob Martinez", "email": "bob@example.com", "role": "Backend Developer"},
    {"name": "Carol Johnson", "email": "carol@example.com", "role": "Frontend Developer"},
    {"name": "David Kim", "email": "david@example.com", "role": "DevOps Engineer"},
    {"name": "Eva Patel", "email": "eva@example.com", "role": "Product Manager"},
]

CONVERSATIONS = [
    {
        "title": "Project Alpha Kickoff",
        "topic": "Technical planning",
        "messages": [
            {"author": "eva@example.com", "content": "Team, let's kick off Project Alpha. We need to migrate our monolith to microservices over the next quarter. Any initial concerns?"},
            {"author": "alice@example.com", "content": "Main concern is the database migration. We've been running PostgreSQL for 5 years and the schema is complex."},
            {"author": "bob@example.com", "content": "I suggest a strangler fig pattern. We can gradually extract services while keeping the core app running."},
            {"author": "david@example.com", "content": "For deployment, we should use Kubernetes. I'll set up the cluster and create deployment templates."},
            {"author": "alice@example.com", "content": "Good idea. Bob, can you draft a migration timeline? Let's aim for 2-week sprints per service."},
            {"author": "bob@example.com", "content": "Will do. I'll also need Carol's help with the frontend API contracts since we're changing how the UI calls services."},
        ]
    },
    {
        "title": "Q4 Planning Discussion",
        "topic": "Product roadmap",
        "messages": [
            {"author": "eva@example.com", "content": "Q4 priorities: mobile app v2, API rate limiting, and onboarding flow redesign. Thoughts?"},
            {"author": "alice@example.com", "content": "Mobile v2 is critical. Current app has performance issues on Android. Can we allocate more QA resources?"},
            {"author": "carol@example.com", "content": "I can lead the onboarding redesign. We have user research data showing drop-off at step 3."},
            {"author": "bob@example.com", "content": "For rate limiting, I recommend a token bucket algorithm. Redis will handle the state well."},
        ]
    },
    {
        "title": "Frontend Architecture Review",
        "topic": "Technical review",
        "messages": [
            {"author": "carol@example.com", "content": "I'm proposing we migrate to Next.js 14 with App Router. The Server Components will improve performance significantly."},
            {"author": "alice@example.com", "content": "What about our existing component library? The migration effort could be substantial."},
            {"author": "carol@example.com", "content": "We can use shadcn/ui as a base. It's headless and integrates well with Next.js. Main work is in testing."},
            {"author": "david@example.com", "content": "I'll prepare a staging environment for the pilot. Can you identify 2-3 pages to start with?"},
            {"author": "carol@example.com", "content": "Dashboard, settings, and the main feed are good candidates. They cover most use cases."},
        ]
    },
    {
        "title": "Database Performance Issues",
        "topic": "Bug investigation",
        "messages": [
            {"author": "alice@example.com", "content": "Production DB is showing 3-second query times on the reports table. 2M rows and no indexes on date ranges."},
            {"author": "bob@example.com", "content": "Adding indexes now. Also noticing missing composite index on (user_id, created_at) which we query often."},
            {"author": "alice@example.com", "content": "Good catch. I think we should also implement query result caching for the dashboard."},
            {"author": "david@example.com", "content": "I'll scale up the RDS instance temporarily while we optimize. P0 incident until resolved."},
            {"author": "bob@example.com", "content": "Indexes created. Monitoring query performance now. Initial improvement looks promising."},
        ]
    },
    {
        "title": "Hiring Technical Discussion",
        "topic": "HR/Team",
        "messages": [
            {"author": "eva@example.com", "content": "We have 2 open senior engineering roles. Engineering lead position is critical for Q1 delivery."},
            {"author": "alice@example.com", "content": "I can do initial technical screens. For system design, maybe rotate between Bob and me?"},
            {"author": "eva@example.com", "content": "Sounds good. Let's also consider take-home projects vs live coding. Candidates have preferred live coding."},
        ]
    },
    {
        "title": "CI/CD Pipeline Upgrade",
        "topic": "DevOps",
        "messages": [
            {"author": "david@example.com", "content": "GitHub Actions is getting slow. 20-minute builds are killing productivity. Proposing we optimize with caching."},
            {"author": "bob@example.com", "content": "Cache node_modules and Docker layers. Also, we can parallelize independent test suites."},
            {"author": "carol@example.com", "content": "Frontend tests run in 8 minutes. If we split by component, we can cut that in half easily."},
        ]
    },
    {
        "title": "Lunch Plans",
        "topic": "Social",
        "messages": [
            {"author": "carol@example.com", "content": "Anyone up for Thai food today? There's a new place around the corner."},
            {"author": "bob@example.com", "content": "Count me in! What time?"},
        ]
    },
    {
        "title": "Security Review Findings",
        "topic": "Security",
        "messages": [
            {"author": "alice@example.com", "content": "The security audit found several issues: SQL injection in legacy API, missing rate limiting on auth endpoints."},
            {"author": "bob@example.com", "content": "The SQL injection is in the reporting module we're deprecating. Can we just remove access to it temporarily?"},
            {"author": "alice@example.com", "content": "Good idea. For the rate limiting, David, can you add CloudFlare rules as a stopgap?"},
            {"author": "david@example.com", "content": "On it. Also adding WAF rules for common attack patterns. Full fix needs code changes."},
            {"author": "eva@example.com", "content": "This is blocking our SOC2 certification. Let's prioritize - can we have mitigations in place by Friday?"},
        ]
    },
]


def check_data_exists():
    """Check if conversation data already exists."""
    result = db.records.find({"labels": ["CONVERSATION"], "limit": 1})
    return len(result.data) > 0


def seed_data():
    """Seed the database with sample conversation data."""
    print("Seeding database with conversation data...\n")
    
    # Check for existing data
    if check_data_exists():
        print("Conversation data already exists. Skipping seed (delete existing data first to reseed).")
        print("To reseed, either delete the project data in RushDB dashboard or use db.records.delete_many().")
        return False
    
    # Create participants
    print("Creating participants...")
    participant_map = {}
    for i, p in enumerate(PARTICIPANTS):
        participant = db.records.create(
            label="PARTICIPANT",
            data={
                "name": p["name"],
                "email": p["email"],
                "role": p["role"]
            }
        )
        participant_map[p["email"]] = participant
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} participants...")
    print(f"  Created {len(PARTICIPANTS)} participants")
    
    # Create conversations and messages
    print("\nCreating conversations and messages...")
    base_time = datetime.now() - timedelta(days=7)
    
    for i, conv_data in enumerate(CONVERSATIONS):
        conversation = db.records.create(
            label="CONVERSATION",
            data={
                "title": conv_data["title"],
                "topic": conv_data["topic"],
                "created_at": (base_time + timedelta(hours=i*2)).isoformat()
            }
        )
        
        # Link participants to conversation
        participant_emails = set(msg["author"] for msg in conv_data["messages"])
        for email in participant_emails:
            if email in participant_map:
                db.records.attach(
                    source=participant_map[email],
                    target=conversation,
                    options={"type": "PARTICIPANT_IN"}
                )
        
        # Create messages with embeddings
        for j, msg in enumerate(conv_data["messages"]):
            message = db.records.create(
                label="MESSAGE",
                data={
                    "content": msg["content"],
                    "author_email": msg["author"],
                    "timestamp": (base_time + timedelta(hours=i*2, minutes=j*10)).isoformat()
                }
            )
            
            # Link message to conversation
            db.records.attach(
                source=message,
                target=conversation,
                options={"type": "CONTAINS"}
            )
        
        print(f"  Created conversation '{conv_data['title']}' with {len(conv_data['messages'])} messages")
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} conversations...")
    
    print("\nSeeding complete!")
    return True


if __name__ == "__main__":
    seed_data()
