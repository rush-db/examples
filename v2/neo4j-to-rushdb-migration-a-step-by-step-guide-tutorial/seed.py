"""
Seed script: Generates mock Neo4j export data for migration demo.

This creates a realistic movie database export in a format that mimics
a Neo4j database dump (nodes + relationships).

Run this before migration.py to generate test data.
"""
import json
import random
from pathlib import Path

# Seed data for generating realistic movie database
MOVIES = [
    {"title": "Inception", "year": 2010, "rating": 8.8},
    {"title": "The Matrix", "year": 1999, "rating": 8.7},
    {"title": "Interstellar", "year": 2014, "rating": 8.6},
    {"title": "The Dark Knight", "year": 2008, "rating": 9.0},
    {"title": "Pulp Fiction", "year": 1994, "rating": 8.9},
    {"title": "Fight Club", "year": 1999, "rating": 8.8},
    {"title": "Forrest Gump", "year": 1994, "rating": 8.8},
    {"title": "The Shawshank Redemption", "year": 1994, "rating": 9.3},
    {"title": "Goodfellas", "year": 1990, "rating": 8.7},
    {"title": "The Godfather", "year": 1972, "rating": 9.2},
    {"title": "Schindler's List", "year": 1993, "rating": 9.0},
    {"title": "Se7en", "year": 1995, "rating": 8.6},
    {"title": "Memento", "year": 2000, "rating": 8.4},
    {"title": "The Prestige", "year": 2006, "rating": 8.5},
    {"title": "Dunkirk", "year": 2017, "rating": 7.8},
    {"title": "Blade Runner 2049", "year": 2017, "rating": 8.0},
    {"title": "John Wick", "year": 2014, "rating": 7.4},
    {"title": "John Wick: Chapter 2", "year": 2017, "rating": 7.5},
    {"title": "The Departed", "year": 2006, "rating": 8.5},
    {"title": "Whiplash", "year": 2014, "rating": 8.5},
    {"title": "The Social Network", "year": 2010, "rating": 7.8},
    {"title": "Django Unchained", "year": 2012, "rating": 8.4},
    {"title": "Inglourious Basterds", "year": 2009, "rating": 8.3},
    {"title": "Shutter Island", "year": 2010, "rating": 7.8},
    {"title": "Batman Begins", "year": 2005, "rating": 8.2},
    {"title": "Taxi Driver", "year": 1976, "rating": 8.2},
    {"title": "Good Will Hunting", "year": 1997, "rating": 8.3},
    {"title": "The Green Mile", "year": 1999, "rating": 8.6},
    {"title": "Catch Me If You Can", "year": 2002, "rating": 8.1},
    {"title": "Catch Me If You Can", "year": 2002, "rating": 8.1},
]

ACTORS = [
    {"name": "Leonardo DiCaprio", "birth_year": 1974, "nationality": "American"},
    {"name": "Christian Bale", "birth_year": 1974, "nationality": "British"},
    {"name": "Keanu Reeves", "birth_year": 1964, "nationality": "Canadian"},
    {"name": "Morgan Freeman", "birth_year": 1937, "nationality": "American"},
    {"name": "Tom Hanks", "birth_year": 1956, "nationality": "American"},
    {"name": "Brad Pitt", "birth_year": 1963, "nationality": "American"},
    {"name": "Samuel L. Jackson", "birth_year": 1948, "nationality": "American"},
    {"name": "Robert De Niro", "birth_year": 1943, "nationality": "American"},
    {"name": "Matt Damon", "birth_year": 1970, "nationality": "American"},
    {"name": "Michael Caine", "birth_year": 1933, "nationality": "British"},
    {"name": "Tom Hardy", "birth_year": 1977, "nationality": "British"},
    {"name": "Joseph Gordon-Levitt", "birth_year": 1981, "nationality": "American"},
    {"name": "Marion Cotillard", "birth_year": 1975, "nationality": "French"},
    {"name": "Ellen Page", "birth_year": 1987, "nationality": "Canadian"},
    {"name": "Laurence Fishburne", "birth_year": 1961, "nationality": "American"},
    {"name": "Carrie-Anne Moss", "birth_year": 1967, "nationality": "Canadian"},
    {"name": "Halle Berry", "birth_year": 1966, "nationality": "American"},
    {"name": "Willem Dafoe", "birth_year": 1955, "nationality": "American"},
    {"name": "John Travolta", "birth_year": 1954, "nationality": "American"},
    {"name": "Uma Thurman", "birth_year": 1970, "nationality": "American"},
    {"name": "Bruce Willis", "birth_year": 1955, "nationality": "German"},
    {"name": "Quentin Tarantino", "birth_year": 1963, "nationality": "American"},
    {"name": "Tim Burton", "birth_year": 1958, "nationality": "American"},
]

DIRECTORS = [
    {"name": "Christopher Nolan", "birth_year": 1970, "nationality": "British"},
    {"name": "Quentin Tarantino", "birth_year": 1963, "nationality": "American"},
    {"name": "Martin Scorsese", "birth_year": 1942, "nationality": "American"},
    {"name": "Frank Darabont", "birth_year": 1959, "nationality": "American"},
    {"name": "David Fincher", "birth_year": 1962, "nationality": "American"},
    {"name": "Ridley Scott", "birth_year": 1937, "nationality": "British"},
    {"name": "Steven Spielberg", "birth_year": 1946, "nationality": "American"},
    {"name": "The Wachowskis", "birth_year": 1965, "nationality": "American"},
]

GENRES = ["Action", "Drama", "Thriller", "Sci-Fi", "Crime", "Biography", "Mystery"]

# Role templates for ACTED_IN relationships
ROLES = [
    "Lead Role",
    "Supporting Role",
    "Villain",
    "Mentor",
    "Sidekick",
    "Anti-hero",
    "Narrator",
    "Cameo",
]


def generate_neo4j_export():
    """Generate a mock Neo4j export with nodes and relationships."""
    nodes = []
    relationships = []
    node_id_counter = 1

    # Create Movie nodes
    movie_ids = {}
    for movie in MOVIES:
        movie_id = str(node_id_counter)
        node_id_counter += 1
        movie_ids[movie["title"]] = movie_id
        nodes.append({
            "id": movie_id,
            "labels": ["Movie"],
            "properties": {
                "title": movie["title"],
                "year": movie["year"],
                "rating": movie["rating"],
            }
        })
        print(f"  Created Movie node: {movie['title']}")


    print(f"\n  Total movies: {len(movie_ids)}")

    # Create Actor nodes
    actor_ids = {}
    for actor in ACTORS:
        actor_id = str(node_id_counter)
        node_id_counter += 1
        actor_ids[actor["name"]] = actor_id
        nodes.append({
            "id": actor_id,
            "labels": ["Actor"],
            "properties": {
                "name": actor["name"],
                "birth_year": actor["birth_year"],
                "nationality": actor["nationality"],
            }
        })
        print(f"  Created Actor node: {actor['name']}")

    print(f"\n  Total actors: {len(actor_ids)}")

    # Create Director nodes
    director_ids = {}
    for director in DIRECTORS:
        director_id = str(node_id_counter)
        node_id_counter += 1
        director_ids[director["name"]] = director_id
        nodes.append({
            "id": director_id,
            "labels": ["Director"],
            "properties": {
                "name": director["name"],
                "birth_year": director["birth_year"],
                "nationality": director["nationality"],
            }
        })
        print(f"  Created Director node: {director['name']}")

    print(f"\n  Total directors: {len(director_ids)}")

    # Create Genre nodes
    genre_ids = {}
    for genre in GENRES:
        genre_id = str(node_id_counter)
        node_id_counter += 1
        genre_ids[genre] = genre_id
        nodes.append({
            "id": genre_id,
            "labels": ["Genre"],
            "properties": {
                "name": genre,
            }
        })

    print(f"  Created Genre nodes: {', '.join(GENRES)}")

    # Create ACTED_IN relationships
    used_combos = set()
    for movie_title, movie_id in movie_ids.items():
        # Pick 1-3 random actors per movie
        num_actors = random.randint(1, 3)
        shuffled_actors = list(actor_ids.keys())
        random.shuffle(shuffled_actors)
        
        for i, actor_name in enumerate(shuffled_actors[:num_actors]):
            actor_id = actor_ids[actor_name]
            combo = (movie_id, actor_id)
            if combo in used_combos:
                continue
            used_combos.add(combo)
            
            rel_id = str(node_id_counter)
            node_id_counter += 1
            relationships.append({
                "id": rel_id,
                "type": "ACTED_IN",
                "startNode": actor_id,
                "endNode": movie_id,
                "properties": {
                    "role": random.choice(ROLES),
                    "salary": random.randint(100000, 5000000),
                }
            })
            print(f"  Created ACTED_IN: {actor_name} -> {movie_title}")

    print(f"\n  Total ACTED_IN relationships: {len([r for r in relationships if r['type'] == 'ACTED_IN'])}")

    # Create DIRECTED relationships (Nolan directs most movies, others direct fewer)
    director_assignments = {
        "Christopher Nolan": list(movie_ids.keys())[:15],
        "Quentin Tarantino": ["Pulp Fiction", "Django Unchained", "Inglourious Basterds", "Kill Bill"],
        "Martin Scorsese": ["Goodfellas", "The Departed", "Shutter Island", "Casino", "Gangs of New York"],
        "Frank Darabont": ["The Shawshank Redemption", "The Green Mile", "The Mist"],
        "David Fincher": ["Fight Club", "Se7en", "The Social Network", "Zodiac"],
        "Steven Spielberg": ["Schindler's List", "Saving Private Ryan", "Catch Me If You Can"],
        "The Wachowskis": ["The Matrix", "The Matrix Reloaded", "The Matrix Revolutions"],
    }

    for director_name, movies in director_assignments.items():
        if director_name not in director_ids:
            continue
        director_id = director_ids[director_name]
        for movie_title in movies:
            if movie_title not in movie_ids:
                continue
            movie_id = movie_ids[movie_title]
            rel_id = str(node_id_counter)
            node_id_counter += 1
            relationships.append({
                "id": rel_id,
                "type": "DIRECTED",
                "startNode": director_id,
                "endNode": movie_id,
                "properties": {
                    "budget": random.randint(5000000, 200000000),
                    "box_office": random.randint(10000000, 800000000),
                }
            })
            print(f"  Created DIRECTED: {director_name} -> {movie_title}")


    print(f"\n  Total DIRECTED relationships: {len([r for r in relationships if r['type'] == 'DIRECTED'])}")

    # Create BELONGS_TO relationships (movies have genres)
    for movie_title, movie_id in movie_ids.items():
        # Assign 1-2 random genres per movie
        num_genres = random.randint(1, 2)
        shuffled_genres = random.sample(GENRES, min(num_genres, len(GENRES)))
        for genre in shuffled_genres:
            genre_id = genre_ids[genre]
            rel_id = str(node_id_counter)
            node_id_counter += 1
            relationships.append({
                "id": rel_id,
                "type": "BELONGS_TO",
                "startNode": movie_id,
                "endNode": genre_id,
                "properties": {}
            })
            print(f"  Created BELONGS_TO: {movie_title} -> {genre}")


    print(f"\n  Total BELONGS_TO relationships: {len([r for r in relationships if r['type'] == 'BELONGS_TO'])}")

    return {
        "nodes": nodes,
        "relationships": relationships,
    }


def main():
    """Generate and save Neo4j export data."""
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "neo4j_export.json"
    
    print("=" * 50)
    print("Generating Mock Neo4j Export Data")
    print("=" * 50)
    print()
    
    export_data = generate_neo4j_export()
    
    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2)
    
    print()
    print("=" * 50)
    print(f"Export saved to: {output_path}")
    print(f"Total nodes: {len(export_data['nodes'])}")
    print(f"Total relationships: {len(export_data['relationships'])}")
    print("=" * 50)


if __name__ == "__main__":
    main()
