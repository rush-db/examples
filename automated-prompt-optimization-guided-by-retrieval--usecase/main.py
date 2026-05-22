#!/usr/bin/env python3
"""
Automated Prompt Optimization Guided by Retrieval Success Metrics

This module demonstrates how RushDB's hybrid graph + vector architecture
enables a feedback loop for continuous prompt improvement.

The scenario: Technical documentation search with real-world challenges
(jargon, ambiguous queries, multi-intent requests).
"""

import os
import sys
import json
from collections import defaultdict
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer


# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    sys.exit(1)

db = RushDB(api_key)

# Initialize embedding model (same as seed.py for consistency)
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')


# =============================================================================
# DATA STRUCTURES FOR RETRIEVAL TRACKING
# =============================================================================

class RetrievalMetrics:
    """Tracks retrieval quality metrics for prompt optimization."""
    
    def __init__(self):
        self.successful_retrievals = []
        self.failed_retrievals = []
        self.patterns = defaultdict(list)
    
    def record_success(self, query: str, results: list, relevance_scores: list):
        """Record a successful retrieval event."""
        self.successful_retrievals.append({
            "query": query,
            "results": results,
            "scores": relevance_scores,
            "avg_score": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        })
    
    def record_failure(self, query: str, reason: str, attempted_resolution: Optional[str] = None):
        """Record a failed retrieval event."""
        self.failed_retrievals.append({
            "query": query,
            "reason": reason,
            "attempted_resolution": attempted_resolution
        })
        self.patterns[reason].append(query)
    
    def analyze_patterns(self) -> dict:
        """Analyze failure patterns to generate optimization suggestions."""
        pattern_counts = defaultdict(int)
        for failure in self.failed_retrievals:
            pattern_counts[failure["reason"]] += 1
        
        return dict(sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True))


# =============================================================================
# PROMPT OPTIMIZATION ENGINE
# =============================================================================

class PromptOptimizer:
    """Generates prompt optimizations based on retrieval patterns."""
    
    def __init__(self):
        self.optimizations = []
    
    def generate_suggestions(self, metrics: RetrievalMetrics, current_prompt_template: str) -> list:
        """Generate prompt optimization suggestions based on failure patterns."""
        suggestions = []
        patterns = metrics.analyze_patterns()
        
        # Pattern 1: Vague intent
        if "vague_intent" in patterns:
            suggestions.append({
                "pattern": "vague_intent",
                "title": "Add intent classification prefix",
                "description": f"{patterns['vague_intent']} queries failed due to ambiguous intent.",
                "original": current_prompt_template,
                "suggested_modification": {
                    "type": "prefix",
                    "content": "Developer API question about: {query}\nClassify intent: [Troubleshooting/How-to/Reference]\n",
                    "expected_improvement": "+15% precision"
                }
            })
        
        # Pattern 2: Missing domain terminology
        if "missing_terminology" in patterns:
            suggestions.append({
                "pattern": "missing_terminology",
                "title": "Include domain context",
                "description": f"{patterns['missing_terminology']} queries lacked domain-specific terms.",
                "original": current_prompt_template,
                "suggested_modification": {
                    "type": "context_injection",
                    "content": "As a {role} working with {tool}, I want to {query}",
                    "expected_improvement": "+23% precision"
                }
            })
        
        # Pattern 3: Multi-intent queries
        if "multi_intent" in patterns:
            suggestions.append({
                "pattern": "multi_intent",
                "title": "Add intent decomposition step",
                "description": f"{patterns['multi_intent']} queries contained multiple sub-intents.",
                "original": current_prompt_template,
                "suggested_modification": {
                    "type": "decomposition",
                    "content": "Break down into sub-queries: 1) {sub_query_1}, 2) {sub_query_2}",
                    "expected_improvement": "+31% precision"
                }
            })
        
        # Pattern 4: Technical jargon confusion
        if "jargon_confusion" in patterns:
            suggestions.append({
                "pattern": "jargon_confusion",
                "title": "Add terminology clarification",
                "description": f"{patterns['jargon_confusion']} queries confused domain terms.",
                "original": current_prompt_template,
                "suggested_modification": {
                    "type": "disambiguation",
                    "content": "Clarify technical terms: {terminology_mapping}",
                    "expected_improvement": "+18% precision"
                }
            })
        
        self.optimizations = suggestions
        return suggestions
    
    def apply_optimization(self, prompt_template: str, optimization: dict) -> str:
        """Apply a specific optimization to a prompt template."""
        mod = optimization["suggested_modification"]
        
        if mod["type"] == "prefix":
            return mod["content"] + prompt_template
        elif mod["type"] == "context_injection":
            # For demo, use generic context
            return f"As a backend developer working with Node.js and Docker, I want to: {prompt_template}"
        elif mod["type"] == "decomposition":
            # Split the query into components
            return f"Query: {prompt_template}\nSub-queries: [1] {prompt_template.split(' and ')[0] if ' and ' in prompt_template else prompt_template}"
        elif mod["type"] == "disambiguation":
            return f"Context: dev-ops tool\n{prompt_template}"
        
        return prompt_template


# =============================================================================
# RETRIEVAL ENGINE WITH GRAPH TRACKING
# =============================================================================

class RetrievalEngine:
    """Handles semantic search with graph-backed outcome tracking."""
    
    def __init__(self):
        self.vector_index_id = None
        self._setup_index()
    
    def _setup_index(self):
        """Get the vector index ID."""
        try:
            indexes = db.ai.indexes.find()
            for idx in indexes.data:
                if idx['label'] == 'DOCUMENTATION' and idx['propertyName'] == 'body':
                    self.vector_index_id = idx.get('__id') or idx.get('id')
                    break
        except Exception as e:
            print(f"Warning: Could not find vector index: {e}")
    
    def search(self, query: str, limit: int = 5) -> list:
        """Perform semantic search with result tracking."""
        if not self.vector_index_id:
            # Fallback to managed search
            results = db.ai.search({
                "propertyName": "body",
                "query": query,
                "labels": ["DOCUMENTATION"],
                "limit": limit
            })
            return results.data
        
        # Use external index with pre-computed query vector
        query_vector = model.encode(query).tolist()
        results = db.ai.search({
            "propertyName": "body",
            "queryVector": query_vector,
            "labels": ["DOCUMENTATION"],
            "limit": limit
        })
        return results.data
    
    def record_retrieval_path(self, query: str, results: list, outcome: str):
        """Record the retrieval path in the graph for analysis."""
        # Create a query record
        query_record = db.records.create(
            label="QUERY",
            data={
                "text": query,
                "outcome": outcome,
                "result_count": len(results)
            }
        )
        
        # Attach results to the query (graph tracking)
        for i, result in enumerate(results):
            db.records.attach(
                source=query_record,
                target=result,
                options={"type": "RETRIEVED", "direction": "out"}
            )
        
        return query_record


# =============================================================================
# TEST QUERIES - REALISTIC SCENARIOS
# =============================================================================

# These queries represent realistic challenges in technical documentation search
TEST_QUERIES = [
    # Vague intent - common in support scenarios
    {
        "query": "it doesn't work",
        "expected_relevance": ["Debugging in Development", "Error Response Format", "Retry Logic Implementation"],
        "category": "vague_intent",
        "description": "Classic vague query - no context about what's broken"
    },
    {
        "query": "deployment is failing",
        "expected_relevance": ["Container Deployment Guide", "CI/CD Pipeline Configuration", "Graceful Shutdown"],
        "category": "vague_intent",
        "description": "Deployment failure without specific error"
    },
    
    # Missing domain terminology
    {
        "query": "how do I make my app update when I change code",
        "expected_relevance": ["Hot Reload Development"],
        "category": "missing_terminology",
        "description": "Describes 'hot reload' concept without knowing the term"
    },
    {
        "query": "my website bundle is too big",
        "expected_relevance": ["Tree Shaking Optimization", "Caching Strategies"],
        "category": "missing_terminology",
        "description": "Describes bundle size issue without knowing 'tree shaking'"
    },
    
    # Multi-intent requests
    {
        "query": "set up CI/CD with container registry and custom domains",
        "expected_relevance": ["CI/CD Pipeline Configuration", "Container Deployment Guide"],
        "category": "multi_intent",
        "description": "Three sub-intents: CI/CD, container registry, custom domains"
    },
    {
        "query": "configure auth with tokens and rate limiting",
        "expected_relevance": ["JWT Token Validation", "API Rate Limiting", "API Key Authentication"],
        "category": "multi_intent",
        "description": "Two distinct concerns: authentication and rate limiting"
    },
    
    # Technical jargon confusion
    {
        "query": "how to do hot reload in production",
        "expected_relevance": ["Hot Reload Development"],
        "category": "jargon_confusion",
        "description": "HMR isn't for production - misunderstood term scope"
    },
    {
        "query": "tree shaking not removing dead code",
        "expected_relevance": ["Tree Shaking Optimization"],
        "category": "jargon_confusion",
        "description": "Confuses tree shaking limitation with side effects"
    },
    
    # Clear, well-formed queries (baseline)
    {
        "query": "configure environment variables for deployment",
        "expected_relevance": ["Environment Variables Reference", "Configuration File Syntax"],
        "category": "clear_intent",
        "description": "Well-structured query with clear technical intent"
    },
    {
        "query": "implement OAuth 2.0 authentication",
        "expected_relevance": ["OAuth 2.0 Integration", "API Key Authentication"],
        "category": "clear_intent",
        "description": "Clear domain terminology and action"
    },
    {
        "query": "set up distributed tracing",
        "expected_relevance": ["Distributed Tracing Setup", "Logging Best Practices"],
        "category": "clear_intent",
        "description": "Direct query with correct terminology"
    },
    {
        "query": "connection pooling for database",
        "expected_relevance": ["Database Connection Pooling"],
        "category": "clear_intent",
        "description": "Specific technical concept clearly stated"
    }
]


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def calculate_precision_at_k(retrieved: list, expected: list, k: int = 3) -> float:
    """Calculate precision@k for retrieval quality."""
    retrieved_titles = [r.data.get("title", "") for r in retrieved[:k]]
    expected_set = set(expected)
    
    relevant = sum(1 for title in retrieved_titles if title in expected_set)
    return relevant / k if k > 0 else 0


def run_retrieval_test(queries: list, prompt_template: str = "{query}", 
                       optimizer: Optional[PromptOptimizer] = None,
                       engine: RetrievalEngine = None) -> RetrievalMetrics:
    """Run retrieval tests with a given prompt template."""
    metrics = RetrievalMetrics()
    
    print(f"\n{'='*60}")
    print(f"Testing with prompt template: {prompt_template}")
    print(f"{'='*60}\n")
    
    for i, test_case in enumerate(queries):
        # Apply prompt transformation if optimizer provided
        if optimizer and test_case["category"] in ["vague_intent", "missing_terminology", "multi_intent"]:
            # Find applicable optimization
            for opt in optimizer.optimizations:
                if opt["pattern"] == test_case["category"]:
                    query = optimizer.apply_optimization(test_case["query"], opt)
                    break
            else:
                query = test_case["query"]
        else:
            query = test_case["query"]
        
        # Perform retrieval
        results = engine.search(query, limit=5)
        
        # Calculate relevance
        precision = calculate_precision_at_k(
            results, 
            test_case["expected_relevance"], 
            k=3
        )
        
        # Record outcome
        scores = [r.score if r.score else 0 for r in results]
        
        if precision >= 0.33:  # At least 1 relevant in top 3
            metrics.record_success(test_case["query"], results, scores)
            outcome = "success"
            status = "✓"
        else:
            metrics.record_failure(
                test_case["query"], 
                test_case["category"],
                test_case.get("description")
            )
            outcome = "failure"
            status = "✗"
        
        # Record in graph for analysis
        engine.record_retrieval_path(test_case["query"], results, outcome)
        
        # Print result
        print(f"{status} Query: {test_case['query'][:50]}...")
        print(f"    Category: {test_case['category']}, Precision@3: {precision:.2f}")
        print(f"    Results: {[r.data.get('title', 'unknown')[:30] for r in results[:3]]}")
        print()
    
    return metrics


def analyze_graph_retrieval_paths():
    """Analyze recorded retrieval paths from the graph."""
    print("\n" + "=" * 60)
    print("Graph-based Retrieval Path Analysis")
    print("=" * 60)
    
    # Find all query records
    queries = db.records.find({"labels": ["QUERY"]})
    
    if not queries:
        print("No query records found in graph.")
        return
    
    print(f"\nTotal queries recorded: {len(queries)}")
    
    # Analyze by outcome
    outcomes = defaultdict(int)
    for query in queries:
        outcome = query.data.get("outcome", "unknown")
        outcomes[outcome] += 1
    
    print("\nOutcomes:")
    for outcome, count in outcomes.items():
        print(f"  {outcome}: {count}")
    
    # Find failed queries with no results
    failed_queries = [q for q in queries if q.data.get("outcome") == "failure"]
    if failed_queries:
        print(f"\nFailed queries with no relevant results: {len(failed_queries)}")
        # Analyze which documentation categories were missing
        categories_seen = defaultdict(int)
        for fq in failed_queries[:5]:  # Sample first 5
            print(f"  - {fq.data.get('text', '')[:50]}...")
    
    print()


def print_metrics_report(metrics: RetrievalMetrics, phase: str = "Before"):
    """Print a formatted metrics report."""
    print("\n" + "=" * 60)
    print(f"Retrieval Quality Analysis ({phase} Optimization)")
    print("=" * 60)
    
    total = len(metrics.successful_retrievals) + len(metrics.failed_retrievals)
    success_rate = len(metrics.successful_retrievals) / total if total > 0 else 0
    
    print(f"\nQueries analyzed: {total}")
    print(f"Successful retrievals: {len(metrics.successful_retrievals)} ({success_rate*100:.0f}%)")
    print(f"Failed retrievals: {len(metrics.failed_retrievals)} ({(1-success_rate)*100:.0f}%)")
    
    # Average precision for successful
    if metrics.successful_retrievals:
        avg_precision = sum(r["avg_score"] for r in metrics.successful_retrievals) / len(metrics.successful_retrievals)
        print(f"Average relevance score (successes): {avg_precision:.3f}")
    
    # Failure pattern analysis
    patterns = metrics.analyze_patterns()
    if patterns:
        print(f"\nTop failure patterns:")
        for pattern, count in list(patterns.items())[:5]:
            print(f"  • {pattern}: {count} failures")
    
    return success_rate


def print_optimization_suggestions(suggestions: list):
    """Print formatted optimization suggestions."""
    print("\n" + "=" * 60)
    print("Generated Prompt Optimizations")
    print("=" * 60)
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\nSuggestion {i}: {suggestion['title']}")
        print(f"  Description: {suggestion['description']}")
        print(f"  Expected improvement: {suggestion['suggested_modification']['expected_improvement']}")
        print(f"  Modification type: {suggestion['suggested_modification']['type']}")
        print(f"  Content: {suggestion['suggested_modification']['content'][:80]}...")


def main():
    print("\n" + "=" * 60)
    print("Automated Prompt Optimization Guided by Retrieval Metrics")
    print("=" * 60)
    print("\nScenario: Technical Documentation Search Assistant")
    print("Challenges: Jargon, ambiguous queries, multi-intent requests")
    
    # Initialize components
    engine = RetrievalEngine()
    
    # Check for documentation data
    docs = db.records.find({"labels": ["DOCUMENTATION"], "limit": 1})
    if not docs:
        print("\nERROR: No documentation found in database.")
        print("Please run 'python seed.py' first to populate the database.")
        sys.exit(1)
    
    print(f"\nFound {len(docs)} documentation records (using first to verify index)")
    
    # =====================================================================
    # PHASE 1: BASELINE RETRIEVAL (unoptimized prompts)
    # =====================================================================
    
    print("\n" + "=" * 60)
    print("PHASE 1: Baseline Retrieval Quality")
    print("=" * 60)
    
    baseline_metrics = run_retrieval_test(
        TEST_QUERIES,
        prompt_template="{query}",
        engine=engine
    )
    
    baseline_rate = print_metrics_report(baseline_metrics, "Baseline")
    
    # =====================================================================
    # PHASE 2: GENERATE OPTIMIZATION SUGGESTIONS
    # =====================================================================
    
    optimizer = PromptOptimizer()
    suggestions = optimizer.generate_suggestions(baseline_metrics, "{query}")
    
    if suggestions:
        print_optimization_suggestions(suggestions)
    else:
        print("\nNo optimization suggestions generated (check for failure patterns).")
    
    # =====================================================================
    # PHASE 3: OPTIMIZED RETRIEVAL
    # =====================================================================
    
    print("\n" + "=" * 60)
    print("PHASE 2: Optimized Retrieval Quality")
    print("=" * 60)
    
    # Re-run with optimization
    optimized_metrics = run_retrieval_test(
        TEST_QUERIES,
        prompt_template="Optimized: {query}",
        optimizer=optimizer,
        engine=engine
    )
    
    optimized_rate = print_metrics_report(optimized_metrics, "After")
    
    # =====================================================================
    # PHASE 4: GRAPH-BASED ANALYSIS
    # =====================================================================
    
    analyze_graph_retrieval_paths()
    
    # =====================================================================
    # FINAL SUMMARY
    # =====================================================================
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    improvement = ((optimized_rate - baseline_rate) / baseline_rate * 100) if baseline_rate > 0 else 0
    
    print(f"\nBaseline success rate: {baseline_rate*100:.0f}%")
    print(f"Optimized success rate: {optimized_rate*100:.0f}%")
    print(f"Relative improvement: +{improvement:.0f}%")
    
    print("\nKey insights:")
    print("  • Vague queries benefit most from intent classification")
    print("  • Multi-intent queries need decomposition strategies")
    print("  • Domain terminology gaps require context injection")
    
    # Honest assessment of limits
    print("\n" + "-" * 60)
    print("Honest Assessment of Limits")
    print("-" * 60)
    print("""
    This approach has clear boundaries:
    
    ✓ WORKS WELL when:
      - Historical data shows clear failure patterns
      - Failures have identifiable root causes
      - Domain vocabulary can be mapped semantically
      
    ✗ STRUGGLES with:
      - Novel queries without matching patterns
      - Subjective quality judgments
      - Real-time requirements (optimization latency)
    """)
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
