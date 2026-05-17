#!/usr/bin/env python3
"""
Seed script: Initializes the knowledge base with sample articles and relationships.

This script:
1. Creates a vector index for article body text
2. Loads articles with embeddings
3. Creates RELATED_TO relationships between semantically similar articles
4. Reports progress and verifies data integrity
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment variables
dotenv.load_dotenv()

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def load_articles():
    """Load sample articles from data file."""
    data_path = Path(__file__).parent / "data" / "articles.json"
    with open(data_path) as f:
        return json.load(f)


def get_embedding_model():
    """Load and return the sentence transformer model."""
    print(f"Loading embedding model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)


def compute_embeddings(model, texts):
    """Compute embeddings for a list of texts."""
    print(f"Computing embeddings for {len(texts)} articles...")
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


def calculate_similarity_scores(embeddings):
    """
    Calculate pairwise cosine similarity scores between all article embeddings.
    Returns a list of (article_a_index, article_b_index, similarity_score) tuples.
    """
    from sentence_transformers import util
    
    print("Calculating article similarities for relationship creation...")
    scores = []
    
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = util.cos_sim(embeddings[i], embeddings[j]).item()
            if sim > 0.3:  # Only create relationships for moderately similar articles
                scores.append((i, j, sim))
    
    # Sort by similarity descending and take top relationships
    scores.sort(key=lambda x: x[2], reverse=True)
    return scores[:15]  # Limit to top 15 relationships


def seed_knowledge_base(db: RushDB, model, articles: list, similarity_scores: list):
    """
    Seed the knowledge base with articles, embeddings, and relationships.
    
    Creates:
    - Article records with vector embeddings
    - RELATED_TO relationships between semantically similar articles
    """
    print("\n=== SEEDING KNOWLEDGE BASE ===")
    
    # Check if already seeded
    existing = db.records.find({"labels": ["Article"], "limit": 1})
    if existing.total > 0:
        print(f"Knowledge base already seeded ({existing.total} articles found)")
        print("Run 'python main.py' to see the feedback loop in action.")
        return existing.data
    
    # Create vector index for Article.body
    print("\nCreating vector index for Article.body...")
    try:
        index = db.ai.indexes.create({
            "label": "Article",
            "propertyName": "body",
            "sourceType": "external",
            "dimensions": 384,  # all-MiniLM-L6-v2 outputs 384 dimensions
            "similarityFunction": "cosine"
        })
        print(f"Vector index created: {index.data.get('__id')}")
    except Exception as e:
        print(f"Note: Index creation: {e}")
    
    # Prepare embeddings for all articles
    texts = [a["body"] for a in articles]
    embeddings = compute_embeddings(model, texts)
    
    # Create articles with embeddings
    print("\nCreating articles with vector embeddings...")
    created_articles = []
    
    with db.transactions.begin() as tx:
        for idx, article in enumerate(articles):
            article_data = {
                "title": article["title"],
                "body": article["body"],
                "tags": article["tags"],
                "version": article["version"],
                "trust_score": 1.0,  # Start with maximum trust
                "created_at": datetime.now().isoformat(),
                "last_verified_at": datetime.now().isoformat(),
                "correction_count": 0
            }
            
            record = db.records.create(
                label="Article",
                data=article_data,
                vectors=[{"propertyName": "body", "vector": embeddings[idx]}],
                transaction=tx
            )
            created_articles.append(record)
            
            if (idx + 1) % 100 == 0:
                print(f"  Created {idx + 1}/{len(articles)} articles...")
    
    print(f"\nCreated {len(created_articles)} articles")
    
    # Create RELATED_TO relationships
    print("\nCreating relationships between related articles...")
    with db.transactions.begin() as tx:
        for art_a_idx, art_b_idx, score in similarity_scores:
            if art_a_idx < len(created_articles) and art_b_idx < len(created_articles):
                article_a = created_articles[art_a_idx]
                article_b = created_articles[art_b_idx]
                
                db.records.attach(
                    source=article_a,
                    target=article_b,
                    options={"type": "RELATED_TO", "direction": "out"},
                    transaction=tx
                )
                
                # Bidirectional relationship
                db.records.attach(
                    source=article_b,
                    target=article_a,
                    options={"type": "RELATED_TO", "direction": "out"},
                    transaction=tx
                )
    
    print(f"Created {len(similarity_scores) * 2} relationships")
    
    # Verify seeding
    final_count = db.records.find({"labels": ["Article"], "limit": 1})
    print(f"\n=== SEEDING COMPLETE ===")
    print(f"Total articles: {final_count.total}")
    print("Run 'python main.py' to see the feedback loop in action.")
    
    return created_articles


def main():
    """Main entry point for seeding the knowledge base."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY environment variable not set")
        print("Copy .env.example to .env and fill in your API key")
        sys.exit(1)
    
    print("=== INITIALIZING RUSHDB CLIENT ===")
    db = RushDB(api_key)
    print("Connected to RushDB")
    
    # Load data
    articles = load_articles()
    print(f"Loaded {len(articles)} articles from data file")
    
    # Load model
    model = get_embedding_model()
    
    # Calculate similarity scores for relationship creation
    texts = [a["body"] for a in articles]
    embeddings = compute_embeddings(model, texts)
    similarity_scores = calculate_similarity_scores(embeddings)
    
    # Seed the database
    seed_knowledge_base(db, model, articles, similarity_scores)
    
    # Print index stats
    try:
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            stats = db.ai.indexes.stats(idx["__id"])
            print(f"\nIndex stats for {idx['label']}.{idx['propertyName']}:")
            print(f"  Status: {idx['status']}")
            print(f"  Indexed: {stats.data.get('indexedRecords', 0)} / {stats.data.get('totalRecords', 0)}")
    except Exception as e:
        print(f"Note: Could not retrieve index stats: {e}")


if __name__ == "__main__":
    main()
