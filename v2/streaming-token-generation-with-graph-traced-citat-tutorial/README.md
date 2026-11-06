# Streaming Token Generation with Graph-Traced Citations

This tutorial demonstrates how to build a streaming token generator that traces citations through a property graph using RushDB. You'll learn how to:

- Store documents and their citation relationships as a graph
- Simulate streaming token generation with citation markers
- Trace citation chains through the graph to build context
- Generate responses with verifiable, traceable citations

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streaming Response                          │
│  "According to [1] and [2], the model architecture [3] enables..."
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Citation Tracer                              │
│  Maps citation references → graph traversal → source context    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RushDB Graph                              │
│                                                                 │
│  ┌──────────┐         CITES          ┌──────────┐             │
│  │ Document │ ──────────────────────▶ │ Document │             │
│  │ (Paper A)│                         │ (Paper B)│             │
│  └──────────┘                         └──────────┘             │
│       │                                     │                  │
│       │ AUTHORED_BY                        │ CITES             │
│       ▼                                     ▼                  │
│  ┌──────────┐                         ┌──────────┐             │
│  │  Author  │                         │ Document │             │
│  └──────────┘                         │ (Paper C)│             │
│                                       └──────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account ([sign up free](https://rushdb.com))
- Neo4j-based knowledge graph in RushDB

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

### 3. Seed the Knowledge Graph

This creates sample documents and citation relationships:

```bash
python seed.py
```

The seed script will:
- Create 10 research documents across AI/ML topics
- Link them with citation relationships
- Create author records and their affiliations

### 4. Run the Tutorial

```bash
python main.py
```

## Expected Output

```
=== Streaming Token Generation with Graph-Traced Citations ===

[1] Query: "How does attention mechanism work in transformers?"

[2] Streaming response with citations...

"The attention mechanism, as described in [1: Vaswani et al. 2017], 
enables the model to weigh the importance of different input tokens..."

[3] Citation trace for [1]:
    Document: Attention Is All You Need
    Authors: Vaswani, Shazeer, Parmar et al.
    Year: 2017
    Key Claim: Introduced self-attention mechanism
    Cited By: 2 documents in graph

[4] Citation chain trace:
    Attention Is All You Need
    └──▶ BERT: Pre-training of Deep Bidirectional Transformers
    └──▶ GPT-3: Language Models are Few-Shot Learners

[5] Generation complete. 847 tokens streamed.
```

## Key Concepts Demonstrated

### 1. Document Storage with Metadata

Documents are stored as records with rich metadata:

```sdk
db.records.create(
    label="DOCUMENT",
    data={
        "title": "Attention Is All You Need",
        "authors": ["Vaswani", "Shazeer", "Parmar"],
        "year": 2017,
        "abstract": "...",
        "key_claims": ["Self-attention", "Multi-head attention"]
    }
)
___SPLIT___
await db.records.create({
    label: 'DOCUMENT',
    data: {
        title: 'Attention Is All You Need',
        authors: ['Vaswani', 'Shazeer', 'Parmar'],
        year: 2017,
        abstract: '...',
        keyClaims: ['Self-attention', 'Multi-head attention']
    }
})
```

### 2. Citation Relationships as Edges

Citations are stored as directed relationships in the graph:

```sdk
db.records.attach(
    source=citing_document,
    target=cited_document,
    options={"type": "CITES", "direction": "out"}
)
___SPLIT___
await db.records.attach({
    source: citingDocument,
    target: citedDocument,
    options: { type: 'CITES', direction: 'out' }
})
```

### 3. Graph-Traversed Citation Context

When generating a response, traverse the graph to build context:

```sdk
# Find documents cited by a source
cited = db.records.find({
    "labels": ["DOCUMENT"],
    "where": {
        "CITES": {"$relation": {"type": "CITES", "direction": "in"}, "id": source.id}
    }
})
___SPLIT___
const cited = await db.records.find({
    labels: ['DOCUMENT'],
    where: {
        CITES: {
            $relation: { type: 'CITES', direction: 'in' },
            id: source.id
        }
    }
})
```

### 4. Streaming Token Generator

Simulated streaming that yields tokens with citation markers:

```python
async def stream_tokens_with_citations(query: str, citations: List[dict]):
    """Simulate streaming token generation with inline citations."""
    for token in generate_response_tokens(query, citations):
        yield token
        await asyncio.sleep(0.01)  # Simulate token generation delay
```

## Project Structure

```
streaming-token-generation-with-graph-traced-citat-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── seed.py             # Seeds knowledge graph with documents/citations
├── main.py             # Main tutorial demonstrating streaming + graph tracing
└── data/
    └── documents.json   # Sample document data (inline, ≤500 rows)
```

## How It Works

1. **Query Analysis**: Parse the user's query to identify citation needs
2. **Graph Search**: Traverse RushDB to find relevant documents
3. **Context Building**: Extract key claims and metadata from cited documents
4. **Token Streaming**: Generate tokens with inline citation markers
5. **Citation Resolution**: Map markers back to graph nodes for verification

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Data Modeling Guide](https://docs.rushdb.com/concepts/property-graph)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/streaming-token-generation-with-graph-traced-citat-tutorial)
