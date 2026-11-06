from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Handle both relative and absolute imports
try:
    from .rag_engine import RagService
    from .config import get_config
except ImportError:
    # If relative import fails, try absolute import
    sys.path.insert(0, str(Path(__file__).parent))
    from rag_engine import RagService
    from config import get_config

app = FastAPI(
    title="RushDB Generic RAG API",
    description="A generic RAG implementation using RushDB for record chunking and vector search",
    version="0.2.0"
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
rag_instance: Optional[RagService] = None
initialization_error: Optional[str] = None

def initialize_rag_from_config():
    """Initialize RAG instance from environment configuration."""
    global rag_instance, initialization_error

    try:
        print("Initializing RAG from environment configuration...")
        config = get_config()

        if not config['api_key']:
            initialization_error = "RushDB API token not found in environment variables or .env file"
            return

        rag_instance = RagService(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model_name=config['embedding_model'],
        )

        initialization_error = None
    except Exception as e:
        print(f"Error initializing RAG: {e}")
        initialization_error = f"Failed to initialize RAG: {str(e)}"
        rag_instance = None


# Remove all Pydantic models and use dictionaries instead


@app.post("/index")
async def index_records(request: Request):
    """Index records with the specified labels and field."""
    if not rag_instance:
        error_msg = "RAG system not initialized."
        if initialization_error:
            error_msg += f" Error: {initialization_error}"
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        # Parse request body as JSON
        index_request = await request.json()

        # Validate required field
        if "field" not in index_request:
            raise HTTPException(status_code=400, detail="Missing required field: field")

        # Extract field and remove it from the request to create search_query
        field = index_request.pop("field")

        # Extract vector_dimension if present and remove it from search_query
        vector_dimension = index_request.pop("vector_dimension", None)

        # If vector_dimension is specified, update the embedding model accordingly
        if vector_dimension:
            rag_instance.set_model_by_dimension(vector_dimension)

        # Use remaining request as search_query
        search_query = index_request

        result = rag_instance.index_records(
            search_query=search_query,
            field=field
        )

        return {
            "message": f"Indexed records with search query {search_query}",
            "processed_count": result["processed"],
            "error_count": result["errors"],
            "skipped_count": result["skipped"],
            "details": result["message"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index records: {str(e)}")


@app.post("/search")
async def search_chunks(request: Request):
    """Search for relevant chunks."""
    if not rag_instance:
        error_msg = "RAG system not initialized."
        if initialization_error:
            error_msg += f" Error: {initialization_error}"
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        search_query = await request.json()

        if "query" not in search_query:
            raise HTTPException(status_code=400, detail="Missing required field: query")

        # Set defaults if not provided
        search_query.setdefault("vector_dimension", 384)
        search_query.setdefault("limit", 5)

        if "vector_dimension" in search_query and search_query["vector_dimension"]:
            rag_instance.set_model_by_dimension(search_query["vector_dimension"])

        results = rag_instance.search(
            search_query["query"],
            search_query
        )

        return results
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Initialize RAG on module import
initialize_rag_from_config()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
