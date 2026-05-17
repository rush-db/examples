# Graph-Based Hallucination Detection: Connecting Facts to Source Nodes

A production-ready pipeline demonstrating how RushDB's unified graph+vector model enables fine-grained hallucination detection with full provenance tracing.

## What This Project Demonstrates

Most RAG systems score the entire LLM output with a single relevance metric — a blunt instrument that can't identify *which* claims are hallucinated. This example shows a claim-level evaluation approach where:

1. **Ingestion**: Documents are chunked, embedded, and stored with explicit `SOURCED_FROM` edges to source nodes
2. **Generation**: An answer is synthesized from the knowledge base (simulated here)
3. **Extraction**: Claims are parsed from the answer as subject-predicate-object triples
4. **Validation**: Each claim is checked against the vector store — if no matching source exists above a similarity threshold, the claim fails
5. **Diagnosis**: Failed claims are traced back to identify which provenance edges are missing

## Architecture Comparison

### The Three-System Stitching Approach (What Most Teams Maintain)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Vector DB  │────▶│  LLM Proxy  │────▶│  Graph DB   │
│  (embed+    │     │  (evaluate  │     │  (store     │
│  retrieve)  │     │  claims)    │     │  provenance)│
└─────────────┘     └─────────────┘     └─────────────┘
    ▲                    │                    │
    └────────────────────┴────────────────────┘
           Expensive data movement, sync errors, three APIs
```

### The RushDB Approach (This Pipeline)

```
┌──────────────────────────────────────────────┐
│                   RushDB                      │
│  ┌────────────┐  ┌────────────┐  ┌─────────┐  │
│  │  Records   │  │  Vectors   │  │  Graph  │  │
│  │  (chunks)  │  │  (indexed) │  │  (edges)│  │
│  └────────────┘  └────────────┘  └─────────┘  │
└──────────────────────────────────────────────┘
                       │
                       ▼
              Single SDK, unified model
```

## Prerequisites

- Python 3.10+
- RushDB account and API key ([Get one](https://docs.rushdb.com))
- `sentence-transformers` for embeddings

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

3. **Seed the knowledge base**:
   ```bash
   python seed.py
   ```
   This creates:
   - 3 source documents (articles about renewable energy)
   - 12 chunk nodes (3-4 chunks per document)
   - Vector embeddings for each chunk
   - `SOURCED_FROM` edges connecting chunks to documents

4. **Run the detection pipeline**:
   ```bash
   python main.py
   ```

## Expected Output

```
=== Hallucination Detection Pipeline ===

📄 Loaded 3 source documents with 12 chunks

--- Generated Answer ---
"Solar panels installed on agricultural land can boost crop yields by up to 30%.
This dual-use approach, known as agrivoltaics, has been shown to reduce water
consumption by 40%. The technology was first developed in Japan in 2004."

--- Claim Extraction ---
1. [SUBJECT] solar panels on agricultural land  [PREDICATE] can boost crop yields [OBJECT] by up to 30%
2. [SUBJECT] agrivoltaics  [PREDICATE] reduces water consumption [OBJECT] by 40%
3. [SUBJECT] the technology  [PREDICATE] was first developed [OBJECT] in Japan in 2004

--- Validation Results ---

✅ Claim 1 VERIFIED (similarity: 0.873)
   Source: NREL Study 2021 (solar+agriculture study)
   Chunk: "...solar panels installed above crops can increase yields by 20-30%..."

✅ Claim 2 VERIFIED (similarity: 0.891)
   Source: Fraunhofer Report (agrivoltaics systems)
   Chunk: "...crop water requirements drop by 30-50% under agrivoltaic installations..."

❌ Claim 3 FAILED (best similarity: 0.412)
   Evidence gap: No chunk confirms Japan or 2004 origin
   Possible causes:
   - Missing source: this fact may not exist in the knowledge base
   - Conflicting sources: multiple documents contradict this claim

=== Summary ===
Verified: 2/3 claims (66.7%)
Failed: 1/3 claims
Overall confidence: LOW - answer requires revision
```

## How It Works

### 1. Document Ingestion

```sdk
# Create a source document node
source_doc = db.records.create(
    label="DOCUMENT",
    data={"title": "NREL Study 2021", "url": "https://...", "content": "..."}
)

# Create chunk nodes with embedded vectors
chunk = db.records.create(
    label="CHUNK",
    data={"text": "solar panels installed above crops...", "chunk_index": 0},
    vectors=[{"propertyName": "text", "vector": embedding}]
)

# Connect chunk to source via edge
db.records.attach(source=chunk, target=source_doc, options={"type": "SOURCED_FROM"})
___SPLIT___
// Create a source document node
const sourceDoc = await db.records.create({
  label: 'DOCUMENT',
  data: { title: 'NREL Study 2021', url: 'https://...', content: '...' }
})

// Create chunk nodes with embedded vectors
const chunk = await db.records.create({
  label: 'CHUNK',
  data: { text: 'solar panels installed above crops...', chunkIndex: 0 },
  vectors: [{ propertyName: 'text', vector: embedding }]
})

// Connect chunk to source via edge
await db.records.attach({ source: chunk, target: sourceDoc, options: { type: 'SOURCED_FROM' } })
```

### 2. Claim Validation via Vector Similarity

```sdk
# For each claim, search for matching chunks
results = db.ai.search({
    "propertyName": "text",
    "query": claim_text,
    "labels": ["CHUNK"],
    "limit": 3
})

# If best similarity < threshold, the claim is hallucinated
if results[0].score < 0.7:
    mark_as_hallucination(claim)
___SPLIT___
// For each claim, search for matching chunks
const results = await db.ai.search({
  propertyName: 'text',
  query: claimText,
  labels: ['CHUNK'],
  limit: 3
})

// If best similarity < threshold, the claim is hallucinated
if (results[0].score < 0.7) {
  markAsHallucination(claim)
}
```

### 3. Provenance Tracing

```sdk
# Find the source document for a failed claim's best-matching chunk
source_docs = db.records.find({
    "labels": ["DOCUMENT"],
    "where": {
        "CHUNK": {"$relation": {"type": "SOURCED_FROM", "direction": "in"}},
        "__id": best_chunk.id
    }
})
___SPLIT___
// Find the source document for a failed claim's best-matching chunk
const sourceDocs = await db.records.find({
  labels: ['DOCUMENT'],
  where: {
    CHUNK: { $relation: { type: 'SOURCED_FROM', direction: 'in' } },
    __id: bestChunk.id
  }
})
```

## Key Files

| File | Purpose |
|------|---------|
| `seed.py` | Populates RushDB with source documents, chunks, and vectors |
| `main.py` | Runs the complete hallucination detection pipeline |
| `claims.py` | Simple claim extraction and validation logic |

## Adjusting Sensitivity

The similarity threshold (default: 0.65) can be tuned:
- **Higher** (0.75+): Fewer false positives, more hallucinations slip through
- **Lower** (0.50-0.60): Catches more hallucinations, more false alarms

## When Hallucinations Are Detected

The system provides actionable feedback:

1. **Missing source**: No chunk matches at all → add relevant document to knowledge base
2. **Conflicting source**: Chunk exists but with contradictory info → review and update source
3. **Weak match**: Chunk partially supports claim → the LLM needs better retrieval

This targeted diagnosis enables surgical fixes rather than full pipeline re-runs.

---

Related resources:
- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graph Model](https://docs.rushdb.com/concepts/property-graph)
- [Vector Search Guide](https://docs.rushdb.com/guides/vector-search)
