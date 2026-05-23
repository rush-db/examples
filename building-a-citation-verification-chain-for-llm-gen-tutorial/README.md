# Building a Citation Verification Chain for LLM-Generated Content

This project demonstrates how to build a citation verification chain using RushDB's property graph and vector search capabilities. The chain verifies that LLM-generated claims are properly supported by source documents.


## What This Project Demonstrates

- **Source Document Storage**: Store research papers, articles, and source materials as records with vector embeddings
- **Claim Extraction & Linking**: Create claim records and link them to source documents via relationships
- **Semantic Verification**: Use RushDB's AI search to find supporting evidence for claims
- **Citation Graph**: Build a navigable graph of claims → citations → sources
- **Verification Status Tracking**: Track whether each claim has valid citations

## Architecture

```
┌─────────────────┐     CITES      ┌─────────────────┐
│   LLM-Generated │───────────────▶│     Source      │
│     Claim       │                │   Document      │
└─────────────────┘                └─────────────────┘
        │                                   │
        │          CITES                   │
        └──────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- RushDB account (https://rushdb.com)
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

3. **Seed the database** (creates sample sources and claims):
   ```bash
   python seed.py
   ```

## Running the Verification Chain

```bash
python main.py
```

## Expected Output

```
=== Citation Verification Chain ===


📚 Loaded 5 source documents
📝 Loaded 3 LLM-generated claims

--- Verification Results ---

Claim: "Global AI spending will reach $500B by 2027"
  ✅ Status: VERIFIED
  📖 Citations:
    • "Artificial Intelligence Market Report 2024" (paragraph 3)
    • "Enterprise Technology Forecast" (paragraph 1)
  📊 Verification Score: 0.94

Claim: "Transformer architecture was introduced in 2017"
  ✅ Status: VERIFIED
  📖 Citations:
    • "Attention Is All You Need" (abstract)
  📊 Verification Score: 0.96

Claim: "Python is the most popular programming language"
  ⚠️ Status: PARTIALLY SUPPORTED
  📖 Citations:
    • "Stack Overflow Developer Survey 2024" (paragraph 2)
  📊 Verification Score: 0.72

--- Summary ---
Total Claims: 3
Verified: 2
Partially Supported: 1
Unverified: 0
```

## Key RushDB Features Used

- `db.records.create()` - Create source and claim records
- `db.records.attach()` - Link claims to sources via relationships
- `db.ai.search()` - Semantic search for evidence matching
- `db.records.find()` - Query claims and sources
- Transaction support for atomic operations

## Project Structure

```
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── seed.py            # Database seeding script
└── main.py            # Main verification chain
```
