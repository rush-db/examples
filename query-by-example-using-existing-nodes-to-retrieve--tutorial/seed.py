"""
Seed script for QBE Tutorial

Creates sample user sessions, help articles, and billing documents
for demonstrating Query-by-Example patterns in RushDB.

This script is idempotent — safe to run multiple times.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()
API_TOKEN = os.getenv("RUSHDB_API_TOKEN")

if not API_TOKEN:
    raise ValueError("RUSHDB_API_TOKEN not found in environment")

db = RushDB(API_TOKEN)

# Sample data for seeding
USERS = [
    {"userId": "user_001", "name": "Sarah Chen", "plan": "pro"},
    {"userId": "user_002", "name": "Marcus Johnson", "plan": "free"},
    {"userId": "user_003", "name": "Elena Rodriguez", "plan": "enterprise"},
    {"userId": "user_004", "name": "Alex Thompson", "plan": "pro"},
]

PAGES = [
    "dashboard",
    "settings",
    "billing",
    "reports",
    "profile",
    "products",
    "checkout",
    "support",
]

TRIGGERS = [
    "page_view",
    "button_click",
    "form_submit",
    "search_query",
    "viewing_product",
    "checkout_started",
    "download_pdf",
]

ARTICLES = [
    {
        "slug": "getting-started",
        "title": "Getting Started with RushDB",
        "body": "Welcome to RushDB! This guide will help you set up your first project, create records, and understand the basic concepts of our memory layer architecture.",
        "tags": ["onboarding", "basics"],
    },
    {
        "slug": "account-security",
        "title": "Account Security Best Practices",
        "body": "Protect your RushDB account by enabling two-factor authentication, using strong passwords, and regularly reviewing your API keys and access logs.",
        "tags": ["security", "account"],
    },
    {
        "slug": "api-authentication",
        "title": "API Authentication Guide",
        "body": "Learn how to authenticate your API requests using tokens, manage API key permissions, and implement secure request signing for production applications.",
        "tags": ["api", "authentication", "security"],
    },
    {
        "slug": "two-factor-auth",
        "title": "Setting Up Two-Factor Authentication",
        "body": "Two-factor authentication adds an extra layer of security. Configure 2FA using authenticator apps or SMS verification to protect your account from unauthorized access.",
        "tags": ["2fa", "security", "account"],
    },
    {
        "slug": "password-management",
        "title": "Managing Your Password",
        "body": "Create strong, unique passwords for your RushDB account. Use a password manager, enable recovery options, and never share your credentials with others.",
        "tags": ["password", "security", "account"],
    },
    {
        "slug": "session-management",
        "title": "Session Management",
        "body": "Understand how RushDB handles user sessions, including session creation, expiration policies, and how to implement secure session handling in your applications.",
        "tags": ["sessions", "security"],
    },
    {
        "slug": "graphql-queries",
        "title": "Writing GraphQL Queries",
        "body": "Master GraphQL queries in RushDB to efficiently fetch related records, filter results, and optimize your data retrieval patterns for better performance.",
        "tags": ["graphql", "queries", "advanced"],
    },
    {
        "slug": "data-modeling",
        "title": "Data Modeling Patterns",
        "body": "Design effective data models for RushDB. Learn about record hierarchies, relationship patterns, and how to structure your data for optimal query performance.",
        "tags": ["data-modeling", "design", "basics"],
    },
    {
        "slug": "billing-overview",
        "title": "Understanding Your Bill",
        "body": "This article explains the different line items on your RushDB bill, including Knowledge Unit usage, overage charges, and how to monitor your consumption.",
        "tags": ["billing", "account"],
    },
    {
        "slug": "payment-methods",
        "title": "Payment Methods",
        "body": "Add and manage payment methods for your RushDB subscription. We support credit cards, bank transfers, and enterprise invoicing options.",
        "tags": ["billing", "payments"],
    },
    {
        "slug": "pricing-plans",
        "title": "Pricing Plans Comparison",
        "body": "Compare RushDB pricing tiers including Free, Pro, Scale, and Enterprise. Understand KU limits, feature availability, and upgrade options.",
        "tags": ["billing", "pricing"],
    },
    {
        "slug": "invoice-history",
        "title": "Accessing Invoice History",
        "body": "View and download your past invoices from RushDB. Learn how to access billing history, export for accounting, and set up invoice delivery.",
        "tags": ["billing", "invoices"],
    },
    {
        "slug": "team-collaboration",
        "title": "Team Collaboration Features",
        "body": "Work together with your team on RushDB projects. Invite members, assign roles, and manage permissions for collaborative development workflows.",
        "tags": ["teamwork", "collaboration"],
    },
    {
        "slug": "webhooks",
        "title": "Configuring Webhooks",
        "body": "Set up webhooks to receive real-time notifications from RushDB. Configure endpoints, handle events, and implement automated workflows based on data changes.",
        "tags": ["webhooks", "automation", "advanced"],
    },
    {
        "slug": "rate-limits",
        "title": "Understanding Rate Limits",
        "body": "Learn about RushDB API rate limits, how they apply to different endpoints, and strategies for optimizing your API usage to avoid throttling.",
        "tags": ["api", "performance", "advanced"],
    },
]


def seed_data():
    """Seed the database with sample data if not already present."""
    print("=" * 80)
    print("Seeding Database for QBE Tutorial")
    print("=" * 80)

    # Check if data already exists
    existing_sessions = db.records.find({"labels": ["SESSION"], "limit": 1})
    if existing_sessions:
        print("\n[INFO] Database already contains data. Skipping seed.")
        print("[INFO] To re-seed, delete existing records first.")
        return False

    print("\n[1/4] Creating users...")
    user_records = []
    for user in USERS:
        record = db.records.create(label="USER", data=user)
        user_records.append(record)
        print(f"  - Created user: {user['name']} ({user['userId']})")

    print("\n[2/4] Creating user sessions...")
    session_count = 0
    for i, user in enumerate(user_records):
        # Create 3-4 sessions per user
        num_sessions = random.randint(3, 4)
        for j in range(num_sessions):
            session_data = {
                "sessionId": f"s_{user.data['userId']}_page_{j}",
                "userId": user.data["userId"],
                "page": random.choice(PAGES),
                "trigger": random.choice(TRIGGERS),
                "duration": random.randint(30, 300),
                "events": random.randint(2, 15),
            }
            session = db.records.create(label="SESSION", data=session_data)
            
            # Attach session to user
            db.records.attach(
                source=session,
                target=user,
                options={"type": "BELONGS_TO", "direction": "out"}
            )
            session_count += 1
            
            if session_count % 100 == 0:
                print(f"  - Created {session_count} sessions...")
        
        print(f"  - Created {num_sessions} sessions for {user.data['name']}")

    print(f"\n[3/4] Creating help articles...")
    for i, article in enumerate(ARTICLES):
        record = db.records.create(label="ARTICLE", data=article)
        print(f"  - Created article: {article['title']}")

    print("\n[4/4] Creating billing documents...")
    billing_docs = [
        {"slug": "billing_invoice", "title": "Invoice #INV-2024-001", "body": "Invoice for January 2024 subscription. Pro plan at $24/mo."},
        {"slug": "billing_summary", "title": "Billing Summary Q1 2024", "body": "Quarterly summary of all RushDB charges including base subscription and overage usage."},
    ]
    for doc in billing_docs:
        record = db.records.create(label="BILLING", data=doc)
        print(f"  - Created billing doc: {doc['title']}")

    print("\n" + "=" * 80)
    print("Seeding Complete!")
    print(f"  - {len(user_records)} users")
    print(f"  - {session_count} sessions")
    print(f"  - {len(ARTICLES)} articles")
    print(f"  - {len(billing_docs)} billing documents")
    print("=" * 80)

    return True


if __name__ == "__main__":
    seed_data()
