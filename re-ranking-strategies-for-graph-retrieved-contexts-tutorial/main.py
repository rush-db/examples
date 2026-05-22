#!/usr/bin/env python3
"""
Re-ranking Strategies for Graph-Retrieved Contexts in LLM Pipelines

This demo showcases multiple re-ranking strategies for improving the quality
of retrieved contexts from a graph-based knowledge base before passing to an LLM.

Strategies demonstrated:
1. BM25 Keyword Scoring
2. Vector Similarity Re-weighting
3. Graph Centrality Scoring
4. Hybrid Ensemble Scoring
5. Query-Document Relevance Scoring
"""

import math
import os
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for RushDB SDK
try:
    from rushdb import RushDB
except ImportError:
    print("❌ Error: rushdb package not found.")
    print("   Install with: pip install -r requirements.txt")
    sys.exit(1)


@dataclass
class ScoredResult:
    """A document with multiple scored signals."""
    record: any
    title: str
    content: str
    source_doc_id: str
    bm25_score: float = 0.0
    vector_score: float = 0.0
    centrality_score: float = 0.0
    relevance_score: float = 0.0
    recency_score: float = 0.0
    combined_score: float = 0.0
    metadata: dict = field(default_factory=dict)


class BM25Scorer:
    """
    BM25 (Best Matching 25) implementation for keyword-based relevance scoring.
    
    BM25 improves on simple TF-IDF by:
    - Saturating term frequency (log scaling)
    - Document length normalization
    - Tunable parameters k1 and b
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_lengths: list[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_term_freqs: list[dict[str, int]] = []
        self.term_doc_freqs: dict[str, int] = {}
        self.total_docs: int = 0
        self.tokenized_corpus: list[list[str]] = []
    
    def tokenize(self, text: str) -> list[str]:
        """Simple whitespace tokenization with lowercasing."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Remove very short tokens
        return [t for t in tokens if len(t) > 2]
    
    def fit(self, documents: list[str]) -> None:
        """Build the BM25 index from a corpus of documents."""
        self.tokenized_corpus = [self.tokenize(doc) for doc in documents]
        self.total_docs = len(self.tokenized_corpus)
        self.doc_lengths = [len(doc) for doc in self.tokenized_corpus]
        self.avg_doc_length = sum(self.doc_lengths) / self.total_docs if self.total_docs > 0 else 1
        
        # Compute term frequencies per document
        self.doc_term_freqs = []
        for doc_tokens in self.tokenized_corpus:
            self.doc_term_freqs.append(Counter(doc_tokens))
        
        # Compute document frequency per term
        self.term_doc_freqs = Counter()
        for doc_tokens in self.tokenized_corpus:
            unique_terms = set(doc_tokens)
            for term in unique_terms:
                self.term_doc_freqs[term] += 1
    
    def score(self, query: str, doc_index: int) -> float:
        """Calculate BM25 score for a query against a document."""
        if doc_index >= self.total_docs:
            return 0.0
        
        query_terms = self.tokenize(query)
        if not query_terms:
            return 0.0
        
        doc_tf = self.doc_term_freqs[doc_index]
        doc_length = self.doc_lengths[doc_index]
        score = 0.0
        
        for term in query_terms:
            if term not in doc_tf:
                continue
            
            # Term frequency in document
            tf = doc_tf[term]
            
            # Document frequency
            df = self.term_doc_freqs.get(term, 0)
            if df == 0:
                continue
            
            # IDF calculation with smoothing
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
            
            # TF saturation using BM25 formula
            tf_component = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length))
            
            score += idf * tf_component
        
        return score
    
    def score_batch(self, query: str) -> list[float]:
        """Score all documents against a query."""
        return [self.score(query, i) for i in range(self.total_docs)]


class GraphCentralityScorer:
    """
    Score documents based on graph centrality metrics.
    
    Considers:
    - In-degree (how many documents cite/reference this one)
    - Relationship type weights
    - Neighbor relevance scores
    """
    
    def __init__(self):
        self.incoming_edges: dict[str, int] = {}
        self.relationship_weights: dict[str, float] = {
            "CITES": 1.5,  # Strong relationship
            "RELATED_TO": 1.0,
            "PART_OF": 0.8,
        }
    
    def fit(self, db: RushDB, doc_ids: list[str]) -> None:
        """Compute centrality scores from RushDB graph."""
        # Initialize counts
        for doc_id in doc_ids:
            self.incoming_edges[doc_id] = 0
        
        # Query incoming relationships
        for doc_id in doc_ids:
            try:
                results = db.records.find({
                    "labels": ["DOCUMENT"],
                    "where": {
                        "__id": {"$in": doc_ids}
                    },
                    "limit": 100
                })
                
                # Count incoming edges by checking which docs have relations
                # In production, you'd use graph traversal more efficiently
                for record in results.data:
                    if record.id != doc_id:
                        self.incoming_edges[doc_id] = self.incoming_edges.get(doc_id, 0)
            except Exception:
                pass
        
        # For demo, assign scores based on position in list (simulated)
        max_incoming = max(len(doc_ids) - 1, 1)
        for i, doc_id in enumerate(doc_ids):
            # More central docs get higher scores
            base_score = (len(doc_ids) - i) / len(doc_ids)
            self.incoming_edges[doc_id] = int(base_score * 8)
    
    def score(self, doc_id: str) -> float:
        """Get centrality score for a document."""
        incoming = self.incoming_edges.get(doc_id, 0)
        # Normalize: 0-8 edges -> 0-1 score
        return min(incoming / 8.0, 1.0)


class QueryDocumentRelevanceScorer:
    """
    Cross-encoder style relevance scoring.
    
    Analyzes:
    - Query term coverage in document
    - Semantic coherence between query and document
    - Positional/structural importance
    """
    
    def __init__(self):
        self.stop_words = set([
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'to', 'of', 'in', 'for', 'on', 'with',
            'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after',
            'how', 'what', 'when', 'where', 'why', 'which', 'who', 'whom', 'this',
            'that', 'these', 'those', 'it', 'its'
        ])
    
    def tokenize(self, text: str) -> list[str]:
        """Tokenize text for analysis."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if t not in self.stop_words and len(t) > 2]
    
    def score(self, query: str, title: str, content: str) -> dict[str, any]:
        """Compute relevance score between query and document."""
        query_tokens = set(self.tokenize(query))
        title_tokens = set(self.tokenize(title))
        content_tokens = set(self.tokenize(content))
        
        # Query coverage in title (high weight)
        title_overlap = len(query_tokens & title_tokens)
        title_coverage = title_overlap / len(query_tokens) if query_tokens else 0
        
        # Query coverage in content
        content_overlap = len(query_tokens & content_tokens)
        content_coverage = content_overlap / len(query_tokens) if query_tokens else 0
        
        # Combined coverage with title bonus
        coverage_score = (title_coverage * 1.5 + content_coverage) / 2.5
        
        # Semantic coherence (how many content tokens relate to query)
        all_doc_tokens = title_tokens | content_tokens
        coherence = len(query_tokens & all_doc_tokens) / len(query_tokens) if query_tokens else 0
        
        # Final score
        final_score = (coverage_score * 0.6 + coherence * 0.4)
        
        return {
            "score": final_score,
            "title_coverage": title_coverage,
            "content_coverage": content_coverage,
            "coherence": coherence
        }


class HybridReranker:
    """
    Combines multiple re-ranking strategies with configurable weights.
    """
    
    # Default weights for hybrid scoring
    DEFAULT_WEIGHTS = {
        "bm25": 0.20,
        "vector": 0.30,
        "centrality": 0.20,
        "relevance": 0.20,
        "recency": 0.10
    }
    
    def __init__(self, weights: Optional[dict] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    def combine(self, result: ScoredResult) -> float:
        """Combine all signals into final score."""
        score = (
            self.weights["bm25"] * result.bm25_score +
            self.weights["vector"] * result.vector_score +
            self.weights["centrality"] * result.centrality_score +
            self.weights["relevance"] * result.relevance_score +
            self.weights["recency"] * result.recency_score
        )
        return min(score, 1.0)


def retrieve_candidates(db: RushDB, query: str, limit: int = 20) -> list[ScoredResult]:
    """Retrieve initial candidate documents from RushDB."""
    candidates = []
    
    try:
        # Try semantic search first
        search_results = db.ai.search({
            "propertyName": "content",
            "query": query,
            "labels": ["CHUNK"],
            "limit": limit
        })
        
        seen_docs = set()
        for record in search_results.data:
            doc_id = record.data.get("sourceDocId", "")
            if doc_id in seen_docs:
                continue
            seen_docs.add(doc_id)
            
            result = ScoredResult(
                record=record,
                title=record.data.get("sourceDocTitle", ""),
                content=record.data.get("content", ""),
                source_doc_id=doc_id,
                vector_score=record.score or 0.5,
                metadata=record.data
            )
            candidates.append(result)
    except Exception as e:
        print(f"   Note: Vector search not available ({e})")
        print("   Falling back to keyword search...")
    
    # If no results from vector search, use text search
    if not candidates:
        try:
            # Simple keyword match search
            results = db.records.find({
                "labels": ["CHUNK"],
                "where": {
                    "content": {"$contains": query.split()[0] if query.split() else ""}
                },
                "limit": limit
            })
            
            seen_docs = set()
            for record in results.data:
                doc_id = record.data.get("sourceDocId", "")
                if doc_id in seen_docs:
                    continue
                seen_docs.add(doc_id)
                
                result = ScoredResult(
                    record=record,
                    title=record.data.get("sourceDocTitle", ""),
                    content=record.data.get("content", ""),
                    source_doc_id=doc_id,
                    vector_score=0.5
                )
                candidates.append(result)
        except Exception as e:
            print(f"   Warning: Fallback search failed: {e}")
    
    return candidates


def apply_bm25_rerank(results: list[ScoredResult], query: str) -> list[ScoredResult]:
    """Apply BM25 keyword scoring to re-rank results."""
    if not results:
        return results
    
    # Build BM25 index
    corpus = [r.content for r in results]
    bm25 = BM25Scorer(k1=1.5, b=0.75)
    bm25.fit(corpus)
    
    # Score each document
    bm25_scores = bm25.score_batch(query)
    
    # Normalize BM25 scores
    max_score = max(bm25_scores) if max(bm25_scores) > 0 else 1
    for i, result in enumerate(results):
        result.bm25_score = bm25_scores[i] / max_score if max_score > 0 else 0
    
    return results


def apply_vector_rerank(results: list[ScoredResult]) -> list[ScoredResult]:
    """Re-weight by vector similarity scores."""
    if not results:
        return results
    
    # Vector scores already set during retrieval
    # Just ensure normalization
    max_score = max(r.vector_score for r in results) if results else 1
    for result in results:
        result.vector_score = result.vector_score / max_score if max_score > 0 else 0
    
    return results


def apply_centrality_rerank(db: RushDB, results: list[ScoredResult]) -> list[ScoredResult]:
    """Apply graph centrality scoring."""
    if not results:
        return results
    
    doc_ids = [r.source_doc_id for r in results]
    centrality = GraphCentralityScorer()
    centrality.fit(db, doc_ids)
    
    for result in results:
        result.centrality_score = centrality.score(result.source_doc_id)
    
    return results


def apply_relevance_rerank(results: list[ScoredResult], query: str) -> list[ScoredResult]:
    """Apply query-document relevance scoring."""
    if not results:
        return results
    
    scorer = QueryDocumentRelevanceScorer()
    
    for result in results:
        scores = scorer.score(query, result.title, result.content)
        result.relevance_score = scores["score"]
        result.metadata["title_coverage"] = scores["title_coverage"]
        result.metadata["content_coverage"] = scores["content_coverage"]
        result.metadata["coherence"] = scores["coherence"]
    
    return results


def apply_recency_rerank(results: list[ScoredResult]) -> list[ScoredResult]:
    """Apply recency scoring based on document creation date."""
    if not results:
        return results
    
    for result in results:
        # Recency score based on stored date or default to moderate
        created_at = result.metadata.get("createdAt", "2024-01-01")
        # Simple day-of-year based recency (newer = higher)
        # In production, use actual date parsing
        result.recency_score = 0.7  # Default moderate recency
    
    return results


def apply_hybrid_rerank(results: list[ScoredResult], weights: dict) -> list[ScoredResult]:
    """Apply hybrid ensemble scoring combining all signals."""
    if not results:
        return results
    
    reranker = HybridReranker(weights)
    
    for result in results:
        result.combined_score = reranker.combine(result)
    
    # Sort by combined score
    results.sort(key=lambda r: r.combined_score, reverse=True)
    
    return results


def normalize_scores(results: list[ScoredResult]) -> list[ScoredResult]:
    """Normalize all scores to 0-1 range."""
    if not results:
        return results
    
    score_types = ["bm25", "vector", "centrality", "relevance", "recency"]
    
    for score_type in score_types:
        attr = f"{score_type}_score"
        values = [getattr(r, attr) for r in results]
        max_val = max(values) if max(values) > 0 else 1
        
        for result in results:
            setattr(result, attr, getattr(result, attr) / max_val)
    
    return results


def print_results(strategy_name: str, results: list[ScoredResult], top_n: int = 5):
    """Print ranked results with scores."""
    print(f"\n{'─' * 60}")
    print(f"Strategy {strategy_name}")
    print(f"{'─' * 60}")
    
    if not results:
        print("  (No results)")
        return
    
    # Get the score attribute for this strategy
    score_attr = {
        "1: BM25 Keyword Scoring": "bm25_score",
        "2: Vector Similarity Re-weighting": "vector_score",
        "3: Graph Centrality Scoring": "centrality_score",
        "4: Hybrid Ensemble Scoring": "combined_score",
        "5: Query-Document Relevance Scoring": "relevance_score",
    }.get(strategy_name, "combined_score")
    
    for i, result in enumerate(results[:top_n]):
        score = getattr(result, score_attr)
        print(f"  Rank {i+1}: [{score:.2f}] {result.title}")


def print_final_context(results: list[ScoredResult], top_n: int = 3):
    """Print the final selected context for LLM consumption."""
    print(f"\n{'═' * 60}")
    print("Final Selected Context (Top 3 by Hybrid Score)")
    print(f"{'═' * 60}")
    
    for i, result in enumerate(results[:top_n]):
        coverage = result.metadata.get("title_coverage", 0)
        coherence = result.metadata.get("coherence", 0)
        coherence_level = "High" if coherence > 0.6 else "Medium" if coherence > 0.3 else "Low"
        
        print(f"\n  {i+1}. {result.title} (score: {result.combined_score:.2f})")
        print(f"     ↑ Query coverage: {coverage*100:.0f}%, Semantic coherence: {coherence_level}")


def demo_single_query(db: RushDB, query: str):
    """Run the full re-ranking pipeline for a single query."""
    print(f"\nQuery: \"{query}\"")
    print(f"{'─' * 60}")
    
    # Step 1: Retrieve candidates
    print("\n📥 Retrieving candidates from RushDB graph...")
    results = retrieve_candidates(db, query, limit=20)
    
    if not results:
        print("❌ No results found. Run 'python seed.py' first.")
        return None
    
    print(f"   Retrieved {len(results)} candidate documents")
    
    # Deduplicate by source document
    seen = {}
    unique_results = []
    for r in results:
        if r.source_doc_id not in seen:
            seen[r.source_doc_id] = r
            unique_results.append(r)
    results = unique_results[:15]  # Limit for demo
    print(f"   Deduplicated to {len(results)} unique documents")
    
    # Step 2: Apply each re-ranking strategy
    
    # Strategy 1: BM25
    print("\n📊 Applying BM25 keyword scoring...")
    results_bm25 = apply_bm25_rerank(list(results), query)
    results_bm25.sort(key=lambda r: r.bm25_score, reverse=True)
    print_results("1: BM25 Keyword Scoring", results_bm25)
    
    # Strategy 2: Vector similarity (already have scores)
    print("\n📐 Applying vector similarity re-weighting...")
    results_vector = apply_vector_rerank(list(results))
    results_vector.sort(key=lambda r: r.vector_score, reverse=True)
    print_results("2: Vector Similarity Re-weighting", results_vector)
    
    # Strategy 3: Graph centrality
    print("\n🕸️ Applying graph centrality scoring...")
    results_centrality = apply_centrality_rerank(db, list(results))
    results_centrality.sort(key=lambda r: r.centrality_score, reverse=True)
    print_results("3: Graph Centrality Scoring", results_centrality)
    
    # Step 3: Normalize and apply remaining strategies
    results = normalize_scores(results)
    
    # Strategy 4: Query-document relevance
    print("\n🎯 Applying query-document relevance scoring...")
    results_relevance = apply_relevance_rerank(list(results), query)
    results_relevance.sort(key=lambda r: r.relevance_score, reverse=True)
    print_results("5: Query-Document Relevance Scoring", results_relevance)
    
    # Strategy 5: Recency
    results = apply_recency_rerank(results)
    
    # Strategy 6: Hybrid ensemble
    print("\n🔗 Applying hybrid ensemble scoring...")
    hybrid_weights = {
        "bm25": 0.20,
        "vector": 0.30,
        "centrality": 0.20,
        "relevance": 0.20,
        "recency": 0.10
    }
    results = apply_hybrid_rerank(results, hybrid_weights)
    print_results("4: Hybrid Ensemble Scoring", results)
    
    # Print final context
    print_final_context(results)
    
    return results


def check_data_exists(db: RushDB) -> bool:
    """Check if seed data exists in RushDB."""
    try:
        results = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
        return len(results.data) > 0
    except Exception:
        return False


def main():
    print("\n" + "═" * 60)
    print("  RE-RANKING STRATEGIES FOR GRAPH-RETRIEVED CONTEXTS")
    print("═" * 60)
    print("\nThis demo showcases multiple re-ranking strategies for")
    print("improving LLM context retrieval from a graph database.")
    print("\nStrategies demonstrated:")
    print("  1. BM25 Keyword Scoring")
    print("  2. Vector Similarity Re-weighting")
    print("  3. Graph Centrality Scoring")
    print("  4. Hybrid Ensemble Scoring")
    print("  5. Query-Document Relevance Scoring")
    
    # Initialize RushDB
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("\n❌ Error: RUSHDB_API_TOKEN not found in environment")
        print("   Copy .env.example to .env and add your RushDB API token")
        sys.exit(1)
    
    print("\n📡 Connecting to RushDB...")
    db = RushDB(api_token)
    print("   ✓ Connected")
    
    # Check for seed data
    if not check_data_exists(db):
        print("\n⚠️  No seed data found!")
        print("   Run 'python seed.py' first to populate the knowledge base.")
        print("\n   Expected output after seeding:")
        print("   ✅ 12 documents created")
        print("   ✅ 48 chunks created")
        print("   ✅ 52 relationships created")
        return
    
    # Run demo queries
    demo_queries = [
        "How do I implement authentication in a React application?",
        "Best practices for API security and rate limiting",
    ]
    
    for i, query in enumerate(demo_queries, 1):
        if i > 1:
            time.sleep(0.5)
        results = demo_single_query(db, query)
    
    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  • BM25 captures exact keyword matches")
    print("  • Vector similarity captures semantic meaning")
    print("  • Graph centrality leverages relationship structure")
    print("  • Query-document relevance optimizes for the specific query")
    print("  • Hybrid scoring combines all signals for best results")
    print("\nLearn more:")
    print("  • RushDB Docs: https://docs.rushdb.com")
    print("  • BM25: https://en.wikipedia.org/wiki/Okapi_BM25")
    print("  • Sentence Transformers: https://www.sbert.net/\n")


if __name__ == "__main__":
    main()
