"""
Seed script for Query Decomposition Tutorial

Creates a rich movie knowledge graph with actors, movies, directors, genres,
and various relationships to demonstrate query decomposition patterns.

Run this once before main.py to populate the database with sample data.
The script is idempotent - running multiple times is safe (checks for existing data).
"""

import os
import sys
from pathlib import Path
from datetime import datetime

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

# Check if data already exists
def check_existing_data():
    """Check if the graph already has data by looking for a known record."""
    existing = db.records.find({
        "labels": ["ACTOR"],
        "where": {"name": "Tom Hanks"},
        "limit": 1
    })
    return existing.total > 0

def seed_graph():
    """Create the movie knowledge graph."""
    print("\n" + "=" * 50)
    print("SEEDING MOVIE KNOWLEDGE GRAPH")
    print("=" * 50)

    # Check for existing data
    if check_existing_data():
        print("\nData already exists! Skipping seed.")
        print("Run main.py to see the query decomposition examples.")
        return

    print("\nCreating entities...")

    # ========================================
    # ACTORS
    # ========================================
    actors_data = [
        {"name": "Tom Hanks", "birthDate": "1956-07-09", "nationality": "American", "biography": "Two-time Academy Award winner known for roles in Forrest Gump and Philadelphia"},
        {"name": "Michael Clarke Duncan", "birthDate": "1957-12-10", "nationality": "American", "biography": "Acclaimed actor best known for The Green Mile and Friday"},
        {"name": "Helen Hunt", "birthDate": "1963-06-15", "nationality": "American", "biography": "Academy Award winner known for As Good as It Gets"},
        {"name": "Robin Wright", "birthDate": "1966-04-08", "nationality": "American", "biography": "Versatile actress known for Forest Gump and House of Cards"},
        {"name": "Gary Sinise", "birthDate": "1955-05-17", "nationality": "American", "biography": "Known for Apollo 13 and Forrest Gump"},
        {"name": "David Morse", "birthDate": "1953-10-11", "nationality": "American", "biography": "Known for The Green Mile and St. Elsewhere"},
        {"name": "Bob Gunton", "birthDate": "1945-11-15", "nationality": "American", "biography": "Known for The Shawshank Redemption and JFK"},
        {"name": "Sam Rockwell", "birthDate": "1968-11-05", "nationality": "American", "biography": "Versatile character actor with multiple Academy Award nominations"},
        {"name": "Paul Giamatti", "birthDate": "1967-06-06", "nationality": "American", "biography": "Known for Sideways, Cinderella Man, and The Illusionist"},
        {"name": "Marion Cotillard", "birthDate": "1975-09-30", "nationality": "French", "biography": "Academy Award winner known for La Vie en Rose and Inception"},
    ]

    actors = []
    for i, actor_data in enumerate(actors_data):
        actor = db.records.create(label="ACTOR", data=actor_data)
        actors.append(actor)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(actors_data)} actors...")

    print(f"  Created {len(actors)} actors total")

    # ========================================
    # DIRECTORS
    # ========================================
    directors_data = [
        {"name": "Robert Zemeckis", "birthDate": "1952-05-14", "nationality": "American", "biography": "Academy Award-winning director known for Forrest Gump and Back to the Future"},
        {"name": "Frank Darabont", "birthDate": "1959-01-28", "nationality": "American", "biography": "Known for The Green Mile, The Shawshank Redemption, and The Majestic"},
        {"name": "James Cameron", "birthDate": "1954-08-16", "nationality": "Canadian", "biography": "Director of Avatar, Titanic, and The Terminator"},
        {"name": "Christopher Nolan", "birthDate": "1970-07-30", "nationality": "British", "biography": "Acclaimed director known for Inception, The Dark Knight, and Interstellar"},
    ]

    directors = []
    for director_data in directors_data:
        director = db.records.create(label="DIRECTOR", data=director_data)
        directors.append(director)

    print(f"  Created {len(directors)} directors")

    # ========================================
    # GENRES
    # ========================================
    genres_data = [
        {"name": "Drama", "description": "Dramatic films focused on character development and emotional themes"},
        {"name": "Sci-Fi", "description": "Science fiction exploring futuristic concepts and technology"},
        {"name": "Romance", "description": "Films focused on romantic relationships and love stories"},
        {"name": "Adventure", "description": "Action-packed films with exciting journeys and challenges"},
    ]

    genres = []
    for genre_data in genres_data:
        genre = db.records.create(label="GENRE", data=genre_data)
        genres.append(genre)

    print(f"  Created {len(genres)} genres")

    # ========================================
    # MOVIES
    # ========================================
    movies_data = [
        {"title": "Forrest Gump", "year": 1994, "rating": 8.8, "duration": 142, "boxOffice": 678.2, "description": "The story of a man with a low IQ who accomplishes great things in life."},
        {"title": "The Green Mile", "year": 1999, "rating": 8.6, "duration": 189, "boxOffice": 287.0, "description": "A death row guard forms a bond with a gentle giant prisoner with supernatural abilities."},
        {"title": "Cast Away", "year": 2000, "rating": 7.8, "duration": 143, "boxOffice": 429.6, "description": "A FedEx executive stranded on an uninhabited island after a plane crash."},
        {"title": "The Shawshank Redemption", "year": 1994, "rating": 9.3, "duration": 142, "boxOffice": 58.3, "description": "Two imprisoned men bond over years, finding solace and eventual redemption."},
        {"title": "Inception", "year": 2010, "rating": 8.8, "duration": 148, "boxOffice": 836.8, "description": "A skilled thief who steals secrets through dream-sharing technology."},
        {"title": "Apollo 13", "year": 1995, "rating": 7.7, "duration": 140, "boxOffice": 355.2, "description": "NASA's mission to safely return three astronauts after an oxygen tank explosion."},
        {"title": "Saving Private Ryan", "year": 1998, "rating": 8.6, "duration": 169, "boxOffice": 482.3, "description": "A group of soldiers are sent to bring back a paratrooper behind enemy lines."},
        {"title": "The Terminal", "year": 2004, "rating": 7.4, "duration": 128, "boxOffice": 219.4, "description": "A man becomes stuck at JFK Airport due to his country's political revolution."},
    ]

    movies = []
    for i, movie_data in enumerate(movies_data):
        movie = db.records.create(label="MOVIE", data=movie_data)
        movies.append(movie)
        if (i + 1) % 4 == 0:
            print(f"  Created {i + 1}/{len(movies_data)} movies...")

    print(f"  Created {len(movies)} movies total")

    # ========================================
    # AWARDS
    # ========================================
    awards_data = [
        {"name": "Academy Award for Best Actor", "year": 1994, "category": "Best Actor"},
        {"name": "Golden Globe Award", "year": 1995, "category": "Best Actor"},
        {"name": "Screen Actors Guild Award", "year": 1995, "category": "Outstanding Performance"},
        {"name": "Academy Award for Best Picture", "year": 1995, "category": "Best Picture"},
        {"name": "BAFTA Award", "year": 1995, "category": "Best Film"},
        {"name": "Academy Award for Best Adapted Screenplay", "year": 2000, "category": "Best Screenplay"},
        {"name": "Academy Award for Best Original Score", "year": 2011, "category": "Best Score"},
        {"name": "Cannes Film Festival Award", "year": 1994, "category": "Palm d'Or"},
    ]

    awards = []
    for award_data in awards_data:
        award = db.records.create(label="AWARD", data=award_data)
        awards.append(award)

    print(f"  Created {len(awards)} awards")

    # ========================================
    # RELATIONSHIPS
    # ========================================
    print("\nCreating relationships...")

    # Movie index mapping for easier reference
    movie_map = {m.data["title"]: m for m in movies}
    actor_map = {a.data["name"]: a for a in actors}
    director_map = {d.data["name"]: d for d in directors}
    genre_map = {g.data["name"]: g for g in genres}

    # ACTED_IN relationships
    acted_in_relations = [
        # Forrest Gump
        ("Tom Hanks", "Forrest Gump"),
        ("Robin Wright", "Forrest Gump"),
        ("Gary Sinise", "Forrest Gump"),
        # The Green Mile
        ("Tom Hanks", "The Green Mile"),
        ("Michael Clarke Duncan", "The Green Mile"),
        ("David Morse", "The Green Mile"),
        ("Bob Gunton", "The Green Mile"),
        # Cast Away
        ("Tom Hanks", "Cast Away"),
        ("Helen Hunt", "Cast Away"),
        # The Shawshank Redemption
        ("Bob Gunton", "The Shawshank Redemption"),
        ("Sam Rockwell", "The Shawshank Redemption"),
        # Inception
        ("Marion Cotillard", "Inception"),
        # Apollo 13
        ("Tom Hanks", "Apollo 13"),
        ("Bill Paxton", "Apollo 13"),
        # Saving Private Ryan
        ("Tom Hanks", "Saving Private Ryan"),
        ("Matt Damon", "Saving Private Ryan"),
        # The Terminal
        ("Tom Hanks", "The Terminal"),
        ("Catherine Zeta-Jones", "The Terminal"),
    ]

    # Add Bill Paxton and Catherine Zeta-Jones if not in actors
    if "Bill Paxton" not in actor_map:
        bp = db.records.create(label="ACTOR", data={"name": "Bill Paxton", "birthDate": "1955-05-17", "nationality": "American", "biography": "Known for Apollo 13 and Twister"})
        actors.append(bp)
        actor_map["Bill Paxton"] = bp

    if "Catherine Zeta-Jones" not in actor_map:
        cz = db.records.create(label="ACTOR", data={"name": "Catherine Zeta-Jones", "birthDate": "1969-09-25", "nationality": "Welsh", "biography": "Known for The Mask of Zorro and Chicago"})
        actors.append(cz)
        actor_map["Catherine Zeta-Jones"] = cz

    # Re-create mapping after potential new actors
    actor_map = {a.data["name"]: a for a in actors}

    for actor_name, movie_title in acted_in_relations:
        actor = actor_map.get(actor_name)
        movie = movie_map.get(movie_title)
        if actor and movie:
            db.records.attach(source=movie, target=actor, options={"type": "ACTED_IN", "direction": "out"})

    print(f"  Created {len(acted_in_relations)} ACTED_IN relationships")

    # DIRECTED relationships
    directed_relations = [
        ("Robert Zemeckis", "Forrest Gump"),
        ("Robert Zemeckis", "Cast Away"),
        ("Robert Zemeckis", "Apollo 13"),
        ("Frank Darabont", "The Green Mile"),
        ("Frank Darabont", "The Shawshank Redemption"),
        ("Christopher Nolan", "Inception"),
        ("Steven Spielberg", "Saving Private Ryan"),
        ("Steven Spielberg", "The Terminal"),
    ]

    # Add Steven Spielberg and Bill Paxton to actors/directors
    if "Steven Spielberg" not in director_map:
        ss = db.records.create(label="DIRECTOR", data={"name": "Steven Spielberg", "birthDate": "1946-12-18", "nationality": "American", "biography": "Legendary director of Jaws, E.T., and Schindler's List"})
        directors.append(ss)
        director_map["Steven Spielberg"] = ss

    for director_name, movie_title in directed_relations:
        director = director_map.get(director_name)
        movie = movie_map.get(movie_title)
        if director and movie:
            db.records.attach(source=movie, target=director, options={"type": "DIRECTED", "direction": "out"})

    print(f"  Created {len(directed_relations)} DIRECTED relationships")

    # BELONGS_TO relationships (movie to genre)
    belongs_to_relations = [
        ("Forrest Gump", "Drama"),
        ("Forrest Gump", "Romance"),
        ("The Green Mile", "Drama"),
        ("Cast Away", "Drama"),
        ("Cast Away", "Adventure"),
        ("The Shawshank Redemption", "Drama"),
        ("Inception", "Sci-Fi"),
        ("Inception", "Adventure"),
        ("Apollo 13", "Drama"),
        ("Saving Private Ryan", "Drama"),
        ("Saving Private Ryan", "Adventure"),
        ("The Terminal", "Drama"),
        ("The Terminal", "Comedy"),
    ]

    # Add Comedy genre
    if "Comedy" not in genre_map:
        cg = db.records.create(label="GENRE", data={"name": "Comedy", "description": "Films intended to make audiences laugh"})
        genres.append(cg)
        genre_map["Comedy"] = cg

    for movie_title, genre_name in belongs_to_relations:
        movie = movie_map.get(movie_title)
        genre = genre_map.get(genre_name)
        if movie and genre:
            db.records.attach(source=movie, target=genre, options={"type": "BELONGS_TO", "direction": "out"})

    print(f"  Created {len(belongs_to_relations)} BELONGS_TO relationships")

    # AWARDED relationships (awards given to actors)
    awarded_relations = [
        ("Tom Hanks", "Academy Award for Best Actor"),
        ("Tom Hanks", "Golden Globe Award"),
        ("Tom Hanks", "Screen Actors Guild Award"),
        ("Tom Hanks", "Academy Award for Best Picture"),
        ("The Shawshank Redemption", "BAFTA Award"),
        ("Inception", "Academy Award for Best Original Score"),
        ("Forrest Gump", "Cannes Film Festival Award"),
    ]

    award_map = {a.data["name"]: a for a in awards}

    for actor_name, award_name in awarded_relations:
        actor = actor_map.get(actor_name)
        movie = movie_map.get(actor_name)  # Check if it's a movie name

        # If not an actor, it might be a movie
        entity = actor
        if not entity:
            entity = movie_map.get(actor_name)

        award = award_map.get(award_name)
        if entity and award:
            db.records.attach(source=entity, target=award, options={"type": "AWARDED", "direction": "out"})

    print(f"  Created {len(awarded_relations)} AWARDED relationships")

    print("\n" + "=" * 50)
    print("SEEDING COMPLETE!")
    print("=" * 50)
    print(f"\nSummary:")
    print(f"  - {len(actors)} actors")
    print(f"  - {len(directors)} directors")
    print(f"  - {len(genres)} genres")
    print(f"  - {len(movies)} movies")
    print(f"  - {len(awards)} awards")
    print(f"  - {len(acted_in_relations)} acted in relationships")
    print(f"  - {len(directed_relations)} directed relationships")
    print(f"  - {len(belongs_to_relations)} belongs to relationships")
    print(f"  - {len(awarded_relations)} awarded relationships")
    print("\nRun main.py to see query decomposition in action!")

if __name__ == "__main__":
    seed_graph()
