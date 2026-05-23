"""
main.py — Entity-aware chunking: Graph traversal vs. Vector search.

Demonstrates the core thesis: entity-aware chunking (graph + typed entities) preserves
cross-document connections that token chunking (pure vector) severs.

Three queries tested:
  1. "authentication flow from login to database"
  2. "how does JWT get validated end-to-end"
  3. "environment variables used in user settings"

For each query:
  - Run vector-only search (naive chunking analog)
  - Run graph traversal (entity-aware analog)
  - Show why graph succeeds where vector fails
"""

import os
import time
from collections import deque

import numpy as np
from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
RUSHDB_URL = os.getenv("RUSHDB_URL") or None

if not API_KEY:
    raise RuntimeError(
        "RUSHDB_API_KEY not set. Copy .env.example to .env and fill in your key."
    )

db = RushDB(API_KEY, url=RUSHDB_URL) if RUSHDB_URL else RushDB(API_KEY)

# --------------------------------------------------------------------------- #
# Embedding model — all-MiniLM-L6-v2 (384-dim, fast, public)
# --------------------------------------------------------------------------- #

print("\n  Loading embedding model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")
EMBED_DIM = 384


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return normalized embedding vectors for a list of text strings."""
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def upsert_function_vectors():
    """
    Pre-compute embeddings for all FUNCTION descriptions and upsert into RushDB.
    This simulates what would happen with a real document chunking pipeline.
    """
    # Find existing vector index for FUNCTION.description
    indexes = db.ai.indexes.find().data
    idx = None
    for candidate in indexes:
        if candidate["label"] == "FUNCTION" and candidate["propertyName"] == "description":
            idx = candidate
            break

    if not idx:
        print("  [WARN] No vector index found. Run `python seed.py` first.")
        return

    index_id = idx.get("__id") or idx.get("id")
    
    # Fetch all functions
    functions = db.records.find({"labels": ["FUNCTION"]}).data
    if not functions:
        print("  [WARN] No FUNCTION records found. Run `python seed.py` first.")
        return

    print(f"  Computing embeddings for {len(functions)} functions...")
    texts = [f.get("description", "") for f in functions]
    vectors = embed_texts(texts)

    items = [
        {"recordId": f.id, "vector": vec}
        for f, vec in zip(functions, vectors)
    ]

    db.ai.indexes.upsert_vectors(index_id, {"items": items})
    print(f"  Upserted {len(items)} vectors into index.")


def query_vector_search(query: str, top_k: int = 5) -> list:
    """
    Naive retrieval: vector similarity search across function descriptions.
    This is what naive token chunking produces — disconnected paragraphs
    with no relationship context.
    """
    query_vec = embed_texts([query])[0]
    results = db.ai.search({
        "propertyName": "description",
        "queryVector": query_vec,
        "labels": ["FUNCTION"],
        "limit": top_k,
    })
    return results.data


def graph_traverse(start_label: str, start_name: str, depth: int = 3) -> list[dict]:
    """
    Entity-aware traversal: follow typed relationships from a known entity.
    
    This mimics what an entity-aware chunking system can do: given a starting
    entity (e.g. "login_user"), traverse its CALLS edges to find dependents,
    then RETURNS edges, then CONFIG edges — preserving the full path.

    We implement BFS traversal using the `where` filter's relationship syntax.
    """
    visited = set()
    queue = deque()
    path_records = []

    # Initialise with the start entity
    start_entities = db.records.find({
        "labels": [start_label],
        "where": {"name": start_name}
    }).data

    if not start_entities:
        return []

    for entity in start_entities:
        queue.append((entity, 0))  # (record, depth)

    REL_TYPES = ["CALLS", "CONTAINS", "DEPENDS_ON", "READS_ENV", "CONFIGS", "RETURNS"]

    while queue:
        current, depth_level = queue.popleft()
        if depth_level > depth:
            continue

        cid = current.id
        if cid in visited:
            continue
        visited.add(cid)

        path_records.append({
            "entity": current.get("name") or current.get("method", "?"),
            "label": current.label,
            "depth": depth_level,
            "id": cid,
            "description": current.get("description", "")[:120],
        })

        # Traverse outgoing relationships of each valid type
        for rel_type in REL_TYPES:
            neighbors = db.records.find({
                "labels": ["FUNCTION", "CLASS", "ENV_VAR", "CONFIG_KEY", "API_ENDPOINT"],
                "where": {
                    start_label: {
                        "$relation": {"type": rel_type, "direction": "out"},
                        "$id": {"$in": [cid]}
                    }
                }
            }).data

            for neighbor in neighbors:
                if neighbor.id not in visited:
                    queue.append((neighbor, depth_level + 1))

    return path_records


def multi_hop_traverse(query_keywords: list[str], max_depth: int = 4) -> list[dict]:
    """
    Multi-hop graph traversal given query keywords.
    
    Strategy: start from the function that best matches the first keyword,
    then follow relationships to build a path that covers all keywords.
    """
    # Find the best starting point using semantic search
    start_results = db.ai.search({
        "propertyName": "description",
        "query": " ".join(query_keywords[:2]),
        "labels": ["FUNCTION", "API_ENDPOINT"],
        "limit": 1,
    }).data

    if not start_results:
        return []

    start_record = start_results[0]
    start_label = start_record.label
    start_name = start_record.get("name") or f"{start_record.get('method', '')} {start_record.get('path', '')}".strip()

    return graph_traverse(start_label, start_name, depth=max_depth)


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #

QUERIES = [
    {
        "question": "authentication flow from login to database",
        "keywords": ["login", "database", "auth"],
        "expected_entities": ["login_user", "DatabaseConnection", "execute_query", "get_user_settings"],
        "vector_query": "user authentication login database connection",
    },
    {
        "question": "how does JWT get validated end-to-end",
        "keywords": ["JWT", "validate", "token"],
        "expected_entities": ["TokenValidator", "JWTAuthenticator", "JWT_SECRET", "validate_token", "check_auth_middleware"],
        "vector_query": "JWT token validation authentication middleware",
    },
    {
        "question": "environment variables used in user settings",
        "keywords": ["user", "settings", "environment"],
        "expected_entities": ["get_user_settings", "DATABASE_URL", "UserService", "DBQuery"],
        "vector_query": "user settings environment variable configuration",
    },
]


def run_demo():
    print("\n" + "=" * 62)
    print("  Entity-Aware Chunking — Comparison Demo")
    print("=" * 62)

    # Check data exists
    count = db.records.find({"labels": ["FUNCTION"], "limit": 1})
    if not count.data:
        print("\n  [ERROR] No data found. Run `python seed.py` first.\n")
        return

    # Upsert vectors (idempotent — safe to run twice)
    print("\n  [Setup] Computing and upserting function embeddings...")
    upsert_function_vectors()
    print()

    total_graph_hits = 0
    total_vector_hits = 0

    for i, q in enumerate(QUERIES, 1):
        print(f"{'─' * 62}")
        print(f"  Query {i}: \"{q['question']}\"")
        print(f"{'─' * 62}")

        # --- Vector search (naive chunking analog) ---
        print("\n  [Vector Search] Naive retrieval — top 5 by cosine similarity:")
        print("  (Simulates fixed-token chunking: returns paragraphs, no relationships)\n")

        start = time.time()
        vector_results = query_vector_search(q["vector_query"])
        vector_elapsed = time.time() - start

        if not vector_results:
            print("  No results found.\n")
        else:
            for rank, rec in enumerate(vector_results, 1):
                name = rec.get("name", rec.id[:12])
                desc = rec.get("description", "")[:90]
                score = rec.score if hasattr(rec, "score") else rec.data.get("__score", 0.0)
                print(f"  [{rank}] {name}")
                print(f"      {desc}")
                print(f"      similarity={score:.3f}  label={rec.label}")
                print()

        # Check how many expected entities appear in top results
        vector_hit_names = {rec.get("name", "") for rec in vector_results}
        vector_hits = sum(1 for e in q["expected_entities"] if any(e.lower() in n.lower() for n in vector_hit_names))
        total_vector_hits += vector_hits

        print(f"  Vector hits on expected entities: {vector_hits}/{len(q['expected_entities'])}")
        print(f"  Time: {vector_elapsed * 1000:.1f}ms\n")

        # --- Graph traversal (entity-aware chunking analog) ---
        print("  [Graph Traversal] Entity-aware retrieval — multi-hop traversal:")
        print("  (Follows CALLS, DEPENDS_ON, READS_ENV, CONFIGS edges from start entity)\n")

        start = time.time()
        graph_results = multi_hop_traverse(q["keywords"])
        graph_elapsed = time.time() - start

        if not graph_results:
            print("  No graph path found.\n")
        else:
            # Show as a path tree
            for entry in graph_results:
                indent = "  " + "    " * entry["depth"] + ("└── " if entry["depth"] > 0 else "")
                print(f"  {indent}[{entry['label']}] {entry['entity']}")
                if entry["description"]:
                    print(f"  {indent}    {entry['description']}")

        graph_hit_names = {e["entity"] for e in graph_results}
        graph_hits = sum(1 for e in q["expected_entities"] if any(e.lower() in n.lower() for n in graph_hit_names))
        total_graph_hits += graph_hits

        print(f"\n  Graph hits on expected entities: {graph_hits}/{len(q['expected_entities'])}")
        print(f"  Entities found: {sorted(graph_hit_names)}")
        print(f"  Time: {graph_elapsed * 1000:.1f}ms\n")

        # --- Analysis ---
        print("  ┌─────────────────────────────────────────────────────────────┐")
        if graph_hits > vector_hits:
            print(f"  │  Graph wins: found {graph_hits} expected entities vs "
                          f"vector's {vector_hits}          │")
        elif graph_hits == vector_hits:
            print(f"  │  Tie: both found {graph_hits} expected entities               │")
        else:
            print(f"  │  Vector won this round ({vector_hits} vs {graph_hits}) — "
                          f"rare but possible with generic query        │")

        # Explain why
        missed = [e for e in q["expected_entities"]
                  if not any(e.lower() in n.lower() for n in graph_hit_names)]
        if missed:
            print(f"  │  Graph missed: {', '.join(missed)}         │")

        vector_missed = [e for e in q["expected_entities"]
                         if not any(e.lower() in n.lower() for n in vector_hit_names)]
        if vector_missed:
            print(f"  │  Vector missed: {', '.join(vector_missed)}        │")

        print("  └─────────────────────────────────────────────────────────────┘\n")

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------

    print("\n" + "=" * 62)
    print("  Summary: Why Entity-Aware Chunking Wins")
    print("=" * 62)

    summary = """
  Approach           Entities Found    How It Works
  ─────────────────────────────────────────────────────────────────
  Naive (Vector)     {vector:3d} / {total:3d}         Cosine similarity on description
                                       chunks — no relationship context

  Entity-Aware       {graph:3d} / {total:3d}         Graph traversal from keyword-matched
  (Graph)                               start entity, following typed edges

  ─────────────────────────────────────────────────────────────────
  The key insight: when a query asks about a PATH or FLOW
  (auth → token → DB), vector similarity finds PARAGRAPHS
  but cannot connect them. Graph traversal preserves the
  traversal path that token chunking severs.

  Entity-aware chunking models documents as:
    nodes = {classes, functions, endpoints, env vars, config keys}
    edges = {calls, imports, configures, reads_env}

  Vector search models documents as:
    flat chunks = {512-char paragraphs with no edges}

  Multi-hop questions like "trace the authentication flow from
  login to DB" require edge traversal that vectors cannot do.
  """.format(
        vector=total_vector_hits,
        graph=total_graph_hits,
        total=sum(len(q["expected_entities"]) for q in QUERIES),
    )
    print(summary)

    print("\n  To extend this demo:")
    print("  - Add CHUNK records that wrap each entity with its full source code")
    print("  - Connect CHUNKs via DEPENDS_ON edges for richer traversal")
    print("  - Use a hybrid: vector search for ranking + graph for path resolution")
    print("  - See https://docs.rushdb.com for RushDB graph query reference\n")


if __name__ == "__main__":
    run_demo()
