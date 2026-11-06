"""
Seed script for the Semantic Cache tutorial.

Generates mock cache entries representing common LLM queries about
software development topics. This populates RushDB with realistic data
for testing the semantic cache layer.

Run this before main.py to have existing cache entries to work with.
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Sample data for realistic cache entries
SAMPLE_QUERIES = [
    {
        "query_text": "How do I implement a Python decorator with arguments?",
        "response_text": "A decorator with arguments wraps your decorator function in another function. Here's the pattern: def decorator_with_args(arg1, arg2): def decorator(func): @functools.wraps(func) def wrapper(*args, **kwargs): # pre-processing print(f'Decorating with {arg1}, {arg2}') result = func(*args, **kwargs) # post-processing return result return wrapper return decorator",
        "model": "gpt-4",
        "context_tags": ["python", "decorators", "advanced"]
    },
    {
        "query_text": "Explain Python decorators with examples",
        "response_text": "Decorators modify function behavior without changing their code. Basic syntax: @decorator_name before the function definition. Common use cases: logging, timing, authentication, and caching. Example: @log_calls def my_function(): pass",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "decorators", "beginner"]
    },
    {
        "query_text": "How to handle async errors in Python asyncio?",
        "response_text": "Use try/except within async functions. For multiple tasks, use asyncio.gather with return_exceptions=True to collect errors. Pattern: try: results = await asyncio.gather(*tasks, return_exceptions=True) except Exception as e: handle_error(e)",
        "model": "gpt-4",
        "context_tags": ["python", "async", "error-handling"]
    },
    {
        "query_text": "Python asyncio best practices for beginners",
        "response_text": "Key practices: 1) Use async/await consistently 2) Don't mix blocking and async code 3) Use asyncio.create_task() for concurrent tasks 4) Always close tasks properly with cancel() 5) Use asyncio.run() for the main entry point",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "async", "beginner"]
    },
    {
        "query_text": "How to implement a thread-safe singleton in Python?",
        "response_text": "Use the Borg pattern or thread-safe locking. Example with threading.Lock: _instance = None _lock = threading.Lock() def get_instance(): if _instance is None: with _lock: if _instance is None: _instance = Singleton() return _instance",
        "model": "gpt-4",
        "context_tags": ["python", "design-patterns", "threading"]
    },
    {
        "query_text": "Fix Python 2 vs 3 print syntax issues",
        "response_text": "Python 3 requires parentheses: print('Hello') instead of print 'Hello'. Use from __future__ import print_function for compatibility. For scripts, add: if sys.version_info[0] < 3: raw_input = input",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "compatibility", "migration"]
    },
    {
        "query_text": "How to profile Python code performance?",
        "response_text": "Use cProfile for function-level analysis: python -m cProfile -s cumtime script.py. For line-by-line, use line_profiler. For memory, use memory_profiler. Quick wins: time.time() wrapping, @functools.lru_cache for memoization.",
        "model": "gpt-4",
        "context_tags": ["python", "performance", "profiling"]
    },
    {
        "query_text": "When should I use dataclasses vs namedtuples in Python?",
        "response_text": "Use dataclasses when: you need mutable attributes, default values, type hints, or methods. Use namedtuple when: you want immutable objects, memory efficiency, or tuple unpacking. Dataclasses offer more flexibility; namedtuples are lighter.",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "dataclasses", "design"]
    },
    {
        "query_text": "How do context managers work in Python?",
        "response_text": "Context managers implement __enter__ and __exit__ methods. Use the contextlib module for simpler creation: @contextmanager def managed_resource(): setup() try: yield resource cleanup() finally: cleanup(). This ensures proper resource handling.",
        "model": "gpt-4",
        "context_tags": ["python", "context-managers", "resource-management"]
    },
    {
        "query_text": "Explain Python generators and when to use them",
        "response_text": "Generators use yield to produce values lazily. Benefits: memory efficiency, infinite sequences, pipeline processing. Use when processing large datasets or streams. Example: def count_up_to(n): i = 1 while i <= n: yield i; i += 1",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "generators", "iterators"]
    },
    {
        "query_text": "How to implement retry logic with exponential backoff?",
        "response_text": "Pattern: start with base delay, multiply by backoff factor each retry. Example: delay = base for attempt in range(max_retries): try: return action() except: sleep(delay); delay *= backoff_factor; raise after max attempts. Use tenacity library for robust implementation.",
        "model": "gpt-4",
        "context_tags": ["python", "resilience", "networking"]
    },
    {
        "query_text": "What's the difference between __str__ and __repr__ in Python?",
        "response_text": "__str__ is for end-users, readable representation. __repr__ is for developers, ideally reproducible. If __str__ is missing, __repr__ is used. Always implement __repr__ for debugging. Example: __repr__ = __str__ if they're identical.",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "magic-methods", "debugging"]
    },
    {
        "query_text": "How to properly type hint Python functions?",
        "response_text": "Use typing module for complex types: def func(name: str, ids: List[int], callback: Optional[Callable] = None) -> Dict[str, Any]. Use Union for multiple types, Any for dynamic. Enable mypy/pyright for static checking. Python 3.10+ supports | syntax.",
        "model": "gpt-4",
        "context_tags": ["python", "type-hints", "best-practices"]
    },
    {
        "query_text": "How to handle database connections in Python?",
        "response_text": "Use connection pooling with context managers. Pattern: with pool.connection() as conn: with conn.cursor() as cur: cur.execute('SELECT * FROM table') results = cur.fetchall(). For async code, use databases or asyncpg. Always close connections or return them to pool.",
        "model": "gpt-4",
        "context_tags": ["python", "databases", "connections"]
    },
    {
        "query_text": "Explain Python's GIL and when it matters",
        "response_text": "GIL (Global Interpreter Lock) prevents multiple threads from executing Python bytecode simultaneously. Matters for CPU-bound tasks (use multiprocessing). Doesn't matter for I/O-bound tasks (use threading). C extensions can release GIL.",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "threading", "performance"]
    },
    {
        "query_text": "How to write unit tests for Python async functions?",
        "response_text": "Use pytest-asyncio. Mark async tests with @pytest.mark.asyncio. Pattern: @pytest.mark.asyncio async def test_async_function(): result = await my_async_func(); assert result == expected. Use pytest.fixture with async def for async fixtures.",
        "model": "gpt-4",
        "context_tags": ["python", "testing", "async"]
    },
    {
        "query_text": "What's the best way to parse JSON in Python?",
        "response_text": "Use json module for standard parsing: json.loads(string) for JSON string, json.load(file) for files. For speed, use orjson or ujson. For validation, combine with jsonschema. Handle JSONDecodeError for malformed input.",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "json", "parsing"]
    },
    {
        "query_text": "How to implement a rate limiter in Python?",
        "response_text": "Use token bucket algorithm with threading.Lock or Redis. Pattern: bucket has max tokens, refills at rate. On request: if tokens >= cost: tokens -= cost; proceed else: wait. Libraries: limitador (Redis), ratelimit (decorator).",
        "model": "gpt-4",
        "context_tags": ["python", "rate-limiting", "api"]
    },
    {
        "query_text": "How to properly handle timezone-aware datetime in Python?",
        "response_text": "Use timezone from datetime module. Store as UTC, convert for display. Pattern: from datetime import datetime, timezone; utc_now = datetime.now(timezone.utc); local = utc_now.astimezone(pytz.timezone('US/Eastern')). Never use naive datetimes for timestamps.",
        "model": "gpt-3.5-turbo",
        "context_tags": ["python", "datetime", "timezone"]
    },
    {
        "query_text": "How to create a CLI tool with Python using argparse?",
        "response_text": "Use argparse: parser = argparse.ArgumentParser(description='My CLI'); parser.add_argument('input', help='Input file'); parser.add_argument('-v', '--verbose', action='store_true'); args = parser.parse_args(). Use subparsers for complex CLIs with multiple commands.",
        "model": "gpt-4",
        "context_tags": ["python", "cli", "argparse"]
    }
]


def get_embedding_provider():
    """Determine which embedding provider to use."""
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
    
    if embedding_provider == "local":
        print("[*] Using local SentenceTransformers embeddings")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return lambda text: model.encode(text).tolist()
    else:
        print("[*] Using OpenAI embeddings")
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return lambda text: client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        ).data[0].embedding


def seed_cache_entries():
    """Seed RushDB with sample cache entries."""
    
    # Check for API key
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("❌ RUSHDB_API_KEY not found in environment")
        print("   Copy .env.example to .env and add your API key")
        sys.exit(1)
    
    # Initialize RushDB
    db = RushDB(api_key, url=os.getenv("RUSHDB_URL"))
    
    print("\n🌱 Seeding Semantic Cache with Sample Data\n")
    print("-" * 50)
    
    # Check existing entries
    existing = db.records.find({
        "labels": ["CacheEntry"],
        "limit": 1
    })
    
    if existing.data:
        print(f"[*] Found {len(existing.data)} existing CacheEntry(ies)")
        response = input("[*] Continue seeding? This will add more entries. (y/N): ")
        if response.lower() != 'y':
            print("[*] Seeding cancelled")
            return
    
    # Get embedding function
    try:
        generate_embedding = get_embedding_provider()
    except Exception as e:
        print(f"❌ Failed to initialize embedding provider: {e}")
        sys.exit(1)
    
    print("\n[*] Generating embeddings and creating cache entries...")
    print("-" * 50)
    
    created_entries = []
    
    for i, query_data in enumerate(SAMPLE_QUERIES):
        try:
            # Generate embedding
            embedding = generate_embedding(query_data["query_text"])
            
            # Create cache entry with inline vector
            # Vary the created_at time for testing TTL scenarios
            age_hours = random.randint(0, 48)
            created_at = datetime.now() - timedelta(hours=age_hours)
            
            entry = db.records.create(
                label="CacheEntry",
                data={
                    "query_text": query_data["query_text"],
                    "response_text": query_data["response_text"],
                    "created_at": created_at.isoformat(),
                    "ttl_seconds": 3600,  # 1 hour TTL
                    "model": query_data["model"],
                    "tokens_used": random.randint(100, 500),
                    "context_tags": query_data["context_tags"]
                },
                vectors=[{"propertyName": "query_text", "vector": embedding}]
            )
            
            created_entries.append(entry)
            
            # Progress indicator
            if (i + 1) % 5 == 0:
                print(f"[*] Created {i + 1}/{len(SAMPLE_QUERIES)} cache entries...")
            
        except Exception as e:
            print(f"❌ Failed to create entry {i + 1}: {e}")
            continue
    
    print(f"\n✅ Created {len(created_entries)} cache entries\n")
    
    # Now create semantic links between entries
    print("[*] Creating semantic links between related entries...")
    
    for i, entry in enumerate(created_entries):
        # Get embedding for this entry
        entry_text = entry.data["query_text"]
        embedding = generate_embedding(entry_text)
        
        # Find similar entries
        similar = db.ai.search({
            "propertyName": "query_text",
            "queryVector": embedding,
            "labels": ["CacheEntry"],
            "limit": 3
        }).data
        
        # Link to similar entries
        for similar_entry in similar:
            if similar_entry.id != entry.id and similar_entry.score >= 0.7:
                try:
                    db.records.attach(
                        source=entry,
                        target=similar_entry,
                        options={"type": "SEMANTICALLY_SIMILAR"}
                    )
                except Exception:
                    # Edge might already exist
                    pass
        
        if (i + 1) % 5 == 0:
            print(f"[*] Linked {i + 1}/{len(created_entries)} entries...")
    
    print("\n✅ Semantic links created\n")
    
    # Print summary
    print("-" * 50)
    print("📊 Seeding Summary:\n")
    print(f"   Total CacheEntries: {len(created_entries)}")
    print(f"   Semantic links: Created between similar topics")
    print(f"   Age distribution: 0-48 hours randomized")
    print("-" * 50)
    print("\n✨ Seeding complete! Run main.py to test the cache.\n")


if __name__ == "__main__":
    seed_cache_entries()
