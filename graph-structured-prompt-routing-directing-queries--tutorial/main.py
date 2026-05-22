"""
Graph-Structured Prompt Routing Demo

Demonstrates how to use RushDB's property graph to route queries
to the correct domain subgraph for targeted retrieval.
"""

import os
import time
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)


class QueryRouter:
    """
    Routes incoming queries to the appropriate domain subgraph.
    
    Uses a two-stage approach:
    1. Semantic search against PATTERN nodes to classify intent
    2. Graph traversal to resolve target domain and retrieve knowledge
    """

    def __init__(self, db_client):
        self.db = db_client

    def route(self, query: str) -> dict:
        """
        Route a query to the correct domain subgraph.
        
        Returns dict with:
            - domain: target domain name
            - patterns: matched patterns
            - knowledge: relevant knowledge entries
            - metrics: routing performance data
        """
        start_time = time.time()
        
        # Stage 1: Classify intent via semantic search on patterns
        pattern_results = self._find_matching_patterns(query)
        
        # Stage 2: Resolve domain from patterns
        target_domain = self._resolve_domain(pattern_results)
        
        if not target_domain:
            return {
                "query": query,
                "domain": None,
                "patterns": [],
                "knowledge": [],
                "classification_confidence": 0.0,
                "routing_time_ms": (time.time() - start_time) * 1000,
            }

        # Stage 3: Retrieve knowledge from target subdomain
        knowledge = self._retrieve_domain_knowledge(target_domain, query)
        
        routing_time = (time.time() - start_time) * 1000
        avg_score = sum(p.score for p in pattern_results) / len(pattern_results) if pattern_results else 0

        return {
            "query": query,
            "domain": target_domain,
            "patterns": [{"text": p.data["text"], "score": p.score} for p in pattern_results[:3]],
            "knowledge": [{"title": k.data["title"], "body": k.data["body"], "tags": k.data["tags"]} for k in knowledge],
            "classification_confidence": avg_score,
            "routing_time_ms": routing_time,
        }

    def _find_matching_patterns(self, query: str, limit: int = 3):
        """Find patterns most similar to the query via semantic search."""
        try:
            # Search for matching patterns in the graph
            results = self.db.ai.search({
                "propertyName": "text",
                "query": query,
                "labels": ["PATTERN"],
                "limit": limit,
            })
            return results.data
        except Exception as e:
            print(f"  Warning: Semantic search unavailable ({e}), falling back to text search")
            return self._find_patterns_text_search(query, limit)

    def _find_patterns_text_search(self, query: str, limit: int = 3):
        """Fallback: text-based pattern matching when semantic search unavailable."""
        # Simple keyword matching as fallback
        query_words = set(query.lower().split())
        
        all_patterns = self.db.records.find({
            "labels": ["PATTERN"],
            "limit": 100,
        }).data
        
        # Score patterns by word overlap
        scored = []
        for pattern in all_patterns:
            pattern_words = set(pattern.data.get("text", "").lower().split())
            overlap = len(query_words & pattern_words)
            if overlap > 0:
                scored.append((overlap / max(len(query_words), 1), pattern))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]

    def _resolve_domain(self, patterns) -> str:
        """Resolve the target domain from matched patterns."""
        if not patterns:
            return None

        # Aggregate domain votes from patterns
        domain_votes = {}
        for pattern in patterns:
            domain = pattern.data.get("domain_id")
            if domain:
                score = getattr(pattern, "score", 0.5)  # Default score for fallback
                if domain not in domain_votes:
                    domain_votes[domain] = 0
                domain_votes[domain] += score

        if not domain_votes:
            return None

        # Return the domain with highest weighted votes
        return max(domain_votes, key=domain_votes.get)

    def _retrieve_domain_knowledge(self, domain_id: str, query: str):
        """Retrieve knowledge entries from the target domain subgraph."""
        # Find knowledge entries linked to this domain
        results = self.db.records.find({
            "labels": ["KNOWLEDGE"],
            "where": {
                "domain_id": domain_id,
            },
            "limit": 5,
        })
        
        return results.data


def print_routing_result(result: dict):
    """Pretty print a routing result."""
    print(f"\n{'='*60}")
    print(f"Query: \"{result['query']}\"")
    print(f"{'='*60}")
    
    if result["domain"] is None:
        print("  ⚠ No route found")
        return

    print(f"  ✓ Routed to: {result['domain']} domain")
    print(f"  ✓ Classification confidence: {result['classification_confidence']:.3f}")
    print(f"  ✓ Routing time: {result['routing_time_ms']:.1f}ms")
    
    if result["patterns"]:
        print(f"\n  Top matched patterns:")
        for i, p in enumerate(result["patterns"], 1):
            print(f"    {i}. \"{p['text']}\" (score: {p['score']:.3f})")
    
    if result["knowledge"]:
        print(f"\n  Relevant knowledge ({len(result['knowledge'])} entries):")
        for k in result["knowledge"][:2]:
            print(f"    • {k['title']}")
            body_preview = k['body'][:80] + "..." if len(k['body']) > 80 else k['body']
            print(f"      {body_preview}")


def main():
    print("\n" + "=" * 60)
    print("  Graph-Structured Prompt Routing Demo")
    print("  Using RushDB Property Graph")
    print("=" * 60)

    router = QueryRouter(db)

    # Test queries spanning different domains
    test_queries = [
        "How do I fix a null pointer exception in Java?",
        "What colors work well for a modern dashboard?",
        "How much should I charge for consulting?",
        "My password reset email never arrived",
        "What's the best way to structure a REST API?",
        "Design a responsive grid layout",
        "How do I optimize email open rates?",
        "Set up Stripe payment processing",
    ]

    print(f"\nProcessing {len(test_queries)} test queries...\n")
    
    results = []
    domains_visited = set()
    
    for query in test_queries:
        result = router.route(query)
        print_routing_result(result)
        results.append(result)
        
        if result["domain"]:
            domains_visited.add(result["domain"])

    # Summary
    print(f"\n{'=' * 60}")
    print("  Routing Summary")
    print(f"{'=' * 60}")
    print(f"  Total queries processed: {len(results)}")
    print(f"  Successful routes: {sum(1 for r in results if r['domain'])}")
    print(f"  Domains visited: {sorted(domains_visited)}")
    
    avg_time = sum(r["routing_time_ms"] for r in results) / len(results)
    print(f"  Average routing time: {avg_time:.1f}ms")
    
    avg_confidence = sum(r["classification_confidence"] for r in results) / len(results)
    print(f"  Average confidence: {avg_confidence:.3f}")

    print(f"\n  Demo complete. Try modifying test_queries for more scenarios.\n")


if __name__ == "__main__":
    main()
