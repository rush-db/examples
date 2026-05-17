"""
seed.py — Seeds RushDB with the conversational intent graph.

Idempotent: detects existing INTENT nodes and skips creation.
Use --reset to clear and rebuild everything.

Run:  python seed.py
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load .env before importing rushdb so the API key is available
load_dotenv()

from rushdb import RushDB

# --------------------------------------------------------------------------- #
# Embedding model — all-MiniLM-L6-v2 is fast, accurate, and free (no API key)
# --------------------------------------------------------------------------- #
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # output dimension for all-MiniLM-L6-v2


def get_embedder() -> SentenceTransformer:
    """Load (and lazily cache) the sentence-transformer model."""
    if not hasattr(get_embedder, "_model"):
        print(f"[seed] Loading embedding model: {MODEL_NAME}")
        get_embedder._model = SentenceTransformer(MODEL_NAME)
        print(f"[seed] Model loaded.")
    return get_embedder._model


def embed_texts(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """Return normalized embedding vectors for a list of texts."""
    model = get_embedder()
    vectors = model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
    return vectors.tolist()


# --------------------------------------------------------------------------- #
# Intent graph definition
# --------------------------------------------------------------------------- #
INTENTS: list[dict[str, Any]] = [
    {
        "name": "GREETING",
        "description": "User says hello or initiates conversation",
        "category": "meta",
        "priority": 10,
        "utterances": [
            "hello",
            "hi there",
            "hey",
            "good morning",
            "hi",
            "good afternoon",
        ],
    },
    {
        "name": "BOOK_FLIGHT",
        "description": "User wants to search for and book a flight",
        "category": "booking",
        "priority": 8,
        "utterances": [
            "book a flight",
            "i need a flight",
            "find me a plane ticket",
            "i want to fly somewhere",
            "search for flights",
            "looking to book a plane",
        ],
    },
    {
        "name": "CANCEL_TRIP",
        "description": "User wants to cancel an existing trip or booking",
        "category": "booking",
        "priority": 9,
        "utterances": [
            "cancel my trip",
            "cancel my booking",
            "i need to cancel",
            "cancel everything",
            "abort my reservation",
        ],
    },
    {
        "name": "RESUME_BOOKING",
        "description": "User wants to continue a previously started booking after cancellation",
        "category": "booking",
        "priority": 8,
        "utterances": [
            "book a flight",
            "let me try again",
            "rebook",
            "i want to try again",
            "book again",
        ],
    },
    {
        "name": "MODIFY_BOOKING",
        "description": "User wants to change dates, destination, or passenger details",
        "category": "booking",
        "priority": 8,
        "utterances": [
            "change my flight",
            "modify my booking",
            "update my reservation",
            "i need to change dates",
            "reschedule",
        ],
    },
    {
        "name": "CHECK_FLIGHT_STATUS",
        "description": "User wants to check the status of an existing flight",
        "category": "information",
        "priority": 7,
        "utterances": [
            "is my flight on time",
            "check my flight status",
            "flight status",
            "is my booking confirmed",
            "where is my flight",
        ],
    },
    {
        "name": "REFUND_REQUEST",
        "description": "User wants a refund for a cancelled booking",
        "category": "billing",
        "priority": 9,
        "utterances": [
            "i want a refund",
            "refund my money",
            "get my money back",
            "refund please",
            "when do i get my money back",
        ],
    },
    {
        "name": "SUPPORT_HUMAN",
        "description": "User explicitly requests to speak to a human agent",
        "category": "meta",
        "priority": 10,
        "utterances": [
            "transfer me to a human",
            "let me talk to an agent",
            "speak to someone",
            "customer support",
            "real person please",
        ],
    },
    {
        "name": "FARE_INQUIRY",
        "description": "User asks about ticket prices or fare options",
        "category": "information",
        "priority": 6,
        "utterances": [
            "how much is a ticket",
            "flight prices",
            "what does it cost",
            "fare options",
            "how much to fly",
        ],
    },
    {
        "name": "BAGGAGE_INFO",
        "description": "User asks about baggage allowances or luggage policies",
        "category": "information",
        "priority": 5,
        "utterances": [
            "baggage allowance",
            "can i bring a bag",
            "luggage policy",
            "how much luggage can i take",
            "check in bags",
        ],
    },
    {
        "name": "CHECK_IN",
        "description": "User wants to check in for a flight",
        "category": "booking",
        "priority": 7,
        "utterances": [
            "check in for my flight",
            "online check in",
            "check me in",
            "i want to check in",
        ],
    },
]

# Valid transitions as (source_intent, target_intent) tuples
TRANSITIONS: list[tuple[str, str]] = [
    # Entry point transitions
    ("GREETING", "BOOK_FLIGHT"),
    ("GREETING", "CHECK_FLIGHT_STATUS"),
    ("GREETING", "FARE_INQUIRY"),
    ("GREETING", "BAGGAGE_INFO"),
    ("GREETING", "SUPPORT_HUMAN"),
    # Standard booking flow
    ("BOOK_FLIGHT", "MODIFY_BOOKING"),
    ("BOOK_FLIGHT", "CHECK_FLIGHT_STATUS"),
    ("BOOK_FLIGHT", "CANCEL_TRIP"),
    # After cancellation
    ("CANCEL_TRIP", "RESUME_BOOKING"),
    ("CANCEL_TRIP", "REFUND_REQUEST"),
    ("CANCEL_TRIP", "SUPPORT_HUMAN"),
    # Resuming after cancellation
    ("RESUME_BOOKING", "MODIFY_BOOKING"),
    ("RESUME_BOOKING", "CANCEL_TRIP"),
    ("RESUME_BOOKING", "CHECK_FLIGHT_STATUS"),
    # Modification flow
    ("MODIFY_BOOKING", "CHECK_FLIGHT_STATUS"),
    ("MODIFY_BOOKING", "CANCEL_TRIP"),
    # Status checks
    ("CHECK_FLIGHT_STATUS", "MODIFY_BOOKING"),
    ("CHECK_FLIGHT_STATUS", "CHECK_IN"),
    ("CHECK_FLIGHT_STATUS", "SUPPORT_HUMAN"),
    # Fare / baggage info
    ("FARE_INQUIRY", "BOOK_FLIGHT"),
    ("FARE_INQUIRY", "BAGGAGE_INFO"),
    ("BAGGAGE_INFO", "BOOK_FLIGHT"),
    ("BAGGAGE_INFO", "FARE_INQUIRY"),
    # Check-in
    ("CHECK_IN", "CHECK_FLIGHT_STATUS"),
    # Refunds
    ("REFUND_REQUEST", "SUPPORT_HUMAN"),
    ("REFUND_REQUEST", "BOOK_FLIGHT"),
]


# --------------------------------------------------------------------------- #
# Helper: reset existing data
# --------------------------------------------------------------------------- #
def reset_database(db: RushDB) -> None:
    """Delete all INTENT and UTTERANCE records to allow a clean rebuild."""
    print("[seed] Resetting database (deleting existing records)...")
    db.records.delete_many({"labels": ["UTTERANCE"]})
    db.records.delete_many({"labels": ["INTENT"]})
    print("[seed] Reset complete.")


# --------------------------------------------------------------------------- #
# Main seeding logic
# --------------------------------------------------------------------------- #
def seed(db: RushDB, *, reset: bool = False) -> dict[str, Any]:
    """
    Build the intent graph and utterance index in RushDB.

    Returns a dict with node counts for reporting.
    """
    if reset:
        reset_database(db)

    # Check whether we already have data
    existing = db.records.find({"labels": ["INTENT"]})
    already_seeded = existing.total > 0

    if already_seeded and not reset:
        print(f"[seed] Database already contains {existing.total} INTENT records. Skipping.")
        print("[seed] Run with --reset to rebuild from scratch.")
        return {"intents_created": existing.total, "utterances_created": 0}

    print(f"[seed] Seeding intent graph... (reset={reset})")
    start = time.perf_counter()

    # ---- Step 1: create vector index for UTTERANCE.description ---------------- #
    print("[seed] Creating vector index for UTTERANCE.description...")
    index_label = "UTTERANCE"
    index_prop = "description"

    # Check if index already exists
    try:
        existing_indexes = db.ai.indexes.find()
        index_id = None
        for idx in existing_indexes:
            if idx.get("label") == index_label and idx.get("propertyName") == index_prop:
                index_id = idx.get("__id") or idx.get("id")
                break

        if index_id is None:
            index_resp = db.ai.indexes.create({
                "label": index_label,
                "propertyName": index_prop,
                "sourceType": "external",
                "dimensions": EMBEDDING_DIM,
                "similarityFunction": "cosine",
            })
            index_id = index_resp.data.get("__id") or index_resp.data.get("id")
            print(f"[seed] Vector index created: {index_id}")
        else:
            print(f"[seed] Vector index already exists: {index_id}")
    except Exception as e:
        print(f"[seed] Index creation note: {e}")
        index_id = None

    # ---- Step 2: create INTENT nodes with embeddings -------------------------- #
    print(f"[seed] Creating {len(INTENTS)} INTENT nodes...")
    intent_records: dict[str, Any] = {}

    # Batch-embed all descriptions for INTENT nodes
    intent_descs = [item["description"] for item in INTENTS]
    intent_vecs = embed_texts(intent_descs)

    with db.transactions.begin() as tx:
        for i, item in enumerate(INTENTS):
            rec = db.records.create(
                label="INTENT",
                data={
                    "name": item["name"],
                    "description": item["description"],
                    "category": item["category"],
                    "priority": item["priority"],
                },
                vectors=[{"propertyName": "description", "vector": intent_vecs[i]}],
                transaction=tx,
            )
            intent_records[item["name"]] = rec

            if (i + 1) % 5 == 0:
                print(f"  [seed]   {i + 1}/{len(INTENTS)} INTENT nodes created")

        print(f"[seed]   {len(INTENTS)} INTENT nodes committed.")

    # ---- Step 3: create UTTERANCE nodes with embeddings ----------------------- #
    print("[seed] Creating UTTERANCE nodes...")

    utterances_to_index: list[dict[str, Any]] = []

    with db.transactions.begin() as tx:
        for i, item in enumerate(INTENTS):
            intent_rec = intent_records[item["name"]]
            for utt_text in item["utterances"]:
                utt_rec = db.records.create(
                    label="UTTERANCE",
                    data={
                        "text": utt_text,
                        "description": utt_text,  # used as vector search property
                        "intentName": item["name"],
                    },
                    transaction=tx,
                )
                # Link UTTERANCE back to its INTENT
                db.records.attach(
                    source=intent_rec,
                    target=utt_rec,
                    options={"type": "HAS_UTTERANCE", "direction": "out"},
                    transaction=tx,
                )
                utterances_to_index.append({
                    "record": utt_rec,
                    "text": utt_text,
                })

            if (i + 1) % 3 == 0:
                print(f"  [seed]   Processed intents through {item['name']}")


        print(f"[seed]   {len(utterances_to_index)} UTTERANCE nodes committed.")

    # ---- Step 4: create CAN_TRANSITION_TO edges -------------------------------- #
    print(f"[seed] Creating {len(TRANSITIONS)} CAN_TRANSITION_TO edges...")
    with db.transactions.begin() as tx:
        for src_name, tgt_name in TRANSITIONS:
            src_rec = intent_records[src_name]
            tgt_rec = intent_records[tgt_name]
            db.records.attach(
                source=src_rec,
                target=tgt_rec,
                options={"type": "CAN_TRANSITION_TO", "direction": "out"},
                transaction=tx,
            )
        print(f"[seed]   {len(TRANSITIONS)} edges committed.")

    # ---- Step 5: upsert vectors into the external index --------------------- #
    if index_id and utterances_to_index:
        print(f"[seed] Embedding {len(utterances_to_index)} utterances...")
        utt_vecs = embed_texts([u["text"] for u in utterances_to_index])

        items = [
            {
                "recordId": u["record"].id,
                "vector": utt_vecs[i],
            }
            for i, u in enumerate(utterances_to_index)
        ]

        db.ai.indexes.upsert_vectors(index_id, {"items": items})
        print(f"[seed] Vectors upserted into index.")

    elapsed = time.perf_counter() - start
    print(f"[seed] Done in {elapsed:.1f}s.")

    return {
        "intents_created": len(INTENTS),
        "utterances_created": len(utterances_to_index),
        "edges_created": len(TRANSITIONS),
        "index_id": index_id,
    }


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the RushDB intent graph.")
    parser.add_argument("--reset", action="store_true", help="Clear existing data and rebuild")
    args = parser.parse_args()

    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY environment variable not set.")
        print("Copy .env.example to .env and fill in your API key.")
        sys.exit(1)

    url = os.environ.get("RUSHDB_URL")
    db = RushDB(api_key, url=url) if url else RushDB(api_key)

    result = seed(db, reset=args.reset)
    print("\n[seed] Summary:")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
