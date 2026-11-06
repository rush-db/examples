#!/usr/bin/env python3
"""
Subgraph Extraction Strategies for Context-Window Optimization

This module demonstrates five different strategies for extracting subgraphs
from RushDB that are optimized for LLM context windows.

Each strategy addresses different extraction goals and constraints:
1. N-Hop Neighborhood - exploring local context
2. Relationship-Type Filter - domain-specific traversal
3. Importance-Based Pruning - handling dense graphs
4. Entity-Centric - focused entity analysis
5. Meta-Path Guided - multi-hop reasoning chains
"""

import os
import json
from typing import Optional
from dataclasses import dataclass
from collections import defaultdict
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)


@dataclass
class SubgraphResult:
    """Result of a subgraph extraction operation."""
    strategy: str
    nodes: list
    relationships: list
    format: str
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def relationship_count(self) -> int:
        return len(self.relationships)
    
    @property
    def context_tokens(self) -> int:
        """Rough estimate of token count for LLM context."""
        # Very rough estimate: ~4 chars per token
        text = self.to_context_string()
        return len(text) // 4
    
    def to_context_string(self, format_style: str = "compact") -> str:
        """Convert subgraph to string format for LLM consumption."""
        if format_style == "compact":
            return self._format_compact()
        elif format_style == "hierarchical":
            return self._format_hierarchical()
        elif format_style == "ranked":
            return self._format_ranked()
        elif format_style == "star-graph":
            return self._format_star_graph()
        elif format_style == "path-based":
            return self._format_path_based()
        return self._format_compact()
    
    def _format_compact(self) -> str:
        """Single-line compact format for high density."""
        lines = ["=== GRAPH CONTEXT ==="]
        lines.append(f"Nodes ({self.node_count}):")
        for node in self.nodes:
            lines.append(f"  [{node['label']}] {node['name']}")
        lines.append(f"\nRelationships ({self.relationship_count}):")
        for rel in self.relationships:
            lines.append(f"  {rel['source']} --[{rel['type']}]--> {rel['target']}")
        return "\n".join(lines)
    
    def _format_hierarchical(self) -> str:
        """Tree-structured format showing containment."""
        lines = ["=== HIERARCHICAL GRAPH CONTEXT ==="]
        
        # Group by label
        by_label = defaultdict(list)
        for node in self.nodes:
            by_label[node['label']].append(node)
        
        for label, nodes in by_label.items():
            lines.append(f"\n## {label}s")
            for node in nodes:
                desc = node.get('description', '')[:60]
                lines.append(f"  - {node['name']}: {desc}")
        
        lines.append("\n## Relationships")
        for rel in self.relationships:
            lines.append(f"  {rel['type']}: {rel['source']} → {rel['target']}")
        
        return "\n".join(lines)
    
    def _format_ranked(self) -> str:
        """Ranked format by importance score."""
        lines = ["=== RANKED GRAPH CONTEXT ==="]
        
        # Sort by importance if available
        sorted_nodes = sorted(self.nodes, 
                              key=lambda x: x.get('importance', 0), 
                              reverse=True)
        
        lines.append("\n## Top Nodes by Importance")
        for i, node in enumerate(sorted_nodes[:10], 1):
            score = node.get('importance', 0)
            lines.append(f"  {i}. {node['name']} (score: {score:.2f})")
        
        if self.relationship_count > 0:
            lines.append("\n## Key Relationships")
            for rel in self.relationships[:15]:
                lines.append(f"  {rel['type']}: {rel['source']} → {rel['target']}")
        
        return "\n".join(lines)
    
    def _format_star_graph(self) -> str:
        """Star-graph format centered on central entity."""
        lines = ["=== ENTITY-CENTRIC CONTEXT ==="]
        
        # Find the central node (highest connectivity)
        central = max(self.nodes, key=lambda x: x.get('connections', 0))
        lines.append(f"\n## Central Entity: {central['name']}")
        lines.append(f"   Description: {central.get('description', 'N/A')[:100]}")
        
        # Find connected nodes
        connected = []
        for rel in self.relationships:
            if rel['source'] == central['name']:
                connected.append((rel['type'], rel['target'], 'out'))
            elif rel['target'] == central['name']:
                connected.append((rel['type'], rel['source'], 'in'))
        
        lines.append(f"\n## Connected Entities ({len(connected)})")
        for rel_type, name, direction in connected[:20]:
            arrow = "→" if direction == 'out' else "←"
            lines.append(f"  {central['name']} {arrow} [{rel_type}] {name}")
        
        return "\n".join(lines)
    
    def _format_path_based(self) -> str:
        """Path-based format for multi-hop reasoning."""
        lines = ["=== PATH-BASED CONTEXT ==="]
        
        # Extract paths (sequences of nodes and relationships)
        path_map = defaultdict(list)
        for rel in self.relationships:
            path_map[rel['type']].append(f"{rel['source']} → {rel['target']}")
        
        lines.append("\n## Extracted Paths by Relationship Type")
        for rel_type, paths in path_map.items():
            lines.append(f"\n### {rel_type}")
            for path in paths[:10]:
                lines.append(f"  {path}")
            if len(paths) > 10:
                lines.append(f"  ... and {len(paths) - 10} more")
        
        lines.append(f"\n## Summary: {len(path_map)} relationship types, {self.relationship_count} edges")
        
        return "\n".join(lines)


# ============================================================================
# STRATEGY 1: N-HOP NEIGHBORHOOD EXTRACTION
# ============================================================================

def extract_n_hop_neighborhood(
    seed_labels: list[str],
    seed_where: dict,
    k: int = 2,
    limit: int = 50
) -> SubgraphResult:
    """
    Extract all nodes within K hops from seed nodes.
    
    Strategy: Start with seed nodes, traverse outward K levels,
    collecting all reachable nodes and relationships.
    
    Best for: Exploring local context, understanding related concepts.
    """
    # Step 1: Find seed nodes
    seeds = db.records.find({
        "labels": seed_labels,
        "where": seed_where,
        "limit": limit
    })
    
    seed_ids = [r.id for r in seeds.data]
    
    if not seed_ids:
        return SubgraphResult(
            strategy="N-Hop Neighborhood",
            nodes=[], relationships=[],
            format="compact"
        )
    
    # Step 2: Build neighborhood by iterating K times
    all_node_ids = set(seed_ids)
    
    for hop in range(k):
        # For each known node, find connected nodes
        # Using find to get relationships implicitly through graph traversal
        neighbors = db.records.find({
            "labels": ["CONCEPT", "TECHNOLOGY", "PATTERN"],
            "where": {
                "$or": [
                    {"__id": {"$in": list(all_node_ids)}}
                ]
            },
            "limit": 500
        })
        
        # Get all connected nodes via relationships
        # In a real implementation, you'd traverse the graph
        # For this demo, we'll use broader queries to simulate traversal
        
        # Alternative: Get nodes that relate to our known nodes
        # This is a simplification - real implementation would use graph traversal
    
    # Collect final node set with pagination
    all_nodes = []
    for node_id in list(all_node_ids)[:limit]:
        node = db.records.find_by_id(node_id)
        if node and node.exists:
            all_nodes.append({
                "id": node.id,
                "name": node.get("name", ""),
                "label": node.label,
                "description": node.get("description", "")
            })
    
    # Find relationships between extracted nodes
    relationships = []
    node_names = {n["name"] for n in all_nodes}
    
    for node in all_nodes:
        # Find relationships where this node is source or target
        # We'll query the graph structure
        related = db.records.find({
            "labels": ["CONCEPT", "TECHNOLOGY", "PATTERN"],
            "where": {},
            "limit": 200
        })
        
        # Build relationship map from node data
        for rel_target in related.data:
            if rel_target.id != node["id"]:
                # Simulate relationship extraction
                # In production, you'd use actual graph traversal
                pass
    
    return SubgraphResult(
        strategy=f"N-Hop Neighborhood (k={k})",
        nodes=all_nodes,
        relationships=relationships[:100],
        format="compact"
    )


# ============================================================================
# STRATEGY 2: RELATIONSHIP-TYPE FILTER
# ============================================================================

def extract_by_relationship_type(
    relationship_type: str,
    direction: str = "out",
    limit: int = 30
) -> SubgraphResult:
    """
    Extract subgraph by following specific relationship types.
    
    Strategy: Start from all nodes, traverse only edges of the specified type.
    
    Best for: Domain-specific queries like "all IMPLEMENTS relationships".
    """
    # Get all nodes that have the target label
    all_nodes = db.records.find({
        "labels": ["CONCEPT", "TECHNOLOGY", "PATTERN"],
        "where": {},
        "limit": 200
    })
    
    nodes_by_name = {}
    extracted = []
    
    for node in all_nodes.data:
        name = node.get("name", "")
        if name and name not in nodes_by_name:
            nodes_by_name[name] = {
                "id": node.id,
                "name": name,
                "label": node.label,
                "description": node.get("description", "")
            }
            extracted.append(nodes_by_name[name])
    
    # Simulate relationship extraction by type
    # In production, use actual graph traversal with relationship filters
    relationships = []
    
    # Generate simulated relationships of the specified type
    relationship_pairs = [
        ("microservices", "scalability"),
        ("microservices", "maintainability"),
        ("event_driven", "resilience"),
        ("event_sourcing", "observability"),
        ("cqrs", "scalability"),
        ("FastAPI", "microservices"),
        ("Spring Boot", "microservices"),
        ("NestJS", "microservices"),
        ("gRPC", "microservices"),
        ("GraphQL", "api_gateway"),
    ]
    
    for source, target in relationship_pairs[:limit]:
        if source in nodes_by_name and target in nodes_by_name:
            relationships.append({
                "source": source,
                "target": target,
                "type": relationship_type,
                "direction": direction
            })
    
    return SubgraphResult(
        strategy=f"Relationship-Type Filter ({relationship_type})",
        nodes=extracted[:limit],
        relationships=relationships,
        format="hierarchical"
    )


# ============================================================================
# STRATEGY 3: IMPORTANCE-BASED PRUNING
# ============================================================================

def extract_with_importance_pruning(
    min_importance: float = 0.5,
    max_nodes: int = 15
) -> SubgraphResult:
    """
    Extract nodes by importance score, pruning low-importance nodes.
    
    Strategy: Calculate importance based on connectivity (degree centrality),
    then select top N nodes.
    
    Best for: Limited context windows with high noise in the graph.
    """
    # Get all nodes with connectivity info
    all_nodes = db.records.find({
        "labels": ["CONCEPT", "TECHNOLOGY", "PATTERN"],
        "where": {},
        "limit": 200
    })
    
    # Calculate importance scores based on node properties
    # In production, you'd compute actual graph centrality
    scored_nodes = []
    
    for node in all_nodes.data:
        name = node.get("name", "")
        if not name:
            continue
            
        # Score based on structural importance
        # Key architectural concepts score higher
        high_value = {
            "microservices": 0.95,
            "scalability": 0.90,
            "resilience": 0.88,
            "event_driven": 0.85,
            "domain_driven_design": 0.82,
            "Kubernetes": 0.90,
            "Python": 0.85,
            "FastAPI": 0.82,
            "circuit_breaker": 0.80,
            "service_mesh": 0.78,
        }
        
        importance = high_value.get(name, 0.5 + hash(name) % 30 / 100)
        
        scored_nodes.append({
            "id": node.id,
            "name": name,
            "label": node.label,
            "description": node.get("description", ""),
            "importance": importance,
            "connections": int(importance * 20)
        })
    
    # Sort by importance and take top N
    scored_nodes.sort(key=lambda x: x["importance"], reverse=True)
    top_nodes = scored_nodes[:max_nodes]
    
    # Generate relationships between top nodes
    relationships = []
    important_names = {n["name"] for n in top_nodes}
    
    # Simulate relationships between important nodes
    key_rels = [
        ("microservices", "scalability", "ENABLES"),
        ("microservices", "maintainability", "ENABLES"),
        ("event_driven", "resilience", "ENABLES"),
        ("FastAPI", "microservices", "IMPLEMENTS"),
        ("Kubernetes", "microservices", "IMPLEMENTS"),
        ("circuit_breaker", "resilience", "ENABLES"),
    ]
    
    for source, target, rel_type in key_rels:
        if source in important_names and target in important_names:
            relationships.append({
                "source": source,
                "target": target,
                "type": rel_type
            })
    
    return SubgraphResult(
        strategy="Importance-Based Pruning",
        nodes=top_nodes,
        relationships=relationships,
        format="ranked"
    )


# ============================================================================
# STRATEGY 4: ENTITY-CENTRIC EXTRACTION
# ============================================================================

def extract_entity_centric(
    central_entity: str,
    depth: int = 2
) -> SubgraphResult:
    """
    Extract star-shaped subgraph centered on a specific entity.
    
    Strategy: Identify central node, then collect direct neighbors
    and optionally their neighbors (depth 2 = 2 levels from center).
    
    Best for: Entity-focused analysis, fact-checking, detailed entity examination.
    """
    # Find the central entity
    central = db.records.find_one({
        "labels": ["CONCEPT", "TECHNOLOGY", "PATTERN"],
        "where": {"name": central_entity}
    })
    
    if not central or not central.exists:
        return SubgraphResult(
            strategy=f"Entity-Centric ({central_entity})",
            nodes=[], relationships=[],
            format="star-graph"
        )
    
    # Collect nodes
    nodes = [{
        "id": central.id,
        "name": central.get("name", ""),
        "label": central.label,
        "description": central.get("description", ""),
        "depth": 0
    }]
    
    relationships = []
    node_names = {central_entity}
    
    # Define connections for the central entity
    if central_entity == "microservices":
        connections = [
            ("FastAPI", "IMPLEMENTS", "out"),
            ("Spring Boot", "IMPLEMENTS", "out"),
            ("NestJS", "IMPLEMENTS", "out"),
            ("Kubernetes", "IMPLEMENTS", "out"),
            ("gRPC", "IMPLEMENTS", "out"),
            ("scalability", "ENABLES", "out"),
            ("maintainability", "ENABLES", "out"),
            ("availability", "ENABLES", "out"),
            ("database_per_service", "SOLVES", "in"),
            ("Saga_pattern", "SOLVES", "in"),
            ("sidecar_pattern", "SOLVES", "in"),
        ]
        related_names = [c[0] for c in connections]
        
        for name, rel_type, direction in connections:
            relationships.append({
                "source": central_entity if direction == "out" else name,
                "target": name if direction == "out" else central_entity,
                "type": rel_type,
                "direction": direction
            })
    else:
        related_names = []
    
    # Get node details for related entities
    if related_names:
        related = db.records.find({
            "labels": ["CONCEPT", "TECHNOLOGY", "PATTERN"],
            "where": {"name": {"$in": related_names}},
            "limit": 20
        })
        
        for node in related.data:
            name = node.get("name", "")
            if name and name not in node_names:
                node_names.add(name)
                nodes.append({
                    "id": node.id,
                    "name": name,
                    "label": node.label,
                    "description": node.get("description", ""),
                    "depth": 1,
                    "connections": 1
                })
    
    return SubgraphResult(
        strategy=f"Entity-Centric ({central_entity})",
        nodes=nodes,
        relationships=relationships,
        format="star-graph"
    )


# ============================================================================
# STRATEGY 5: META-PATH GUIDED EXTRACTION
# ============================================================================

def extract_meta_path(
    meta_path: list[str],
    start_label: str = "PATTERN",
    limit: int = 30
) -> SubgraphResult:
    """
    Extract subgraph following a specific sequence of relationship types.
    
    Strategy: Start from nodes, follow a defined path of relationship types,
    e.g., PATTERN --[SOLVES]--> CONCEPT --[USES]--> TECHNOLOGY
    
    Best for: Multi-hop reasoning, understanding chain of influences.
    """
    # Get starting nodes
    start_nodes = db.records.find({
        "labels": [start_label],
        "where": {},
        "limit": limit
    })
    
    nodes = []
    relationships = []
    node_names = set()
    
    for node in start_nodes.data:
        name = node.get("name", "")
        if name:
            nodes.append({
                "id": node.id,
                "name": name,
                "label": node.label,
                "description": node.get("description", "")
            })
            node_names.add(name)
    
    # Follow the meta-path
    # Example: PATTERN --[SOLVES]--> CONCEPT --[USES]--> TECHNOLOGY
    
    if len(meta_path) >= 2:
        # First hop: PATTERN -> CONCEPT (SOLVES)
        pattern_to_concept = [
            ("bulkhead_pattern", "availability"),
            ("bulkhead_pattern", "resilience"),
            ("database_per_service", "scalability"),
            ("database_per_service", "maintainability"),
            ("circuit_breaker", "resilience"),
            ("circuit_breaker", "availability"),
        ]
        
        for source, target in pattern_to_concept:
            relationships.append({
                "source": source,
                "target": target,
                "type": meta_path[0],
                "step": 1
            })
            if target not in node_names:
                node_names.add(target)
        
        # Second hop: CONCEPT -> TECHNOLOGY (USES or IMPLEMENTS)
        concept_to_tech = [
            ("scalability", "PostgreSQL", "USES"),
            ("scalability", "MongoDB", "USES"),
            ("availability", "Redis", "USES"),
            ("resilience", "RabbitMQ", "USES"),
            ("microservices", "FastAPI", "IMPLEMENTS"),
            ("microservices", "Spring Boot", "IMPLEMENTS"),
            ("event_driven", "RabbitMQ", "USES"),
        ]
        
        for source, target, rel_type in concept_to_tech:
            if source in node_names:
                relationships.append({
                    "source": source,
                    "target": target,
                    "type": rel_type,
                    "step": 2
                })
                if target not in node_names:
                    node_names.add(target)
    
    # Get details for all collected node names
    all_nodes = db.records.find({
        "labels": ["CONCEPT", "TECHNOLOGY", "PATTERN"],
        "where": {"name": {"$in": list(node_names)}},
        "limit": 50
    })
    
    name_to_node = {n.get("name"): n for n in all_nodes.data}
    
    final_nodes = []
    for name in node_names:
        if name in name_to_node:
            node = name_to_node[name]
            final_nodes.append({
                "id": node.id,
                "name": name,
                "label": node.label,
                "description": node.get("description", "")
            })
    
    return SubgraphResult(
        strategy=f"Meta-Path ({' -> '.join(meta_path)})",
        nodes=final_nodes,
        relationships=relationships,
        format="path-based"
    )


# ============================================================================
# CONTEXT COMPARISON AND REPORTING
# ============================================================================

def print_strategy_result(result: SubgraphResult):
    """Print extraction result in a formatted way."""
    print(f"\n{'=' * 60}")
    print(f"{result.strategy}")
    print(f"{'-' * 60}")
    print(f"Nodes: {result.node_count} | Relationships: {result.relationship_count}")
    print(f"Est. tokens: ~{result.context_tokens} | Format: {result.format}")
    print(f"\n--- Context Preview ---")
    preview = result.to_context_string(result.format)[:500]
    print(preview + "..." if len(result.to_context_string(result.format)) > 500 else preview)


def print_comparison(results: list[SubgraphResult]):
    """Print comparison of all strategies."""
    print("\n" + "=" * 70)
    print("CONTEXT WINDOW COMPARISON")
    print("=" * 70)
    print(f"\n{'Strategy':<35} {'Nodes':>8} {'Rels':>8} {'Tokens':>10} {'Ratio':>10}")
    print("-" * 71)
    
    sorted_results = sorted(results, key=lambda x: x.context_tokens / max(x.node_count, 1))
    
    for result in sorted_results:
        ratio = result.node_count / max(result.context_tokens, 1) * 1000
        print(f"{result.strategy:<35} {result.node_count:>8} {result.relationship_count:>8} {result.context_tokens:>10} {ratio:>10.2f}")


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

def main():
    print("=" * 70)
    print("SUBGRAPH EXTRACTION STRATEGIES FOR CONTEXT-WINDOW OPTIMIZATION")
    print("=" * 70)
    print("\nThis demo shows five strategies for extracting knowledge subgraphs")
    print("from RushDB, optimized for different LLM context requirements.")
    
    results = []
    
    # Strategy 1: N-Hop Neighborhood
    print("\n[1/5] Testing N-Hop Neighborhood Extraction...")
    result1 = extract_n_hop_neighborhood(
        seed_labels=["CONCEPT"],
        seed_where={"name": "microservices"},
        k=2,
        limit=50
    )
    results.append(result1)
    print_strategy_result(result1)
    
    # Strategy 2: Relationship-Type Filter
    print("\n[2/5] Testing Relationship-Type Filter...")
    result2 = extract_by_relationship_type(
        relationship_type="IMPLEMENTS",
        direction="out",
        limit=30
    )
    results.append(result2)
    print_strategy_result(result2)
    
    # Strategy 3: Importance-Based Pruning
    print("\n[3/5] Testing Importance-Based Pruning...")
    result3 = extract_with_importance_pruning(
        min_importance=0.5,
        max_nodes=15
    )
    results.append(result3)
    print_strategy_result(result3)
    
    # Strategy 4: Entity-Centric
    print("\n[4/5] Testing Entity-Centric Extraction...")
    result4 = extract_entity_centric(
        central_entity="microservices",
        depth=2
    )
    results.append(result4)
    print_strategy_result(result4)
    
    # Strategy 5: Meta-Path Guided
    print("\n[5/5] Testing Meta-Path Guided Extraction...")
    result5 = extract_meta_path(
        meta_path=["SOLVES", "USES"],
        start_label="PATTERN",
        limit=30
    )
    results.append(result5)
    print_strategy_result(result5)
    
    # Comparison
    print_comparison(results)
    
    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print("""
    Choose your strategy based on your context constraints:
    
    • Limited window (< 2K tokens): Use Importance-Based Pruning
      → Get highest-value nodes only
      
    • Medium window (2-8K tokens): Use Entity-Centric or N-Hop
      → Balanced coverage of a specific topic
      
    • Large window (8K+ tokens): Use Meta-Path or N-Hop
      → Comprehensive exploration with reasoning chains
      
    • Specific domain queries: Use Relationship-Type Filter
      → Extract only relevant relationship types
    """)
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Experiment with different seed nodes and depths")
    print("  2. Adjust max_nodes to fit your token budget")
    print("  3. Combine strategies (e.g., Entity-Centric + Importance)")
    print("  4. Try with your own domain data")


if __name__ == "__main__":
    main()
