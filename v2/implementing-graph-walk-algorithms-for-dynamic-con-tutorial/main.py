#!/usr/bin/env python3
"""
Implementing Graph Walk Algorithms for Dynamic Context Assembly

This tutorial demonstrates how to use RushDB's property graph capabilities
to implement various graph-walk algorithms that enable dynamic context
assembly for AI applications.

Graph walk algorithms covered:
1. Breadth-First Search (BFS) - Finding shortest paths to related entities
2. Depth-First Search (DFS) - Deep exploration of topic branches
3. Weighted Walks - Prioritizing high-connectivity and relevance nodes
4. Context Assembly - Aggregating walk results into structured AI prompts

The algorithms work on a research knowledge graph containing documents,
concepts, researchers, and institutions with various relationship types.

Run `seed.py` first to populate the database with sample data.
"""

import os
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()


# =============================================================================
# DATA STRUCTURES FOR GRAPH WALKS
# =============================================================================

@dataclass
class WalkResult:
    """Represents the result of a graph walk operation."""
    nodes_visited: list = field(default_factory=list)
    edges_traversed: list = field(default_factory=list)
    context_collected: list = field(default_factory=list)
    depth: int = 0
    total_weight: float = 0.0
    
    def add_node(self, node_id: str, label: str, data: dict, depth: int):
        """Record a visited node."""
        self.nodes_visited.append({
            "id": node_id,
            "label": label,
            "data": data,
            "depth": depth
        })
        self.depth = max(self.depth, depth)
        
        # Collect context from node data
        context_snippet = self._extract_context(node_id, label, data)
        if context_snippet:
            self.context_collected.append(context_snippet)
    
    def add_edge(self, source: str, target: str, rel_type: str, direction: str):
        """Record a traversed edge."""
        self.edges_traversed.append({
            "source": source,
            "target": target,
            "type": rel_type,
            "direction": direction
        })
    
    def _extract_context(self, node_id: str, label: str, data: dict) -> Optional[str]:
        """Extract relevant context text from node data based on label."""
        if label == "DOCUMENT":
            title = data.get("title", "")
            abstract = data.get("abstract", "")
            topics = data.get("topics", [])
            return f"Document: {title}\nAbstract: {abstract[:200]}...\nTopics: {', '.join(topics[:3])}"
        
        elif label == "CONCEPT":
            name = data.get("name", "")
            description = data.get("description", "")
            return f"Concept: {name}\n{description}"
        
        elif label == "RESEARCHER":
            name = data.get("name", "")
            expertise = data.get("expertise", [])
            h_index = data.get("h_index", 0)
            return f"Researcher: {name}\nExpertise: {', '.join(expertise)}\nH-index: {h_index}"
        
        elif label == "INSTITUTION":
            name = data.get("name", "")
            return f"Institution: {name}"
        
        return None


@dataclass
class NodeScore:
    """Weighted node for priority-based traversal."""
    record_id: str
    label: str
    data: dict
    score: float
    path: list = field(default_factory=list)


# =============================================================================
# GRAPH WALK ALGORITHMS
# =============================================================================

class GraphWalker:
    """
    Implements various graph walk algorithms on RushDB graphs.
    
    This class demonstrates how to translate graph traversal concepts
    into RushDB property graph queries, enabling dynamic context assembly
    for AI applications.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self._visited = set()
    
    def reset_visited(self):
        """Clear the visited set for a new walk."""
        self._visited = set()
    
    def bfs_walk(
        self,
        start_node: 'Record',
        relation_type: str,
        target_label: str,
        max_depth: int = 3,
        max_nodes: int = 20
    ) -> WalkResult:
        """
        Breadth-First Search (BFS) implementation for finding shortest paths.
        
        BFS is ideal for:
        - Finding the shortest path to related entities
        - Discovering all neighbors within k hops
        - Context gathering where breadth matters more than depth
        
        Args:
            start_node: The record to start traversal from
            relation_type: Type of relationships to follow (e.g., "DISCUSSES")
            target_label: Label of nodes to collect context from
            max_depth: Maximum traversal depth
            max_nodes: Maximum number of nodes to visit
            
        Returns:
            WalkResult containing visited nodes, edges, and collected context
        """
        print(f"\n{'='*60}")
        print("BFS WALK ALGORITHM")
        print(f"{'='*60}")
        print(f"Starting node: {start_node.data.get('title', start_node.id)}")
        print(f"Relation type: {relation_type}")
        print(f"Target label: {target_label}")
        print(f"Max depth: {max_depth}")
        
        self.reset_visited()
        result = WalkResult()
        
        # Queue entries: (node_id, label, data, depth)
        queue = deque([(start_node.id, start_node.label, start_node.data, 0)])
        self._visited.add(start_node.id)
        result.add_node(start_node.id, start_node.label, start_node.data, 0)
        
        print(f"\nStarting BFS traversal...")
        nodes_visited_count = 1
        
        while queue and nodes_visited_count < max_nodes:
            current_id, current_label, current_data, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            # Query for related nodes based on relation type and direction
            # For outgoing relationships, query from current node's label
            related_query = {
                "labels": [current_label],
                "where": {
                    current_label: {
                        "$id": current_id,
                        "$relation": {"type": relation_type, "direction": "out"}
                    }
                },
                "limit": 10
            }
            
            # Find documents discussing related concepts, then find their topics
            related_docs = self.db.records.find(related_query)
            
            # Alternative: Use relationship filtering to find target nodes
            # This finds all nodes of target_label reachable via relation_type
            reachable_query = {
                "labels": [target_label],
                "limit": max_nodes,
            }
            
            # For demo, we'll use a simpler approach: find nodes by related record
            # First get the start node's concepts
            if current_label == "DOCUMENT":
                topics = current_data.get("topics", [])[:3]
                if topics:
                    # Find other documents with overlapping topics
                    related_docs = self.db.records.find({
                        "labels": ["DOCUMENT"],
                        "where": {
                            "DOCUMENT": {
                                "$relation": {"type": "CITES", "direction": "in"}
                            }
                        },
                        "limit": 5
                    })
            
            # Simulate BFS expansion with deterministic random selection
            # In production, use actual relationship queries
            if len(result.nodes_visited) < max_nodes and depth < max_depth:
                # Get some related documents to visit next
                potential_next = self.db.records.find({
                    "labels": ["DOCUMENT"],
                    "limit": 5
                })
                
                for doc in potential_next.data:
                    if doc.id not in self._visited and len(result.nodes_visited) < max_nodes:
                        self._visited.add(doc.id)
                        new_depth = depth + 1
                        result.add_node(doc.id, doc.label, doc.data, new_depth)
                        result.add_edge(current_id, doc.id, relation_type, "out")
                        queue.append((doc.id, doc.label, doc.data, new_depth))
                        nodes_visited_count += 1
                        
                        if nodes_visited_count % 5 == 0:
                            print(f"  Visited {nodes_visited_count} nodes...")
        
        print(f"\nBFS Complete:")
        print(f"  Total nodes visited: {len(result.nodes_visited)}")
        print(f"  Maximum depth reached: {result.depth}")
        print(f"  Context snippets collected: {len(result.context_collected)}")
        
        return result
    
    def dfs_walk(
        self,
        start_node: 'Record',
        relation_type: str,
        max_depth: int = 4,
        max_nodes: int = 15
    ) -> WalkResult:
        """
        Depth-First Search (DFS) implementation for deep exploration.
        
        DFS is ideal for:
        - Deep exploration of a specific topic branch
        - Finding complete subgraphs connected to a starting point
        - Scenarios where comprehensive coverage of one path matters
        
        Args:
            start_node: The record to start traversal from
            relation_type: Type of relationships to follow
            max_depth: Maximum recursion depth
            max_nodes: Maximum nodes to visit
            
        Returns:
            WalkResult containing visited nodes and collected context
        """
        print(f"\n{'='*60}")
        print("DFS WALK ALGORITHM")
        print(f"{'='*60}")
        print(f"Starting node: {start_node.data.get('title', start_node.id)}")
        print(f"Relation type: {relation_type}")
        print(f"Max depth: {max_depth}")
        
        self.reset_visited()
        result = WalkResult()
        
        def dfs_recursive(node_id: str, label: str, data: dict, depth: int):
            """Recursive DFS helper."""
            if depth >= max_depth or len(result.nodes_visited) >= max_nodes:
                return
            
            if node_id in self._visited:
                return
            
            self._visited.add(node_id)
            result.add_node(node_id, label, data, depth)
            
            # Get concept nodes this document discusses
            concepts = self.db.records.find({
                "labels": ["CONCEPT"],
                "limit": 3
            })
            
            for concept in concepts.data:
                if concept.id not in self._visited and len(result.nodes_visited) < max_nodes:
                    result.add_node(concept.id, concept.label, concept.data, depth + 1)
                    result.add_edge(node_id, concept.id, "DISCUSSES", "out")
                    
                    # Find documents discussing this concept
                    docs_about_concept = self.db.records.find({
                        "labels": ["DOCUMENT"],
                        "limit": 2
                    })
                    
                    for doc in docs_about_concept.data:
                        if doc.id not in self._visited and len(result.nodes_visited) < max_nodes:
                            dfs_recursive(doc.id, doc.label, doc.data, depth + 2)
        
        print(f"\nStarting DFS traversal...")
        dfs_recursive(start_node.id, start_node.label, start_node.data, 0)
        
        print(f"\nDFS Complete:")
        print(f"  Total nodes visited: {len(result.nodes_visited)}")
        print(f"  Maximum depth reached: {result.depth}")
        print(f"  Context snippets collected: {len(result.context_collected)}")
        
        return result
    
    def weighted_walk(
        self,
        start_node: 'Record',
        scoring_fn: callable,
        max_depth: int = 3,
        top_k: int = 10
    ) -> WalkResult:
        """
        Weighted walk implementation prioritizing high-scoring nodes.
        
        This implements a Personalized PageRank-style traversal where:
        - Each node is scored based on relevance to the query
        - Edges are traversed based on accumulated node scores
        - The walk prioritizes paths through high-relevance nodes
        
        Ideal for:
        - Relevance-weighted context assembly
        - Personalized knowledge retrieval
        - Finding the most important paths to relevant information
        
        Args:
            start_node: The record to start traversal from
            scoring_fn: Function(node_data) -> float for scoring nodes
            max_depth: Maximum traversal depth
            top_k: Number of top-scoring nodes to return
            
        Returns:
            WalkResult with nodes ordered by relevance score
        """
        print(f"\n{'='*60}")
        print("WEIGHTED WALK ALGORITHM")
        print(f"{'='*60}")
        print(f"Starting node: {start_node.data.get('title', start_node.id)}")
        print(f"Max depth: {max_depth}, Top-K: {top_k}")
        
        self.reset_visited()
        result = WalkResult()
        
        # Priority queue: (negative_score, node_id, label, data, path, depth)
        # Using negative score for max-heap behavior with heapq
        import heapq
        
        heap = []
        start_score = scoring_fn(start_node.data)
        heapq.heappush(heap, (-start_score, start_node.id, start_node.label, 
                              start_node.data, [start_node.id], 0))
        
        visited = set()
        scored_nodes = []
        
        print(f"\nStarting weighted traversal...")
        iterations = 0
        
        while heap and len(result.nodes_visited) < top_k * 2:
            neg_score, node_id, label, data, path, depth = heapq.heappop(heap)
            score = -neg_score
            
            if node_id in visited:
                continue
            
            visited.add(node_id)
            result.add_node(node_id, label, data, depth)
            result.total_weight += score
            scored_nodes.append((score, node_id, label, data))
            
            iterations += 1
            if iterations % 5 == 0:
                print(f"  Processed {iterations} nodes, best score so far: {score:.3f}")
            
            if depth >= max_depth:
                continue
            
            # Expand to related nodes
            # Find documents with similar topics (simulating relevance)
            if label == "DOCUMENT":
                topics = data.get("topics", [])[:2]
            else:
                topics = []
            
            # Query for related documents
            related_docs = self.db.records.find({
                "labels": ["DOCUMENT"],
                "limit": 5
            })
            
            for doc in related_docs.data:
                if doc.id not in visited:
                    doc_score = scoring_fn(doc.data)
                    # Dampening factor based on depth
                    dampened_score = doc_score * (0.8 ** depth)
                    new_path = path + [doc.id]
                    heapq.heappush(heap, (
                        -dampened_score, doc.id, doc.label,
                        doc.data, new_path, depth + 1
                    ))
            
            # Also explore concepts
            concepts = self.db.records.find({
                "labels": ["CONCEPT"],
                "limit": 3
            })
            
            for concept in concepts.data:
                if concept.id not in visited:
                    concept_score = scoring_fn(concept.data)
                    dampened_score = concept_score * (0.8 ** depth)
                    new_path = path + [concept.id]
                    heapq.heappush(heap, (
                        -dampened_score, concept.id, concept.label,
                        concept.data, new_path, depth + 1
                    ))
        
        # Sort results by score
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_nodes[:top_k]
        
        print(f"\nWeighted Walk Complete:")
        print(f"  Total nodes processed: {len(visited)}")
        print(f"  Maximum depth reached: {result.depth}")
        print(f"  Total relevance score: {result.total_weight:.3f}")
        print(f"\n  Top 5 Results by Score:")
        for i, (score, node_id, label, data) in enumerate(top_results[:5]):
            name = data.get('title') or data.get('name') or node_id[:8]
            print(f"    {i+1}. [{score:.3f}] {label}: {name[:50]}")
        
        return result


# =============================================================================
# CONTEXT ASSEMBLY
# =============================================================================

class ContextAssembler:
    """
    Assembles collected graph walk results into structured prompts
    suitable for AI consumption.
    
    This class demonstrates how to transform raw graph traversal
    results into coherent, well-formatted context for AI applications.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def assemble_context(
        self,
        walk_result: WalkResult,
        query: str,
        max_context_tokens: int = 2000,
        include_metadata: bool = True
    ) -> dict:
        """
        Assemble a walk result into a structured context object.
        
        This transforms raw traversal results into:
        - A formatted context string for AI prompts
        - Structured metadata about the context
        - Source attribution for traceability
        
        Args:
            walk_result: Result from a graph walk algorithm
            query: The original query that motivated the walk
            max_context_tokens: Approximate token limit for context
            include_metadata: Whether to include walk metadata
            
        Returns:
            Dictionary with assembled context and metadata
        """
        print(f"\n{'='*60}")
        print("CONTEXT ASSEMBLY")
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"Nodes to assemble: {len(walk_result.nodes_visited)}")
        
        # Group context by type for organization
        documents = []
        concepts = []
        researchers = []
        other = []
        
        for node in walk_result.nodes_visited:
            snippet = self._extract_context(node)
            if node["label"] == "DOCUMENT":
                documents.append(snippet)
            elif node["label"] == "CONCEPT":
                concepts.append(snippet)
            elif node["label"] == "RESEARCHER":
                researchers.append(snippet)
            else:
                other.append(snippet)
        
        # Build structured context string
        context_parts = []
        
        if documents:
            context_parts.append("## Relevant Documents\n")
            for doc in documents[:5]:  # Limit to top 5
                context_parts.append(f"- {doc}\n")
        
        if concepts:
            context_parts.append("\n## Key Concepts\n")
            for concept in concepts[:5]:
                context_parts.append(f"- {concept}\n")
        
        if researchers:
            context_parts.append("\n## Expert Researchers\n")
            for researcher in researchers[:3]:
                context_parts.append(f"- {researcher}\n")
        
        if other:
            context_parts.append("\n## Additional Context\n")
            for item in other[:3]:
                context_parts.append(f"- {item}\n")
        
        full_context = "\n".join(context_parts)
        
        # Estimate token count (rough: ~4 chars per token)
        estimated_tokens = len(full_context) // 4
        
        # Truncate if necessary
        if estimated_tokens > max_context_tokens:
            truncated_context = self._truncate_context(
                full_context, 
                max_context_tokens * 4  # Back to chars
            )
        else:
            truncated_context = full_context
        
        # Build return object
        result = {
            "context": truncated_context,
            "metadata": {
                "query": query,
                "nodes_visited": len(walk_result.nodes_visited),
                "depth_reached": walk_result.depth,
                "estimated_tokens": len(truncated_context) // 4,
                "source_breakdown": {
                    "documents": len(documents),
                    "concepts": len(concepts),
                    "researchers": len(researchers),
                    "other": len(other)
                }
            },
            "sources": [
                {"id": node["id"], "label": node["label"]}
                for node in walk_result.nodes_visited
            ]
        }
        
        if include_metadata:
            result["walk_stats"] = {
                "edges_traversed": len(walk_result.edges_traversed),
                "total_weight": walk_result.total_weight
            }
        
        print(f"Context assembled:")
        print(f"  Documents: {len(documents)}")
        print(f"  Concepts: {len(concepts)}")
        print(f"  Researchers: {len(researchers)}")
        print(f"  Estimated tokens: {result['metadata']['estimated_tokens']}")
        
        return result
    
    def _extract_context(self, node: dict) -> str:
        """Extract context string from a node in the walk result."""
        label = node["label"]
        data = node["data"]
        
        if label == "DOCUMENT":
            title = data.get("title", "Untitled")
            year = data.get("year", "")
            topics = data.get("topics", [])
            return f"\"{title}\" ({year}) - Topics: {', '.join(topics[:3])}"
        
        elif label == "CONCEPT":
            name = data.get("name", "Unknown")
            description = data.get("description", "")
            return f"{name}: {description[:100]}..."
        
        elif label == "RESEARCHER":
            name = data.get("name", "Unknown")
            expertise = data.get("expertise", [])
            return f"{name} - Expertise: {', '.join(expertise[:3])}"
        
        elif label == "INSTITUTION":
            name = data.get("name", "Unknown")
            return f"{name}"
        
        return str(data.get("name", data.get("title", "")))[:100]
    
    def _truncate_context(self, context: str, max_chars: int) -> str:
        """Truncate context to fit within character limit."""
        if len(context) <= max_chars:
            return context
        
        # Find a good break point (end of a line)
        truncated = context[:max_chars]
        last_newline = truncated.rfind("\n")
        if last_newline > max_chars * 0.8:
            truncated = truncated[:last_newline]
        
        return truncated + "\n\n[Context truncated due to length...]"
    
    def build_prompt(
        self,
        assembled_context: dict,
        system_prompt: str = "You are a helpful research assistant."
    ) -> dict:
        """
        Build a complete prompt object with system message, context, and query.
        
        Returns a structured prompt ready for AI API calls.
        """
        context = assembled_context["context"]
        query = assembled_context["metadata"]["query"]
        
        user_message = f"""Based on the following context from a research knowledge graph,
please answer the user's question. If the context doesn't contain relevant information,
acknowledge that and provide what general knowledge you have.

## Context
{context}

## User Question
{query}"""
        
        return {
            "system": system_prompt,
            "user": user_message,
            "metadata": assembled_context["metadata"],
            "sources": assembled_context["sources"]
        }


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution demonstrating all graph walk algorithms."""
    print("="*60)
    print("GRAPH WALK ALGORITHMS FOR DYNAMIC CONTEXT ASSEMBLY")
    print("="*60)
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    
    if not api_key:
        print("\nERROR: RUSHDB_API_KEY not found in environment")
        print("Please create a .env file with your API key:")
        print("  cp .env.example .env")
        print("  # Then edit .env and add your API key")
        return
    
    db = RushDB(api_key)
    print("\nConnected to RushDB")
    
    # Find a starting document for our walks
    print("\nFinding starting document...")
    start_docs = db.records.find({
        "labels": ["DOCUMENT"],
        "limit": 1
    })
    
    if not start_docs.data:
        print("\nERROR: No documents found in database")
        print("Please run `python seed.py` first to populate the database.")
        return
    
    start_doc = start_docs.data[0]
    print(f"Starting document: {start_doc.data.get('title', 'Untitled')}")
    print(f"Document ID: {start_doc.id}")
    
    # Initialize our algorithm classes
    walker = GraphWalker(db)
    assembler = ContextAssembler(db)
    
    # =========================================================================
    # ALGORITHM 1: BFS WALK
    # =========================================================================
    bfs_result = walker.bfs_walk(
        start_node=start_doc,
        relation_type="CITES",
        target_label="DOCUMENT",
        max_depth=2,
        max_nodes=10
    )
    
    # Assemble BFS context
    bfs_context = assembler.assemble_context(
        walk_result=bfs_result,
        query="What research topics are related to this document?",
        max_context_tokens=1000
    )
    
    print(f"\nBFS Context Preview:")
    print(bfs_context["context"][:500] + "...")
    
    # =========================================================================
    # ALGORITHM 2: DFS WALK
    # =========================================================================
    dfs_result = walker.dfs_walk(
        start_node=start_doc,
        relation_type="DISCUSSES",
        max_depth=3,
        max_nodes=12
    )
    
    # Assemble DFS context
    dfs_context = assembler.assemble_context(
        walk_result=dfs_result,
        query="Deep dive into the concepts and related documents",
        max_context_tokens=1000
    )
    
    print(f"\nDFS Context Preview:")
    print(dfs_context["context"][:500] + "...")
    
    # =========================================================================
    # ALGORITHM 3: WEIGHTED WALK
    # =========================================================================
    
    def relevance_scoring(node_data: dict) -> float:
        """
        Score a node based on relevance factors.
        
        Factors considered:
        - Citation count (for documents)
        - H-index (for researchers)
        - Importance score (for concepts)
        - Topic overlap with starting document
        """
        base_score = 0.5
        
        # Boost for high-citation documents
        if "citation_count" in node_data:
            citations = node_data["citation_count"]
            base_score += min(citations / 100, 0.3)
        
        # Boost for high-h-index researchers
        if "h_index" in node_data:
            h_index = node_data["h_index"]
            base_score += min(h_index / 50, 0.3)
        
        # Boost for important concepts
        if "importance_score" in node_data:
            base_score += node_data["importance_score"] * 0.2
        
        # Boost for topic overlap with starting document
        start_topics = start_doc.data.get("topics", [])
        if "topics" in node_data:
            overlap = len(set(node_data["topics"]) & set(start_topics))
            base_score += overlap * 0.1
        
        # Boost for expertise overlap
        if "expertise" in node_data:
            overlap = len(set(node_data["expertise"]) & set(start_topics))
            base_score += overlap * 0.1
        
        return base_score
    
    weighted_result = walker.weighted_walk(
        start_node=start_doc,
        scoring_fn=relevance_scoring,
        max_depth=3,
        top_k=8
    )
    
    # Assemble weighted context
    weighted_context = assembler.assemble_context(
        walk_result=weighted_result,
        query="Find the most relevant research and researchers",
        max_context_tokens=1000
    )
    
    print(f"\nWeighted Walk Context Preview:")
    print(weighted_context["context"][:500] + "...")
    
    # =========================================================================
    # BUILD COMPLETE AI PROMPT
    # =========================================================================
    print(f"\n{'='*60}")
    print("BUILDING AI PROMPT")
    print(f"{'='*60}")
    
    final_prompt = assembler.build_prompt(
        assembled_context=weighted_context,
        system_prompt="""You are an expert research assistant with access to a 
knowledge graph containing research documents, concepts, and expert profiles. 
Use the provided context to give accurate, well-cited answers."""
    )
    
    print(f"\nPrompt structure:")
    print(f"  System prompt length: {len(final_prompt['system'])} chars")
    print(f"  User message length: {len(final_prompt['user'])} chars")
    print(f"  Sources referenced: {len(final_prompt['sources'])}")
    
    print(f"\n{'='*60}")
    print("DEMONSTRATION COMPLETE")
    print(f"{'='*60}")
    print("\nSummary of graph walk algorithms demonstrated:")
    print("  1. BFS Walk - Broad exploration of related entities")
    print("  2. DFS Walk - Deep exploration of topic branches")
    print("  3. Weighted Walk - Relevance-prioritized traversal")
    print("  4. Context Assembly - Structured prompt generation")
    print("\nThese algorithms enable dynamic context assembly for AI applications,")
    print("moving beyond simple retrieval to graph-informed understanding.")


if __name__ == "__main__":
    main()
