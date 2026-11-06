# Building Conversation Memory Chains with Time-Decay Relationship Weights

A tutorial demonstrating how to build intelligent conversation memory systems using RushDB's property graph model with time-decay weighted relationships.

## What This Project Demonstrates

- **Conversation Chain Modeling**: Represent multi-turn conversations as linked message chains
- **Time-Decay Weighting**: Assign relationship weights that decay based on temporal distance
- **Context Retrieval**: Query weighted conversation history to provide context for new messages
- **Memory Prioritization**: Automatically surface the most relevant past context using decay weights

## Core Concepts

### Time-Decay Formula

We use exponential decay to weight relationships:

```
weight = base^(-days_since / half_life)
```

- **half_life**: Days until the weight drops to 50% (default: 7 days)
- **base**: Decay base (default: 2, meaning halving every half_life days)
- Result: Weights range from 1.0 (now) down to ~0.0 (very old)

### RushDB Graph Model

```
CONVERSATION ──[PART_OF]──> MESSAGE ──[REPLY_TO]──> MESSAGE
     │                                                     │
     │                CONTEXTUALLY_LINKED (weight: 0.85)   │
     └─────────────────────────────────────────────────────┘
```

- **CONVERSATION**: Session container
- **MESSAGE**: Individual messages with timestamps
- **CONTEXTUALLY_LINKED**: Time-weighted relationship to relevant past context
- **REPLY_TO**: Sequential conversation flow

## Prerequisites

- Python 3.10+
- RushDB account ([get free API key](https://app.rushdb.com))
- `rushdb>=2.0.0` package

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```


2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_TOKEN
   ```

3. **Generate mock data** (optional but recommended):
   ```bash
   python seed.py
   ```
   This creates sample conversations across multiple users with realistic message chains.

## How to Run

```bash
python main.py
```

The script will:
1. Initialize RushDB connection
2. Create sample conversations (if not already seeded)
3. Calculate and assign time-decay weights to context relationships
4. Query weighted context for a sample message
5. Demonstrate context retrieval sorted by relevance


## Expected Output

```
=== Conversation Memory Chains with Time-Decay ===

[1] Creating sample conversation history...
    ✓ Created conversation 'project-kickoff'
    ✓ Created 12 messages in conversation

[2] Calculating time-decay weights for context links...
    Context Link weights (oldest → newest):
      Day 14: weight = 0.250
      Day 13: weight = 0.271
      Day 10: weight = 0.357
      Day 7:  weight = 0.500
      Day 5:  weight = 0.629
      Day 3:  weight = 0.794
      Day 1:  weight = 0.944
      Day 0:  weight = 1.000

[3] Querying weighted context for new message...
    Context Relevance Scores:
      [0.94] "Thanks for the quick summary!" (1 day ago)
      [0.81] "I'll draft the technical spec document" (2 days ago)
      [0.63] "Need to verify database schema requirements" (5 days ago)
      [0.50] "Architecture review scheduled for Friday" (7 days ago)
      [0.36] "Initial database requirements from client" (10 days ago)

[4] Querying specific user conversation history...
    Found 45 messages from alice@example.com across 8 conversations

=== Success ===
```

## Project Structure

```
building-conversation-memory-chains-with-time-deca-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py            # Mock data generation
└── main.py            # Main demonstration
```

## Key RushDB API Calls Used

```sdk
# Create conversation
conversation = db.records.create(
    label="CONVERSATION",
    data={"title": "project-kickoff", "channel": "engineering"}
)

# Create message with timestamp
message = db.records.create(
    label="MESSAGE",
    data={
        "content": "Thanks for the quick summary!",
        "timestamp": "2024-01-15T10:30:00Z",
        "author": "alice@example.com"
    }
)

# Attach time-weighted context relationship
db.records.attach(
    source=current_message,
    target=past_context,
    options={
        "type": "CONTEXTUALLY_LINKED",
        "properties": {"weight": 0.85, "decay_half_life_days": 7}
    }
)

# Query weighted context
contexts = db.records.find({
    "labels": ["MESSAGE"],
    "where": {
        "MESSAGE": {
            "$relation": {"type": "CONTEXTUALLY_LINKED", "direction": "in"},
            "timestamp": {"$gte": cutoff_date}
        }
    },
    "orderBy": {"CONTEXTUALLY_LINKED.weight": "desc"}
})
___SPLIT___
// TypeScript equivalent pattern
const conversation = await db.records.create({
  label: 'CONVERSATION',
  data: { title: 'project-kickoff', channel: 'engineering' }
})

const message = await db.records.create({
  label: 'MESSAGE',
  data: {
    content: 'Thanks for the quick summary!',
    timestamp: '2024-01-15T10:30:00Z',
    author: 'alice@example.com'
  }
})

await db.records.attach({
  source: currentMessage,
  target: pastContext,
  options: { type: 'CONTEXTUALLY_LINKED' }
})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/building-conversation-memory-chains-with-time-deca-tutorial)
- [RushDB Pricing](https://rushdb.com/pricing)
