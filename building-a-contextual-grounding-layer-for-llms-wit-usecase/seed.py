#!/usr/bin/env python3
"""
Seed script for the contextual grounding layer example.

Creates a realistic support ticket dataset with:
- Customers (various tiers: free, pro, enterprise)
- Products (different categories and versions)
- Categories (billing, technical, account, feature)
- Tickets (varied status, priority, descriptions)
- Solutions (linked to resolved tickets)
- Relationships (filed_by, relates_to, resolved_with, etc.)

The data is designed to demonstrate graph+RAG retrieval:
- Same issue on different tiers produces different confidence
- Product relationships affect relevance
- Customer history matters for context
"""

import os
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Configuration
TICKETS_COUNT = 50
CUSTOMERS_COUNT = 15
PRODUCTS_COUNT = 8

# Realistic support data
TIERS = ["free", "pro", "enterprise"]

PRODUCTS = [
    {"name": "Starter Workspace", "category": "account", "version": "2.1"},
    {"name": "Pro Dashboard", "category": "billing", "version": "3.0"},
    {"name": "Enterprise Suite", "category": "technical", "version": "4.2"},
    {"name": "API Gateway", "category": "technical", "version": "1.8"},
    {"name": "Analytics Module", "category": "feature", "version": "2.5"},
    {"name": "Team Collaboration", "category": "feature", "version": "3.1"},
    {"name": "Security Center", "category": "technical", "version": "2.0"},
    {"name": "Billing Portal", "category": "billing", "version": "1.5"},
]

CATEGORIES = [
    {"name": "billing", "description": "Payment, invoices, and subscription issues"},
    {"name": "technical", "description": "Bugs, errors, and system performance"},
    {"name": "account", "description": "Access, authentication, and profile management"},
    {"name": "feature", "description": "Feature requests and product feedback"},
]

# Ticket templates with semantic variety
TICKET_TEMPLATES = [
    # Billing issues
    {
        "subject": "Wrong charge on my {tier} account",
        "description": "I was charged ${amount} but my plan is ${tier} which costs ${expected}. Please investigate and refund the difference.",
        "category": "billing",
    },
    {
        "subject": "Unable to update payment method",
        "description": "The payment update form keeps throwing an error when I try to save my new credit card details.",
        "category": "billing",
    },
    {
        "subject": "Invoice showing incorrect amount",
        "description": "My monthly invoice shows charges for features I haven't used. I need an itemized breakdown.",
        "category": "billing",
    },
    {
        "subject": "Billing portal not loading",
        "description": "The billing section of the dashboard shows a blank page. I've tried multiple browsers.",
        "category": "billing",
    },
    {
        "subject": "Subscription cancellation not processed",
        "description": "I cancelled my subscription last week but I'm still being charged. Please stop the recurring billing.",
        "category": "billing",
    },
    # Technical issues
    {
        "subject": "API returning 500 errors intermittently",
        "description": "Our integration is hitting random 500 errors. This is affecting our production workload.",
        "category": "technical",
    },
    {
        "subject": "Dashboard loading very slowly",
        "description": "The main dashboard takes 30+ seconds to load. This started happening after the last update.",
        "category": "technical",
    },
    {
        "subject": "Data export feature broken",
        "description": "When I click export, the file downloads but is corrupted. Tried CSV and JSON formats.",
        "category": "technical",
    },
    {
        "subject": "Webhook deliveries failing",
        "description": "Our webhook endpoint is not receiving events. The logs show successful delivery but nothing arrives.",
        "category": "technical",
    },
    {
        "subject": "Search functionality not working",
        "description": "Searching for any term returns zero results even though the data exists in the system.",
        "category": "technical",
    },
    # Account issues
    {
        "subject": "Cannot reset my password",
        "description": "The password reset email never arrives. Checked spam folder and tried multiple email addresses.",
        "category": "account",
    },
    {
        "subject": "Two-factor authentication locked out",
        "description": "Lost access to my authenticator app and backup codes. Need account recovery assistance.",
        "category": "account",
    },
    {
        "subject": "Team member cannot access shared workspace",
        "description": "I invited a colleague but they can't see the workspace. The invite shows as accepted.",
        "category": "account",
    },
    {
        "subject": "Profile information not saving",
        "description": "Changes to my profile settings are not persisting. I edit and save but the values revert.",
        "category": "account",
    },
    # Feature requests
    {
        "subject": "Request: Dark mode support",
        "description": "Would love to have a dark theme option for the dashboard. Current bright interface is hard on the eyes.",
        "category": "feature",
    },
    {
        "subject": "Bulk import feature needed",
        "description": "Need to import thousands of records. Currently have to do this one by one which is impractical.",
        "category": "feature",
    },
    {
        "subject": "Mobile app for iOS",
        "description": "Is there a mobile app planned? Would be very helpful to manage tickets on the go.",
        "category": "feature",
    },
    {
        "subject": "Custom email templates",
        "description": "Want to personalize notification emails with our company branding. Need template customization.",
        "category": "feature",
    },
]

SOLUTIONS = {
    "billing": [
        {"title": "Prorated charge explanation", "steps": "Explained proration for mid-cycle upgrades. Customer satisfied."},
        {"title": "Payment method updated", "steps": "Cleared browser cache, re-submitted form successfully."},
        {"title": "Invoice corrected", "steps": "Identified duplicate line item. Reissued corrected invoice."},
        {"title": "Portal cache cleared", "steps": "Cleared CDN cache. Portal now loading correctly."},
        {"title": "Cancellation processed", "steps": "Found pending cancellation. Force-processed and confirmed."},
    ],
    "technical": [
        {"title": "API rate limit increased", "steps": "Customer was hitting rate limits. Upgraded to higher tier."},
        {"title": "Performance issue resolved", "steps": "Identified slow query. Added index on frequently filtered field."},
        {"title": "Export encoding fixed", "steps": "Changed encoding from UTF-16 to UTF-8. Re-exported data."},
        {"title": "Webhook endpoint verified", "steps": "Endpoint was returning 200 but body was malformed. Fixed parser."},
        {"title": "Search index rebuilt", "steps": "Elasticsearch index was stale. Triggered full reindex."},
    ],
    "account": [
        {"title": "Password reset email resent", "steps": "Added to whitelist, resent email successfully delivered."},
        {"title": "2FA recovered via backup", "steps": "Verified identity via phone. Reset 2FA to authenticator."},
        {"title": "Workspace permission fixed", "steps": "Role was incorrectly assigned. Reassigned as admin."},
        {"title": "Profile form submission fixed", "steps": "JavaScript error blocking save. Patched frontend."},
    ],
    "feature": [
        {"title": "Dark mode added to roadmap", "steps": "Logged as feature request. Added to Q2 roadmap."},
        {"title": "Bulk import available", "steps": "Directed to CSV import feature in Settings > Import."},
        {"title": "Mobile app in beta", "steps": "Invited customer to iOS beta program."},
        {"title": "Email templates available", "steps": "Undocumented feature in Admin > Branding. Enabled for customer."},
    ],
}

CUSTOMER_NAMES = [
    "Alice Chen", "Bob Martinez", "Carol Johnson", "David Kim", "Emma Wilson",
    "Frank Garcia", "Grace Lee", "Henry Taylor", "Iris Patel", "Jack Brown",
    "Karen White", "Leo Zhang", "Maria Rodriguez", "Nathan Clark", "Olivia Moore"
]


def init_rushdb():
    """Initialize RushDB client."""
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        raise ValueError(
            "RushDB API token not found. "
            "Please set RUSHDB_API_TOKEN in your .env file."
        )
    
    db = RushDB(api_token)
    print(f"Connected to RushDB: {db}")
    return db


def init_embeddings():
    """Initialize sentence transformer for embeddings."""
    print("Loading embedding model (this may take a moment)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Embedding model ready.")
    return model


def create_vector_index(db, label, property_name, dimensions=384):
    """Create vector index if it doesn't exist."""
    try:
        response = db.ai.indexes.find()
        existing = [idx for idx in response.data if idx['label'] == label]
        if existing:
            print(f"  Vector index for {label}.{property_name} already exists")
            return existing[0]['__id']
    except:
        pass
    
    try:
        index = db.ai.indexes.create({
            "label": label,
            "propertyName": property_name,
            "sourceType": "external",
            "dimensions": dimensions,
            "similarityFunction": "cosine"
        })
        print(f"  Created vector index: {label}.{property_name}")
        return index.data["__id"]
    except Exception as e:
        print(f"  Warning: Could not create index: {e}")
        return None


def seed_customers(db):
    """Create customer records."""
    print(f"\nCreating {CUSTOMERS_COUNT} customers...")
    customers = []
    
    with db.transactions.begin() as tx:
        for i, name in enumerate(CUSTOMER_NAMES[:CUSTOMERS_COUNT]):
            tier = random.choice(TIERS)
            account_age_days = random.randint(30, 730)
            created_at = datetime.now() - timedelta(days=account_age_days)
            
            customer = db.records.create(
                label="CUSTOMER",
                data={
                    "name": name,
                    "email": f"{name.lower().replace(' ', '.')}@company.com",
                    "tier": tier,
                    "account_age_days": account_age_days,
                    "created_at": created_at.isoformat(),
                },
                transaction=tx
            )
            customers.append(customer)
            
            if (i + 1) % 5 == 0:
                print(f"  Created {i + 1}/{CUSTOMERS_COUNT} customers")
    
    print(f"  Created {len(customers)} customers total")
    return customers


def seed_products(db):
    """Create product records."""
    print(f"\nCreating {PRODUCTS_COUNT} products...")
    products = []
    
    with db.transactions.begin() as tx:
        for i, product_data in enumerate(PRODUCTS[:PRODUCTS_COUNT]):
            product = db.records.create(
                label="PRODUCT",
                data={
                    "name": product_data["name"],
                    "category": product_data["category"],
                    "version": product_data["version"],
                    "active_users": random.randint(100, 10000),
                },
                transaction=tx
            )
            products.append(product)
    
    print(f"  Created {len(products)} products total")
    return products


def seed_categories(db):
    """Create category records."""
    print(f"\nCreating {len(CATEGORIES)} categories...")
    categories = {}
    
    with db.transactions.begin() as tx:
        for cat_data in CATEGORIES:
            category = db.records.create(
                label="CATEGORY",
                data={
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "resolution_rate": random.uniform(0.7, 0.95),
                },
                transaction=tx
            )
            categories[cat_data["name"]] = category
    
    print(f"  Created {len(categories)} categories: {list(categories.keys())}")
    return categories


def seed_tickets(db, customers, products, categories, model):
    """Create ticket records with embeddings."""
    print(f"\nCreating {TICKETS_COUNT} tickets with vector embeddings...")
    tickets = []
    index_id = create_vector_index(db, "TICKET", "description")
    
    # Batch embeddings for efficiency
    texts_to_embed = []
    ticket_data = []
    
    for i in range(TICKETS_COUNT):
        customer = random.choice(customers)
        product = random.choice(products)
        template = random.choice(TICKET_TEMPLATES)
        category_name = template["category"]
        category = categories[category_name]
        
        # Generate varied ticket content
        tier = customer["tier"]
        amount = random.randint(10, 200)
        expected = {"free": 0, "pro": 49, "enterprise": 199}.get(tier, 0)
        
        subject = template["subject"].format(tier=tier, amount=amount, expected=expected)
        description = template["description"].format(
            tier=tier, amount=amount, expected=expected
        )
        
        created_at = datetime.now() - timedelta(days=random.randint(1, 90))
        status = random.choices(
            ["open", "in_progress", "resolved", "closed"],
            weights=[0.2, 0.2, 0.4, 0.2]
        )[0]
        priority = random.choice(["low", "medium", "high", "critical"])
        
        ticket_data.append({
            "customer": customer,
            "product": product,
            "category": category,
            "subject": subject,
            "description": description,
            "status": status,
            "priority": priority,
            "created_at": created_at.isoformat(),
        })
        
        # Prepare combined text for embedding
        combined_text = f"{subject}. {description}"
        texts_to_embed.append(combined_text)
    
    # Generate all embeddings at once
    print("  Computing embeddings...")
    embeddings = model.encode(texts_to_embed)
    
    # Create tickets with embeddings in batches
    with db.transactions.begin() as tx:
        for i, td in enumerate(ticket_data):
            ticket = db.records.create(
                label="TICKET",
                data={
                    "subject": td["subject"],
                    "description": td["description"],
                    "status": td["status"],
                    "priority": td["priority"],
                    "created_at": td["created_at"],
                },
                vectors=[{
                    "propertyName": "description",
                    "vector": embeddings[i].tolist()
                }],
                transaction=tx
            )
            tickets.append(ticket)
            
            # Attach relationships
            db.records.attach(
                source=ticket,
                target=td["customer"],
                options={"type": "FILED_BY", "direction": "out"},
                transaction=tx
            )
            db.records.attach(
                source=ticket,
                target=td["product"],
                options={"type": "RELATES_TO", "direction": "out"},
                transaction=tx
            )
            db.records.attach(
                source=ticket,
                target=td["category"],
                options={"type": "CATEGORIZED_AS", "direction": "out"},
                transaction=tx
            )
            
            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/{TICKETS_COUNT} tickets")
    
    # Upsert vectors to index
    if index_id and tickets:
        print("  Indexing vectors...")
        items = [
            {"recordId": ticket.id, "vector": embeddings[i].tolist()}
            for i, ticket in enumerate(tickets)
        ]
        try:
            db.ai.indexes.upsert_vectors(index_id, {"items": items})
            print("  Vectors indexed successfully")
        except Exception as e:
            print(f"  Warning: Vector indexing failed: {e}")
    
    print(f"  Created {len(tickets)} tickets total")
    return tickets


def seed_solutions(db, tickets, categories):
    """Create solutions linked to resolved tickets."""
    print("\nCreating solutions...")
    solutions = []
    
    resolved_tickets = [t for t in tickets if t["status"] in ["resolved", "closed"]]
    
    with db.transactions.begin() as tx:
        for ticket in resolved_tickets[:25]:  # Create ~25 solutions
            category_name = None
            for cat_name, cat_obj in categories.items():
                try:
                    related = db.records.find({
                        "labels": ["CATEGORY"],
                        "where": {"TICKET": {"$id": ticket.id}}
                    })
                    if related.data:
                        category_name = cat_name
                        break
                except:
                    pass
            
            if not category_name:
                category_name = random.choice(list(CATEGORIES.keys()))
            
            sol_templates = SOLUTIONS.get(category_name, SOLUTIONS["billing"])
            sol_template = random.choice(sol_templates)
            
            solution = db.records.create(
                label="SOLUTION",
                data={
                    "title": sol_template["title"],
                    "steps": sol_template["steps"],
                    "verified": random.choice([True, False]),
                    "helpful_count": random.randint(0, 50),
                },
                transaction=tx
            )
            solutions.append(solution)
            
            # Link solution to ticket
            db.records.attach(
                source=ticket,
                target=solution,
                options={"type": "RESOLVED_WITH", "direction": "out"},
                transaction=tx
            )
    
    print(f"  Created {len(solutions)} solutions")
    return solutions


def seed_contracts(db, customers):
    """Create contract records linking customers to plans."""
    print("\nCreating customer contracts...")
    
    contracts = []
    with db.transactions.begin() as tx:
        for customer in customers:
            tier = customer["tier"]
            plan_prices = {"free": 0, "pro": 49, "enterprise": 199}
            
            contract = db.records.create(
                label="CONTRACT",
                data={
                    "plan_type": tier,
                    "monthly_price": plan_prices.get(tier, 0),
                    "start_date": customer["created_at"],
                    "auto_renew": tier != "free",
                },
                transaction=tx
            )
            contracts.append(contract)
            
            # Link customer to contract
            db.records.attach(
                source=customer,
                target=contract,
                options={"type": "HAS_CONTRACT", "direction": "out"},
                transaction=tx
            )
    
    print(f"  Created {len(contracts)} contracts")
    return contracts


def main():
    """Run the seeding process."""
    print("=" * 60)
    print("RushDB Contextual Grounding Layer - Data Seeding")
    print("=" * 60)
    
    # Initialize
    db = init_rushdb()
    model = init_embeddings()
    
    # Seed data
    customers = seed_customers(db)
    products = seed_products(db)
    categories = seed_categories(db)
    tickets = seed_tickets(db, customers, products, categories, model)
    solutions = seed_solutions(db, tickets, categories)
    contracts = seed_contracts(db, customers)
    
    print("\n" + "=" * 60)
    print("Seeding complete!")
    print(f"  - {len(customers)} customers")
    print(f"  - {len(products)} products")
    print(f"  - {len(categories)} categories")
    print(f"  - {len(tickets)} tickets")
    print(f"  - {len(solutions)} solutions")
    print(f"  - {len(contracts)} contracts")
    print("=" * 60)
    print("\nRun `python main.py` to see the retrieval comparison!")


if __name__ == "__main__":
    main()
