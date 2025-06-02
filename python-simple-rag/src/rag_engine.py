import os
import glob
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import markdown
from rushdb import RushDB


class DocumentProcessor:
    """Handles document loading, chunking, and vectorization."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", chunk_size: int = 500):
        self.model = SentenceTransformer(model_name)
        self.chunk_size = chunk_size

    def load_documents(self, docs_path: str) -> List[Dict[str, Any]]:
        """Load markdown documents from a directory."""
        documents = []
        doc_files = glob.glob(os.path.join(docs_path, "**/*.md"), recursive=True)

        for file_path in doc_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Convert markdown to plain text for better processing
            html = markdown.markdown(content)
            # Simple HTML tag removal (for basic cases)
            import re
            text = re.sub('<[^<]+?>', '', html)

            documents.append({
                "title": Path(file_path).stem,
                "path": file_path,
                "content": text.strip(),
                "file_hash": self._get_file_hash(file_path)
            })

        return documents

    def _get_file_hash(self, file_path: str) -> str:
        """Generate MD5 hash of file for change detection."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for better vector search."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())

        return chunks

    def vectorize_text(self, text: str) -> List[float]:
        """Convert text to vector embedding."""
        embedding = self.model.encode(text)
        return embedding.tolist()


class RAGDatabase:
    """Handles RushDB operations for document storage and retrieval."""

    def __init__(self, api_token: str, base_url: str = None):
        if base_url:
            self.db = RushDB(api_token, base_url=base_url)
        else:
            self.db = RushDB(api_token)

    def store_document(self, document: Dict[str, Any], chunks_data: List[Dict[str, Any]]):
        """Store document with its chunks in RushDB."""
        doc_data = {
            "title": document["title"],
            "path": document["path"],
            "file_hash": document["file_hash"],
            "content_preview": document["content"][:200] + "..." if len(document["content"]) > 200 else document["content"],
            "Chunk": chunks_data
        }

        return self.db.records.create_many(
            label="Document",
            data=doc_data,
            options={
              "returnResult": True,
              "suggestTypes": True,
              "castNumberArraysToVectors": True
            }
        )

    def search_similar_chunks(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        try:
            results = self.db.records.find({
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

            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def check_document_exists(self, file_hash: str) -> bool:
        """Check if document with given hash already exists."""
        try:
            results = self.db.records.find({
                "labels": ["Document"],
                "where": {
                    "file_hash": file_hash
                },
                "limit": 1
            })
            return len(results.get("data", [])) > 0
        except Exception:
            return False


class SimpleRAG:
    """Main RAG implementation class."""

    def __init__(self, api_token: str, base_url: str = None, model_name: str = "all-MiniLM-L6-v2"):
        self.processor = DocumentProcessor(model_name=model_name)
        self.database = RAGDatabase(api_token, base_url)

    def ingest_documents(self, docs_path: str):
        """Load and process documents from directory."""
        print(f"Loading documents from {docs_path}...")
        documents = self.processor.load_documents(docs_path)

        processed_count = 0
        for document in documents:
            # Skip if document already exists and hasn't changed
            if self.database.check_document_exists(document["file_hash"]):
                print(f"Skipping {document['title']} (already exists)")
                continue

            print(f"Processing {document['title']}...")

            # Chunk the document
            chunks = self.processor.chunk_text(document["content"])

            # Process each chunk
            chunks_data = []
            for i, chunk_text in enumerate(chunks):
                embedding = self.processor.vectorize_text(chunk_text)
                chunk_data = {
                    "text": chunk_text,
                    "chunk_index": i,
                    "embedding": embedding,
                    "document_title": document["title"]
                }
                chunks_data.append(chunk_data)

            # Store in RushDB
            try:
                self.database.store_document(document, chunks_data)
                processed_count += 1
                print(f"Stored {document['title']} with {len(chunks_data)} chunks")
            except Exception as e:
                print(f"Error storing {document['title']}: {e}")

        print(f"Ingestion complete. Processed {processed_count} documents.")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant chunks based on query."""
        # Vectorize the query
        query_vector = self.processor.vectorize_text(query)

        # Search similar chunks
        results = self.database.search_similar_chunks(query_vector, limit)



        # Format results
        formatted_results = []
        try:
            for result in results:
                formatted_results.append({
                    "text": result.data.get("text", ""),
                    "document_title": result.data.get("document_title", ""),
                    "chunk_index": result.data.get("chunk_index", 0),
                    "score": result.data.get("score", 0)
                })
        except Exception as e:
            print(f"Error accessing data: {e}")
            return formatted_results
        return formatted_results
