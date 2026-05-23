"""
Multi-Hop Question Answerer with RushDB's Traversal API

This module demonstrates how to build a multi-hop question answering system
using RushDB's graph traversal capabilities. Each step chains semantic search
results through relationship edges to answer complex questions.

Example questions:
- Single-hop: "Who are AI researchers?"
- Two-hop: "What organizations do AI researchers work at?"
- Three-hop: "What cities host organizations with AI researchers?"
- Four-hop: "Who are AI researchers in tech companies in California?"
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

# ============================================================================
# EMBEDDING UTILITIES
# ============================================================================

# Using all-MiniLM-L6-v2: fast, good quality, 384 dimensions
# This model is ideal for tutorial code because it's:
# - Fast: suitable for development/demo scenarios
# - Small: easy to install, low memory footprint
# - High quality: competitive with larger models on semantic similarity tasks
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


def get_embedding_model():
    """Load and cache the embedding model."""
    if not hasattr(get_embedding_model, "_model"):
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        get_embedding_model._model = SentenceTransformer(EMBEDDING_MODEL)
        print("Embedding model loaded.")
    return get_embedding_model._model


def generate_embeddings(texts):
    """Generate embeddings for a list of texts.

    Returns a numpy array of shape (len(texts), EMBEDDING_DIMENSIONS)
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings


def create_vector_index(db):
    """Create vector indexes for semantic search on all entity types."""
    labels_properties = [
        ("PERSON", "description"),
        ("ORGANIZATION", "description"),
        ("LOCATION", "description"),
    ]

    for label, prop in labels_properties:
        try:
            db.ai.indexes.create({
                "label": label,
                "propertyName": prop,
                "sourceType": "external",
                "dimensions": EMBEDDING_DIMENSIONS,
            })
            print(f"✓ Created index for {label}.{prop}")
        except Exception as e:
            # Index might already exist
            print(f"  Index for {label}.{prop} already exists or error: {e}")


# ============================================================================
# STEP 1: SINGLE-HOP VECTOR SEARCH
# ============================================================================

def single_hop_search(db, query_text, limit=5):
    """Find records via semantic similarity search.

    This is the foundation of multi-hop Q&A - start with meaning-based search.

    Args:
        db: RushDB instance
        query_text: Natural language query (will be embedded)
        limit: Maximum number of results

    Returns:
        List of matching Person records with similarity scores
    """
    print(f"\nSearching for: '{query_text}'")

    results = db.ai.search({
        "propertyName": "description",
        "query": query_text,
        "labels": ["PERSON"],
        "limit": limit,
    })

    return results.data


# ============================================================================
# STEP 2: TWO-HOP TRAVERSAL
# ============================================================================

def two_hop_search(db, query_text, limit=5):
    """Chain semantic search through one relationship type.

    Find people matching the query, then traverse to their organizations.

    Question pattern: "What [target] do [seed] who match [query] [relate to]?"
    Example: "What organizations do AI researchers work at?"
    """
    print(f"\nQuery: '{query_text}'")
    print("Path: PERSON → ORGANIZATION")

    # Step 2a: Find initial candidates via semantic search
    candidates = db.ai.search({
        "propertyName": "description",
        "query": query_text,
        "labels": ["PERSON"],
        "limit": 10,
    }).data

    if not candidates:
        return []

    candidate_ids = [c.id for c in candidates]
    candidate_scores = {c.id: c.score for c in candidates}
    print(f"  Step 1: Found {len(candidates)} matching people")

    # Step 2b: Traverse WORKS_AT relationships to organizations
    organizations = db.records.find({
        "labels": ["ORGANIZATION"],
        "where": {
            "PERSON": {
                "$relation": {"type": "WORKS_AT", "direction": "in"},
                "$id": {"$in": candidate_ids},
            }
        },
        "limit": limit,
    }).data

    print(f"  Step 2: Found {len(organizations)} organizations via WORKS_AT")

    # Step 2c: Score results based on source record similarity
    for org in organizations:
        # Accumulate scores from source candidates
        related_persons = db.records.find({
            "labels": ["PERSON"],
            "where": {
                "ORGANIZATION": {
                    "$relation": {"type": "WORKS_AT", "direction": "in"},
                    "$id": org.id,
                }
            },
        }).data

        # Average score of related persons (weighted by semantic similarity)
        if related_persons:
            avg_score = sum(candidate_scores.get(p.id, 0) for p in related_persons) / len(related_persons)
            org._hop_score = avg_score * 0.9  # Slight penalty for hop distance

    return organizations


# ============================================================================
# STEP 3: THREE-HOP TRAVERSAL
# ============================================================================

def three_hop_search(db, query_text, limit=5):
    """Extend two-hop to three hops through the knowledge graph.

    Find people matching query → their organizations → organization locations.

    Question pattern: "What [target] are [rel1] [seed] who [rel2] [rel3]?"
    Example: "What cities host organizations with AI researchers?"
    """
    print(f"\nQuery: '{query_text}'")
    print("Path: PERSON → ORGANIZATION → LOCATION")

    # Step 3a: Find initial candidates
    candidates = db.ai.search({
        "propertyName": "description",
        "query": query_text,
        "labels": ["PERSON"],
        "limit": 10,
    }).data

    if not candidates:
        return []

    candidate_ids = [c.id for c in candidates]
    candidate_scores = {c.id: c.score for c in candidates}
    print(f"  Step 1: Found {len(candidates)} matching people")

    # Step 3b: Traverse to organizations
    organizations = db.records.find({
        "labels": ["ORGANIZATION"],
        "where": {
            "PERSON": {
                "$relation": {"type": "WORKS_AT", "direction": "in"},
                "$id": {"$in": candidate_ids},
            }
        },
        "limit": 20,
    }).data

    if not organizations:
        return []

    org_ids = [o.id for o in organizations]
    print(f"  Step 2: Found {len(organizations)} organizations")

    # Step 3c: Traverse to locations
    locations = db.records.find({
        "labels": ["LOCATION"],
        "where": {
            "ORGANIZATION": {
                "$relation": {"type": "LOCATED_IN", "direction": "in"},
                "$id": {"$in": org_ids},
            }
        },
        "limit": limit,
    }).data

    print(f"  Step 3: Found {len(locations)} locations")

    # Step 3d: Score by accumulated hop scores
    for loc in locations:
        # Find organizations that connect to this location
        related_orgs = db.records.find({
            "labels": ["ORGANIZATION"],
            "where": {
                "LOCATION": {
                    "$relation": {"type": "LOCATED_IN", "direction": "in"},
                    "$id": loc.id,
                }
            },
        }).data

        # Score based on average organization score (which inherits from person)
        if related_orgs:
            # Get max person score for each org
            org_max_scores = []
            for org in related_orgs:
                persons = db.records.find({
                    "labels": ["PERSON"],
                    "where": {
                        "ORGANIZATION": {
                            "$relation": {"type": "WORKS_AT", "direction": "in"},
                            "$id": org.id,
                        }
                    },
                }).data
                if persons:
                    max_person_score = max(candidate_scores.get(p.id, 0) for p in persons)
                    org_max_scores.append(max_person_score)

            if org_max_scores:
                loc._hop_score = (sum(org_max_scores) / len(org_max_scores)) * 0.8

    return locations


# ============================================================================
# STEP 4: PARAMETERIZED N-HOP QUERY FUNCTION
# ============================================================================

def traverse_to_related(record_ids, source_label, target_label, relation_type, db):
    """Helper: traverse from records to related records via relationship.

    Args:
        record_ids: List of source record IDs
        source_label: Label of source records (for filtering)
        target_label: Label of target records to find
        relation_type: Type of relationship to traverse
        db: RushDB instance

    Returns:
        List of target records
    """
    if not record_ids:
        return []

    results = db.records.find({
        "labels": [target_label],
        "where": {
            source_label: {
                "$relation": {"type": relation_type, "direction": "in"},
                "$id": {"$in": record_ids},
            }
        },
        "limit": 50,
    })

    return results.data


def multi_hop_search(db, query_text, num_hops=2, labels=None, limit=5):
    """Parameterized multi-hop query that handles any number of hops.

    This is the core function for multi-hop Q&A - reuse one function for
    1, 2, 3, or more hops by changing parameters.

    Args:
        db: RushDB instance
        query_text: Natural language query for initial semantic search
        num_hops: Number of relationship traversals after initial search
        labels: List of labels for each hop (default: PERSON, ORGANIZATION, LOCATION)
        limit: Maximum results to return

    Returns:
        List of final target records with accumulated scores

    The traversal path uses these relationship types:
        PERSON → ORGANIZATION: WORKS_AT
        ORGANIZATION → LOCATION: LOCATED_IN
        PERSON → LOCATION: LOCATED_IN (direct)
        PERSON → PERSON: KNOWS
    """
    # Default labels and relationship types
    default_labels = ["PERSON", "ORGANIZATION", "LOCATION"]
    default_relations = {
        ("PERSON", "ORGANIZATION"): "WORKS_AT",
        ("ORGANIZATION", "LOCATION"): "LOCATED_IN",
        ("PERSON", "LOCATION"): "LOCATED_IN",
        ("PERSON", "PERSON"): "KNOWS",
    }

    labels = labels or default_labels[:num_hops + 1]

    print(f"\nQuery: '{query_text}'")
    print(f"Path: {' → '.join(labels[:num_hops + 1])}")

    # Step 1: Initial semantic search on first label
    initial_results = db.ai.search({
        "propertyName": "description",
        "query": query_text,
        "labels": [labels[0]],
        "limit": 10,
    }).data

    if not initial_results:
        print(f"  No initial matches found for '{query_text}'")
        return []

    # Store scores for accumulation
    current_ids = [r.id for r in initial_results]
    current_scores = {r.id: r.score for r in initial_results}

    print(f"  Step 1: Found {len(initial_results)} matching {labels[0]} records")

    # Step 2+: Traverse each hop
    for hop_idx in range(1, num_hops + 1):
        if hop_idx >= len(labels):
            break

        source_label = labels[hop_idx - 1]
        target_label = labels[hop_idx]
        relation_type = default_relations.get((source_label, target_label), "RELATED_TO")

        # Traverse to next hop
        next_records = traverse_to_related(
            record_ids=current_ids,
            source_label=source_label,
            target_label=target_label,
            relation_type=relation_type,
            db=db,
        )

        if not next_records:
            print(f"  Step {hop_idx + 1}: No connected {target_label} records found")
            return []

        # Update IDs for next iteration
        current_ids = [r.id for r in next_records]

        # Score accumulation: multiply by hop penalty (0.9 per hop)
        hop_penalty = 0.9 ** hop_idx
        for record in next_records:
            record._hop_score = current_scores.get(record.id, 0.5) * hop_penalty

        print(f"  Step {hop_idx + 1}: Found {len(next_records)} {target_label} records")

        # For next hop, use average score of connected records
        current_scores = {r.id: r._hop_score for r in next_records}

    # Return final results sorted by accumulated score
    return sorted(next_records, key=lambda r: r._hop_score, reverse=True)[:limit]


# ============================================================================
# STEP 5: RESULT RANKING WITH TEMPORAL PROPERTIES
# ============================================================================

def rank_by_temporal_property(results, date_field="collaboration_date",
                              semantic_weight=0.7, temporal_weight=0.3):
    """Rank results combining semantic similarity with temporal recency.

    More recent collaborations score higher within similar semantic matches.

    Args:
        results: List of records with scores
        date_field: Name of the date property to use for recency
        semantic_weight: Weight for semantic score (0.0-1.0)
        temporal_weight: Weight for recency score (0.0-1.0)

    Returns:
        Sorted list of records with combined scores
    """
    scored_results = []

    for record in results:
        # Base score from semantic/hop similarity
        base_score = getattr(record, "score", 0) or getattr(record, "_hop_score", 0) or 0.5

        # Temporal scoring
        date_value = record.get(date_field)
        if date_value:
            try:
                # Parse ISO date string
                if isinstance(date_value, str):
                    record_date = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                else:
                    record_date = date_value

                # Calculate days since record
                days_ago = (datetime.now() - record_date).days

                # Recency score: 1.0 if today, 0.0 if > 365 days
                recency_score = max(0, 1 - (days_ago / 365))

                # Combine scores
                combined_score = (base_score * semantic_weight) + (recency_score * temporal_weight)
                record._combined_score = combined_score
                record._recency_score = recency_score
            except (ValueError, TypeError):
                # If date parsing fails, use base score only
                record._combined_score = base_score
                record._recency_score = 0.5
        else:
            record._combined_score = base_score
            record._recency_score = None

        scored_results.append(record)

    # Sort by combined score
    scored_results.sort(key=lambda r: r._combined_score, reverse=True)

    return scored_results


def multi_hop_search_with_ranking(db, query_text, num_hops=2,
                                  temporal_field="collaboration_date",
                                  semantic_weight=0.7,
                                  temporal_weight=0.3,
                                  limit=5):
    """Multi-hop search with temporal ranking.

    Combines semantic similarity, hop distance, and temporal recency into
    a single ranking score.

    Args:
        db: RushDB instance
        query_text: Natural language query
        num_hops: Number of relationship traversals
        temporal_field: Property name for date-based ranking
        semantic_weight: Weight for semantic/hop score (default 0.7)
        temporal_weight: Weight for recency score (default 0.3)
        limit: Maximum results

    Returns:
        Sorted list of records with combined scores
    """
    # Run multi-hop search
    results = multi_hop_search(
        db=db,
        query_text=query_text,
        num_hops=num_hops,
        limit=limit * 2,  # Get more results before ranking
    )

    if not results:
        return []

    # Apply temporal ranking
    ranked_results = rank_by_temporal_property(
        results,
        date_field=temporal_field,
        semantic_weight=semantic_weight,
        temporal_weight=temporal_weight,
    )

    return ranked_results[:limit]


# ============================================================================
# DEMONSTRATION: RUN ALL STEPS
# ============================================================================

def print_results(results, label, show_temporal=False):
    """Pretty print query results."""
    if not results:
        print(f"  No {label} results found.")
        return

    for i, result in enumerate(results, 1):
        name = result.get("name") or result.get("city") or result.get("title", "Unknown")
        score = getattr(result, "_combined_score", None) or getattr(result, "_hop_score", result.score)
        print(f"  {i}. [score={score:.3f}] {label}: {name}")

        if show_temporal and hasattr(result, "_recency_score") and result._recency_score is not None:
            print(f"     Temporal score: {result._recency_score:.2f} (recency)")


def main():
    """Run the complete multi-hop Q&A demonstration."""
    # Initialize RushDB
    api_key = os.getenv("RUSHD_API_KEY")
    if not api_key:
        print("ERROR: RUSHD_API_KEY environment variable not set.")
        print("Copy .env.example to .env and add your API key.")
        return

    db = RushDB(api_key)

    print("=" * 70)
    print("MULTI-HOP QUESTION ANSWERER WITH RUSHDB TRAVERSAL API")
    print("=" * 70)

    # Step 1: Single-hop search
    print("\n" + "=" * 70)
    print("STEP 1: Single-Hop Vector Search")
    print("-" * 70)
    print("Finding records via semantic similarity (no graph traversal)")
    print("Question: 'Who are AI researchers?'")

    results = single_hop_search(db, "AI researcher", limit=3)
    print_results(results, "PERSON")

    # Step 2: Two-hop traversal
    print("\n" + "=" * 70)
    print("STEP 2: Two-Hop Traversal")
    print("-" * 70)
    print("Chaining semantic search through WORKS_AT relationship")
    print("Question: 'What organizations do AI researchers work at?'")

    results = two_hop_search(db, "AI researcher", limit=3)
    print_results(results, "ORGANIZATION")

    # Step 3: Three-hop traversal
    print("\n" + "=" * 70)
    print("STEP 3: Three-Hop Traversal")
    print("-" * 70)
    print("Extending to PERSON → ORGANIZATION → LOCATION")
    print("Question: 'What cities host organizations with AI researchers?'")

    results = three_hop_search(db, "AI researcher", limit=3)
    print_results(results, "LOCATION")

    # Step 4: Parameterized N-hop
    print("\n" + "=" * 70)
    print("STEP 4: Parameterized N-Hop Query Function")
    print("-" * 70)
    print("Same function handles 2, 3, or 4 hops by changing parameters")

    # 2-hop
    print("\n  [2-hop] Query: 'machine learning engineer'")
    results = multi_hop_search(db, "machine learning engineer", num_hops=2, limit=2)
    print_results(results, "ORGANIZATION")

    # 3-hop
    print("\n  [3-hop] Query: 'machine learning engineer'")
    results = multi_hop_search(db, "machine learning engineer", num_hops=3, limit=2)
    print_results(results, "LOCATION")

    # 4-hop (using KNOWS relationship)
    print("\n  [4-hop with KNOWS] Query: 'AI researcher'")
    results = multi_hop_search(
        db, "AI researcher",
        num_hops=3,
        labels=["PERSON", "KNOWS_PERSON", "ORGANIZATION"],
        limit=2
    )
    print_results(results, "ORGANIZATION")

    # Step 5: Temporal ranking
    print("\n" + "=" * 70)
    print("STEP 5: Temporal Ranking")
    print("-" * 70)
    print("Combining semantic similarity with collaboration recency")
    print("Question: 'Who are recent AI researchers?' (weighted by recency)")

    results = multi_hop_search_with_ranking(
        db,
        "AI researcher",
        num_hops=1,
        temporal_field="collaboration_date",
        semantic_weight=0.6,
        temporal_weight=0.4,
        limit=3,
    )
    print_results(results, "PERSON", show_temporal=True)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("-" * 70)
    print("""
This tutorial demonstrated:

1. SINGLE-HOP: Semantic search across record descriptions
   → db.ai.search() with query text

2. TWO-HOP: Chaining semantic search through graph relationships
   → db.ai.search() + db.records.find() with $relation filter

3. THREE-HOP: Extending traversal to multiple relationship types
   → Consecutive db.records.find() calls with accumulated IDs

4. PARAMETERIZED N-HOP: Reusable function for any traversal depth
   → multi_hop_search() with configurable num_hops and labels

5. TEMPORAL RANKING: Combining semantic scores with recency
   → rank_by_temporal_property() scoring function

Key RushDB Patterns:
- db.ai.search() for semantic similarity
- db.records.find() with $relation filter for traversal
- $id with $in for filtering by previous hop results
- Record._hop_score for accumulated ranking
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
