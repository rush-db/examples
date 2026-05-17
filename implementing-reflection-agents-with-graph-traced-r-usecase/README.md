# Implementing Reflection Agents with Graph-Traced Reasoning

**Topic:** Agentic systems · Debugging · Audit trails  
**Stack:** TypeScript · RushDB (graph memory layer)  
**Repo:** [rush-db/examples](https://github.com/rush-db/examples/tree/main/implementing-reflection-agents-with-graph-traced-r-usecase)

---

## What this example demonstrates

Reflection agents improve their outputs by examining and revising their own reasoning. The problem: without structured introspection, a reflection agent is a black box — you can't see _what_ it observed, _why_ it made a particular critique, or _which_ revision changed the outcome.

**Graph-traced reasoning** solves this by making reasoning paths first-class data in a property graph. Every step — observation, thought, critique, revision, verification — is stored as a typed record with typed edges to its context. The resulting trace is a debugging artifact and an audit trail.

### The reasoning cycle this example implements

```
Input → Observation → Thought → Critique
                              ↓ (if failed)
                           Revision → Verification → Output
```

### Graph model

| Node label   | Role                                                              |
| ------------ | ----------------------------------------------------------------- |
| `INPUT`      | The raw problem statement or document                              |
| `OBSERVATION`| The agent's parsing of the input — what it _saw_                  |
| `THOUGHT`    | The initial response generation                                     |
| `CRITIQUE`   | A structured review finding a specific flaw                        |
| `REVISION`   | A targeted change to the thought addressing a critique             |
| `VERIFICATION`| The pass/fail check after a revision                              |

| Edge type      | Meaning                                                       |
| -------------- | ------------------------------------------------------------- |
| `OBSERVED`     | This INPUT was the source of this OBSERVATION                   |
| `GENERATED`    | This OBSERVATION led to this THOUGHT                            |
| `CRITIQUED`    | This THOUGHT was reviewed and produced this CRITIQUE             |
| `ADDRESSES`    | This REVISION fixes the issue described in this CRITIQUE         |
| `REVISED`      | This REVISION replaced this THOUGHT                              |
| `VERIFIED`     | This REVISION passed this VERIFICATION                           |

### Why targeted revision instead of full re-generation?

The graph tells you exactly which thought failed and why. A critique targets a specific flaw — the corresponding revision patches only that flaw. You don't re-run the entire pipeline; you surgically update the failing node and re-verify.

---

## Prerequisites

- **Node.js** ≥ 18
- **npm** or **pnpm**
- A **RushDB** project (free tier works). Create one at [rushdb.com](https://rushdb.com)

---

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required: your RushDB API key (from https://app.rushdb.com/settings/api-keys)
RUSHDB_API_KEY=your_api_key_here

# Optional: custom self-hosted endpoint
# RUSHDB_URL=https://your-host/api/v1
```

### 3. Seed test data

```bash
npx ts-node seed.ts
```

This creates a set of INPUT documents that the reflection agent will process. The seeding is idempotent — safe to run twice.

---

## Run the example

```bash
npx ts-node main.ts
```

**Expected output (abbreviated):**

```
=== Reflection Agent: Graph-Traced Reasoning ===

--- Processing: Invoice document --- 
  Step 1/5: OBSERVED → stored as RECORD (id: 01JD...)
  Step 2/5: Generated initial THOUGHT (id: 01JD...)
  Step 3/5: CRITIQUED → found 1 flaw(s)
  Step 4/5: REVISED thought (id: 01JD...)
  Step 5/5: VERIFIED → passed ✓
  Final output: Invoice analysis complete with 2 line items totaling $174.50

--- Processing: Support ticket --- 
  Step 1/5: OBSERVED → stored as RECORD (id: 01JD...)
  Step 2/5: Generated initial THOUGHT (id: 01JD...)
  Step 3/5: CRITIQUED → found 2 flaw(s), iterating...
  Step 4/5: REVISION 1 (addresses: hallucinated_order_id)
  Step 4/5: REVISION 2 (addresses: missing_sentiment_analysis)
  Step 5/5: VERIFIED → passed ✓
  Final output: Support priority: HIGH — category: REFUND_REQUEST

--- Processing: Technical doc --- 
  Step 1/5: OBSERVED → stored as RECORD (id: 01JD...)
  Step 2/5: Generated initial THOUGHT (id: 01JD...)
  Step 3/5: CRITIQUED → found 1 flaw(s)
  Step 4/5: REVISED thought (id: 01JD...)
  Step 5/5: VERIFIED → passed ✓
  Final output: API maintenance required: deprecation notice → sunset date: 2025-12-31

=== All traces available in RushDB ===
```

---

## Inspect the traces

Because all reasoning steps are stored as graph records, you can query them:

```typescript
// Find all critiques for a specific input
db.records.find({
  labels: ['CRITIQUE'],
  where: {
    INPUT: { title: 'Invoice document' }
  }
})

// Find all thoughts and their revisions for an input
db.records.find({
  labels: ['THOUGHT', 'REVISION'],
  where: { inputId: '...' }
})

// Get the full reasoning chain for any record
const observation = db.records.findOne({ labels: ['OBSERVATION'], where: { inputId: '...' } })
const thought = db.records.find({ labels: ['THOUGHT'], where: { observationId: observation.id } })
const critiques = db.records.find({ labels: ['CRITIQUE'], where: { thoughtId: thought.id } })
const revisions = db.records.find({ labels: ['REVISION'], where: { critiqueId: critiques[0].id } })
```

---

## How the code works

### `ReflectionAgent` class

The agent maintains a `trace` object that mirrors the graph structure. At each step, it:

1. **Observes** — parses the input and stores the parse as an OBSERVATION node
2. **Thinks** — generates an initial response stored as a THOUGHT node
3. **Critiques** — reviews the thought for specific failure modes, stores each as a CRITIQUE node
4. **Revises** — for each critique, generates a targeted patch stored as a REVISION node linked via `ADDRESSES` edge
5. **Verifies** — runs a checklist pass stored as a VERIFICATION node; if it fails, the cycle repeats

Each step creates a RushDB record and a typed edge. The full chain is traversable in both directions.

### Targeted revision logic

Critiques are structured — they carry a `failureMode` field ("incomplete", "incorrect", "hallucinated"). Revisions carry an `addresses` field that matches the critique's ID. The agent does a surgical patch rather than regenerating from scratch:

```typescript
// Before: full re-generation (wasteful, non-auditable)
// After: targeted patch
const revision = {
  addresses: critique.id,        // links to the specific critique
  patch: patchThoughtsContent(originalThought, critique.fixSuggestion),
  failureMode: critique.failureMode
}
```

### Simulated LLM calls

The example uses deterministic pattern-matching to simulate LLM responses. In production, replace the `_simulateLLM` methods with actual API calls. The interface is identical — only the implementation changes.

---

## Key RushDB patterns used

```sdk
// All reasoning steps are first-class records
const observation = await db.records.create({
  label: 'OBSERVATION',
  data: { inputId: input.id, parseTree: parsed, rawLength: text.length }
})

// Typed edges encode the reasoning relationship
await db.records.attach({
  source: thought,
  target: critique,
  options: { type: 'CRITIQUED' }
})

// Transaction wraps the full reasoning step atomically
const tx = await db.transactions.begin()
await db.records.create({ label: 'THOUGHT', data: thoughtData }, tx)
await db.records.attach({ source: observation, target: thought, options: { type: 'GENERATED' } }, tx)
await tx.commit()
___SPLIT___
// All reasoning steps are first-class records
const observation = await db.records.create({
  label: 'OBSERVATION',
  data: { inputId: input.id, parseTree: parsed, rawLength: text.length },
})

// Typed edges encode the reasoning relationship
await db.records.attach({
  source: thought,
  target: critique,
  options: { type: 'CRITIQUED' },
})

// Transaction wraps the full reasoning step atomically
const tx = await db.transactions.begin()
await db.records.create({ label: 'THOUGHT', data: thoughtData }, tx)
await db.records.attach({ source: observation, target: thought, options: { type: 'GENERATED' } }, tx)
await tx.commit()
```

---

## Files

| File           | Purpose                                                        |
| -------------- | -------------------------------------------------------------- |
| `main.ts`      | Entry point — creates inputs, runs the agent, prints results     |
| `agent.ts`     | `ReflectionAgent` class — the full reasoning cycle              |
| `seed.ts`      | Creates INPUT records for the agent to process                  |
| `types.ts`     | TypeScript types for trace nodes, edges, and agent state        |
| `.env.example` | Environment variable template                                   |
| `package.json` | Dependencies and scripts                                        |

---

## Extending this example

**Add real LLM calls:** Replace `_simulateLLMObserve`, `_simulateLLMThink`, etc. with actual API calls to your model provider. The RushDB graph layer stays unchanged.

**Add vector search:** After the agent runs, embed the final output and store the vector. Future queries can retrieve similar reasoning traces:

```typescript
db.records.create({
  label: 'VERIFICATION',
  data: finalOutput,
  vectors: [{ propertyName: 'output', vector: embedding }]
})
```

**Trace analysis:** Query the graph to find patterns — e.g., which failure modes appear most frequently, or which inputs require the most revision cycles.
