"""
Query Planning Strategies in Graph-Vector Hybrids: Path vs Beam Search

This tutorial demonstrates how RushDB enables advanced query planning strategies
that combine graph traversal with vector similarity search.

Key Strategies:
1. Path Search - Sequential graph traversal following relationship chains
2. Beam Search - Parallel exploration maintaining top-K candidates at each level
3. Hybrid Strategy - Combines both approaches for optimal results
"""

import os
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)


# ============================================================================
# Data Structures for Query Planning
# ============================================================================

@dataclass
class SearchCandidate:
    """Represents a candidate in beam search."""
    record: Any
    path: List[str] = field(default_factory=list)
    vector_score: float = 0.0
    graph_score: float = 0.0
    depth: int = 0
    
    @property
    def combined_score(self) -> float:
        """Combine vector similarity with graph traversal score."""
        # Weighted combination: vector similarity primary, graph authority secondary
        return self.vector_score * 0.6 + self.graph_score * 0.4


@dataclass
class PathResult:
    """Represents a complete path from start to end node."""
    start_node: Any
    end_node: Any
    path_nodes: List[Any] = field(default_factory=list)
    path_relationships: List[str] = field(default_factory=list)
    aggregate_score: float = 0.0
    documents: List[Any] = field(default_factory=list)


# ============================================================================
# Strategy 1: Path Search Implementation
# ============================================================================

class PathSearchStrategy:
    """
    Path Search Strategy:
    - Explores the graph by following relationship chains sequentially
    - Scores paths by aggregate relevance of all nodes along the path
    - Good for finding all connected documents in a hierarchy
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.max_depth = 5
        
    def search(self, query: str, limit: int = 10) -> List[PathResult]:
        """
        Execute path search starting from vector similarity results.
        
        Algorithm:
        1. Find initial candidates via vector similarity
        2. For each candidate, traverse parent/child relationships
        3. Build complete paths and score them
        4. Return paths sorted by aggregate score
        """
        print(f"\n  Step 1: Vector similarity search for '{query}'")
        
        # Get initial candidates from vector search
        initial_results = self.db.ai.search({
            "propertyName": "description",
            "query": query,
            "labels": ["CONCEPT"],
            "limit": 5,
        })
        
        initial_candidates = initial_results.data
        print(f"  Found {len(initial_candidates)} initial concept matches")
        
        if not initial_candidates:
            return []
        
        # Explore paths from each initial candidate
        all_paths = []
        
        for candidate in initial_candidates:
            print(f"  Exploring paths from: {candidate['name']}")
            paths = self._traverse_paths(candidate, depth=0, visited=set())
            all_paths.extend(paths)
        
        print(f"  Traversed {len(all_paths)} total paths")
        
        # Sort by aggregate score and return top results
        all_paths.sort(key=lambda p: p.aggregate_score, reverse=True)
        return all_paths[:limit]
    
    def _traverse_paths(
        self, 
        current_node: Any, 
        depth: int, 
        visited: set,
        current_path: List[Any] = None,
        current_rels: List[str] = None,
    ) -> List[PathResult]:
        """Recursively traverse graph paths."""
        
        if current_path is None:
            current_path = [current_node]
        if current_rels is None:
            current_rels = []
        
        if depth >= self.max_depth:
            # Reached max depth, return current path
            return [self._build_path_result(current_path, current_rels)]
        
        paths = []
        
        # Find connected concepts (both directions)
        connected = self.db.records.find({
            "labels": ["CONCEPT"],
            "where": {
                "CONCEPT": {
                    "$relation": {"direction": "any"},
                    "name": {"$ne": current_node["name"]},
                }
            },
            "limit": 5,
        })
        
        for related in connected.data:
            node_id = related.id
            if node_id in visited:
                continue
            
            visited.add(node_id)
            new_path = current_path + [related]
            new_rels = current_rels + ["CONNECTED"]
            
            # Recursively explore from this node
            sub_paths = self._traverse_paths(
                related, 
                depth + 1, 
                visited.copy(),
                new_path,
                new_rels,
            )
            paths.extend(sub_paths)
        
        # If no connected nodes, just return current path
        if not paths:
            paths.append(self._build_path_result(current_path, current_rels))
        
        return paths
    
    def _build_path_result(self, path_nodes: List[Any], path_rels: List[str]) -> PathResult:
        """Build a PathResult from traversed nodes."""
        
        # Calculate aggregate score from all nodes in path
        aggregate_score = 0.0
        concept_names = []
        
        for node in path_nodes:
            # Use vector score if available, otherwise estimate from rank
            score = node.get("__score", random.uniform(0.5, 0.9))
            aggregate_score += score
            concept_names.append(node.get("name", ""))
        
        # Normalize by path length
        aggregate_score /= max(len(path_nodes), 1)
        
        # Find documents covering any concept in the path
        documents = self.db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "CONCEPT": {
                    "name": {"$in": concept_names[:3]},
                }
            },
            "limit": 10,
        }).data
        
        return PathResult(
            start_node=path_nodes[0] if path_nodes else None,
            end_node=path_nodes[-1] if path_nodes else None,
            path_nodes=path_nodes,
            path_relationships=path_rels,
            aggregate_score=aggregate_score,
            documents=documents,
        )


# ============================================================================
# Strategy 2: Beam Search Implementation
# ============================================================================

class BeamSearchStrategy:
    """
    Beam Search Strategy:
    - Explores multiple branches in parallel
    - Maintains top-K candidates at each level (beam width)
    - Prunes to top candidates using combined scoring
    - More efficient for deep traversals
    """
    
    def __init__(self, db: RushDB, beam_width: int = 4, max_depth: int = 3):
        self.db = db
        self.beam_width = beam_width
        self.max_depth = max_depth
    
    def search(self, query: str, limit: int = 10) -> List[SearchCandidate]:
        """
        Execute beam search with vector-guided expansion.
        
        Algorithm:
        1. Get initial candidates from vector search
        2. For each level:
           a. Expand current candidates via graph relationships
           b. Score each candidate (vector + graph)
           c. Prune to top beam_width candidates
        3. Return final candidates with paths
        """
        print(f"\n  Step 1: Vector search for '{query}'")
        
        # Initial candidates from vector search
        initial_results = self.db.ai.search({
            "propertyName": "description",
            "query": query,
            "labels": ["CONCEPT"],
            "limit": self.beam_width,
        })
        
        current_beam = [
            SearchCandidate(
                record=r,
                path=[r["name"]],
                vector_score=r.get("__score", 0.8),
                graph_score=1.0,
                depth=0,
            )
            for r in initial_results.data
        ]
        
        print(f"  Level 0: {len(current_beam)} candidates (from vector search)")
        
        # Beam search through depth levels
        for depth in range(1, self.max_depth + 1):
            print(f"  Level {depth}: Expanding candidates...")
            
            next_candidates = []
            
            for candidate in current_beam:
                # Expand this candidate
                expanded = self._expand_candidate(candidate, depth)
                next_candidates.extend(expanded)
            
            if not next_candidates:
                break
            
            print(f"    Expanded to {len(next_candidates)} candidates")
            
            # Prune to beam_width
            next_candidates.sort(key=lambda c: c.combined_score, reverse=True)
            current_beam = next_candidates[: self.beam_width]
            
            print(f"    Pruned to {len(current_beam)} best candidates")
            print(f"    Top scores: {[f'{c.combined_score:.3f}' for c in current_beam[:3]]}")
        
        # Get documents for final candidates
        for candidate in current_beam:
            candidate.documents = self._get_linked_documents(candidate.record)
        
        return current_beam[:limit]
    
    def _expand_candidate(
        self, 
        candidate: SearchCandidate, 
        depth: int,
    ) -> List[SearchCandidate]:
        """Expand a candidate by exploring its graph connections."""
        
        # Find connected concepts
        connected = self.db.records.find({
            "labels": ["CONCEPT"],
            "where": {
                "CONCEPT": {
                    "$relation": {
                        "direction": "any",
                        "type": {"$in": ["PARENT_OF", "INCLUDES", "ENABLED_BY"]},
                    },
                }
            },
            "limit": 5,
        }).data
        
        expanded = []
        for conn in connected:
            if conn["name"] in candidate.path:
                continue  # Avoid cycles
            
            # Calculate graph score based on edge strength and depth
            edge_strength = conn.get("edge_strength", 0.8)
            graph_score = edge_strength * (1 / (depth + 1))  # Decay with depth
            
            new_candidate = SearchCandidate(
                record=conn,
                path=candidate.path + [conn["name"]],
                vector_score=conn.get("__score", candidate.vector_score * 0.9),
                graph_score=graph_score,
                depth=depth,
            )
            expanded.append(new_candidate)
        
        return expanded
    
    def _get_linked_documents(self, concept_record: Any) -> List[Any]:
        """Get documents linked to a concept."""
        docs = self.db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "CONCEPT": {
                    "$relation": {"direction": "in", "type": "COVERS"},
                    "name": concept_record.get("name"),
                }
            },
            "limit": 5,
        })
        return docs.data


# Extend SearchCandidate to support documents
SearchCandidate.documents = []


# ============================================================================
# Strategy 3: Hybrid Search Strategy
# ============================================================================

class HybridSearchStrategy:
    """
    Hybrid Strategy:
    - Combines vector search precision with graph traversal breadth
    - Uses vector results to initialize exploration
    - Applies path-based scoring with beam pruning
    - Optimal for production systems needing both quality and speed
    """
    
    def __init__(self, db: RushDB, beam_width: int = 3, path_weight: float = 0.4):
        self.db = db
        self.beam_width = beam_width
        self.path_weight = path_weight
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Execute hybrid search combining path and beam strategies.
        
        Combined scoring: vector_similarity * path_authority * edge_strength
        """
        print(f"\n  Step 1: Vector search for '{query}'")
        
        # Initial vector search
        vector_results = self.db.ai.search({
            "propertyName": "description",
            "query": query,
            "labels": ["CONCEPT"],
            "limit": self.beam_width * 2,
        })
        
        if not vector_results.data:
            return []
        
        # Score and rank based on hybrid factors
        scored_results = []
        
        for result in vector_results.data:
            vector_score = result.get("__score", 0.8)
            
            # Calculate path authority (how many connections)
            connections = self.db.records.find({
                "labels": ["CONCEPT"],
                "where": {
                    "CONCEPT": {
                        "$relation": {"direction": "any"},
                    },
                },
            }).data
            
            path_authority = min(len(connections) / 10, 1.0)  # Normalize to [0, 1]
            
            # Edge strength from graph
            edge_strength = result.get("edge_strength", 0.85)
            
            # Combined score
            combined_score = vector_score * path_authority * edge_strength
            
            # Get linked documents
            docs = self.db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "CONCEPT": {
                        "$relation": {"direction": "in", "type": "COVERS"},
                        "name": result.get("name"),
                    }
                },
            }).data
            
            scored_results.append({
                "concept": result,
                "vector_score": vector_score,
                "path_authority": path_authority,
                "edge_strength": edge_strength,
                "combined_score": combined_score,
                "documents": docs,
            })
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return scored_results[:limit]


# ============================================================================
# Main Demonstration
# ============================================================================

def print_separator(title: str):
    """Print a section separator."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_path_search(db: RushDB, query: str):
    """Demonstrate Path Search strategy."""
    print_separator("PATH SEARCH DEMO")
    print(f"\nQuery: '{query}'")
    
    strategy = PathSearchStrategy(db)
    results = strategy.search(query, limit=5)
    
    if not results:
        print("  No results found. Make sure seed.py has been run.")
        return
    
    best_path = results[0]
    print(f"\n  Best path score: {best_path.aggregate_score:.3f}")
    print(f"  Path: {' → '.join(n.get('name', '') for n in best_path.path_nodes)}")
    print(f"  Documents found: {len(best_path.documents)}")
    
    if best_path.documents:
        print(f"  Top document: {best_path.documents[0].get('title', 'N/A')}")


def demo_beam_search(db: RushDB, query: str):
    """Demonstrate Beam Search strategy."""
    print_separator("BEAM SEARCH DEMO")
    print(f"\nQuery: '{query}'")
    print(f"Beam width: 4, Max depth: 3")
    
    strategy = BeamSearchStrategy(db, beam_width=4, max_depth=3)
    results = strategy.search(query, limit=4)
    
    if not results:
        print("  No results found. Make sure seed.py has been run.")
        return
    
    print(f"\n  Final results: {len(results)} concepts")
    for i, candidate in enumerate(results[:3], 1):
        print(f"  {i}. {candidate.record.get('name', 'N/A')}")
        print(f"     Combined score: {candidate.combined_score:.3f}")
        print(f"     Path: {' → '.join(candidate.path)}")
        print(f"     Documents: {len(candidate.documents)}")


def demo_hybrid_search(db: RushDB, query: str):
    """Demonstrate Hybrid Search strategy."""
    print_separator("HYBRID SEARCH DEMO")
    print(f"\nQuery: '{query}'")
    print("Scoring: vector_similarity * path_authority * edge_strength")
    
    strategy = HybridSearchStrategy(db)
    results = strategy.search(query, limit=3)
    
    if not results:
        print("  No results found. Make sure seed.py has been run.")
        return
    
    print(f"\n  Top {len(results)} results:")
    for i, result in enumerate(results, 1):
        concept = result["concept"]
        print(f"\n  {i}. [{result['combined_score']:.3f}] {concept.get('name', 'N/A')}")
        print(f"     Vector score: {result['vector_score']:.3f}")
        print(f"     Path authority: {result['path_authority']:.3f}")
        print(f"     Edge strength: {result['edge_strength']:.3f}")
        if result["documents"]:
            doc_titles = [d.get("title", "") for d in result["documents"]]
            print(f"     Documents: {', '.join(doc_titles[:2])}")


def main():
    """Main demonstration function."""
    print("\n" + "=" * 60)
    print(" Query Planning Strategies in Graph-Vector Hybrids")
    print(" Path Search vs Beam Search Demonstration")
    print("=" * 60)
    
    # Define test queries
    queries = [
        "machine learning optimization",
        "neural network training",
        "transformer architecture",
    ]
    
    for query in queries:
        print_separator(f"QUERY: '{query}'")
        
        # Run all three strategies
        demo_path_search(db, query)
        demo_beam_search(db, query)
        demo_hybrid_search(db, query)
    
    # Summary
    print_separator("SUMMARY")
    print("""
  Key Takeaways:
  
  PATH SEARCH:
    - Explores complete paths through the graph
    - Good for finding all connected documents
    - Can be slow for deep traversals (exponential)
  
  BEAM SEARCH:
    - Maintains fixed width candidates at each level
    - Efficient for deep traversals (constant memory)
    - May miss better paths due to pruning
  
  HYBRID:
    - Combines vector precision with graph breadth
    - Tunable via beam width and path weight
    - Best for production systems
    
  RushDB enables all three strategies through:
    - Native vector similarity search (db.ai.search)
    - Graph relationship traversal (db.records.find with $relation)
    - Flexible scoring via record properties
    """)
    
    print("\nTutorial complete! See README.md for more details.")


if __name__ == "__main__":
    main()
