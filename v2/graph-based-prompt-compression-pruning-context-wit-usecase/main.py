"""
Graph-Based Prompt Compression: Main Pipeline

This script demonstrates:
1. Naive chunk retrieval (top-k by vector similarity)
2. Graph-pruned retrieval (minimal connected subgraph)
3. Side-by-side metrics comparison

Run: python main.py
"""

import os
import time
import tiktoken
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB


# ============================================================================
# Configuration
# ============================================================================

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
PRUNING_THRESHOLD = float(os.getenv("PRUNING_THRESHOLD", "0.5"))
CANDIDATE_CHUNK_LIMIT = int(os.getenv("CANDIDATE_CHUNK_LIMIT", "20"))
FINAL_CHUNK_LIMIT = int(os.getenv("FINAL_CHUNK_LIMIT", "5"))

# Tokenizer for counting
ENCODER = tiktoken.get_encoding("cl100k_base")

# Benchmark queries
BENCHMARK_QUERIES = [
    "How do self-attention mechanisms work?",
    "What is retrieval-augmented generation?",
    "Explain the transformer architecture",
    "What are graph neural networks?",
    "How does BERT pre-training work?",
    "What is chain-of-thought prompting?",
    "How do you optimize transformer efficiency?",
    "What is context compression in LLMs?",
    "How are knowledge graphs used in AI?",
    "What are the trade-offs between RAG and fine-tuning?",
]


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class RetrievalResult:
    """Result of a retrieval operation with metrics."""
    chunks: list
    tokens: int
    latency_ms: float
    chunk_ids: set = field(default_factory=set)
    concept_ids: set = field(default_factory=set)


# ============================================================================
# Token Counting
# ============================================================================

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(ENCODER.encode(text))


def count_result_tokens(chunks: list) -> int:
    """Count total tokens in retrieval result."""
    total = 0
    for chunk in chunks:
        body = chunk.get("body", "")
        title = chunk.get("title", "")
        total += count_tokens(f"{title}\n{body}")
    return total


# ============================================================================
# Naive Retrieval (Baseline)
# ============================================================================

def naive_retrieval(db: RushDB, query: str, limit: int = 3) -> RetrievalResult:
    """
    Baseline retrieval: simple vector similarity search.
    Returns top-k chunks by relevance score.
    """
    start = time.perf_counter()
    
    try:
        # Try semantic search
        results = db.ai.search({
            "propertyName": "body",
            "query": query,
            "labels": ["CHUNK"],
            "limit": limit
        })
        
        chunks = []
        for record in results.data:
            chunks.append({
                "id": record.id,
                "title": record.get("title", ""),
                "body": record.get("body", ""),
                "score": record.score
            })
    except Exception:
        # Fallback to text search
        results = db.records.find({
            "labels": ["CHUNK"],
            "where": {"body": {"$contains": query.split()[0]}},
            "limit": limit
        })
        
        chunks = []
        for record in results.data:
            chunks.append({
                "id": record.id,
                "title": record.get("title", ""),
                "body": record.get("body", ""),
                "score": 1.0
            })
    
    latency_ms = (time.perf_counter() - start) * 1000
    tokens = count_result_tokens(chunks)
    chunk_ids = {c["id"] for c in chunks}
    
    return RetrievalResult(
        chunks=chunks,
        tokens=tokens,
        latency_ms=latency_ms,
        chunk_ids=chunk_ids
    )


# ============================================================================
# Graph-Pruned Retrieval
# ============================================================================

def graph_pruned_retrieval(
    db: RushDB,
    query: str,
    candidate_limit: int = CANDIDATE_CHUNK_LIMIT,
    final_limit: int = FINAL_CHUNK_LIMIT,
    relevance_threshold: float = PRUNING_THRESHOLD
) -> RetrievalResult:
    """
    Graph-aware retrieval using RushDB's relationship traversal.
    
    Algorithm:
    1. Semantic search to get candidate chunks (k=20)
    2. Traverse graph to find connected concepts
    3. Expand to chunks that share these concepts
    4. Score by combined relevance × graph connectivity
    5. Prune to top-k chunks
    """
    start = time.perf_counter()
    
    # Step 1: Get candidate chunks via semantic search
    try:
        candidates = db.ai.search({
            "propertyName": "body",
            "query": query,
            "labels": ["CHUNK"],
            "limit": candidate_limit
        })
    except Exception:
        candidates = db.records.find({
            "labels": ["CHUNK"],
            "where": {"body": {"$contains": query.split()[0]}},
            "limit": candidate_limit
        })
    
    # Convert to dict format
    candidate_chunks = []
    for record in candidates.data:
        candidate_chunks.append({
            "id": record.id,
            "title": record.get("title", ""),
            "body": record.get("body", ""),
            "score": record.score if hasattr(record, 'score') else 1.0
        })
    
    # Step 2: Find seed chunks (above relevance threshold)
    seed_chunks = [
        c for c in candidate_chunks
        if c["score"] >= relevance_threshold
    ]
    
    if not seed_chunks:
        # If no chunks meet threshold, use top candidates
        seed_chunks = candidate_chunks[:3]
    
    # Step 3: Traverse to connected concepts via RushDB relationships
    connected_concept_ids = set()
    concept_chunks = {}
    
    for chunk in seed_chunks:
        # RushDB: find CONCEPT nodes connected via MENTIONS relationship
        # Direction is 'in' because CHUNK MENTIONS CONCEPT
        related_concepts = db.records.find({
            "labels": ["CONCEPT"],
            "where": {
                "CHUNK": {
                    "$relation": {"type": "MENTIONS", "direction": "in"}
                },
                "$id": chunk["id"]
            },
            "limit": 20
        })
        
        for concept in related_concepts.data:
            connected_concept_ids.add(concept.id)
            
            # Step 4: Get all chunks mentioning this concept
            concept_chunk_records = db.records.find({
                "labels": ["CHUNK"],
                "where": {
                    "CONCEPT": {"$id": concept.id}
                },
                "limit": 50
            })
            
            for chunk_record in concept_chunk_records.data:
                cid = chunk_record.id
                if cid not in concept_chunks:
                    concept_chunks[cid] = {
                        "id": chunk_record.id,
                        "title": chunk_record.get("title", ""),
                        "body": chunk_record.get("body", ""),
                        "score": chunk_record.score if hasattr(chunk_record, 'score') else 1.0,
                        "concept_count": 0
                    }
                concept_chunks[cid]["concept_count"] += 1
    
    # Also include original candidates
    for chunk in candidate_chunks:
        cid = chunk["id"]
        if cid not in concept_chunks:
            concept_chunks[cid] = chunk.copy()
            concept_chunks[cid]["concept_count"] = 0
    
    # Step 5: Score chunks by combined metric
    # relevance_score * (1 + concept_connections)
    scored_chunks = []
    for chunk_id, chunk_data in concept_chunks.items():
        base_score = chunk_data["score"]
        concept_boost = 1 + (chunk_data["concept_count"] / max(1, len(connected_concept_ids)))
        combined_score = base_score * concept_boost
        
        scored_chunks.append({
            **chunk_data,
            "combined_score": combined_score
        })
    
    # Sort by combined score
    scored_chunks.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Step 6: Prune to final_limit chunks
    pruned_chunks = scored_chunks[:final_limit]
    
    # Also traverse RELATED_TO concepts for additional context
    additional_concept_ids = set()
    for concept_id in connected_concept_ids:
        related_concepts = db.records.find({
            "labels": ["CONCEPT"],
            "where": {
                "CONCEPT": {
                    "$relation": {"type": "RELATED_TO", "direction": "in"}
                },
                "$id": concept_id
            },
            "limit": 5
        })
        for rc in related_concepts.data:
            additional_concept_ids.add(rc.id)
    
    latency_ms = (time.perf_counter() - start) * 1000
    tokens = count_result_tokens(pruned_chunks)
    chunk_ids = {c["id"] for c in pruned_chunks}
    concept_ids = connected_concept_ids.union(additional_concept_ids)
    
    return RetrievalResult(
        chunks=pruned_chunks,
        tokens=tokens,
        latency_ms=latency_ms,
        chunk_ids=chunk_ids,
        concept_ids=concept_ids
    )


# ============================================================================
# Context Assembly
# ============================================================================

def assemble_context(chunks: list, style: str = "detailed") -> str:
    """
    Assemble retrieved chunks into a context string for LLM prompting.
    
    Args:
        chunks: List of chunk dictionaries with 'title' and 'body'
        style: 'detailed' includes all content, 'compressed' is shorter
    """
    if not chunks:
        return "No relevant context found."
    
    context_parts = ["=== Retrieved Context ===\n"]
    
    for i, chunk in enumerate(chunks, 1):
        title = chunk.get("title", "Untitled")
        body = chunk.get("body", "")
        score = chunk.get("score", 0)
        
        if style == "detailed":
            context_parts.append(f"\n[Source {i}] (relevance: {score:.2f})")
            context_parts.append(f"Title: {title}")
            context_parts.append(f"Content: {body}")
        else:
            # Compressed: just the body
            context_parts.append(f"\n{body}")
    
    return "".join(context_parts)


# ============================================================================
# Metrics Calculation
# ============================================================================

def calculate_metrics(
    naive_result: RetrievalResult,
    graph_result: RetrievalResult,
    query: str
) -> dict:
    """
    Calculate comparison metrics between naive and graph-pruned retrieval.
    """
    token_reduction = ((naive_result.tokens - graph_result.tokens) 
                       / naive_result.tokens * 100) if naive_result.tokens > 0 else 0
    
    # Concept overlap (simulated - in production, compare against reference)
    concept_overlap = len(naive_result.concept_ids & graph_result.concept_ids)
    total_concepts = len(naive_result.concept_ids | graph_result.concept_ids)
    overlap_ratio = concept_overlap / total_concepts if total_concepts > 0 else 0
    
    # Chunk overlap
    chunk_overlap = len(naive_result.chunk_ids & graph_result.chunk_ids)
    total_unique = len(naive_result.chunk_ids | graph_result.chunk_ids)
    chunk_overlap_ratio = chunk_overlap / total_unique if total_unique > 0 else 0
    
    return {
        "query": query,
        "naive_tokens": naive_result.tokens,
        "graph_tokens": graph_result.tokens,
        "token_reduction_pct": token_reduction,
        "naive_latency_ms": naive_result.latency_ms,
        "graph_latency_ms": graph_result.latency_ms,
        "latency_overhead_ms": graph_result.latency_ms - naive_result.latency_ms,
        "chunk_overlap_ratio": chunk_overlap_ratio,
        "concept_overlap_ratio": overlap_ratio,
        "naive_chunk_count": len(naive_result.chunks),
        "graph_chunk_count": len(graph_result.chunks),
    }


def print_metrics(metrics: dict):
    """Pretty print metrics for a single query."""
    print(f"\n  📊 Metrics for: \"{metrics['query']}\"")
    print(f"  " + "─" * 50)
    print(f"  Token Reduction:     {metrics['naive_tokens']} → {metrics['graph_tokens']} ({metrics['token_reduction_pct']:.1f}% saved)")
    print(f"  Latency Overhead:     {metrics['latency_overhead_ms']:.1f}ms (naive: {metrics['naive_latency_ms']:.1f}ms, graph: {metrics['graph_latency_ms']:.1f}ms)")
    print(f"  Chunk Overlap:        {metrics['chunk_overlap_ratio']*100:.1f}% ({metrics['naive_chunk_count']} vs {metrics['graph_chunk_count']} chunks)")


def print_summary(all_metrics: list):
    """Print aggregate summary across all queries."""
    avg_token_reduction = sum(m["token_reduction_pct"] for m in all_metrics) / len(all_metrics)
    avg_naive_latency = sum(m["naive_latency_ms"] for m in all_metrics) / len(all_metrics)
    avg_graph_latency = sum(m["graph_latency_ms"] for m in all_metrics) / len(all_metrics)
    avg_chunk_overlap = sum(m["chunk_overlap_ratio"] for m in all_metrics) / len(all_metrics)
    
    print("\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)
    print(f"  Queries evaluated:    {len(all_metrics)}")
    print(f"  Avg Token Reduction:  {avg_token_reduction:.1f}%")
    print(f"  Avg Retrieval Latency:")
    print(f"    - Naive:             {avg_naive_latency:.1f}ms")
    print(f"    - Graph:             {avg_graph_latency:.1f}ms")
    print(f"    - Overhead:          {avg_graph_latency - avg_naive_latency:.1f}ms")
    print(f"  Avg Chunk Overlap:     {avg_chunk_overlap*100:.1f}%")
    print("=" * 60)


# ============================================================================
# Production Considerations Demo
# ============================================================================

def show_production_considerations():
    """Display production deployment considerations."""
    print("""
🏭 PRODUCTION CONSIDERATIONS

1. GRAPH UPDATE FREQUENCY
   ------------------------
   • On Document Update: Re-extract concepts and update MENTIONS relationships
   • Nightly Batch: Full graph consistency check and orphan cleanup
   • On-Demand: Lazy-update only queried concepts
   
   Code pattern:
   ```python
   def update_document_graph(document_id):
       # Get affected chunks
       chunks = db.records.find({
           "labels": ["CHUNK"],
           "where": {"DOCUMENT": {"$id": document_id}}
       })
       
       for chunk in chunks:
           concepts = extract_concepts(chunk.body)
           # Update relationships...
   ```

2. VECTOR INDEX SYNC
   ------------------
   • External index: Re-embed chunks on document update
   • Managed index: RushDB handles embedding, use refresh API
   • Sync strategy: Event-driven on write, batch-repair nightly
   
   Code pattern:
   ```python
   # Batch sync after bulk updates
   db.ai.indexes.upsert_vectors(index_id, {
       "items": [{"recordId": c.id, "vector": embed(c.body)} 
                 for c in updated_chunks]
   })
   ```

3. PRUNING THRESHOLD TUNING
   -------------------------
   Use case           | Threshold | Rationale
   -------------------|-----------|-----------------------------------
   Code generation    | 0.7       | High accuracy required
   General Q&A        | 0.5       | Balance speed/quality  
   Creative writing   | 0.3       | More context helps
   Legal/compliance   | 0.8       | Minimize hallucinations
   
   Tune by running your benchmark set and plotting precision-recall.

4. SCALABILITY
   ------------
   • Graph traversal: Use depth limits and result caps
   • Batch queries: Process multiple queries in parallel
   • Caching: Cache graph neighborhoods for hot concepts
   • Sharding: RushDB handles Neo4j partitioning automatically

5. MONITORING
   -----------
   Track these metrics in production:
   • Retrieval latency (p50, p95, p99)
   • Token reduction rate over time
   • Concept coverage (% queries with relevant concepts)
   • Pruning ratio (candidate vs final chunks)
""")


# ============================================================================
# Main Pipeline
# ============================================================================

def main():
    print("=" * 60)
    print("Graph-Based Prompt Compression Demo")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  • Pruning threshold: {PRUNING_THRESHOLD}")
    print(f"  • Candidate limit:   {CANDIDATE_CHUNK_LIMIT}")
    print(f"  • Final chunk limit:  {FINAL_CHUNK_LIMIT}")
    
    # Initialize RushDB
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("\n❌ Error: RUSHDB_API_KEY not set")
        print("   Set it in .env or as an environment variable.")
        return
    
    db = RushDB(api_key)
    print("\n✓ Connected to RushDB")
    
    # Check for data
    existing = db.records.find({"labels": ["CHUNK"], "limit": 1})
    if existing.total == 0:
        print("\n❌ No data found. Run `python seed.py` first.")
        return
    
    print(f"✓ Found {existing.total or 'many'} chunks in database\n")
    
    # Run benchmark queries
    all_metrics = []
    
    for i, query in enumerate(BENCHMARK_QUERIES, 1):
        print(f"[{i}/{len(BENCHMARK_QUERIES)}] Query: \"{query}\"")
        
        # Naive retrieval
        naive_result = naive_retrieval(db, query, limit=3)
        
        # Graph-pruned retrieval
        graph_result = graph_pruned_retrieval(db, query)
        
        # Calculate and store metrics
        metrics = calculate_metrics(naive_result, graph_result, query)
        all_metrics.append(metrics)
        
        # Print per-query metrics
        print_metrics(metrics)
        
        # Show context comparison (optional, for demo)
        if i <= 3:
            naive_ctx = assemble_context(naive_result.chunks[:2], "compressed")
            graph_ctx = assemble_context(graph_result.chunks, "compressed")
            print(f"\n  📝 Naive context preview ({naive_result.tokens} tokens):")
            print(f"     {naive_ctx[:200]}...")
            print(f"\n  📝 Graph-pruned context preview ({graph_result.tokens} tokens):")
            print(f"     {graph_ctx[:200]}...")
    
    # Print summary
    print_summary(all_metrics)
    
    # Show production considerations
    show_production_considerations()
    
    print("\n✅ Pipeline complete!")


if __name__ == "__main__":
    main()
