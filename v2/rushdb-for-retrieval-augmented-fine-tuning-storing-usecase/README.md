# RushDB for Retrieval-Augmented Fine-Tuning

## Storing and Querying Training Examples with Graph + Vector Storage

**Use case:** Building a retrieval-augmented fine-tuning (RALT) pipeline where structured training examples are stored with rich relationships and semantically queried for model training.

---

## The Problem with Fragmented Storage

Most RAG fine-tuning pipelines duct-tape together multiple systems:

| Component | Storage Solution | Drawback |
|-----------|-------------------|----------|
| Raw training examples | S3 / blob storage | No querying, must download entire dataset |
| Vector embeddings | Pinecone / Weaviate / Qdrant | Cannot express graph relationships |
| Metadata & labels | PostgreSQL / BigQuery | No vector search, schema rigidity |
| Relationships | Manual foreign keys | No traversal queries |

This fragmentation leads to:
- **Sync complexity** — embeddings drift when examples update
- **Join gymnastics** — matching examples to source documents across systems
- **Brittle pipelines** — multiple failure points between systems


## The RushDB Solution

RushDB provides unified graph + vector storage as a single layer:

```
┌─────────────────────────────────────────────────────┐
│                    RushDB                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Neo4j     │  │   Vectors  │  │  Graph      │  │
│  │  (storage)  │  │  (indexed) │  │  (traversal)│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
```

- Store training examples as graph nodes with full metadata
- Link to source documents, task definitions, and categories via edges
- Query using vector similarity **combined** with graph filters
- All in one API, one SDK, one billing unit (KnowledgeUnits)


---

## What This Demo Shows

1. **Ingest** — Store training examples with rich metadata (source, timestamp, label confidence, user feedback)
2. **Relate** — Link examples to source documents and fine-tuning task definitions via graph edges
3. **Index** — Create vector embeddings for semantic search
4. **Query** — Retrieve batches using combined vector similarity + graph traversal
5. **Fine-tune loop** — Demonstrate batching for a training iteration

---

## Prerequisites

- Python 3.9+
- RushDB account with API key ([sign up free](https://rushdb.com))
- `sentence-transformers` for embeddings (or use RushDB's managed embedding API)

---

## Setup

```bash
# 1. Clone the examples repo
git clone https://github.com/rush-db/examples.git
cd rushdb-for-retrieval-augmented-fine-tuning-storing-usecase

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set your RUSHDB_API_KEY
```

## Environment Variables

```bash
RUSHDB_API_KEY=your_api_key_here     # Required: RushDB API key
RUSHDB_URL=https://api.rushdb.com    # Optional: for self-hosted instances
EMBEDDING_MODEL=all-MiniLM-L6-v2     # Optional: embedding model (default: all-MiniLM-L6-v2)
```

---

## Running the Demo

### Step 1: Seed Mock Training Data

```bash
python seed.py
```

This generates 50 synthetic training examples across three domains:
- **Customer Support** — FAQ responses, ticket resolutions
- **Code Generation** — Docstrings, unit tests, refactoring suggestions
- **Data Analysis** — SQL query generation, report summaries


Each example is linked to:
- A `SourceDocument` (the origin text or document)
- A `FineTuningTask` (which task this example trains for)
- A `Category` (for stratified sampling)


### Step 2: Run the Main Demo

```bash
python main.py
```

The script demonstrates:

```
=== Demo 1: Semantic Search for Similar Examples ===
Query: "How do I reset my password"
→ Found similar example: "User asks about account access and password issues"
   Score: 0.847, Confidence: 0.92, Label: positive, Feedback: accepted

=== Demo 2: Graph-Traversal Query (High Confidence + Manual Label) ===
→ Found 2 examples matching criteria:
   - ID: ..., Source: knowledge_base, Confidence: 0.95, Feedback: accepted
   - ID: ..., Source: documentation, Confidence: 0.98, Feedback: accepted

=== Demo 3: Combined Vector + Graph Query ===
Query: "API authentication errors"
Filters: source_type=documentation, confidence>=0.8
→ Found 1 example:
   - ID: ..., Task: code_generation, Confidence: 0.87, Feedback: accepted

=== Demo 4: Batch Retrieval for Fine-Tuning Loop ===
Batching strategy: stratified_sampling
Batch size: 6 examples
→ Batch 1:
   - customer_support: 2 examples (avg confidence: 0.84)
   - code_generation: 2 examples (avg confidence: 0.91)
   - data_analysis: 2 examples (avg confidence: 0.88)
```

---

## Key Code Patterns

### Storing Training Examples

```sdk
# Create a training example with rich metadata
example = db.records.create(
    label="TrainingExample",
    data={
        "instruction": "How do I reset my password?",
        "input": "",
        "output": "To reset your password, go to Settings > Security > Reset Password.",
        "source": "knowledge_base",
        "source_document_id": "doc_123",
        "timestamp": "2024-01-15T10:30:00Z",
        "label_confidence": 0.92,
        "label": "positive",
        "user_feedback": "accepted",
        "task_id": "task_customer_support"
    }
)
___SPLIT___
// TypeScript equivalent
const example = await db.records.create({
    label: "TrainingExample",
    data: {
        instruction: "How do I reset my password?",
        input: "",
        output: "To reset your password, go to Settings > Security > Reset Password.",
        source: "knowledge_base",
        source_document_id: "doc_123",
        timestamp: "2024-01-15T10:30:00Z",
        label_confidence: 0.92,
        label: "positive",
        user_feedback: "accepted",
        task_id: "task_customer_support"
    }
})
```

### Linking Examples to Documents and Tasks

```sdk
# Attach example to source document
db.records.attach(
    source=example,
    target=source_doc,
    options={"type": "DERIVED_FROM", "direction": "out"}
)

# Attach example to fine-tuning task
db.records.attach(
    source=example,
    target=task,
    options={"type": "TRAINS_FOR", "direction": "out"}
)
___SPLIT___
// TypeScript equivalent
await db.records.attach({
    source: example,
    target: source_doc,
    options: { type: "DERIVED_FROM", direction: "out" }
})

await db.records.attach({
    source: example,
    target: task,
    options: { type: "TRAINS_FOR", direction: "out" }
})
```

### Creating a Vector Index

```sdk
# External index: you supply pre-computed embeddings
index = db.ai.indexes.create({
    "label": "TrainingExample",
    "propertyName": "instruction",
    "sourceType": "external",
    "dimensions": 384,
    "similarityFunction": "cosine"
})
___SPLIT___
// TypeScript equivalent
const index = await db.ai.indexes.create({
    label: "TrainingExample",
    propertyName: "instruction",
    sourceType: "external",
    dimensions: 384,
    similarityFunction: "cosine"
})
```

### Semantic Search with Graph Filters

```sdk
# Find examples similar to query, filtered by graph relationships
results = db.ai.search({
    "propertyName": "instruction",
    "query": "API authentication errors",
    "labels": ["TrainingExample"],
    "where": {
        "$or": [
            {"label_confidence": {"$gte": 0.8}},
            {"user_feedback": "accepted"}
        ]
    },
    "limit": 10
})
___SPLIT___
// TypeScript equivalent
const results = await db.ai.search({
    propertyName: "instruction",
    query: "API authentication errors",
    labels: ["TrainingExample"],
    where: {
        $or: [
            { label_confidence: { $gte: 0.8 } },
            { user_feedback: "accepted" }
        ]
    },
    limit: 10
})
```

### Batching for Fine-Tuning Loop

```sdk
# Get diverse batch for training iteration
def get_training_batch(db, batch_size=8, strategy="stratified"):
    """Retrieve a batch of examples for fine-tuning."""
    
    # Get task distribution from existing examples
    tasks = db.labels.find({"where": {"label": "FineTuningTask"}})
    
    # For each task, get highest-confidence examples
    batch = []
    per_task = batch_size // len(tasks)
    
    for task in tasks:
        examples = db.records.find({
            "labels": ["TrainingExample"],
            "where": {
                "FineTuningTask": {"$relation": {"type": "TRAINS_FOR", "direction": "in"}},
                "label_confidence": {"$gte": 0.7},
                "user_feedback": {"$in": ["accepted", "reviewed"]}
            },
            "limit": per_task,
            "orderBy": {"label_confidence": "desc"}
        })
        batch.extend(examples)
    
    return batch
```

---

## Data Model

```
┌───────────────────┐       DERIVED_FROM       ┌───────────────────┐
│  TrainingExample  │─────────────────────────▶│   SourceDocument  │
│                   │                           │                   │
│  - instruction    │       TRAINS_FOR         │  - content        │
│  - input          │◀─────────────────────────│  - source_type    │
│  - output         │                           │  - author         │
│  - label_confidence│      BELONGS_TO          │  - url            │
│  - user_feedback  │─────────────────────────▶│                   │
└───────────────────┘         ┌─────────────────┘                   │
                              │                                     │
                              ▼                                     │
                    ┌───────────────────┐                           │
                    │   FineTuningTask  │                           │
                    │                   │   PART_OF                 │
                    │  - name           │◀──────────────────────────┘
                    │  - target_model   │
                    │  - status         │
                    └───────────────────┘
```

---

## Pricing Note

RushDB charges by **KnowledgeUnits (KU)** — only on write operations:

| Operation | KU |
|-----------|----|
| Record created | 0.5 KU |
| Property stored | 1 KU |
| Relationship | 0.25 KU |
| Embedding generated | 5 KU |
| Vector search | 5 KU |
| Reads | **Free** |


The Free tier includes 100K KU/month — sufficient for most fine-tuning pipelines.

---

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB SDK Reference](https://docs.rushdb.com/sdk/python)
- [Pricing](https://rushdb.com/pricing)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/rushdb-for-retrieval-augmented-fine-tuning-storing-usecase)

---

## License

MIT License - feel free to use this code in your own projects.
