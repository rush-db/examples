#!/usr/bin/env python3
"""
Contextual Retrieval Chains with Relationship-Weighted Relevance

This example demonstrates how to build intelligent retrieval systems using
RushDB's property graph combined with vector similarity search.

Key concepts:
1. Basic semantic search (baseline)
2. Relationship-weighted scoring
3. Chain traversal for contextual retrieval
4. Combining semantic and relationship scores
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Relationship weights for scoring
RELATIONSHIP_WEIGHTS = {
    "CITES": 1.0,
    "AUTHORED_BY": 0.8,
    "RELATED_TO": 0.5,
    "REFERENCES": 0.3,
}

# Depth penalties for chain traversal
DEPTH_PENALTIES = {
    1: 1.0,
    2: 0.6,
    3: 0.3,
}


@dataclass
class ScoredDocument:
    """Document with computed relevance score."""
    id: str
    title: str
    semantic_score: float
    relationship_score: float
    combined_score: float
    path: str  # Relationship chain to source


class RetrievalChain:
    """Contextual retrieval chain with relationship-weighted relevance."""

    def __init__(self, db: RushDB):
        self.db = db

    def basic_semantic_search(
        self,
        query: str,
        limit: int = 5
    ) -> list:
        """
        Phase 1: Basic semantic search without relationship context.
        This serves as our baseline for comparison.
        """
        print("\n" + "=" * 60)
        print("PHASE 1: Basic Semantic Search (Baseline)")
        print("=" * 60)
        print(f"Query: '{query}'")
        print("-" * 60)

        results = self.db.ai.search({
            "propertyName": "body",
            "query": query,
            "labels": ["DOCUMENT"],
            "limit": limit,
        })

        documents = []
        for result in results.data:
            documents.append(ScoredDocument(
                id=result.id,
                title=result.data.get("title", "Unknown"),
                semantic_score=result.score or 0.0,
                relationship_score=0.0,
                combined_score=result.score or 0.0,
                path="Direct semantic match",
            ))

        self._print_results(documents, show_relationship=False)
        return documents

    def relationship_weighted_search(
        self,
        query: str,
        related_to_ids: list[str],
        limit: int = 5
    ) -> list[ScoredDocument]:
        """
        Phase 2: Semantic search with relationship weighting.
        
        Documents connected to the given related IDs get boosted
        based on relationship type and strength.
        """
        print("\n" + "=" * 60)
        print("PHASE 2: Relationship-Weighted Search")
        print("=" * 60)
        print(f"Query: '{query}'")
        print(f"Context documents: {len(related_to_ids)}")
        print("-" * 60)

        # Get semantic search results
        results = self.db.ai.search({
            "propertyName": "body",
            "query": query,
            "labels": ["DOCUMENT"],
            "limit": limit * 2,  # Get more to allow for boosting
        })

        # Build relationship context
        relationship_boost = {}
        for doc_id in related_to_ids:
            related_doc = self.db.records.find_by_id(doc_id)
            if not related_doc:
                continue

            # Find outgoing relationships from this document
            connected = self.db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "DOCUMENT": {
                        "$relation": {
                            "type": "CITES|RELATED_TO|REFERENCES|AUTHORED_BY",
                            "direction": "in"
                        },
                        "$id": doc_id
                    }
                },
                "limit": 100
            })

            for conn in connected.data:
                rel_type = self._get_relationship_type(doc_id, conn.id)
                weight = RELATIONSHIP_WEIGHTS.get(rel_type, 0.3)
                
                if conn.id in relationship_boost:
                    relationship_boost[conn.id] = max(relationship_boost[conn.id], weight)
                else:
                    relationship_boost[conn.id] = weight

        # Score and rank documents
        documents = []
        for result in results.data:
            semantic_score = result.score or 0.0
            
            # Apply relationship boost if applicable
            rel_score = relationship_boost.get(result.id, 0.0)
            
            # Combined score: semantic (70%) + relationship (30%)
            combined = (semantic_score * 0.7) + (rel_score * 0.3)

            documents.append(ScoredDocument(
                id=result.id,
                title=result.data.get("title", "Unknown"),
                semantic_score=semantic_score,
                relationship_score=rel_score,
                combined_score=combined,
                path=f"Connected via relationship" if rel_score > 0 else "Semantic match",
            ))

        # Sort by combined score and limit
        documents.sort(key=lambda d: d.combined_score, reverse=True)
        documents = documents[:limit]

        self._print_results(documents, show_relationship=True)
        return documents

    def chain_traversal_search(
        self,
        query: str,
        seed_document_id: str,
        max_depth: int = 2,
        limit: int = 5
    ) -> list[ScoredDocument]:
        """
        Phase 3: Chain traversal for contextual retrieval.
        
        Follows relationship chains from seed document, accumulating
        context and applying depth-based penalties.
        """
        print("\n" + "=" * 60)
        print("PHASE 3: Chain Traversal with Depth-Based Weighting")
        print("=" * 60)
        print(f"Query: '{query}'")
        print(f"Seed document: {seed_document_id}")
        print(f"Max traversal depth: {max_depth}")
        print("-" * 60)

        # Get seed document
        seed = self.db.records.find_by_id(seed_document_id)
        if not seed:
            print("Seed document not found")
            return []

        print(f"Seed: {seed.data.get('title', 'Unknown')}")

        # Collect documents at each depth level
        depth_documents = {1: [], 2: [], 3: []}
        depth_documents[1].append(seed_document_id)

        # Traverse relationships
        for depth in range(1, max_depth + 1):
            if not depth_documents[depth]:
                continue

            for doc_id in depth_documents[depth][:]:  # Copy to avoid modification issues
                # Find all connected documents
                connected = self.db.records.find({
                    "labels": ["DOCUMENT"],
                    "where": {
                        "DOCUMENT": {
                            "$relation": {
                                "type": "CITES|RELATED_TO|REFERENCES|AUTHORED_BY",
                                "direction": "out"
                            },
                            "$id": doc_id
                        }
                    },
                    "limit": 100
                })

                for conn in connected.data:
                    if conn.id not in depth_documents[1] and \
                       conn.id not in depth_documents.get(2, []) and \
                       conn.id not in depth_documents.get(3, []):
                        if depth + 1 <= 3:
                            depth_documents[depth + 1].append(conn.id)

        print(f"Traversal found {sum(len(v) for v in depth_documents.values())} documents")

        # Combine semantic search with chain context
        results = self.db.ai.search({
            "propertyName": "body",
            "query": query,
            "labels": ["DOCUMENT"],
            "limit": limit * 3,
        })

        documents = []
        for result in results.data:
            semantic_score = result.score or 0.0
            
            # Calculate chain score based on depth
            chain_score = 0.0
            path = "Semantic match only"
            
            for depth, docs in depth_documents.items():
                if result.id in docs:
                    rel_type = self._get_relationship_type(seed_document_id, result.id)
                    base_weight = RELATIONSHIP_WEIGHTS.get(rel_type, 0.3)
                    depth_penalty = DEPTH_PENALTIES.get(depth, 0.3)
                    chain_score = base_weight * depth_penalty
                    path = f"Depth {depth} via {rel_type}"
                    break

            # Combined: semantic (60%) + chain (40%)
            combined = (semantic_score * 0.6) + (chain_score * 0.4)

            documents.append(ScoredDocument(
                id=result.id,
                title=result.data.get("title", "Unknown"),
                semantic_score=semantic_score,
                relationship_score=chain_score,
                combined_score=combined,
                path=path,
            ))

        # Sort and limit
        documents.sort(key=lambda d: d.combined_score, reverse=True)
        documents = documents[:limit]

        self._print_results(documents, show_relationship=True, show_path=True)
        return documents

    def contextual_chain_demo(
        self,
        topic: str,
        query: str
    ) -> list[ScoredDocument]:
        """
        Phase 4: Full contextual chain retrieval demo.
        
        Finds documents about a topic, then uses them as context
        for enhanced retrieval of related content.
        """
        print("\n" + "=" * 60)
        print("PHASE 4: Full Contextual Chain Retrieval")
        print("=" * 60)
        print(f"Topic: '{topic}'")
        print(f"Query: '{query}'")
        print("-" * 60)

        # First, find documents about the topic
        topic_docs = self.db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "TOPIC": {
                    "$relation": {"type": "DISCUSSES", "direction": "out"},
                    "name": topic
                }
            },
            "limit": 10
        })

        if not topic_docs.data:
            print(f"No documents found for topic: {topic}")
            return []

        print(f"Found {len(topic_docs.data)} documents about '{topic}'")
        topic_doc_ids = [d.id for d in topic_docs.data]

        # Now use these as context for enhanced retrieval
        return self.relationship_weighted_search(query, topic_doc_ids, limit=5)

    def _get_relationship_type(self, source_id: str, target_id: str) -> Optional[str]:
        """Get the relationship type between two documents."""
        # This would ideally use a native relationship query
        # For now, we return a default based on common patterns
        return "RELATED_TO"

    def _print_results(
        self,
        documents: list[ScoredDocument],
        show_relationship: bool = False,
        show_path: bool = False
    ):
        """Print formatted results."""
        if not documents:
            print("No results found")
            return

        print(f"\nTop {len(documents)} Results:")
        print("-" * 60)

        for i, doc in enumerate(documents, 1):
            print(f"\n{i}. {doc.title}")
            print(f"   Semantic: {doc.semantic_score:.4f}")
            if show_relationship:
                print(f"   Relationship: {doc.relationship_score:.4f}")
                print(f"   Combined: {doc.combined_score:.4f}")
            if show_path:
                print(f"   Path: {doc.path}")


def main():
    """Main demonstration of contextual retrieval chains."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found")
        print("Please copy .env.example to .env and add your API key")
        return

    print("\n" + "#" * 60)
    print("# Contextual Retrieval Chains with Relationship-Weighted Relevance")
    print("#" * 60)

    db = RushDB(api_key)
    chain = RetrievalChain(db)

    # Verify we have data
    count = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if not count.data:
        print("\nNo documents found. Please run 'python seed.py' first.")
        return

    # Get a sample document to use as seed
    sample_docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    seed_id = sample_docs.data[0].id if sample_docs.data else None

    # Phase 1: Basic semantic search
    basic_results = chain.basic_semantic_search(
        query="event driven architecture and patterns",
        limit=5
    )

    # Phase 2: Relationship-weighted search (using first result as context)
    if basic_results:
        context_ids = [r.id for r in basic_results[:2]]
        chain.relationship_weighted_search(
            query="resilience and fault tolerance",
            related_to_ids=context_ids,
            limit=5
        )

    # Phase 3: Chain traversal
    if seed_id:
        chain.chain_traversal_search(
            query="microservices and distributed systems",
            seed_document_id=seed_id,
            max_depth=2,
            limit=5
        )

    # Phase 4: Full contextual chain
    chain.contextual_chain_demo(
        topic="Microservices",
        query="service communication and API design"
    )

    print("\n" + "#" * 60)
    print("# Demonstration Complete")
    print("#" * 60)
    print("\nKey Takeaways:")
    print("  - Basic semantic search provides baseline results")
    print("  - Relationship weighting boosts connected documents")
    print("  - Chain traversal adds depth-based context")
    print("  - Combined scoring merges semantic + relationship signals")
    print("\nRelationship Weights Used:")
    for rel, weight in RELATIONSHIP_WEIGHTS.items():
        print(f"  - {rel}: {weight}")
    print("\nDepth Penalties:")
    for depth, penalty in DEPTH_PENALTIES.items():
        print(f"  - Depth {depth}: {penalty}")


if __name__ == "__main__":
    main()
