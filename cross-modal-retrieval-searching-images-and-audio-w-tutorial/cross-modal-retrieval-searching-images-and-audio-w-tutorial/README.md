# Cross-Modal Retrieval: Searching Images and Audio with Graph-Structured Vectors

This tutorial demonstrates how to build a cross-modal retrieval system using RushDB, allowing you to search across images and audio files using semantic queries. We use **CLIP** for image embeddings and **CLAP** for audio embeddings, stored in RushDB's property graph with shared concept nodes for cross-modal linkage.

## What This Tutorial Demonstrates

- **Schema Design**: Modeling images, audio, and shared concept nodes in RushDB
- **Embedding Generation**: Using CLIP (images) and CLAP (audio) for semantic vectors
- **Graph Linking**: Connecting modalities through shared concept nodes
- **Cross-Modal Queries**: Searching across modalities (e.g., "find audio that matches this image's mood")
- **Refinements**: Filtering by metadata and adjusting graph traversal depth

## Prerequisites

- Python 3.9+
- RushDB account with API key ([get one free](https://rushdb.com))
- Neo4j Aura instance (required for vector indexes) or local Neo4j

## Setup

1. **Clone the repository and navigate to the project:**
```bash
git clone https://github.com/rush-db/examples
cd cross-modal-retrieval-searching-images-and-audio-w-tutorial
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env and fill in your RUSHDB_API_KEY and optional RushDB URL
```

5. **Run the seed script to populate sample data:**
```bash
python seed.py
```

6. **Execute the main tutorial script:**
```bash
python main.py
```

## Expected Output

The script will:
1. Create the schema (Image, Audio, Concept labels)
2. Generate CLIP embeddings for images and CLAP embeddings for audio
3. Create vector indexes for semantic search
4. Demonstrate cross-modal queries between images and audio
5. Show metadata filtering and graph traversal refinements

## How Cross-Modal Retrieval Works

```
Text Query (e.g., "calm nature sounds")
         │
         ▼
┌─────────────────────────────┐
│   RushDB Vector Search      │
│                             │
│  ┌─────────┐    ┌────────┐  │
│  │ CLIP    │    │ CLAP   │  │
│  │ Index   │    │ Index  │  │
│  └────┬────┘    └────┬───┘  │
│       │              │      │
│       ▼              ▼      │
│  ┌─────────┐    ┌────────┐  │
│  │ Images  │    │ Audio  │  │
│  └────┬────┘    └────┬───┘  │
│       │              │      │
│       └──────┬───────┘      │
│              ▼              │
│     Shared Concept Nodes    │
│     (categories, moods)     │
└─────────────────────────────┘
```

## Project Structure

```
.
├── README.md          # This file
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── seed.py           # Generates sample images, audio, and concepts
├── main.py           # Main tutorial demonstrating cross-modal retrieval
└── data/
    └── sample_data.json  # Generated sample data (created by seed.py)
```

## Cost Note

This tutorial demonstrates the following RushDB operations:
- **Record creation**: ~0.5 KU per record
- **Vector embedding generation**: ~5 KU per embedding (external - you generate)
- **Vector search**: ~5 KU per search call
- **Reads**: Always free

The sample dataset (~40 records) will cost approximately 100-150 KU total.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [CLIP Model Paper](https://arxiv.org/abs/2103.00020)
- [CLAP Model](https://github.com/LAION-AI/audio-dataset)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/cross-modal-retrieval-searching-images-and-audio-w-tutorial)
