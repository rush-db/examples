# RushDB Simple RAG Implementation

A simple RAG (Retrieval Augmented Generation) application using RushDB for document storage and vector search capabilities.

## Features

- **Document Ingestion**: Load markdown documents from local directories or upload files
- **Automatic Chunking**: Split documents into manageable chunks for better vector search
- **Vector Embeddings**: Use sentence transformers to create embeddings for semantic search
- **RushDB Storage**: Store documents and chunks with relationships in RushDB
- **Vector Search**: Search for relevant chunks using cosine similarity
- **FastAPI Interface**: RESTful API for easy integration
- **Auto-Configuration**: Automatic initialization from environment variables

## Setup with UV

This project uses UV for dependency management. Make sure you have UV installed:

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository and navigate to the project
cd packages/python-simple-rag

# Install dependencies
uv sync
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your RushDB API token:
```bash
# Get your API token from https://app.rushdb.com/
RUSHDB_API_TOKEN=your_actual_token_here
```

3. (Optional) Customize other settings in `.env`:
```bash
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
SIMILARITY_THRESHOLD=0.7
```

## Quick Start

1. **Run the application**:
```bash
uv run python run_app.py
```

2. **Or start the API server directly**:
```bash
uv run uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

The application will automatically initialize from your `.env` configuration. The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Install Dependencies

```bash
# Navigate to the project directory
cd /path/to/rushdb/packages/python-simple-rag

# Install dependencies with UV
uv sync
```

## Configuration

You'll need a RushDB API token. You can get one from:
- [RushDB Cloud Dashboard](https://app.rushdb.com) (for cloud instance)
- Your self-hosted RushDB instance

## Usage

The application provides a RESTful API for document ingestion and search. All configuration is handled through environment variables - no manual initialization required.

### API Endpoints

1. **Check API status and configuration**:
```bash
curl http://localhost:8000/
```

2. **Health check**:
```bash
curl http://localhost:8000/health
```

3. **Ingest documents from directory**:
```bash
curl -X POST "http://localhost:8000/ingest/directory" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "docs_path=/path/to/your/markdown/docs"
```

4. **Upload and ingest files**:
```bash
curl -X POST "http://localhost:8000/ingest/files" \
  -F "files=@document1.md" \
  -F "files=@document2.md"
```

5. **Search for relevant chunks**:
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RushDB?",
    "limit": 5
  }'
```

All endpoints return JSON responses. The API automatically initializes from your `.env` configuration on startup.

## How It Works

### Data Structure in RushDB

The application stores documents using the following structure in RushDB:

```python
{
  "label": "Document",
  "data": {
    "title": "document_title",
    "path": "/path/to/document.md",
    "file_hash": "md5_hash_for_change_detection",
    "content_preview": "First 200 characters...",
    "Chunk": [
      {
        "text": "chunk_content",
        "chunk_index": 0,
        "embedding": [0.1, 0.2, 0.3, ...],
        "document_title": "document_title"
      },
      # ... more chunks
    ]
  }
}
```

### Processing Flow

1. **Document Loading**: Markdown files are loaded from the specified directory
2. **Content Processing**: Markdown is converted to plain text
3. **Chunking**: Documents are split into chunks of ~500 words each
4. **Vectorization**: Each chunk is converted to a vector embedding using sentence transformers
5. **Storage**: Documents and chunks are stored in RushDB with the `create_many` method
6. **Search**: Vector similarity search is performed using RushDB's `$vector` operator

### Vector Search

The application uses RushDB's updated vector search capabilities with aggregation:

```python
results = db.records.find({
    "labels": ["Chunk"],
    "aggregate": {
        "text": "$record.text",
        "document_title": "$record.document_title", 
        "chunk_index": "$record.chunk_index",
        "score": {
            "alias": "$record",
            "field": "embedding",
            "fn": "gds.similarity.cosine",
            "query": query_vector
        }
    },
    "orderBy": { "score": "desc" },
    "limit": limit
})
```

## Testing

The project includes test documents in the `test_docs/` directory. To test the system:

1. Start the application: `uv run python run_app.py`
2. Ingest test documents: `POST /ingest/directory` with `docs_path=test_docs`
3. Search for content: `POST /search` with queries like "vector search" or "RushDB features"

## Development

### Code Structure

- `src/rag_engine.py`: Core RAG implementation with document processing and RushDB operations
- `src/api.py`: FastAPI application with REST endpoints  
- `src/config.py`: Configuration management and environment variable handling
- `run_app.py`: Application runner with testing and server startup
- `pyproject.toml`: Project configuration and dependencies

### Key Components

1. **DocumentProcessor**: Handles document loading, chunking, and vectorization
2. **RAGDatabase**: Manages RushDB operations for storage and retrieval  
3. **SimpleRAG**: Main class that orchestrates the RAG workflow
4. **FastAPI App**: RESTful API with automatic configuration from environment

## Customization

- **Embedding Model**: Change the `EMBEDDING_MODEL` in `.env` to use different sentence transformer models
- **Chunk Size**: Adjust `CHUNK_SIZE` for different chunking strategies
- **Search Configuration**: Modify similarity scoring in the search aggregation
- **Document Formats**: Extend DocumentProcessor to support other document formats beyond markdown

## Dependencies

- `fastapi`: Web framework for the API
- `rushdb`: RushDB Python SDK
- `sentence-transformers`: For text embeddings
- `python-markdown`: Markdown processing
- `uvicorn`: ASGI server
- `numpy`: Numerical operations
- `pydantic`: Data validation

## Notes

- The application automatically skips documents that haven't changed (using file hash comparison)
- Vector embeddings are stored as arrays in RushDB and searchable using aggregation with cosine similarity
- The default embedding model (`all-MiniLM-L6-v2`) provides a good balance of performance and quality
- Search results include relevance scoring and document metadata
- Configuration is entirely environment-driven - no manual API initialization required