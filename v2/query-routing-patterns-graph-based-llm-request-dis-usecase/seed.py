"""
Seed script: Creates the routing graph with mock users, queries, models, and history.

This script is idempotent - safe to run multiple times. It checks for existing data
and skips seeding if the graph already has records.
"""
import os
import random
from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

# Initialize RushDB client
db = RushDB(os.getenv("RUSHDB_API_KEY"))

# Initialize embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list[float]:
    """Generate embedding vector for text."""
    return embedding_model.encode(text).tolist()

def check_seeded() -> bool:
    """Check if data already exists."""
    models = db.records.find({"labels": ["Model"], "limit": 1})
    return models.total > 0

def create_models(tx):
    """Create LLM models with performance metadata."""
    models = [
        {
            "name": "GPT-4",
            "provider": "OpenAI",
            "success_rate": 0.92,
            "avg_latency_ms": 4500,
            "cost_per_1k_tokens": 0.03,
            "max_tokens": 8192,
            "strengths": ["complex_reasoning", "code_generation", "analysis"],
            "weaknesses": ["speed", "cost"],
            "description": "Most capable model for complex reasoning and analysis"
        },
        {
            "name": "Claude-Haiku",
            "provider": "Anthropic",
            "success_rate": 0.65,
            "avg_latency_ms": 800,
            "cost_per_1k_tokens": 0.0001,
            "max_tokens": 4096,
            "strengths": ["speed", "simple_queries", "cost_efficiency"],
            "weaknesses": ["complex_reasoning", "long_context"],
            "description": "Fast, cost-effective model for simple queries"
        },
        {
            "name": "GPT-3.5-Turbo",
            "provider": "OpenAI",
            "success_rate": 0.78,
            "avg_latency_ms": 1200,
            "cost_per_1k_tokens": 0.002,
            "max_tokens": 4096,
            "strengths": ["balanced", "moderate_complexity"],
            "weaknesses": ["complex_analysis", "detailed_code"],
            "description": "Balanced model for moderate complexity tasks"
        },
        {
            "name": "Claude-Sonnet",
            "provider": "Anthropic",
            "success_rate": 0.88,
            "avg_latency_ms": 2500,
            "cost_per_1k_tokens": 0.003,
            "max_tokens": 200000,
            "strengths": ["long_context", "analysis", "reasoning"],
            "weaknesses": ["simple_tasks_cost"],
            "description": "Excellent for long documents and analysis tasks"
        }
    ]
    
    created = []
    for m in models:
        # Generate embedding for model description
        emb = get_embedding(m["description"])
        record = db.records.create(
            label="Model",
            data=m,
            vectors=[{"propertyName": "description", "vector": emb}],
            transaction=tx
        )
        created.append(record)
        print(f"  ✓ Created model: {m['name']}")
    
    return created

def create_users(tx):
    """Create users with different routing preferences."""
    users = [
        {"name": "alice", "preference": "quality", "tier": "premium"},
        {"name": "bob", "preference": "cost", "tier": "basic"},
        {"name": "charlie", "preference": "speed", "tier": "pro"},
        {"name": "diana", "preference": "balanced", "tier": "pro"},
        {"name": "eve", "preference": "cost", "tier": "basic"}
    ]
    
    created = []
    for u in users:
        record = db.records.create(label="User", data=u, transaction=tx)
        created.append(record)
        print(f"  ✓ Created user: {u['name']}")
    
    return created

def create_query_history(users: list, models: list, tx):
    """Create historical query data with routing outcomes."""
    
    # Query templates with complexity levels
    queries = [
        # Simple queries (low complexity)
        ("What's the weather today?", "simple", 0.1),
        ("Remind me to call mom", "simple", 0.1),
        ("Add milk to my shopping list", "simple", 0.1),
        ("What time is it?", "simple", 0.05),
        ("Play some music", "simple", 0.1),
        ("Convert 100 dollars to euros", "simple", 0.15),
        ("Define photosynthesis", "simple", 0.2),
        
        # Medium complexity
        ("Explain how vaccines work", "medium", 0.4),
        ("Write a thank you email to my team", "medium", 0.35),
        ("Summarize the key points of this article", "medium", 0.45),
        ("Compare REST and GraphQL APIs", "medium", 0.5),
        ("Write a Python function to validate email", "medium", 0.4),
        ("Explain the water cycle", "medium", 0.35),
        
        # High complexity
        ("Analyze the impact of quantum computing on cryptography", "complex", 0.85),
        ("Explain quantum entanglement in detail", "complex", 0.9),
        ("Design a distributed system for handling 1M requests/second", "complex", 0.95),
        ("Write a comprehensive technical design document", "complex", 0.8),
        ("Debug this multi-threaded race condition", "complex", 0.88),
        ("Explain the proof of P vs NP problem", "complex", 0.92),
        
        # Moderate complexity
        ("Help me write a marketing strategy", "moderate", 0.55),
        ("Create a data analysis plan for my dataset", "moderate", 0.6),
        ("Explain machine learning basics", "moderate", 0.5),
        ("Write unit tests for this function", "moderate", 0.45),
        ("Review my code for security issues", "moderate", 0.58),
    ]
    
    # Map complexity to preferred models
    complexity_to_model_idx = {
        "simple": 1,      # Claude-Haiku (fast/cheap)
        "medium": 2,      # GPT-3.5-Turbo (balanced)
        "moderate": 0,    # GPT-4 (quality for moderate)
        "complex": 0      # GPT-4 (quality for complex)
    }
    
    total_created = 0
    for i, (text, complexity, complexity_score) in enumerate(queries):
        # Randomly vary success rate slightly per query
        base_model_idx = complexity_to_model_idx[complexity]
        preferred_model = models[base_model_idx]
        
        # Sometimes route to different model (realistic distribution)
        if random.random() < 0.2:
            chosen_model = random.choice(models)
        else:
            chosen_model = preferred_model
        
        # Determine success based on model suitability
        model_complexity = complexity_to_model_idx[complexity]
        chosen_complexity = models.index(chosen_model)
        
        # Model is appropriate if it can handle the complexity level
        if chosen_complexity >= model_complexity:
            base_success = chosen_model["success_rate"] + random.uniform(-0.05, 0.05)
        else:
            base_success = chosen_model["success_rate"] - random.uniform(0.15, 0.25)
        
        success = base_success > 0.7
        
        query_data = {
            "text": text,
            "complexity_level": complexity,
            "complexity_score": complexity_score,
            "success": success,
            "latency_ms": int(chosen_model["avg_latency_ms"] * random.uniform(0.8, 1.2))
        }
        
        emb = get_embedding(text)
        query_record = db.records.create(
            label="Query",
            data=query_data,
            vectors=[{"propertyName": "text", "vector": emb}],
            transaction=tx
        )
        
        # Link to a random user
        user = random.choice(users)
        db.records.attach(
            source=user,
            target=query_record,
            options={"type": "QUERIED", "direction": "out"},
            transaction=tx
        )
        
        # Link to the chosen model
        db.records.attach(
            source=query_record,
            target=chosen_model,
            options={"type": "ROUTED_TO", "direction": "out"},
            transaction=tx
        )
        
        total_created += 1
        if total_created % 10 == 0:
            print(f"  📝 Created {total_created} queries...")
    
    return total_created

def main():
    """Main seeding function."""
    print("\n=== RushDB Routing Graph Seeder ===\n")
    
    # Check if already seeded
    if check_seeded():
        print("⚠️  Data already exists. Skipping seed.")
        print("   Delete records manually or run 'python seed.py --force' to re-seed.\n")
        return
    
    print("🌱 Creating routing graph...")
    
    with db.transactions.begin() as tx:
        print("\n📦 Creating models...")
        models = create_models(tx)
        
        print("\n👥 Creating users...")
        users = create_users(tx)
        
        print("\n📝 Creating query history...")
        query_count = create_query_history(users, models, tx)
        
        print(f"\n✅ Seeding complete!")
        print(f"   • {len(models)} models")
        print(f"   • {len(users)} users")
        print(f"   • {query_count} queries")
        print(f"   • Historical routing patterns captured\n")

if __name__ == "__main__":
    main()
