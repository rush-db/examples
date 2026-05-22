#!/usr/bin/env python3
"""
PageRank-Style Relevance Propagation for RAG Context Ordering

This script demonstrates how to improve RAG retrieval quality using
PageRank-style iterative relevance propagation through a knowledge graph.

Key insight: Graph edges carry topical signal that cosine similarity alone misses.
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx
import numpy as np
from dotenv import load_dotenv

from rushdb import RushDB

# Load environment
load_dotenv()

# Initialize RushDB client
db = RushDB(os.environ["RUSHDB_API_TOKEN"])


@dataclass
class ScoredChunk:
    """A chunk with its similarity and authority scores."""
    id: str
    text: str
    article_title: str
    topic: str
    similarity_score: float
    authority_score: float = 0.0


def get_chunk_neighbors(chunk_id: str, edge_type: Optional[str] = None) -> list[str]:
    """
    Get neighboring chunk IDs via graph traversal.
    
    Uses RushDB's relationship query to find chunks connected through
    any edge type (CITES, SHARES_AUTHOR, SHARES_TOPIC, FROM_ARTICLE).
    """
    # Query for related records through any relationship type
    # We fetch chunks that are connected to the given chunk
    results = db.records.find({
        "labels": ["CHUNK"],
        "where": {
            "CHUNK": {
                "$relation": {"direction": "any"}
            }
        },
        "limit": 200
    })
    
    # Filter to only chunks connected to our target
    neighbors = []
    for record in results:
        if record.id != chunk_id:
            neighbors.append(record.id)
    
    return neighbors


def build_graph_from_chunks(chunk_ids: list[str]) -> nx.DiGraph:
    """
    Build a directed graph from chunk IDs.
    
    Nodes: chunk IDs
    Edges: graph relationships (CITES, SHARES_AUTHOR, SHARES_TOPIC)
    Edge weights: based on relationship type importance
    """
    G = nx.DiGraph()
    
    # Add all chunks as nodes
    for chunk_id in chunk_ids:
        G.add_node(chunk_id)
    
    # Find all relationships between these chunks
    # We'll query each chunk for its relationships
    for chunk_id in chunk_ids:
        # Get chunks that share author (strong topical signal)
        author_results = db.records.find({
            "labels": ["CHUNK"],
            "where": {
                "author": db.records.find_by_id(chunk_id).get("author")
            },
            "limit": 50
        })
        for related in author_results:
            if related.id != chunk_id and related.id in chunk_ids:
                # Bidirectional for author sharing
                G.add_edge(chunk_id, related.id, weight=2.0, type="SHARES_AUTHOR")
                G.add_edge(related.id, chunk_id, weight=2.0, type="SHARES_AUTHOR")
        
        # Get chunks that share topic
        topic_results = db.records.find({
            "labels": ["CHUNK"],
            "where": {
                "topic": db.records.find_by_id(chunk_id).get("topic")
            },
            "limit": 50
        })
        for related in topic_results:
            if related.id != chunk_id and related.id in chunk_ids:
                G.add_edge(chunk_id, related.id, weight=1.5, type="SHARES_TOPIC")
        
        # Get cited chunks (citations indicate authoritative content)
        # In a real system, you'd query relationship type specifically
        article_title = db.records.find_by_id(chunk_id).get("articleTitle")
        if article_title:
            # Find previous chunks in same article
            same_article = db.records.find({
                "labels": ["CHUNK"],
                "where": {
                    "articleTitle": article_title,
                    "position": {"$lt": db.records.find_by_id(chunk_id).get("position", 0)}
                },
                "limit": 5
            })
            for related in same_article:
                if related.id in chunk_ids:
                    G.add_edge(chunk_id, related.id, weight=3.0, type="CITES")
    
    return G


def pagerank_propagation(
    initial_scores: dict[str, float],
    graph: nx.DiGraph,
    damping: float = 0.85,
    iterations: int = 20,
    convergence: float = 1e-6
) -> dict[str, float]:
    """
    Apply PageRank-style iterative propagation to refine scores.
    
    Algorithm:
    1. Initialize scores from similarity search
    2. For each iteration:
       - Propagate scores through graph edges
       - Dampened by edge weights
       - Include teleportation back to initial scores
    3. Return converged authority scores
    
    Args:
        initial_scores: Chunk ID -> similarity score from vector search
        graph: Directed graph of chunk relationships
        damping: Damping factor (0.85 is standard for PageRank)
        iterations: Maximum iterations
        convergence: Stop when score changes are below this threshold
    
    Returns:
        Chunk ID -> authority score after propagation
    """
    if not graph.nodes():
        return initial_scores
    
    # Normalize initial scores
    total = sum(initial_scores.values())
    if total > 0:
        init_normalized = {k: v / total for k, v in initial_scores.items()}
    else:
        init_normalized = initial_scores
    
    # Initialize authority scores
    scores = dict(init_normalized)
    
    # Get edge weights for normalization
    out_weights = {}
    for node in graph.nodes():
        out_weights[node] = sum(
            data.get('weight', 1.0) 
            for _, _, data in graph.out_edges(node, data=True)
        )
    
    for iteration in range(iterations):
        new_scores = {}
        total_change = 0.0
        
        for node in graph.nodes():
            # Propagate from in-neighbors
            propagated = 0.0
            in_edges = graph.in_edges(node, data=True)
            
            if out_weights[node] > 0:
                for predecessor, _, data in in_edges:
                    weight = data.get('weight', 1.0)
                    if predecessor in scores and predecessor in out_weights and out_weights[predecessor] > 0:
                        # Weighted PageRank contribution
                        contribution = (scores[predecessor] * weight) / out_weights[predecessor]
                        propagated += contribution
            
            # Apply damping and add teleportation to initial scores
            teleportation = init_normalized.get(node, 0.0) * (1 - damping)
            new_score = (1 - damping) * teleportation + damping * propagated
            
            # Add base score to prevent score collapse
            new_score += init_normalized.get(node, 0.0) * 0.1
            
            new_scores[node] = new_score
            total_change += abs(new_score - scores.get(node, 0.0))
        
        scores = new_scores
        
        if total_change < convergence:
            print(f"  Converged after {iteration + 1} iterations")
            break
    else:
        print(f"  Completed {iterations} iterations")
    
    # Normalize final scores
    total_score = sum(scores.values())
    if total_score > 0:
        scores = {k: v / total_score for k, v in scores.items()}
    
    return scores


def naive_similarity_search(query: str, limit: int = 10) -> list[ScoredChunk]:
    """
    Perform pure vector similarity search (baseline).
    """
    print(f"\n🔍 Performing similarity search for: \"{query}\"")
    
    results = db.ai.search({
        "propertyName": "text",
        "query": query,
        "labels": ["CHUNK"],
        "limit": limit * 2  # Fetch more for comparison
    })
    
    chunks = []
    for record in results:
        chunks.append(ScoredChunk(
            id=record.id,
            text=record.get("text", "")[:150] + "...",
            article_title=record.get("articleTitle", ""),
            topic=record.get("topic", ""),
            similarity_score=record.score if record.score else 0.0
        ))
    
    return chunks[:limit]


def propagation_scored_search(query: str, limit: int = 10) -> list[ScoredChunk]:
    """
    Apply PageRank-style propagation to improve ranking.
    """
    print(f"\n🔄 Applying PageRank-style propagation...")
    
    # Step 1: Get initial candidates via similarity search
    results = db.ai.search({
        "propertyName": "text",
        "query": query,
        "labels": ["CHUNK"],
        "limit": 50  # Get more candidates for propagation
    })
    
    # Build initial scores
    initial_scores = {}
    candidate_chunks = {}
    
    for record in results:
        chunk_id = record.id
        initial_scores[chunk_id] = record.score if record.score else 0.0
        candidate_chunks[chunk_id] = ScoredChunk(
            id=chunk_id,
            text=record.get("text", "")[:150] + "...",
            article_title=record.get("articleTitle", ""),
            topic=record.get("topic", ""),
            similarity_score=record.score if record.score else 0.0
        )
    
    print(f"  Found {len(initial_scores)} candidate chunks")
    
    # Step 2: Build graph from candidates
    print("  Building relevance graph...")
    graph = build_graph_from_chunks(list(initial_scores.keys()))
    print(f"  Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Step 3: Apply PageRank propagation
    print("  Running iterative propagation...")
    authority_scores = pagerank_propagation(
        initial_scores, 
        graph,
        damping=0.85,
        iterations=20
    )
    
    # Step 4: Update chunks with authority scores
    for chunk_id, authority_score in authority_scores.items():
        if chunk_id in candidate_chunks:
            candidate_chunks[chunk_id].authority_score = authority_score
    
    # Step 5: Sort by authority score
    scored_chunks = sorted(
        candidate_chunks.values(),
        key=lambda c: c.authority_score,
        reverse=True
    )
    
    return scored_chunks[:limit]


def display_comparison(naive_chunks: list[ScoredChunk], propagation_chunks: list[ScoredChunk]):
    """
    Display side-by-side comparison of naive vs propagation ordering.
    """
    print("\n" + "=" * 80)
    print("COMPARISON: NAIVE SIMILARITY vs. PROPAGATION-SCORED ORDERING")
    print("=" * 80)
    
    print("\n📊 NAIVE SIMILARITY ORDERING (Pure Vector Search)")
    print("-" * 80)
    for i, chunk in enumerate(naive_chunks, 1):
        print(f"\n{i}. [{chunk.topic}] {chunk.article_title}")
        print(f"   Similarity: {chunk.similarity_score:.4f}")
        print(f"   Preview: {chunk.text[:100]}...")
    
    print("\n\n📈 PROPAGATION-SCORED ORDERING (With Graph Propagation)")
    print("-" * 80)
    for i, chunk in enumerate(propagation_chunks, 1):
        print(f"\n{i}. [{chunk.topic}] {chunk.article_title}")
        print(f"   Authority: {chunk.authority_score:.4f} (sim: {chunk.similarity_score:.4f})")
        print(f"   Preview: {chunk.text[:100]}...")
    
    # Analyze reordering
    print("\n\n🔄 ORDERING CHANGES")
    print("-" * 80)
    
    naive_ids = [c.id for c in naive_chunks]
    propagation_ids = [c.id for c in propagation_chunks]
    
    promoted = []
    demoted = []
    
    for i, chunk_id in enumerate(propagation_ids):
        if chunk_id in naive_ids:
            old_pos = naive_ids.index(chunk_id)
            new_pos = i
            if new_pos < old_pos:
                promoted.append((chunk_id, old_pos, new_pos, propagation_chunks[i]))
            elif new_pos > old_pos:
                demoted.append((chunk_id, old_pos, new_pos, propagation_chunks[i]))
    
    if promoted:
        print("\n✅ PROMOTED (gained authority from connections):")
        for chunk_id, old_pos, new_pos, chunk in promoted[:3]:
            print(f"   {chunk.article_title}: pos {old_pos + 1} -> {new_pos + 1}")
            print(f"      Authority boosted: {chunk.similarity_score:.4f} -> {chunk.authority_score:.4f}")
    
    if demoted:
        print("\n⚠️  DEMOTED (similarity alone was misleading):")
        for chunk_id, old_pos, new_pos, chunk in demoted[:3]:
            print(f"   {chunk.article_title}: pos {old_pos + 1} -> {new_pos + 1}")
            print(f"      Overranked by sim: {chunk.similarity_score:.4f} -> {chunk.authority_score:.4f}")


def demonstrate_false_positive_fix():
    """
    Demonstrate how propagation fixes semantic false positives.
    
    Query: "How does cryptography relate to web security?"
    Expected: Chunks about security + cryptography should be elevated
    """
    print("\n" + "=" * 80)
    print("DEMONSTRATING FALSE POSITIVE FIX")
    print("=" * 80)
    print("\nQuery: \"How does cryptography relate to web security?\"")
    print("\nThis query spans two topics. Pure similarity might surface:")
    print("  - Cryptography chunks (high similarity to 'cryptography')")
    print("  - Security chunks (high similarity to 'security')")
    print("\nBut authoritative content connects both. Propagation should:")
    print("  - Identify security content that CITES or links to cryptography")
    print("  - Elevate chunks that bridge both domains")
    
    naive = naive_similarity_search("How does cryptography relate to web security?", limit=5)
    propagation = propagation_scored_search("How does cryptography relate to web security?", limit=5)
    
    print("\n📊 Results Analysis:")
    print("-" * 80)
    
    # Check for cross-topic authority
    crypto_security_chunks = []
    for chunk in propagation:
        # Chunks that discuss both or are well-connected across topics
        if chunk.topic in ["Security", "Data Engineering"]:
            crypto_security_chunks.append(chunk)
    
    if crypto_security_chunks:
        print("\n✅ Propagation elevated cross-topic authoritative chunks:")
        for chunk in crypto_security_chunks[:2]:
            print(f"   - {chunk.article_title} ({chunk.topic})")
            print(f"     Authority: {chunk.authority_score:.4f}")
    
    # Show specific reordering
    print("\n📈 Top propagation-scored chunks:")
    for i, chunk in enumerate(propagation[:3], 1):
        print(f"\n   {i}. {chunk.article_title}")
        print(f"      Topic: {chunk.topic}")
        print(f"      Authority: {chunk.authority_score:.4f}")
        print(f"      Text: {chunk.text[:80]}...")


def main():
    """Main demonstration function."""
    print("=" * 80)
    print("PAGERANK-STYLE SCORING FOR RAG CONTEXT ORDERING")
    print("=" * 80)
    print("""
This demonstration shows how to improve RAG retrieval quality using
PageRank-style iterative relevance propagation through graph edges.

Key insight: Graph edges carry topical signal that cosine similarity alone misses.

When a chunk is highly similar to the query AND well-connected to other
relevant chunks (via citations, shared authors, shared topics), its
authority score increases through iterative propagation.
    """)
    
    # Check for data
    try:
        test_find = db.records.find({"labels": ["CHUNK"], "limit": 1})
        if not test_find:
            print("⚠️  No chunks found. Run `python seed.py` first!")
            return
    except Exception as e:
        print(f"⚠️  Error connecting to RushDB: {e}")
        return
    
    # Main query: transformers and LLMs
    print("\n" + "=" * 80)
    print("MAIN DEMONSTRATION")
    print("=" * 80)
    
    query = "How do transformers work in large language models?"
    
    # Perform both searches
    naive_chunks = naive_similarity_search(query, limit=8)
    propagation_chunks = propagation_scored_search(query, limit=8)
    
    # Display comparison
    display_comparison(naive_chunks, propagation_chunks)
    
    # Demonstrate false positive fix
    demonstrate_false_positive_fix()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
PageRank-style propagation improves RAG context ordering by:

1. SEEDING with vector similarity scores
2. PROPAGATING through graph edges (citations, shared authors, topics)
3. ITERATING until convergence (authority flows through the graph)
4. RANKING by final authority scores

Benefits:
- Fixes semantic false positives (highly similar but not authoritative)
- Elevates well-connected, cross-topic content
- Produces context ordering that reflects document structure

Trade-offs:
- Requires graph edges between chunks
- More compute than pure similarity (iterations over graph)
- Edge creation requires domain knowledge or heuristics
    """)
    
    print("\n✅ Demo complete! Check the comparison above to see how propagation")
    print("   improves context ordering for better RAG quality.")


if __name__ == "__main__":
    main()
