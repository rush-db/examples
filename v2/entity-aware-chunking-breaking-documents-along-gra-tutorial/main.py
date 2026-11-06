#!/usr/bin/env python3
"""
main.py — Compare retrieval quality: token-based chunks vs entity-aware chunks.

For each query:
  1. Embed the query
  2. Search the CHUNK label (token-window chunks)
  3. Search the ENTITY labels (entity nodes with summaries)
  4. Print results side-by-side with similarity scores
  5. Show graph traversal: follow HAS_ENTITY → up to source DOCUMENT
"""

import os
import time

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("RUSHDB_TOKEN", "")
URL   = os.environ.get("RUSHDB_URL")

EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
DIM      = 384

QUERIES = [
    "What happened with AI chips and performance benchmarks?",
    "Regulatory issues affecting big tech companies",
]


def print_divider(title: str, width: int = 80):
    """Pretty divider with centred title."""
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def format_record(rec, label_width: int = 16) -> str:
    """Format a single result for display."""
    score_str = f"{rec.score:.4f}" if rec.score is not None else "n/a"
    label     = (rec.label or "?").ljust(label_width)
    name      = rec.data.get("name", "") or ""
    title     = rec.data.get("title", "") or ""
    body      = rec.data.get("body", "") or rec.data.get("summary", "") or ""

    identifier = name or title
    snippet    = body[:120] + ("…" if len(body) > 120 else "")

    return (
        f"  [{score_str}] ({label})\n"
        f"       {identifier}\n"
        f"       {snippet}"
    )


def search_and_compare(db: RushDB, query: str):
    """Run one query against both chunk types and print a side-by-side report."""
    query_vec = EMBEDDER.encode(query, normalize_embeddings=True).tolist()

    print_divider(f"QUERY: {query}")

    # ── Token-based: search CHUNK label ──────────────────────────────────
    print("\n  ▼ TOKEN-BASED (CHUNK label — fixed 200-token windows)")
    token_results = db.ai.search({
        "propertyName":  "body",
        "queryVector":   query_vec,
        "labels":        ["CHUNK"],
        "limit":         4,
    }).data

    if not token_results:
        print("    (no results)")
    else:
        for rec in token_results:
            doc_id   = rec.get("document_id", "?")
            ch_idx   = rec.get("chunk_index", "?")
            score    = rec.get("__score", 0.0)
            body     = rec.get("body", "")[:140]
            print(f"  [{score:.4f}] chunk {ch_idx} from doc {doc_id}")
            print(f"           {body}…")

    # ── Entity-based: search across entity type labels ──────────────────
    entity_labels = ["COMPANY", "PRODUCT", "PERSON", "ORGANIZATION", "REGULATION"]

    print("\n  ▼ ENTITY-AWARE (typed entity nodes + document context)")
    all_entity_results = []

    for elabel in entity_labels:
        results = db.ai.search({
            "propertyName": "summary",
            "queryVector":  query_vec,
            "labels":       [elabel],
            "limit":        4,
        }).data
        all_entity_results.extend(results)

    # Deduplicate by ID, re-sort by score
    seen_ids  = set()
    deduped   = []
    for rec in all_entity_results:
        rid = rec.get("__id") or rec.get("id")
        if rid and rid not in seen_ids:
            seen_ids.add(rid)
            deduped.append(rec)

    deduped.sort(key=lambda r: r.get("__score", 0), reverse=True)
    top_entities = deduped[:4]

    if not top_entities:
        print("    (no results)")
    else:
        for rec in top_entities:
            score  = rec.get("__score", 0.0)
            etype  = rec.get("__label", "ENTITY")
            ename  = rec.get("name", "?")
            summ   = rec.get("summary", "")[:140]
            src_id = rec.get("source_document_id", "")
            print(f"  [{score:.4f}] {etype}: {ename}")
            print(f"           {summ}…")
            if src_id:
                # Fetch the source document title for context
                doc_matches = db.records.find({
                    "labels": ["DOCUMENT"],
                    "where":  {"source_id": src_id},
                    "limit":  1,
                }).data
                if doc_matches:
                    doc_title = doc_matches[0].get("title", "")
                    print(f"           ← from: {doc_title}")

    # ── Verdict ──────────────────────────────────────────────────────────
    print("\n  ★ QUALITY VERDICT")
    if not top_entities:
        print("    No entity results to compare.")
    elif not token_results:
        print("    No token-chunk results to compare.")
    else:
        entity_top_score = max(r.get("__score", 0) for r in top_entities)
        token_top_score  = max(r.get("__score", 0) for r in token_results)

        if entity_top_score > token_top_score:
            winner = "ENTITY-AWARE"
            diff   = entity_top_score - token_top_score
        else:
            winner = "TOKEN-BASED"
            diff   = token_top_score - entity_top_score

        print(f"    Entity chunks score: {entity_top_score:.4f}")
        print(f"    Token  chunks score: {token_top_score:.4f}")
        print(f"    → {winner} returned a more relevant top result (Δ = {diff:.4f})")
        print("    Note: higher score = closer cosine similarity to query embedding.")
        print("    Entity results include typed names and linked document titles,")
        print("    providing immediate context that token-chunks lack.")


def demonstrate_graph_traversal(db: RushDB):
    """
    Show RushDB graph traversal in action:
    Find a COMPANY entity, then follow HAS_ENTITY relationship to its source DOCUMENT.
    """
    print_divider("BONUS: Graph Traversal — Find Entity → Source Document")

    # Find a Company entity with a meaningful name (pick "Nvidia" if present)
    entity_search = db.ai.search({
        "propertyName": "summary",
        "query":        "Nvidia AI GPU semiconductor market",
        "labels":       ["COMPANY"],
        "limit":        1,
    }).data

    if not entity_search:
        print("  No COMPANY entity found — seed data may not be loaded.")
        return

    company = entity_search[0]
    print(f"\n  Step 1 — Found entity: {company.get('name')} (id={company.get('__id')})")

    # Follow HAS_ENTITY edges inbound to the source document
    # In RushDB's relationship model, DOCUMENT → HAS_ENTITY → ENTITY
    # So from entity's perspective, documents connect to it via HAS_ENTITY (inbound)
    doc_matches = db.records.find({
        "labels": ["DOCUMENT"],
        "where": {
            "COMPANY": {
                "$relation": {"type": "HAS_ENTITY", "direction": "out"},
                "name": company.get("name"),
            }
        },
        "limit": 2,
    }).data

    print(f"  Step 2 — Documents that have '{company.get('name')}' as an entity:")
    if not doc_matches:
        print("    (no documents found — relationship direction may be reversed; checking)")
        # Try the reverse: find records where this entity has source_document_id
        doc_matches = db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "source_id": company.get("source_document_id", "")
            },
            "limit": 2,
        }).data

    if doc_matches:
        for doc in doc_matches:
            print(f"\n    📄 Document: {doc.get('title')}")
            print(f"       Body preview: {str(doc.get('body', ''))[:200]}…")
    else:
        print("    (no linked document found)")

    print("\n  This demonstrates RushDB's graph traversal:")
    print("    Query starts at an ENTITY node → follows HAS_ENTITY → lands on DOCUMENT")
    print("    No Cypher, no JOINs — just label + relationship filtering in the where clause.")


def print_index_stats(db: RushDB):
    """Print vector index build progress."""
    print_divider("Vector Index Status")
    all_indexes = db.ai.indexes.find().data
    if not all_indexes:
        print("  No indexes found — run seed.py first.")
        return
    for idx in all_indexes:
        stats_resp = db.ai.indexes.stats(idx.get("__id"))
        stats      = stats_resp.data
        total      = stats.get("totalRecords", "?")
        indexed    = stats.get("indexedRecords", "?")
        status     = idx.get("status", "?")
        print(f"  {idx.get('label')}.{idx.get('propertyName')}")
        print(f"    status: {status} | indexed: {indexed} / {total} records")


def main():
    if not TOKEN:
        print("ERROR: RUSHDB_TOKEN is not set. See .env.example.")
        return

    db_kwargs = {"token": TOKEN}
    if URL:
        db_kwargs["url"] = URL
    db = RushDB(**db_kwargs)

    print_index_stats(db)

    for query in QUERIES:
        search_and_compare(db, query)

    demonstrate_graph_traversal(db)

    print_divider("Done")
    print("\n  Key takeaway: entity-aware chunking stores named concepts as first-class nodes.")
    print("  Semantic search returns a typed, named entity — not an arbitrary text window.")
    print("  RushDB's property graph makes this a zero-pipeline write pattern.")
    print()


if __name__ == "__main__":
    main()
