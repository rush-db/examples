# Building a Graph-Backed Reflection Mechanism for Agent Self-Improvement

This project demonstrates how to build an agent reflection system using RushDB's graph database capabilities. It models an AI agent that learns from its experiences by recording actions, analyzing outcomes, and generating actionable insights.

## What This Demonstrates

- **Experience Recording**: Store agent actions as graph nodes with rich metadata
- **Reflection Creation**: Link analytical reflections to specific experiences
- **Insight Generation**: Extract reusable patterns from multiple reflections
- **Graph Traversal**: Find relevant past insights when encountering similar situations
- **Self-Improvement Loop**: Use historical insights to inform future decision-making

## Architecture

```
EXPERIENCE ──CONTAINS──> ACTION
    │                      
    ▼ PRODUCES             
 REFLECTION ──GENERATES──> INSIGHT
    │                      
    ▼ ANALYSIS             
 PATTERN ◄──INFORMS───────
```

## Prerequisites

- Python 3.10+
- RushDB account (Free tier works)
- `rushdb>=2.0.0` Python SDK

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your RushDB API key
   ```

3. **Get your API key:**
   - Sign up at https://dash.rushdb.com
   - Create a project and copy the API key

4. **Seed the database (optional but recommended):**
   ```bash
   python seed.py
   ```
   This creates sample experiences, reflections, and insights to demonstrate the system.

## Running the Example

```bash
python main.py
```

The script will:
1. Create sample experiences with agent actions
2. Generate reflections analyzing those experiences
3. Extract insights from patterns across reflections
4. Demonstrate querying insights for similar future situations

## Expected Output

```
=== Agent Reflection System Demo ===

[1] Creating experiences and actions...
   ✓ Created experience: 'customer_support_session_001'
   ✓ Created experience: 'code_review_session_001'
   ✓ Created experience: 'debugging_session_001'

[2] Creating reflections on experiences...
   ✓ Created reflection for 'customer_support_session_001'
   ✓ Created reflection for 'code_review_session_001'
   ✓ Created reflection for 'debugging_session_001'

[3] Generating insights from reflections...
   ✓ Generated insight: 'patience_in_support'
   ✓ Generated insight: 'systematic_code_review'
   ✓ Generated insight: 'root_cause_analysis'

[4] Finding insights for new situations...
   Query: "A user is frustrated and doesn't understand the product"
   Found 3 relevant insights:
   - patience_in_support (confidence: 0.95)
   - clear_communication (confidence: 0.87)
   - root_cause_analysis (confidence: 0.82)

[5] Traversing the reflection graph...
   Experience 'debugging_session_001' produced insights:
   - root_cause_analysis
   - systematic_approach
   - documentation_importance

[6] Analyzing patterns across experiences...
   Pattern found: Actions involving 'user_frustration' lead to insights
   about patience and clear communication with 85% frequency.
```

## Data Model

### Labels

| Label | Description |
|-------|-------------|
| `EXPERIENCE` | A session or interaction the agent had |
| `ACTION` | A specific action taken during an experience |
| `REFLECTION` | The agent's analysis of what happened |
| `INSIGHT` | A reusable lesson extracted from reflections |
| `SITUATION` | A context descriptor for matching insights |

### Relationships

| Type | From → To | Description |
|------|-----------|-------------|
| `CONTAINS` | EXPERIENCE → ACTION | Action taken during experience |
| `PRODUCES` | EXPERIENCE → REFLECTION | Analysis generated from experience |
| `GENERATES` | REFLECTION → INSIGHT | Lesson extracted from reflection |
| `INFORMS` | INSIGHT → SITUATION | Insight applies to these situations |
| `INFLUENCES` | INSIGHT → EXPERIENCE | Insight guides future experiences |

## Key RushDB Patterns Used

- **Nested creation**: Creating actions as part of experience creation
- **Relationship attachment**: Linking reflections to experiences
- **Graph traversal**: Finding related insights through connected nodes
- **Semantic search**: Matching new situations to relevant insights

## Extending This Example

To adapt this for your own agent:

1. **Add custom metadata**: Extend the `data` dict with fields relevant to your domain
2. **Create domain-specific insights**: Modify the insight generation logic for your use case
3. **Build decision loops**: Use the insight query results to guide agent actions
4. **Track confidence**: Update insight confidence based on outcomes

## Further Reading

- [RushDB Python SDK Docs](https://docs.rushdb.com/sdk/python/)
- [Graph Data Modeling](https://docs.rushdb.com/concepts/property-graph/)
- [Semantic Search](https://docs.rushdb.com/features/ai-search/)

---

Project: https://github.com/rush-db/examples/tree/main/building-a-graph-backed-reflection-mechanism-for-a-tutorial
