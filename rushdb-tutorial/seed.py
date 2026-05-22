"""
Seed script for RushDB tutorial.

Generates realistic tech articles data with embeddings and establishes
graph relationships between articles, authors, and topics.

Run this once before main.py to populate the database with demo data.
The script is idempotent — safe to run multiple times.
"""

import os
import random
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Check if data already exists
def check_existing_data(db):
    result = db.labels.find()
    for label in result:
        if label.name == 'ARTICLE' and label.count > 0:
            return True
    return False

# Initialize embedding model
def get_embedder():
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    return SentenceTransformer('all-MiniLM-L6-v2')

# Sample data for realistic content
AUTHORS = [
    {"name": "Sarah Chen", "bio": "Senior ML Engineer at TechCorp"},
    {"name": "Marcus Rodriguez", "bio": "Distributed Systems Architect"},
    {"name": "Aisha Patel", "bio": "AI Research Lead"},
    {"name": "James Wilson", "bio": "Backend Systems Expert"},
    {"name": "Elena Kowalski", "bio": "Data Infrastructure Engineer"},
]

TOPICS = [
    {"name": "Machine Learning", "description": "ML algorithms and training"},
    {"name": "Distributed Systems", "description": "Scalable architecture patterns"},
    {"name": "Natural Language Processing", "description": "Text understanding and generation"},
    {"name": "Database Systems", "description": "Data storage and retrieval"},
    {"name": "DevOps", "description": "Deployment and operations"},
]

ARTICLES = [
    {"title": "Understanding Transformer Architecture", "body": "Transformers revolutionized NLP by using self-attention mechanisms instead of RNNs. The key innovation is allowing every token to attend to every other token, enabling parallel processing and capturing long-range dependencies effectively."},
    {"title": "Vector Databases in Production", "body": "When deploying vector similarity search at scale, consider index type (HNSW vs IVF), memory footprint, and update latency. Hybrid search combining dense and sparse vectors often outperforms either alone."},
    {"title": "Graph Neural Networks Explained", "body": "GNNs extend deep learning to graph-structured data by propagating information along edges. Message passing aggregates neighbor features, allowing nodes to learn from their local graph neighborhoods."},
    {"title": "Scaling RAG Systems", "body": "Retrieval-Augmented Generation combines semantic search with LLM reasoning. Key optimizations include chunking strategy, re-ranking, and hybrid filtering to balance precision and recall."},
    {"title": "Neo4j for Knowledge Graphs", "body": "Property graphs excel at representing complex relationships. Native graph storage enables efficient traversal queries that would be prohibitively expensive in relational databases for deep hops."},
    {"title": "Distributed Training Patterns", "body": "Data parallelism splits batches across GPUs while model parallelism splits layers. Hybrid approaches like pipeline parallelism balance communication overhead with compute utilization."},
    {"title": "Embedding Strategies", "body": "Different embedding models suit different tasks: dense vectors for semantic similarity, sparse for keyword matching. Cross-encoders provide better relevance but at higher latency."},
    {"title": "Cache Strategies for AI Applications", "body": "LLM responses are expensive to compute. Semantic caching stores embeddings of queries and retrieves similar cached responses, reducing cost and latency for repeated questions."},
    {"title": "Knowledge Graph Construction", "body": "Building KG from unstructured text involves NER, relation extraction, and entity linking. Quality control and canonicalization ensure consistent node and edge definitions."},
    {"title": "Fine-tuning vs RAG", "body": "Fine-tuning adapts model weights to domain data but requires significant compute. RAG keeps the base model frozen and retrieves relevant context, offering better interpretability and easier updates."},
]

def seed():
    api_key = os.getenv('RUSHDB_API_KEY')
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        return

    print("\n=== RushDB Tutorial: Data Seeder ===\n")
    
    db = RushDB(api_key)
    
    # Check if data already exists
    if check_existing_data(db):
        print("Data already exists (found ARTICLE records). Skipping seed.")
        print("Delete existing records or run main.py to query existing data.\n")
        return

    embedder = get_embedder()
    
    # Create vector index first
    print("\n[1/5] Creating vector index...")
    index = db.ai.indexes.create({
        "label": "ARTICLE",
        "propertyName": "embedding",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    print(f"  Index created: {index.data.get('__id', 'unknown')}")

    # Create authors
    print("\n[2/5] Creating authors...")
    author_records = []
    for author in AUTHORS:
        record = db.records.create(label="AUTHOR", data=author)
        author_records.append(record)
        print(f"  Created author: {author['name']}")

    # Create topics
    print("\n[3/5] Creating topics...")
    topic_records = []
    for topic in TOPICS:
        record = db.records.create(label="TOPIC", data=topic)
        topic_records.append(record)
        print(f"  Created topic: {topic['name']}")

    # Create articles with embeddings
    print("\n[4/5] Creating articles with embeddings...")
    article_records = []
    for i, article in enumerate(ARTICLES):
        # Generate embedding for the article body
        text_for_embedding = f"{article['title']}. {article['body']}"
        embedding = embedder.encode(text_for_embedding).tolist()
        
        record = db.records.create(
            label="ARTICLE",
            data={
                "title": article["title"],
                "body": article["body"],
                "views": random.randint(100, 5000),
                "published_at": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            },
            vectors=[{"propertyName": "embedding", "vector": embedding}]
        )
        article_records.append(record)
        
        if (i + 1) % 5 == 0:
            print(f"  Progress: {i + 1}/{len(ARTICLES)} articles created")

    print(f"  Created {len(article_records)} articles with vector embeddings")

    # Establish relationships using transaction
    print("\n[5/5] Establishing graph relationships...")
    with db.transactions.begin() as tx:
        for article in article_records:
            # Link to random author
            author = random.choice(author_records)
            db.records.attach(
                source=article,
                target=author,
                options={"type": "WRITTEN_BY", "direction": "out"},
                transaction=tx
            )
            
            # Link to 1-2 random topics
            topics = random.sample(topic_records, random.randint(1, 2))
            for topic in topics:
                db.records.attach(
                    source=article,
                    target=topic,
                    options={"type": "TAGGED_WITH", "direction": "out"},
                    transaction=tx
                )
        # Transaction auto-commits on clean exit
    
    print("  Established WRITTEN_BY and TAGGED_WITH relationships")
    
    print("\n=== Seeding Complete! ===")
    print(f"  • {len(AUTHORS)} authors")
    print(f"  • {len(TOPICS)} topics")
    print(f"  • {len(ARTICLES)} articles with embeddings")
    print(f"  Run 'python main.py' to execute hybrid queries\n")

if __name__ == "__main__":
    seed()
