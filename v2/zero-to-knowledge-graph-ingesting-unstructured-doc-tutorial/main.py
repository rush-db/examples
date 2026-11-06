#!/usr/bin/env python3
"""
Zero-to-Knowledge-Graph: Ingesting Unstructured Documents with RushDB

This tutorial demonstrates RushDB's zero-config document ingestion and
immediate relationship querying. Run this to see RushDB in action in < 5 minutes.

Usage:
    python main.py

Prerequisites:
    1. pip install -r requirements.txt
    2. Copy .env.example to .env and add your RUSHDB_API_KEY
"""

import json
import os
import sys
from pathlib import Path

import dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
dotenv.load_dotenv()

# Import RushDB
from rushdb import RushDB

# ============================================================
# CONFIGURATION
# ============================================================

# Load sample documents
DATA_DIR = Path(__file__).parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"

# Embedding model (local, no API key required)
# Using all-MiniLM-L6-v2: fast, good quality, 384 dimensions
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking configuration for reindexing demo
DEFAULT_CHUNK_SIZE = 200  # words
DEFAULT_OVERLAP = 50      # words

# ============================================================
# SAMPLE DATA
# ============================================================

DOCUMENTS = [
    {
        "title": "Understanding Neural Networks",
        "author": {"name": "Dr. Sarah Chen", "affiliation": "MIT"},
        "tags": ["machine-learning", "neural-networks"],
        "sections": [
            {"heading": "Introduction", "content": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes that process information using connectionist approaches."},
            {"heading": "Architecture", "content": "A typical neural network consists of an input layer, hidden layers, and an output layer. Each connection between nodes has a weight that adjusts during learning."},
            {"heading": "Training", "content": "Neural networks learn through backpropagation, adjusting weights to minimize the difference between predicted and actual outputs."}
        ],
        "content": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes that process information using connectionist approaches to computation. Modern neural networks are non-linear statistical data modeling tools used to model complex relationships between inputs and outputs.",
        "published_year": 2024
    },
    {
        "title": "Introduction to Graph Databases",
        "author": {"name": "Prof. James Miller", "affiliation": "Stanford"},
        "tags": ["databases", "graphs"],
        "sections": [
            {"heading": "What is a Graph Database", "content": "A graph database stores data in terms of nodes and edges, representing entities and their relationships respectively."},
            {"heading": "Use Cases", "content": "Graph databases excel at social networks, recommendation engines, fraud detection, and knowledge graphs."},
            {"heading": "Query Languages", "content": "Cypher, Gremlin, and SPARQL are common query languages for graph databases, allowing traversal of complex relationships."}
        ],
        "content": "A graph database stores data in terms of nodes and edges, representing entities and their relationships respectively. This structure allows for efficient querying of highly connected data, making graph databases ideal for applications that require relationship analysis.",
        "published_year": 2023
    },
    {
        "title": "Machine Learning Best Practices",
        "author": {"name": "Dr. Sarah Chen", "affiliation": "MIT"},
        "tags": ["machine-learning", "best-practices"],
        "sections": [
            {"heading": "Data Preparation", "content": "Quality data is crucial. Clean, normalize, and augment your datasets before training models."},
            {"heading": "Model Selection", "content": "Start simple. Begin with baseline models before moving to complex architectures."},
            {"heading": "Evaluation", "content": "Use cross-validation and appropriate metrics. Avoid data leakage in your evaluation pipeline."}
        ],
        "content": "Successfully deploying ML models requires careful attention to data quality, model selection, and evaluation methodology. Best practices include proper data preprocessing, cross-validation, and avoiding common pitfalls like overfitting and data leakage.",
        "published_year": 2024
    },
    {
        "title": "The Rise of Vector Databases",
        "author": {"name": "Dr. Emily Watson", "affiliation": "Google Research"},
        "tags": ["databases", "vectors", "ai"],
        "sections": [
            {"heading": "Vector Similarity", "content": "Vector databases index data by semantic similarity, enabling natural language queries across large document collections."},
            {"heading": "Embeddings", "content": "Text, images, and audio are converted to dense vectors using transformer models, capturing semantic meaning."},
            {"heading": "Applications", "content": "Semantic search, recommendation systems, anomaly detection, and RAG (Retrieval Augmented Generation) pipelines."}
        ],
        "content": "Vector databases have emerged as a critical infrastructure for AI applications, enabling semantic similarity search across embeddings. They power recommendation systems, RAG pipelines, and natural language interfaces to enterprise data.",
        "published_year": 2024
    },
    {
        "title": "Graph Neural Networks Explained",
        "author": {"name": "Dr. Emily Watson", "affiliation": "Google Research"},
        "tags": ["deep-learning", "gnns", "graphs"],
        "sections": [
            {"heading": "Graph Representation", "content": "GNNs operate on graph-structured data, where nodes represent entities and edges represent relationships."},
            {"heading": "Message Passing", "content": "GNNs learn by aggregating information from neighboring nodes, updating node representations iteratively."},
            {"heading": "Applications", "content": "Molecular property prediction, social network analysis, knowledge graph completion, and traffic forecasting."}
        ],
        "content": "Graph Neural Networks (GNNs) extend deep learning to graph-structured data, enabling predictions on molecules, social networks, and knowledge graphs. They learn by propagating information between connected nodes, capturing both feature and structural information.",
        "published_year": 2024
    }
]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_step(step_num: int, title: str):
    """Print a formatted step header."""
    print(f"\n📋 STEP {step_num}: {title}")
    print("-" * 60)


def print_substep(title: str):
    """Print a formatted substep header."""
    print(f"\n  {title}")


def load_documents():
    """Load sample documents from JSON file or use inline data."""
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, "r") as f:
            return json.load(f)
    return DOCUMENTS


def get_embedding_model():
    """Load the sentence transformer model (cached after first call)."""
    return SentenceTransformer(EMBEDDING_MODEL)


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0
    
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        start = end - overlap  # Move forward with overlap
    
    return chunks


# ============================================================
# MAIN TUTORIAL
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("🚀 ZERO-TO-KNOWLEDGE-GRAPH TUTORIAL")
    print("=" * 60)
    
    # ----------------------------------------------------------
    # STEP 1: Environment Check
    # ----------------------------------------------------------
    print_step(1, "Environment Check")
    
    # Check RushDB SDK version
    import rushdb
    print(f"✅ RushDB SDK Version: {rushdb.__version__}")
    
    # Check API key
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("❌ RUSHDB_API_KEY not found!")
        print("   Please create a .env file with your API key.")
        print("   cp .env.example .env")
        sys.exit(1)
    print(f"✅ API Key configured: Yes")
    
    # Initialize RushDB client
    db = RushDB(api_key)
    print(f"✅ RushDB client initialized")
    
    # ----------------------------------------------------------
    # STEP 2: Initial Graph State
    # ----------------------------------------------------------
    print_step(2, "Initial Graph State")
    
    # Query the current graph state
    try:
        result = db.query.raw("MATCH (n) RETURN count(n) AS total")
        total_nodes = result.get("total", 0) if isinstance(result, dict) else 0
    except Exception:
        total_nodes = 0
    
    try:
        result = db.query.raw("MATCH ()-[r]->() RETURN count(r) AS total")
        total_rels = result.get("total", 0) if isinstance(result, dict) else 0
    except Exception:
        total_rels = 0
    
    try:
        labels_result = db.labels.find({})
        labels = [lbl.name for lbl in labels_result] if labels_result else []
    except Exception:
        labels = []
    
    print(f"  • Graph nodes: {total_nodes}")
    print(f"  • Graph relationships: {total_rels}")
    print(f"  • Labels: {labels}")
    
    # ----------------------------------------------------------
    # STEP 3: Zero-Config Document Ingestion
    # ----------------------------------------------------------
    print_step(3, "Zero-Config Document Ingestion")
    print("Ingesting documents with NO schema definition required...")
    print("Each nested JSON object becomes a graph node automatically.\n")
    
    # Load documents
    docs = load_documents()
    
    # Create documents
    created_records = []
    for doc in docs:
        record = db.records.create(label="ARTICLE", data=doc)
        created_records.append(record)
        title_preview = doc["title"][:50] + "..." if len(doc["title"]) > 50 else doc["title"]
        print(f"  ✓ Created: {title_preview} (id: {record.id[:12]}...)")
    
    print(f"\n✅ Ingested {len(created_records)} documents")
    
    # ----------------------------------------------------------
    # STEP 4: Auto-Normalization - Show Graph Structure
    # ----------------------------------------------------------
    print_step(4, "Auto-Normalization - Graph Structure")
    print("RushDB automatically normalized your nested JSON into a property graph:\n")
    
    # Find the first article to show its structure
    first_article = db.records.find_one({"labels": ["ARTICLE"]})
    if first_article:
        print(f"  ARTICLE \"{first_article['title'][:40]}...\"")
        
        # Find related AUTHOR
        authors = db.records.find({
            "labels": ["AUTHOR"],
            "where": {"ARTICLE": {"$relation": {"type": "WRITTEN_BY", "direction": "in"}}},
            "limit": 1
        })
        if authors.data:
            author = authors.data[0]
            print(f"    └── [WRITTEN_BY] → AUTHOR \"{author['name']}\"")
        
        # Find related TAGS
        tags = db.records.find({"labels": ["TAG"],
            "where": {"ARTICLE": {"$relation": {"type": "TAGGED_WITH", "direction": "in"}}},
            "limit": 3
        })
        if tags.data:
            for i, tag in enumerate(tags.data):
                prefix = "    └── [TAGGED_WITH]" if i == len(tags.data) - 1 else "    │   [TAGGED_WITH]"
                print(f"{prefix} → TAG \"{tag['name']}\"")
        
        # Find related SECTIONS
        sections = db.records.find({
            "labels": ["SECTION"],
            "where": {"ARTICLE": {"$relation": {"type": "HAS_SECTION", "direction": "in"}}},
            "limit": 2
        })
        if sections.data:
            for i, section in enumerate(sections.data):
                prefix = "    └── [HAS_SECTION]" if i == len(sections.data) - 1 else "    │   [HAS_SECTION]"
                print(f"{prefix} → SECTION \"{section['heading']}\"")
    
    # Show summary statistics
    print("\n  Graph Summary:")
    
    try:
        result = db.query.raw("MATCH (n) RETURN count(n) AS total")
        new_nodes = result.get("total", 0) if isinstance(result, dict) else 0
        print(f"    • Total nodes: {new_nodes}")
    except Exception:
        pass
    
    try:
        result = db.query.raw("MATCH ()-[r]->() RETURN count(r) AS total")
        new_rels = result.get("total", 0) if isinstance(result, dict) else 0
        print(f"    • Total relationships: {new_rels}")
    except Exception:
        pass
    
    try:
        labels_result = db.labels.find({})
        labels = [lbl.name for lbl in labels_result] if labels_result else []
        print(f"    • Labels created: {', '.join(labels)}")
    except Exception:
        pass
    
    # ----------------------------------------------------------
    # STEP 5: Semantic Search
    # ----------------------------------------------------------
    print_step(5, "Semantic Search")
    
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = get_embedding_model()
    print("✅ Model loaded (384 dimensions)\n")
    
    # Find or create vector index
    print_substep("Creating Vector Index")
    
    # Check for existing index
    existing_indexes = db.ai.indexes.find()
    index_id = None
    
    if existing_indexes:
        for idx in existing_indexes.data if hasattr(existing_indexes, 'data') else existing_indexes:
            if idx.get("label") == "ARTICLE" and idx.get("propertyName") == "content":
                index_id = idx.get("__id") or idx.get("id")
                print(f"  ℹ️  Using existing index: {index_id[:12]}...")
                break
    
    if not index_id:
        # Create new managed index
        index = db.ai.indexes.create({
            "label": "ARTICLE",
            "propertyName": "content",
            "sourceType": "managed"
        })
        index_id = index.data.get("__id") or index.data.get("id") if hasattr(index, 'data') else None
        print(f"  ✅ Created managed index: {index_id}")
    
    # Wait for indexing to complete (managed indexes embed automatically)
    print("  ⏳ Waiting for documents to be indexed...")
    import time
    for _ in range(10):
        try:
            stats = db.ai.indexes.stats(index_id)
            if stats.data and stats.data.get("indexedRecords", 0) >= len(DOCUMENTS):
                break
        except Exception:
            pass
        time.sleep(1)
    
    # Perform semantic search
    print_substep("Performing Semantic Search")
    
    query_text = "deep learning architectures"
    print(f"  Query: \"{query_text}\"\n")
    
    # Generate query embedding
    query_vector = model.encode(query_text).tolist()
    
    # Search using external index (supply pre-computed vector)
    results = db.ai.search({
        "propertyName": "content",
        "queryVector": query_vector,
        "labels": ["ARTICLE"],
        "limit": 5
    })
    
    print("  Results:")
    for i, result in enumerate(results.data, 1):
        title = result.get("title", "Untitled")[:50]
        score = result.score if hasattr(result, 'score') else result.get("__score", 0)
        content = result.get("content", "")[:100]
        print(f"\n  {i}. [{score:.3f}] {title}")
        print(f"     \"{content}...\"")
    
    # ----------------------------------------------------------
    # STEP 6: Graph Traversal Queries
    # ----------------------------------------------------------
    print_step(6, "Graph Traversal Queries")
    
    # Query 1: Find articles by a specific author
    print_substep("Query: Articles by \"Dr. Sarah Chen\"")
    
    # First find the author record
    author_result = db.records.find({
        "labels": ["AUTHOR"],
        "where": {"name": "Dr. Sarah Chen"}
    })
    
    if author_result.data:
        author_id = author_result.data[0].id
        
        # Find articles written by this author using relationship traversal
        articles_result = db.records.find({
            "labels": ["ARTICLE"],
            "where": {
                "AUTHOR": {
                    "$relation": {"type": "WRITTEN_BY", "direction": "in"}
                }
            }
        })
        
        print(f"  Found {articles_result.total} articles by this author:")
        for article in articles_result.data:
            tags_result = db.records.find({
                "labels": ["TAG"],
                "where": {"ARTICLE": {"$relation": {"type": "TAGGED_WITH", "direction": "in"}}},
                "limit": 3
            })
            tag_names = [t["name"] for t in tags_result.data] if tags_result.data else []
            print(f"    • {article['title']} ({', '.join(tag_names)})")
    
    # Query 2: Find articles with a specific tag
    print_substep("Query: Articles tagged with \"databases\"")
    
    # Find articles with the databases tag
    articles_result = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "TAG": {
                "$relation": {"type": "TAGGED_WITH", "direction": "in"},
                "name": "databases"
            }
        }
    })
    
    print(f"  Found {articles_result.total} articles with this tag:")
    for article in articles_result.data:
        print(f"    • {article['title']}")
    
    # Query 3: Find co-authors (authors who wrote articles with overlapping tags)
    print_substep("Query: Find related articles through shared tags")
    
    # Get articles similar to the first one based on shared tags
    if created_records:
        first_article_id = created_records[0].id
        
        # Find tags for the first article
        first_tags = db.records.find({
            "labels": ["TAG"],
            "where": {"ARTICLE": {"$relation": {"type": "TAGGED_WITH", "direction": "in"}}},
            "limit": 5
        })
        
        if first_tags.data:
            tag_names = [t["name"] for t in first_tags.data]
            print(f"  Article 1 tags: {', '.join(tag_names)}")
            
            # Find other articles with any of these tags
            related_result = db.records.find({
                "labels": ["ARTICLE"],
                "where": {
                    "$or": [{"TAG": {"$relation": {"type": "TAGGED_WITH", "direction": "in"}, "name": tag}} for tag in tag_names[:2]]
                }
            })
            
            # Filter out the first article itself
            related = [a for a in related_result.data if a.id != first_article_id][:3]
            
            print(f"  Related articles (shared tags): {len(related)}")
            for article in related:
                print(f"    • {article['title']}")
    
    # ----------------------------------------------------------
    # STEP 7: Chunking Strategy & Reindexing
    # ----------------------------------------------------------
    print_step(7, "Chunking Strategy & Reindexing")
    
    print_substep("Current Index Stats")
    
    if index_id:
        stats = db.ai.indexes.stats(index_id)
        total = stats.data.get("totalRecords", "N/A") if stats.data else "N/A"
        indexed = stats.data.get("indexedRecords", "N/A") if stats.data else "N/A"
        print(f"  • Records indexed: {indexed} / {total}")
    
    print_substep(f"Reindexing with Chunking Strategy (size={DEFAULT_CHUNK_SIZE}, overlap={DEFAULT_OVERLAP})")
    print("  Creating document chunks for more granular semantic search...\n")
    
    # Create chunks for each document
    total_chunks = 0
    for doc in DOCUMENTS:
        chunks = chunk_text(doc["content"], DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP)
        total_chunks += len(chunks)
        
        # Find the corresponding article record
        article_result = db.records.find_one({
            "labels": ["ARTICLE"],
            "where": {"title": doc["title"]}
        })
        
        if article_result:
            for i, chunk in enumerate(chunks):
                chunk_record = db.records.create(
                    label="CHUNK",
                    data={
                        "text": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "parent_title": doc["title"]
                    }
                )
                # Link chunk to parent article
                db.records.attach(
                    source=chunk_record,
                    target=article_result,
                    options={"type": "PART_OF", "direction": "out"}
                )
        
        print(f"  • \"{doc['title'][:40]}...\" → {len(chunks)} chunks")
    
    print(f"\n  ✅ Created {total_chunks} chunks from {len(DOCUMENTS)} documents")
    print(f"  📊 Average chunks per document: {total_chunks / len(DOCUMENTS):.1f}")
    
    # Create vector index for chunks
    print_substep("Creating Vector Index for Chunks")
    
    chunk_index = db.ai.indexes.create({
        "label": "CHUNK",
        "propertyName": "text",
        "sourceType": "managed"
    })
    
    chunk_index_id = chunk_index.data.get("__id") if hasattr(chunk_index, 'data') else None
    print(f"  ✅ Created chunk index: {chunk_index_id}")
    
    # Wait for chunk indexing
    print("  ⏳ Waiting for chunks to be indexed...")
    for _ in range(15):
        try:
            stats = db.ai.indexes.stats(chunk_index_id)
            if stats.data and stats.data.get("indexedRecords", 0) >= total_chunks:
                break
        except Exception:
            pass
        time.sleep(1)
    
    # Show new stats
    print_substep("Updated Index Stats")
    
    if index_id:
        stats = db.ai.indexes.stats(index_id)
        total = stats.data.get("totalRecords", "N/A") if stats.data else "N/A"
        indexed = stats.data.get("indexedRecords", "N/A") if stats.data else "N/A"
        print(f"  • Article index: {indexed} / {total}")
    
    if chunk_index_id:
        stats = db.ai.indexes.stats(chunk_index_id)
        total = stats.data.get("totalRecords", "N/A") if stats.data else "N/A"
        indexed = stats.data.get("indexedRecords", "N/A") if stats.data else "N/A"
        print(f"  • Chunk index: {indexed} / {total}")
    
    # Demonstrate chunk-level search
    print_substep("Chunk-Level Semantic Search")
    
    query_vector = model.encode("how do neural networks learn through training").tolist()
    
    chunk_results = db.ai.search({
        "propertyName": "text",
        "queryVector": query_vector,
        "labels": ["CHUNK"],
        "limit": 3
    })
    
    print(f"  Query: \"how do neural networks learn through training\"\n")
    for i, result in enumerate(chunk_results.data, 1):
        parent = result.get("parent_title", "Unknown")[:40]
        score = result.score if hasattr(result, 'score') else result.get("__score", 0)
        text = result.get("text", "")[:80]
        chunk_idx = result.get("chunk_index", 0)
        print(f"  {i}. [{score:.3f}] {parent} [chunk {chunk_idx}]")
        print(f"     \"{text}...\"")
    
    # ----------------------------------------------------------
    # COMPLETION
    # ----------------------------------------------------------
    print("\n" + "=" * 60)
    print("✨ TUTORIAL COMPLETE")
    print("=" * 60)
    print("\nYou've successfully:")
    print("  ✅ Ingested documents with zero schema configuration")
    print("  ✅ Seen auto-normalization create a property graph")
    print("  ✅ Performed semantic similarity search")
    print("  ✅ Traversed graph relationships across documents")
    print("  ✅ Adjusted chunking strategy and reindexed")
    print("\nNext steps:")
    print("  • Explore more complex relationship patterns")
    print("  • Try importing your own JSON documents")
    print("  • Build a RAG pipeline with RushDB as your memory layer")
    print("\nLearn more: https://docs.rushdb.com")
    print("\n" + "=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
