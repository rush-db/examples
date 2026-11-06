"""
Python SDK implementation — RushDB Python vs Node.js Comparison

Demonstrates the three most common patterns:
1. CRUD Operations
2. Graph Traversal
3. Vector Similarity Search

Each pattern is shown side-by-side with commentary on ergonomic differences.
"""

import os
import time
from rushdb import RushDB

# Initialize the client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise RuntimeError(
        "RUSHDB_API_KEY not found. "
        "Copy .env.example to .env and fill in your API key."
    )

db = RushDB(api_key)

# ===============================
# PATTERN 1: CRUD OPERATIONS
# ===============================

def demonstrate_crud():
    """
    Both SDKs support full CRUD. Python is synchronous, returns dict-like Records.

    Key Python patterns:
    - db.records.create(label="LABEL", data={...}) — keyword args only
    - db.records.find({...}) — returns paginated results
    - record.id, record.data, record.fields — Record object access
    """
    print("\n" + "=" * 60)
    print("PATTERN 1: CRUD OPERATIONS (Python SDK)")
    print("=" * 60)

    # Create a movie record
    movie = db.records.create(
        label="MOVIE",
        data={"title": "Oppenheimer", "year": 2023, "rating": 8.9, "genre": "drama"},
    )
    print(f"\n[CREATE] Movie '{movie['title']}' created with ID: {movie.id}")

    # Find movies with high ratings
    results = db.records.find({
        "labels": ["MOVIE"],
        "where": {"rating": {"$gte": 8.5}},
        "limit": 10,
        "orderBy": {"rating": "desc"},
    })
    print(f"\n[FIND] Found {results.total} movies with rating >= 8.5:")
    for m in results.data:
        print(f"  - {m.title} ({m.year}): ★ {m['rating']}")

    # Update the record
    db.records.update(record_id=movie.id, data={"rating": 9.0})
    print(f"\n[UPDATE] Oppenheimer rating updated to 9.0")

    # Verify the update
    updated = db.records.find_by_id(movie.id)
    print(f"[VERIFY] Updated rating: {updated['rating']}")

    # Delete the test record (cleanup)
    db.records.delete(record_id=movie.id)
    print(f"\n[DELETE] Oppenheimer deleted")

    print("\n→ Python SDK: Synchronous, dict-like Record objects")
    print("→ TypeScript: async/await, typed responses with .data property")


# ===============================
# PATTERN 2: GRAPH TRAVERSAL
# ===============================

def demonstrate_graph():
    """
    RushDB stores records as graph nodes. Filter by related record properties.

    Key Python patterns:
    - db.records.find({...}) with nested where clauses
    - {"LABEL": {"$relation": {...}, "field": value}} for relationship filters
    - db.records.attach(source=..., target=..., options={...}) for relationships
    """
    print("\n" + "=" * 60)
    print("PATTERN 2: GRAPH TRAVERSAL (Python SDK)")
    print("=" * 60)

    # Find actors in high-rated sci-fi movies using relationship traversal
    # Filter: ACTOR records where the related MOVIE has rating >= 8.5 AND genre = sci-fi
    actors_in_quality_sci_fi = db.records.find({
        "labels": ["ACTOR"],
        "where": {
            "MOVIE": {
                "$relation": {"type": "ACTED_IN", "direction": "in"},
                "rating": {"$gte": 8.5},
                "genre": "sci-fi",
            }
        },
    })
    print(f"\n[GRAPH TRAVERSE] Actors in high-rated sci-fi movies: {actors_in_quality_sci_fi.total}")
    for actor in actors_in_quality_sci_fi.data:
        # Find the related movies for this actor
        related = db.records.find({
            "labels": ["MOVIE"],
            "where": {
                "ACTOR": {"$relation": {"type": "ACTED_IN", "direction": "in"}}
            },
        })
        movie_titles = [m.title for m in related.data]
        print(f"  - {actor.name}: {movie_titles}")

    # Find all movies and their actors
    all_movies = db.records.find({"labels": ["MOVIE"], "limit": 5, "orderBy": {"title": "asc"}})
    print(f"\n[GRAPH] Movies and their cast:")
    for movie in all_movies.data:
        cast = db.records.find({
            "labels": ["ACTOR"],
            "where": {
                "MOVIE": {
                    "$id": movie.id,
                    "$relation": {"type": "ACTED_IN", "direction": "in"}
                }
            },
        })
        cast_names = [a.name for a in cast.data]
        print(f"  '{movie.title}' ({movie.year}) starring: {', '.join(cast_names) if cast_names else 'unknown'}")

    print("\n→ Graph traversal uses relationship filters in 'where' clause")
    print("→ No Cypher queries needed — RushDB handles graph traversal internally")


# ===============================
# PATTERN 3: VECTOR SIMILARITY SEARCH
# ===============================

def demonstrate_vector_search():
    """
    Store records with vector embeddings, then search semantically.

    Key Python patterns:
    - db.records.create(..., vectors=[{"propertyName": "field", "vector": [...]}]) for writes
    - db.ai.search({...}) for similarity search
    - record.score — similarity score from search results

    Note: This demo uses mock embeddings. In production, use sentence-transformers
    or OpenAI embeddings to generate real vectors.
    """
    print("\n" + "=" * 60)
    print("PATTERN 3: VECTOR SIMILARITY SEARCH (Python SDK)")
    print("=" * 60)

    # Ensure we have vector data
    existing_articles = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    if existing_articles.total == 0:
        print("\n[SKIP] No articles found. Run `python seed.py` first.")
        return

    # Semantic search: find articles about AI and machine learning
    # Using a natural language query (RushDB embeds it server-side)
    ai_results = db.ai.search({
        "propertyName": "content",
        "query": "machine learning and neural networks",
        "labels": ["ARTICLE"],
        "limit": 5,
    })

    print(f"\n[SEMANTIC SEARCH] Articles about 'machine learning and neural networks':")
    for article in ai_results.data:
        score = article.score if hasattr(article, 'score') else article.data.get('__score', 0)
        print(f"  [{score:.3f}] {article.title}")
        print(f"       Tags: {article.get('tags', [])}")

    # Filter by tag in addition to semantic similarity
    tagged_results = db.ai.search({
        "propertyName": "content",
        "query": "database technology",
        "labels": ["ARTICLE"],
        "where": {"tags": {"$contains": "databases"}},
        "limit": 3,
    })

    print(f"\n[SEMANTIC SEARCH] Articles about 'database technology' tagged 'databases':")
    for article in tagged_results.data:
        print(f"  - {article.title}")

    # Count total indexed articles
    all_articles = db.records.find({"labels": ["ARTICLE"]})
    print(f"\n[INDEX] Total articles: {all_articles.total}")

    print("\n→ Vector search uses natural language queries (server embeds the query)")
    print("→ Combine semantic similarity with standard field filters")
    print("→ record.score gives similarity confidence (higher = more similar)")


# ===============================
# ERGONOMIC COMPARISON SUMMARY
# ===============================

def print_summary():
    print("\n" + "=" * 60)
    print("SDK ERGONOMIC SUMMARY")
    print("=" * 60)
    print("""
| Aspect              | Python SDK               | TypeScript SDK           |
|---------------------|--------------------------|--------------------------|
| Async Model         | Synchronous (blocking)   | async/await (non-blocking)|
| Response Style      | Record objects (dict)   | Typed responses (T[])    |
| Method Names        | snake_case              | camelCase               |
| Transaction Syntax  | with db.transactions...  | await db.tx.begin()     |
| ML/AI Integration   | Native (sentence-transformers)| Via HTTP/external    |
| Web Framework       | Works but less idiomatic | Next.js, Express-native |
| Type Safety         | Duck-typed              | Full TypeScript inference|

When to choose Python:
  → Data pipelines, ETL, batch scripts
  → ML/AI workflows (RAG, embeddings)
  → Rapid prototyping (no async ceremony)

When to choose TypeScript:
  → Web APIs (Next.js, Express)
  → Real-time apps (WebSocket integrations)
  → Full-stack projects (shared types)
""")


# ===============================
# MAIN EXECUTION
# ===============================

def main():
    print("\n" + "#" * 60)
    print("# RushDB Python SDK — Comparison Demo")
    print("# See typescript/ for the equivalent Node.js implementation")
    print("#" * 60)

    demonstrate_crud()
    demonstrate_graph()
    demonstrate_vector_search()
    print_summary()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
