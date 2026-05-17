"""
Seed script: Creates the classification graph for intelligent routing.

This sets up:
- Categories: classification taxonomy for support tickets
- Handlers: agents with expertise areas
- Routes: mappings from category to handler with priority

Run this once before main.py. Safe to run multiple times (idempotent).
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not set in environment")

db = RushDB(API_KEY)

# Categories define our classification taxonomy
CATEGORIES = [
    {
        "name": "billing_inquiry",
        "description": "Questions about invoices, payments, subscriptions, and charges",
        "keywords": ["invoice", "payment", "charge", "subscription", "billing", "refund"]
    },
    {
        "name": "technical_support",
        "description": "Technical issues, bugs, integration problems, and API questions",
        "keywords": ["error", "bug", "crash", "api", "integration", "technical", "broken"]
    },
    {
        "name": "account_management",
        "description": "Account changes, permissions, user management, and access issues",
        "keywords": ["account", "permission", "access", "user", "password", "login"]
    },
    {
        "name": "feature_request",
        "description": "Requests for new features, enhancements, and product improvements",
        "keywords": ["feature", "request", "suggest", "improve", "wish", "enhancement"]
    },
    {
        "name": "sales_inquiry",
        "description": "Pre-sales questions, pricing, enterprise plans, and partnerships",
        "keywords": ["price", "pricing", "enterprise", "quote", "sales", "demo", "buy"]
    },
    {
        "name": "compliance_legal",
        "description": "Legal questions, compliance, GDPR, data privacy, and terms of service",
        "keywords": ["legal", "gdpr", "privacy", "compliance", "terms", "data", "regulation"]
    }
]

# Handlers with their expertise profiles
HANDLERS = [
    {
        "name": "billing_team",
        "expertise": "billing payments subscriptions invoices refunds",
        "categories": ["billing_inquiry"],
        "capacity": 10
    },
    {
        "name": "tech_support_tier1",
        "expertise": "technical issues API errors integration debugging basic troubleshooting",
        "categories": ["technical_support"],
        "capacity": 15
    },
    {
        "name": "tech_support_tier2",
        "expertise": "complex technical issues architecture debugging performance deep technical",
        "categories": ["technical_support"],
        "capacity": 5
    },
    {
        "name": "account_admin",
        "expertise": "account management permissions access security user management",
        "categories": ["account_management"],
        "capacity": 12
    },
    {
        "name": "product_team",
        "expertise": "features enhancements improvements suggestions product roadmap",
        "categories": ["feature_request"],
        "capacity": 8
    },
    {
        "name": "sales_team",
        "expertise": "sales pricing enterprise quotes demos partnerships buy",
        "categories": ["sales_inquiry"],
        "capacity": 10
    },
    {
        "name": "legal_compliance",
        "expertise": "legal compliance GDPR privacy terms regulations contracts",
        "categories": ["compliance_legal"],
        "capacity": 3
    }
]

def clear_existing_data():
    """Clean up existing test data (idempotent cleanup)."""
    labels_to_clean = ["CATEGORY", "HANDLER", "ROUTE", "TICKET"]
    for label in labels_to_clean:
        db.records.delete_many({"labels": [label], "where": {}})
    print("[SEED] Cleared existing records")

def create_categories():
    """Create category nodes with embeddings for semantic matching."""
    print("[SEED] Creating categories...")
    
    created_categories = []
    for idx, cat in enumerate(CATEGORIES):
        # Prepare vector-compatible description
        combined_text = f"{cat['description']} {' '.join(cat['keywords'])}"
        
        record = db.records.create(
            label="CATEGORY",
            data={
                "name": cat["name"],
                "description": cat["description"],
                "keywords": cat["keywords"]
            },
            vectors=[{"propertyName": "description", "vector": []}]  # Placeholder for managed index
        )
        created_categories.append(record)
        
        if (idx + 1) % 3 == 0:
            print(f"  Created {idx + 1}/{len(CATEGORIES)} categories...")
    
    print(f"[SEED] Created {len(created_categories)} categories")
    return created_categories

def create_handlers():
    """Create handler nodes representing support agents/teams."""
    print("[SEED] Creating handlers...")
    
    created_handlers = []
    for idx, handler in enumerate(HANDLERS):
        record = db.records.create(
            label="HANDLER",
            data={
                "name": handler["name"],
                "expertise": handler["expertise"],
                "capacity": handler["capacity"],
                "current_load": 0
            },
            vectors=[{"propertyName": "expertise", "vector": []}]
        )
        created_handlers.append(record)
        
        if (idx + 1) % 3 == 0:
            print(f"  Created {idx + 1}/{len(HANDLERS)} handlers...")
    
    print(f"[SEED] Created {len(created_handlers)} handlers")
    return created_handlers

def create_routes(categories, handlers):
    """Create routing rules linking categories to appropriate handlers."""
    print("[SEED] Creating routes...")
    
    created_routes = 0
    category_map = {cat.data["name"]: cat for cat in categories}
    handler_map = {h.data["name"]: h for h in handlers}
    
    for handler_data in HANDLERS:
        for cat_name in handler_data["categories"]:
            category = category_map.get(cat_name)
            handler = handler_map.get(handler_data["name"])
            
            if category and handler:
                # Higher priority handlers get lower priority number (process first)
                # Map priority based on handler type (tier2 higher priority for tech)
                priority = 5 if "tier2" in handler_data["name"] else 10
                
                route = db.records.create(
                    label="ROUTE",
                    data={
                        "priority": priority,
                        "status": "active"
                    }
                )
                
                # Attach route to category
                db.records.attach(
                    source=route,
                    target=category,
                    options={"type": "ROUTES_TO", "direction": "out"}
                )
                
                # Attach route to handler
                db.records.attach(
                    source=route,
                    target=handler,
                    options={"type": "HANDLED_BY", "direction": "out"}
                )
                
                created_routes += 1
    
    print(f"[SEED] Created {created_routes} routing rules")
    return created_routes

def create_vector_index():
    """Create vector indexes for semantic search on categories and handlers."""
    print("[SEED] Setting up vector indexes...")
    
    try:
        # Check if indexes already exist
        existing = db.ai.indexes.find()
        if existing.data:
            print(f"[SEED] Found {len(existing.data)} existing indexes")
            return
    except Exception:
        pass
    
    try:
        # Create category description index (managed - server embeds)
        db.ai.indexes.create({
            "label": "CATEGORY",
            "propertyName": "description"
        })
        print("[SEED] Created CATEGORY.description index")
    except Exception as e:
        print(f"[SEED] Category index note: {str(e)[:100]}")
    
    try:
        # Create handler expertise index
        db.ai.indexes.create({
            "label": "HANDLER",
            "propertyName": "expertise"
        })
        print("[SEED] Created HANDLER.expertise index")
    except Exception as e:
        print(f"[SEED] Handler index note: {str(e)[:100]}")

def main():
    print("=" * 60)
    print("RUSHDB NODE CLASSIFICATION GRAPH - SEED SCRIPT")
    print("=" * 60)
    
    # Check if already seeded
    existing_categories = db.records.find({"labels": ["CATEGORY"], "limit": 1})
    if existing_categories.total > 0:
        print("[SEED] Database already seeded. Skipping...")
        print("[SEED] Run with --force to re-seed")
        return
    
    print("[SEED] Starting database seed...\n")
    
    clear_existing_data()
    
    categories = create_categories()
    print()
    
    handlers = create_handlers()
    print()
    
    routes = create_routes(categories, handlers)
    print()
    
    create_vector_index()
    
    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"  - {len(CATEGORIES)} categories")
    print(f"  - {len(HANDLERS)} handlers")
    print(f"  - {routes} routing rules")
    print(f"\nNext: Run 'python main.py' to classify and route tickets")

if __name__ == "__main__":
    main()
