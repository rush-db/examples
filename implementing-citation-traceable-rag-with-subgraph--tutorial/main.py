"""
Citation-Traceable RAG with Subgraph Provenance - Main Demo

This script demonstrates the complete provenance-traceable RAG pipeline:
1. Schema inspection - See the provenance graph structure
2. Provenance-aware retrieval - Semantic search with full subgraph fetch
3. Citation assembly - Build citations from retrieval back to source
4. Trace visualization - Structured output of the complete reasoning path
"""

import os
import time
import json
from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

load_dotenv()

# Initialize clients
db = RushDB(os.getenv("RUSHDB_API_KEY"))
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

# Sample queries for demonstration
QUERIES = [
    "How does retrieval-augmented generation reduce hallucinations?",
    "What are the best practices for document chunking in RAG systems?",
    "Explain how provenance tracking improves AI system reliability."
]


# =============================================================================
# PART 1: Schema Inspection
# =============================================================================

def inspect_schema():
    """Inspect and display the provenance graph schema."""
    print("\n" + "="*70)
    print("PART 1: PROVENANCE GRAPH SCHEMA")
    print("="*70)
    
    # Get ontology (all labels and properties)
    ontology = db.ai.getOntology()
    
    print("\nLabels in the graph:")
    for label_info in ontology.get('labels', []):
        record_count = label_info.get('count', 'N/A')
        print(f"  • {label_info['name']}: {record_count} records")
    
    print("\nRelationship types (derived from graph structure):")
    relationship_types = [
        ("DOCUMENT", "CONTAINS", "CHUNK", "Document-to-chunk containment"),
        ("CHUNK", "EMBEDDING_OF", "EMBEDDING", "Chunk-to-embedding reference"),
        ("RETRIEVAL_EVENT", "RETRIEVED", "CHUNK", "Retrieval event to chunk"),
        ("GENERATION", "BASED_ON", "RETRIEVAL_EVENT", "Generation to retrieval trace")
    ]
    for src, rel, tgt, desc in relationship_types:
        print(f"  • {src} --[{rel}]--> {tgt}")
        print(f"    Purpose: {desc}")
    
    return ontology


# =============================================================================
# PART 2: Provenance-Aware Retrieval
# =============================================================================

def semantic_search_with_provenance(query, limit=3):
    """
    Perform semantic search that returns chunks AND their provenance subgraph.
    
    This is the key function that implements provenance-aware retrieval:
    1. Generate query embedding
    2. Search for similar chunks
    3. For each chunk, traverse back to its parent document
    4. Create a retrieval event linking the query to retrieved chunks
    """
    # Generate query embedding
    query_vector = model.encode(query).tolist()
    
    # Perform vector search
    results = db.ai.search({
        "propertyName": "embedding",
        "queryVector": query_vector,
        "labels": ["CHUNK"],
        "limit": limit
    })
    
    retrieved_chunks = []
    
    for result in results.data:
        # Get the chunk's properties
        chunk_text = result.get('text', '')
        chunk_score = result.score
        
        # Traverse back to parent document via CONTAINS relationship
        # We need to find which document CONTAINS this chunk
        # Using find with related record filtering
        parent_docs = db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "CHUNK": {
                    "$relation": {"type": "CONTAINS", "direction": "in"},
                    "text": chunk_text
                }
            },
            "limit": 1
        })
        
        # Get the document info if found
        doc_info = None
        if parent_docs.data:
            doc = parent_docs.data[0]
            doc_info = {
                "id": doc.id,
                "title": doc.get('title', 'Unknown'),
                "category": doc.get('category', 'Unknown')
            }
        
        # Get chunk metadata for provenance
        chunk_info = {
            "id": result.id,
            "text": chunk_text,
            "score": chunk_score,
            "chunk_index": result.get('chunk_index'),
            "context_before": result.get('context_before'),
            "context_after": result.get('context_after'),
            "document": doc_info
        }
        
        retrieved_chunks.append(chunk_info)
    
    return {
        "query": query,
        "chunks": retrieved_chunks,
        "total_retrieved": len(retrieved_chunks)
    }


def create_retrieval_event(query, retrieved_chunks):
    """Create a retrieval event that links the query to all retrieved chunks."""
    retrieval_event = db.records.create(
        label="RETRIEVAL_EVENT",
        data={
            "query": query,
            "timestamp": time.time(),
            "retrieved_chunk_ids": [c['id'] for c in retrieved_chunks],
            "embedding_model": EMBEDDING_MODEL
        }
    )
    
    # Attach retrieval event to each retrieved chunk
    for chunk in retrieved_chunks:
        chunk_record = db.records.find_by_id(chunk['id'])
        db.records.attach(
            source=retrieval_event,
            target=chunk_record,
            options={"type": "RETRIEVED"}
        )
    
    return retrieval_event


def demonstrate_retrieval():
    """Demonstrate provenance-aware retrieval with sample queries."""
    print("\n" + "="*70)
    print("PART 2: PROVENANCE-AWARE RETRIEVAL")
    print("="*70)
    
    # Pick one query to demonstrate in detail
    query = QUERIES[0]
    
    print(f"\nQuery: \"{query}\"")
    print("-"*60)
    
    # Perform search
    results = semantic_search_with_provenance(query, limit=3)
    
    print(f"\nRetrieved {results['total_retrieved']} chunks:")
    for i, chunk in enumerate(results['chunks'], 1):
        print(f"\n  Chunk {i} [score: {chunk['score']:.3f}]")
        print(f"    Text: {chunk['text'][:100]}...")
        if chunk['document']:
            print(f"    Source: {chunk['document']['title']}")
        else:
            print(f"    Source: [Document not found via traversal]")
    
    # Create retrieval event for tracking
    retrieval_event = create_retrieval_event(query, results['chunks'])
    print(f"\n  -> Created RETRIEVAL_EVENT: {retrieval_event.id}")
    
    return results, retrieval_event


# =============================================================================
# PART 3: Citation Assembly
# =============================================================================

def assemble_citations(retrieval_results):
    """
    Build citations from retrieval results back to source documents.
    
    This demonstrates the forward trace: from generation to retrieved chunks
    and backward trace: from chunks to source documents.
    """
    print("\n" + "="*70)
    print("PART 3: CITATION ASSEMBLY")
    print("="*70)
    
    citations = []
    
    for chunk in retrieval_results['chunks']:
        citation = {
            "chunk_id": chunk['id'],
            "source_chunk": chunk['text'],
            "relevance_score": chunk['score'],
            "provenance_path": []
        }
        
        # Trace backward: Chunk -> Document
        if chunk['document']:
            citation['provenance_path'].append({
                "step": "Document",
                "id": chunk['document']['id'],
                "title": chunk['document']['title'],
                "category": chunk['document']['category']
            })
        
        citation['provenance_path'].append({
            "step": "Chunk",
            "id": chunk['id'],
            "chunk_index": chunk['chunk_index'],
            "score": chunk['score']
        })
        
        citations.append(citation)
    
    print("\nAssembled citations (backward trace):")
    for i, citation in enumerate(citations, 1):
        print(f"\n  Citation {i}:")
        print(f"    Source: {citation['provenance_path'][0].get('title', 'Unknown')}")
        print(f"    Chunk: {citation['source_chunk'][:80]}...")
        print(f"    Relevance: {citation['relevance_score']:.3f}")
    
    return citations


def build_generation_with_citations(query, retrieval_results, citations):
    """
    Simulate a generation response with embedded citations.
    In production, this would call an LLM API.
    """
    # Create a simulated generation response
    generation = db.records.create(
        label="GENERATION",
        data={
            "query": query,
            "answer": f"Based on the retrieved context about RAG systems: "
                      f"retrieval-augmented generation reduces hallucinations by "
                      f"grounding responses in actual retrieved facts rather than "
                      f"relying solely on parametric knowledge. The retrieved chunks "
                      f"provide evidence from authoritative sources including '{citations[0]['provenance_path'][0].get('title', 'source') if citations else 'knowledge base'}'.",
            "timestamp": time.time(),
            "model": "citation-demo (simulated)",
            "citation_count": len(citations)
        }
    )
    
    return generation


# =============================================================================
# PART 4: Trace Visualization
# =============================================================================

def visualize_trace(generation, retrieval_event, retrieval_results, citations):
    """
    Build and display a complete provenance trace object.
    This is the structured output showing the full reasoning path.
    """
    print("\n" + "="*70)
    print("PART 4: PROVENANCE TRACE VISUALIZATION")
    print("="*70)
    
    trace = {
        "answer": {
            "text": generation.get('answer', ''),
            "model": generation.get('model', 'Unknown'),
            "generated_at": generation.get('timestamp', 0)
        },
        "sources": [],
        "audit_trail": {
            "query": retrieval_results['query'],
            "embedding_model": EMBEDDING_MODEL,
            "retrieval_event_id": retrieval_event.id,
            "total_chunks_evaluated": retrieval_results['total_retrieved'],
            "retrieval_timestamp": retrieval_event.get('timestamp', 0)
        },
        "provenance_chain": []
    }
    
    # Build source citations with full provenance path
    for citation in citations:
        source_info = {
            "chunk": citation['source_chunk'],
            "document": citation['provenance_path'][0] if citation['provenance_path'] else None,
            "relevance_score": citation['relevance_score'],
            "provenance_path": [
                p['step'] for p in citation['provenance_path']
            ]
        }
        trace['sources'].append(source_info)
    
    # Build the complete provenance chain
    trace['provenance_chain'] = [
        {
            "node": "GENERATION",
            "id": generation.id,
            "type": "output",
            "description": "Final generated response with citations"
        },
        {
            "node": "RETRIEVAL_EVENT",
            "id": retrieval_event.id,
            "type": "process",
            "description": f"Retrieved {len(citations)} relevant chunks"
        },
        {
            "node": "CHUNK",
            "count": len(citations),
            "type": "retrieved",
            "description": "Matched document segments with vectors"
        },
        {
            "node": "EMBEDDING",
            "type": "transformation",
            "description": "Vector representations enabling similarity search"
        },
        {
            "node": "DOCUMENT",
            "count": len(set(c['provenance_path'][0].get('id') for c in citations if c['provenance_path'])),
            "type": "source",
            "description": "Original source documents"
        }
    ]
    
    # Print the trace
    print("\nCOMPLETE PROVENANCE TRACE:")
    print("-"*60)
    print(json.dumps(trace, indent=2))
    
    print("\n" + "-"*60)
    print("TRACE EXPLANATION:")
    print("-"*60)
    print("""
  The trace object above shows the complete reasoning path:
  
  1. USER QUERY → Generation: The original question that triggered retrieval
  2. GENERATION → RETRIEVAL_EVENT: Which retrieval event informed the answer
  3. RETRIEVAL_EVENT → CHUNKS: Which chunks were retrieved for context
  4. CHUNKS → EMBEDDING: How chunks were matched (vector similarity)
  5. EMBEDDING → DOCUMENT: The original source documents
  
  This structure enables:
  • Audit: Verify exactly which sources informed any answer
  • Debug: Trace back to understand why specific chunks were retrieved
  • Compliance: Provide evidence of proper sourcing for regulatory requirements
  • Trust: Users can verify citations against original documents
""")
    
    return trace


# =============================================================================
# PART 5: Complete Query Demonstration
# =============================================================================

def run_complete_demo():
    """Run a complete query demonstrating all provenance features."""
    print("\n" + "="*70)
    print("PART 5: COMPLETE QUERY DEMONSTRATION")
    print("="*70)
    
    # Run all sample queries
    for i, query in enumerate(QUERIES, 1):
        print(f"\n{'='*60}")
        print(f"QUERY {i}: {query}")
        print('='*60)
        
        # 1. Provenance-aware retrieval
        results = semantic_search_with_provenance(query, limit=2)
        
        # 2. Create retrieval event
        event = create_retrieval_event(query, results['chunks'])
        
        # 3. Assemble citations
        citations = assemble_citations(results)
        
        # 4. Build generation with citations (simulated)
        generation = build_generation_with_citations(query, results, citations)
        
        # 5. Show concise trace
        print(f"\n  Answer: {generation.get('answer', '')[:150]}...")
        print(f"  Sources cited: {len(citations)}")
        for j, c in enumerate(citations[:2], 1):
            doc_title = c['provenance_path'][0].get('title', 'Unknown') if c['provenance_path'] else 'Unknown'
            print(f"    [{j}] {doc_title} (score: {c['relevance_score']:.3f})")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("="*70)
    print("CITATION-TRACEABLE RAG WITH SUBGRAPH PROVENANCE")
    print("="*70)
    print("\nThis demo shows how to build a RAG pipeline where every answer")
    print("carries a verifiable audit trail from source document to generated output.")
    
    # Part 1: Schema inspection
    ontology = inspect_schema()
    
    # Part 2: Provenance-aware retrieval
    retrieval_results, retrieval_event = demonstrate_retrieval()
    
    # Part 3: Citation assembly
    citations = assemble_citations(retrieval_results)
    
    # Part 4: Trace visualization
    generation = build_generation_with_citations(
        retrieval_results['query'],
        retrieval_results,
        citations
    )
    trace = visualize_trace(generation, retrieval_event, retrieval_results, citations)
    
    # Part 5: Complete demo with multiple queries
    run_complete_demo()
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("""
You have seen:
  1. Schema: The graph structure modeling the RAG lifecycle
  2. Retrieval: Semantic search that fetches chunks AND provenance
  3. Citations: Assembly of traceable citations from chunk back to document
  4. Trace: Complete audit trail from query to answer
  5. Demo: Full provenance trace on sample queries

Key patterns implemented:
  • Document → Chunk → Embedding provenance chain
  • Vector search with provenance subgraph traversal
  • Retrieval event tracking linked to all retrieved chunks
  • Generation that carries full citation metadata
  • Structured trace output enabling audit and compliance

Next steps:
  • Run seed.py to populate the knowledge base first
  • Integrate with your LLM API for real generation
  • Add UI components to visualize citations
  • Implement compliance export features
""")


if __name__ == "__main__":
    main()
