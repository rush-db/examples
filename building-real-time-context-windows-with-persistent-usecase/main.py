"""
RushDB Memory Graph Demo — Real-Time Context Windows with Persistent Graph Memory

This script demonstrates a full cycle of a persistent AI agent memory system:

  1. SCHEMA — define node labels and relationship types
  2. STORE  — write graph events on each user interaction
  3. TRAVERSE — find relevant history via graph traversal
  4. RETRIEVE — rank results by vector similarity within the subgraph
  5. REBUILD  — assemble a context window from the subgraph, no summarization

Run `python seed.py` first to load mock data, then `python main.py`.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer


# ── Config ──────────────────────────────────────────────────────────────────

RUSHDB_API_KEY = os.environ.get("RUSHDB_API_KEY")
RUSHDB_URL = os.environ.get("RUSHDB_URL")

MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_LABEL = "MESSAGE"
INDEX_PROPERTY = "content"

USER_EMAIL = "alice@example.com"
USER_NAME = "Alice Chen"


# ── Client ──────────────────────────────────────────────────────────────────

def get_db():
    kwargs = {"token": RUSHDB_API_KEY} if RUSHDB_API_KEY else {}
    if RUSHDB_URL:
        kwargs["url"] = RUSHDB_URL
    return RushDB(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — SCHEMA DESIGN
# Show what the graph looks like without creating anything.
# The schema is inferred from the data — labels are defined by usage.
# ─────────────────────────────────────────────────────────────────────────────

LABELS = {
    "USER": "Persistent user identity — name, email, account preferences",
    "SESSION": "A conversation thread — has a title, startedAt, endedAt, channel",
    "MESSAGE": "A single turn — role (user/agent), content, createdAt",
    "ENTITY": "A person, topic, product, or object mentioned across sessions",
    "PREFERENCE": "A named preference edge — prefers X over Y with confidence score",
}

RELATIONSHIPS = {
    "HAS_SESSION": "USER → SESSION  |  User opened this session",
    "CONTAINS": "SESSION → MESSAGE  |  Message belongs to this session",
    "AUTHORED": "USER → MESSAGE  |  User (not agent) wrote this message",
    "MENTIONED_IN": "ENTITY → SESSION  |  Entity was referenced in this session",
    "REFERENCES": "MESSAGE → ENTITY  |  Message directly mentions this entity",
    "PREFERS_X_OVER_Y": "USER → PREFERENCE  |  Explicit preference relationship",
    "RELATED_TO": "ENTITY → ENTITY  |  Entities are semantically linked",
}


def show_schema():
    print("\n" + "=" * 60)
    print("STEP 1 — SCHEMA DESIGN")
    print("=" * 60)
    print("\nNode Labels:")
    for label, desc in LABELS.items():
        print(f"  [{label}] — {desc}")
    print("\nRelationships:")
    for rel, desc in RELATIONSHIPS.items():
        print(f"  {rel}: {desc}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — STORE: Write a new interaction into the graph
# In a real system this runs on every user message + agent response.
# ─────────────────────────────────────────────────────────────────────────────

def store_interaction(db, user_record, session_record, role, content):
    """
    Store a single message as a graph event.

    Creates:
      - MESSAGE node with role + content
      - CONTAINS edge: session → message
      - AUTHORED edge: user → message (if role == 'user')
    """
    message = db.records.create(label="MESSAGE", data={
        "role": role,
        "content": content,
        "createdAt": datetime.now().isoformat(),
    })

    db.records.attach(
        source=session_record,
        target=message,
        options={"type": "CONTAINS", "direction": "out"},
    )

    if role == "user":
        db.records.attach(
            source=user_record,
            target=message,
            options={"type": "AUTHORED", "direction": "out"},
        )

    return message


def store_entity_mention(db, session_record, entity_name, entity_type="topic"):
    """
    Create or find an ENTITY node and link it to the session.
    Called when a message mentions a product, person, or concept.
    """
    # Upsert — idempotent: find existing or create new
    existing = db.records.find({
        "labels": ["ENTITY"],
        "where": {"name": entity_name},
    })

    if existing.total > 0:
        entity = existing.data[0]
    else:
        entity = db.records.create(label="ENTITY", data={
            "name": entity_name,
            "type": entity_type,
        })

    # Link entity → session (only if not already linked)
    db.records.attach(
        source=entity,
        target=session_record,
        options={"type": "MENTIONED_IN", "direction": "out"},
    )

    return entity


def store_preference(db, user_record, prefers, over, confidence=0.9):
    """
    Store or update a preference as a PREFERENCE node.
    Uses upsert so running this twice updates the confidence, not duplicates.
    """
    pref_record = db.records.upsert(
        label="PREFERENCE",
        data={
            "prefers": prefers,
            "over": over,
            "confidence": confidence,
        },
        options={"mergeBy": ["prefers", "over"]},
    )

    # Detach old link if exists (safe to call even if not attached)
    try:
        db.records.detach(
            source=user_record,
            target=pref_record,
            options={"type": "PREFERS_X_OVER_Y"},
        )
    except Exception:
        pass  # Not attached yet — first time

    db.records.attach(
        source=user_record,
        target=pref_record,
        options={"type": "PREFERS_X_OVER_Y", "direction": "out"},
    )

    return pref_record


def demonstrate_store(db, user_record, session_record):
    print("\n" + "=" * 60)
    print("STEP 2 — STORE: Writing graph events")
    print("=" * 60)

    # Store a user message
    user_msg = store_interaction(
        db, user_record, session_record,
        role="user",
        content="I prefer working with Tailwind over plain CSS for speed."
    )
    print(f"\n  Stored message: \"{user_msg['content']}\"")
    print(f"  ID: {user_msg.id}")

    # Store an agent response
    agent_msg = store_interaction(
        db, user_record, session_record,
        role="agent",
        content="Tailwind's utility-first approach really does speed up iteration. I've seen teams cut their CSS file size significantly after switching."
    )
    print(f"\n  Stored response: \"{agent_msg['content'][:60]}...\"")
    print(f"  ID: {agent_msg.id}")

    # Store entity mentions
    entity = store_entity_mention(db, session_record, "Tailwind CSS", "framework")
    print(f"\n  Entity linked: {entity['name']} → SESSION")

    # Store a preference
    pref = store_preference(db, user_record, "Tailwind CSS", "plain CSS", confidence=0.9)
    print(f"  Preference stored: prefers {pref['prefers']} over {pref['over']} (conf={pref['confidence']})")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — TRAVERSE: Find relevant history via graph traversal
# Graph traversal narrows the search space before vector ranking.
# ─────────────────────────────────────────────────────────────────────────────

def traverse_user_sessions(db, user_record, limit=5):
    """
    Graph traversal: find the user's most recent sessions.
    Uses the USER → HAS_SESSION → SESSION path.
    """
    sessions = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "USER": {"$relation": {"type": "HAS_SESSION", "direction": "in"}},
        },
        "orderBy": {"startedAt": "desc"},
        "limit": limit,
    })
    return sessions.data


def traverse_user_messages(db, user_record, session_ids, limit=10):
    """
    Graph traversal: find user's messages within specific sessions.
    Uses SESSION → CONTAINS → MESSAGE path.
    """
    if not session_ids:
        return []

    messages = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "SESSION": {"$id": {"$in": session_ids}},
            "role": "user",
        },
        "limit": limit,
    })
    return messages.data


def traverse_user_preferences(db, user_record):
    """
    Graph traversal: get all preference relationships for this user.
    USER → PREFERS_X_OVER_Y → PREFERENCE
    """
    prefs = db.records.find({
        "labels": ["PREFERENCE"],
        "where": {
            "USER": {"$relation": {"type": "PREFERS_X_OVER_Y", "direction": "in"}},
        },
    })
    return prefs.data


def traverse_entities_in_sessions(db, session_ids):
    """
    Graph traversal: find all entities mentioned across a set of sessions.
    ENTITY → MENTIONED_IN → SESSION
    """
    if not session_ids:
        return []

    entities = db.records.find({
        "labels": ["ENTITY"],
        "where": {
            "SESSION": {"$id": {"$in": session_ids}},
        },
    })
    return entities.data


def demonstrate_traversal(db, user_record):
    print("\n" + "=" * 60)
    print("STEP 3 — TRAVERSE: Graph traversal to find relevant history")
    print("=" * 60)

    # Find recent sessions
    sessions = traverse_user_sessions(db, user_record, limit=5)
    session_ids = [s.id for s in sessions]

    print(f"\n  Found {len(sessions)} sessions for {USER_NAME}:")
    for s in sessions:
        started = s.get("startedAt", "unknown")
        title = s.get("title", "untitled")
        print(f"    [{started[:10]}] {title}")

    # Get preferences
    prefs = traverse_user_preferences(db, user_record)
    print(f"\n  Found {len(prefs)} explicit preferences:")
    for p in prefs:
        print(f"    • prefers {p['prefers']} over {p['over']} (conf={p.get('confidence', '?')})")

    # Get entities
    entities = traverse_entities_in_sessions(db, session_ids)
    print(f"\n  Found {len(entities)} entities mentioned across sessions:")
    for e in entities:
        print(f"    • {e['name']} ({e.get('type', 'unknown')})")

    # Get user messages in those sessions
    messages = traverse_user_messages(db, user_record, session_ids, limit=5)
    print(f"\n  Found {len(messages)} user-authored messages:")
    for m in messages[:3]:
        content = m["content"][:60]
        print(f"    \"{content}...\"")

    return sessions, prefs, entities


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — RETRIEVE: Vector search within the subgraph
# Graph traversal narrows the scope → vector ranking picks the right memories.
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_relevant_memories(db, sessions, query, limit=3):
    """
    Vector search within the subgraph narrowed by traversal.

    Two-step retrieval:
      1. Graph traversal identifies which sessions are relevant
      2. Vector search ranks messages within those sessions by semantic similarity

    This is more precise than pure vector search because the graph
    enforces constraints that text similarity alone cannot encode.
    """
    session_ids = [s.id for s in sessions]
    if not session_ids:
        return []

    # Vector search scoped to messages in these sessions
    results = db.ai.search({
        "propertyName": INDEX_PROPERTY,
        "query": query,
        "labels": [INDEX_LABEL],
        "where": {
            "SESSION": {"$id": {"$in": session_ids}},
            "role": "user",
        },
        "limit": limit,
    })

    return results.data


def demonstrate_retrieval(db, sessions):
    print("\n" + "=" * 60)
    print("STEP 4 — RETRIEVE: Vector search within subgraph")
    print("=" * 60)

    queries = [
        "React component structure and best practices",
        "TypeScript project configuration",
        "styling with Tailwind CSS",
    ]

    for query in queries:
        results = retrieve_relevant_memories(db, sessions, query, limit=2)
        print(f'\n  Query: "{query}"')
        if not results:
            print("    No results (vector index may not be seeded — run seed.py)")
        else:
            for r in results:
                score = r.score if hasattr(r, 'score') else r.data.get("__score", 0)
                content = r["content"][:70]
                print(f"    [{score:.3f}] \"{content}...\"")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — REBUILD: Assemble context window from subgraph
# No summarization — the full subgraph is injected verbatim.
# ─────────────────────────────────────────────────────────────────────────────

class ContextBuilder:
    """
    Assembles a context window from the memory graph.

    The context window contains:
      - User identity and preferences
      - Recent sessions with titles and dates
      - Top-ranked memories from vector search
      - Entities mentioned in relevant sessions

    This is a data structure, not a prompt string —
    callers decide how to inject it into their prompt format.
    """

    def __init__(self, db: RushDB):
        self.db = db
        self._user = None
        self._sessions = []
        self._preferences = []
        self._top_memories = []
        self._entities = []

    def load_user(self, email: str):
        """Identify the user and load their profile."""
        result = self.db.records.find({
            "labels": ["USER"],
            "where": {"email": email},
        })
        if result.total == 0:
            raise ValueError(f"No user found with email: {email}")
        self._user = result.data[0]
        return self

    def load_sessions(self, limit=5):
        """Traverse graph to find recent sessions."""
        if not self._user:
            raise RuntimeError("Call load_user() first")
        self._sessions = traverse_user_sessions(self.db, self._user, limit=limit)
        return self

    def load_preferences(self):
        """Traverse graph to get all explicit preferences."""
        if not self._user:
            raise RuntimeError("Call load_user() first")
        self._preferences = traverse_user_preferences(self.db, self._user)
        return self

    def load_top_memories(self, query: str, limit=3):
        """Vector search within the subgraph."""
        if not self._sessions:
            raise RuntimeError("Call load_sessions() first")
        self._top_memories = retrieve_relevant_memories(
            self.db, self._sessions, query, limit=limit
        )
        return self

    def load_entities(self):
        """Traverse graph to find entities in relevant sessions."""
        if not self._sessions:
            raise RuntimeError("Call load_sessions() first")
        session_ids = [s.id for s in self._sessions]
        self._entities = traverse_entities_in_sessions(self.db, session_ids)
        return self

    def build(self) -> dict:
        """
        Return the complete context window as a structured dict.
        This is the raw subgraph — callers inject into their prompt format.
        """
        return {
            "user": {
                "id": self._user.id,
                "name": self._user.get("name"),
                "email": self._user.get("email"),
            },
            "preferences": [
                {
                    "prefers": p["prefers"],
                    "over": p["over"],
                    "confidence": p.get("confidence"),
                }
                for p in self._preferences
            ],
            "sessions": [
                {
                    "id": s.id,
                    "title": s.get("title"),
                    "startedAt": s.get("startedAt"),
                    "channel": s.get("channel"),
                }
                for s in self._sessions
            ],
            "top_memories": [
                {
                    "id": m.id,
                    "content": m["content"],
                    "role": m.get("role"),
                    "score": m.score if hasattr(m, 'score') else None,
                }
                for m in self._top_memories
            ],
            "entities": [
                {"name": e["name"], "type": e.get("type")}
                for e in self._entities
            ],
        }

    def to_prompt_text(self, current_message: str = "") -> str:
        """
        Render the context window as plain text for a prompt.
        This format is ready to inject into an LLM prompt.
        """
        if not self._user:
            return "[No user context loaded]"

        parts = []
        parts.append(f"[USER] {self._user.get('name')} <{self._user.get('email')}>\n")

        if self._preferences:
            parts.append("[PREFERENCES]")
            for p in self._preferences:
                parts.append(f"  - prefers {p['prefers']} over {p['over']}")
            parts.append("")

        if self._sessions:
            parts.append("[RECENT SESSIONS]")
            for s in self._sessions:
                date = s.get("startedAt", "")[:10]
                parts.append(f"  - [{date}] {s.get('title', 'untitled')}")
            parts.append("")

        if self._top_memories:
            parts.append("[RELEVANT MEMORIES]")
            for m in self._top_memories:
                parts.append(f"  - \"{m['content'][:120]}\"")
            parts.append("")

        if self._entities:
            parts.append("[KNOWN ENTITIES]")
            parts.append(", ".join(e["name"] for e in self._entities))
            parts.append("")

        if current_message:
            parts.append(f"[CURRENT MESSAGE] {current_message}")

        return "\n".join(parts)


def demonstrate_context_rebuild(db, user_record):
    print("\n" + "=" * 60)
    print("STEP 5 — REBUILD: Assemble context window from subgraph")
    print("=" * 60)

    builder = (
        ContextBuilder(db)
        .load_user(USER_EMAIL)
        .load_sessions(limit=5)
        .load_preferences()
        .load_entities()
        .load_top_memories("React and styling preferences", limit=3)
    )

    context = builder.build()

    print("\n  Context window (structured dict):")
    print(f"    user: {context['user']['name']}")
    print(f"    sessions: {len(context['sessions'])}")
    print(f"    preferences: {len(context['preferences'])}")
    print(f"    top_memories: {len(context['top_memories'])}")
    print(f"    entities: {len(context['entities'])}")

    print("\n  Prompt-ready text:\n")
    prompt_text = builder.to_prompt_text(current_message="How do I structure a React component?")
    for line in prompt_text.split("\n"):
        print(f"    {line}")

    return context


# ─────────────────────────────────────────────────────────────────────────────
# DEMO: Full session lifecycle
# Simulates a new session starting, context being loaded, and a message stored.
# ─────────────────────────────────────────────────────────────────────────────

def demo_session_lifecycle(db):
    print("\n" + "=" * 60)
    print("DEMO: New session lifecycle")
    print("=" * 60)

    # Check for existing user
    user_result = db.records.find({
        "labels": ["USER"],
        "where": {"email": USER_EMAIL},
    })

    if user_result.total == 0:
        print(f"\n  No prior memory found for {USER_NAME}")
        print("  → Cold start: no context window needed")
        return

    user = user_result.data[0]

    # Build context for the new session
    builder = (
        ContextBuilder(db)
        .load_user(USER_EMAIL)
        .load_sessions(limit=5)
        .load_preferences()
        .load_top_memories("React frontend styling", limit=3)
    )

    print(f"\n  Context window for {USER_NAME}:")
    print("  ─" * 20)
    context = builder.build()

    print("\n  Alice's preferences:")
    for p in context["preferences"]:
        print(f"    • prefers {p['prefers']} over {p['over']}")

    print("\n  Recent sessions:")
    for s in context["sessions"]:
        date = s["startedAt"][:10]
        print(f"    • {date}: {s['title']}")

    print("\n  Relevant memories (semantic):")
    for m in context["top_memories"]:
        score = m["score"] if m["score"] else 0
        content = m["content"][:60]
        print(f"    [{score:.2f}] \"{content}...\"")

    print("\n  Context window ready for injection:")
    print("  ─" * 20)
    prompt = builder.to_prompt_text(current_message="How do I structure a React component?")
    print("\n" + prompt)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "#" * 60)
    print("#  RushDB: Real-Time Context Windows with Persistent Memory")
    print("#" * 60)

    if not RUSHDB_API_KEY:
        print("\nERROR: RUSHDB_API_KEY is not set.")
        print("Copy .env.example to .env and fill in your API key.")
        sys.exit(1)

    db = get_db()

    # Step 1: Show schema (data model design)
    show_schema()

    # Find existing user
    user_result = db.records.find({
        "labels": ["USER"],
        "where": {"email": USER_EMAIL},
    })

    if user_result.total == 0:
        print("\n" + "=" * 60)
        print("No data found. Run `python seed.py` first to load mock data.")
        print("=" * 60 + "\n")
        return

    user = user_result.data[0]

    # Step 2: Demonstrate storing new interactions
    # Find the latest session to attach to
    sessions_result = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "USER": {"$relation": {"type": "HAS_SESSION", "direction": "in"}},
        },
        "orderBy": {"startedAt": "desc"},
        "limit": 1,
    })
    latest_session = sessions_result.data[0] if sessions_result.total > 0 else None

    if latest_session:
        demonstrate_store(db, user, latest_session)

    # Step 3: Demonstrate graph traversal
    demonstrate_traversal(db, user)

    # Step 4: Demonstrate vector retrieval within subgraph
    demonstrate_retrieval(db, sessions_result.data)

    # Step 5: Demonstrate context window reconstruction
    demonstrate_context_rebuild(db, user)

    # Demo: New session lifecycle
    demo_session_lifecycle(db)

    print("\n" + "#" * 60)
    print("#  Demo complete!")
    print("#  Try querying with different search terms in main.py")
    print("#  Or run seed.py to reset the data and start fresh.")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
