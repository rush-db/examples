# Synthetic Training Data Generation Using Graph-Sampled Conversations

This tutorial demonstrates how to use RushDB's property graph model to sample realistic conversation patterns and generate synthetic training data for LLM fine-tuning.

## What You'll Learn

- How to model conversation data as a property graph in RushDB
- How to traverse graph relationships to sample conversation patterns
- How to generate high-quality synthetic training data from sampled patterns
- How to maintain semantic diversity in generated datasets

## Why RushDB for This Use Case?

RushDB excels at this because:

1. **Relationship-first structure**: Conversations naturally form graphs (users → conversations → messages → topics)
2. **Flexible schema**: No upfront schema needed; model your domain as you discover it
3. **Native graph traversal**: Find conversation patterns by traversing relationships, not writing Cypher
4. **Property nodes**: Share vocabulary across labels (e.g., "sentiment" property links across all message types)

## Architecture

```
┌─────────────┐       ┌───────────────┐       ┌──────────────┐
│    USER     │──────→│  CONVERSATION │──────→│   MESSAGE    │
└─────────────┘ 1:N   └───────────────┘  1:N  └──────────────┘
                           │                    │
                           │                    ▼
                           │              ┌──────────────┐
                           └─────────────→│    TOPIC     │
                                N:1        └──────────────┘
```

## Prerequisites

- Python 3.9+
- RushDB account (free tier at https://rushdb.com)
- `pip install -r requirements.txt`

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### 3. Seed the Database

This creates a realistic conversation graph with users, conversations, messages, and topics:

```bash
python seed.py
```

Expected output:
```
[Seeding] Creating 50 users...
[Seeding] Creating 200 conversations...
[Seeding] Creating 800 messages...
[Seeding] Creating 15 topics...
[Seeding] Creating relationships...
[Seeding] Done! Created 1065 records
```

### 4. Run the Tutorial

```bash
python main.py
```

Expected output:
```
=== Synthetic Training Data Generation Using Graph-Sampled Conversations ===

[1] Loading conversation patterns from graph...
  Found 200 conversations across 50 users
  Pattern distribution:
    - billing: 45 conversations (22.5%)
    - technical_support: 52 conversations (26.0%)
    - account_management: 38 conversations (19.0%)
    - product_inquiry: 35 conversations (17.5%)
    - general_feedback: 30 conversations (15.0%)

[2] Sampling conversation trees...
  Sampled 8 conversation trees with varying depths and patterns
  Depth distribution: {1: 2, 2: 3, 3: 2, 4: 1}

[3] Generating synthetic conversations...
  Generated 50 synthetic conversations
  Quality metrics:
    - Pattern adherence: 94.2%
    - Topic diversity: 0.87
    - Avg turns per conversation: 4.3

[4] Sample generated conversation:
  User: jane_employee_42
  Topic: technical_support
  Turns:
    1. USER: How do I reset my development environment?
    2. AGENT: You can reset by running the init script...
    3. USER: That worked, thanks!
    4. AGENT: Great! Anything else I can help with?
    5. USER: No, that was everything.
  Outcome: resolved
  Synthetic: Yes

[5] Exporting training data...
  Saved 50 examples to synthetic_training_data.json
  Format: ChatML-compatible instruction dataset
```

## Project Structure

```
synthetic-training-data-generation-using-graph-sam-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Data seeding script
└── main.py             # Main tutorial code
```

## Key Concepts Demonstrated

### 1. Graph-Based Pattern Sampling

RushDB's relationship traversal lets you find conversation patterns by their structure, not just properties:

```sdk
# Find conversations by their topic
conversations = db.records.find({
    "labels": ["CONVERSATION"],
    "where": {
        "TOPIC": {"$relation": {"type": "HAS_TOPIC", "direction": "out"}},
        "resolution_status": "resolved"
    }
})
___SPLIT___
// Find conversations by their topic
const conversations = await db.records.find({
    labels: ["CONVERSATION"],
    where: {
        "TOPIC": {"$relation": {"type": "HAS_TOPIC", "direction": "out"}},
        "resolution_status": "resolved"
    }
})
```

### 2. Message Tree Traversal

Traverse from conversation to messages in order:

```sdk
# Get all messages for a conversation, ordered by sequence
messages = db.records.find({
    "labels": ["MESSAGE"],
    "where": {
        "CONVERSATION": {"$relation": {"type": "PART_OF", "direction": "in"}},
        "conversation_id": conv_id
    },
    "orderBy": {"sequence_number": "asc"
    }
})
___SPLIT___
// Get all messages for a conversation, ordered by sequence
const messages = await db.records.find({
    labels: ["MESSAGE"],
    where: {
        "CONVERSATION": {"$relation": {"type": "PART_OF", "direction": "in"}},
        "conversation_id": conv_id
    },
    orderBy: {"sequence_number": "asc"}
})
```

### 3. Synthetic Data Generation

Generate new conversations by:
- Sampling message templates from real conversations
- Varying sentiment, vocabulary, and structure
- Maintaining topic coherence
- Adding diverse user personas

## Extending This Tutorial

### Add Vector Search for Semantic Diversity

Create a vector index to ensure generated data covers semantic space:

```sdk
# Create index on message content
index = db.ai.indexes.create({
    "label": "MESSAGE",
    "propertyName": "content",
    "sourceType": "managed"
})
___SPLIT___
// Create index on message content
const index = await db.ai.indexes.create({
    label: "MESSAGE",
    propertyName: "content",
    sourceType: "managed"
})
```

### Add User Preference Modeling

Extend the graph with user preference nodes to generate personalized synthetic data:

```sdk
# Link user preferences to conversation patterns
db.records.attach(
    source=user,
    target=preference,
    options={"type": "HAS_PREFERENCE"}
)
___SPLIT___
// Link user preferences to conversation patterns
await db.records.attach({
    source: user,
    target: preference,
    options: {type: "HAS_PREFERENCE"}
})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Data Modeling Guide](https://docs.rushdb.com/concepts/property-graph)
- [AI/Vector Search Features](https://docs.rushdb.com/ai-search)
- [GitHub Examples](https://github.com/rush-db/examples)
