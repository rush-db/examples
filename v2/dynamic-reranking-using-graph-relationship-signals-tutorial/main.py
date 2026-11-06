"""
Dynamic Reranking Using Graph Relationship Signals — Main Pipeline

This script demonstrates how RushDB's property graph model enables dynamic
reranking of semantic search results using relationship-based behavioral signals.


Pipeline:
  1. Semantic search → get candidate articles ranked by content similarity
  2. Extract relationship signals → count VIEWED/SAVED/SHARED edges per article
  3. Compute recency-weighted interaction scores
  4. Fuse semantic + signal scores → final ranked list
  5. Display before/after rankings with signal breakdown
"""

import os
import math
from datetime import datetime, timedelta
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

db = RushDB(os.environ["RUSHDB_API_KEY"])

# ─── Configuration ─────────────────────────────────────────────────────────────


SEMANTIC_QUERY         = "node.js performance"
SEARCH_LIMIT          = 8
TARGET_USER_EMAIL     = "alex@example.com"
SIGNAL_DECAY_HALF_LIFE_HOURS = 24 * 3   # 3-day half-life for recency

# Weights for score fusion
SEMANTIC_WEIGHT   = 0.7
SIGNAL_WEIGHT     = 0.3

# Interaction weights — SAVED and SHARED are stronger signals
INTERACTION_WEIGHTS = {
    "VIEWED": 1.0,
    "SAVED":  3.0,
    "SHARED": 5.0,
}

# ─── Helpers ───────────────────────────────────────────────────────────────────



def hours_since(timestamp_str: str) -> float:
    """Parse an ISO timestamp and return hours since now. Returns float."""
    try:
        # Handle both 'Z' suffix and naive ISO strings
        ts = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        # Normalize to naive UTC for arithmetic
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None) - (dt.utcoffset() or timedelta(0))
        delta = datetime.utcnow() - dt
        return max(delta.total_seconds() / 3600, 0.5)  # clamp to avoid /0
    except (ValueError, AttributeError):
        return float("inf")


def recency_score(hours_ago: float, half_life: float = SIGNAL_DECAY_HALF_LIFE_HOURS) -> float:
    """Exponential decay score: 1.0 now, 0.5 at half_life, 0.25 at 2× half_life."""
    return math.pow(0.5, hours_ago / half_life)


def interaction_signal_score(
    count: int,
    last_hours_ago: float,
    interaction_type: str,
    half_life: float = SIGNAL_DECAY_HALF_LIFE_HOURS,
) -> float:
    """
    Compute a weighted, recency-decayed signal score for a single interaction type.

    score = interaction_weight × count × recency_score
    """
    weight = INTERACTION_WEIGHTS.get(interaction_type, 1.0)
    return weight * count * recency_score(last_hours_ago, half_life)



def relative_time_str(hours: float) -> str:
    """Convert a decimal hour count to a human-readable relative string."""
    if hours == float("inf"):
        return "never"
    if hours < 1:
        return f"{int(hours * 60)}m ago"
    if hours < 24:
        return f"{int(hours)}h ago"
    days = int(hours // 24)
    if days == 1:
        return "1d ago"
    return f"{days}d ago"


# ─── Step 1: Semantic search ────────────────────────────────────────────────────


print("\n📊 Article Graph Signal Re-Ranking Demo")
print("═" * 58)
print("\n🔍 Step 1 — Semantic search for articles")

semantic_results = db.ai.search({
    "propertyName": "body",
    "query":       SEMANTIC_QUERY,
    "labels":      ["ARTICLE"],
    "limit":       SEARCH_LIMIT,
})

candidates = semantic_results.data
print(f"   Found {len(candidates)} candidate articles:\n")

for i, article in enumerate(candidates, 1):
    print(f"   {i}. [{article.score:.3f}] {article['title']}")

# ─── Step 2: Identify the target user ──────────────────────────────────────────


print("\n🔗 Step 2 — Identifying target user for signal extraction")

user_result = db.records.find({
    "labels": ["USER"],
    "where":  {"email": TARGET_USER_EMAIL},
})

if user_result.total == 0:
    raise RuntimeError(f"User {TARGET_USER_EMAIL} not found. Run seed.py first.")

target_user = user_result.data[0]
print(f"   Target user: {target_user['name']} <{target_user['email']}>")
print(f"   User ID: {target_user.id}")

# ─── Step 3: Extract relationship signals ──────────────────────────────────────


print("\n🔗 Step 3 — Extracting relationship signals per article")
print("   (Querying VIEWED / SAVED / SHARED edges from target user)\n")


article_signals: dict[str, dict] = {}

# For each candidate article, query its relationship edges from this user
for article in candidates:
    article_id  = article.id
    signals = {"VIEWED": {"count": 0, "last_hours": float("inf")},
               "SAVED":  {"count": 0, "last_hours": float("inf")},
               "SHARED": {"count": 0, "last_hours": float("inf")},
               }

    for rel_type in ["VIEWED", "SAVED", "SHARED"]:
        edges = db.relationships.find({
            "where": {
                "type":           rel_type,
                "sourceLabel":    "USER",
                "targetLabel":    "ARTICLE",
                "source__id":     target_user.id,
                "target__id":     article_id,
            },
            "limit": 50,
        })

        if edges.data:
            # Use the most recent lastInteractionAt across all edges
            last_at = max(
                e.get("properties", {}).get("lastInteractionAt", "")
                for e in edges.data
            )
            # Sum counts from edge properties
            total_count = sum(
                e.get("properties", {}).get("count", 1)
                for e in edges.data
            )
            signals[rel_type] = {
                "count":      total_count,
                "last_hours": hours_since(last_at),
            }

    article_signals[article_id] = signals

# Pretty-print extracted signals
print(f"   Extracted signals for {len(candidates)} articles:\n")
for article in candidates:
    sigs = article_signals[article.id]
    lines = [f"   {article['title']}"]
    for rel_type in ["VIEWED", "SAVED", "SHARED"]:
        s = sigs[rel_type]
        hrs = s["last_hours"]
        time_str = relative_time_str(hrs)
        score = interaction_signal_score(s["count"], hrs, rel_type)
        lines.append(
            f"     {rel_type:<7} {s['count']:>2}x  last: {time_str:<10}  "
            f"raw: {s['count'] * INTERACTION_WEIGHTS[rel_type]:.1f}  "
            f"decay: {recency_score(hrs):.3f}  score: {score:.3f}"
        )

    # Combined signal score (not capped yet — cap during fusion)
    combined = sum(
        interaction_signal_score(sigs[rt]["count"], sigs[rt]["last_hours"], rt)
        for rt in ["VIEWED", "SAVED", "SHARED"]
    )
    lines.append(f"     → combined raw signal: {combined:.3f}")
    print("\n".join(lines))

# ─── Step 4: Score fusion and reranking ───────────────────────────────────────


print("\n🏆 Step 4 — Score fusion and dynamic reranking")
print(f"   Fusion formula: ({SEMANTIC_WEIGHT:.0%} × semantic) + ({SIGNAL_WEIGHT:.0%} × signal)\n")

# Max signal to normalize
max_signal = max(
    sum(
        interaction_signal_score(
            article_signals[art.id][rt]["count"],
            article_signals[art.id][rt]["last_hours"],
            rt,
        )
        for rt in ["VIEWED", "SAVED", "SHARED"]
    )
    for art in candidates
) or 1.0

ranked = []
for article in candidates:
    sigs    = article_signals[article.id]
    sem_score   = article.score or 0.0
    signal_raw  = sum(
        interaction_signal_score(sigs[rt]["count"], sigs[rt]["last_hours"], rt)
        for rt in ["VIEWED", "SAVED", "SHARED"]
    )
    signal_norm = min(signal_raw / max_signal, 1.0)   # cap at 1.0
    final_score  = (SEMANTIC_WEIGHT * sem_score) + (SIGNAL_WEIGHT * signal_norm)

    ranked.append({
        "article":     article,
        "sem_score":   sem_score,
        "signal_raw":  signal_raw,
        "signal_norm": signal_norm,
        "final_score": final_score,
    })

# Sort by final_score descending
ranked.sort(key=lambda x: x["final_score"], reverse=True)

# Original order (from semantic) for comparison
orig_order = {art.id: i for i, art in enumerate(candidates)}


for rank, item in enumerate(ranked, 1):
    art    = item["article"]
    badge = "★" if orig_order.get(art.id, -1) != rank - 1 else " "
    sigs  = article_signals[art.id]

    print(f"   {rank}. [{badge} {item['final_score']:.3f}] {art['title']}")
    print(
        f"       ↳ semantic={item['sem_score']:.3f}  "
        f"signal={item['signal_norm']:.3f}  "
        f"(raw={item['signal_raw']:.2f})"
    )
    # Detail each interaction type contributing to the signal
    for rt in ["VIEWED", "SAVED", "SHARED"]:
        s = sigs[rt]
        if s["count"] > 0:
            iscore = interaction_signal_score(s["count"], s["last_hours"], rt) / max_signal
            print(
                f"       ↳ {rt}: {s['count']}x "
                f"({relative_time_str(s['last_hours'])}) → "
                f"{iscore:.3f} norm"
            )
    print()

# ─── Step 5: Ranking impact summary ────────────────────────────────────────────


print("\n📈 Ranking impact summary:")
moved_up = moved_down = unchanged = 0
for rank, item in enumerate(ranked, 1):
    orig = orig_order.get(item["article"].id, 0)
    delta = orig - (rank - 1)
    if delta > 0:
        moved_up += 1
        title = item["article"]["title"]
        print(f"   ↑ Article moved UP {delta} position(s): {title}")
    elif delta < 0:
        moved_down += 1
        title = item["article"]["title"]
        print(f"   ↓ Article moved DOWN {abs(delta)} position(s): {title}")
    else:
        unchanged += 1

print(f"\n   Up: {moved_up}  |  Down: {moved_down}  |  Unchanged: {unchanged}")
print("\n   Dynamic reranking using graph relationship signals is complete.")
print("   Articles with strong user engagement receive a meaningful boost.")
print("\n" + "─" * 58)
