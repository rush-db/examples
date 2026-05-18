# Building a Customer Support Bot with RushDB: End-to-End Tutorial

A complete demonstration of building a customer support bot using RushDB's property graph, semantic search, and relationship traversal capabilities.

## What This Tutorial Demonstrates

- **Record Management**: Creating customers, agents, tickets, and FAQ articles as typed RushDB records
- **Relationship Graph**: Linking customers to tickets, agents to tickets, products to issues
- **Semantic Search**: Using AI-powered vector search to find relevant FAQ articles from ticket descriptions
- **Transaction Support**: Atomic operations for creating linked ticket chains
- **Advanced Queries**: Filtering and traversing relationships to find related records

## Prerequisites

- Python 3.9+
- A RushDB API key (get one at https://rushdb.com)
- `pip` for installing dependencies

## Setup

1. **Clone the repository and navigate to this directory:**

   ```bash
   git clone https://github.com/rush-db/examples
   cd building-a-customer-support-bot-with-rushdb-end-to-tutorial
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your environment:**

   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

4. **Seed the database with mock data:**

   ```bash
   python seed.py
   ```

   The seed script generates:
   - 10 customers with contact info
   - 5 support agents
   - 20 support tickets in various states
   - 30 FAQ articles covering common support topics

## Running the Tutorial

After seeding, run the main script to see all capabilities in action:

```bash
python main.py
```

The script demonstrates:

1. **Querying existing data** — Finding customers, agents, and tickets
2. **Creating new records** — Adding customers, tickets, and FAQ articles
3. **Building relationships** — Linking tickets to customers, agents, and products
4. **Semantic search** — Finding relevant FAQ articles from ticket descriptions
5. **Relationship traversal** — Finding all tickets for a customer, all assignments for an agent

## Expected Output

```
=== Customer Support Bot with RushDB ===

[1] Querying existing customers...
Found 10 customers

[2] Finding open tickets...
Found 8 open tickets (priority sorted)

[3] Creating a new ticket...
Created ticket TICKET-NEW-001 for customer@example.com

[4] Linking ticket to agent...
Assigned ticket to agent Sarah

[5] Semantic FAQ search...
Query: "I can't log into my account"
Top 3 FAQ matches:
  - [0.923] Account Access Issues
  - [0.871] Password Reset Guide
  - [0.812] Two-Factor Authentication Setup

[6] Finding customer's ticket history...
customer@example.com has 3 tickets:
  - TICKET-001 (Open)
  - TICKET-005 (Pending)
  - TICKET-NEW-001 (Open)

[7] Finding agent's active assignments...
Agent Sarah has 5 open tickets

=== Tutorial Complete ===
```

## Project Structure

```
building-a-customer-support-bot-with-rushdb-end-to-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Mock data generation script
└── main.py             # Main tutorial demonstration
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RUSHDB_API_KEY` | Yes | Your RushDB API key from the dashboard |
| `RUSHDB_URL` | No | Self-hosted URL (defaults to cloud) |

## Key RushDB Patterns Used

### Creating Records

```sdk
from rushdb import RushDB

db = RushDB("API_KEY")

# Create a customer
customer = db.records.create(
    label="CUSTOMER",
    data={
        "email": "alice@example.com",
        "name": "Alice Johnson",
        "plan": "pro"
    }
)
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Create a customer
const customer = await db.records.create({
    label: 'CUSTOMER',
    data: {
        email: 'alice@example.com',
        name: 'Alice Johnson',
        plan: 'pro'
    }
})
```

### Creating Relationships

```sdk
# Link customer to ticket
db.records.attach(
    source=customer,
    target=ticket,
    options={"type": "OPENED", "direction": "out"}
)

# Link agent to ticket
db.records.attach(
    source=agent,
    target=ticket,
    options={"type": "ASSIGNED_TO", "direction": "out"}
)
___SPLIT___
// Link customer to ticket
await db.records.attach({
    source: customer,
    target: ticket,
    options: { type: 'OPENED', direction: 'out' }
})

// Link agent to ticket
await db.records.attach({
    source: agent,
    target: ticket,
    options: { type: 'ASSIGNED_TO', direction: 'out' }
})
```

### Semantic Search

```sdk
# Find relevant FAQ articles from a ticket description
results = db.ai.search({
    propertyName: "content",
    query: "I can't reset my password",
    labels: ["FAQ"],
    limit: 3
}).data

for article in results:
    print(f"[{article.score:.3f}] {article['title']}")
___SPLIT___
// Find relevant FAQ articles from a ticket description
const results = await db.ai.search({
    propertyName: 'content',
    query: "I can't reset my password",
    labels: ['FAQ'],
    limit: 3
})

for (const article of results.data) {
    console.log(`[${article.score.toFixed(3)}] ${article.title}`)
}
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://pypi.org/project/rushdb/)
- [RushDB Examples](https://github.com/rush-db/examples)
