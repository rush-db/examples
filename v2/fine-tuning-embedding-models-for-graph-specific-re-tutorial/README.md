# Fine-tuning Embedding Models for Graph-Specific Representation Learning

This project demonstrates how to use RushDB as a memory layer for fine-tuning embedding models on graph-specific tasks. It combines graph-structured data storage with vector embeddings to enable semantic search over domain-specific knowledge graphs.

## What This Tutorial Covers

- **Graph Data Modeling**: Storing structured graph data (papers, authors, topics, citations) in RushDB
- **Embedding Generation**: Creating vector representations using pre-trained sentence transformers
- **Graph-Aware Fine-tuning**: Fine-tuning embeddings using graph structure (node relationships) via contrastive learning
- **Semantic Search**: Querying the knowledge graph with natural language using RushDB's vector similarity search

## Why RushDB for Graph + Embeddings?

RushDB provides a dual-layer architecture that combines:
- **Neo4j** for graph storage and traversal
- **Native vector indexes** for similarity search

This eliminates the need to manage separate graph and vector databases, making it ideal for RAG (Retrieval-Augmented Generation) workflows that require both relationship traversal and semantic search.

## Prerequisites

- Python 3.10+
- A RushDB account (get one at https://rushdb.com)
- `pip` or `uv` for dependency management

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `RUSHDB_API_KEY` - Your RushDB API token
- `RUSHDB_URL` - API endpoint (defaults to cloud: https://api.rushdb.com/api/v1)

### 3. Seed the Database

The seed script generates a sample academic knowledge graph with:
- 50 research papers
- 20 authors
- 10 research topics
- Citation relationships between papers
- Authorship relationships between authors and papers

```bash
python seed.py
```

This will:
1. Check if data already exists (idempotent)
2. Create all nodes and relationships in RushDB
3. Generate base embeddings for paper abstracts
4. Print progress every 100 records

### 4. Run the Tutorial

```bash
python main.py
```

## Project Structure

```
fine-tuning-embedding-models-for-graph-specific-re-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .env                # Your credentials (gitignored)
├── seed.py             # Generates and imports mock academic graph data
├── main.py             # Main tutorial demonstrating fine-tuning workflow
├── config.py           # Configuration settings
└── data/
    └── schema.json     # Graph schema definition
```

## Expected Output

Running `main.py` will demonstrate:

1. **Ontology Exploration**: Display the graph schema from RushDB
2. **Base Embedding Search**: Find papers using pre-trained embeddings
3. **Graph Analysis**: Traverse the citation graph to understand structure
4. **Contrastive Fine-tuning**: Apply graph-aware contrastive learning to embeddings
5. **Fine-tuned Search**: Compare search results before and after fine-tuning

Example output:
```
=== Graph Schema from RushDB ===
Labels: PAPER, AUTHOR, TOPIC
Properties: title, abstract, name, field

=== Base Embedding Search (query: "machine learning transformers") ===
Found 3 papers:
  - [0.892] Attention Is All You Need
  - [0.847] BERT: Pre-training of Deep Bidirectional Transformers
  - [0.823] GPT-3: Language Models are Few-Shot Learners

=== Citation Graph Analysis ===
Most cited paper: Attention Is All You Need (15 citations)
Hottest topic: Machine Learning (12 papers)

=== Fine-tuning with Graph Contrastive Learning ===
Training for 5 epochs...
Epoch 1/5 - Loss: 0.823 - Similar pairs: 85%
Epoch 2/5 - Loss: 0.612 - Similar pairs: 89%
...
Fine-tuning complete!

=== Fine-tuned Semantic Search ===
Now finding papers with graph-aware embeddings...
  - [0.951] Attention Is All You Need (fine-tuned)
  - [0.912] BERT: Pre-training... (fine-tuned)
  
=== Graph-Aware Recommendations ===
Papers similar to "Attention Is All You Need":
  1. BERT: Pre-training... (cited by same authors)
  2. GPT-2: Language Models... (shares topic: NLP)
  3. T5: Text-to-Text... (co-cited frequently)
```

## Key Concepts Demonstrated

### 1. Contrastive Learning on Graphs

The fine-tuning approach uses **graph contrastive learning**:
- **Positive pairs**: Papers that cite each other or share authors
- **Negative pairs**: Randomly sampled papers from different topics
- **Loss**: NT-Xent (Normalized Temperature-scaled Cross Entropy)

This forces the model to learn that:
- Cited papers should have similar embeddings
- Papers by the same author should cluster together
- Topics form distinct embedding regions

### 2. Storing Embeddings in RushDB

Embeddings are stored using RushDB's inline vector writes:

```sdk
db.records.upsert(
    label="PAPER",
    data={"title": paper["title"], "abstract": paper["abstract"]},
    options={"mergeBy": ["title"]},
    vectors=[{"propertyName": "abstract", "vector": embedding}]
)
```

### 3. Hybrid Graph + Vector Search

The workflow combines:
- **Vector search**: `db.ai.search()` for semantic similarity
- **Graph traversal**: `db.records.find()` with relationship filters

This enables queries like: "Find papers similar to X that were written by author Y"

## Extending This Project

To adapt this for your own domain:

1. **Custom Data**: Replace `seed.py` with your graph data
2. **Domain Fine-tuning**: Fine-tune on your specific relationships
3. **Multi-hop Reasoning**: Use RushDB's relationship queries for multi-hop paths
4. **RAG Integration**: Use fine-tuned embeddings in LLM prompts

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph Contrastive Learning (GRACE)](https://arxiv.org/abs/2008.08843)
- [Sentence Transformers](https://sbert.net/)
- [Node2Vec: Scalable Feature Learning for Networks](https://arxiv.org/abs/1607.00653)
