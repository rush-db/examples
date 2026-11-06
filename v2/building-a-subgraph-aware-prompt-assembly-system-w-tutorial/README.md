# Building a Subgraph-Aware Prompt Assembly System with RushDB

A practical guide to building LLM prompt assembly systems that leverage RushDB's graph traversal capabilities for intelligent context retrieval.

## Overview

This project demonstrates how to build a **subgraph-aware prompt assembly system** — a way to construct rich, contextual prompts for LLMs by traversing a knowledge graph stored in RushDB. Instead of flat RAG (Retrieval Augmented Generation), we retrieve interconnected knowledge as subgraphs, preserving relationships and enabling more coherent AI responses.

### What This System Does

1. **Graph-Based Knowledge Storage**: Stores documentation, concepts, and their relationships
2. **Contextual Subgraph Retrieval**: Traverses the graph to gather related context
3. **Prompt Assembly**: Builds structured prompts from retrieved subgraphs
4. **Strategy Patterns**: Demonstrates multiple traversal strategies (breadth-first, depth-first, relevance-weighted)

### Why This Approach

Traditional RAG retrieves individual documents. Subgraph-aware retrieval:
- Preserves **relationships** between concepts
- Enables **multi-hop reasoning** over the knowledge base
- Produces **coherent context** for complex queries
- Supports **structured extraction** of knowledge chains

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Subgraph Query Engine                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ BFS Traversal│  │ DFS Traversal│  │ Hybrid Strategy │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   RushDB Graph                           │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐            │
│  │Concept│───│Concept│───│ Doc  │───│ Topic │            │
│  └──────┘   └──────┘   └──────┘   └──────┘            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Prompt Assembler                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ System Prompt│  │  Context    │  │   User Query    │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    LLM Input                            │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- A RushDB account (get one at https://rushdb.com)
- `rushdb>=2.0.0` Python SDK

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your RushDB credentials:

```env
RUSHDB_API_KEY=your_api_key_here
# For self-hosted deployments, uncomment and configure:
# RUSHDB_URL=https://your-rushdb-instance.com/api/v1
```

### 3. Seed the Knowledge Graph

```bash
python seed.py
```

This creates a sample knowledge graph with:
- **Concepts**: Core technical concepts (e.g., "authentication", "caching")
- **Documents**: Technical articles and tutorials
- **Topics**: Subject areas (e.g., "security", "performance")
- **Relationships**: `DEFINES`, `RELATES_TO`, `BELONGS_TO`, `DEPENDS_ON`

### 4. Run the Examples

```bash
python main.py
```

## Project Structure

```
building-a-subgraph-aware-prompt-assembly-system-w-tutorial/
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── seed.py                # Graph data seeding script
├── main.py                # Main demonstration script
└── data/
    └── graph_schema.json  # Schema reference for the knowledge graph
```

## Key Concepts Demonstrated

### 1. Graph Schema Design

We use four labels with intentional relationships:

| Label     | Purpose                          | Key Properties          |
| --------- | -------------------------------- | ------------------------ |
| `CONCEPT` | Technical concepts/terms         | name, definition, domain |
| `DOCUMENT`| Articles, tutorials, guides      | title, content, type     |
| `TOPIC`   | Subject areas/categories        | name, priority           |
| `EXAMPLE` | Code examples or use cases      | title, code, language    |

### 2. Relationship Types

| Type           | Direction | Purpose                                      |
| -------------- | --------- | -------------------------------------------- |
| `DEFINES`      | Concept → Document | Concept explained in document          |
| `RELATES_TO`   | Any ↔ Any | General relationship between nodes           |
| `BELONGS_TO`   | Any → Topic | Node belongs to a topic category        |
| `DEPENDS_ON`   | Any → Any | Dependency/ prerequisite relationship    |
| `ILLUSTRATES`  | Example → Any | Example demonstrates a concept      |

### 3. Traversal Strategies

#### BFS (Breadth-First Search)
Gathers all immediate neighbors first, then expands. Best for:
- Getting a broad overview of related concepts
- Building comprehensive context quickly

#### DFS (Depth-First Search)
Follows relationships deeply before backtracking. Best for:
- Deep dives into specific topics
- Tracing dependencies to their roots

#### Relevance-Weighted Strategy
Scores and ranks nodes by relevance to query. Best for:
- Prioritizing most relevant context
- Handling large subgraphs efficiently

## Code Examples

### Basic Usage

```sdk
# Initialize the client
from rushdb import RushDB
import os

db = RushDB(os.environ["RUSHDB_API_KEY"])

# Query concepts related to "authentication"
concepts = db.records.find({
    "labels": ["CONCEPT"],
    "where": {
        "name": {"$contains": "auth"}
    }
})

for concept in concepts:
    print(f"Concept: {concept['name']}")
    print(f"Definition: {concept.get('definition', 'N/A')}")
    print()
___SPLIT___
// TypeScript
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Query concepts related to "authentication"
const { data: concepts } = await db.records.find({
    labels: ['CONCEPT'],
    where: {
        name: { $contains: 'auth' }
    }
})

for (const concept of concepts) {
    console.log(`Concept: ${concept.name}`)
    console.log(`Definition: ${concept.definition ?? 'N/A'}`)
    console.log()
}
```

### Building a Subgraph-Aware Prompt

```sdk
# Assemble a prompt with contextual subgraph
def assemble_context_prompt(query: str, topic: str, max_depth: int = 2) -> dict:
    """Build a prompt with context from the knowledge graph."""
    
    # Get primary topic node
    topics = db.records.find({
        "labels": ["TOPIC"],
        "where": {"name": topic}
    })
    
    if not topics:
        return {"prompt": query, "context": []}
    
    topic_node = topics[0]
    context_nodes = []
    
    # BFS traversal: gather related concepts and documents
    with db.transactions.begin() as tx:
        # Get concepts in this topic
        concepts = db.records.find({
            "labels": ["CONCEPT"],
            "where": {
                "BELONGS_TO": {"$id": topic_node.id}
            }
        })
        context_nodes.extend(concepts)
        
        # For each concept, get defining documents
        for concept in concepts[:5]:  # Limit for prompt size
            docs = db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "DEFINES": {"$id": concept.id}
                },
                "limit": 2
            })
            context_nodes.extend(docs)
    
    # Build prompt with context
    context_text = format_subgraph_context(context_nodes)
    prompt = f"""Context from knowledge base:
{context_text}

---

User query: {query}"""
    
    return {"prompt": prompt, "context": context_nodes}
___SPLIT___
// TypeScript
async function assembleContextPrompt(
    query: string,
    topic: string,
    maxDepth: number = 2
): Promise<{ prompt: string; context: any[] }> {
    // Get primary topic node
    const { data: topics } = await db.records.find({
        labels: ['TOPIC'],
        where: { name: topic }
    })
    
    if (!topics.length) {
        return { prompt: query, context: [] }
    }
    
    const topicNode = topics[0]
    const contextNodes: any[] = []
    
    // BFS traversal: gather related concepts and documents
    const tx = await db.transactions.begin()
    
    // Get concepts in this topic
    const { data: concepts } = await db.records.find({
        labels: ['CONCEPT'],
        where: {
            BELONGS_TO: { $id: topicNode.id }
        }
    })
    contextNodes.push(...concepts)
    
    // For each concept, get defining documents
    for (const concept of concepts.slice(0, 5)) {
        const { data: docs } = await db.records.find({
            labels: ['DOCUMENT'],
            where: {
                DEFINES: { $id: concept.id }
            },
            limit: 2
        })
        contextNodes.push(...docs)
    }
    
    await tx.commit()
    
    // Build prompt with context
    const contextText = formatSubgraphContext(contextNodes)
    const prompt = `Context from knowledge base:
${contextText}

---

User query: ${query}`
    
    return { prompt, context: contextNodes }
}
```

## Expected Output

When running `python main.py`, you'll see:

```
=== Subgraph-Aware Prompt Assembly Demo ===

[1] BFS Traversal Strategy
    Found 12 context nodes
    Generated prompt with 3 concepts and 5 documents

[2] DFS Traversal Strategy  
    Found 8 context nodes
    Generated prompt with deep dependency chain

[3] Relevance-Weighted Strategy
    Found 6 highest-scoring nodes
    Generated focused prompt

[4] Topic-Based Assembly
    Security topic context assembled
    Prompt includes auth concepts and best practices

[5] Dependency Chain Assembly
    Extracted full dependency chain for caching
    Assembled ordered context respecting prerequisites
```

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Graph-Based RAG Patterns](https://docs.rushdb.com/patterns)
- [RushDB SDK Reference](https://docs.rushdb.com/sdk/python)

## License

MIT License - See LICENSE file for details.
