#!/usr/bin/env python3
"""
Seed script for Customer Support Bot tutorial.

Generates mock data in RushDB:
- Customers (10)
- Support Agents (5)
- Support Tickets (20)
- FAQ Articles (30)

Run this once before main.py. The script is idempotent —
checking for existing data before creating new records.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
db = RushDB(
    token=os.getenv("RUSHDB_API_KEY"),
    url=os.getenv("RUSHDB_URL")
)

# Mock data constants
FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Edward",
    "Fiona", "George", "Hannah", "Ivan", "Julia"
]

LAST_NAMES = [
    "Anderson", "Brown", "Chen", "Davis", "Evans",
    "Foster", "Garcia", "Harris", "Ivanov", "Jones"
]

PLANS = ["free", "starter", "pro", "enterprise"]

TICKET_SUBJECTS = [
    "Can't login to my account",
    "Billing discrepancy on last invoice",
    "Feature request: Dark mode",
    "API rate limiting issue",
    "Password reset not working",
    "Data export taking too long",
    "Dashboard loading slowly",
    "Integration with Slack broken",
    "Missing emails in notification",
    "Cannot update payment method",
    "SSO configuration help needed",
    "Account suspension inquiry",
    "Webhook events not firing",
    "Bulk import failing silently",
    "Mobile app crashing on launch",
    "Search results not accurate",
    "PDF export formatting issues",
    "Two-factor auth codes not arriving",
    "Team member invitation stuck",
    "GDPR data request"
]

TICKET_STATUSES = ["open", "pending", "resolved", "closed"]

TICKET_PRIORITIES = ["low", "medium", "high", "urgent"]

FAQ_TOPICS = [
    ("Getting Started Guide", [
        "Welcome to our platform! This guide will help you get up and running quickly.",
        "Setting up your first project is easy. Follow these steps to configure your workspace.",
        "Inviting team members to your workspace is simple. Learn how to manage permissions."
    ]),
    ("Account Management", [
        "Your profile settings allow you to customize your experience.",
        "To change your password, navigate to settings and click 'Security'.",
        "Two-factor authentication adds an extra layer of security to your account."
    ]),
    ("Billing and Payments", [
        "You can update your payment method in the billing section of settings.",
        "Invoice history is available in the billing dashboard.",
        "To cancel your subscription, contact our support team."
    ]),
    ("Troubleshooting Login Issues", [
        "If you can't log in, try clearing your browser cache and cookies.",
        "Password reset emails can take up to 5 minutes to arrive.",
        "If SSO isn't working, check with your IT administrator for configuration details."
    ]),
    ("API Documentation", [
        "Our REST API allows programmatic access to all platform features.",
        "Rate limits apply based on your subscription plan.",
        "Webhooks can notify your systems of events in real-time."
    ]),
    ("Data Management", [
        "You can export your data in CSV or JSON format.",
        "Data retention policies determine how long records are kept.",
        "GDPR requests can be submitted through our privacy portal."
    ]),
    ("Integration Setup", [
        "We integrate with popular tools like Slack, Jira, and GitHub.",
        "OAuth integration requires creating an app in the developer settings.",
        "Zapier allows connecting to hundreds of other applications."
    ]),
    ("Security Best Practices", [
        "Enable two-factor authentication for enhanced account security.",
        "Use strong, unique passwords for each service.",
        "Review active sessions regularly and revoke unused access."
    ]),
    ("Performance Optimization", [
        "Caching strategies can significantly improve response times.",
        "Database indexing improves query performance on large datasets.",
        "Monitor your API usage to identify potential bottlenecks."
    ]),
    ("Mobile App Guide", [
        "Our mobile app is available for iOS and Android.",
        "Offline mode allows you to work without an internet connection.",
        "Push notifications can be customized in app settings."
    ])
]

PRODUCTS = [
    "Basic Plan",
    "Pro Plan",
    "Enterprise Suite",
    "API Access",
    "Mobile App",
    "Analytics Dashboard"
]

AGENT_NAMES = [
    "Sarah Mitchell",
    "Michael Chen",
    "Emily Rodriguez",
    "David Kim",
    "Jessica Thompson"
]


def check_already_seeded():
    """Check if data already exists to avoid duplicates."""
    existing = db.records.find({"labels": ["CUSTOMER"], "limit": 1})
    return existing.total > 0


def create_customers():
    """Create 10 customer records."""
    print("Creating customers...")
    customers = []
    
    for i in range(10):
        first = FIRST_NAMES[i]
        last = LAST_NAMES[i]
        email = f"{first.lower()}.{last.lower()}@example.com"
        
        customer = db.records.create(
            label="CUSTOMER",
            data={
                "email": email,
                "name": f"{first} {last}",
                "plan": random.choice(PLANS),
                "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
            }
        )
        customers.append(customer)
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1} customers...")
    
    print(f"  Created {len(customers)} customers total")
    return customers


def create_agents():
    """Create 5 support agent records."""
    print("Creating agents...")
    agents = []
    
    for i, name in enumerate(AGENT_NAMES):
        agent = db.records.create(
            label="AGENT",
            data={
                "name": name,
                "email": name.lower().replace(" ", ".") + "@support.com",
                "department": random.choice(["tier1", "tier2", "escalations"]),
                "active": True
            }
        )
        agents.append(agent)
    
    print(f"  Created {len(agents)} agents total")
    return agents


def create_tickets(customers, agents):
    """Create 20 support tickets with relationships."""
    print("Creating tickets...")
    tickets = []
    
    for i in range(20):
        customer = random.choice(customers)
        agent = random.choice(agents)
        created_at = datetime.now() - timedelta(days=random.randint(0, 60))
        
        # Create the ticket
        ticket = db.records.create(
            label="TICKET",
            data={
                "subject": TICKET_SUBJECTS[i],
                "status": random.choice(TICKET_STATUSES),
                "priority": random.choice(TICKET_PRIORITIES),
                "created_at": created_at.isoformat(),
                "ticket_id": f"TICKET-{i + 1:03d}"
            }
        )
        tickets.append(ticket)
        
        # Create relationships within a transaction
        with db.transactions.begin() as tx:
            # Link customer to ticket
            db.records.attach(
                source=customer,
                target=ticket,
                options={"type": "OPENED", "direction": "out"},
                transaction=tx
            )
            
            # Link agent to ticket
            db.records.attach(
                source=agent,
                target=ticket,
                options={"type": "ASSIGNED_TO", "direction": "out"},
                transaction=tx
            )
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1} tickets...")
    
    print(f"  Created {len(tickets)} tickets total")
    return tickets


def create_faq_articles():
    """Create 30 FAQ articles for semantic search."""
    print("Creating FAQ articles...")
    articles = []
    
    article_num = 1
    for topic, contents in FAQ_TOPICS:
        for content in contents:
            article = db.records.create(
                label="FAQ",
                data={
                    "title": f"{topic} - Article {article_num}",
                    "topic": topic,
                    "content": content,
                    "helpful_count": random.randint(10, 500),
                    "published_at": (datetime.now() - timedelta(days=random.randint(7, 180))).isoformat()
                }
            )
            articles.append(article)
            article_num += 1
            
            if article_num % 10 == 0:
                print(f"  Created {article_num} articles...")
    
    print(f"  Created {len(articles)} FAQ articles total")
    return articles


def create_products(tickets):
    """Create product records and link some tickets to them."""
    print("Creating products and linking to tickets...")
    products = []
    
    for product_name in PRODUCTS:
        product = db.records.create(
            label="PRODUCT",
            data={
                "name": product_name,
                "active": True
            }
        )
        products.append(product)
    
    # Link ~30% of tickets to products
    for ticket in tickets[:6]:
        product = random.choice(products)
        db.records.attach(
            source=ticket,
            target=product,
            options={"type": "RELATED_TO", "direction": "out"}
        )
    
    print(f"  Created {len(products)} products and linked 6 tickets")
    return products


def main():
    print("\n=== Seeding Customer Support Bot Data ===\n")
    
    # Check if already seeded
    if check_already_seeded():
        print("Data already exists in the database.")
        print("Skipping seed to avoid duplicates.")
        print("To reseed, delete the records from your RushDB dashboard.\n")
        return
    
    # Create all data
    customers = create_customers()
    agents = create_agents()
    tickets = create_tickets(customers, agents)
    articles = create_faq_articles()
    products = create_products(tickets)
    
    print("\n=== Seeding Complete ===")
    print(f"  Customers: {len(customers)}")
    print(f"  Agents: {len(agents)}")
    print(f"  Tickets: {len(tickets)}")
    print(f"  FAQ Articles: {len(articles)}")
    print(f"  Products: {len(products)}")
    print("\nRun 'python main.py' to see the tutorial in action!\n")


if __name__ == "__main__":
    main()
