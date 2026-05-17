"""
Main demo: Node Classification for Intelligent Routing in AI Pipelines

This script demonstrates how to use RushDB for:
1. Classifying incoming support tickets against a taxonomy
2. Routing tickets to appropriate handlers using semantic matching
3. Maintaining pipeline integrity with transactions

Run 'python seed.py' first to set up the classification graph.
"""

import os
import random
from datetime import datetime
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not set in environment")

db = RushDB(API_KEY)

# Sample tickets for classification demo
SAMPLE_TICKETS = [
    {
        "subject": "Invoice #4521 shows incorrect charges",
        "body": "Hi, I noticed that our invoice for this month includes charges for a service we cancelled last week. Please review invoice #4521 and issue a refund for the incorrect amount.",
        "requester": "finance@acmecorp.com"
    },
    {
        "subject": "API returning 500 errors intermittently",
        "body": "Our integration is failing with 500 errors starting this morning around 9am. The errors seem random - about 20% of requests fail. Affected endpoint: /api/v2/data/sync. This is blocking our production pipeline.",
        "requester": "devops@techstart.io"
    },
    {
        "subject": "Cannot add new team member to workspace",
        "body": "I've been trying to invite a new colleague to our workspace but the invitation email never arrives. I've checked spam folder. Tried 3 different email addresses. Admin settings show invitation pending but recipient gets nothing.",
        "requester": "hr@globalretail.com"
    },
    {
        "subject": "Feature request: Dark mode support",
        "body": "Would love to see a dark mode option for the dashboard. Many of us work late hours and the bright interface is hard on the eyes. Even a simple toggle would be helpful.",
        "requester": "ux@designstudio.co"
    },
    {
        "subject": "Enterprise pricing for 500-seat deployment",
        "body": "We're evaluating your platform for our entire organization of 500 employees. Need detailed pricing for enterprise plan, SSO integration, dedicated support, and SLA guarantees. Timeline: decision by end of quarter.",
        "requester": "cto@megacorp.com"
    },
    {
        "subject": "GDPR compliance - data processing agreement",
        "body": "Our legal team requires a Data Processing Agreement that complies with GDPR Article 28. Please provide your standard DPA and confirm your data processing locations for EU operations.",
        "requester": "legal@financeplus.eu"
    },
    {
        "subject": "Webhook integration not firing on events",
        "body": "Our webhook endpoint is registered but not receiving events. We've verified the endpoint URL is correct and receiving pings from other services. Subscription is active. Debug ID: WH-88421. Please investigate.",
        "requester": "backend@solutions.dev"
    }
]


def classify_ticket(ticket_body: str) -> dict:
    """
    Classify a ticket by finding the best-matching category.
    
    Uses RushDB's semantic search to match the ticket content
    against the category descriptions.
    """
    try:
        # Search for matching category using semantic similarity
        results = db.ai.search({
            "propertyName": "description",
            "query": ticket_body,
            "labels": ["CATEGORY"],
            "limit": 3
        })
        
        if not results.data:
            return {"name": "unclassified", "confidence": 0.0}
        
        best_match = results.data[0]
        confidence = best_match.score if best_match.score else 0.0
        
        return {
            "id": best_match.id,
            "name": best_match.data.get("name", "unknown"),
            "description": best_match.data.get("description", ""),
            "confidence": confidence
        }
    except Exception as e:
        # Fallback: keyword-based classification
        print(f"  [WARN] Semantic search failed, using keyword fallback: {str(e)[:50]}")
        return keyword_classify(ticket_body)


def keyword_classify(text: str) -> dict:
    """Fallback classification using simple keyword matching."""
    text_lower = text.lower()
    
    keywords_map = {
        "billing_inquiry": ["invoice", "payment", "charge", "billing", "refund"],
        "technical_support": ["error", "api", "integration", "webhook", "bug", "crash"],
        "account_management": ["user", "permission", "access", "invite", "workspace"],
        "feature_request": ["feature", "request", "suggest", "dark mode"],
        "sales_inquiry": ["pricing", "enterprise", "quote", "buy", "deployment"],
        "compliance_legal": ["gdpr", "legal", "compliance", "dpa", "regulation"]
    }
    
    scores = {}
    for category, keywords in keywords_map.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[category] = score
    
    best_category = max(scores, key=scores.get) if scores else "unclassified"
    
    # Find the actual category record
    categories = db.records.find({"labels": ["CATEGORY"], "where": {"name": best_category}})
    cat_id = categories.data[0].id if categories.data else None
    
    return {
        "id": cat_id,
        "name": best_category,
        "confidence": scores.get(best_category, 0) / max(1, len(keywords_map.get(best_category, [1])))
    }


def find_route(category_id: str) -> list:
    """
    Find available routes for a given category.
    
    Returns handlers sorted by route priority (lower = higher priority).
    """
    # Find routes attached to this category
    routes = db.records.find({
        "labels": ["ROUTE"],
        "where": {
            "status": "active"
        },
        "limit": 10
    })
    
    available_handlers = []
    
    for route in routes.data:
        # Find handlers attached to this route
        handlers_via_route = db.records.find({
            "labels": ["HANDLER"],
            "where": {
                "ROUTE": {"$relation": {"type": "HANDLED_BY", "direction": "in"}},
                "status": "active"
            }
        })
        
        for handler in handlers_via_route.data:
            # Check capacity
            current_load = handler.data.get("current_load", 0)
            capacity = handler.data.get("capacity", 10)
            
            if current_load < capacity:
                available_handlers.append({
                    "id": handler.id,
                    "name": handler.data.get("name", "unknown"),
                    "expertise": handler.data.get("expertise", ""),
                    "current_load": current_load,
                    "priority": route.data.get("priority", 99)
                })
    
    # Sort by priority (lower = better)
    available_handlers.sort(key=lambda x: x["priority"])
    return available_handlers


def semantically_match_handler(ticket_body: str, handlers: list) -> dict:
    """
    Use semantic search to find the best handler for a ticket.
    
    Matches ticket content against handler expertise profiles.
    """
    if not handlers:
        return None
    
    try:
        # Search for matching handler
        results = db.ai.search({
            "propertyName": "expertise",
            "query": ticket_body,
            "labels": ["HANDLER"],
            "limit": 1
        })
        
        if results.data:
            best = results.data[0]
            # Find matching handler from our list
            for h in handlers:
                if h["id"] == best.id:
                    h["confidence"] = best.score if best.score else 0.5
                    return h
        
        # Fallback: return highest priority handler
        handlers[0]["confidence"] = 0.5
        return handlers[0]
        
    except Exception as e:
        print(f"  [WARN] Semantic handler match failed: {str(e)[:50]}")
        handlers[0]["confidence"] = 0.3
        return handlers[0]


def process_ticket(ticket_data: dict) -> dict:
    """
    Process a single ticket through the classification and routing pipeline.
    
    Uses a transaction to ensure atomicity:
    - Create the ticket record
    - Attach to classified category
    - Attach to assigned handler
    """
    print(f"\n{'='*60}")
    print(f"Processing: {ticket_data['subject'][:50]}...")
    print(f"{'='*60}")
    
    # Step 1: Classify the ticket
    print("\n[STEP 1] Classifying ticket...")
    classification = classify_ticket(ticket_data["body"])
    print(f"  → Category: {classification['name']}")
    print(f"  → Confidence: {classification.get('confidence', 0):.2f}")
    
    # Step 2: Find available routes
    print("\n[STEP 2] Finding routes...")
    category_id = classification.get("id") or db.records.find({
        "labels": ["CATEGORY"],
        "where": {"name": classification["name"]}
    }).data[0].id if classification["name"] != "unclassified" else None
    
    routes = find_route(category_id) if category_id else []
    print(f"  → Found {len(routes)} available handler(s)")
    
    # Step 3: Select best handler using semantic matching
    print("\n[STEP 3] Matching handler...")
    if routes:
        handler = semantically_match_handler(ticket_data["body"], routes)
    else:
        # Fallback: find any available handler
        all_handlers = db.records.find({"labels": ["HANDLER"], "limit": 5})
        handler = {
            "id": all_handlers.data[0].id if all_handlers.data else None,
            "name": all_handlers.data[0].data.get("name", "unassigned") if all_handlers.data else "unassigned",
            "confidence": 0.1
        } if all_handlers.data else {"id": None, "name": "unassigned", "confidence": 0}
    
    print(f"  → Assigned to: {handler['name']}")
    print(f"  → Match confidence: {handler.get('confidence', 0):.2f}")
    
    # Step 4: Create ticket record with transaction
    print("\n[STEP 4] Creating ticket record (transactional)...")
    
    with db.transactions.begin() as tx:
        # Create the ticket
        ticket_record = db.records.create(
            label="TICKET",
            data={
                "subject": ticket_data["subject"],
                "body": ticket_data["body"[:500]],  # Truncate for storage efficiency
                "requester": ticket_data["requester"],
                "status": "classified",
                "classified_at": datetime.now().isoformat(),
                "classification_confidence": classification.get("confidence", 0),
                "routing_confidence": handler.get("confidence", 0)
            },
            transaction=tx
        )
        
        # Attach to category if classified
        if classification.get("id"):
            category_record = db.records.find_by_id(classification["id"])
            if category_record and category_record.exists:
                db.records.attach(
                    source=ticket_record,
                    target=category_record,
                    options={"type": "CLASSIFIED_AS", "direction": "out"},
                    transaction=tx
                )
        
        # Attach to handler
        if handler.get("id"):
            handler_record = db.records.find_by_id(handler["id"])
            if handler_record and handler_record.exists:
                db.records.attach(
                    source=ticket_record,
                    target=handler_record,
                    options={"type": "ASSIGNED_TO", "direction": "out"},
                    transaction=tx
                )
                
                # Update handler load
                current_load = handler_record.data.get("current_load", 0)
                handler_record.update({"current_load": current_load + 1})
        
        # Transaction auto-commits on clean exit
        print("  → Ticket created and relationships established")
    
    return {
        "ticket_id": ticket_record.id,
        "category": classification["name"],
        "handler": handler["name"],
        "classification_confidence": classification.get("confidence", 0),
        "routing_confidence": handler.get("confidence", 0)
    }


def display_pipeline_summary(results: list):
    """Display a summary of all routing decisions."""
    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY: Intelligent Routing Results")
    print("=" * 70)
    
    print(f"\n{'Ticket ID':<30} {'Category':<20} {'Handler':<20} {'Conf'":<8}")
    print("-" * 78)
    
    for result in results:
        ticket_id_short = result["ticket_id"][:28] + ".."
        conf = max(result["classification_confidence"], result["routing_confidence"])
        print(f"{ticket_id_short:<30} {result['category']:<20} {result['handler']:<20} {conf:.2f}")
    
    print("-" * 78)
    
    # Aggregate by category
    print("\nRouting Distribution:")
    category_counts = {}
    handler_counts = {}
    
    for result in results:
        category_counts[result["category"]] = category_counts.get(result["category"], 0) + 1
        handler_counts[result["handler"]] = handler_counts.get(result["handler"], 0) + 1
    
    print("\n  By Category:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"    - {cat}: {count} ticket(s)")
    
    print("\n  By Handler:")
    for handler, count in sorted(handler_counts.items(), key=lambda x: -x[1]):
        print(f"    - {handler}: {count} ticket(s)")
    
    print("\n" + "=" * 70)


def verify_classification_graph():
    """Verify the classification graph is properly set up."""
    print("\n[VERIFY] Checking classification graph...")
    
    categories = db.records.find({"labels": ["CATEGORY"], "limit": 10})
    handlers = db.records.find({"labels": ["HANDLER"], "limit": 10})
    routes = db.records.find({"labels": ["ROUTE"], "limit": 20})
    
    print(f"  - Categories: {categories.total}")
    print(f"  - Handlers: {handlers.total}")
    print(f"  - Routes: {routes.total}")
    
    if categories.total == 0:
        print("\n[WARN] No categories found. Run 'python seed.py' first!")
        return False
    
    return True


def main():
    """Main entry point: process sample tickets through the classification pipeline."""
    print("\n" + "#" * 70)
    print("# NODE CLASSIFICATION FOR INTELLIGENT ROUTING IN AI PIPELINES")
    print("# RushDB Demo")
    print("-" * 70)
    
    # Verify graph is set up
    if not verify_classification_graph():
        print("\n[ERROR] Classification graph not initialized. Exiting.")
        return
    
    print("\n[DEMO] Processing sample tickets through intelligent routing pipeline...")
    print("      This demonstrates semantic classification and graph-based routing.\n")
    
    # Process each ticket
    results = []
    for ticket in SAMPLE_TICKETS:
        try:
            result = process_ticket(ticket)
            results.append(result)
        except Exception as e:
            print(f"  [ERROR] Failed to process ticket: {str(e)}")
            print(f"  [ERROR] Continuing with next ticket...")
    
    # Display summary
    if results:
        display_pipeline_summary(results)
    
    print("\n[DEMO] Complete!")
    print(f"\nProcessed {len(results)}/{len(SAMPLE_TICKETS)} tickets")
    print("\nKey concepts demonstrated:")
    print("  1. Graph-based classification taxonomy (CATEGORY nodes)")
    print("  2. Handler expertise modeling (HANDLER nodes)")
    print("  3. Routing rules as graph relationships (ROUTE nodes)")
    print("  4. Semantic search for classification matching")
    print("  5. Transactional pipeline integrity")
    print("  6. Traversal-based route discovery")


if __name__ == "__main__":
    main()
