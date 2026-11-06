# Cross Modal Linking: Connecting Text Chunks to Tables and Images

This tutorial demonstrates a complete pipeline for ingesting multimodal documents into RushDB — extracting text sections, tables, and images, chunking them semantically, and creating a rich graph of relationships that enables cross-modal retrieval.

## What It Demonstrates

- **Document parsing**: Extract text, tables (as structured JSON), and image references with bounding box context from a research paper
- **Semantic chunking**: Split text by sections, tables by logical row boundaries, and prepare images with caption context
- **Graph modeling**: Create RushDB nodes with modality-specific labels (`TextChunk`, `TableChunk`, `ImageReference`)
- **Relationship creation**: Link modalities with typed edges (`SUPPORTS`, `CONTAINS`, `SOURCE_OF`, `ILLUSTRATES`)
- **Cross-modal retrieval**: Embed a query, find similar text chunks, then traverse graph edges to pull in related tables and images

## Prerequisites

- Python 3.9+
- A RushDB account (free tier works)
- `sentence-transformers` for local embeddings (no API key required)

## Setup

```bash
# Clone the repository
git clone https://github.com/rush-db/examples
cd cross-modal-linking-connecting-text-chunks-to-tabl-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your RushDB API key from https://app.rushdb.com
```

## Running the Tutorial

### Step 1: Seed the sample data (optional)

The `seed.py` script generates a synthetic research paper document with text sections, tables, and image references. Run it once to load the document into RushDB:

```bash
python seed.py
```

This will:
- Create a document record
- Parse and chunk text sections into `TextChunk` nodes
- Parse tables into `TableChunk` nodes
- Create image references as `ImageReference` nodes
- Link everything with cross-modal relationships

### Step 2: Run the main query pipeline

```bash
python main.py
```

This will:
1. Create a vector index for text embeddings (if not exists)
2. Embed a sample query about the research findings
3. Find similar text chunks via semantic search
4. Traverse graph edges to retrieve related tables and images
5. Display the cross-modal results

## Project Structure

```
.
├── README.md          # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py            # Document ingestion script
├── main.py            # Cross-modal query demonstration
└── data/
    └── document.json  # Sample research paper data
```

## Understanding the Graph Model

```
DOCUMENT
    ├── SUPPORTS ──► TextChunk (section: abstract)
    ├── CONTAINS ──► TableChunk (table: results_comparison)
    │       ▲
    │       └── SOURCE_OF ──► ImageReference (figure 1)
    │
    └── ILLUSTRATES ──► ImageReference (figure 2)
```

**Labels**:
- `DOCUMENT` — The source document
- `TextChunk` — Parsed text sections with metadata
- `TableChunk` — Tables with structured row/column data
- `ImageReference` — Image references with caption and bounding box

**Relationships**:
- `SUPPORTS` — Document → TextChunk
- `CONTAINS` — Document → TableChunk
- `SOURCE_OF` — TableChunk → ImageReference (image derived from table)
- `ILLUSTRATES` — ImageReference → TextChunk (image illustrates text)

## Key Code Patterns

### Creating Modal Nodes

```sdk
from rushdb import RushDB

db = RushDB("your-api-key")

# Text chunk with embedding
text_chunk = db.records.create(
    label="TextChunk",
    data={
        "content": "Our experiments show a 23% improvement...",
        "section": "results",
        "heading": "Experimental Results"
    },
    vectors=[{"propertyName": "content", "vector": embedding}]
)

# Table chunk as structured JSON
table_chunk = db.records.create(
    label="TableChunk",
    data={
        "title": "Model Comparison Results",
        "rows": [{"model": "Alpha", "accuracy": 0.92}, ...],
        "headers": ["Model", "Accuracy", "Latency"]
    }
)

# Image reference with bounding box
image_ref = db.records.create(
    label="ImageReference",
    data={
        "caption": "Training loss curve over 100 epochs",
        "source_file": "figure_3.png",
        "bounding_box": {"x": 100, "y": 200, "width": 400, "height": 300}
    }
)
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Text chunk with embedding
const textChunk = await db.records.create({
    label: 'TextChunk',
    data: {
        content: 'Our experiments show a 23% improvement...',
        section: 'results',
        heading: 'Experimental Results'
    },
    vectors: [{ propertyName: 'content', vector: embedding }]
})

// Table chunk as structured JSON
const tableChunk = await db.records.create({
    label: 'TableChunk',
    data: {
        title: 'Model Comparison Results',
        rows: [{ model: 'Alpha', accuracy: 0.92 }, ...],
        headers: ['Model', 'Accuracy', 'Latency']
    }
})

// Image reference with bounding box
const imageRef = await db.records.create({
    label: 'ImageReference',
    data: {
        caption: 'Training loss curve over 100 epochs',
        sourceFile: 'figure_3.png',
        boundingBox: { x: 100, y: 200, width: 400, height: 300 }
    }
})
```

### Creating Cross-Modal Relationships

```sdk
from rushdb import RushDB

db = RushDB("your-api-key")

# Link table to supporting text
db.records.attach(
    source=table_chunk,
    target=text_chunk,
    options={"type": "SUPPORTS"}
)

# Link image to source table
db.records.attach(
    source=table_chunk,
    target=image_ref,
    options={"type": "SOURCE_OF"}
)

# Link image to illustrated text
db.records.attach(
    source=image_ref,
    target=text_chunk,
    options={"type": "ILLUSTRATES"}
)
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Link table to supporting text
await db.records.attach({
    source: tableChunk,
    target: textChunk,
    options: { type: 'SUPPORTS' }
})

// Link image to source table
await db.records.attach({
    source: tableChunk,
    target: imageRef,
    options: { type: 'SOURCE_OF' }
})

// Link image to illustrated text
await db.records.attach({
    source: imageRef,
    target: textChunk,
    options: { type: 'ILLUSTRATES' }
})
```

### Cross-Modal Query

```sdk
from rushdb import RushDB

db = RushDB("your-api-key")

# 1. Semantic search for text chunks
results = db.ai.search({
    propertyName: "content",
    query: "neural network training improvements",
    labels: ["TextChunk"],
    limit: 3
})

# 2. For each result, traverse to related tables and images
for chunk in results.data:
    # Find supporting tables
    supporting_tables = db.records.find({
        labels: ["TableChunk"],
        where: {
            "TextChunk": {"$relation": {"type": "SUPPORTS", "direction": "in"}}
        }
    })
    
    # Find illustrating images
    illustrating_images = db.records.find({
        labels: ["ImageReference"],
        where: {
            "TextChunk": {"$relation": {"type": "ILLUSTRATES", "direction": "in"}}
        }
    })
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// 1. Semantic search for text chunks
const results = await db.ai.search({
    propertyName: 'content',
    query: 'neural network training improvements',
    labels: ['TextChunk'],
    limit: 3
})

// 2. For each result, traverse to related tables and images
for (const chunk of results.data) {
    // Find supporting tables
    const supportingTables = await db.records.find({
        labels: ['TableChunk'],
        where: {
            'TextChunk': { $relation: { type: 'SUPPORTS', direction: 'in' } }
        }
    })
    
    // Find illustrating images
    const illustratingImages = await db.records.find({
        labels: ['ImageReference'],
        where: {
            'TextChunk': { $relation: { type: 'ILLUSTRATES', direction: 'in' } }
        }
    })
}
```

## Expected Output

```
=== Cross-Modal Document Retrieval ===

Query: "neural network training improvements"

--- Top Text Chunk (score: 0.847) ---
Section: results | Heading: Experimental Results
"Our experiments show a 23% improvement in training convergence when using the proposed adaptive learning rate..."

  [RELATED] Tables: 1 found
    - "Model Comparison Results" (3 rows, 4 columns)
      Related to chunk via: SUPPORTS

  [RELATED] Images: 2 found
    - "figure_1.png" - Training convergence comparison chart
    - "figure_2.png" - Loss curve over epochs
      Related to chunk via: ILLUSTRATES
```

## Customization

To adapt this tutorial for your own documents:

1. **Replace `data/document.json`** with your document structure
2. **Adjust chunking logic** in `seed.py` based on your document format
3. **Modify relationship types** to match your domain (e.g., `CITES`, `REFERENCES`)
4. **Update the query** in `main.py` to test your specific retrieval needs

## Further Reading

- [RushDB Python SDK Documentation](https://docs.rushdb.com/sdk/python/)
- [RushDB Property Graph Model](https://docs.rushdb.com/concepts/property-graph/)
- [Vector Search in RushDB](https://docs.rushdb.com/features/vector-search/)
- [Semantic Search Guide](https://docs.rushdb.com/features/semantic-search/)

## License

MIT License - See LICENSE file for details.
