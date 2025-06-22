from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
import tempfile
from pathlib import Path

# Handle both relative and absolute imports
try:
    from .rag_engine import SimpleRAG
    from .config import get_config
except ImportError:
    # If relative import fails, try absolute import
    sys.path.insert(0, str(Path(__file__).parent))
    from rag_engine import SimpleRAG
    from config import get_config

app = FastAPI(
    title="RushDB Simple RAG API",
    description="A simple RAG implementation using RushDB for document storage and vector search",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG instance - initialize automatically from environment
rag_instance: Optional[SimpleRAG] = None
initialization_error: Optional[str] = None

def initialize_rag_from_config():
    """Initialize RAG instance from environment configuration."""
    global rag_instance, initialization_error

    try:
        config = get_config()

        if not config['api_key']:
            initialization_error = "RushDB API token not found in environment variables or .env file"
            return

        rag_instance = SimpleRAG(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model_name=config['embedding_model']
        )
        initialization_error = None
    except Exception as e:
        initialization_error = f"Failed to initialize RAG: {str(e)}"
        rag_instance = None

# Initialize on startup
initialize_rag_from_config()


class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5


class SearchResult(BaseModel):
    text: str
    document_title: str
    chunk_index: int
    score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int


@app.post("/ingest/directory")
async def ingest_directory(docs_path: str = Form(...)):
    """Ingest documents from a local directory."""
    if not rag_instance:
        error_msg = "RAG system not initialized."
        if initialization_error:
            error_msg += f" Error: {initialization_error}"
        raise HTTPException(status_code=400, detail=error_msg)

    if not os.path.exists(docs_path):
        raise HTTPException(status_code=404, detail=f"Directory not found: {docs_path}")

    try:
        rag_instance.ingest_documents(docs_path)
        return {"message": f"Documents from {docs_path} ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest documents: {str(e)}")


@app.post("/ingest/files")
async def ingest_files(files: List[UploadFile] = File(...)):
    """Ingest uploaded markdown files."""
    if not rag_instance:
        error_msg = "RAG system not initialized."
        if initialization_error:
            error_msg += f" Error: {initialization_error}"
        raise HTTPException(status_code=400, detail=error_msg)

    # Create temporary directory for uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        for file in files:
            if not file.filename.endswith('.md'):
                continue

            file_path = Path(temp_dir) / file.filename
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)

        try:
            rag_instance.ingest_documents(temp_dir)
            return {"message": f"Uploaded {len(files)} files ingested successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to ingest files: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_documents(search_query: SearchQuery):
    """Search for relevant document chunks."""
    if not rag_instance:
        error_msg = "RAG system not initialized."
        if initialization_error:
            error_msg += f" Error: {initialization_error}"
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        results = rag_instance.search(search_query.query, search_query.limit)

        search_results = [
            SearchResult(
                text=result["text"],
                document_title=result["document_title"],
                chunk_index=result["chunk_index"],
                score=result["score"]
            )
            for result in results
        ]

        return SearchResponse(
            results=search_results,
            query=search_query.query,
            total_results=len(search_results)
        )
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "rag_initialized": rag_instance is not None,
        "message": "RushDB Simple RAG API"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RushDB Simple RAG API",
        "version": "0.1.0",
        "description": "A simple RAG implementation using RushDB for document storage and vector search",
        "rag_initialized": rag_instance is not None,
        "initialization_error": initialization_error if initialization_error else None,
        "endpoints": {
            "ingest_directory": "POST /ingest/directory - Ingest documents from directory",
            "ingest_files": "POST /ingest/files - Upload and ingest markdown files",
            "search": "POST /search - Search for relevant document chunks",
            "health": "GET /health - Health check"
        },
        "configuration_help": {
            "setup": "Create .env file from .env.example and set RUSHDB_API_TOKEN",
            "required_env_vars": ["RUSHDB_API_TOKEN"],
            "optional_env_vars": ["RUSHDB_BASE_URL", "EMBEDDING_MODEL", "CHUNK_SIZE", "SIMILARITY_THRESHOLD"]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
