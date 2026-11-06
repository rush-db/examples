# Building Production-Ready Agent Toolchains with Graph-Native Orchestration

A complete real-world build demonstrating a customer support agent that uses RushDB's property graph + vector search to route, execute, and audit multi-step support flows with sub-100ms latency.

## What This Demonstrates

- **Graph-native orchestration**: Each agent action becomes a node in a traversable graph — conversation flow, tool dependencies, and resolution paths are all first-class graph citizens.
- **Vector-semantic tool routing**: Support tools are indexed by their description embeddings. A user query is embedded and similarity-searched to find the most relevant tools in a single API call.
- **Context-preserving escalation**: When an issue requires human intervention, the entire conversation graph is attached to the escalation record — no context is lost in handoff.
- **Complete audit trail**: Every node records what the agent did, why it made that decision, and the exact context at that moment. Timestamps, scores, and decision reasoning are all persisted.
- **Single-query performance**: RushDB handles graph traversal and vector search in the same query layer — no ETL, no data pipeline lag, no N+1 queries.

## Architecture

```
User Query
    │
    ▼
┌─────────────────┐     ┌─────────────────────────────────┐
│  Embed Query    │────▶│  RushDB Semantic Search         │
└─────────────────┘     │  (vector similarity on tools)   │
                        └─────────────┬───────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────────┐
                        │  Selected Support Tool      │
                        │  + Execution Context         │
                        └─────────────┬───────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────────┐
                        │  AgentAction Node Created    │
                        │  (attached to conversation)  │
                        └─────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            [Resolution]              [Escalation → Human Agent]
            (session complete)         (full context graph attached)
```

## Prerequisites

- Python 3.10+
- A RushDB account (Free tier works) — [sign up](https://rushdb.com)
- `sentence-transformers` for embeddings (all-MiniLM-L6-v2, 384 dimensions)

## Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env and add your RUSHDb_API_TOKEN
```

## Get Your RushDB API Token

1. Sign up at [rushdb.com](https://rushdb.com)
2. Create a new project
3. Navigate to Settings → API Tokens
4. Copy your API key into `.env` as `RUSHDb_API_TOKEN=your-key-here`

## Run the Demo

```bash
# Step 1: Seed the knowledge base with support tools
python seed.py

# Step 2: Run the agent demo
python main.py
```

### What You'll See

1. **Seeding phase**: Creates ~20 support tool records with vector embeddings indexed on their descriptions.
2. **Agent execution phase**:
   - A customer query arrives ("I can't log in after resetting my password")
   - The query is embedded and semantic search finds the most relevant tools
   - The agent executes the tool and creates an audit node
   - A multi-step conversation is simulated (resolve → escalate → resolve)
   - The full conversation graph is retrieved and displayed

## Project Structure

```
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── seed.py            # Seeds the support tool knowledge base
└── main.py            # Main agent orchestration demo
```

## Key Code Patterns

### Creating a Vector Index

```sdk
# Create an index for tool descriptions (managed - RushDB embeds for you)
index = db.ai.indexes.create({
    "label": "SUPPORT_TOOL",
    "propertyName": "description"
})
___SPLIT___
# Create an index for tool descriptions (managed - RushDB embeds for you)
index = db.ai.indexes.create({
    "label": "SUPPORT_TOOL",
    "propertyName": "description"
})
```

### Semantic Tool Discovery

```sdk
# Find the most relevant support tool for a user query
tools = db.ai.search({
    "propertyName": "description",
    "query": "I can't reset my password",
    "labels": ["SUPPORT_TOOL"],
    "limit": 3
})
___SPLIT___
# Find the most relevant support tool for a user query
tools = db.ai.search({
    "propertyName": "description",
    "query": "I can't reset my password",
    "labels": ["SUPPORT_TOOL"],
    "limit": 3
})
```

### Audit Trail Creation (Atomic Transaction)

```sdk
# Every agent action is recorded with full context
with db.transactions.begin() as tx:
    action = db.records.create(
        label="AGENT_ACTION",
        data={
            "type": "tool_execution",
            "tool": tool.data["name"],
            "reasoning": "Password reset flow requires account verification",
            "context": {"user_id": user_id, "session_id": session_id},
            "status": "success"
        },
        transaction=tx
    )
    db.records.attach(source=action, target=session, options={"type": "EXECUTED_IN"}, transaction=tx)
___SPLIT___
# Every agent action is recorded with full context
with db.transactions.begin() as tx:
    action = db.records.create(
        label="AGENT_ACTION",
        data={
            "type": "tool_execution",
            "tool": tool.data["name"],
            "reasoning": "Password reset flow requires account verification",
            "context": {"user_id": user_id, "session_id": session_id},
            "status": "success"
        },
        transaction=tx
    )
    db.records.attach(source=action, target=session, options={"type": "EXECUTED_IN"}, transaction=tx)
```

### Context-Preserving Escalation

```sdk
# Escalation carries the entire conversation graph
escalation = db.records.create(
    label="ESCALATION",
    data={
        "reason": "account_locked",
        "priority": "high",
        "summary": "User locked out after failed password reset attempts"
    }
)
# Attach all conversation history to the escalation
for action in conversation_history:
    db.records.attach(source=action, target=escalation, options={"type": "PART_OF"})
___SPLIT___
# Escalation carries the entire conversation graph
escalation = db.records.create(
    label="ESCALATION",
    data={
        "reason": "account_locked",
        "priority": "high",
        "summary": "User locked out after failed password reset attempts"
    }
)
# Attach all conversation history to the escalation
for action in conversation_history:
    db.records.attach(source=action, target=escalation, options={"type": "PART_OF"})
```

## Cost Notes

This demo uses:
- ~20 records created (knowledge base seeding) — ~10.5 KU each
- Vector index creation (1KU per property)
- 3-5 semantic searches at runtime (5 KU each)
- Agent action records for audit trail

**Total for this demo**: Well under the Free tier's 100K monthly KU limit.

See [RushDB Pricing](https://rushdb.com/pricing) for full cost details.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Concepts](https://docs.rushdb.com/concepts/property-graph)
- [Vector Search Guide](https://docs.rushdb.com/guides/vector-search)
- [Transaction Reference](https://docs.rushdb.com/reference/transactions)
