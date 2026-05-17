"""
Query Routing Engine: Demonstrates RushDB graph-based LLM request distribution.


This module shows how RushDB's property graph enables intelligent routing decisions
by traversing User → Query → Model relationships and comparing performance metrics.
"""
import os
from typing import Optional
from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

load_dotenv()

# Initialize RushDB client
db = RushDB(os.getenv("RUSHDB_API_KEY"))

# Initialize embedding model for query vectorization
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


def get_embedding(text: str) -> list[float]:
    """Generate embedding vector for text."""
    return embedding_model.encode(text).tolist()


def estimate_complexity(query_text: str, recent_queries: list) -> float:
    """
    Estimate query complexity based on:
    - Text length and vocabulary
    - Presence of technical keywords
    - Comparison to user's recent query patterns
    """
    # Technical complexity indicators
    technical_keywords = [
        'analyze', 'design', 'architecture', 'algorithm', 'distributed',
        'quantum', 'cryptography', 'optimize', 'debug', 'implement',
        'complex', 'advanced', 'comprehensive', 'detailed', 'explain'
    ]
    
    words = query_text.lower().split()
    word_count = len(words)
    technical_count = sum(1 for w in words if w in technical_keywords)
    
    # Base complexity from keywords
    keyword_complexity = min(technical_count * 0.1, 0.4)
    
    # Length factor (longer queries tend to be more complex)
    length_complexity = min(word_count * 0.01, 0.3)
    
    # Historical context: compare to user's recent queries
    historical_complexity = 0.0
    if recent_queries:
        avg_recent = sum(q.get("complexity_score", 0) for q in recent_queries) / len(recent_queries)
        historical_complexity = avg_recent * 0.2
    
    base_complexity = keyword_complexity + length_complexity + historical_complexity
    
    return min(base_complexity, 1.0)


def get_user(username: str) -> Optional[dict]:
    """Find user by name."""
    result = db.records.find({"labels": ["User"], "where": {"name": username}})
    if result.total > 0:
        return result.data[0]
    return None


def get_user_recent_queries(user_id: str, limit: int = 10) -> list[dict]:
    """
    Traverse graph to find user's recent queries.
    
    RushDB traversal pattern: User → QUERIED → Query
    """
    result = db.records.find({
        "labels": ["Query"],
        "where": {
            "User": {"$id": {"$eq": user_id}}
        },
        "limit": limit,
        "orderBy": {"__createdAt": "desc"}
    })
    return result.data


def find_similar_queries(query_text: str, limit: int = 5) -> list[dict]:
    """
    Use vector similarity to find queries similar to the incoming query.
    
    This demonstrates RushDB's inline vector write pattern:
    - Queries already have embeddings stored
    - Search finds semantically similar historical queries
    """
    query_vector = get_embedding(query_text)
    
    # Semantic search across all historical queries
    results = db.ai.search({
        "propertyName": "text",
        "queryVector": query_vector,
        "labels": ["Query"],
        "limit": limit
    })
    
    return results.data



def get_model_success_for_similar_queries(similar_queries: list) -> dict:
    """
    Analyze which models succeeded on similar queries.
    
    RushDB traversal: Query → ROUTED_TO → Model
    This finds the models used for similar queries and their success rates.
    """
    model_stats = {}
    
    for query in similar_queries:
        # Find the model this query was routed to
        result = db.records.find({
            "labels": ["Model"],
            "where": {
                "Query": {"$id": {"$eq": query.id}}
            }
        })
        
        if result.total > 0:
            model = result.data[0]
            model_name = model.get("name")
            
            if model_name not in model_stats:
                model_stats[model_name] = {
                    "count": 0,
                    "successes": 0,
                    "model_record": model
                }
            
            model_stats[model_name]["count"] += 1
            if query.get("success"):
                model_stats[model_name]["successes"] += 1
    
    # Calculate success rates for each model
    for model_name, stats in model_stats.items():
        if stats["count"] > 0:
            stats["historical_success_rate"] = stats["successes"] / stats["count"]
    
    return model_stats


def select_model(
    complexity: float,
    model_stats: dict,
    user_preference: str = "balanced"
) -> dict:
    """
    Select the optimal model based on complexity and historical performance.
    
    Routing logic:
    - Low complexity (≤0.3): Prefer fast/cheap models unless history says otherwise
    - High complexity (≥0.7): Prefer capable models
    - User preference: Quality vs Cost vs Speed tradeoff
    """
    # Get all available models
    all_models = db.records.find({"labels": ["Model"]})
    
    if all_models.total == 0:
        raise ValueError("No models found. Run seed.py first.")
    
    model_candidates = {}
    
    for model in all_models.data:
        model_name = model.get("name")
        base_success_rate = model.get("success_rate", 0.5)
        
        # Adjust success rate based on historical performance for similar queries
        if model_name in model_stats:
            historical_rate = model_stats[model_name].get("historical_success_rate", base_success_rate)
            # Weight historical performance heavily (70% history, 30% base)
            effective_success = historical_rate * 0.7 + base_success_rate * 0.3
        else:
            effective_success = base_success_rate
        
        # Adjust based on complexity suitability
        complexity_adjustment = 0.0
        if complexity <= 0.3:
            # Low complexity: fast models get a boost
            if model.get("avg_latency_ms", 5000) < 1500:
                complexity_adjustment = 0.1
        elif complexity >= 0.7:
            # High complexity: capable models get a boost
            if model.get("max_tokens", 4096) >= 8000:
                complexity_adjustment = 0.15
        
        # Apply user preference weighting
        preference_multiplier = 1.0
        if user_preference == "cost":
            # Reduce score for expensive models
            cost = model.get("cost_per_1k_tokens", 0.01)
            preference_multiplier = 1.0 / (1 + cost * 50)
        elif user_preference == "speed":
            # Reduce score for slow models
            latency = model.get("avg_latency_ms", 1000)
            preference_multiplier = 1000 / (latency + 100)
        elif user_preference == "quality":
            # Reduce score for lower capability models
            if model.get("max_tokens", 4096) < 8000:
                preference_multiplier = 0.7
        
        score = (effective_success + complexity_adjustment) * preference_multiplier
        
        model_candidates[model_name] = {
            "model_record": model,
            "score": score,
            "effective_success_rate": effective_success,
            "complexity_adjustment": complexity_adjustment
        }
    
    # Select the model with highest score
    best_model_name = max(model_candidates, key=lambda k: model_candidates[k]["score"])
    best_model_data = model_candidates[best_model_name]
    
    return {
        "name": best_model_name,
        "model_record": best_model_data["model_record"],
        "score": best_model_data["score"],
        "effective_success_rate": best_model_data["effective_success_rate"],
        "reasoning": build_routing_reasoning(
            complexity,
            model_candidates,
            best_model_name,
            user_preference
        )
    }



def build_routing_reasoning(
    complexity: float,
    model_candidates: dict,
    selected_model: str,
    user_preference: str
) -> str:
    """Build human-readable explanation of routing decision."""
    parts = []
    
    # Complexity reasoning
    if complexity <= 0.3:
        parts.append("Low complexity query (≤0.3)")
    elif complexity <= 0.6:
        parts.append("Moderate complexity query (0.3-0.6)")
    else:
        parts.append("High complexity query (≥0.7)")
    
    # Model-specific reasoning
    selected = model_candidates[selected_model]
    if selected["effective_success_rate"] > 0.85:
        parts.append(f"{selected_model} shows strong historical success ({selected['effective_success_rate']:.0%})")
    
    # Preference reasoning
    if user_preference == "cost":
        parts.append("User prefers cost-optimized routing")
    elif user_preference == "speed":
        parts.append("User prefers low-latency responses")
    elif user_preference == "quality":
        parts.append("User prefers high-quality outputs")
    
    return "; ".join(parts)


def route_query(username: str, query_text: str) -> dict:
    """
    Main routing function: Select optimal model for a user's query.
    
    This demonstrates the complete routing pipeline:
    1. Get user context
    2. Analyze query complexity
    3. Find similar historical queries
    4. Analyze model performance on similar queries
    5. Select optimal model based on all factors
    """
    # Step 1: Get user
    user = get_user(username)
    if not user:
        raise ValueError(f"User '{username}' not found. Run seed.py first.")
    
    user_preference = user.get("preference", "balanced")
    
    # Step 2: Get user's recent query history (graph traversal)
    recent_queries = get_user_recent_queries(user.id)
    
    # Step 3: Estimate query complexity
    complexity = estimate_complexity(query_text, recent_queries)
    
    # Step 4: Find similar queries (vector similarity)
    similar_queries = find_similar_queries(query_text, limit=5)
    
    # Step 5: Analyze model performance on similar queries
    model_stats = get_model_success_for_similar_queries(similar_queries)
    
    # Step 6: Select optimal model
    selection = select_model(complexity, model_stats, user_preference)
    
    return {
        "user": user,
        "query": query_text,
        "complexity": complexity,
        "recent_query_count": len(recent_queries),
        "similar_query_count": len(similar_queries),
        "model_stats": model_stats,
        "selected_model": selection
    }


def print_routing_report(routing: dict):
    """Pretty print the routing decision."""
    print("\n" + "=" * 50)
    print("  RushDB Graph-Based LLM Router")
    print("=" * 50)
    
    print(f"\n📝 Query: \"{routing['query']}\"")
    print(f"👤 User: {routing['user'].get('name')} ({routing['user'].get('tier')} tier)")
    print(f"   Preference: {routing['user'].get('preference')}")
    
    print(f"\n📊 Analysis:")
    print(f"   • Complexity score: {routing['complexity']:.2f}")
    print(f"   • Recent queries analyzed: {routing['recent_query_count']}")
    print(f"   • Similar historical queries: {routing['similar_query_count']}")
    
    if routing['model_stats']:
        print(f"\n📈 Historical Model Performance:")
        for model_name, stats in routing['model_stats'].items():
            rate = stats.get('historical_success_rate', 0)
            count = stats.get('count', 0)
            print(f"   • {model_name}: {rate:.0%} success ({count} similar queries)")
    else:
        print(f"\n📈 Model Performance (from metadata):")
        all_models = db.records.find({"labels": ["Model"]})
        for model in all_models.data:
            print(f"   • {model.get('name')}: {model.get('success_rate'):.0%} success rate")
    
    selected = routing['selected_model']
    model = selected['model_record']
    
    print(f"\n🎯 ROUTING DECISION: {selected['name']}")
    print(f"   Reasoning: {selected['reasoning']}")
    print(f"   \n   Estimated metrics:")
    print(f"     • Success rate: {model.get('success_rate', 'N/A'):.0%}")
    print(f"     • Latency: ~{model.get('avg_latency_ms', 'N/A')}ms")
    print(f"     • Cost: ${model.get('cost_per_1k_tokens', 'N/A'):.4f}/1k tokens")
    print(f"     • Provider: {model.get('provider', 'N/A')}")
    
    print("\n" + "=" * 50 + "\n")


def demonstrate_graph_traversal():
    """Demonstrate the underlying graph structure."""
    print("\n🔍 Graph Structure Demonstration\n")
    print("-" * 40)
    
    # Show all models
    print("\n📦 Available Models:")
    models = db.records.find({"labels": ["Model"]})
    for m in models.data:
        print(f"   • {m.get('name')} ({m.get('provider')})")
        print(f"     - Success rate: {m.get('success_rate'):.0%}")
        print(f"     - Latency: {m.get('avg_latency_ms')}ms")
        print(f"     - Cost: ${m.get('cost_per_1k_tokens')}/1k tokens")
    
    # Show users
    print("\n👥 Users:")
    users = db.records.find({"labels": ["User"]})
    for u in users.data:
        print(f"   • {u.get('name')} (prefers: {u.get('preference')})")
    
    # Show sample queries for first user
    if users.total > 0:
        first_user = users.data[0]
        print(f"\n📝 Recent queries for {first_user.get('name')}:")
        queries = get_user_recent_queries(first_user.id, limit=3)
        for q in queries:
            success = "✅" if q.get("success") else "❌"
            print(f"   {success} \"{q.get('text', '')[:50]}...\"")
            print(f"      Complexity: {q.get('complexity_score', 0):.2f}")
    
    print("\n" + "-" * 40)


def main():
    """Run the routing demonstration."""
    print("\n" + "🌟" * 25)
    print("\n  Query Routing Patterns: Graph-Based LLM Request Distribution")
    print("  RushDB Use Case Demonstration\n")
    print("🌟" * 25)
    
    # First, show the graph structure
    demonstrate_graph_traversal()
    
    # Demo queries with different complexity levels
    demo_queries = [
        ("alice", "What's the weather like today?", "simple query"),
        ("alice", "Explain quantum entanglement in detail", "complex query"),
        ("bob", "Write a thank you email for my team", "moderate query"),
        ("charlie", "Design a distributed system for handling 1M requests/second", "highly complex"),
    ]
    
    for username, query, description in demo_queries:
        print(f"\n{'─' * 50}")
        print(f"  Test: {description}")
        print(f"{'─' * 50}")
        
        try:
            routing = route_query(username, query)
            print_routing_report(routing)
        except ValueError as e:
            print(f"\n❌ Error: {e}")
            print("   Make sure to run 'python seed.py' first.\n")


if __name__ == "__main__":
    main()
