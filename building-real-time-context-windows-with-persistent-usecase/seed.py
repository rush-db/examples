"""
Seed script — generates mock multi-session agent memory data.

Creates:
  - 1 USER (Alice Chen)
  - 3 SESSION nodes across different dates
  - ~15 MESSAGE nodes (user + agent turns)
  - 6 ENTITY nodes (people, topics, products)
  - 4 PREFERENCE relationships
  - All messages are vectorized for semantic search

Idempotent: skips re-seeding if data already exists.
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
or os.environ.get("RUSHDB_URL")  # self-hosted fallback
RUSHDB_URL = os.environ.get("RUSHDB_URL")

MODEL_NAME = "all-MiniLM-L6-v2"  # lightweight, fast, good quality
INDEX_LABEL = "MESSAGE"
INDEX_PROPERTY = "content"

# ── Seed data ───────────────────────────────────────────────────────────────

USER_EMAIL = "alice@example.com"
USER_NAME = "Alice Chen"

# Three sessions spanning two weeks
now = datetime.now()

SESSIONS = [
    {
        "id": "session-1",
        "title": "VSCode Extension Research",
        "startedAt": (now - timedelta(days=14)).isoformat(),
        "endedAt": (now - timedelta(days=14, hours=1)).isoformat(),
        "channel": "chat",
    },
    {
        "id": "session-2",
        "title": "TypeScript Project Setup",
        "startedAt": (now - timedelta(days=2)).isoformat(),
        "endedAt": (now - timedelta(days=2, hours=2)).isoformat(),
        "channel": "chat",
    },
    {
        "id": "session-3",
        "title": "React + Tailwind UI Discussion",
        "startedAt": now.isoformat(),
        "channel": "chat",
    },
]

# Messages per session: (role, content)
MESSAGES = {
    "session-1": [
        ("user", "I'm looking into building a VSCode extension for our team. Where do I start?"),
        ("agent", "Great question! The VSCode Extension API is well-documented. Start with the Hello World template, then explore the contribution points you need — commands, tree views, or a webview."),
        ("user", "Can I use TypeScript for the extension?"),
        ("agent", "Yes, TypeScript is the recommended language for VSCode extensions. The yo code generator scaffolds a TS project by default."),
        ("user", "Perfect. I'll use the webview API for the UI part."),
    ],
    "session-2": [
        ("user", "Can you help me set up a TypeScript project from scratch?"),
        ("agent", "Sure. Start with npm init -y, then install typescript and @types/node as dev dependencies. Run npx tsc --init to generate tsconfig.json."),
        ("user", "What about linting and formatting?"),
        ("agent", "Add ESLint with the TypeScript parser and Prettier for formatting. Configure them to work together so there are no conflicts between lint and format rules."),
        ("user", "I want to use React for the frontend. Any tsconfig recommendations?"),
        ("agent", "Enable jsx: react-jsx in tsconfig, install @types/react and @types/react-dom, and consider strict: true for better type safety across your React components."),
        ("user", "Great, I'll try that setup today."),
    ],
    "session-3": [
        ("user", "I started the React project. Now I want to style it nicely."),
        ("agent", "Tailwind CSS pairs very well with React. Run npm install -D tailwindcss postcss autoprefixer, then npx tailwindcss init -p to scaffold the config."),
        ("user", "Do you prefer Tailwind or plain CSS?"),
        ("agent", "Tailwind wins on velocity for most projects — utility classes mean you rarely write a separate stylesheet. Plain CSS with BEM is still solid for small, design-heavy projects."),
        ("user", "I tried Tailwind but the dark mode setup is confusing."),
        ("agent", "Enable darkMode: 'class' in tailwind.config.js, then add class='dark' to your html element. Use the dark: prefix on any class to target dark mode — dark:bg-gray-900, dark:text-white."),
        ("user", "That worked. Now I want to deploy to Vercel."),
        ("agent", "Install vercel globally (npm i -g vercel), run vercel in your project root. It auto-detects Next.js and React. For a plain React app, set the output directory to build if needed."),
    ],
}

ENTITIES = [
    {"name": "VSCode", "type": "tool", "description": "Visual Studio Code, a code editor by Microsoft"},
    {"name": "TypeScript", "type": "language", "description": "A typed superset of JavaScript by Microsoft"},
    {"name": "React", "type": "framework", "description": "A JavaScript library for building user interfaces"},
    {"name": "Tailwind CSS", "type": "framework", "description": "A utility-first CSS framework"},
    {"name": "Vercel", "type": "platform", "description": "A cloud platform for frontend frameworks"},
    {"name": "ESLint", "type": "tool", "description": "A static code analyzer for JavaScript and TypeScript"},
]

PREFERENCES = [
    {"prefers": "React", "over": "Angular", "confidence": 0.9},
    {"prefers": "Tailwind CSS", "over": "plain CSS", "confidence": 0.85},
    {"prefers": "dark mode", "over": "light mode", "confidence": 0.95},
    {"prefers": "TypeScript", "over": "plain JavaScript", "confidence": 1.0},
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_db():
    kwargs = {"token": RUSHDB_API_KEY} if RUSHDB_API_KEY else {}
    if RUSHDB_URL:
        kwargs["url"] = RUSHDB_URL
    return RushDB(**kwargs)


def get_embedding_model():
    print(f"Loading embedding model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)


def setup_vector_index(db):
    """Create the vector index if it doesn't exist."""
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx["label"] == INDEX_LABEL and idx["propertyName"] == INDEX_PROPERTY:
            print(f"  Vector index already exists: {INDEX_LABEL}.{INDEX_PROPERTY}")
            return idx["__id"]

    print(f"  Creating vector index: {INDEX_LABEL}.{INDEX_PROPERTY}")
    index = db.ai.indexes.create({
        "label": INDEX_LABEL,
        "propertyName": INDEX_PROPERTY,
        "sourceType": "external",
        "dimensions": 384,  # all-MiniLM-L6-v2 output dimension
        "similarityFunction": "cosine",
    })
    return index.data["__id"]


# ── Main ─────────────────────────────────────────────────────────────────────

def seed():
    print("\n=== RushDB Memory Seed Script ===\n")

    db = get_db()

    # Check if already seeded
    existing_users = db.records.find({"labels": ["USER"], "where": {"email": USER_EMAIL}})
    if existing_users.total > 0:
        print(f"Data already exists for {USER_EMAIL}. Skipping seed.")
        print(f"Run 'python main.py' to explore the existing memory graph.\n")
        return

    print("Seeding new data...\n")

    # Load model and create index
    model = get_embedding_model()
    index_id = setup_vector_index(db)

    # 1. Create USER
    print("  Creating USER: Alice Chen")
    user = db.records.create(label="USER", data={
        "name": USER_NAME,
        "email": USER_EMAIL,
        "createdAt": (now - timedelta(days=14)).isoformat(),
    })

    # 2. Create sessions, messages, and vectors
    all_messages = []  # (record, content, session_id)

    for i, session_data in enumerate(SESSIONS):
        print(f"  Creating SESSION {i+1}/3: {session_data['title']}")
        session = db.records.create(label="SESSION", data=session_data)

        # Attach user → session
        db.records.attach(
            source=user,
            target=session,
            options={"type": "HAS_SESSION", "direction": "out"},
        )

        # Create messages in this session
        session_messages = MESSAGES.get(session_data["id"], [])
        for j, (role, content) in enumerate(session_messages):
            if j % 100 == 0:
                print(f"    Messages: {j}/{len(session_messages)}")

            message_record = db.records.create(label="MESSAGE", data={
                "role": role,
                "content": content,
                "createdAt": (datetime.fromisoformat(session_data["startedAt"]) + timedelta(minutes=j * 5)).isoformat(),
            })

            # Link: session → message → user (authored)
            db.records.attach(
                source=session,
                target=message_record,
                options={"type": "CONTAINS", "direction": "out"},
            )
            if role == "user":
                db.records.attach(
                    source=user,
                    target=message_record,
                    options={"type": "AUTHORED", "direction": "out"},
                )

            all_messages.append((message_record, content, session.id))

    print(f"  Created {len(all_messages)} messages across 3 sessions")

    # 3. Create entities and link to sessions where they were mentioned
    print("  Creating ENTITY nodes and cross-links...")
    for entity_data in ENTITIES:
        entity = db.records.create(label="ENTITY", data=entity_data)

        # Link entity → session for relevant mentions
        entity_name_lower = entity_data["name"].lower()
        for session_data in SESSIONS:
            session_messages = MESSAGES.get(session_data["id"], [])
            full_text = " ".join(c for _, c in session_messages).lower()
            if entity_name_lower in full_text:
                # Find the session record
                found = db.records.find({
                    "labels": ["SESSION"],
                    "where": {"title": session_data["title"]},
                })
                if found.total > 0:
                    db.records.attach(
                        source=entity,
                        target=found.data[0],
                        options={"type": "MENTIONED_IN", "direction": "out"},
                    )

    print("  Created 6 ENTITY nodes")

    # 4. Create preferences as relationships
    print("  Creating PREFERENCE relationships...")
    for pref in PREFERENCES:
        pref_record = db.records.create(label="PREFERENCE", data={
            "prefers": pref["prefers"],
            "over": pref["over"],
            "confidence": pref["confidence"],
        })
        db.records.attach(
            source=user,
            target=pref_record,
            options={"type": "PREFERS_X_OVER_Y", "direction": "out"},
        )

    print("  Created 4 preference relationships")

    # 5. Batch upsert vectors
    print("  Computing embeddings and upserting to vector index...")
    texts = [content for _, content, _ in all_messages]
    vectors = model.encode(texts, show_progress_bar=False)

    vector_items = [
        {"recordId": msg_record.id, "vector": vector.tolist()}
        for (msg_record, _, _), vector in zip(all_messages, vectors)
    ]

    db.ai.indexes.upsert_vectors(index_id, {"items": vector_items})

    print(f"  Upserted {len(vector_items)} vectors")

    print("\n✅ Seed complete!")
    print(f"   User: {USER_NAME} ({USER_EMAIL})")
    print(f"   Sessions: {len(SESSIONS)}")
    print(f"   Messages: {len(all_messages)}")
    print(f"   Entities: {len(ENTITIES)}")
    print(f"   Preferences: {len(PREFERENCES)}")
    print(f"   Vectors indexed: {len(vector_items)}\n")


if __name__ == "__main__":
    if not RUSHDB_API_KEY:
        print("ERROR: RUSHDB_API_KEY is not set.")
        print("Copy .env.example to .env and fill in your API key.")
        sys.exit(1)
    seed()
