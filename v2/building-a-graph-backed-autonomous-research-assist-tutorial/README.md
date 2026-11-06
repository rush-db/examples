# Building a Graph-Backed Autonomous Research Assistant

This tutorial demonstrates how to use RushDB as the memory layer for an autonomous research assistant. You'll learn how to:

- Model research entities (papers, claims, findings) as graph nodes
- Create semantic relationships between research artifacts
- Traverse the graph to build contextual memory for LLM prompts
- Perform vector similarity search on research content
- Use transactions for atomic research operations

## What is a Graph-Backed Research Assistant?

Unlike traditional vector databases that store flat embeddings, RushDB lets you store research as a **property graph** with typed relationships. This means:

- **Structured memory**: Papers cite papers, claims support hypotheses, findings contradict each other
- **Traversable context**: Walk from a query to relevant papers to citations to related claims
- **Semantic search**: Find relevant content by meaning, not just keywords
- **Audit trail**: Every research action is stored and linked

## Prerequisites

- Python 3.9+
- RushDB API key (free tier at https://rushdb.com)
- `sentence-transformers` for local embeddings (or use OpenAI)

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RUSHDB_API_TOKEN

# Seed the database with sample research data
python seed.py
```

## Running the Tutorial

```bash
python main.py
```

The tutorial walks through five key patterns:

### 1. Research Entity Modeling

Create typed records for research artifacts with rich properties:

```sdk
paper = db.records.create(
    label="PAPER",
    data={
        "title": "Attention Is All You Need",
        "abstract": "We propose a new simple network architecture...",
        "authors": ["Vaswani et al."],
        "year": 2017
    }
)
___SPLIT___
const paper = await db.records.create({
  label: 'PAPER',
  data: {
    title: 'Attention Is All You Need',
    abstract: 'We propose a new simple network architecture...',
    authors: ['Vaswani et al.'],
    year: 2017
  }
})
```

### 2. Building the Citation Graph

Link papers with typed relationships:

```sdk
db.records.attach(
    source=citing_paper,
    target=referenced_paper,
    options={"type": "CITES"}
)

db.records.attach(
    source=claim,
    target=supporting_evidence,
    options={"type": "SUPPORTED_BY"}
)

db.records.attach(
    source=claim_a,
    target=claim_b,
    options={"type": "CONTRADICTS"}
)
___SPLIT___
await db.records.attach({
  source: citingPaper,
  target: referencedPaper,
  options: { type: 'CITES' }
})

await db.records.attach({
  source: claim,
  target: supportingEvidence,
  options: { type: 'SUPPORTED_BY' }
})

await db.records.attach({
  source: claimA,
  target: claimB,
  options: { type: 'CONTRADICTS' }
})
```

### 3. Graph Traversal for Context Building

Walk the graph to gather relevant research context:

```sdk
# Find all claims that support a hypothesis
supporting_claims = db.records.find({
    "labels": ["CLAIM"],
    "where": {
        "HYPOTHESIS": {"$id": hypothesis.id},
        "$relation": {"type": "SUPPORTS", "direction": "out"}
    }
})

# Find papers that cite the same source (bibliographic coupling)
related_papers = db.records.find({
    "labels": ["PAPER"],
    "where": {
        "PAPER": {
            "$relation": {"type": "CITES", "direction": "out"},
            "__id": referenced_source.id
        }
    }
})
___SPLIT___
// Find all claims that support a hypothesis
const supportingClaims = await db.records.find({
  labels: ['CLAIM'],
  where: {
    HYPOTHESIS: { $id: hypothesis.id },
    $relation: { type: 'SUPPORTS', direction: 'out' }
  }
})

// Find papers that cite the same source
const relatedPapers = await db.records.find({
  labels: ['PAPER'],
  where: {
    PAPER: {
      $relation: { type: 'CITES', direction: 'out' },
      __id: referencedSource.id
    }
  }
})
```

### 4. Semantic Search on Research Content

Create a vector index on paper abstracts and search semantically:

```sdk
# Create external index (you provide vectors)
index = db.ai.indexes.create({
    "label": "PAPER",
    "propertyName": "abstract",
    "sourceType": "external",
    "dimensions": 384,
    "similarityFunction": "cosine"
})

# Upsert vectors for existing papers
db.ai.indexes.upsert_vectors(index.id, {
    "items": [
        {"recordId": paper.id, "vector": embedding}
        for paper in papers
    ]
})

# Semantic search
results = db.ai.search({
    "propertyName": "abstract",
    "query": "neural network architecture innovations",
    "labels": ["PAPER"],
    "limit": 5
})
___SPLIT___
// Create external index
const index = await db.ai.indexes.create({
  label: 'PAPER',
  propertyName: 'abstract',
  sourceType: 'external',
  dimensions: 384,
  similarityFunction: 'cosine'
})

// Semantic search
const results = await db.ai.search({
  propertyName: 'abstract',
  query: 'neural network architecture innovations',
  labels: ['PAPER'],
  limit: 5
})
```

### 5. Transactions for Research Workflows

Atomically create research artifacts with their relationships:

```sdk
with db.transactions.begin() as tx:
    # Create a new finding
    finding = db.records.create(
        label="FINDING",
        data={"text": "Model X outperforms baseline by 15%", "confidence": 0.92},
        transaction=tx
    )
    
    # Link to supporting evidence
    evidence = db.records.create(
        label="EVIDENCE",
        data={"source": "Table 3 in paper", "statistic": "accuracy=0.87"},
        transaction=tx
    )
    
    db.records.attach(
        source=finding,
        target=evidence,
        options={"type": "EXTRACTED_FROM"}
    )
    # Auto-commits on clean exit
___SPLIT___
const tx = await db.transactions.begin()
try {
  const finding = await db.records.create({
    label: 'FINDING',
    data: { text: 'Model X outperforms baseline by 15%', confidence: 0.92 }
  }, tx)
  
  const evidence = await db.records.create({
    label: 'EVIDENCE',
    data: { source: 'Table 3 in paper', statistic: 'accuracy=0.87' }
  }, tx)
  
  await db.records.attach({
    source: finding,
    target: evidence,
    options: { type: 'EXTRACTED_FROM' }
  })
  
  await tx.commit()
} catch (e) {
  await tx.rollback()
  throw e
}
```

## Expected Output

When you run `main.py`, you'll see:

```
=== Graph-Backed Research Assistant Tutorial ===

[1] Research Entity Modeling
  ✓ Created PAPER: Attention Is All You Need
  ✓ Created CLAIM: Transformers enable parallelization
  ✓ Created HYPOTHESIS: Attention mechanisms capture long-range dependencies

[2] Building the Citation Graph
  ✓ Connected papers with CITES relationships
  ✓ Linked claims to evidence with SUPPORTED_BY
  ✓ Found contradicting claims with CONTRADICTS

[3] Graph Traversal for Context
  ✓ Found 3 claims supporting hypothesis
  ✓ Found 2 papers in bibliographic coupling
  ✓ Built context tree with 5 hops

[4] Semantic Search on Research
  ✓ Created vector index on PAPER.abstract
  ✓ Indexed 10 papers with embeddings
  ✓ Semantic search found: [Transformer Architecture Advances]

[5] Transactions for Research Workflows
  ✓ Atomic creation of FINDING + EVIDENCE
  ✓ Verified relationship integrity

=== Tutorial Complete ===

All RushDB operations shown above use the Python SDK.
See https://github.com/rush-db/examples/tree/main/building-a-graph-backed-autonomous-research-assist-tutorial
```

## Architecture Overview


```
┌─────────────────────────────────────────────────────────────────┐
│                    Research Assistant                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐ │
│  │  Query    │   │  Context  │   │  Action   │   │  Memory   │ │
│  │  Handler  │──▶│  Builder   │──▶│  Planner  │──▶│  Store    │ │
│  └───────────┘   └───────────┘   └───────────┘   └───────────┘ │
│       │                                    │                    │
│       │              ┌────────────────────┘                    │
│       │              ▼                                         │
│       │     ┌───────────────────────┐                           │
│       │     │      RushDB          │                           │
│       │     │  ┌─────────────────┐ │                           │
│       │     │  │ Property Graph  │ │                           │
│       │     │  │   (Neo4j)       │ │                           │
│       │     │  └─────────────────┘ │                           │
│       │     │  ┌─────────────────┐ │                           │
│       │     │  │ Vector Index    │ │                           │
│       │     │  │  (Neo4j)       │ │                           │
│       │     │  └─────────────────┘ │                           │
│       │     └───────────────────────┘                           │
│       └─────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

## Key Takeaways

1. **Graph > Flat Storage**: Research relationships (citations, support, contradiction) are first-class citizens
2. **Traversable Context**: Walk the graph to build rich context for LLM prompts
3. **Semantic + Structured**: Combine vector search with graph queries for hybrid retrieval
4. **Transactional Integrity**: Group related research artifacts atomically
5. **Pay for Writes**: RushDB charges per write (KnowledgeUnits) — reads are free

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Data Modeling Best Practices](https://docs.rushdb.com/concepts)
- [Vector Search Integration](https://docs.rushdb.com/ai-search)
