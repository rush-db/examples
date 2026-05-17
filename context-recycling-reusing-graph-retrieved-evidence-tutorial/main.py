#!/usr/bin/env python3
"""
Context Recycling: Reusing Graph-Retrieved Evidence Across Related Queries

This tutorial demonstrates how to implement context recycling in RushDB using
entity-based cache keys to optimize graph retrieval patterns for multi-turn
applications like conversational AI or complex query pipelines.
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

# RushDB SDK
from rushdb import RushDB

# =============================================================================
# Configuration
# =============================================================================

RUSHDB_API_KEY = os.getenv("RUSHDB_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# =============================================================================
# Data Models
# =============================================================================

@dataclass
class EvidenceRecord:
    """A single piece of evidence from graph retrieval."""
    entity_id: str
    entity_type: str
    entity_label: str
    data: dict
    relationships: list = field(default_factory=list)
    retrieved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_llm_context(self) -> str:
        """Format for LLM system prompt."""
        rels = ", ".join([f"{r['type']} → {r['target_label']}:{r['target_id']}" 
                          for r in self.relationships])
        return f"[{self.entity_label}] {self.entity_id}: {json.dumps(self.data, indent=2)}\n  Relationships: [{rels}]"


@dataclass
class CachedEvidence:
    """A cached subgraph evidence unit."""
    cache_key: str
    entity_ids: list  # List of entity IDs this evidence covers
    evidence: list[EvidenceRecord]
    version: int
    created_at: str
    expires_at: str
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        expiry = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() > expiry
    
    @property
    def is_partial_match(self) -> bool:
        """Check if this is a partial cache hit (some entities missing)."""
        return len(self.entity_ids) > 0 and len(self.evidence) < len(self.entity_ids)
    
    def to_llm_context(self) -> str:
        """Format all evidence for LLM context."""
        return "\n\n".join([e.to_llm_context() for e in self.evidence])


@dataclass
class RetrievalMetrics:
    """Metrics for a retrieval operation."""
    cache_status: str  # HIT, MISS, PARTIAL
    graph_traversals: int
    cache_hits: int
    latency_ms: float
    evidence_count: int
    cached_count: int
    fresh_count: int
    
    def __str__(self) -> str:
        status_emoji = {"HIT": "✅", "MISS": "❄️", "PARTIAL": "🔄"}
        emoji = status_emoji.get(self.cache_status, "📦")
        return (
            f"   {emoji} Cache: {self.cache_status} | "
            f"Traversals: {self.graph_traversals} | "
            f"Evidence: {self.cached_count} reused + {self.fresh_count} fresh | "
            f"Latency: {self.latency_ms:.2f}ms"
        )


# =============================================================================
# Context Cache Implementation
# =============================================================================

class ContextCache:
    """
    Entity-based context cache for graph-retrieved evidence.
    
    This cache uses graph relationships as the cache key pattern.
    When you retrieve evidence about Entity A and its connections,
    subsequent queries about Entity A can reuse that cached evidence.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self._memory_cache: dict[str, CachedEvidence] = {}
        self._cache_version = 1
    
    def _generate_cache_key(self, entity_type: str, entity_ids: list[str]) -> str:
        """Generate a deterministic cache key from entity identifiers."""
        # Sort IDs for consistent key generation
        sorted_ids = sorted(set(entity_ids))
        key_data = f"{entity_type}:{','.join(sorted_ids)}:v{self._cache_version}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"evidence:{entity_type}:{key_hash}"
    
    def get(self, entity_type: str, entity_ids: list[str]) -> Optional[CachedEvidence]:
        """
        Retrieve cached evidence for given entities.
        
        Returns:
            CachedEvidence if found and not expired, None otherwise.
        """
        cache_key = self._generate_cache_key(entity_type, entity_ids)
        cached = self._memory_cache.get(cache_key)
        
        if cached is None:
            return None
        
        # Check expiration
        if cached.is_expired:
            del self._memory_cache[cache_key]
            return None
        
        # Increment hit count for metrics
        cached.hit_count += 1
        return cached
    
    def get_partial(self, entity_type: str, requested_ids: list[str], 
                    cached_ids: list[str]) -> tuple[list, list]:
        """
        Get partial cache match - separates fresh from stale entity IDs.
        
        Returns:
            Tuple of (cached_ids, missing_ids) to fetch from graph.
        """
        cached_set = set(cached_ids)
        requested_set = set(requested_ids)
        
        cached = list(requested_set & cached_set)
        missing = list(requested_set - cached_set)
        
        return cached, missing
    
    def set(self, entity_type: str, entity_ids: list[str], 
            evidence: list[EvidenceRecord]) -> CachedEvidence:
        """
        Store evidence in the cache.
        """
        cache_key = self._generate_cache_key(entity_type, entity_ids)
        
        now = datetime.utcnow()
        expires = now + timedelta(seconds=CACHE_TTL)
        
        cached = CachedEvidence(
            cache_key=cache_key,
            entity_ids=entity_ids,
            evidence=evidence,
            version=self._cache_version,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )
        
        self._memory_cache[cache_key] = cached
        return cached
    
    def invalidate(self, entity_type: str, entity_ids: list[str]) -> bool:
        """Invalidate specific cache entries."""
        cache_key = self._generate_cache_key(entity_type, entity_ids)
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
            return True
        return False
    
    def invalidate_all(self):
        """Clear entire cache."""
        self._memory_cache.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_hits = sum(e.hit_count for e in self._memory_cache.values())
        return {
            "entries": len(self._memory_cache),
            "total_hits": total_hits,
            "version": self._cache_version,
        }


# =============================================================================
# Graph Retrieval with Context Recycling
# =============================================================================

class EvidenceRetriever:
    """
    Retrieves subgraph evidence with context recycling support.
    
    This class demonstrates:
    1. Cache-first retrieval pattern
    2. Partial cache hit handling
    3. Full graph traversal when needed
    4. Metrics collection
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.cache = ContextCache(db)
        self._traversal_count = 0
    
    def retrieve_project_evidence(self, project_name: str) -> tuple[list[EvidenceRecord], RetrievalMetrics]:
        """
        Retrieve evidence for a project and its related entities.
        
        This demonstrates the core context recycling pattern:
        1. Check cache for existing evidence
        2. If miss, traverse graph to build evidence
        3. Store evidence in cache
        4. Return evidence with metrics
        """
        start_time = time.perf_counter()
        self._traversal_count = 0
        
        # Find the project
        projects = self.db.records.find({
            "labels": ["PROJECT"],
            "where": {"name": project_name}
        })
        
        if projects.total == 0:
            return [], RetrievalMetrics(
                cache_status="MISS",
                graph_traversals=0,
                cache_hits=0,
                latency_ms=0,
                evidence_count=0,
                cached_count=0,
                fresh_count=0,
            )
        
        project = projects.data[0]
        project_id = project.id
        
        # Check cache first
        cached = self.cache.get("PROJECT", [project_id])
        
        if cached:
            # Cache HIT - return cached evidence immediately
            latency_ms = (time.perf_counter() - start_time) * 1000
            return cached.evidence, RetrievalMetrics(
                cache_status="HIT",
                graph_traversals=0,
                cache_hits=1,
                latency_ms=latency_ms,
                evidence_count=len(cached.evidence),
                cached_count=len(cached.evidence),
                fresh_count=0,
            )
        
        # Cache MISS - build evidence through graph traversal
        evidence = []
        
        # 1. Get project details
        self._traversal_count += 1
        evidence.append(EvidenceRecord(
            entity_id=project_id,
            entity_type="PROJECT",
            entity_label="PROJECT",
            data=project.fields,
            relationships=[],
        ))
        
        # 2. Find team members working on this project
        self._traversal_count += 1
        team_members = self.db.records.find({
            "labels": ["EMPLOYEE"],
            "where": {"PROJECT": {"$relation": {"type": "WORKS_ON", "direction": "out"}}},
        })
        
        employee_records = []
        for member in team_members.data:
            self._traversal_count += 1
            employee_records.append(member)
            evidence.append(EvidenceRecord(
                entity_id=member.id,
                entity_type="EMPLOYEE",
                entity_label="EMPLOYEE",
                data=member.fields,
                relationships=[{"type": "WORKS_ON", "target_id": project_id, "target_label": "PROJECT"}],
            ))
        
        # 3. Find project documents
        self._traversal_count += 1
        docs = self.db.records.find({
            "labels": ["DOCUMENT"],
            "where": {"PROJECT": {"$relation": {"type": "HAS_DOC", "direction": "in"}}},
        })
        
        for doc in docs.data:
            self._traversal_count += 1
            evidence.append(EvidenceRecord(
                entity_id=doc.id,
                entity_type="DOCUMENT",
                entity_label="DOCUMENT",
                data=doc.fields,
                relationships=[{"type": "HAS_DOC", "target_id": project_id, "target_label": "PROJECT"}],
            ))
        
        # Cache the evidence
        entity_ids = [project_id] + [e.id for e in employee_records]
        self.cache.set("PROJECT", entity_ids, evidence)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        return evidence, RetrievalMetrics(
            cache_status="MISS",
            graph_traversals=self._traversal_count,
            cache_hits=0,
            latency_ms=latency_ms,
            evidence_count=len(evidence),
            cached_count=0,
            fresh_count=len(evidence),
        )
    
    def retrieve_employee_evidence(self, employee_name: str = None, 
                                   employee_id: str = None) -> tuple[list[EvidenceRecord], RetrievalMetrics]:
        """
        Retrieve evidence for an employee and their work.
        """
        start_time = time.perf_counter()
        self._traversal_count = 0
        
        # Find the employee
        if employee_id:
            employee = self.db.records.find_by_id(employee_id)
        else:
            employees = self.db.records.find({
                "labels": ["EMPLOYEE"],
                "where": {"name": {"$contains": employee_name}} if employee_name else {}
            })
            if employees.total == 0:
                return [], RetrievalMetrics("MISS", 0, 0, 0, 0, 0, 0)
            employee = employees.data[0]
        
        emp_id = employee.id
        
        # Check cache
        cached = self.cache.get("EMPLOYEE", [emp_id])
        if cached:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return cached.evidence, RetrievalMetrics(
                cache_status="HIT",
                graph_traversals=0,
                cache_hits=1,
                latency_ms=latency_ms,
                evidence_count=len(cached.evidence),
                cached_count=len(cached.evidence),
                fresh_count=0,
            )
        
        # Build evidence
        evidence = []
        self._traversal_count += 1
        evidence.append(EvidenceRecord(
            entity_id=emp_id,
            entity_type="EMPLOYEE",
            entity_label="EMPLOYEE",
            data=employee.fields,
            relationships=[],
        ))
        
        # Find their projects
        self._traversal_count += 1
        projects = self.db.records.find({
            "labels": ["PROJECT"],
            "where": {"EMPLOYEE": {"$relation": {"type": "WORKS_ON", "direction": "in"}}},
        })
        
        for proj in projects.data:
            self._traversal_count += 1
            evidence.append(EvidenceRecord(
                entity_id=proj.id,
                entity_type="PROJECT",
                entity_label="PROJECT",
                data=proj.fields,
                relationships=[{"type": "WORKS_ON", "target_id": emp_id, "target_label": "EMPLOYEE"}],
            ))
        
        # Find their documents
        self._traversal_count += 1
        docs = self.db.records.find({
            "labels": ["DOCUMENT"],
            "where": {"EMPLOYEE": {"$relation": {"type": "AUTHORED_BY", "direction": "in"}}},
        })
        
        for doc in docs.data:
            self._traversal_count += 1
            evidence.append(EvidenceRecord(
                entity_id=doc.id,
                entity_type="DOCUMENT",
                entity_label="DOCUMENT",
                data=doc.fields,
                relationships=[{"type": "AUTHORED_BY", "target_id": emp_id, "target_label": "EMPLOYEE"}],
            ))
        
        # Cache evidence
        self.cache.set("EMPLOYEE", [emp_id], evidence)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        return evidence, RetrievalMetrics(
            cache_status="MISS",
            graph_traversals=self._traversal_count,
            cache_hits=0,
            latency_ms=latency_ms,
            evidence_count=len(evidence),
            cached_count=0,
            fresh_count=len(evidence),
        )
    
    def handle_partial_hit(self, project_name: str, 
                          stale_entity_ids: list[str]) -> tuple[list[EvidenceRecord], RetrievalMetrics]:
        """
        Handle partial cache hit - some entities are stale, need refresh.
        
        This is called when we know some context is cached but may be outdated.
        We fetch only the missing/fresh data and merge with cache.
        """
        start_time = time.perf_counter()
        self._traversal_count = 0
        
        # Get fresh evidence for the main project
        fresh_evidence, _ = self.retrieve_project_evidence(project_name)
        
        # In a real implementation, we would:
        # 1. Fetch only the stale entity IDs from the graph
        # 2. Merge with cached data
        # 3. Update cache with merged result
        # 4. Return merged evidence
        
        # For demo, we'll simulate partial by fetching fresh and combining
        cached = self.cache.get("PROJECT", stale_entity_ids)
        if cached:
            # Merge cached and fresh
            all_evidence = fresh_evidence + cached.evidence
            # Deduplicate by entity_id
            seen = set()
            merged = []
            for e in all_evidence:
                if e.entity_id not in seen:
                    seen.add(e.entity_id)
                    merged.append(e)
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            return merged, RetrievalMetrics(
                cache_status="PARTIAL",
                graph_traversals=self._traversal_count,
                cache_hits=1,
                latency_ms=latency_ms,
                evidence_count=len(merged),
                cached_count=len(cached.evidence),
                fresh_count=len(fresh_evidence),
            )
        
        return fresh_evidence, RetrievalMetrics(
            cache_status="PARTIAL",
            graph_traversals=self._traversal_count,
            cache_hits=0,
            latency_ms=latency_ms,
            evidence_count=len(fresh_evidence),
            cached_count=0,
            fresh_count=len(fresh_evidence),
        )


# =============================================================================
# LLM Integration Helper
# =============================================================================

def format_evidence_for_llm(evidence: list[EvidenceRecord], 
                            include_context: bool = True) -> str:
    """
    Format retrieved evidence as context for an LLM.
    
    This creates a structured system prompt that includes:
    - Entity summaries
    - Relationship context
    - Temporal metadata
    """
    if not evidence:
        return "No relevant evidence found."
    
    # Group by entity type
    by_type = {}
    for e in evidence:
        if e.entity_type not in by_type:
            by_type[e.entity_type] = []
        by_type[e.entity_type].append(e)
    
    lines = ["=" * 60]
    lines.append("KNOWLEDGE GRAPH EVIDENCE")
    lines.append("=" * 60)
    
    if include_context:
        lines.append(f"\n📊 Evidence items: {len(evidence)}")
        lines.append(f"📅 Retrieved: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
    
    for entity_type, items in by_type.items():
        lines.append(f"\n## {entity_type}s ({len(items)})")
        for item in items:
            lines.append(f"\n### {item.entity_id}")
            for key, value in item.data.items():
                lines.append(f"  - {key}: {value}")
            if item.relationships:
                lines.append("  Relationships:")
                for rel in item.relationships:
                    lines.append(f"    → {rel['type']} → {rel['target_label']} ({rel['target_id']})")
    
    return "\n".join(lines)


def build_llm_prompt(user_query: str, evidence: list[EvidenceRecord], 
                     conversation_history: list[dict] = None) -> list[dict]:
    """
    Build a complete LLM prompt with recycled context.
    
    Args:
        user_query: The current user question
        evidence: Retrieved and potentially cached evidence
        conversation_history: Optional previous turns
    
    Returns:
        List of message dictionaries for OpenAI API
    """
    system_prompt = f"""You are an AI assistant with access to a knowledge graph.
Use the provided evidence to answer questions accurately.
If information is not in the evidence, say so.

{format_evidence_for_llm(evidence)}

Guidelines:
- Reference specific entities and their properties when answering
- Mention relationship context when relevant
- Be concise but informative"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history[-3:]:  # Last 3 turns
            messages.append(msg)
    
    messages.append({"role": "user", "content": user_query})
    
    return messages


# =============================================================================
# Demo Runner
# =============================================================================

def run_demo():
    """Run the complete context recycling demonstration."""
    
    print("\n" + "=" * 70)
    print("🚀 CONTEXT RECYCLING DEMO")
    print("   Reusing Graph-Retrieved Evidence Across Related Queries")
    print("=" * 70)
    print()
    
    # Validate environment
    if not RUSHDB_API_KEY:
        print("❌ Error: RUSHDB_API_KEY not found")
        print("   Please copy .env.example to .env and add your API key")
        return
    
    db = RushDB(RUSHDB_API_KEY)
    retriever = EvidenceRetriever(db)
    
    # Verify data exists
    companies = db.records.find({"labels": ["COMPANY"], "where": {"name": "TechCorp"}})
    if companies.total == 0:
        print("❌ Error: TechCorp not found in database")
        print("   Please run `python seed.py` first to create sample data")
        return
    
    print(f"✅ Connected to RushDB. Found: TechCorp company")
    print()
    
    # =========================================================================
    # Session 1: Initial query (cold cache)
    # =========================================================================
    print("─" * 70)
    print("📊 SESSION 1: Initial query about 'AI Platform' project")
    print("─" * 70)
    
    evidence1, metrics1 = retriever.retrieve_project_evidence("AI Platform")
    print(f"\n   ❄️  Cold retrieval (cache empty)")
    print(f"   🔍 Graph traversals: {metrics1.graph_traversals}")
    print(f"   📦 Evidence items: {metrics1.evidence_count}")
    print(f"   ⏱️  Latency: {metrics1.latency_ms:.2f}ms")
    
    print("\n   Retrieved Evidence:")
    for e in evidence1[:4]:  # Show first 4
        print(f"     • {e.entity_label}: {e.data.get('name', e.data.get('title', 'N/A'))}")
    if len(evidence1) > 4:
        print(f"     ... and {len(evidence1) - 4} more")
    
    cold_latency = metrics1.latency_ms
    
    # =========================================================================
    # Session 2: Follow-up query (cache hit)
    # =========================================================================
    print("\n" + "─" * 70)
    print("📊 SESSION 2: Follow-up query - 'Who works on AI Platform?'")
    print("─" * 70)
    
    evidence2, metrics2 = retriever.retrieve_project_evidence("AI Platform")
    print(f"\n   ✅ Cache HIT - Evidence reused from Session 1")
    print(f"   🔍 Graph traversals: {metrics2.graph_traversals} (0 new traversals!)")
    print(f"   📦 Evidence items: {metrics2.cached_count} cached")
    print(f"   ⏱️  Latency: {metrics2.latency_ms:.4f}ms")
    
    if cold_latency > 0:
        speedup = cold_latency / metrics2.latency_ms if metrics2.latency_ms > 0 else float('inf')
        print(f"   🚀 Speedup: {speedup:.0f}x faster than cold retrieval")
    
    # =========================================================================
    # Session 3: Different project query
    # =========================================================================
    print("\n" + "─" * 70)
    print("📊 SESSION 3: Query for 'Mobile App Rewrite' project")
    print("─" * 70)
    
    evidence3, metrics3 = retriever.retrieve_project_evidence("Mobile App Rewrite")
    print(f"\n   ❄️  Cache MISS (different project)")
    print(f"   🔍 Graph traversals: {metrics3.graph_traversals}")
    print(f"   📦 Evidence items: {metrics3.evidence_count}")
    print(f"   ⏱️  Latency: {metrics3.latency_ms:.2f}ms")
    
    # =========================================================================
    # Session 4: Re-query first project (should be cached)
    # =========================================================================
    print("\n" + "─" * 70)
    print("📊 SESSION 4: Return to 'AI Platform' (cache should have it)")
    print("─" * 70)
    
    evidence4, metrics4 = retriever.retrieve_project_evidence("AI Platform")
    print(f"\n   ✅ Cache HIT - Evidence immediately available")
    print(f"   ⏱️  Latency: {metrics4.latency_ms:.4f}ms")
    
    # =========================================================================
    # Session 5: Employee query
    # =========================================================================
    print("\n" + "─" * 70)
    print("📊 SESSION 5: Query for employee details")
    print("─" * 70)
    
    # Get an employee from previous evidence
    emp_evidence = None
    for e in evidence1:
        if e.entity_type == "EMPLOYEE":
            emp_evidence = e
            break
    
    if emp_evidence:
        emp_name = emp_evidence.data.get("name", "Unknown")
        print(f"\n   Querying: {emp_name}")
        
        employee_evidence, emp_metrics = retriever.retrieve_employee_evidence(employee_id=emp_evidence.entity_id)
        
        if emp_metrics.cache_status == "HIT":
            print(f"   ✅ Cache HIT for employee")
        else:
            print(f"   ❄️  Cache MISS - Retrieved employee evidence")
        print(f"   🔍 Graph traversals: {emp_metrics.graph_traversals}")
        print(f"   ⏱️  Latency: {emp_metrics.latency_ms:.2f}ms")
    
    # =========================================================================
    # Cache Statistics
    # =========================================================================
    print("\n" + "=" * 70)
    print("📈 CACHE STATISTICS")
    print("=" * 70)
    
    stats = retriever.cache.get_stats()
    print(f"\n   📊 Total cache entries: {stats['entries']}")
    print(f"   🔄 Total cache hits: {stats['total_hits']}")
    print(f"   🏷️  Cache version: {stats['version']}")
    print(f"   ⏰ TTL: {CACHE_TTL} seconds")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 70)
    print("💡 KEY TAKEAWAYS")
    print("=" * 70)
    print("""
   1. CACHE-FIRST PATTERN
      Check cache before graph traversal to avoid redundant work.
   
   2. ENTITY-BASED KEYS
      Use entity IDs (not query text) as cache keys for precise matching.
   
   3. EVIDENCE REUSE
      Store the retrieved subgraph, not just the result. Future queries
      about related entities can reuse parts of the evidence.
   
   4. PARTIAL HITS
      When cache is partially stale, fetch only missing data and merge.
      This balances freshness with performance.
   
   5. LLM INTEGRATION
      Pass formatted evidence as system context for grounded answers.
      Cache the evidence to avoid re-retrieving on each turn.
""")
    
    # =========================================================================
    # LLM Integration Demo (Optional)
    # =========================================================================
    if OPENAI_API_KEY:
        print("=" * 70)
        print("🤖 LLM INTEGRATION DEMO")
        print("=" * 70)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Build prompt with cached evidence
            messages = build_llm_prompt(
                "What is the current status of the AI Platform project?",
                evidence1
            )
            
            print("\n   Sending query to GPT-4 with cached evidence context...")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=200,
            )
            
            print(f"\n   📝 LLM Response:\n")
            print(f"   {response.choices[0].message.content}")
            print("\n   ✅ Note: Evidence was retrieved using cached context!")
            
        except ImportError:
            print("\n   ⚠️  OpenAI package not installed. Skipping LLM demo.")
            print("   Run: pip install openai")
        except Exception as e:
            print(f"\n   ⚠️  LLM demo failed: {str(e)}")
            print("   (Check your OPENAI_API_KEY in .env)")
    else:
        print("\n" + "─" * 70)
        print("💡 To enable LLM integration, add OPENAI_API_KEY to your .env file")
        print("─" * 70)
    
    print("\n" + "=" * 70)
    print("✅ Demo complete! Try modifying queries or adding new data.")
    print("=" * 70 + "\n")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    run_demo()
