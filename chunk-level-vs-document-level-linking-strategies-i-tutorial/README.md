# Chunk-Level vs Document-Level Linking Strategies in RushDB

A practical tutorial demonstrating two fundamental graph modeling approaches for hierarchical data in RushDB — using a knowledge base as the real-world context.

## What This Tutorial Covers

- **Document-Level Linking**: Entire documents linked to each other (author, category, related)
- **Chunk-Level Linking**: Granular content chunks linked to parent documents AND cross-referenced with other chunks
- **Hybrid Approach**: Combining both strategies for complex information systems
- **Query patterns** that exploit each linking strategy

## Scenario

We model a technical documentation system with:
- `Article` records (top-level documents)
- `Section` records (major sections within articles)
- `Paragraph` records (individual content chunks)

### Document-Level Strategy

- Articles link to other articles (related, authored_by)
- Sections link to their parent article
- Query focus: navigation, taxonomy, authorship

### Chunk-Level Strategy

- Paragraphs link to parent sections and sibling paragraphs
- Cross-references between related content (even across articles)
- Query focus: granular traversal, content similarity, precise retrieval

## Prerequisites

- Python 3.10+
- RushDB account (free tier works)
- `rushdb>=2.0.0`

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Tutorial

```bash
# Seed the database with sample knowledge base
python seed.py

# Run the main tutorial (demonstrates both strategies)
python main.py
```

**Note**: `seed.py` is idempotent — run it multiple times safely. It detects existing data and skips re-seeding.

## Project Structure

```
chunk-level-vs-document-level-linking-strategies-i-tutorial/
├── README.md          # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Mock data generator
└── main.py             # Tutorial demonstration
```

## Expected Output

The tutorial produces structured output showing:

1. **Document-level traversal** — navigating article hierarchies
2. **Chunk-level traversal** — walking through sections and paragraphs
3. **Cross-document chunk links** — related content across article boundaries
4. **Comparison queries** — performance and utility of each approach

## Key Takeaways

| Strategy | Best For |
|----------|----------|
| **Document-Level** | Navigation, taxonomy, browsing, authorship tracking |
| **Chunk-Level** | RAG pipelines, fine-grained retrieval, content similarity |
| **Hybrid** | Complex systems requiring both navigation and granular access |

## Resources

- RushDB Docs: https://docs.rushdb.com
- GitHub: https://github.com/rush-db/examples/tree/main/chunk-level-vs-document-level-linking-strategies-i-tutorial
