# RushDB Property Types for Modeling Agent Belief States

A practical tutorial demonstrating how to use RushDB's property type system to model agent belief states in AI systems.

## What You'll Learn

This tutorial covers the core RushDB property types and how to apply them to model complex belief structures in AI agents:

- **String** — Categorical beliefs, semantic content, text annotations
- **Number** — Confidence scores, probability distributions, numeric metadata
- **Boolean** — Binary states (confirmed, active, verified)
- **Array** — Multi-valued beliefs, tagged categories, evidence lists
- **Object** — Structured belief metadata, nested evidence, provenance chains

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works)
- Your RushDB API key

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY

# Run the tutorial
python main.py
```

## Project Structure

```
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── data/
│   └── beliefs.json    # Sample belief state data
├── seed.py             # Optional: seed initial beliefs
└── main.py             # Main tutorial script
```

## Key Concepts Demonstrated

### 1. Belief Record Structure

Each belief is modeled as a RushDB record with typed properties:

| Property | Type | Purpose |
|----------|------|---------|
| `content` | String | The semantic content of the belief |
| `confidence` | Number | 0.0–1.0 confidence level |
| `status` | String | Belief state (confirmed, hypothesis, doubt) |
| `is_active` | Boolean | Whether belief is currently relevant |
| `tags` | Array | Categorical tags for filtering |
| `metadata` | Object | Structured provenance and evidence |

### 2. Property Types in Action

```sdk
# Create a belief with all property types
belief = db.records.create(
    label="BELIEF",
    data={
        "content": "User prefers dark mode interface",
        "confidence": 0.85,
        "status": "confirmed",
        "is_active": True,
        "tags": ["preference", "ui", "accessibility"],
        "metadata": {
            "source": "direct_feedback",
            "timestamp": "2024-01-15T10:30:00Z",
            "evidence_count": 3,
            "origin_agent": "preference_analyzer"
        }
    }
)
___SPLIT___
// Create a belief with all property types
const belief = await db.records.create({
    label: "BELIEF",
    data: {
        content: "User prefers dark mode interface",
        confidence: 0.85,
        status: "confirmed",
        is_active: true,
        tags: ["preference", "ui", "accessibility"],
        metadata: {
            source: "direct_feedback",
            timestamp: "2024-01-15T10:30:00Z",
            evidence_count: 3,
            origin_agent: "preference_analyzer"
        }
    }
});
```

### 3. Querying by Property Type

```sdk
# Find high-confidence active beliefs
high_confidence = db.records.find({
    "labels": ["BELIEF"],
    "where": {
        "confidence": {"$gte": 0.8},
        "is_active": True,
        "status": "confirmed"
    }
})

# Filter by array membership
ui_beliefs = db.records.find({
    "labels": ["BELIEF"],
    "where": {
        "tags": {"$contains": "ui"}
    }
})
___SPLIT___
// Find high-confidence active beliefs
const highConfidence = await db.records.find({
    labels: ["BELIEF"],
    where: {
        confidence: { $gte: 0.8 },
        is_active: true,
        status: "confirmed"
    }
});

// Filter by array membership
const uiBeliefs = await db.records.find({
    labels: ["BELIEF"],
    where: {
        tags: { $contains: "ui" }
    }
});
```

### 4. Transactions for Atomic Belief Updates

```sdk
# Update belief state atomically
with db.transactions.begin() as tx:
    # Update confidence
    belief.update({"confidence": 0.92}, transaction=tx)
    # Add new evidence tag
    belief.update({"metadata": {"last_verified": "2024-01-20"}}, transaction=tx)
    # No explicit commit - context manager handles it
___SPLIT___
// Update belief state atomically
const tx = await db.transactions.begin();
try {
    // Update confidence
    await belief.update({ confidence: 0.92 }, tx);
    // Add new evidence tag
    await belief.update({ metadata: { last_verified: "2024-01-20" } }, tx);
    await tx.commit();
} catch (e) {
    await tx.rollback();
    throw e;
}
```

## Running the Tutorial

```bash
# Option 1: Run with existing data (if previously seeded)
python main.py

# Option 2: Seed fresh data then run
python seed.py && python main.py
```

## Expected Output

The script demonstrates:
1. Creating belief records with all property types
2. Querying by different type constraints
3. Updating beliefs with type-safe operations
4. Using transactions for atomic state changes
5. Demonstrating RushDB's schema flexibility

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Property Types Reference](https://docs.rushdb.com/properties)
- [RushDB Python SDK](https://docs.rushdb.com/sdks/python)

## Repository

Full code available at: https://github.com/rush-db/examples/tree/main/rushdb-property-types-for-modeling-agent-belief-st-tutorial
