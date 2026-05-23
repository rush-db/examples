"""
Seed script for Graph-Native RAG Caching Tutorial

Generates sample documents and chunks demonstrating graph relationships.
This data models a typical knowledge base for a technical documentation system.
"""

import os
import random
import time
from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(api_key)

# Initialize embedding model (all-MiniLM-L6-v2 - 384 dimensions)
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_DIM = 384

# Sample documents about technical topics
DOCUMENTS = [
    {
        "title": "Introduction to Graph Databases",
        "topic": "databases",
        "chunks": [
            "Graph databases store data as nodes and edges, representing relationships naturally.",
            "Unlike relational databases, graph databases excel at traversing deep relationships.",
            "Neo4j is a popular graph database that uses the Cypher query language.",
            "Property graphs allow nodes and edges to have attributes, enabling rich data modeling.",
            "Graph databases are ideal for social networks, recommendation engines, and fraud detection."
        ]
    },
    {
        "title": "RAG Architecture Basics",
        "topic": "ai",
        "chunks": [
            "Retrieval Augmented Generation combines retrieval systems with LLMs.",
            "RAG reduces hallucinations by grounding responses in retrieved context.",
            "Vector databases enable semantic similarity search for retrieval.",
            "Chunk size significantly impacts retrieval quality and context window usage.",
            "Hybrid search combining dense vectors and sparse keywords improves results."
        ]
    },
    {
        "title": "Vector Search Optimization",
        "topic": "ai",
        "chunks": [
            "Vector indexes like HNSW enable approximate nearest neighbor search at scale.",
            "Embedding models determine the quality of semantic representations.",
            "Dimensionality reduction can speed up search at the cost of some accuracy.",
            "Query caching avoids redundant embedding generation for repeated queries.",
            "Re-ranking models like BGE can improve precision after initial retrieval."
        ]
    },
    {
        "title": "Python SDK Best Practices",
        "topic": "programming",
        "chunks": [
            "Always use keyword arguments when calling RushDB SDK methods.",
            "Transactions ensure atomic operations across multiple record creates.",
            "Use context managers for automatic transaction handling.",
            "Batch operations with create_many reduce API overhead.",
            "Field projection with 'select' reduces data transfer for read-heavy workloads."
        ]
    },
    {
        "title": "Context Window Management",
        "topic": "ai",
        "chunks": [
            "Modern LLMs have context windows ranging from 4K to 128K tokens.",
            "Priority ranking helps select the most relevant chunks when context is limited.",
            "Hierarchical summarization compresses long documents while preserving key information.",
            "Sliding window approaches ensure no information is lost at chunk boundaries.",
            "Metadata filtering can reduce chunk count while maintaining relevance."
        ]
    },
    {
        "title": "Performance Monitoring",
        "topic": "devops",
        "chunks": [
            "Latency tracking helps identify bottlenecks in the retrieval pipeline.",
            "Cache hit rates indicate how effectively repeated queries are served.",
            "Embedding generation is often the most expensive operation in RAG.",
            "Connection pooling reduces overhead for high-throughput applications.",
            "Distributed tracing helps debug issues across service boundaries."
        ]
    },
    {
        "title": "Caching Strategies",
        "topic": "architecture",
        "chunks": [
            "Query caching stores frequently requested results to avoid recomputation.",
            "Semantic caching groups similar queries to share retrieval results.",
            "Invalidation strategies determine when cached data becomes stale.",
            "Graph-native caching leverages relationships for context-aware retrieval.",
            "Multi-level caching combines memory, disk, and database layers."
        ]
    },
    {
        "title": "Data Modeling Patterns",
        "topic": "databases",
        "chunks": [
            "Star schemas work well for analytics workloads with clear fact/dimension separation.",
            "Graph schemas excel when relationships are as important as entities.",
            "Denormalization trades storage for read performance.",
            "Time-partitioning enables efficient temporal queries on large datasets.",
            "Hierarchical data benefits from recursive CTEs or nested set models."
        ]
    },
    {
        "title": "LLM Integration Patterns",
        "topic": "ai",
        "chunks": [
            "Prompt templates separate static instructions from dynamic context.",
            "Chain-of-thought prompting improves reasoning on complex tasks.",
            "Few-shot examples help models understand desired output formats.",
            "System prompts set the assistant's personality and capability boundaries.",
            "Temperature and top-p sampling control output randomness and creativity."
        ]
    },
    {
        "title": "Error Handling in Production",
        "topic": "devops",
        "chunks": [
            "Circuit breakers prevent cascade failures when services become unavailable.",
            "Graceful degradation maintains partial functionality during outages.",
            "Retry policies with exponential backoff handle transient failures.",
            "Dead letter queues capture failed operations for later analysis.",
            "Health checks enable load balancers to route traffic away from unhealthy instances."
        ]
    }
]


def create_indexes():
    """Create vector indexes for semantic search."""
    print("\n[1] Creating vector indexes...")
    
    # Create index for CHUNK labels (external source, requires dimensions)
    try:
        db.ai.indexes.create({
            "label": "CHUNK",
            "propertyName": "content",
            "sourceType": "external",
            "dimensions": EMBEDDING_DIM,
            "similarityFunction": "cosine"
        })
        print("  ✓ Created CHUNK index with {} dimensions".format(EMBEDDING_DIM))
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("  ✓ CHUNK index already exists")
        else:
            print("  ⚠ Index creation: {}".format(str(e)[:50]))
    
    # Create index for DOCUMENT labels
    try:
        db.ai.indexes.create({
            "label": "DOCUMENT",
            "propertyName": "title",
            "sourceType": "external",
            "dimensions": EMBEDDING_DIM,
            "similarityFunction": "cosine"
        })
        print("  ✓ Created DOCUMENT index")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("  ✓ DOCUMENT index already exists")
        else:
            print("  ⚠ Index creation: {}".format(str(e)[:50]))


def check_data_exists():
    """Check if documents are already seeded."""
    result = db.records.find({
        "labels": ["DOCUMENT"],
        "limit": 1
    })
    return len(result.data) > 0


def seed_documents():
    """Seed sample documents with chunks and relationships."""
    if check_data_exists():
        print("\n[2] Data already exists, skipping seed...")
        return
    
    print("\n[2] Seeding documents...")
    
    # First, create topics
    topics = {}
    topic_names = list(set(doc["topic"] for doc in DOCUMENTS))
    
    for topic_name in topic_names:
        topic = db.records.create(
            label="TOPIC",
            data={"name": topic_name}
        )
        topics[topic_name] = topic
        print("  Created TOPIC: {}".format(topic_name))
        
        # Small delay to avoid rate limits
        time.sleep(0.1)
    
    # Now create documents and their chunks
    for doc_data in DOCUMENTS:
        # Generate document embedding
        title_embedding = model.encode(doc_data["title"]).tolist()
        
        # Create document
        document = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc_data["title"],
                "topic": doc_data["topic"]
            },
            vectors=[{"propertyName": "title", "vector": title_embedding}]
        )
        print("  Created DOCUMENT: {}".format(doc_data["title"]))
        
        # Link document to topic
        topic = topics[doc_data["topic"]]
        db.records.attach(
            source=document,
            target=topic,
            options={"type": "HAS_TOPIC"}
        )
        
        # Create chunks for this document
        prev_chunk = None
        for i, chunk_text in enumerate(doc_data["chunks"]):
            # Generate chunk embedding
            chunk_embedding = model.encode(chunk_text).tolist()
            
            chunk = db.records.create(
                label="CHUNK",
                data={
                    "content": chunk_text,
                    "index": i,
                    "doc_title": doc_data["title"]
                },
                vectors=[{"propertyName": "content", "vector": chunk_embedding}]
            )
            
            # Link chunk to document
            db.records.attach(
                source=document,
                target=chunk,
                options={"type": "CONTAINS"}
            )
            
            # Link sequential chunks (for context continuity)
            if prev_chunk:
                db.records.attach(
                    source=prev_chunk,
                    target=chunk,
                    options={"type": "NEXT"}
                )
            
            # Link to topic
            db.records.attach(
                source=chunk,
                target=topic,
                options={"type": "TAGGED_WITH"}
            )
            
            prev_chunk = chunk
            print("    └─ CHUNK {}: {}..." .format(i + 1, chunk_text[:50]))
            
            # Small delay to avoid rate limits
            time.sleep(0.1)
    
    print("\n  ✓ Seeding complete! Created {} documents with {} topics".format(
        len(DOCUMENTS), len(topics)
    ))


def add_cross_references():
    """Add additional relationship links between related chunks."""
    print("\n[3] Adding cross-references between related chunks...")
    
    # Find AI-related chunks and link them
    ai_chunks = db.records.find({
        "labels": ["CHUNK"],
        "where": {"TOPIC": {"$relation": {"type": "TAGGED_WITH", "direction": "out"}}},
        "limit": 20
    })
    
    # Create additional relationships for demo
    all_chunks = db.records.find({
        "labels": ["CHUNK"],
        "limit": 10
    })
    
    for i, chunk in enumerate(all_chunks.data[:5]):
        for other_chunk in all_chunks.data[i+1:3+i]:
            db.records.attach(
                source=chunk,
                target=other_chunk,
                options={"type": "RELATED_TO"}
            )
    
    print("  ✓ Added cross-references")


if __name__ == "__main__":
    print("=" * 60)
    print("Graph-Native RAG Caching - Data Seeder")
    print("=" * 60)
    
    create_indexes()
    seed_documents()
    add_cross_references()
    
    print("\n" + "=" * 60)
    print("Seeding complete! Run 'python main.py' to start the demo.")
    print("=" * 60)
