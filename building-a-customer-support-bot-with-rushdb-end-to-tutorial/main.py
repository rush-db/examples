#!/usr/bin/env python3
"""
Customer Support Bot with RushDB - End-to-End Tutorial

This script demonstrates core RushDB patterns for building a customer support bot:
- Querying existing data (customers, agents, tickets)
- Creating new records and relationships
- Semantic search for FAQ lookup
- Relationship traversal for ticket history

Run seed.py first to populate the database with test data.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
db = RushDB(
    token=os.getenv("RUSHDB_API_KEY"),
    url=os.getenv("RUSHDB_URL")
)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print('=' * 50)


def demo_query_customers():
    """Demonstrate querying customer records."""
    print_section("[1] Querying Customers")
    
    # Find all customers
    customers = db.records.find({
        "labels": ["CUSTOMER"],
        "limit": 10
    })
    
    print(f"Found {customers.total} customers in database")
    
    # Show customer details
    for customer in customers.data:
        plan_badge = f" [{customer['plan'].upper()}]" if customer.get('plan') != 'free' else ""
        print(f"  - {customer['name']} ({customer['email']}){plan_badge}")


def demo_find_open_tickets():
    """Demonstrate filtering tickets by status and priority."""
    print_section("[2] Finding Open Tickets")
    
    # Find tickets that are still open
    open_tickets = db.records.find({
        "labels": ["TICKET"],
        "where": {
            "status": {"$in": ["open", "pending"]}
        },
        "orderBy": {
            "priority": "desc"
        },
        "limit": 10
    })
    
    print(f"Found {open_tickets.total} open/pending tickets")
    
    for ticket in open_tickets.data:
        priority_indicator = {
            "urgent": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }.get(ticket.get('priority', 'low'), "⚪")
        
        print(f"  {priority_indicator} [{ticket['status'].upper()}] {ticket['subject']}")


def demo_create_ticket():
    """Demonstrate creating a new ticket record."""
    print_section("[3] Creating a New Ticket")
    
    # Find a customer to associate with
    customer = db.records.find({
        "labels": ["CUSTOMER"],
        "limit": 1
    }).data[0]
    
    print(f"Creating ticket for customer: {customer['email']}")
    
    # Create the ticket
    new_ticket = db.records.create(
        label="TICKET",
        data={
            "subject": "Cannot access my dashboard after password reset",
            "status": "open",
            "priority": "high",
            "ticket_id": "TICKET-NEW-001",
            "source": "customer_portal"
        }
    )
    
    print(f"Created ticket: {new_ticket.id}")
    print(f"  Subject: {new_ticket['subject']}")
    print(f"  Status: {new_ticket['status']}")
    print(f"  Priority: {new_ticket['priority']}")
    
    return new_ticket, customer


def demo_link_ticket_to_agent(new_ticket):
    """Demonstrate creating relationships between records."""
    print_section("[4] Linking Ticket to Agent")
    
    # Find an available agent
    agent = db.records.find({
        "labels": ["AGENT"],
        "where": {"department": "tier2"},
        "limit": 1
    }).data
    
    if agent:
        agent = agent[0]
    else:
        # Fall back to any agent
        agent = db.records.find({
            "labels": ["AGENT"],
            "limit": 1
        }).data[0]
    
    print(f"Assigning ticket to agent: {agent['name']} ({agent['department']})")
    
    # Link agent to ticket
    db.records.attach(
        source=agent,
        target=new_ticket,
        options={"type": "ASSIGNED_TO", "direction": "out"}
    )
    
    print(f"Created relationship: AGENT -> ASSIGNED_TO -> TICKET")
    
    return agent


def demo_semantic_search():
    """Demonstrate AI-powered semantic search for FAQ articles."""
    print_section("[5] Semantic FAQ Search")
    
    # Query a customer issue description
    customer_query = "I can't log into my account after resetting my password"
    print(f"Customer query: \"{customer_query}\"")
    print("Searching for relevant FAQ articles...\n")
    
    # Perform semantic search on FAQ content
    results = db.ai.search({
        "propertyName": "content",
        "query": customer_query,
        "labels": ["FAQ"],
        "limit": 3
    })
    
    if results.data:
        print("Top matching FAQ articles:")
        for i, article in enumerate(results.data):
            relevance = f"{article.score * 100:.1f}%"
            print(f"  {i + 1}. [{relevance}] {article['title']}")
            print(f"     Topic: {article.get('topic', 'N/A')}")
    else:
        print("  No matching articles found (FAQs may not be indexed yet)")
        print("  Note: Run 'python -c \"from rushdb import RushDB; db = RushDB(); db.ai.indexes.create({'label': 'FAQ', 'propertyName': 'content'})\"' to create an index")


def demo_ticket_history(new_ticket, customer):
    """Demonstrate traversing relationships to find ticket history."""
    print_section("[6] Finding Customer's Ticket History")
    
    print(f"Customer: {customer['email']}")
    
    # Find all tickets linked to this customer
    customer_tickets = db.records.find({
        "labels": ["TICKET"],
        "where": {
            "CUSTOMER": {"$id": {"$eq": customer.id}}
        },
        "orderBy": {"created_at": "desc"}
    })
    
    print(f"Found {customer_tickets.total} tickets in history:")
    
    for ticket in customer_tickets.data:
        status_icon = {
            "open": "🟢",
            "pending": "🟡",
            "resolved": "🔵",
            "closed": "⚫"
        }.get(ticket.get('status', ''), "⚪")
        
        ticket_id = ticket.get('ticket_id', ticket.id[:8])
        print(f"  {status_icon} {ticket_id} - {ticket['subject']}")


def demo_agent_workload(agent):
    """Demonstrate finding all tickets assigned to an agent."""
    print_section("[7] Finding Agent's Active Assignments")
    
    print(f"Agent: {agent['name']}")
    
    # Find all tickets assigned to this agent
    agent_tickets = db.records.find({
        "labels": ["TICKET"],
        "where": {
            "AGENT": {"$id": {"$eq": agent.id}}
        },
        "orderBy": {"priority": "desc"}
    })
    
    # Count by status
    status_counts = {}
    for ticket in agent_tickets.data:
        status = ticket.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"Total active tickets: {agent_tickets.total}")
    print("Breakdown by status:")
    for status, count in status_counts.items():
        print(f"  - {status.title()}: {count}")


def demo_create_faq_article():
    """Demonstrate creating a new FAQ article."""
    print_section("[8] Creating a New FAQ Article")
    
    new_faq = db.records.create(
        label="FAQ",
        data={
            "title": "Password Reset Troubleshooting Guide",
            "topic": "Account Management",
            "content": "If you're having trouble resetting your password, please ensure you have access to the email address associated with your account. Check your spam folder for the reset link. The link expires after 24 hours. If you continue to have issues, contact support.",
            "helpful_count": 0,
            "tags": ["password", "login", "account", "troubleshooting"]
        }
    )
    
    print(f"Created FAQ article: {new_faq.id}")
    print(f"  Title: {new_faq['title']}")
    print(f"  Topic: {new_faq['topic']}")
    print(f"  Tags: {', '.join(new_faq.get('tags', []))}")


def demo_upsert_record():
    """Demonstrate upsert pattern for updating or creating records."""
    print_section("[9] Upsert Pattern - Update or Create")
    
    # Check if a customer exists, update if so, create if not
    # This is useful for syncing data from external systems
    customer_email = "alice.anderson@example.com"
    
    print(f"Attempting upsert for: {customer_email}")
    
    upserted = db.records.upsert(
        label="CUSTOMER",
        data={
            "email": customer_email,
            "name": "Alice Anderson",
            "plan": "pro",
            "last_sync": "2024-01-15T10:30:00Z"
        },
        options={
            "mergeBy": ["email"],
            "mergeStrategy": "replace"
        }
    )
    
    action = "Created" if upserted.data.get("__created") else "Updated"
    print(f"Action: {action}")
    print(f"  Customer ID: {upserted.id}")
    print(f"  Plan: {upserted['plan']}")


def main():
    print("\n" + "=" * 60)
    print(" Building a Customer Support Bot with RushDB ")
    print(" " * 20 + "End-to-End Tutorial")
    print("=" * 60)
    
    # Run demonstrations
    demo_query_customers()
    demo_find_open_tickets()
    new_ticket, customer = demo_create_ticket()
    agent = demo_link_ticket_to_agent(new_ticket)
    demo_semantic_search()
    demo_ticket_history(new_ticket, customer)
    demo_agent_workload(agent)
    demo_create_faq_article()
    demo_upsert_record()
    
    print_section("Tutorial Complete!")
    print("""
You've seen the core patterns for building a customer support bot:

  ✓ Querying records with filters and ordering
  ✓ Creating new records with custom properties
  ✓ Building relationships between records
  ✓ Semantic search for finding relevant content
  ✓ Traversing relationships for ticket history
  ✓ Upsert pattern for sync operations

Next steps:
  - Check your RushDB dashboard to explore the data graph
  - Try modifying the queries to explore other relationships
  - Build a frontend to interact with this support bot
    """)


if __name__ == "__main__":
    main()
