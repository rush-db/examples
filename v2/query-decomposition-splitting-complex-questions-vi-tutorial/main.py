"""
Query Decomposition: Splitting Complex Questions via Graph Exploration
======================================================================

This tutorial demonstrates how to use RushDB's property graph model for
query decomposition - breaking complex questions into simpler sub-queries
that can be answered independently and combined.

Key patterns demonstrated:
1. Entity identification via property lookup
2. Direct relationship traversal with relationship-based filtering
3. Multi-step decomposition (sequential queries)
4. Result aggregation from multiple sources

Run seed.py first to populate the graph with sample data.
"""

import os
import sys
from collections import defaultdict
from typing import Optional
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB
from dotenv import load_dotenv

load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(API_KEY)


def separator(title: str):
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def example_header(num: int, question: str):
    """Print an example header."""
    print(f"\n--- Example {num}: {question} ---")


# =============================================================================
# QUERY DECOMPOSITION PATTERNS
# =============================================================================

def pattern_1_simple_entity_lookup(question: str, entity_name: str) -> dict:
    """
    Pattern 1: Simple Entity Lookup

    For questions like "Who is X?", we simply find the record and return its properties.

    Decomposition:
      Step 1: Find the entity by name using db.records.find()
      Step 2: Return the entity's properties
    """
    print(f"Question: \"{question}\"")
    print("Decomposition: Identify the entity and fetch basic properties")

    # Find the actor by name
    result = db.records.find({
        "labels": ["ACTOR"],
        "where": {"name": entity_name},
        "limit": 1
    })

    if result.total > 0:
        actor = result.data[0]
        print(f"Result: {actor['name']} is a {actor['nationality']} actor born on {actor['birthDate']}")
        print(f"       Biography: {actor['biography']}")
        return {"status": "success", "entity": actor}
    else:
        print("Result: Entity not found")
        return {"status": "not_found"}


def pattern_2_direct_relationship(question: str, actor_name: str) -> dict:
    """
    Pattern 2: Direct Relationship Traversal

    For questions like "What movies has X acted in?", we use RushDB's
    relationship-based filtering in the where clause.

    Decomposition:
      Step 1: Find all records with ACTED_IN relationship to the actor
              using "where": {"ACTOR": {"name": actor_name}}
    """
    print(f"Question: \"{question}\"")
    print("Decomposition: Find all movies connected via ACTED_IN relationship")

    # Find all movies where this actor ACTED_IN
    # Using relationship-based filtering in the where clause
    result = db.records.find({
        "labels": ["MOVIE"],
        "where": {
            "ACTOR": {"name": actor_name}
        }
    })

    movies = [m.data for m in result.data]
    movie_titles = [m["title"] for m in movies]

    print(f"Result: {result.total} movie(s) found: {', '.join(movie_titles)}")

    # Show additional details
    for movie in movies:
        print(f"       - {movie['title']} ({movie['year']}) - Rating: {movie['rating']}")

    return {"status": "success", "movies": movies}


def pattern_3_multi_hop_traversal(question: str, actor_name: str) -> dict:
    """
    Pattern 3: Multi-Hop Traversal

    For questions like "Who directed X's movies?", we need two hops:
      1. Find the movies the actor acted in
      2. Find the directors of those movies

    Decomposition:
      Step 1: Find all movies the actor acted in
      Step 2: For each movie, find its director
      Step 3: Aggregate unique directors
    """
    print(f"Question: \"{question}\"")
    print("Decomposition:")
    print("  Step 1: Find the actor's movies")
    print("  Step 2: Find directors of those movies")

    # Step 1: Find actor's movies
    movies_result = db.records.find({
        "labels": ["MOVIE"],
        "where": {"ACTOR": {"name": actor_name}}
    })

    if movies_result.total == 0:
        print("Result: No movies found for this actor")
        return {"status": "not_found"}

    movies = movies_result.data
    print(f"\nStep 1 complete: Found {len(movies)} movie(s)")

    # Step 2: Find directors for each movie
    directors_map = defaultdict(list)  # director -> [movies]

    for movie in movies:
        # Find the director of this specific movie
        director_result = db.records.find({
            "labels": ["DIRECTOR"],
            "where": {
                "MOVIE": {"$id": movie.id}
            }
        })

        for director in director_result.data:
            directors_map[director.data["name"]].append(movie.data["title"])

    print(f"\nStep 2 complete: Found {len(directors_map)} director(s)")

    # Print results
    for director_name, directed_movies in directors_map.items():
        count = len(directed_movies)
        print(f"  - {director_name} directed {count} of {actor_name}'s movies: {', '.join(directed_movies)}")

    return {"status": "success", "directors": dict(directors_map)}


def pattern_4_complex_filtering(question: str) -> dict:
    """
    Pattern 4: Complex Filtering with Multiple Criteria

    For questions like "Which actors have won awards for drama movies from the 90s?",
    we chain multiple filters:
      1. Find drama movies from the 90s
      2. Find actors in those movies
      3. Filter to those with awards

    Decomposition:
      Step 1: Find drama movies from 1990-1999
      Step 2: Find all actors in those movies
      Step 3: Filter actors who have received awards
    """
    print(f"Question: \"{question}\"")
    print("Decomposition:")
    print("  Step 1: Find drama movies from the 90s")
    print("  Step 2: Find actors in those movies")
    print("  Step 3: Check which actors have awards")

    # Step 1: Find drama movies from the 90s
    print("\nStep 1: Finding drama movies from 1990-1999...")
    drama_movies_result = db.records.find({
        "labels": ["MOVIE"],
        "where": {
            "year": {"$gte": 1990, "$lte": 1999},
            "GENRE": {"name": "Drama"}
        }
    })

    if drama_movies_result.total == 0:
        print("Result: No drama movies from the 90s found")
        return {"status": "not_found"}

    drama_movies = drama_movies_result.data
    print(f"  Found {len(drama_movies)} drama movie(s) from the 90s")

    # Step 2: Find actors in those movies
    print("\nStep 2: Finding actors in these movies...")
    actors_in_movies = set()

    for movie in drama_movies:
        actors_result = db.records.find({
            "labels": ["ACTOR"],
            "where": {"MOVIE": {"$id": movie.id}}
        })
        for actor in actors_result.data:
            actors_in_movies.add(actor.id)

    print(f"  Found {len(actors_in_movies)} unique actor(s)")

    # Step 3: Filter actors with awards
    print("\nStep 3: Filtering to actors with awards...")
    awarded_actors = []

    for actor_id in actors_in_movies:
        # Find if this actor has any awards
        awards_result = db.records.find({
            "labels": ["AWARD"],
            "where": {
                "ACTOR": {"$id": actor_id}
            }
        })

        if awards_result.total > 0:
            # Get actor details
            actor_data = db.records.find_by_id(actor_id)
            awarded_actors.append({
                "actor": actor_data.data,
                "award_count": awards_result.total
            })

    print(f"  Found {len(awarded_actors)} actor(s) with awards")

    # Print results
    for item in awarded_actors:
        print(f"  - {item['actor']['name']} ({item['award_count']} award(s))")

    return {"status": "success", "actors": awarded_actors}


def pattern_5_aggregation(question: str, director_name: str) -> dict:
    """
    Pattern 5: Aggregating Multi-Source Data

    For questions like "Compare the movies directed by X", we:
      1. Find all movies by that director
      2. Collect all actors across those movies
      3. Aggregate ratings, awards, etc.

    Decomposition:
      Step 1: Find all movies by the director
      Step 2: Collect all actors in those movies
      Step 3: Aggregate statistics
    """
    print(f"Question: \"{question}\"")
    print("Decomposition:")
    print("  Step 1: Find movies directed by the director")
    print("  Step 2: Fetch all actors in those movies")
    print("  Step 3: Aggregate ratings and awards")

    # Step 1: Find movies by director
    print("\nStep 1: Finding movies...")
    movies_result = db.records.find({
        "labels": ["MOVIE"],
        "where": {"DIRECTOR": {"name": director_name}}
    })

    if movies_result.total == 0:
        print("Result: No movies found for this director")
        return {"status": "not_found"}

    movies = movies_result.data
    print(f"  Found {len(movies)} movie(s)")

    # Step 2: Collect all actors
    print("\nStep 2: Collecting actors...")
    all_actors = set()
    total_awards = 0

    for movie in movies:
        actors_result = db.records.find({
            "labels": ["ACTOR"],
            "where": {"MOVIE": {"$id": movie.id}}
        })

        for actor in actors_result.data:
            all_actors.add(actor.data["name"])

        # Count awards for this movie
        awards_result = db.records.find({
            "labels": ["AWARD"],
            "where": {"MOVIE": {"$id": movie.id}}
        })
        total_awards += awards_result.total

    print(f"  Found {len(all_actors)} unique actor(s)")

    # Step 3: Aggregate statistics
    print("\nStep 3: Aggregating statistics...")
    avg_rating = sum(m.data["rating"] for m in movies) / len(movies)
    total_box_office = sum(m.data["boxOffice"] for m in movies)

    print(f"\n  Comparison Summary:")
    print(f"  - Average rating: {avg_rating:.1f}")
    print(f"  - Total box office: ${total_box_office:.1f}M")
    print(f"  - Total awards: {total_awards}")
    print(f"\n  Movies:")
    for movie in movies:
        print(f"    - {movie['title']} ({movie.data['year']}) Rating: {movie.data['rating']}")

    print(f"\n  Actors: {', '.join(sorted(all_actors))}")

    return {
        "status": "success",
        "movies": [m.data for m in movies],
        "actors": list(all_actors),
        "avg_rating": avg_rating,
        "total_awards": total_awards
    }


def pattern_6_chain_decomposition(question: str, actor_name: str) -> dict:
    """
    Pattern 6: Chain Decomposition

    For questions like "Find co-actors who have worked with directors of X's movies",
    we chain multiple queries:
      1. Get X's movies
      2. Get directors of those movies
      3. Get other movies by those directors
      4. Get actors in those other movies

    Decomposition:
      Step 1: Get target actor's movies
      Step 2: Get directors of those movies
      Step 3: Find other movies by those directors
      Step 4: Get actors in those other movies (excluding target actor)
    """
    print(f"Question: \"{question}\"")
    print("Decomposition:")
    print("  Step 1: Get target actor's movies")
    print("  Step 2: Get directors of those movies")
    print("  Step 3: Find other movies by those directors")
    print("  Step 4: Get actors in those other movies")

    # Step 1: Get target actor's movies
    print("\nStep 1: Finding target actor's movies...")
    target_movies_result = db.records.find({
        "labels": ["MOVIE"],
        "where": {"ACTOR": {"name": actor_name}}
    })

    if target_movies_result.total == 0:
        print("Result: No movies found for this actor")
        return {"status": "not_found"}

    target_movie_ids = {m.id for m in target_movies_result.data}
    print(f"  Found {len(target_movie_ids)} movie(s)")

    # Step 2: Get directors of those movies
    print("\nStep 2: Finding directors...")
    director_ids = set()

    for movie_id in target_movie_ids:
        directors_result = db.records.find({
            "labels": ["DIRECTOR"],
            "where": {"MOVIE": {"$id": movie_id}}
        })
        for director in directors_result.data:
            director_ids.add(director.id)

    print(f"  Found {len(director_ids)} director(s)")

    # Step 3: Find other movies by those directors
    print("\nStep 3: Finding other movies by these directors...")
    other_movie_ids = set()

    for director_id in director_ids:
        movies_result = db.records.find({
            "labels": ["MOVIE"],
            "where": {"DIRECTOR": {"$id": director_id}}
        })
        for movie in movies_result.data:
            if movie.id not in target_movie_ids:
                other_movie_ids.add(movie.id)

    print(f"  Found {len(other_movie_ids)} other movie(s)")

    # Step 4: Get actors in those other movies (excluding target actor)
    print("\nStep 4: Finding co-actors...")
    co_actors = []

    for movie_id in other_movie_ids:
        actors_result = db.records.find({
            "labels": ["ACTOR"],
            "where": {"MOVIE": {"$id": movie_id}}
        })

        for actor in actors_result.data:
            if actor.data["name"] != actor_name:
                movie_title = db.records.find_by_id(movie_id).data["title"]
                co_actors.append({
                    "actor": actor.data["name"],
                    "movie": movie_title
                })

    print(f"  Found {len(co_actors)} co-actor appearance(s)")

    # Deduplicate and show
    unique_co_actors = list({c["actor"]: c for c in co_actors}.values())
    print(f"\n  Unique co-actors: {len(unique_co_actors)}")
    for item in unique_co_actors:
        print(f"    - {item['actor']} (via {item['movie']})")

    return {"status": "success", "co_actors": unique_co_actors}


def bonus_pattern_ontology_aware_query(question: str) -> dict:
    """
    Bonus Pattern: Ontology-Aware Query Decomposition

    Before decomposing, we can inspect the database schema (ontology)
    to understand what labels, properties, and relationships exist.

    This is useful for:
      - Building LLM-powered agents that need to understand the schema
      - Self-documenting systems
      - Dynamic query building

    Decomposition:
      Step 1: Get the ontology (schema)
      Step 2: Identify relevant labels and relationships
      Step 3: Build query based on available schema
    """
    print(f"Question: \"{question}\"")
    print("Decomposition:")
    print("  Step 1: Inspect the ontology (schema)")
    print("  Step 2: Identify relevant labels and relationships")
    print("  Step 3: Build query based on available schema")

    # Step 1: Get ontology
    print("\nStep 1: Inspecting database schema...")
    try:
        ontology = db.ai.getOntology()
        labels = ontology.get("labels", [])
        print(f"  Found {len(labels)} labels in the database:")
        for label in labels:
            print(f"    - {label['name']} ({label['recordCount']} records)")
    except Exception as e:
        print(f"  Note: getOntology() not available in this context: {e}")
        # Fallback: list labels directly
        labels_result = db.labels.find({})
        print(f"  Found {len(labels_result)} labels")
        labels = [{"name": l.name} for l in labels_result]

    # Step 2 & 3: Use schema to answer question
    # Question: "Show me high-rated movies with their directors"
    print("\nStep 2 & 3: Building query from schema...")
    print("  Based on schema, we can query MOVIE -> DIRECTOR relationships")

    result = db.records.find({
        "labels": ["MOVIE"],
        "where": {"rating": {"$gte": 8.0}}
    })

    print(f"\n  High-rated movies (≥8.0) found: {result.total}")
    for movie in result.data:
        # Find director for each movie
        director_result = db.records.find({
            "labels": ["DIRECTOR"],
            "where": {"MOVIE": {"$id": movie.id}}
        })
        director_name = director_result.data[0].data["name"] if director_result.total > 0 else "Unknown"
        print(f"    - {movie.data['title']} ({movie.data['year']}) directed by {director_name}")

    return {"status": "success", "count": result.total}


# =============================================================================
# MAIN TUTORIAL EXECUTION
# =============================================================================

def main():
    """Run all query decomposition examples."""

    separator("QUERY DECOMPOSITION TUTORIAL")
    print("\nThis tutorial demonstrates splitting complex questions into simpler")
    print("sub-queries using RushDB's property graph model.")

    # Example 1: Simple Entity Lookup
    example_header(1, "Simple Entity Lookup")
    pattern_1_simple_entity_lookup(
        question="Who is Tom Hanks?",
        entity_name="Tom Hanks"
    )

    # Example 2: Direct Relationship Traversal
    example_header(2, "Relationship Traversal")
    pattern_2_direct_relationship(
        question="What movies has Tom Hanks acted in?",
        actor_name="Tom Hanks"
    )

    # Example 3: Multi-Hop Traversal
    example_header(3, "Multi-Hop Traversal")
    pattern_3_multi_hop_traversal(
        question="Who directed Tom Hanks' movies?",
        actor_name="Tom Hanks"
    )

    # Example 4: Complex Filtering
    example_header(4, "Complex Decomposition")
    pattern_4_complex_filtering(
        question="Which actors have won awards for drama movies from the 90s?"
    )

    # Example 5: Aggregation
    example_header(5, "Aggregating Multi-Source Data")
    pattern_5_aggregation(
        question="Compare the movies directed by Robert Zemeckis",
        director_name="Robert Zemeckis"
    )

    # Example 6: Chain Decomposition
    example_header(6, "Chain Decomposition")
    pattern_6_chain_decomposition(
        question="Find co-actors who have worked with directors of Tom Hanks' movies",
        actor_name="Tom Hanks"
    )

    # Bonus: Ontology-Aware Query
    separator("BONUS: Ontology-Aware Query Decomposition")
    bonus_pattern_ontology_aware_query(
        question="Show me high-rated movies with their directors"
    )

    # Summary
    separator("TUTORIAL COMPLETE!")
    print("""
Key Takeaways:

1. START SIMPLE: Begin with basic entity lookups, then add relationships.

2. USE RELATIONSHIP FILTERING: The "where": {"LABEL": {...}} pattern
   is powerful for direct graph traversal without writing Cypher.

3. CHAIN QUERIES: Complex questions can be broken into sequential steps,
   using results from one query as input for the next.

4. AGGREGATE CAREFULLY: Collect results and use Python (or your language
   of choice) to summarize, compare, and present.

5. KNOW YOUR SCHEMA: Understanding the labels and relationships in your
   graph helps write better decompositions.

Further Exploration:
- Try decomposing your own complex questions
- Experiment with different relationship types
- Combine with vector search for semantic similarity
- Use the ontology endpoint for dynamic schema discovery
""")


if __name__ == "__main__":
    main()
