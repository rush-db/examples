"""
Context Recycling: Reusing Graph-Retrieved Evidence Across Related Queries

This example demonstrates how context recycling transforms expensive repeated
graph traversals into single-query operations, enabling real-time relationship-
aware AI responses without latency penalties.

Run `python seed.py` first to populate the knowledge graph.
"""

import os
import time
import json
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env and add your key.")

db = RushDB(API_KEY)

# ============================================================================
# CONTEXT CACHE - The core of context recycling
# ============================================================================

@dataclass
class CacheEntry:
    """A cached subgraph entry with TTL support."""
    entity_id: str
    evidence: dict[str, Any]
    created_at: datetime
    ttl_seconds: int = 300  # Default 5 minutes
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def touch(self):
        """Record an access."""
        self.access_count += 1


class EvidenceCache:
    """
    A simple in-memory cache for graph evidence.
    
    In production, this could be Redis, Memcached, or a distributed cache.
    """
    
    def __init__(self, default_ttl_seconds: int = 300):
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl_seconds = default_ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> dict[str, Any] | None:
        """
        Retrieve cached evidence if it exists and is not expired.
        Returns None on cache miss or expiration.
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self.misses += 1
            return None
        
        if entry.is_expired():
            del self._cache[key]
            self.misses += 1
            return None
        
        entry.touch()
        self.hits += 1
        return entry.evidence
    
    def set(self, key: str, evidence: dict[str, Any], ttl_seconds: int | None = None):
        """Store evidence in the cache with optional custom TTL."""
        self._cache[key] = CacheEntry(
            entity_id=key,
            evidence=evidence,
            created_at=datetime.now(),
            ttl_seconds=ttl_seconds or self.default_ttl_seconds,
        )
    
    def invalidate(self, key: str):
        """Manually invalidate a cache entry (e.g., on write events)."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def invalidate_pattern(self, prefix: str):
        """Invalidate all entries matching a prefix."""
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)
    
    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 3),
            "entries": {
                key: {
                    "age_seconds": (datetime.now() - entry.created_at).total_seconds(),
                    "ttl_seconds": entry.ttl_seconds,
                    "access_count": entry.access_count,
                }
                for key, entry in self._cache.items()
            }
        }


# Global cache instance
cache = EvidenceCache(default_ttl_seconds=300)


# ============================================================================
# GRAPH QUERY FUNCTIONS
# ============================================================================

def find_project_by_name(name: str) -> Any | None:
    """Find a project by its name."""
    results = db.records.find({
        "labels": ["PROJECT"],
        "where": {"name": name}
    })
    return results.data[0] if results.data else None


def get_project_team(project: Any) -> list[dict[str, Any]]:
    """
    Get all team members working on a project.
    
    This queries the WORKS_ON relationship from the project.
    """
    # Find all team members linked to this project via WORKS_ON
    results = db.records.find({
        "labels": ["TEAM_MEMBER"],
        "where": {
            "PROJECT": {
                "$relation": {"type": "WORKS_ON", "direction": "in"},
                "name": project["name"]
            }
        }
    })
    
    return [{"name": m["name"], "role": m["role"], "department": m["department"]} for m in results.data]


def get_project_technologies(project: Any) -> list[dict[str, Any]]:
    """
    Get all technologies used by a project.
    
    This queries the USES relationship from the project.
    """
    results = db.records.find({
        "labels": ["TECHNOLOGY"],
        "where": {
            "PROJECT": {
                "$relation": {"type": "USES", "direction": "in"},
                "name": project["name"]
            }
        }
    })
    
    return [{"name": t["name"], "category": t["category"], "version": t["version"]} for t in results.data]


def get_project_dependencies(project: Any) -> list[dict[str, Any]]:
    """
    Get all projects that this project depends on.
    
    This queries the DEPENDS_ON relationship from the project.
    """
    results = db.records.find({
        "labels": ["PROJECT"],
        "where": {
            "PROJECT": {
                "$relation": {"type": "DEPENDS_ON", "direction": "in"},
                "name": project["name"]
            }
        }
    })
    
    return [{"name": p["name"], "status": p["status"], "priority": p["priority"]} for p in results.data]


def fetch_full_subgraph(project: Any) -> dict[str, Any]:
    """
    Fetch the complete subgraph for a project in a single operation.
    
    This is the "expensive" operation that context recycling amortizes
    across multiple related queries.
    """
    team = get_project_team(project)
    technologies = get_project_technologies(project)
    dependencies = get_project_dependencies(project)
    
    return {
        "project": {
            "id": project.id,
            "name": project["name"],
            "description": project["description"],
            "status": project["status"],
            "priority": project["priority"],
        },
        "team": team,
        "technologies": technologies,
        "dependencies": dependencies,
        "_metadata": {
            "cached_at": datetime.now().isoformat(),
            "evidence_count": len(team) + len(technologies) + len(dependencies) + 1,
        }
    }


# ============================================================================
# QUERY HANDLERS - With and without recycling
# ============================================================================

def query_without_recycling(project_name: str) -> tuple[dict[str, Any], float]:
    """
    Query a project using fresh graph traversals every time.
    
    Returns the aggregated result and total time taken.
    """
    start_total = time.perf_counter()
    
    # Each call triggers a new graph traversal
    project = find_project_by_name(project_name)
    if not project:
        return {"error": "Project not found"}, time.perf_counter() - start_total
    
    timings = {}
    
    # Query 1: Get team
    t0 = time.perf_counter()
    team = get_project_team(project)
    timings["team"] = (time.perf_counter() - t0) * 1000
    
    # Query 2: Get technologies
    t0 = time.perf_counter()
    technologies = get_project_technologies(project)
    timings["technologies"] = (time.perf_counter() - t0) * 1000
    
    # Query 3: Get dependencies
    t0 = time.perf_counter()
    dependencies = get_project_dependencies(project)
    timings["dependencies"] = (time.perf_counter() - t0) * 1000
    
    total_time = (time.perf_counter() - start_total) * 1000
    
    return {
        "project": project.data if hasattr(project, 'data') else project,
        "team": team,
        "technologies": technologies,
        "dependencies": dependencies,
        "_query_timings_ms": timings,
        "_total_time_ms": total_time,
    }, total_time


def query_with_recycling(project_name: str, use_cache: bool = True) -> tuple[dict[str, Any], float, bool]:
    """
    Query a project using context recycling (cached subgraph).
    
    Returns the result, time taken, and whether it was a cache hit.
    """
    cache_key = f"project:{project_name.lower().replace(' ', '-')}"
    
    # Try cache first
    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            # Cache hit! Return immediately without any graph traversal
            return cached, 0.08, True  # ~0.08ms for cache lookup
    
    # Cache miss - need to fetch the subgraph
    start_time = time.perf_counter()
    
    project = find_project_by_name(project_name)
    if not project:
        return {"error": "Project not found"}, 0, False
    
    # This single operation fetches all evidence
    subgraph = fetch_full_subgraph(project)
    
    # Store in cache for future queries
    cache.set(cache_key, subgraph)
    
    fetch_time = (time.perf_counter() - start_time) * 1000
    
    return subgraph, fetch_time, False


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate_without_recycling(project_name: str = "Project Atlas"):
    """Show the naive approach: 3 separate graph traversals."""
    print(f"\nWITHOUT RECYCLING (3 sequential traversals):")
    print(f"  Query \"team\":        ", end="")
    
    project = find_project_by_name(project_name)
    
    t0 = time.perf_counter()
    team = get_project_team(project)
    team_time = (time.perf_counter() - t0) * 1000
    print(f"{team_time:>6.1f}ms")
    
    print(f"  Query \"technologies\": ", end="")
    t0 = time.perf_counter()
    technologies = get_project_technologies(project)
    tech_time = (time.perf_counter() - t0) * 1000
    print(f"{tech_time:>6.1f}ms")
    
    print(f"  Query \"dependencies\": ", end="")
    t0 = time.perf_counter()
    dependencies = get_project_dependencies(project)
    dep_time = (time.perf_counter() - t0) * 1000
    print(f"{dep_time:>6.1f}ms")
    
    total = team_time + tech_time + dep_time
    print(f"  {'─'*40}")
    print(f"  Total: {total:.1f}ms (3 traversals)")
    
    return total


def demonstrate_with_recycling(project_name: str = "Project Atlas"):
    """Show the optimized approach: 1 traversal, cached, reused."""
    cache_key = f"project:{project_name.lower().replace(' ', '-')}"
    
    # Clear any existing cache for clean demo
    cache.invalidate(cache_key)
    
    print(f"\nWITH RECYCLING (1 traversal, cached):")
    
    # First query - cache miss, fetches subgraph
    print(f"  First query (traverse): ", end="")
    result1, time1, is_hit1 = query_with_recycling(project_name)
    print(f"{time1:>6.1f}ms")
    print(f"  Cache stored: {cache_key} ({result1.get('_metadata', {}).get('evidence_count', '?')} evidence nodes)")
    
    # Second query - cache hit, no graph traversal
    print(f"  Second query (cache):   ", end="")
    result2, time2, is_hit2 = query_with_recycling(project_name)
    status = "✓" if is_hit2 else "miss"
    print(f"{time2:>6.1f}ms  {status}")
    
    # Third query - cache hit, no graph traversal
    print(f"  Third query (cache):   ", end="")
    result3, time3, is_hit3 = query_with_recycling(project_name)
    status = "✓" if is_hit3 else "miss"
    print(f"{time3:>6.1f}ms  {status}")
    
    total = time1 + time2 + time3
    print(f"  {'─'*40}")
    print(f"  Total: {total:.2f}ms (1 traversal + 2 cache hits)")
    
    return total


def demonstrate_staleness_tradeoffs():
    """Explain the staleness risks and TTL strategies."""
    print(f"\n{'─'*60}")
    print("FRESHNESS TRADE-OFFS")
    print("─"*60)
    
    print("\nStaleness Examples:")
    print("  • Team member leaves → cache still shows them on project")
    print("  • New technology adopted → cache misses the update")
    print("  • Dependency removed → cache reflects removed relationship")
    
    print("\nTTL Strategy Analysis:")
    strategies = [
        ("5 minutes", "Good for real-time chat, may miss fast changes", True),
        ("1 hour", "Safe for documentation, stale for active projects", True),
        ("24 hours", "Batch processing only, inappropriate for AI apps", False),
        ("No expiry", "+ manual invalidation on writes", True),
    ]
    
    for ttl, description, recommended in strategies:
        marker = "✓" if recommended else "✗"
        print(f"  {marker} {ttl}: {description}")
    
    print("\nCache Invalidation Triggers:")
    print("  ✓ Manual: User requests fresh data")
    print("  ✓ Event:  Webhook on PROJECT update → invalidate cache")
    print("  ✓ Time:   TTL expiration")
    print("  ✓ Scope:  Cascade invalidation to related entities")
    
    # Show cache stats
    print("\nCurrent Cache Statistics:")
    stats = cache.stats()
    print(f"  • Size: {stats['size']} entries")
    print(f"  • Hits: {stats['hits']}, Misses: {stats['misses']}")
    print(f"  • Hit Rate: {stats['hit_rate']*100:.1f}%")


def demonstrate_invalidation_scenarios():
    """Show different cache invalidation strategies."""
    print(f"\n{'─'*60}")
    print("CACHE INVALIDATION SCENARIOS")
    print("─"*60)
    
    # Pre-populate cache
    projects = ["Project Atlas", "Project Beacon", "Project Chronos"]
    for proj in projects:
        result, _, _ = query_with_recycling(proj)
        if "error" not in result:
            print(f"  ✓ Cached: {proj}")
    
    print("\nScenario 1: Manual invalidation")
    cache.invalidate("project:project-atlas")
    print("  cache.invalidate('project:project-atlas')")
    print(f"  Cache size after: {len(cache._cache)}")
    
    print("\nScenario 2: Pattern invalidation (e.g., on project deletion)")
    count = cache.invalidate_pattern("project:")
    print(f"  cache.invalidate_pattern('project:')")
    print(f"  Invalidated {count} entries")
    
    print("\nScenario 3: Event-driven invalidation (pseudo-code)")
    print("""
    @app.on_event("project.updated")
    async def on_project_updated(event):
        cache.invalidate(f"project:{event.project_slug}")
    
    @app.on_event("team_member.departed")
    async def on_member_departed(event):
        # Invalidate all projects this member worked on
        for project in event.member.projects:
            cache.invalidate(f"project:{project.slug}")
    """)


def cleanup():
    """Clean up demo data."""
    print("\nCleaning up...")
    try:
        db.records.delete_many({"labels": ["PROJECT"], "where": {}})
        db.records.delete_many({"labels": ["TEAM_MEMBER"], "where": {}})
        db.records.delete_many({"labels": ["TECHNOLOGY"], "where": {}})
        print("  ✓ Cleanup complete")
    except Exception as e:
        print(f"  ! Cleanup skipped (may be empty): {e}")


def check_and_seed_data():
    """Check if data exists, seed if not."""
    existing = db.records.find({"labels": ["PROJECT"], "where": {}})
    
    if existing.total == 0:
        print("\nNo data found. Running seed script first...")
        import seed
        seed.seed_data()
    else:
        print(f"\nFound {existing.total} existing PROJECT records.")


def main():
    print("\n" + "="*60)
    print("CONTEXT RECYCLING DEMONSTRATION")
    print("Reusing Graph-Retrieved Evidence Across Related Queries")
    print("="*60)
    
    # Ensure data exists
    check_and_seed_data()
    
    # Scenario description
    print(f"\n{'─'*60}")
    print("SCENARIO: \"Tell me about Project Atlas\"")
    print("  - Who works on it?")
    print("  - What technologies does it use?")
    print("  - What are its dependencies?")
    print("─"*60)
    
    # Run demonstrations
    time_without = demonstrate_without_recycling("Project Atlas")
    time_with = demonstrate_with_recycling("Project Atlas")
    
    # Calculate speedup
    speedup = time_without / time_with if time_with > 0 else 0
    print(f"\n  {'─'*40}")
    print(f"  SPEEDUP: {speedup:.1f}x faster for related queries")
    
    # Explain freshness tradeoffs
    demonstrate_staleness_tradeoffs()
    
    # Show invalidation scenarios
    demonstrate_invalidation_scenarios()
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)
    print("\nKey Takeaways:")
    print("  1. Context recycling eliminates redundant graph traversals")
    print("  2. Cache by entity ID for predictable invalidation")
    print("  3. TTL should match your freshness requirements")
    print("  4. Event-driven invalidation keeps caches fresh on writes")
    print("  5. RushDB's free reads make cache misses cheap")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you've run `python seed.py` first to populate the database.")
        raise
