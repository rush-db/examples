"""
RAG Feedback Loop Demo — Main Script

This script demonstrates building a graph-backed feedback loop for RAG relevance tuning.
It shows how to:
1. Search documents using vector similarity
2. Collect user feedback on retrieved results
3. Store feedback as graph relationships
4. Analyze feedback patterns
5. Use feedback to weight future retrieval
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()


@dataclass
class SearchResult:
    """Represents a document retrieved via vector search."""
    document_id: str
    title: str
    content: str
    score: float



@dataclass
class FeedbackEntry:
    """Represents user feedback on a search result."""
    query: str
    document_id: str
    document_title: str
    rating: str  # "helpful" or "not_helpful"
    comment: Optional[str] = None


class RAGFeedbackLoop:
    """
    Graph-backed feedback loop for RAG relevance tuning.
    
    This class demonstrates the complete feedback loop pattern:
    - Store documents with embeddings
    - Search using vector similarity
    - Collect and store feedback as graph relationships
    - Analyze feedback patterns
    - Use feedback to weight future retrieval
    """
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def semantic_search(
        self,
        query: str,
        labels: list[str] = None,
        limit: int = 5,
        boost_previously_helpful: bool = True
    ) -> list[SearchResult]:
        """
        Perform semantic search with optional feedback boosting.
        
        Args:
            query: Natural language query
            labels: Labels to search within
            limit: Maximum results to return
            boost_previously_helpful: Whether to boost documents with positive feedback
            
        Returns:
            List of SearchResult objects
        """
        labels = labels or ["DOCUMENT"]
        
        # Standard vector search
        search_params = {
            "propertyName": "content",
            "query": query,
            "labels": labels,
            "limit": limit
        }
        
        results = self.db.ai.search(search_params)
        search_results = []
        
        for doc in results.data:
            score = doc.score if doc.score is not None else 0.0
            
            # Boost score for documents with positive feedback history
            if boost_previously_helpful:
                boost = self._calculate_feedback_boost(doc.id)
                score += boost
            
            search_results.append(SearchResult(
                document_id=doc.id,
                title=doc.get("title", "Untitled"),
                content=doc.get("content", ""),
                score=score
            ))
        
        # Re-sort by boosted score
        search_results.sort(key=lambda x: x.score, reverse=True)
        
        return search_results
    
    def _calculate_feedback_boost(self, document_id: str) -> float:
        """
        Calculate score boost based on historical feedback.
        
        Documents with positive feedback get a small boost,
        documents with negative feedback get a slight penalty.
        """
        feedback_records = self.db.records.find({
            "labels": ["FEEDBACK"],
            "where": {
                "DOCUMENT": {
                    "$relation": {"type": "RATES", "direction": "in"},
                    "$id": document_id
                }
            }
        })
        
        if not feedback_records.data:
            return 0.0
        
        # Count helpful vs not_helpful
        helpful = sum(1 for f in feedback_records.data if f.get("rating") == "helpful")
        not_helpful = sum(1 for f in feedback_records.data if f.get("rating") == "not_helpful")
        
        total = helpful + not_helpful
        if total == 0:
            return 0.0
        
        # Boost proportional to helpful ratio
        helpful_ratio = helpful / total
        
        # +0.05 for helpful, -0.02 for not helpful
        boost = (helpful_ratio - 0.5) * 0.1
        return boost
    
    def store_feedback(
        self,
        feedback: FeedbackEntry,
        create_transaction: bool = True
    ) -> dict:
        """
        Store user feedback as a graph relationship.
        
        Creates FEEDBACK record linked to both:
        - DOCUMENT via RATES relationship
        - QUERY via FOR_QUERY relationship
        """
        # Find the document
        docs = self.db.records.find({
            "labels": ["DOCUMENT"],
            "where": {"__id": feedback.document_id}
        })
        
        if not docs.data:
            raise ValueError(f"Document {feedback.document_id} not found")
        
        doc = docs.data[0]
        
        # Create or find query record
        query_record = self._get_or_create_query_record(feedback.query)
        
        # Create feedback record with relationships in a transaction
        def create_feedback(tx):
            # Create the feedback record
            feedback_record = self.db.records.create(
                label="FEEDBACK",
                data={
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "query_text": feedback.query,
                    "document_title": feedback.document_title
                },
                transaction=tx
            )
            
            # Attach feedback to document (RATES relationship)
            self.db.records.attach(
                source=feedback_record,
                target=doc,
                options={"type": "RATES", "direction": "out"},
                transaction=tx
            )
            
            # Attach feedback to query (FOR_QUERY relationship)
            self.db.records.attach(
                source=feedback_record,
                target=query_record,
                options={"type": "FOR_QUERY", "direction": "out"},
                transaction=tx
            )
            
            return feedback_record
        
        if create_transaction:
            with self.db.transactions.begin() as tx:
                result = create_feedback(tx)
        else:
            tx = self.db.transactions.begin()
            try:
                result = create_feedback(tx)
                tx.commit()
            except Exception:
                tx.rollback()
                raise
        
        return {"status": "success", "feedback_id": result.id}
    
    def _get_or_create_query_record(self, query_text: str):
        """Find existing query or create new one."""
        existing = self.db.records.find({
            "labels": ["QUERY"],
            "where": {"text": query_text}
        })
        
        if existing.data:
            return existing.data[0]
        
        return self.db.records.create(
            label="QUERY",
            data={"text": query_text}
        )
    
    def get_feedback_stats(self) -> dict:
        """Get aggregate feedback statistics."""
        all_feedback = self.db.records.find({"labels": ["FEEDBACK"]})
        
        if not all_feedback.data:
            return {"total": 0, "helpful": 0, "not_helpful": 0}
        
        helpful = sum(1 for f in all_feedback.data if f.get("rating") == "helpful")
        not_helpful = sum(1 for f in all_feedback.data if f.get("rating") == "not_helpful")
        
        return {
            "total": len(all_feedback.data),
            "helpful": helpful,
            "not_helpful": not_helpful,
            "helpful_percentage": (helpful / len(all_feedback.data)) * 100 if all_feedback.data else 0
        }
    
    def get_document_feedback_history(self, document_id: str) -> list:
        """Get all feedback entries for a specific document."""
        feedback = self.db.records.find({
            "labels": ["FEEDBACK"],
            "where": {
                "DOCUMENT": {
                    "$relation": {"type": "RATES", "direction": "in"},
                    "$id": document_id
                }
            }
        })
        
        return [
            {
                "rating": f.get("rating"),
                "comment": f.get("comment"),
                "query": f.get("query_text")
            }
            for f in feedback.data
        ]
    
    def get_top_performing_documents(self, limit: int = 5) -> list:
        """Get documents with the most positive feedback."""
        all_docs = self.db.records.find({"labels": ["DOCUMENT"], "limit": 100})
        
        doc_scores = []
        for doc in all_docs.data:
            feedback = self.db.records.find({
                "labels": ["FEEDBACK"],
                "where": {
                    "DOCUMENT": {
                        "$relation": {"type": "RATES", "direction": "in"},
                        "$id": doc.id
                    }
                }
            })
            
            helpful = sum(1 for f in feedback.data if f.get("rating") == "helpful")
            not_helpful = sum(1 for f in feedback.data if f.get("rating") == "not_helpful")
            total = helpful + not_helpful
            
            score = helpful if total > 0 else 0
            doc_scores.append({
                "id": doc.id,
                "title": doc.get("title"),
                "helpful": helpful,
                "not_helpful": not_helpful,
                "total": total,
                "score": score
            })
        
        # Sort by score descending
        doc_scores.sort(key=lambda x: x["score"], reverse=True)
        return doc_scores[:limit]



def simulate_user_feedback(
    results: list[SearchResult],
    feedback_loop: RAGFeedbackLoop,
    query: str
) -> list[FeedbackEntry]:
    """
    Simulate user feedback on search results.
    
    In a real application, this would come from actual user interactions.
    Here we simulate by treating all results as helpful for demo purposes.
    """
    feedback_entries = []
    
    for result in results:
        # Simulate feedback (in real app, this comes from user interaction)
        # For demo: randomly rate as helpful or not_helpful, weighted toward helpful
        import random
        rating = "helpful" if random.random() < 0.85 else "not_helpful"
        
        entry = FeedbackEntry(
            query=query,
            document_id=result.document_id,
            document_title=result.title,
            rating=rating,
            comment=None
        )
        feedback_entries.append(entry)
        
        # Store in RushDB
        feedback_loop.store_feedback(entry)
        
        status = "✓" if rating == "helpful" else "✗"
        print(f"     • Document '{result.title}': {rating} {status}")
    
    return feedback_entries


def main():
    """Main demonstration of the RAG feedback loop."""
    print("=== RAG Feedback Loop Demo ===\n")
    
    # Initialize RushDB client
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY environment variable not set")
        print("Please copy .env.example to .env and fill in your API key")
        return
    
    url = os.environ.get("RUSHDB_API_KEY")
    if url:
        db = RushDB(api_key, url=url)
    else:
        db = RushDB(api_key)
    
    feedback_loop = RAGFeedbackLoop(db)
    
    # Step 1: Semantic Search
    print("[1/6] Running semantic search for 'machine learning optimization'...")
    results = feedback_loop.semantic_search(
        query="machine learning optimization techniques",
        limit=5,
        boost_previously_helpful=True
    )
    print(f"  ✓ Found {len(results)} relevant documents")
    for i, result in enumerate(results, 1):
        print(f"     [{result.score:.3f}] {result.title}")
    print()
    
    # Step 2: Simulate User Feedback
    print("[2/6] Simulating user feedback on results...")
    feedback = simulate_user_feedback(results, feedback_loop, "machine learning optimization techniques")
    print(f"  ✓ Collected {len(feedback)} feedback entries\n")
    
    # Step 3: Get Feedback Statistics
    print("[3/6] Analyzing feedback patterns...")
    stats = feedback_loop.get_feedback_stats()
    print(f"  ✓ Feedback pattern analysis:")
    print(f"     Total feedback: {stats['total']}")
    print(f"     Helpful: {stats['helpful']} ({stats['helpful_percentage']:.0f}%)")
    print(f"     Not helpful: {stats['not_helpful']} ({100 - stats['helpful_percentage']:.0f}%)")
    print()
    
    # Step 4: Get Top Performing Documents
    print("[4/6] Identifying top performing documents...")
    top_docs = feedback_loop.get_top_performing_documents(limit=3)
    if top_docs:
        print("  ✓ Top documents by helpfulness:")
        for doc in top_docs:
            print(f"     • {doc['title']}: {doc['helpful']} helpful, {doc['not_helpful']} not helpful")
    else:
        print("  No feedback collected yet")
    print()
    
    # Step 5: Feedback-Boosted Search
    print("[5/6] Running feedback-boosted retrieval...")
    boosted_results = feedback_loop.semantic_search(
        query="neural network training deep learning",
        limit=5,
        boost_previously_helpful=True
    )
    print(f"  ✓ Documents with feedback history boosted:")
    for result in boosted_results:
        boost = feedback_loop._calculate_feedback_boost(result.document_id)
        boost_str = f"+{boost:.3f}" if boost > 0 else f"{boost:.3f}"
        print(f"     [Boosted by {boost_str}] {result.title}")
    print()
    
    # Step 6: Document Feedback History
    print("[6/6] Checking feedback history for specific documents...")
    if results:
        doc_id = results[0].document_id
        history = feedback_loop.get_document_feedback_history(doc_id)
        print(f"  ✓ Feedback history for '{results[0].title}':")
        if history:
            for entry in history:
                print(f"     • Query: '{entry['query']}' - Rating: {entry['rating']}")
        else:
            print("     No feedback history")
    print()
    
    print("=== Demo Complete ===")
    print("\nThe feedback loop is now active:")
    print("- User searches retrieve documents via vector similarity")
    print("- Feedback is stored as graph relationships")
    print("- Future searches boost documents with positive feedback history")
    print("- Pattern analysis helps identify high-quality content")



if __name__ == "__main__":
    main()
