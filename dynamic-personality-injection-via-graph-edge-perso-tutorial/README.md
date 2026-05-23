# Dynamic Personality Injection via Graph-Edge Personality Traits

A practical tutorial demonstrating how to use RushDB's property graph model to implement dynamic, context-aware personality injection for AI agents and characters.

## What This Solves

Traditional personality systems bake traits into static character objects. When an AI agent needs to behave differently based on context (customer support vs. creative brainstorming vs. technical troubleshooting), you typically:

- Maintain multiple character configs
- Write complex conditional logic
- Hard-code context-trait mappings

This approach is brittle, hard to extend, and doesn't capture the **relational nature** of personality. In reality, personality is contextual — a support agent's "empathetic" trait might amplify when dealing with frustrated customers, or a creative assistant might inject "playful" when brainstorming with a user who previously engaged positively.

## The Graph Solution

RushDB's property graph model lets you:

1. **Store personality traits as first-class records** — queryable, filterable, versionable
2. **Attach traits to agents via edges** — relationships become personality carriers
3. **Contextualize traits via context nodes** — same agent, different personality based on situation
4. **Query the graph to "inject" personality** — traverse relationships to build personality profile

### Data Model

```
[AGENT] ──HAS_TRAIT──> [PERSONALITY_TRAIT]
  │
  └──ACTS_IN──> [CONTEXT] ──REQUIRES──> [PERSONALITY_TRAIT]
```

- **Agent**: The AI character/assistant (static base identity)
- **PersonalityTrait**: Specific traits like "empathetic", "analytical", "playful"
- **Context**: Situation or domain (e.g., "customer_support", "creative_writing")
- **Relationships**: Edges carry both the trait and the context that triggers it

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- `rushdb>=2.0.0`

## Setup

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd dynamic-personality-injection-via-graph-edge-perso-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

## Quick Start

### 1. Seed the database (creates agents, traits, and contexts)

```bash
python seed.py
```

This creates:
- 3 AI agents: "SupportBot", "CodeAssistant", "CreativeMuse"
- 8 personality traits: empathetic, analytical, playful, formal, creative, patient, witty, diplomatic
- 5 contexts: customer_support, technical_debugging, creative_writing, onboarding, conflict_resolution

### 2. Run the demonstration

```bash
python main.py
```

Expected output:
```
=== Dynamic Personality Injection Demo ===

[1] Base personality for SupportBot:
  • empathetic: 0.9
  • patient: 0.8
  • diplomatic: 0.7

[2] Context-aware personality injection:
  Context: customer_support (high stakes)
  Active traits:
    • empathetic: 0.95 (boosted: +6.7%)
    • diplomatic: 0.85 (boosted: +21.4%)
    • patient: 0.9 (boosted: +12.5%)

  Context: technical_debugging
  Active traits:
    • analytical: 0.9
    • patient: 0.85
    • empathetic: 0.6 (de-emphasized)

[3] Traversal query - All traits for SupportBot in customer_support:
  Found 4 traits via graph traversal
  - empathetic (0.95)
  - diplomatic (0.85)
  - patient (0.9)
  - witty (0.5)

[4] Dynamic trait switching:
  Switching SupportBot from customer_support to conflict_resolution...
  New active traits:
    • diplomatic: 0.95 (primary: +37.5%)
    • empathetic: 0.85 (secondary)
    • patient: 0.7 (reduced: -12.5%)

[5] Cross-context trait comparison:
  CreativeMuse comparison across contexts:
  ┌─────────────────────┬──────────────────────────────────────────┐
  │ creative_writing     │ playful, creative, empathetic            │
  │ onboarding          │ empathetic, patient, diplomatic           │
  │ technical_debugging │ analytical, patient, empathetic            │
  └─────────────────────┴──────────────────────────────────────────┘
```

## Project Structure

```
.
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Data seeding script
└── main.py            # Main demonstration
```

## Key Concepts Demonstrated

| Concept | Implementation |
|---------|----------------|
| **Records as first-class entities** | Agents, traits, and contexts are RushDB records |
| **Relationships as personality carriers** | `HAS_TRAIT`, `ACTS_IN`, `REQUIRES` edges |
| **Graph traversal for personality queries** | `db.records.find()` with relationship filtering |
| **Contextual trait modification** | Query by context, adjust trait weights |
| **Dynamic personality injection** | Build prompt/system message from graph traversal |

## How It Works

### 1. Graph Structure

Each record type:

- **AGENT**: Base identity (`name`, `description`, `base_prompt_template`)
- **PERSONALITY_TRAIT**: Trait definition (`name`, `description`, `weight_range`)
- **CONTEXT**: Situation type (`name`, `domain`, `stakes_level`)

### 2. Relationship Types

- `AGENT --[HAS_TRAIT]--> PERSONALITY_TRAIT` — base traits with `weight` property
- `AGENT --[ACTS_IN]--> CONTEXT` — which contexts an agent serves
- `CONTEXT --[REQUIRES]--> PERSONALITY_TRAIT` — which traits are important in a context
- `CONTEXT --[BOOSTS]--> PERSONALITY_TRAIT` — how much a context boosts a trait

### 3. Personality Injection Flow

```python
def get_context_personality(agent_id, context_id):
    # 1. Get agent's base traits
    base_traits = db.records.find({
        "labels": ["PERSONALITY_TRAIT"],
        "where": {
            "AGENT": {"$id": {"$in": [agent_id]}, "$relation": {"type": "HAS_TRAIT", "direction": "in"}}
        }
    })
    
    # 2. Get context's required and boosted traits
    context_traits = db.records.find({
        "labels": ["PERSONALITY_TRAIT"],
        "where": {
            "CONTEXT": {"$id": {"$in": [context_id]}, "$relation": {"type": "REQUIRES", "direction": "in"}}
        }
    })
    
    # 3. Merge and adjust weights based on context
    # ... (see main.py for full implementation)
    
    return personality_profile
```

### 4. Building the System Prompt

```python
def inject_personality(agent, context, traits):
    trait_descriptions = [
        f"- {t['name']}: {t['description']} (weight: {t['weight']})"
        for t in sorted(traits, key=lambda x: x['weight'], reverse=True)
    ]
    
    return f"""You are {agent['name']}.

Your personality traits:
{chr(10).join(trait_descriptions)}

Current context: {context['name']}"""
```

## Extending the Model

### Add User-Specific Traits

```python
# Link user's historical engagement to agent's trait weights
db.records.attach(source=user, target=trait, options={"type": "INFLUENCES"})
```

### Temporal Trait Evolution

```python
# Update trait weights based on interaction success
db.records.update(record_id=trait.id, data={"weight": 0.85, "last_adjusted": "..."})
```

### Multi-Agent Personality Blending

```python
# For team-based interactions, blend multiple agents' traits
def blend_personalities(agents, context):
    traits = {}
    for agent in agents:
        agent_traits = get_context_personality(agent.id, context.id)
        for name, weight in agent_traits.items():
            traits[name] = traits.get(name, 0) + (weight / len(agents))
    return traits
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Model](https://docs.rushdb.com/core-concepts/property-graph)
- [Relationship Queries](https://docs.rushdb.com/api-reference/records#find)
