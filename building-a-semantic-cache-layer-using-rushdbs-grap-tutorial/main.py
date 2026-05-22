"""
Building a Semantic Cache Layer Using RushDB's Graph Storage

A complete, runnable tutorial demonstrating how to build a semantic cache
from scratch with RushDB.

This code covers:
- Embedding generation (OpenAI or local model)
- Node storage with inline vectors
- Graph edge creation for related entries
- Retrieval-by-similarity using RushDB's AI search
- TTL-based invalidation
- Contextual invalidation via edge pruning
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Application configuration loaded from environment."""
    
    RUSHDB_API_KEY = os.getenv("RUSHDB_API_KEY")
    RUSHDB_URL = os.getenv("RUSHDB_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
    DEFAULT_TTL_SECONDS = int(os.getenv("DEFAULT_TTL_SECONDS", "3600"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.90"))
    MAX_SIMILAR_LINKS = int(os.getenv("MAX_SIMILAR_LINKS", "5"))


# =============================================================================
# EMBEDDING PROVIDERS
# =============================================================================

class EmbeddingProvider:
    """Manages embedding generation for query text."""
    
    def __init__(self, provider_type: str, api_key: Optional[str] = None):
        self.provider_type = provider_type
        self._client = None
        self._model = None
        
        if provider_type == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required for OpenAI embeddings")
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
            self.model_name = "text-embedding-ada-002"
            self.dimensions = 1536
        elif provider_type == "local":
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            self.model_name = "all-MiniLM-L6-v2"
            test_emb = self._model.encode("test")
            self.dimensions = len(test_emb)
        else:
            raise ValueError(f"Unknown embedding provider: {provider_type}")
    
    def generate(self, text: str) -> List[float]:
        """Generate embedding for the given text."""
        if self.provider_type == "openai":
            response = self._client.embeddings.create(
                input=text,
                model=self.model_name
            )
            return response.data[0].embedding
        else:
            return self._model.encode(text).tolist()


# =============================================================================
# SEMANTIC CACHE CLASS
# =============================================================================

class SemanticCache:
    """
    A semantic cache that stores LLM query/response pairs and retrieves
    similar entries using vector similarity search.
    
    Key features:
    - Stores entries with embedded query vectors
    - Links related entries via graph edges (SEMANTICALLY_SIMILAR)
    - Supports TTL-based expiration
    - Supports contextual invalidation via edge pruning
    """
    
    def __init__(self, db: RushDB, embedding_provider: EmbeddingProvider):
        self.db = db
        self.embedding = embedding_provider
        self.ttl_seconds = Config.DEFAULT_TTL_SECONDS
        self.similarity_threshold = Config.SIMILARITY_THRESHOLD
        self.max_similar_links = Config.MAX_SIMILAR_LINKS
    
    def _is_entry_valid(self, entry) -> bool:
        """Check if a cache entry is still valid based on TTL."""
        created_at_str = entry.data.get("created_at")
        if not created_at_str:
            return False
        
        try:
            created_at = datetime.fromisoformat(created_at_str)
            age = datetime.now() - created_at
            ttl = int(entry.data.get("ttl_seconds", self.ttl_seconds))
            return age < timedelta(seconds=ttl)
        except (ValueError, TypeError):
            return False
    
    def lookup(self, query_text: str, min_similarity: float = None) -> Optional[Dict[str, Any]]:
        """
        Look up a query in the semantic cache.
        
        Returns the cached entry if found with sufficient similarity and valid TTL,
        or None if no suitable match exists.
        """
        threshold = min_similarity or self.similarity_threshold
        
        # Generate embedding for the query
        query_embedding = self.embedding.generate(query_text)
        
        # Search for similar entries
        results = self.db.ai.search({
            "propertyName": "query_text",
            "queryVector": query_embedding,
            "labels": ["CacheEntry"],
            "limit": 10
        }).data
        
        # Find the best valid match
        best_match = None
        best_score = 0.0
        
        for result in results:
            if result.score >= threshold and self._is_entry_valid(result):
                if result.score > best_score:
                    best_score = result.score
                    best_match = result
        
        if best_match:
            return {
                "entry": best_match,
                "score": best_score,
                "is_cache_hit": True
            }
        
        return None
    
    def store(
        self,
        query_text: str,
        response_text: str,
        model: str = "gpt-4",
        tokens_used: int = 0,
        context_tags: List[str] = None,
        ttl_seconds: int = None
    ) -> Dict[str, Any]:
        """
        Store a new entry in the semantic cache.
        
        Automatically links the new entry to semantically similar existing entries.
        """
        ttl = ttl_seconds or self.ttl_seconds
        tags = context_tags or []
        
        # Generate embedding
        embedding = self.embedding.generate(query_text)
        
        # Create the cache entry with inline vector
        new_entry = self.db.records.create(
            label="CacheEntry",
            data={
                "query_text": query_text,
                "response_text": response_text,
                "created_at": datetime.now().isoformat(),
                "ttl_seconds": ttl,
                "model": model,
                "tokens_used": tokens_used,
                "context_tags": tags
            },
            vectors=[{"propertyName": "query_text", "vector": embedding}]
        )
        
        # Find similar entries and create graph edges
        similar_results = self.db.ai.search({
            "propertyName": "query_text",
            "queryVector": embedding,
            "labels": ["CacheEntry"],
            "limit": self.max_similar_links
        }).data
        
        linked_count = 0
        for similar_entry in similar_results:
            # Don't link to self
            if similar_entry.id == new_entry.id:
                continue
            
            # Only link entries with sufficient similarity
            if similar_entry.score >= 0.7:
                self.db.records.attach(
                    source=new_entry,
                    target=similar_entry,
                    options={"type": "SEMANTICALLY_SIMILAR"}
                )
                linked_count += 1
        
        return {
            "entry": new_entry,
            "linked_entries": linked_count,
            "is_cache_hit": False
        }
    
    def invalidate_by_ttl(self) -> List[str]:
        """
        Find and mark expired cache entries.
        
        Note: RushDB doesn't auto-delete; this returns IDs of expired entries
        for the caller to handle.
        """
        all_entries = self.db.records.find({
            "labels": ["CacheEntry"]
        })
        
        expired_ids = []
        for entry in all_entries.data:
            if not self._is_entry_valid(entry):
                expired_ids.append(entry.id)
        
        return expired_ids
    
    def prune_context_edges(
        self,
        entry_id: str,
        valid_context_tags: List[str]
    ) -> int:
        """
        Remove SEMANTICALLY_SIMILAR edges from an entry to entries
        that don't share any context tags.
        
        This implements contextual invalidation - when the context for a
        cached entry changes, we prune links to entries in different contexts.
        
        Returns the number of edges pruned.
        """
        # Find the entry
        entry = self.db.records.find_by_id(entry_id)
        if not entry:
            return 0
        
        # Find all entries linked via SEMANTICALLY_SIMILAR
        related = self.db.records.find({
            "labels": ["CacheEntry"],
            "where": {
                "CacheEntry": {
                    "$relation": {
                        "type": "SEMANTICALLY_SIMILAR",
                        "direction": "out"
                    },
                    "$id": entry_id
                }
            }
        })
        
        pruned_count = 0
        for related_entry in related.data:
            related_tags = related_entry.data.get("context_tags", [])
            
            # Check if any context tags overlap
            has_overlap = any(tag in valid_context_tags for tag in related_tags)
            
            if not has_overlap:
                # Prune the edge - entries are contextually incompatible
                self.db.records.detach(
                    source=entry,
                    target=related_entry,
                    options={"type": "SEMANTICALLY_SIMILAR"}
                )
                pruned_count += 1
        
        return pruned_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache."""
        all_entries = self.db.records.find({
            "labels": ["CacheEntry"]
        })
        
        total = len(all_entries.data)
        valid = sum(1 for e in all_entries.data if self._is_entry_valid(e))
        expired = total - valid
        
        # Count edges
        edge_count = 0
        for entry in all_entries.data:
            related = self.db.records.find({
                "labels": ["CacheEntry"],
                "where": {
                    "CacheEntry": {
                        "$relation": {
                            "type": "SEMANTICALLY_SIMILAR",
                            "direction": "out"
                        },
                        "$id": entry.id
                    }
                }
            })
            edge_count += len(related.data)
        
        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "total_edges": edge_count
        }


# =============================================================================
# DEMONSTRATION FUNCTIONS
# =============================================================================

def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_cache_result(result: Dict[str, Any], query: str):
    """Print a formatted cache lookup result."""
    print(f"[•] Testing query: \"{query[:50]}{'...' if len(query) > 50 else ''}\"")
    
    if result["is_cache_hit"]:
        entry = result["entry"]
        print(f"    ↳ Cache HIT! Found: \"{entry.data['query_text'][:40]}...\"")
        print(f"       Similarity: {result['score']:.2f}")
        print(f"       Model: {entry.data.get('model', 'N/A')} | "
              f"Tokens: {entry.data.get('tokens_used', 'N/A')} | "
              f"Tags: {', '.join(entry.data.get('context_tags', []))}")
    else:
        print(f"    ↳ Cache MISS - No similar entry found")
        if "linked_entries" in result:
            print(f"    ↳ Stored new cache entry (linked to {result['linked_entries']} similar entries)")


# =============================================================================
# MAIN TUTORIAL
# =============================================================================

def main():
    """Run the complete semantic cache tutorial demonstration."""
    
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "Building a Semantic Cache Layer" + " " * 16 + "║")
    print("║" + " " * 12 + "with RushDB's Graph Storage" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # ==========================================================================
    # STEP 1: Initialize RushDB and Embedding Provider
    # ==========================================================================
    
    print_header("Step 1: Initializing Semantic Cache")
    
    # Check API key
    if not Config.RUSHDB_API_KEY:
        print("❌ RUSHDB_API_KEY not found in environment")
        print("   Copy .env.example to .env and add your API key")
        sys.exit(1)
    
    # Initialize RushDB
    print("[*] Connecting to RushDB...")
    db = RushDB(Config.RUSHDB_API_KEY, url=Config.RUSHDB_URL)
    print("    ✓ RushDB connection established")
    
    # Initialize embedding provider
    print(f"[*] Initializing embedding provider ({Config.EMBEDDING_PROVIDER})...")
    try:
        embedding_provider = EmbeddingProvider(
            provider_type=Config.EMBEDDING_PROVIDER,
            api_key=Config.OPENAI_API_KEY
        )
        print(f"    ✓ Embedding provider ready (model: {embedding_provider.model_name})")
        print(f"    ✓ Embedding dimensions: {embedding_provider.dimensions}")
    except Exception as e:
        print(f"❌ Failed to initialize embedding provider: {e}")
        sys.exit(1)
    
    # Create the semantic cache
    cache = SemanticCache(db, embedding_provider)
    print("    ✓ SemanticCache instance created")
    
    # ==========================================================================
    # STEP 2: Cache Lookup Demo
    # ==========================================================================
    
    print_header("Step 2: Cache Lookup Demo")
    
    # Test queries with varying similarity to existing cache entries
    test_queries = [
        "How do I implement a Python decorator with arguments?",  # High similarity to seed data
        "What's the best way to handle async errors in Python?",   # Should hit similar
        "Help me debug Python 2 vs 3 print syntax issues",         # Moderate similarity
        "How to create a thread-safe singleton pattern?",          # Should miss
        "Explain Python generators and yield statements",          # Should hit similar
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i} ", end="")
        result = cache.lookup(query)
        print_cache_result(result, query)
        
        # If cache miss, store the entry (simulating a real LLM response)
        if not result:
            new_result = cache.store(
                query_text=query,
                response_text=f"[Simulated LLM response for: {query}]",
                model="gpt-4",
                tokens_used=250,
                context_tags=["python", "tutorial"]
            )
            result = new_result
            print(f"    ↳ Stored new cache entry (linked to {result['linked_entries']} similar entries)")
    
    # ==========================================================================
    # STEP 3: Cache Invalidation Demo
    # ==========================================================================
    
    print_header("Step 3: Cache Invalidation Demo")
    
    # 3a: TTL-based invalidation
    print("[1] TTL-Based Invalidation:\n")
    expired_ids = cache.invalidate_by_ttl()
    print(f"    ↳ Found {len(expired_ids)} entries past their TTL")
    
    if expired_ids:
        # Show a few examples
        for entry_id in expired_ids[:3]:
            entry = db.records.find_by_id(entry_id)
            if entry:
                created = entry.data.get("created_at", "unknown")
                ttl = entry.data.get("ttl_seconds", cache.ttl_seconds)
                print(f"    ↳ Entry '{entry.data.get('query_text', '')[:30]}...' ")
                print(f"       Created: {created}, TTL: {ttl}s")
        print(f"    ↳ (Run cache.store with expired entry ID to remove)")
    
    # 3b: Contextual invalidation via edge pruning
    print("\n[2] Contextual Invalidation (Edge Pruning):\n")
    
    # Find an entry to demonstrate pruning
    all_entries = db.records.find({"labels": ["CacheEntry"]})
    
    if all_entries.data:
        # Pick an entry and change its context
        sample_entry = all_entries.data[0]
        original_tags = sample_entry.data.get("context_tags", [])
        
        print(f"    ↳ Sample entry tags: {original_tags}")
        print(f"    ↳ Updating context to: ['deprecated', 'old-api']")
        
        # Update the entry's context tags
        db.records.update(
            record_id=sample_entry.id,
            data={"context_tags": ["deprecated", "old-api"]}
        )
        
        # Prune edges to entries that don't share the new context
        pruned = cache.prune_context_edges(
            entry_id=sample_entry.id,
            valid_context_tags=["deprecated", "old-api"]
        )
        
        print(f"    ↳ Pruned {pruned} edges to contextually incompatible entries")
        print(f"    ↳ Entry now only linked to entries with overlapping context")
    
    # ==========================================================================
    # STEP 4: Graph Statistics
    # ==========================================================================
    
    print_header("Step 4: Cache Statistics")
    
    stats = cache.get_cache_stats()
    print(f"    Total CacheEntries: {stats['total_entries']}")
    print(f"    Valid (non-expired): {stats['valid_entries']}")
    print(f"    Expired (TTL passed): {stats['expired_entries']}")
    print(f"    Total SEMANTICALLY_SIMILAR edges: {stats['total_edges']}")
    
    # ==========================================================================
    # STEP 5: Graph Traversal Demo
    # ==========================================================================
    
    print_header("Step 5: Graph Traversal Demo")
    
    # Find an entry with linked neighbors and traverse
    for entry in all_entries.data[:1]:
        related = db.records.find({
            "labels": ["CacheEntry"],
            "where": {
                "CacheEntry": {
                    "$relation": {
                        "type": "SEMANTICALLY_SIMILAR",
                        "direction": "out"
                    },
                    "$id": entry.id
                }
            }
        })
        
        print(f"    Entry: \"{entry.data.get('query_text', '')[:40]}...\"")
        print(f"    Linked to {len(related.data)} semantically similar entries:\n")
        
        for rel in related.data[:3]:
            print(f"      → \"{rel.data.get('query_text', '')[:40]}...\"")
            print(f"        Similarity: {rel.score:.2f}")
            print(f"        Tags: {rel.data.get('context_tags', [])}")
            print()
    
    # ==========================================================================
    # COMPLETE!
    # ==========================================================================
    
    print_header("Tutorial Complete!")
    print("✓ You now have a working semantic cache with:")
    print("  • Vector-based similarity search")
    print("  • Graph edges linking related entries")
    print("  • TTL-based invalidation")
    print("  • Contextual edge pruning")
    print("\n📚 Resources:")
    print("  • RushDB Docs: https://docs.rushdb.com")
    print("  • GitHub: https://github.com/rush-db/examples")
    print()


if __name__ == "__main__":
    main()
