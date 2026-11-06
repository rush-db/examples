# RushDB Generic RAG API

A generic RAG (Retrieval Augmented Generation) API using RushDB for record vectorization and vector search capabilities.

## Features

- **Generic Record Processing**: Index any text field from any record type in RushDB
- **Vector Embeddings**: Use sentence transformers to create embeddings for semantic search
- **RushDB Integration**: Add embedding properties directly to existing records
- **Vector Search**: Search for relevant records using cosine similarity
- **FastAPI Interface**: RESTful API for easy integration
- **Auto-Configuration**: Automatic initialization from environment variables

## Setup with UV

This project uses UV for dependency management. Make sure you have UV installed:

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository and navigate to the project
cd python-books-rag

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
cd /path/to/project

# Install dependencies with UV
uv sync
```

## Configuration

You'll need a RushDB API token. You can get one from:

- [RushDB Cloud Dashboard](https://app.rushdb.com) (for cloud instance)
- Your self-hosted RushDB instance

## Usage

The application provides a RESTful API for record indexing and search. All configuration is handled through environment variables - no manual initialization required.

### API Endpoints

1. **Check API status and configuration**:

```bash
curl http://localhost:8000/
```

2. **Health check**:

```bash
curl http://localhost:8000/health
```

3. **Index records**:

```bash
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "labels": ["Article"],
    "field": "content",
    "vector_dimension": 384
  }'
```

You can also use more complex search queries for indexing:

```bash
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "labels": ["Article"],
    "where": {"category": "technology"},
    "field": "content",
    "vector_dimension": 384,
    "limit": 500
  }'
```

4. **Search records** (basic search):

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "labels": ["Article"],
    "query": "What is RushDB?",
    "limit": 5
  }'
```

5. **Advanced search with filtering**:

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "labels": ["Article"],
    "query": "What is RushDB?",
    "limit": 5,
    "vector_dimension": 384,
    "min_score": 0.7,
    "offset": 0
  }'
```

All endpoints return JSON responses. The API automatically initializes from your `.env` configuration on startup.

## How It Works

### Data Structure in RushDB

The application adds embedding properties directly to existing records:

```
Record (e.g., Article)
{
  "title": "Sample Article",
  "content": "This is the article content...",
  "embedding": [0.1, 0.2, 0.3, ...],
  // ... other properties
}
```

### Processing Flow

1. **Record Selection**: Records are retrieved from RushDB using the provided search query
2. **Content Extraction**: Text from the specified field is extracted
3. **Vectorization**: The content is converted to a vector embedding using sentence transformers
4. **Storage**: The embedding is added as a property to the existing record
5. **Search**: Vector similarity search is performed directly on the records

### Vector Search

The application uses RushDB's powerful vector search capabilities with the following features:

1. **Label-based filtering**: Target specific record types
2. **Vector similarity**: Calculate cosine similarity between query and stored embeddings
3. **Minimum score threshold**: Filter out low-relevance results (optional)
4. **Sorting**: Order results by similarity score
5. **Pagination**: Control the number of results returned

Search parameters:

- `labels`: Labels of records to search
- `query`: Text query to find similar content
- `limit`: Maximum number of results to return
- `min_score`: Minimum similarity threshold (0-1)
- `offset`: Number of results to skip (for pagination)
- `vector_dimension`: Control embedding size/quality tradeoff

```python
# Basic vector search query
results = db.records.find({
    "labels": ["Article"],
    "aggregate": {
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

## Development

### Code Structure

- `src/rag_engine.py`: Core RAG implementation with text processing and RushDB operations
- `src/api.py`: FastAPI application with REST endpoints
- `src/config.py`: Configuration management and environment variable handling
- `run_app.py`: Application runner with testing and server startup
- `pyproject.toml`: Project configuration and dependencies

### Key Components

1. **TextProcessor**: Handles text vectorization
2. **RagService**: Manages RushDB operations for indexing and search
3. **FastAPI App**: RESTful API with automatic configuration from environment

## Customization

- **Embedding Model**: Change the `EMBEDDING_MODEL` in `.env` to use different sentence transformer models
- **Vector Dimensions**: Use the `vector_dimension` parameter in API requests to specify the embedding dimension:
  - 384: Uses the all-MiniLM-L6-v2 model (faster, smaller embeddings)
  - 768: Uses the all-mpnet-base-v2 model (slower, more accurate embeddings)
- **Search Configuration**: Modify similarity scoring in the search aggregation
- **Record Selection**: Specify different record labels and fields to process

## Dependencies

- `fastapi`: Web framework for the API
- `rushdb`: RushDB Python SDK
- `sentence-transformers`: For text embeddings
- `uvicorn`: ASGI server
- `pydantic`: Data validation
