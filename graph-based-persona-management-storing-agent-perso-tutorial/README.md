# Graph-Based Persona Management: Storing Agent Personality Vectors

This tutorial demonstrates how to use RushDB for **graph-based persona management** in multi-agent systems. You'll learn how to:

- Store agent personality traits as semantic vectors
- Create hierarchical agent relationships (supervisors, teams)
- Link agents to users/customers they serve
- Query personas using graph traversal and vector similarity
- Build rich agent context from the persona graph

## What is Graph-Based Persona Management?

In production AI systems, agents often need:

1. **Personality persistence** — Who is this agent? What are its traits?
2. **Relationship awareness** — Who does this agent report to? What users does it serve?
3. **Trait matching** — Which agent best fits a user's personality?

RushDB excels at this because it combines:

- **Property graph storage** — Native relationships between records
- **Vector search** — Semantic similarity on personality embeddings
- **Zero-schema flexibility** — Add new traits without migrations

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works)
- `RUSHDB_API_KEY` from your RushDB project

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

3. **Seed mock persona data:**

```bash
python seed.py
```

This creates sample personas with personality vectors representing traits like:
- **empathy** (0.0–1.0) — How understanding is the agent?
- **assertiveness** (0.0–1.0) — How directive should it be?
- **technical** (0.0–1.0) — Technical depth vs. conversational
- **creativity** (0.0–1.0) — Creative problem-solving vs. structured
- **patience** (0.0–1.0) — Tolerance for repetition

## Running the Tutorial

```bash
python main.py
```

### What the Demo Does

1. **Create Personas** — Defines support, sales, and assistant agent personas with personality vectors
2. **Build Relationships** — Links agents to supervisors, teams, and served users
3. **Traverse the Graph** — Find an agent's team, supervisor chain, or assigned users
4. **Vector Search** — Find the most similar persona to a given personality profile
5. **Persona Lookup** — Retrieve complete agent context for LLM system prompts

## Project Structure

```
graph-based-persona-management-storing-agent-perso-tutorial/
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── seed.py            # Mock persona data generator
└── main.py            # Main tutorial demonstration
```

## Key RushDB Features Used

| Feature | Method | Purpose |
|---------|--------|---------|
| Record creation | `db.records.create()` | Store persona nodes |
| Vector storage | `vectors=[...]` param | Attach personality embeddings |
| Relationships | `db.records.attach()` | Link personas in graph |
| Graph queries | `db.records.find()` with `$relation` | Traverse persona connections |
| Semantic search | `db.ai.search()` | Find similar personas |
| Transactions | `db.transactions.begin()` | Atomic persona creation |

## Expected Output

```
=== Graph-Based Persona Management Demo ===

[1] Created 3 personas with personality vectors
[2] Established supervisor relationships
[3] Linked agents to users
[4] Found 'alice@example.com's agent: Support-Alice
[5] Alice's supervisor: Manager-Bob
[6] Found similar persona to [0.9, 0.1, 0.5, 0.3, 0.8]: Support-Alice (0.95 similarity)
[7] Full persona context retrieved for Support-Alice

Demo complete! Check RushDB dashboard to see your persona graph.
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)
- [Property Graph vs. Relational](https://docs.rushdb.com/concepts/property-graph)
