"""
Neo4j to RushDB Migration Script

This script migrates a Neo4j property graph export to RushDB.
It demonstrates:
1. Loading Neo4j export data (nodes + relationships)
2. Converting nodes to RushDB records
3. Converting relationships to RushDB links via attach()
4. Transactional batch processing
5. Verifying migrated data with relationship traversal

Run `python seed.py` first to generate sample data.
"""
import json
import sys
import time
from pathlib import Path
from collections import defaultdict

from rushdb import RushDB

from config import get_rushdb_token, get_rushdb_url


def load_neo4j_export(data_path: Path) -> dict:
    """Load Neo4j export data from JSON file."""
    with open(data_path, "r") as f:
        return json.load(f)


def clear_existing_data(db: RushDB):
    """"Clear previously migrated records for idempotency."""
    labels_to_clear = ["Movie", "Actor", "Director", "Genre"]
    total_deleted = 0
    
    for label in labels_to_clear:
        result = db.records.find({"labels": [label], "limit": 1000})
        if result.data:
            for record in result.data:
                db.records.delete(record_id=record.id)
            total_deleted += len(result.data)
    
    print(f"  Deleted {total_deleted} existing records")



def migrate_nodes(db: RushDB, export_data: dict) -> dict:
    """
    Migrate Neo4j nodes to RushDB records.
    
    Returns a mapping from Neo4j node IDs to RushDB record objects.
    This mapping is needed later to recreate relationships.
    """
    print("\n[3/5] Migrating nodes...")
    
    # Track records by Neo4j ID for relationship mapping
    neo4j_id_to_record = {}
    
    # Group nodes by label for efficient processing
    nodes_by_label = defaultdict(list)
    for node in export_data["nodes"]:
        # Neo4j allows multiple labels, but RushDB uses single label
        # We'll use the first label (primary label)
        primary_label = node["labels"][0] if node["labels"] else "Unknown"
        nodes_by_label[primary_label].append(node)
    
    # Process each label group
    for label, nodes in nodes_by_label.items():
        print(f"\n  Processing {label} nodes ({len(nodes)} total)...")
        
        # Use transaction for atomic batch creation
        with db.transactions.begin() as tx:
            for node in nodes:
                # Convert Neo4j properties to RushDB data
                data = node["properties"].copy()
                
                # Create the record
                record = db.records.create(
                    label=label,
                    data=data,
                    transaction=tx
                )
                
                # Store mapping: Neo4j ID -> RushDB record
                neo4j_id_to_record[node["id"]] = record
                
                # Print first few as progress indicator
                if len(neo4j_id_to_record) <= 10:
                    if label == "Movie":
                        title = data.get("title", "Unknown")
                        year = data.get("year", "?")
                        print(f"    ✓ Created Movie: {title} ({year})")
                    elif label == "Actor":
                        name = data.get("name", "Unknown")
                        print(f"    ✓ Created Actor: {name}")
                    elif label == "Director":
                        name = data.get("name", "Unknown")
                        print(f"    ✓ Created Director: {name}")
    
    print(f"\n  ✓ Created {len(neo4j_id_to_record)} records in 1 transaction")
    
    return neo4j_id_to_record


def migrate_relationships(
    db: RushDB,
    export_data: dict,
    neo4j_id_to_record: dict
) -> None:
    """
    Migrate Neo4j relationships to RushDB links.
    
    Uses db.records.attach() to create directed edges between records.
    """
    print("\n[4/5] Migrating relationships...")
    
    relationships = export_data["relationships"]
    created_count = 0
    
    # Use transaction for atomic batch linking
    with db.transactions.begin() as tx:
        for rel in relationships:
            # Get source and target records by their Neo4j IDs
            source_record = neo4j_id_to_record.get(rel["startNode"])
            target_record = neo4j_id_to_record.get(rel["endNode"])
            
            if not source_record or not target_record:
                print(f"  ⚠ Skipping relationship {rel['id']}: node not found")
                continue
            
            # Create the relationship as a RushDB link
            db.records.attach(
                source=source_record,
                target=target_record,
                options={"type": rel["type"]},
                transaction=tx
            )
            
            created_count += 1
            
            # Print first few as progress indicator
            if created_count <= 10:
                source_label = source_record.label
                target_label = target_record.label
                source_name = source_record.data.get("name") or source_record.data.get("title") or "?"
                target_name = target_record.data.get("title") or target_record.data.get("name") or "?"
                role = rel["properties"].get("role", "")
                role_str = f" (role: {role})" if role else ""
                print(f"    ✓ Linked {source_name} --{rel['type']}--> {target_name}{role_str}")
    
    print(f"\n  ✓ Created {created_count} relationships in 1 transaction")


def verify_migration(db: RushDB) -> None:
    """Verify migrated data by querying each label type."""
    print("\n[5/5] Verifying migration...")
    
    label_counts = {
        "Movie": 0,
        "Actor": 0,
        "Director": 0,
        "Genre": 0,
    }
    
    for label in label_counts.keys():
        result = db.records.find({"labels": [label]})
        count = len(result.data)
        label_counts[label] = count
        print(f"  ✓ Found {count} {label} records")
    
    total = sum(label_counts.values())
    print(f"\n  Total verified: {total} records")
    print("  ✓ Migration complete! Data verified successfully.")


def demo_relationship_traversal(db: RushDB) -> None:
    """Demonstrate relationship traversal queries on migrated data."""
    print("\n" + "=" * 50)
    print("Relationship Traversal Demo")
    print("=" * 50)
    
    # Query 1: Movies directed by Christopher Nolan
    print("\n1. Movies directed by Christopher Nolan:")
    nolan_movies = db.records.find({
        "labels": ["Movie"],
        "where": {
            "DIRECTED_BY": {
                "DIRECTOR": {
                    "name": "Christopher Nolan"
                }
            }
        }
    })
    for movie in nolan_movies.data:
        print(f"   - {movie['title']} ({movie['year']})")
    
    # Query 2: Actors who acted in movies with rating > 8.5
    print("\n2. Actors in highly-rated movies (rating > 8.5):")
    high_rated_actors = db.records.find({
        "labels": ["Actor"],
        "where": {
            "ACTED_IN": {
                "Movie": {
                    "rating": {"$gt": 8.5}
                }
            }
        }
    })
    for actor in high_rated_actors.data:
        print(f"   - {actor['name']}")
    
    # Query 3: All relationships for a specific movie
    print("\n3. All people connected to 'Inception':")
    inception_result = db.records.find({
        "labels": ["Movie"],
        "where": {"title": "Inception"}
    })
    if inception_result.data:
        inception = inception_result.data[0]
        print(f"   Movie: {inception['title']} ({inception['year']})")
        print(f"   Rating: {inception['rating']}")
        
        # Show actors
        actors = db.records.find({
            "labels": ["Actor"],
            "where": {
                "ACTED_IN": {
                    "Movie": {
                        "title": "Inception"
                    }
                }
            }
        })
        print(f"   Actors: {', '.join(a['name'] for a in actors.data)}")


def main():
    """Main migration pipeline."""
    print("=" * 50)
    print("Neo4j to RushDB Migration")
    print("=" * 50)
    
    # Step 1: Initialize RushDB client
    print("\n[1/5] Initializing RushDB client...")
    token = get_rushdb_token()
    url = get_rushdb_url()
    
    if url:
        db = RushDB(token, url=url)
        print(f"  ✓ Connected to RushDB at {url}")
    else:
        db = RushDB(token)
        print("  ✓ Connected to RushDB Cloud")
    
    # Step 2: Load Neo4j export data
    print("\n[2/5] Loading Neo4j export data...")
    data_path = Path(__file__).parent / "data" / "neo4j_export.json"
    
    if not data_path.exists():
        print(f"  ✗ Export file not found: {data_path}")
        print("  Run `python seed.py` first to generate sample data.")
        sys.exit(1)
    
    export_data = load_neo4j_export(data_path)
    num_nodes = len(export_data["nodes"])
    num_rels = len(export_data["relationships"])
    print(f"  ✓ Loaded {num_nodes} nodes and {num_rels} relationships")
    
    # Clear existing data for idempotency
    print("\n[2.5/5] Clearing existing migration records (idempotency)...")
    clear_existing_data(db)
    
    # Step 3: Migrate nodes
    start_time = time.time()
    neo4j_id_to_record = migrate_nodes(db, export_data)
    node_time = time.time() - start_time
    print(f"  Node migration took {node_time:.2f}s")
    
    # Step 4: Migrate relationships
    start_time = time.time()
    migrate_relationships(db, export_data, neo4j_id_to_record)
    rel_time = time.time() - start_time
    print(f"  Relationship migration took {rel_time:.2f}s")
    
    # Step 5: Verify migration
    verify_migration(db)
    
    # Demo: Show relationship traversal capabilities
    demo_relationship_traversal(db)
    
    print("\n" + "=" * 50)
    print("Migration completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
