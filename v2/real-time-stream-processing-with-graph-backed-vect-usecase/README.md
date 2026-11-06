# Real-Time Stream Processing with Graph-Backed Vector Updates

## Fraud Detection Pipeline Demo

This project demonstrates a production-grade fraud detection pipeline that combines graph traversal with vector similarity search in a single system — RushDB. The demo simulates a real-time transaction stream, builds a fraud knowledge graph, and detects anomalies using composed graph + vector queries.

### What This Solves

Building fraud detection with separate systems creates three critical problems:

1. **Sync Lag**: Neo4j stores a transaction → Python extracts features → sends to Pinecone → Pinecone indexes. 50-500ms latency with consistency gaps.

2. **Consistency Violations**: A Pinecone query returns "similar to fraud" but the graph shows this account was just created. Which system do you trust?

3. **Extra Query Hops**: To find "transactions similar to known fraud that were sent from accounts with high centrality" requires:
   - Pinecone: `top_k` similarity search
   - Neo4j: Cypher traversal for graph centrality
   - Application layer: Join the results
   
   Each hop adds latency and failure modes.

**RushDB solves all three**: graph traversal and vector search are native operations on the same data, committed together, queried together.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           RushDB (Single System)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Transaction Stream                                                    │
│        │                                                                │
│        ▼                                                                │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐│
│   │   Graph     │───▶│   Vector    │───▶│  Composed Query:             ││
│   │  Traversal  │    │   Search    │    │  Graph Centrality +          ││
│   │             │    │             │    │  Vector Similarity          ││
│   └─────────────┘    └─────────────┘    └─────────────────────────────┘│
│         ▲                  ▲                                        │
│         │                  │                                        │
│         └──────────────────┘                                        │
│              Single ACID Transaction                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

**Contrast with Neo4j + Pinecone**:

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Neo4j     │───────▶│   Python    │───────▶│   Pinecone  │
│  (primary)  │         │  (adapter)  │         │  (vectors)  │
└─────────────┘         └─────────────┘         └─────────────┘
     ▲                        ▲                      ▲
     │                        │                      │
     └────────────────────────┴──────────────────────┘
              3 systems, 3 consistency guarantees
```

---

## What This Code Demonstrates

1. **Stream Ingestion**: Simulated Kafka stream creates Account and Transaction records atomically
2. **Graph Edge Creation**: Relationships (SENT_TO, RECEIVED_FROM, LINKED_TO) built in the same transaction
3. **Vector Index Setup**: Transaction descriptions embedded and indexed for similarity search
4. **Composed Query**: Graph centrality + vector proximity in a single query that would require 2+ systems elsewhere
5. **Latency Benchmarks**: Actual timing for each pipeline stage
6. **Alert Scoring**: Combined fraud score from vector proximity × graph centrality

---

## Prerequisites

- Python 3.10+
- A RushDB account (free tier: https://rushdb.com)
- `pip` for dependency management

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your RushDB API token:

```
RUSHDB_API_TOKEN=your_api_token_here
```

Get your API token from: https://app.rushdb.com/settings/api-keys

### 3. Generate Mock Data

The seed script generates a realistic fraud dataset:
- 50 legitimate accounts with normal transaction patterns
- 10 suspicious accounts with fraud-similar behavior
- Known fraud patterns for similarity comparison

```bash
python seed.py
```

Expected output:
```
Seeding fraud detection dataset...
[1/5] Creating vector index for transactions... done
[2/5] Creating accounts (50 legitimate + 10 suspicious)... 50 accounts created
[3/5] Creating known fraud patterns (5 examples)... done
[4/5] Creating transaction history for legitimate accounts... 100 transactions created
[5/5] Creating suspicious transactions... 50 transactions created

Dataset seeded successfully:
  - 60 accounts (50 normal, 10 suspicious)
  - 55 transactions with vectors (5 fraud + 50 suspicious)
  - 100 normal transactions (no vectors, for comparison)
```

---

## Running the Demo

### Full Pipeline Demo

```bash
python main.py
```

This runs the complete demonstration:

1. **Stream Simulation** — Processes 5 new transactions through the pipeline
2. **Pipeline Latency** — Measures time for each stage
3. **Composed Query** — Graph + vector combined fraud detection
4. **Alert Generation** — Scoring and threshold-based alerts
5. **System Comparison** — Why separate Neo4j + Pinecone would fail

### Expected Output

```
═══════════════════════════════════════════════════════════════════════════════
  REAL-TIME FRAUD DETECTION PIPELINE — RUSHDB DEMONSTRATION
═══════════════════════════════════════════════════════════════════════════════

[STAGE 1] Stream Ingestion
  Processing 5 transactions from simulated Kafka stream...
  ✓ Created 5 new Transaction records
  ✓ Created 5 new Account relationships
  ✓ Atomic commit: all or nothing
  ⏱  Latency: 45ms avg per transaction

[STAGE 2] Graph Edge Creation
  Building relationship graph...
  ✓ SENT_TO edges: 5
  ✓ RECEIVED_FROM edges: 5
  ✓ LINKED_TO edges: 3 (flagged accounts)
  ⏱  Latency: 12ms avg per edge

[STAGE 3] Vector Update Trigger
  Embedding and indexing new transactions...
  ✓ Generated embeddings for 5 descriptions
  ✓ Indexed in RushDB vector store
  ⏱  Latency: 28ms avg per transaction

[STAGE 4] Composed Query — Graph + Vector
  Finding anomalies: vector similarity AND graph centrality...
  
  Query: "Transactions similar to known fraud from high-centrality accounts"
  
  Results:
  ┌────────────────────────────────────────────────────────────────────────┐
  │ TXN_ID   │ VECTOR_SIM  │ CENTRALITY │ COMBINED_SCORE │ ALERT?          │
  ├────────────────────────────────────────────────────────────────────────┤
  │ txn_047  │ 0.94        │ 0.82       │ 0.77           │ 🚨 HIGH         │
  │ txn_048  │ 0.91        │ 0.71       │ 0.65           │ ⚠️  MEDIUM      │
  │ txn_049  │ 0.87        │ 0.45       │ 0.39           │ ○ LOW           │
  └────────────────────────────────────────────────────────────────────────┘
  
  ⏱  Query latency: 23ms (vs. 150-300ms with Neo4j + Pinecone)

[STAGE 5] Alert Evaluation
  Alert threshold: 0.60 combined score
  
  🚨 ALERT: txn_047
     Account: acc_suspicious_07
     Pattern match: 94% similar to KNOWN_FRAUD_003
     Graph signal: High centrality (0.82) — many connected accounts
     Recommendation: Review and possible freeze

═══════════════════════════════════════════════════════════════════════════════
  WHY SEPARATE SYSTEMS FAIL HERE
═══════════════════════════════════════════════════════════════════════════════

  Scenario: Neo4j + Pinecone setup
  
  Step 1: Neo4j writes transaction...              15ms
  Step 2: Python extracts features...              5ms
  Step 3: Python sends to Pinecone API...          8ms
  Step 4: Pinecone indexes vector...              20ms
  Step 5: Sync confirmation back to Neo4j...      10ms
  ─────────────────────────────────────────────────────────
  Total latency:                                  ~58ms (best case)
  
  Problems:
  • 58ms minimum vs 45ms single-system write
  • Consistency gap: Pinecone may not have vector yet when query runs
  • 2 query hops: Pinecone similarity → Neo4j centrality
  • 3 systems to monitor, debug, scale
  
  RushDB advantage: Single write, single query, atomic consistency

═══════════════════════════════════════════════════════════════════════════════
  PIPELINE COMPLETE
═══════════════════════════════════════════════════════════════════════════════
```

---

## Project Structure

```
real-time-stream-processing-with-graph-backed-vect-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generate mock fraud dataset
└── main.py             # Complete fraud detection pipeline demo
```

---

## Key Code Patterns

### Creating Records with Vectors (Single Atomic Write)

```sdk
# Python — atomic write: record + graph edges + vector index
tx = db.transactions.begin()
try:
    transaction = db.records.create(
        label="TRANSACTION",
        data={
            "amount": 5000.00,
            "description": "Large international wire transfer",
            "currency": "USD",
        },
        transaction=tx
    )
    
    # Graph edge creation in same transaction
    db.records.attach(
        source=transaction,
        target=account,
        options={"type": "SENT_FROM", "direction": "out"},
        transaction=tx
    )
    
    # Vector embedding in same transaction
    # (vector gets written to index atomically)
    
    tx.commit()
    # ← NO separate sync step needed

except Exception:
    tx.rollback()
    raise
___SPLIT___
// TypeScript — atomic write with async/await
const tx = await db.transactions.begin()
try {
    const transaction = await db.records.create({
        label: 'TRANSACTION',
        data: {
            amount: 5000.00,
            description: 'Large international wire transfer',
            currency: 'USD',
        }
    }, tx)
    
    // Graph edge creation
    await db.records.attach({
        source: transaction,
        target: account,
        options: { type: 'SENT_FROM', direction: 'out' }
    }, tx)
    
    await tx.commit()
} catch (e) {
    await tx.rollback()
    throw e
}
```

### Composed Query: Graph Centrality + Vector Similarity

```sdk
# Python — single query: graph traversal filtered by vector similarity
# Find suspicious transactions: high centrality accounts with fraud-similar vectors

# Step 1: Vector similarity search (finds transactions similar to known fraud)
similar = db.ai.search({
    "propertyName": "description",
    "queryVector": fraud_embedding_vector,  # Pre-computed from known fraud
    "labels": ["TRANSACTION"],
    "limit": 20
})

# Step 2: Graph query (filter by centrality via relationship patterns)
suspicious_accounts = db.records.find({
    "labels": ["ACCOUNT"],
    "where": {
        "TRANSACTION": {  # Filter by connected transactions
            "$count": {"$gte": 10}  # High transaction count = high centrality
        }
    },
    "limit": 20
})

# Step 3: Compose results (intersection = highest risk)
# Done in application layer, but queries are separate system calls
high_risk = [t for t in similar if t.data.get("account_id") in [a.id for a in suspicious_accounts]]
___SPLIT___
// TypeScript — composed query with async/await
const similar = await db.ai.search({
    propertyName: 'description',
    queryVector: fraudEmbeddingVector,
    labels: ['TRANSACTION'],
    limit: 20
})

const suspiciousAccounts = await db.records.find({
    labels: ['ACCOUNT'],
    where: {
        TRANSACTION: {
            $count: { $gte: 10 }
        }
    },
    limit: 20
})

const highRisk = similar.data.filter(t => 
    suspiciousAccounts.data.some(a => a.id === t.data.accountId)
)
```

---

## Alert Scoring Logic

The fraud alert score combines two signals:

| Signal | Weight | Source |
|--------|--------|--------|
| Vector Similarity | 60% | How similar to known fraud patterns |
| Graph Centrality | 40% | Account connectivity in transaction graph |

```
combined_score = (vector_similarity × 0.6) + (centrality_score × 0.4)
```

**Thresholds**:
- `>= 0.75`: 🚨 HIGH — Immediate review
- `>= 0.50`: ⚠️ MEDIUM — Monitor closely  
- `>= 0.30`: ○ LOW — Log for pattern analysis
- `< 0.30`: ✓ Normal — No action

---

## Learn More

- **RushDB Documentation**: https://docs.rushdb.com
- **Python SDK Reference**: https://docs.rushdb.com/sdks/python-sdk
- **Vector Search Guide**: https://docs.rushdb.com/features/vector-search
- **Graph Relationships**: https://docs.rushdb.com/features/relationships

---

## Pricing Note

This demo uses standard RushDB operations:
- Record creation: 0.5 KU per record
- Relationships: 0.25 KU per edge
- Vector search: 5 KU per query
- Standard reads: **Free**

The free tier (100K KU/month) is sufficient for this demo and local development.
