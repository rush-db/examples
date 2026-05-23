#!/usr/bin/env python3
"""
seed.py — Ingest mock tech-news articles into RushDB.

This script:
  1. Creates a DOCUMENT record per article (raw body + title)
  2. Extracts inline entities from each article's `entities` list
  3. Writes each entity as a typed node (COMPANY / PRODUCT / PERSON / etc.)
  4. Links entities to their source document via HAS_ENTITY relationship
  5. Creates artificial token-based CHUNK records for side-by-side comparison

Pass --reset to wipe existing DOCUMENT, ENTITY, CHUNK, COMPANY, PRODUCT,
PERSON, ORGANIZATION, REGULATION records before seeding.

No external NLP needed — entity data is already embedded in data/articles.json.
"""

import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("RUSHDB_TOKEN", "")
URL   = os.environ.get("RUSHDB_URL")

SEED_FILE = os.path.join(os.path.dirname(__file__), "data", "articles.json")

# Embedding model — all-MiniLM-L6-v2 is fast and produces 384-dim vectors.
EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
DIM      = 384

# Token-chunk settings (arbitrary 200-token windows for comparison)
TOKEN_CHUNK_SIZE   = 200
TOKEN_CHUNK_OVERLAP = 40


def _tokenize(text: str) -> list[str]:
    """Simple whitespace tokenizer for rough chunk sizing."""
    return text.split()


def _split_by_tokens(text: str, chunk_size: int = TOKEN_CHUNK_SIZE,
                     overlap: int = TOKEN_CHUNK_OVERLAP) -> list[str]:
    """Yield overlapping text chunks of approximately `chunk_size` tokens."""
    tokens = _tokenize(text)
    start  = 0
    while start < len(tokens):
        end  = start + chunk_size
        chunk_text = " ".join(tokens[start:end])
        yield chunk_text
        start = end - overlap


def _embed(texts: list[str]) -> list[list[float]]:
    """Return a list of embedding vectors (list of floats)."""
    return EMBEDDER.encode(texts, normalize_embeddings=True).tolist()


def _log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def reset(db: RushDB):
    """Delete all records seeded by this script."""
    labels = ["DOCUMENT", "ENTITY", "CHUNK", "COMPANY",
              "PRODUCT",  "PERSON",  "ORGANIZATION", "REGULATION"]
    for lbl in labels:
        deleted = db.records.delete({"labels": [lbl], "where": {}})
        print(f"  Cleared {deleted.data.get('deleted', 0)} {lbl} records")


def ensure_indexes(db: RushDB):
    """Create vector indexes for searchable properties."""
    index_specs = [
        {"label": "DOCUMENT", "propertyName": "body"},
        {"label": "ENTITY",   "propertyName": "summary"},
        {"label": "CHUNK",    "propertyName": "body"},
    ]
    existing = {idx["label"] + "." + idx["propertyName"]
                for idx in db.ai.indexes.find().data}

    for spec in index_specs:
        key = spec["label"] + "." + spec["propertyName"]
        if key in existing:
            print(f"  Index {key} already exists — skipping creation")
            continue
        db.ai.indexes.create({
            "label":           spec["label"],
            "propertyName":    spec["propertyName"],
            "sourceType":      "external",
            "dimensions":      DIM,
            "similarityFunction": "cosine",
        })
        print(f"  Created index on {key}")


def seed(db: RushDB, data: list[dict]):
    """
    Ingest all articles with dual storage strategy:
      - Token chunks  → CHUNK records (fixed-size windows)
      - Entity chunks → ENTITY records (semantic boundaries)
    """
    total_entities = 0
    total_chunks   = 0

    for art_idx, article in enumerate(data, 1):
        art_id   = article["id"]
        title    = article["title"]
        body     = article["body"]
        entities = article.get("entities", [])

        # ── 1. Write the DOCUMENT record ───────────────────────────────────
        doc_record = db.records.upsert(
            label="DOCUMENT",
            data={"title": title, "body": body, "source_id": art_id},
            options={"mergeBy": ["source_id"]},
        )

        # ── 2. Token-based chunks ─────────────────────────────────────────
        chunk_texts = list(_split_by_tokens(body))
        chunk_bodies_for_embed = []
        chunk_meta = []

        for ch_idx, chunk_text in enumerate(chunk_texts):
            chunk_meta.append({
                "document_id":  art_id,
                "document_title": title,
                "chunk_index":  ch_idx,
                "body":          chunk_text,
            })
            chunk_bodies_for_embed.append(chunk_text)

        # Batch-embed all chunks
        chunk_vecs = _embed(chunk_bodies_for_embed)

        with db.transactions.begin() as tx:
            for meta, vec in zip(chunk_meta, chunk_vecs):
                chunk_record = db.records.create(
                    label="CHUNK",
                    data={
                        "document_id":   meta["document_id"],
                        "document_title": meta["document_title"],
                        "chunk_index":   meta["chunk_index"],
                        "body":          meta["body"],
                    },
                    vectors=[{"propertyName": "body", "vector": vec}],
                    transaction=tx,
                )
                # Link chunk -> document
                db.records.attach(
                    source=chunk_record,
                    target=doc_record,
                    options={"type": "PART_OF", "direction": "out"},
                    transaction=tx,
                )
            # No tx.commit() — context manager auto-commits

        total_chunks += len(chunk_texts)

        # ── 3. Entity-based nodes ─────────────────────────────────────────
        entity_bodies_for_embed = []

        for entity in entities:
            etype   = entity["type"]      # COMPANY, PRODUCT, PERSON …
            ename   = entity["name"]
            esum    = entity["summary"]
            label   = etype.upper()        # RushDB label convention

            entity_record = db.records.create(
                label=label,
                data={
                    "name":    ename,
                    "summary": esum,
                    "source_document_id": art_id,
                },
            )
            entity_bodies_for_embed.append(esum)

            # Link entity -> document
            db.records.attach(
                source=doc_record,
                target=entity_record,
                options={"type": "HAS_ENTITY", "direction": "out"},
            )
            total_entities += 1

            if total_entities % 100 == 0:
                _log(f"  ... {total_entities} entities written")

        # Upsert entity summaries with computed vectors
        # Re-fetch all entity records for this article
        entity_records = db.records.find({
            "labels": [label for label in
                       {e["type"].upper() for e in entities}],
            "where": {"source_document_id": art_id},
        }).data

        # Build a map name -> record for vector upsert
        name_to_record = {rec["name"]: rec for rec in entity_records}

        entity_vecs = _embed(entity_bodies_for_embed)
        for entity, vec in zip(entities, entity_vecs):
            rec = name_to_record.get(entity["name"])
            if rec:
                db.records.set(
                    target=rec,
                    label=entity["type"].upper(),
                    data={"name": rec["name"], "summary": rec["summary"]},
                    vectors=[{"propertyName": "summary", "vector": vec}],
                )

        _log(f"Article {art_idx}/{len(data)}: '{title[:55]}...'")
        _log(f"  → {len(chunk_texts)} token-chunks, {len(entities)} entities")

    return total_entities, total_chunks


def main():
    parser = argparse.ArgumentParser(description="Seed RushDB with tech-news articles")
    parser.add_argument("--reset", action="store_true",
                        help="Delete existing seeded records before re-seeding")
    args = parser.parse_args()

    if not TOKEN:
        print("ERROR: RUSHDB_TOKEN is not set. See .env.example.")
        sys.exit(1)

    # Initialise RushDB client
    db_kwargs = {"token": TOKEN}
    if URL:
        db_kwargs["url"] = URL
    db = RushDB(**db_kwargs)

    if args.reset:
        print("\n=== Resetting existing records ===")
        reset(db)
        print()

    # Ensure vector indexes exist
    print("\n=== Ensuring vector indexes ===")
    ensure_indexes(db)

    # Load seed data
    print("\n=== Loading articles from data/articles.json ===")
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)
    print(f"  Loaded {len(articles)} articles\n")

    # Seed
    print("=== Seeding records ===")
    total_entities, total_chunks = seed(db, articles)

    print(f"\n✅ Done — seeded {total_entities} entity nodes and "
          f"{total_chunks} token-chunks across {len(articles)} articles.")
    print("   Run `python main.py` to compare retrieval quality.")


if __name__ == "__main__":
    main()
