# Dynamic Persona Switching in Multi-Agent Systems

This tutorial demonstrates how to use RushDB as a memory layer for multi-agent systems that dynamically switch between personas based on context and task requirements.

## What It Demonstrates

- **Persona modeling**: Creating structured personas with traits, capabilities, and context
- **Dynamic switching**: Logic for determining when and how an agent transitions between personas
- **Context preservation**: Storing conversation history and state per persona
- **Graph relationships**: Using RushDB's property graph to model agent-persona relationships
- **State management**: Tracking active personas, switching history, and task context

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Multi-Agent System                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                │
│  │  Agent   │────▶│  Persona │────▶│ Context  │                │
│  │  Core    │     │  Store   │     │  Memory  │                │
│  └──────────┘     └──────────┘     └──────────┘                │
│       │                  │                │                     │
│       ▼                  ▼                ▼                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    RushDB (Graph Layer)                  │   │
│  │  Nodes: Agents, Personas, Contexts, Conversations        │   │
│  │  Edges: SWITCHED_TO, ACTIVE_AS, PARTICIPATED_IN          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Persona Structure
Each persona consists of:
- **Name & Description**: Identity and purpose
- **Traits**: Behavioral characteristics (e.g., `{"creativity": 0.9, "analytical": 0.3}`)
- **Capabilities**: What the persona can do (e.g., `["code_review", "architecture"]`)
- **Communication Style**: How it responds (formal, casual, technical)
- **Domain**: Primary area of expertise

### Switching Triggers
- Task type matching capability
- Conversation topic shift
- Explicit user request
- Contextual need (e.g., debugging requires technical persona)

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/rush-db/examples.git
cd dynamic-persona-switching-in-multi-agent-systems-u-tutorial

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your RushDB API key
```

## Running the Tutorial

```bash
# Seed sample personas and agents
python seed.py

# Run the main demonstration
python main.py
```

## Expected Output

```
=== Multi-Agent Persona System Demo ===

[1] Created 5 personas: Technical Expert, Creative Writer, Business Analyst, Support Assistant, Data Scientist

[2] Created 3 agents with different specializations

[3] Agent 'assistant-alpha' switched to Technical Expert persona
    → SWITCHED_TO relationship created
    → Active persona context updated

[4] Simulated conversation with persona context:
    User: "How do I optimize this Python function?"
    Technical Expert: "Let me analyze the code structure..."

[5] Traced conversation through RushDB:
    Found 3 conversation segments for assistant-alpha
    Total interactions: 12

[6] Persona switch history for assistant-alpha:
    - Current: Technical Expert
    - Previous: Support Assistant (30 minutes ago)
    - Previous: Creative Writer (2 hours ago)
```

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py            # Creates sample personas and agents
└── main.py            # Main demonstration script
```

## Dependencies

- `rushdb>=2.0.0` - RushDB Python SDK
- `python-dotenv` - Environment variable management

## Prerequisites

- Python 3.10+
- RushDB API key (get one at https://rushdb.com)

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdks/python)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/dynamic-persona-switching-in-multi-agent-systems-u-tutorial)
