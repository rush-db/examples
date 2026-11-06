# Graph-to-Prompt Conversion: Extracting Context from Relationships

A step-by-step implementation guide for extracting structured context from a RushDB property graph and feeding it to an LLM. This tutorial demonstrates how relationship semantics and traversal depth can be leveraged to build rich, contextual prompts for AI-powered applications.

## What This Demonstrates

- **Semantic graph modeling**: Building a knowledge graph where relationships carry meaning, not just connections
- **Contextual traversal**: Writing queries that extract context by relationship type and depth
- **Prompt conversion**: Transforming graph output into structured prompt format
- **Token management**: Priority-based pruning to respect LLM token limits
- **End-to-end pipeline**: RushDB → graph traversal → structured context → LLM prompt → response

## Prerequisites

- Python 3.9+
- RushDB account with API key ([sign up free](https://app.rushdb.com))
- OpenAI API key (for the LLM integration demo)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your RushDB and OpenAI API keys
```

### 3. Seed the Graph Database

This creates a sample knowledge graph about software tutorials with rich relationship semantics:

```bash
python seed.py
```

Expected output:
```
Seeding tutorial knowledge graph...
✓ Created 12 TUTORIAL records
✓ Created 45 CONCEPT records
✓ Created 28 EXAMPLE records
✓ Created 8 relationship types
✓ Seeding complete
```

### 4. Run the Main Demo

```bash
python main.py
```

Expected output:
```
=== Graph-to-Prompt Context Extraction Demo ===

1. Single-entity context (1-hop):
   Found 5 related concepts for 'Graph Databases'
   Token count: 847

2. Full depth traversal (3-hop):
   Found 12 related records across 3 depths
   Token count: 2,341

3. Priority-based pruning (1500 tokens):
   Reduced from 12 to 8 records
   Final token count: 1,487

4. LLM Response:
   [OpenAI API response displayed]

=== Demo Complete ===
```

## Project Structure


```
graph-to-prompt-conversion-extracting-context-from-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Graph seeding script
└── main.py             # Main demo (graph traversal + prompt conversion)
```

## Key Concepts

### The Graph Data Model

The tutorial knowledge graph uses these labels and relationship types:

| Label      | Description                              |
|------------|------------------------------------------|
| `TUTORIAL` | Top-level learning resource              |
| `CHAPTER`  | Major section within a tutorial          |
| `CONCEPT`  | Key idea or technique being taught      |
| `EXAMPLE`  | Code or scenario demonstrating a concept |

Relationship types carry semantic meaning:

| Relationship     | Direction        | Meaning                                    |
|------------------|------------------|--------------------------------------------|
| `CONTAINS`       | TUTORIAL→CHAPTER | Tutorial organization                      |
| `EXPLAINS`       | CHAPTER→CONCEPT  | Chapter introduces this concept            |
| `DEMONSTRATES`   | CONCEPT→EXAMPLE  | Concrete example for the concept            |
| `PREREQUISITE`   | TUTORIAL→TUTORIAL| Learning order dependency                  |
| `RELATED_TO`     | CONCEPT→CONCEPT  | Thematic relationship between ideas        |
| `EXTENDS`        | EXAMPLE→CONCEPT  | Example builds on previous concept         |

### Token Budget Management

When extracting context from deep traversals, the result set can exceed LLM token limits. This project implements priority-based pruning:

1. **Depth priority**: Closer nodes are more relevant
2. **Relationship type priority**: Semantic relationships ranked by importance
3. **Content priority**: Shorter, denser content preserved

### Prompt Format

The extracted context is converted to a structured format:

```
## Context
[Relationship path]
- Node: {type} "{name}"
  Properties: {key: value}
  Relationship: {rel_type} → {target}

## Question
{user_query}
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Modeling Best Practices](https://docs.rushdb.com/concepts/property-graph)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/graph-to-prompt-conversion-extracting-context-from-tutorial)
