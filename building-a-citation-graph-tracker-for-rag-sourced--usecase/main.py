#!/usr/bin/env python3
"""
Citation Graph Tracker for RAG-Sourced Answers

This prototype demonstrates how to build a complete citation tracking system
for RAG applications using RushDB's graph + vector combination.

Key capabilities:
- Semantic search across document chunks
- Multi-hop graph traversal for provenance
- Auditable answer generation with full source lineage

Run: python main.py
Prerequisite: python seed.py (run once to populate the database)
"""

import os
import sys
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment
load_dotenv()

# Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.5  # Minimum similarity score for retrieval
MAX_RETRIEVALS = 5          # Maximum chunks to retrieve per query


class CitationGraphTracker:
    """
    Citation graph tracker that manages the RAG retrieval graph.
    
    Tracks: DOCUMENTS -> CHUNKS -> RETRIEVAL_EVENTS -> LLM_RESPONSES
    Enables full provenance tracing from answers back to sources.
    """
    
    def __init__(self, db: RushDB, embedding_model):
        self.db = db
        self.model = embedding_model
        self.vector_index_id: Optional[str] = None
        self._discover_vector_index()
    
    def _discover_vector_index(self):
        """Find the CHUNK.body vector index."""
        indexes = self.db.ai.indexes.find()
        for idx in indexes.data:
            if idx["label"] == "CHUNK" and idx["propertyName"] == "body":
                self.vector_index_id = idx["__id"]
                break
    
    def semantic_search(
        self,
        query: str,
        limit: int = MAX_RETRIEVALS,
        min_score: float = SIMILARITY_THRESHOLD
    ) -> list[dict]:
        """
        Perform semantic search to find relevant document chunks.
        
        Args:
            query: Natural language query
            limit: Maximum number of results
            min_score: Minimum similarity threshold
        
        Returns:
            List of retrieved chunks with scores
        """
        # Generate query embedding
        query_vector = self.model.encode(query).tolist()
        
        # Search using external vector (pre-computed query embedding)
        results = self.db.ai.search({
            "propertyName": "body",
            "queryVector": query_vector,
            "labels": ["CHUNK"],
            "limit": limit
        })
        
        # Filter and format results
        retrieved_chunks = []
        for record in results.data:
            if record.score and record.score >= min_score:
                # Get parent document via graph traversal
                document = self._get_chunk_document(record.id)
                
                retrieved_chunks.append({
                    "chunk_id": record.id,
                    "chunk_body": record.get("body", ""),
                    "position": record.get("position", 0),
                    "score": record.score,
                    "document": document
                })
        
        return retrieved_chunks
    
    def _get_chunk_document(self, chunk_id: str) -> Optional[dict]:
        """
        Traverse graph to find the parent document of a chunk.
        
        Uses RushDB's relationship query to find DOCUMENT linked via PART_OF.
        """
        # Find document through PART_OF relationship
        documents = self.db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "CHUNK": {
                    "$relation": {"type": "PART_OF", "direction": "in"},
                    "$id": {"$in": [chunk_id]}
                }
            }
        })
        
        if documents.data:
            doc = documents.data[0]
            return {
                "document_id": doc.id,
                "title": doc.get("title", "Unknown"),
                "author": doc.get("author", "Unknown"),
                "published_date": doc.get("published_date", ""),
                "category": doc.get("category", ""),
                "source_url": doc.get("source_url", "")
            }
        return None
    
    def create_retrieval_event(
        self,
        query: str,
        retrieved_chunks: list[dict],
        tx=None
    ) -> dict:
        """
        Record a retrieval event - captures the query and retrieved chunks.
        
        Args:
            query: The original user query
            retrieved_chunks: List of chunks from semantic search
            tx: Optional transaction for atomic operations
        
        Returns:
            Created RETRIEVAL_EVENT record
        """
        # Create retrieval event record
        retrieval_event = self.db.records.create(
            label="RETRIEVAL_EVENT",
            data={
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "chunk_count": len(retrieved_chunks),
                "avg_score": sum(c["score"] for c in retrieved_chunks) / len(retrieved_chunks) if retrieved_chunks else 0
            },
            transaction=tx
        )
        
        # Attach retrieved chunks to the event
        for chunk_info in retrieved_chunks:
            # Find the actual chunk record
            chunks = self.db.records.find_by_id(chunk_info["chunk_id"])
            if chunks:
                chunk_record = chunks if hasattr(chunks, 'id') else chunks[0]
                self.db.records.attach(
                    source=chunk_record,
                    target=retrieval_event,
                    options={"type": "RETRIEVED_FOR", "direction": "in"},
                    transaction=tx
                )
        
        return retrieval_event
    
    def create_llm_response(
        self,
        query: str,
        response_text: str,
        retrieved_chunks: list[dict],
        tx=None
    ) -> dict:
        """
        Create an LLM response record with citations to retrieved chunks.
        
        Args:
            query: The original user query
            response_text: The generated response text
            retrieved_chunks: List of retrieved chunks
            tx: Optional transaction
        
        Returns:
            Dict with LLM_RESPONSE and associated CITATION records
        """
        # Create retrieval event first
        retrieval_event = self.create_retrieval_event(query, retrieved_chunks, tx)
        
        # Create LLM response record
        llm_response = self.db.records.create(
            label="LLM_RESPONSE",
            data={
                "query": query,
                "response_text": response_text,
                "timestamp": datetime.utcnow().isoformat(),
                "model": "gpt-4-turbo (simulated)",
                "citation_count": len(retrieved_chunks)
            },
            transaction=tx
        )
        
        # Create citations linking response to retrieval event
        citations = []
        for i, chunk_info in enumerate(retrieved_chunks):
            citation = self.db.records.create(
                label="CITATION",
                data={
                    "position": i + 1,
                    "chunk_id": chunk_info["chunk_id"],
                    "relevance_score": chunk_info["score"],
                    "cited_text": chunk_info["chunk_body"][:100] + "..."
                },
                transaction=tx
            )
            
            # Link citation to response and retrieval event
            self.db.records.attach(
                source=citation,
                target=llm_response,
                options={"type": "BELONGS_TO", "direction": "out"},
                transaction=tx
            )
            self.db.records.attach(
                source=citation,
                target=retrieval_event,
                options={"type": "REFERENCES", "direction": "out"},
                transaction=tx
            )
            
            citations.append(citation)
        
        return {
            "response": llm_response,
            "retrieval_event": retrieval_event,
            "citations": citations
        }
    
    def trace_provenance(self, response_id: str) -> dict:
        """
        Trace the full provenance of an LLM response.
        
        Follows the graph:
        LLM_RESPONSE -> CITATION -> RETRIEVAL_EVENT -> CHUNK -> DOCUMENT
        
        Args:
            response_id: ID of the LLM_RESPONSE to trace
        
        Returns:
            Complete provenance information
        """
        # Get the response
        responses = self.db.records.find_by_id(response_id)
        if not responses:
            return {"error": "Response not found"}
        
        response = responses if hasattr(responses, 'id') else responses[0]
        
        # Find citations
        citations = self.db.records.find({
            "labels": ["CITATION"],
            "where": {
                "LLM_RESPONSE": {
                    "$relation": {"type": "BELONGS_TO", "direction": "in"},
                    "$id": {"$in": [response_id]}
                }
            }
        })
        
        provenance = {
            "response": {
                "id": response.id,
                "query": response.get("query", ""),
                "text": response.get("response_text", ""),
                "timestamp": response.get("timestamp", ""),
                "model": response.get("model", "")
            },
            "citations": []
        }
        
        # Trace each citation
        for citation in citations.data:
            citation_provenance = {
                "position": citation.get("position", 0),
                "relevance_score": citation.get("relevance_score", 0),
                "cited_text": citation.get("cited_text", ""),
                "chunk": None,
                "document": None
            }
            
            # Get the chunk this citation references
            chunk_id = citation.get("chunk_id")
            if chunk_id:
                chunks = self.db.records.find_by_id(chunk_id)
                if chunks:
                    chunk = chunks if hasattr(chunks, 'id') else chunks[0]
                    citation_provenance["chunk"] = {
                        "id": chunk.id,
                        "body": chunk.get("body", ""),
                        "position": chunk.get("position", 0)
                    }
                    
                    # Get parent document
                    citation_provenance["document"] = self._get_chunk_document(chunk.id)
            
            provenance["citations"].append(citation_provenance)
        
        return provenance
    
    def run_rag_query(self, query: str) -> dict:
        """
        Run a complete RAG query with citation tracking.
        
        1. Semantic search for relevant chunks
        2. Create retrieval event
        3. Generate (simulated) LLM response
        4. Create citations
        5. Return results with provenance
        
        Args:
            query: User's natural language question
        
        Returns:
            Complete RAG response with citations and provenance
        """
        print(f"\n📚 Query: \"{query}\"")
        print("-" * 65)
        
        # Step 1: Semantic search
        print("\n🔍 Semantic Search Results:")
        retrieved_chunks = self.semantic_search(query)
        
        for i, chunk in enumerate(retrieved_chunks[:MAX_RETRIEVALS], 1):
            body_preview = chunk["chunk_body"][:60] + "..."
            print(f"  [{i}] \"{body_preview}\" (score: {chunk['score']:.3f})")
        
        if not retrieved_chunks:
            print("  No relevant chunks found.")
            return {"error": "No relevant content found"}
        
        # Step 2: Simulate LLM response (in production, this would call an LLM API)
        print("\n🤖 Simulated LLM Response:")
        response_text = self._simulate_llm_response(query, retrieved_chunks)
        print("-" * 65)
        print(response_text)
        
        # Step 3: Store in graph with full citation tracking
        print(f"\n📎 Creating citations for {len(retrieved_chunks)} sources...")
        
        with self.db.transactions.begin() as tx:
            result = self.create_llm_response(
                query=query,
                response_text=response_text,
                retrieved_chunks=retrieved_chunks,
                tx=tx
            )
            # Context manager handles commit automatically
        
        print("   ✅ Response and citations stored in graph")
        
        # Step 4: Trace and display provenance
        print("\n🔬 PROVENANCE TRACE")
        print("-" * 65)
        provenance = self.trace_provenance(result["response"].id)
        
        self._display_provenance(provenance)
        
        return {
            "response": result["response"],
            "retrieval_event": result["retrieval_event"],
            "citations": result["citations"],
            "provenance": provenance
        }
    
    def _simulate_llm_response(self, query: str, chunks: list[dict]) -> str:
        """
        Simulate an LLM response based on retrieved chunks.
        
        In production, this would call an LLM API with the retrieved
        chunks as context. Here we create a template response that
        demonstrates citation awareness.
        """
        # Extract key information from top chunks
        top_chunk = chunks[0]["chunk_body"] if chunks else "No relevant information found."
        
        # Create a response that references the content
        response_parts = []
        
        if len(chunks) >= 1:
            response_parts.append(
                f"Based on the retrieved information, {chunks[0]['chunk_body'][:150]}..."
            )
        
        if len(chunks) >= 2:
            response_parts.append(
                f"Additionally, {chunks[1]['chunk_body'][:150]}..."
            )
        
        if len(chunks) >= 3:
            response_parts.append(
                f"For more details, {chunks[2]['chunk_body'][:100]}..."
            )
        
        if not response_parts:
            return "I couldn't find relevant information to answer your question."
        
        return " ".join(response_parts) + "\n\n[This response was generated with citation tracking enabled.]"
    
    def _display_provenance(self, provenance: dict):
        """Display provenance information in a readable format."""
        if "error" in provenance:
            print(f"   Error: {provenance['error']}")
            return
        
        for citation in provenance.get("citations", []):
            pos = citation.get("position", "?")
            score = citation.get("relevance_score", 0)
            chunk = citation.get("chunk", {})
            doc = citation.get("document", {})
            
            print(f"\nCitation #{pos} → CHUNK (ID: {chunk.get('id', 'unknown')[:12]}...)")
            print(f"  Content: \"{chunk.get('body', '')[:60]}...\"")
            print(f"  Score: {score:.3f}")
            
            if doc:
                print(f"  Parent Document: \"{doc.get('title', 'Unknown')}\"")
                print(f"    - Author: {doc.get('author', 'Unknown')}")
                print(f"    - Published: {doc.get('published_date', 'Unknown')}")
            else:
                print("  ⚠️  Document not found (orphan chunk)")
        
        total_docs = len(set(
            c.get("document", {}).get("document_id", "") 
            for c in provenance.get("citations", [])
        ))
        
        print(f"\n✅ Answer fully auditable: {total_docs} document(s) traced")


def check_database_ready():
    """Verify the database is seeded and ready."""
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("❌ Error: RUSHDB_API_TOKEN not found")
        print("   Please copy .env.example to .env and add your API key")
        return False
    
    db = RushDB(api_token)
    
    # Check for documents
    docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if not docs.data:
        print("❌ Error: No documents found in database")
        print("   Please run `python seed.py` first to populate the database")
        return False
    
    # Check for chunks
    chunks = db.records.find({"labels": ["CHUNK"], "limit": 1})
    if not chunks.data:
        print("❌ Error: No chunks found in database")
        print("   Please run `python seed.py` first")
        return False
    
    # Check for vector index
    indexes = db.ai.indexes.find()
    has_index = any(
        idx["label"] == "CHUNK" and idx["propertyName"] == "body"
        for idx in indexes.data
    )
    if not has_index:
        print("❌ Error: No vector index found for CHUNK.body")
        print("   Please run `python seed.py` first")
        return False
    
    print(f"✅ Database ready: {len(docs.data)} documents, {len(chunks.data)} chunks")
    return True


def main():
    """Main entry point for the citation graph tracker."""
    
    print("\n" + "=" * 70)
    print("   CITATION GRAPH TRACKER FOR RAG-SOURCED ANSWERS")
    print("   Powered by RushDB: Graph + Vector Search")
    print("=" * 70)
    
    # Check prerequisites
    if not check_database_ready():
        sys.exit(1)
    
    # Initialize
    api_token = os.getenv("RUSHDB_API_TOKEN")
    db = RushDB(api_token)
    
    print(f"\n📦 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    tracker = CitationGraphTracker(db, model)
    
    # Example queries demonstrating different aspects of citation tracking
    queries = [
        "How does vector search work in databases?",
        "What are the main ANN algorithms and their trade-offs?",
        "How can we attribute AI responses to their sources?"
    ]
    
    print("\n" + "=" * 70)
    print("   RUNNING RAG QUERIES WITH CITATION TRACKING")
    print("=" * 70)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'─' * 70}")
        print(f"   QUERY {i} of {len(queries)}")
        print(f"{'─' * 70}")
        
        try:
            result = tracker.run_rag_query(query)
            
            if "error" in result:
                print(f"\n⚠️  {result['error']}")
            else:
                print(f"\n✅ Query {i} complete - Response ID: {result['response'].id}")
        
        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            raise
    
    # Demonstrate provenance tracing on the last response
    if result and "response" in result:
        print("\n" + "=" * 70)
        print("   DEMONSTRATING PROVENANCE TRACE (POST-HOC ANALYSIS)")
        print("=" * 70)
        
        print(f"\n📋 Re-tracing provenance for response: {result['response'].id}")
        provenance = tracker.trace_provenance(result['response'].id)
        
        print(f"\n📊 Provenance Summary:")
        print(f"   • Query: {provenance['response']['query']}")
        print(f"   • Timestamp: {provenance['response']['timestamp']}")
        print(f"   • Citations: {len(provenance['citations'])}")
        
        unique_docs = set(
            c.get('document', {}).get('document_id', '')
            for c in provenance['citations']
            if c.get('document')
        )
        print(f"   • Unique source documents: {len(unique_docs)}")
    
    print("\n" + "=" * 70)
    print("   DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("""
The citation graph tracker successfully demonstrates:

✅ Graph + Vector Integration
   Documents → Chunks → Retrieval Events → LLM Responses

✅ Semantic Search
   Vector embeddings enable similarity-based retrieval

✅ Full Provenance
   Any response can be traced back to its source documents

✅ Citation Tracking
   Each response links to the chunks that informed it

This pattern enables compliance auditing, debugging, and trust.
""")


if __name__ == "__main__":
    main()
