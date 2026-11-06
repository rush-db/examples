# Cross-Modal Retrieval: Searching Images and Audio with Graph-Structured Vectors

**Repository**: [github.com/rush-db/examples](https://github.com/rush-db/examples/tree/main/cross-modal-retrieval-searching-images-and-audio-w-usecase)

## What This Demonstrates

This project implements a complete cross-modal search system using RushDB's hybrid graph+vector architecture. It solves the fundamental problem that semantic gaps between modalities (images vs. audio) prevent pure vector similarity from working across them.

**The Core Problem**: A dog bark and a photo of a dog share no pixels or waveforms, yet humans instantly recognize their semantic relationship. Vector similarity across modalities requires a bridge.

**The Solution**: Graph topology as the semantic bridge. Images and audio are indexed by their vector embeddings, but they're connected through `CONCEPT` anchor nodes representing shared semantic properties (emotions, themes, objects, contexts). This allows queries like:

> "Find audio clips that match this image's emotional tone"

## Architecture

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   IMAGE     │──────▶│   CONCEPT    │◀──────│    AUDIO    │
│  (vectors)  │       │   (anchor)   │       │  (vectors)  │
└─────────────┘       └──────────────┘       └─────────────┘
     │                     ▲                      │
     │                     │                      │
     ▼                     │                      ▼
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│  Semantic   │       │   Graph      │       │  Cross-Modal│
│  Search     │       │  Traversal   │       │   Bridge    │
└─────────────┘       └──────────────┘       └─────────────┘
```

## Setup

```bash
# 1. Clone and navigate to project
cd cross-modal-retrieval-searching-images-and-audio-w-usecase

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your RushDB API key
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `RUSHDB_API_KEY` | Your RushDB API key from the dashboard |
| `RUSHDB_URL` | (Optional) Custom self-hosted URL |

## Running

### Option 1: Full Pipeline (seed + demonstrate)

```bash
python main.py --mode full
```

This will:
1. Check if data exists, seed if needed (creates 30 images, 30 audio clips, 15 concept anchors)
2. Create vector indexes for semantic search
3. Run all demonstration queries

### Option 2: Demonstrate Only (requires pre-seeded data)

```bash
python main.py --mode demo
```

### Option 3: Seed Only

```bash
python seed.py
```

## What the Code Demonstrates

### 1. Schema Design

RushDB's zero-schema approach allows modeling cross-modal relationships without predefined Cypher:

- **IMAGE** nodes: visual content with embeddings for semantic search
- **AUDIO** nodes: audio content with embeddings for semantic search  
- **CONCEPT** nodes: semantic bridge anchors (emotions, themes, objects)
- **Relationships**: `IMAGE-[:REPRESENTS]->CONCEPT`, `AUDIO-[:EXPRESSES]->CONCEPT`

### 2. Cross-Modal Query Pattern

```python
# Query: "Find audio clips matching this image's emotional tone"

# Step 1: Vector search within modality
query_image = db.ai.search({
    "propertyName": "description",
    "query": "peaceful sunrise over mountains",
    "labels": ["IMAGE"],
    "limit": 3
})

# Step 2: Graph traversal to bridge modalities
audio_clips = db.records.find({
    "labels": ["AUDIO"],
    "where": {
        "CONCEPT": {
            "$relation": {
                "type": "EXPRESSES",
                "direction": "in"
            },
            "id": {"$in": [c.id for c in query_image.data[0].concepts]}
        }
    },
    "limit": 10
})
```

### 3. Graph-First Query Pattern

For queries where modality matters less than semantic relationship:

```python
# Query: "Find everything related to 'serenity' concept"
concepts = db.records.find({
    "labels": ["CONCEPT"],
    "where": {
        "name": {"$contains": "serene"}
    }
})

related_images = db.records.find({
    "labels": ["IMAGE"],
    "where": {
        "CONCEPT": {"$id": {"$in": [c.id for c in concepts.data]}}
    }
})

related_audio = db.records.find({
    "labels": ["AUDIO"],
    "where": {
        "CONCEPT": {"$id": {"$in": [c.id for c in concepts.data]}}
    }
})
```

## Embedding Strategy

This example uses **all-MiniLM-L6-v2** from `sentence-transformers`:
- 384 dimensions, fast inference, good general-purpose performance
- Captures semantic meaning for cross-modal bridging
- Runs locally (no external API needed)

For production, consider:
- **CLIP** for image-text alignment (OpenAI)
- **AudioCLIP** for audio-visual alignment
- OpenAI/Cohere embeddings for higher quality

## Expected Output

```
=== CROSS-MODAL RETRIEVAL DEMO ===

[1] Seeding database with cross-modal content...
    ✓ Created 30 IMAGE records
    ✓ Created 30 AUDIO clips  
    ✓ Created 15 CONCEPT anchors
    ✓ Established 90 cross-modal relationships
    ✓ Indexed 60 records with vector embeddings

[2] Demo 1: Within-modality semantic search (Images)
    Query: "peaceful nature scene"
    Results: [score] - description
    - 0.847 - "Golden hour over mountain lake"
    - 0.812 - "Autumn forest path with soft light"

[3] Demo 2: Within-modality semantic search (Audio)
    Query: "upbeat celebration music"
    Results:
    - 0.891 - "Festival drum circle recording"
    - 0.834 - "Orchestral celebration fanfare"

[4] Demo 3: Cross-modal search - Images to Audio
    Query image: "sunset over calm ocean"
    Concepts via graph: [serene, peaceful, contemplative]
    Bridged audio results:
    - "Gentle waves ambient track" (0.78)
    - "Meditation bell sequence" (0.72)

[5] Demo 4: Concept-centric retrieval
    Concept: "excitement"
    Related images: 4
    Related audio: 6
    All items connected via graph edges

=== DONE ===
```

## Key RushDB Features Used

| Feature | Method | Purpose |
|---------|--------|---------|
| Record creation | `db.records.create()` | Store image/audio/concept nodes |
| Relationships | `db.records.attach()` | Link media to concept anchors |
| Vector index | `db.ai.indexes.create()` | Enable semantic search |
| Vector write | `vectors=[]` on create | Store embeddings inline |
| Semantic search | `db.ai.search()` | Find similar content by meaning |
| Graph traversal | `db.records.find()` with `where` | Filter by related record properties |
| Transactions | `with db.transactions.begin() as tx` | Atomic multi-step operations |

## Pricing Note

This example creates ~75 records with properties, relationships, and embeddings.

**Estimated Knowledge Units**: ~650 KU (records: 0.5, properties: 1, relationships: 0.25, embeddings: 5 each)

- **Free tier**: 100K KU/month - fully sufficient for this demo
- **Pro tier**: $24/month for 10M KU

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Vector Search Guide](https://docs.rushdb.com/features/vector-search)
- [Graph Relationships](https://docs.rushdb.com/features/relationships)
- [Python SDK Reference](https://docs.rushdb.com/sdks/python)