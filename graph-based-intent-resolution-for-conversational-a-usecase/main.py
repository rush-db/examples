"""
main.py — Graph + Vector Intent Resolution Pipeline

Demonstrates:
  1. Graph-based intent resolution (respects CAN_TRANSITION_TO edges)
  2. Semantic fallback via vector similarity on UTTERANCE nodes
  3. Contextual disambiguation: the same phrase means different things
     depending on which node the user entered from
  4. Benchmark: pure vector retrieval vs. graph+vector hybrid

Run:  python main.py
"""

from __future__ import annotations


import os
import time
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

from rushdb import RushDB

# --------------------------------------------------------------------------- #
# Embedding utilities
# --------------------------------------------------------------------------- #
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def _embedder() -> SentenceTransformer:
    if not hasattr(_embedder, "_model"):
        print("[main] Loading embedding model...")
        _embedder._model = SentenceTransformer(MODEL_NAME)
    return _embedder._model


def embed(query: str) -> list[float]:
    """Return a normalized embedding vector for the given text."""
    model = _embedder()
    vec = model.encode(query, normalize_embeddings=True)
    return vec.tolist()


# --------------------------------------------------------------------------- #
# RushDB client
# --------------------------------------------------------------------------- #
def get_db() -> RushDB:
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        raise RuntimeError("RUSHDB_API_KEY not set — copy .env.example to .env")
    url = os.environ.get("RUSHDB_URL")
    return RushDB(api_key, url=url) if url else RushDB(api_key)


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #
@dataclass
class ResolutionResult:
    intent_name: str
    intent_description: str
    score: float
    method: str  # "graph_vector" | "pure_vector" | "direct_match"
    candidates_considered: int
    transition_path: list[str] = field(default_factory=list)


@dataclass
class BenchmarkCase:
    query: str
    context_intent: Optional[str]  # None = no context / cold start
    correct_intent: str
    note: str = ""


# --------------------------------------------------------------------------- #
# IntentGraph — wraps RushDB graph traversal + vector search
# --------------------------------------------------------------------------- #
class IntentGraph:
    """
    Manages intent resolution against the RushDB-backed conversation graph.


    Resolution strategy (in order):
      1. Direct exact match on INTENT.name for cold-start first-turn queries
      2. Graph + vector: if a context_intent is provided, find reachable intents
         via CAN_TRANSITION_TO edges, then rank by vector similarity
      3. Pure vector: global vector search across all UTTERANCE nodes
    """

    def __init__(self, db: RushDB):
        self.db = db
        self._index_id: Optional[str] = None
        self._resolve_index_id()

    def _resolve_index_id(self) -> None:
        """Find (or cache) the vector index ID for UTTERANCE.description."""
        try:
            indexes = self.db.ai.indexes.find()
            for idx in indexes:
                if idx.get("label") == "UTTERANCE" and idx.get("propertyName") == "description":
                    self._index_id = idx.get("__id") or idx.get("id")
                    return
        except Exception:
            pass
        self._index_id = None

    # ------------------------------------------------------------------ #
    # Pure vector retrieval — global similarity, no graph context
    # ------------------------------------------------------------------ #
    def resolve_pure_vector(self, query: str) -> ResolutionResult:
        """
        Rank all UTTERANCE nodes by cosine similarity to query.
        Return the intent of the top-scoring UTTERANCE.


        This is the "fragile classifier" baseline: picks the globally
        most-similar intent without any conversation-state awareness.
        """
        query_vec = embed(query)

        results = self.db.ai.search(
            {
                "propertyName": "description",
                "queryVector": query_vec,
                "labels": ["UTTERANCE"],
                "limit": 5,
            }
        ).data

        if not results:
            return ResolutionResult(
                intent_name="UNKNOWN",
                intent_description="",
                score=0.0,
                method="pure_vector",
                candidates_considered=0,
            )

        top = results[0]
        intent_name = top.get("intentName", "UNKNOWN")

        # Fetch the intent record for its description
        intent_rec = self._get_intent_by_name(intent_name)
        return ResolutionResult(
            intent_name=intent_name,
            intent_description=intent_rec.get("description", "") if intent_rec else "",
            score=top.score if hasattr(top, "score") else top.get("__score", 0.0),
            method="pure_vector",
            candidates_considered=len(results),
        )

    # ------------------------------------------------------------------ #
    # Graph + vector hybrid resolution
    # ------------------------------------------------------------------ #
    def resolve_hybrid(
        self, query: str, context_intent: Optional[str] = None
    ) -> ResolutionResult:
        """
        Resolve user query using the graph + vector hybrid strategy.


        Steps:
          1. If context_intent is provided, find all CAN_TRANSITION_TO neighbours
             to get the candidate set (conversationally valid next intents).
          2. If no context (cold start), use direct name matching as step 1.
          3. Perform vector search over UTTERANCE nodes.
          4. Filter results to intents in the candidate set.
          5. Return the highest-scoring filtered result.

        This is the approach that correctly disambiguates "book a flight"
        depending on whether the user entered from CANCEL_TRIP or GREETING.
        """
        candidates: list[str] = []
        transition_path: list[str] = []


        if context_intent:
            # Step 1: graph traversal — find reachable intents
            reachable = self._get_reachable_intents(context_intent)
            candidates = [ctx["name"] for ctx in reachable]
            transition_path = [context_intent] + candidates

        if not candidates:
            # Cold start: fall back to direct matching against all intents
            all_intents = self.db.records.find({"labels": ["INTENT"]}).data
            candidates = [r.get("name") for r in all_intents if r.get("name")]
            transition_path = ["<cold_start>"] + candidates

        # Step 2: vector search across all UTTERANCE nodes
        query_vec = embed(query)
        vector_results = self.db.ai.search(
            {
                "propertyName": "description",
                "queryVector": query_vec,
                "labels": ["UTTERANCE"],
                "limit": 20,
            }
        ).data

        if not vector_results:
            return ResolutionResult(
                intent_name="UNKNOWN",
                intent_description="",
                score=0.0,
                method="graph_vector",
                candidates_considered=len(candidates),
                transition_path=transition_path,
            )

        # Step 3: filter to candidates and pick the best
        best_intent: Optional[str] = None
        best_score = -1.0

        for rec in vector_results:
            rec_intent = rec.get("intentName")
            if rec_intent in candidates:
                s = rec.score if hasattr(rec, "score") else rec.get("__score", 0.0)
                if s > best_score:
                    best_score = s
                    best_intent = rec_intent

        if best_intent is None:
            # Fallback: pick the top global result if no candidate matched
            fallback = vector_results[0]
            best_intent = fallback.get("intentName", "UNKNOWN")
            best_score = fallback.score if hasattr(fallback, "score") else fallback.get("__score", 0.0)

        intent_rec = self._get_intent_by_name(best_intent)
        return ResolutionResult(
            intent_name=best_intent,
            intent_description=intent_rec.get("description", "") if intent_rec else "",
            score=best_score,
            method="graph_vector",
            candidates_considered=len(candidates),
            transition_path=transition_path,
        )


    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _get_reachable_intents(self, current_intent: str) -> list[dict]:
        """
        Traverse CAN_TRANSITION_TO edges from current_intent.
        Returns a list of target INTENT record dicts.
        """
        # Find the source INTENT record
        src_results = self.db.records.find({
            "labels": ["INTENT"],
            "where": {"name": current_intent},
        }).data

        if not src_results:
            return []

        src_rec = src_results[0]
        if not src_rec.exists:
            return []


        # Follow CAN_TRANSITION_TO edges via the graph relationship filter
        reachable = self.db.records.find({
            "labels": ["INTENT"],
            "where": {
                "INTENT": {
                    "$relation": {"type": "CAN_TRANSITION_TO", "direction": "in"},
                    "$id": {"$in": [src_rec.id]},
                }
            },
        }).data

        return reachable

    def _get_intent_by_name(self, name: str) -> Optional[Any]:
        """Fetch an INTENT record by name."""
        results = self.db.records.find({
            "labels": ["INTENT"],
            "where": {"name": name},
        }).data
        return results[0] if results else None


# --------------------------------------------------------------------------- #
# Benchmark runner
# --------------------------------------------------------------------------- #

# Cases designed to show where graph+vector beats pure retrieval.
# correct_intent is the intent a human operator would choose given the context.
BENCHMARK_CASES: list[BenchmarkCase] = [
    # --- Context-dependent cases (where graph+vector shines) ---
    BenchmarkCase(
        query="book a flight",
        context_intent="CANCEL_TRIP",
        correct_intent="RESUME_BOOKING",
        note="'book a flight' after cancellation = rebook, not start fresh",
    ),
    BenchmarkCase(
        query="book a flight",
        context_intent="GREETING",
        correct_intent="BOOK_FLIGHT",
        note="'book a flight' from a fresh start = new booking",
    ),
    BenchmarkCase(
        query="book a flight",
        context_intent="FARE_INQUIRY",
        correct_intent="BOOK_FLIGHT",
        note="Asked about fares, then said 'book a flight' = proceed to book",
    ),
    BenchmarkCase(
        query="change my flight",
        context_intent="CHECK_FLIGHT_STATUS",
        correct_intent="MODIFY_BOOKING",
        note="After checking status, 'change my flight' = modify",
    ),
    BenchmarkCase(
        query="check my flight status",
        context_intent="BOOK_FLIGHT",
        correct_intent="CHECK_FLIGHT_STATUS",
        note="After booking, checking status is the natural next step",
    ),
    BenchmarkCase(
        query="i need to cancel",
        context_intent="RESUME_BOOKING",
        correct_intent="CANCEL_TRIP",
        note="Second cancellation attempt while resuming = cancel again",
    ),
    BenchmarkCase(
        query="modify my booking",
        context_intent="CANCEL_TRIP",
        correct_intent="RESUME_BOOKING",
        note="After cancellation, 'modify' implies resuming — not modifying cancelled",
    ),
    BenchmarkCase(
        query="is my flight on time",
        context_intent="BOOK_FLIGHT",
        correct_intent="CHECK_FLIGHT_STATUS",
        note="After booking, asking about timing = status check",
    ),
    BenchmarkCase(
        query="how much is a ticket",
        context_intent="GREETING",
        correct_intent="FARE_INQUIRY",
        note="Cold-start fare inquiry",
    ),
    BenchmarkCase(
        query="flight prices",
        context_intent="BAGGAGE_INFO",
        correct_intent="FARE_INQUIRY",
        note="Asked about baggage, now about prices = fare inquiry",
    ),
    BenchmarkCase(
        query="can i bring a bag",
        context_intent="BOOK_FLIGHT",
        correct_intent="BAGGAGE_INFO",
        note="After booking, baggage allowance question",
    ),
    BenchmarkCase(
        query="check in for my flight",
        context_intent="CHECK_FLIGHT_STATUS",
        correct_intent="CHECK_IN",
        note="After status check, natural next step is check-in",
    ),
    # --- Cold-start cases (pure vector handles these well) ---
    BenchmarkCase(
        query="cancel my trip",
        context_intent=None,
        correct_intent="CANCEL_TRIP",
        note="Cold start — cancellation is unambiguous",
    ),
    BenchmarkCase(
        query="transfer me to a human",
        context_intent=None,
        correct_intent="SUPPORT_HUMAN",
        note="Cold start — human request is unambiguous",
    ),
    BenchmarkCase(
        query="i want a refund",
        context_intent="CANCEL_TRIP",
        correct_intent="REFUND_REQUEST",
        note="After cancellation, refund request is the natural follow-up",
    ),
]


def run_benchmark(graph: IntentGraph, cases: list[BenchmarkCase]) -> None:
    """
    Run each benchmark case through both pure_vector and graph_vector.
    Report accuracy and timing.
    """
    print("\n" + "=" * 70)
    print(" BENCHMARK: Pure Vector Retrieval vs. Graph + Vector Hybrid")
    print("=" * 70)
    print()

    print(f"  {'Case':<4} {'Query':<30} {'Context':<20} {'Pure-V':<12} {'Hybrid':<12} {'Note'}")
    print(f"  {'-'*4} {'-'*30} {'-'*20} {'-'*12} {'-'*12} {'-'*30}")


    pure_correct = 0
    hybrid_correct = 0
    pure_timing: list[float] = []
    hybrid_timing: list[float] = []

    for i, case in enumerate(cases, 1):
        context_str = case.context_intent or "<cold_start>"
        query = case.query

        # --- Pure vector ---
        t0 = time.perf_counter()
        pure_result = graph.resolve_pure_vector(query)
        t_pure = time.perf_counter() - t0
        pure_timing.append(t_pure)
        pure_ok = "✓" if pure_result.intent_name == case.correct_intent else "✗"

        # --- Hybrid ---
        t0 = time.perf_counter()
        hybrid_result = graph.resolve_hybrid(query, case.context_intent)
        t_hybrid = time.perf_counter() - t0
        hybrid_timing.append(t_hybrid)
        hybrid_ok = "✓" if hybrid_result.intent_name == case.correct_intent else "✗"

        if pure_result.intent_name == case.correct_intent:
            pure_correct += 1
        if hybrid_result.intent_name == case.correct_intent:
            hybrid_correct += 1

        print(
            f"  {i:<4} {query:<30} {context_str:<20} "
            f"{pure_result.intent_name:<12} {hybrid_result.intent_name:<12} {case.note}"
        )
        print(
            f"       {pure_ok} (score={pure_result.score:.3f}, {t_pure*1000:.0f}ms)   "
            f"{hybrid_ok} (score={hybrid_result.score:.3f}, {t_hybrid*1000:.0f}ms)"
        )
        print()

    n = len(cases)
    pure_acc = pure_correct / n * 100
    hybrid_acc = hybrid_correct / n * 100

    avg_pure = sum(pure_timing) / n * 1000
    avg_hybrid = sum(hybrid_timing) / n * 1000

    print("=" * 70)
    print(" SUMMARY")
    print("=" * 70)
    print(f"  Total cases:               {n}")
    print(f"  Pure vector accuracy:       {pure_correct}/{n}  ({pure_acc:.0f}%)")
    print(f"  Graph + vector accuracy:    {hybrid_correct}/{n}  ({hybrid_acc:.0f}%)")
    print(f"  Accuracy improvement:       +{hybrid_acc - pure_acc:.0f} pp")
    print()
    print(f"  Avg latency (pure vector):  {avg_pure:.1f} ms")
    print(f"  Avg latency (hybrid):        {avg_hybrid:.1f} ms")
    print()

    if hybrid_acc > pure_acc:
        print("  → Graph + vector outperforms pure retrieval on context-dependent cases.")
        print("  → Pure vector excels on cold-start, unambiguous queries.")
        print("  → The hybrid approach combines the best of both: graph rules + vector flexibility.")
    elif hybrid_acc == pure_acc:
        print("  → Both approaches perform equally on this benchmark set.")
        print("  → Try adding more context-dependent cases to surface the graph advantage.")
    else:
        print("  → Pure vector outperformed — likely due to small graph or many cold-start cases.")

        print("  → Graph + vector gains advantage as conversation depth increases.")


# --------------------------------------------------------------------------- #
# Contextual disambiguation demo
# --------------------------------------------------------------------------- #
def demo_disambiguation(graph: IntentGraph) -> None:
    """Show that 'book a flight' means different things from different entry points."""
    print()
    print("=" * 70)
    print(" DEMO: Contextual Disambiguation — 'book a flight'")
    print("=" * 70)
    print()


    query = "book a flight"
    contexts = [("GREETING", "Fresh conversation start"),
                ("CANCEL_TRIP", "Immediately after cancellation"),
                ("FARE_INQUIRY", "After asking about prices"),
                ("BAGGAGE_INFO", "After asking about luggage"),
                (None, "No context (cold start)")]

    for ctx, note in contexts:
        ctx_label = ctx or "<cold_start>"
        result = graph.resolve_hybrid(query, ctx)

        print(f"  Context: {ctx_label:<16}  →  Intent: {result.intent_name:<20} ({note})")
        print(f"           Score: {result.score:.3f}   Candidates: {result.candidates_considered}")
        print()

    print("  Key insight: the same phrase resolves to different intents based on")
    print("  conversation history. Pure vector retrieval picks one global winner,")
    print("  ignoring context entirely.")


# --------------------------------------------------------------------------- #
# Show graph structure
# --------------------------------------------------------------------------- #
def show_graph_structure(db: RushDB) -> None:
    """Print the intent graph edges for educational purposes."""
    print()
    print("=" * 70)
    print(" INTENT GRAPH: CAN_TRANSITION_TO Edges")
    print("=" * 70)
    print()

    all_intents = db.records.find({"labels": ["INTENT"], "limit": 100}).data
    intent_map = {r.get("name"): r for r in all_intents}

    for name, rec in intent_map.items():
        neighbours = db.records.find({
            "labels": ["INTENT"],
            "where": {
                "INTENT": {
                    "$relation": {"type": "CAN_TRANSITION_TO", "direction": "in"},
                    "$id": {"$in": [rec.id]},
                }
            },
        }).data
        if neighbours:
            targets = ", ".join(r.get("name", "?") for r in neighbours)
            print(f"  {name:<22} → [{targets}]")



# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    db = get_db()
    graph = IntentGraph(db)

    print("\n[main] Intent Resolution Pipeline loaded.")
    print(f"[main] Vector index ID: {graph._index_id or 'not found (run seed.py first)'}")
    print()

    # Show the graph structure
    show_graph_structure(db)

    # Run the disambiguation demo
    demo_disambiguation(graph)

    # Run the full benchmark
    run_benchmark(graph, BENCHMARK_CASES)


if __name__ == "__main__":
    main()
