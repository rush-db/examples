"""
Seed script for RushDB Python SDK comparison.

Creates a small graph of Movies, Actors, and Articles to demonstrate
graph traversal and vector similarity search patterns.

This script is idempotent — running it multiple times is safe.
"""

import os
import random
from rushdb import RushDB

# Initialize the client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise RuntimeError(
        "RUSHDB_API_KEY not found. "
        "Copy .env.example to .env and fill in your API key."
    )

db = RushDB(api_key)

# Sample data
MOVIES = [
    {"title": "Inception", "year": 2010, "rating": 8.8, "genre": "sci-fi"},
    {"title": "The Dark Knight", "year": 2008, "rating": 9.0, "genre": "action"},
    {"title": "Interstellar", "year": 2014, "rating": 8.6, "genre": "sci-fi"},
    {"title": "Dunkirk", "year": 2017, "rating": 7.8, "genre": "war"},
    {"title": "Tenet", "year": 2020, "rating": 7.5, "genre": "sci-fi"},
]

ACTORS = [
    {"name": "Leonardo DiCaprio", "age": 49},
    {"name": "Christian Bale", "age": 49},
    {"name": "Michael Caine", "age": 89},
    {"name": "Marion Cotillard", "age": 48},
    {"name": "Tom Hardy", "age": 46},
]

ARTICLES = [
    {
        "title": "Understanding Transformer Architecture",
        "content": "Transformers revolutionized NLP by using self-attention mechanisms "
                   "to process sequences in parallel. Unlike RNNs, transformers can "
                   "capture long-range dependencies efficiently.",
        "tags": ["ai", "machine-learning"],
    },
    {
        "title": "Introduction to Graph Neural Networks",
        "content": "Graph Neural Networks (GNNs) extend deep learning to graph-structured "
                   "data. They can reason about relationships between entities, making them "
                   "ideal for social networks and knowledge graphs.",
        "tags": ["ai", "deep-learning"],
    },
    {
        "title": "Building RAG Applications",
        "content": "Retrieval-Augmented Generation combines vector search with LLMs to "
                   "produce contextually relevant answers grounded in your documents. "
                   "This pattern is essential for enterprise AI applications.",
        "tags": ["ai", "rag", "llm"],
    },
    {
        "title": "Vector Databases Explained",
        "content": "Vector databases store high-dimensional embeddings that enable "
                   "semantic similarity search. Unlike traditional databases, they excel "
                   "at finding conceptually similar items rather than exact matches.",
        "tags": ["databases", "ai"],
    },
    {
        "title": "AsyncIO Best Practices",
        "content": "Python's asyncio library enables concurrent I/O operations without "
                   "threads. Proper use involves async/await syntax, event loop management, "
                   "and avoiding blocking calls in async functions.",
        "tags": ["python", "async"],
    },
]


def seed_graph_data():
    """Create movies, actors, and relationships (graph traversal demo data)."""
    print("Seeding graph data (Movies and Actors)...")

    # Check if data already exists
    existing = db.records.find({"labels": ["MOVIE"], "where": {"title": "Inception"}})
    if existing.total > 0:
        print("  Graph data already exists, skipping seed.")
        return

    # Create movies
    movies = []
    for movie_data in MOVIES:
        movie = db.records.create(label="MOVIE", data=movie_data)
        movies.append(movie)
        print(f"  Created movie: {movie_data['title']}")

    # Create actors and relationships
    for i, actor_data in enumerate(ACTORS):
        actor = db.records.create(label="ACTOR", data=actor_data)

        # Each actor acts in a random subset of movies
        selected_movies = random.sample(movies, random.randint(1, 3))
        for movie in selected_movies:
            db.records.attach(source=movie, target=actor, options={"type": "ACTED_IN"})

        print(f"  Created actor: {actor_data['name']} ({len(selected_movies)} movies)")

    print("  Graph data seeded successfully!\n")


def seed_vector_data():
    """Create articles with mock embeddings (vector similarity demo data)."""
    print("Seeding vector data (Articles)...")

    # Check if data already exists
    existing = db.records.find({"labels": ["ARTICLE"], "where": {"title": "Understanding Transformer Architecture"}})
    if existing.total > 0:
        print("  Article data already exists, skipping seed.")
        return

    # Create a vector index for the content property
    try:
        indexes = db.ai.indexes.find()
        article_index = None
        for idx in indexes.data:
            if idx["label"] == "ARTICLE" and idx["propertyName"] == "content":
                article_index = idx
                break

        if not article_index:
            print("  Creating vector index for ARTICLE.content...")
            index = db.ai.indexes.create({
                "label": "ARTICLE",
                "propertyName": "content",
                "sourceType": "external",
                "dimensions": 384,
            })
            print(f"  Index created: {index.data.get('__id', 'unknown')}")
    except Exception as e:
        print(f"  Index creation warning: {e}")

    # Generate mock embedding vectors (deterministic for reproducibility)
    # In production, use sentence-transformers or OpenAI embeddings
    def mock_embedding(text: str, dim: int = 384) -> list:
        """Generate a deterministic mock embedding based on text hash."""
        seed = sum(ord(c) for c in text)
        random.seed(seed)
        return [random.uniform(-1, 1) for _ in range(dim)]

    # Create articles with embeddings
    for i, article_data in enumerate(ARTICLES):
        vector = mock_embedding(article_data["content"])

        article = db.records.create(
            label="ARTICLE",
            data=article_data,
            vectors=[{"propertyName": "content", "vector": vector}],
        )
        print(f"  Created article: {article_data['title']} (dim=384)")

        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  ... {i + 1} articles created")

    print("  Vector data seeded successfully!\n")


def main():
    print("=" * 60)
    print("RushDB Python SDK — Seed Script")
    print("=" * 60)
    print()

    seed_graph_data()
    seed_vector_data()

    print("=" * 60)
    print("Seed complete! Run `python main.py` to see the SDK comparison.")
    print("=" * 60)


if __name__ == "__main__":
    main()
