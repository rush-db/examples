#!/usr/bin/env python3
"""
Subgraph-Aware Prompt Assembly System Demo

This script demonstrates how to build a prompt assembly system that leverages
RushDB's graph traversal capabilities for intelligent context retrieval.

Key patterns demonstrated:
1. BFS traversal for broad context gathering
2. DFS traversal for deep dependency chains
3. Relevance-weighted retrieval
4. Topic-based context assembly
5. Dependency-aware prompt ordering
"""

import os
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from collections import deque

# Ensure we're using the local rushdb package
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize RushDB client
API_KEY = os.environ.get("RUSHDB_API_KEY")
if not API_KEY:
    print("Error: RUSHDB_API_KEY environment variable not set")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(API_KEY)

# Optional: self-hosted URL
# db = RushDB(API_KEY, url=os.environ.get("RUSHDB_URL", "https://localhost/api/v1"))


@dataclass
class SubgraphNode:
    """Represents a node in the subgraph context."""
    record: Any
    depth: int = 0
    relationship_path: list = field(default_factory=list)
    relevance_score: float = 1.0


class PromptAssembler:
    """
    Assembles prompts by traversing the knowledge graph in RushDB.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.max_context_nodes = 15
    
    def assemble_bfs_context(self, query: str, start_labels: list[str], 
                             start_where: dict, max_depth: int = 2) -> dict:
        """
        Breadth-First Search traversal for gathering broad context.
        
        Best for: Getting comprehensive overview of related concepts.
        """
        print("\n  [Strategy: BFS Traversal]")
        
        # Start with initial query
        initial_nodes = self.db.records.find({
            "labels": start_labels,
            "where": start_where,
            "limit": 5
        })
        
        if not initial_nodes:
            return {"prompt": query, "nodes": [], "strategy": "bfs"}
        
        visited = {n.id for n in initial_nodes}
        queue = deque([(n, 0) for n in initial_nodes])
        context_nodes = [n for n in initial_nodes]
        
        # BFS traversal
        while queue and len(context_nodes) < self.max_context_nodes:
            current, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            # Find related nodes by querying through relationships
            # Look for documents that define this concept
            if current.label == "CONCEPT":
                related_docs = self.db.records.find({
                    "labels": ["DOCUMENT"],
                    "where": {
                        "DEFINES": {"$id": current.id}
                    },
                    "limit": 3
                })
                
                for doc in related_docs:
                    if doc.id not in visited:
                        visited.add(doc.id)
                        context_nodes.append(doc)
                        queue.append((doc, depth + 1))
            
            # Look for related concepts
            related_concepts = self.db.records.find({
                "labels": ["CONCEPT"],
                "where": {
                    "RELATES_TO": {"$id": current.id}
                },
                "limit": 2
            })
            
            for concept in related_concepts:
                if concept.id not in visited:
                    visited.add(concept.id)
                    context_nodes.append(concept)
                    queue.append((concept, depth + 1))
        
        prompt = self._build_prompt(query, context_nodes, "bfs")
        return {"prompt": prompt, "nodes": context_nodes, "strategy": "bfs"}
    
    def assemble_dfs_context(self, concept_name: str, max_depth: int = 3) -> dict:
        """
        Depth-First Search traversal for deep dependency chains.
        
        Best for: Understanding prerequisite chains and deep topic exploration.
        """
        print("\n  [Strategy: DFS Traversal]")
        
        # Find the starting concept
        concepts = self.db.records.find({
            "labels": ["CONCEPT"],
            "where": {"name": concept_name}
        })
        
        if not concepts:
            return {"prompt": f"Explore {concept_name}", "nodes": [], "strategy": "dfs"}
        
        start = concepts[0]
        visited = set()
        context_nodes = []
        
        def dfs(node: Any, depth: int):
            if depth >= max_depth or node.id in visited:
                return
            
            visited.add(node.id)
            context_nodes.append(node)
            
            # Get dependencies first (depth-first)
            if node.label == "CONCEPT":
                dependencies = self.db.records.find({
                    "labels": ["CONCEPT"],
                    "where": {
                        "DEPENDS_ON": {"$id": node.id}
                    }
                })
                
                for dep in dependencies:
                    dfs(dep, depth + 1)
            
            # Then get defining documents
            if node.label == "CONCEPT":
                defining_docs = self.db.records.find({
                    "labels": ["DOCUMENT"],
                    "where": {
                        "DEFINES": {"$id": node.id}
                    },
                    "limit": 1
                })
                
                for doc in defining_docs:
                    if doc.id not in visited:
                        dfs(doc, depth + 1)
        
        dfs(start, 0)
        
        prompt = self._build_prompt(
            f"Explore {concept_name} and its dependencies",
            context_nodes,
            "dfs"
        )
        
        return {"prompt": prompt, "nodes": context_nodes, "strategy": "dfs"}
    
    def assemble_relevance_weighted_context(self, query: str, keywords: list[str]) -> dict:
        """
        Relevance-weighted retrieval based on keyword matching.
        
        Best for: Focused, high-precision context retrieval.
        """
        print("\n  [Strategy: Relevance-Weighted]")
        
        scored_nodes = []
        
        # Search concepts matching keywords
        for keyword in keywords:
            concepts = self.db.records.find({
                "labels": ["CONCEPT"],
                "where": {
                    "$or": [
                        {"name": {"$contains": keyword}},
                        {"definition": {"$contains": keyword}}
                    ]
                },
                "limit": 10
            })
            
            for concept in concepts:
                relevance = 1.0 if keyword.lower() in concept["name"].lower() else 0.7
                scored_nodes.append((concept, relevance))
        
        # Get documents for top concepts
        concept_nodes = [n for n, _ in scored_nodes]
        concept_nodes = concept_nodes[:5]
        
        for concept in concept_nodes:
            docs = self.db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "DEFINES": {"$id": concept.id}
                },
                "limit": 1
            })
            
            for doc in docs:
                score = next((s for n, s in scored_nodes if n.id == concept.id), 1.0)
                scored_nodes.append((doc, score * 0.9))
        
        # Sort by relevance and limit
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        scored_nodes = scored_nodes[:self.max_context_nodes]
        
        context_nodes = [n for n, _ in scored_nodes]
        
        prompt = self._build_prompt(query, context_nodes, "relevance")
        return {
            "prompt": prompt,
            "nodes": context_nodes,
            "strategy": "relevance",
            "scores": [s for _, s in scored_nodes]
        }
    
    def assemble_topic_context(self, topic_name: str, query: str) -> dict:
        """
        Topic-based context assembly - gather all related concepts and docs.
        
        Best for: Building comprehensive context for a subject area.
        """
        print(f"\n  [Strategy: Topic-Based ({topic_name})]")
        
        # Find the topic
        topics = self.db.records.find({
            "labels": ["TOPIC"],
            "where": {"name": topic_name}
        })
        
        if not topics:
            return {"prompt": query, "nodes": [], "strategy": "topic"}
        
        topic = topics[0]
        context_nodes = []
        
        # Get all concepts in this topic
        concepts = self.db.records.find({
            "labels": ["CONCEPT"],
            "where": {
                "BELONGS_TO": {"$id": topic.id}
            },
            "limit": 8
        })
        context_nodes.extend(concepts)
        
        # Get defining documents for each concept
        for concept in concepts[:4]:
            docs = self.db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "DEFINES": {"$id": concept.id}
                },
                "limit": 1
            })
            context_nodes.extend(docs)
        
        # Get examples
        for concept in concepts[:3]:
            examples = self.db.records.find({
                "labels": ["EXAMPLE"],
                "where": {
                    "ILLUSTRATES": {"$id": concept.id}
                },
                "limit": 1
            })
            context_nodes.extend(examples)
        
        context_nodes = context_nodes[:self.max_context_nodes]
        
        prompt = self._build_prompt(query, context_nodes, "topic")
        return {"prompt": prompt, "nodes": context_nodes, "strategy": "topic", "topic": topic_name}
    
    def assemble_dependency_chain(self, concept_name: str, query: str) -> dict:
        """
        Extract and order context based on dependency chains.
        
        Best for: Learning paths and understanding prerequisites.
        """
        print(f"\n  [Strategy: Dependency Chain ({concept_name})]")
        
        # Find starting concept
        concepts = self.db.records.find({
            "labels": ["CONCEPT"],
            "where": {"name": concept_name}
        })
        
        if not concepts:
            return {"prompt": query, "nodes": [], "strategy": "dependency"}
        
        start = concepts[0]
        
        # Build dependency graph
        dependency_chain = []
        visited = set()
        
        def collect_dependencies(concept: Any):
            """Recursively collect all dependencies."""
            if concept.id in visited:
                return
            visited.add(concept.id)
            
            # Get what this concept depends on
            dependencies = self.db.records.find({
                "labels": ["CONCEPT"],
                "where": {
                    "DEPENDS_ON": {"$id": concept.id}
                }
            })
            
            # Process dependencies first (they should come first in the prompt)
            for dep in dependencies:
                collect_dependencies(dep)
            
            # Add concept after its dependencies
            dependency_chain.append(concept)
        
        collect_dependencies(start)
        
        # Add defining documents for each concept in order
        ordered_context = []
        for concept in dependency_chain:
            ordered_context.append(concept)
            
            docs = self.db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "DEFINES": {"$id": concept.id}
                },
                "limit": 1
            })
            ordered_context.extend(docs)
        
        ordered_context = ordered_context[:self.max_context_nodes]
        
        prompt = self._build_prompt(query, ordered_context, "dependency")
        return {
            "prompt": prompt,
            "nodes": ordered_context,
            "strategy": "dependency",
            "dependency_order": [n.get("name", n.get("title", "")) for n in dependency_chain[:5]]
        }
    
    def _build_prompt(self, query: str, nodes: list, strategy: str) -> str:
        """Build a structured prompt from gathered context nodes."""
        
        # Group nodes by label
        by_label = {"CONCEPT": [], "DOCUMENT": [], "TOPIC": [], "EXAMPLE": []}
        for node in nodes:
            if node.label in by_label:
                by_label[node.label].append(node)
        
        sections = []
        
        # Add concepts section
        if by_label["CONCEPT"]:
            concepts_text = "\n".join([
                f"- **{c.get('name', 'Unknown')}**: {c.get('definition', 'No definition')[:100]}..."
                for c in by_label["CONCEPT"]
            ])
            sections.append(f"## Relevant Concepts\n{concepts_text}")
        
        # Add documents section
        if by_label["DOCUMENT"]:
            docs_text = "\n".join([
                f"- *{c.get('title', 'Untitled')}* ({c.get('type', 'guide')}): {c.get('content', '')[:80]}..."
                for c in by_label["DOCUMENT"]
            ])
            sections.append(f"## Reference Documents\n{docs_text}")
        
        # Add examples section
        if by_label["EXAMPLE"]:
            examples_text = "\n".join([
                f"- *{c.get('title', 'Example')}* ({c.get('language', 'text')}):\n```\n{c.get('code', '')[:100]}...\n```"
                for c in by_label["EXAMPLE"]
            ])
            sections.append(f"## Code Examples\n{examples_text}")
        
        context_section = "\n\n".join(sections)
        
        prompt = f"""Based on the following knowledge graph context, please answer the query.

--- CONTEXT ---
{context_section if context_section else "No relevant context found."}

--- QUERY ---
{query}

--- INSTRUCTIONS ---
Use the context above to provide a comprehensive answer. Reference specific concepts and documents where relevant."""
        
        return prompt


def demonstrate_bfs_assembly(assembler: PromptAssembler):
    """Demonstrate BFS-based prompt assembly."""
    print("\n" + "=" * 60)
    print("[1] BFS Traversal Strategy")
    print("=" * 60)
    print("\nQuery: Explain authentication and related security concepts")
    
    result = assembler.assemble_bfs_context(
        query="Explain authentication and related security concepts",
        start_labels=["CONCEPT"],
        start_where={"domain": "security"},
        max_depth=2
    )
    
    print(f"   Found {len(result['nodes'])} context nodes")
    concepts = [n for n in result['nodes'] if n.label == "CONCEPT"]
    docs = [n for n in result['nodes'] if n.label == "DOCUMENT"]
    print(f"   Concepts: {len(concepts)}, Documents: {len(docs)}")
    
    print("\n📝 Generated Prompt Preview:")
    print("-" * 40)
    print(result["prompt"][:500] + "..." if len(result["prompt"]) > 500 else result["prompt"])


def demonstrate_dfs_assembly(assembler: PromptAssembler):
    """Demonstrate DFS-based prompt assembly."""
    print("\n" + "=" * 60)
    print("[2] DFS Traversal Strategy")
    print("=" * 60)
    print("\nQuery: Deep dive into CQRS and its dependencies")
    
    result = assembler.assemble_dfs_context(concept_name="cqrs", max_depth=3)
    
    print(f"   Found {len(result['nodes'])} nodes in dependency chain")
    print(f"   Traversal order preserved dependencies")
    
    print("\n📝 Generated Prompt Preview:")
    print("-" * 40)
    print(result["prompt"][:500] + "..." if len(result["prompt"]) > 500 else result["prompt"])


def demonstrate_relevance_assembly(assembler: PromptAssembler):
    """Demonstrate relevance-weighted assembly."""
    print("\n" + "=" * 60)
    print("[3] Relevance-Weighted Strategy")
    print("=" * 60)
    print("\nQuery: How to implement caching and optimization")
    
    result = assembler.assemble_relevance_weighted_context(
        query="How to implement caching and optimization",
        keywords=["caching", "performance", "optimization"]
    )
    
    print(f"   Found {len(result['nodes'])} relevant nodes")
    if "scores" in result:
        print(f"   Top relevance scores: {result['scores'][:3]}")
    
    print("\n📝 Generated Prompt Preview:")
    print("-" * 40)
    print(result["prompt"][:500] + "..." if len(result["prompt"]) > 500 else result["prompt"])


def demonstrate_topic_assembly(assembler: PromptAssembler):
    """Demonstrate topic-based assembly."""
    print("\n" + "=" * 60)
    print("[4] Topic-Based Assembly")
    print("=" * 60)
    print("\nQuery: What should I know about API design?")
    
    result = assembler.assemble_topic_context(
        topic_name="api-design",
        query="What should I know about API design?"
    )
    
    print(f"   Topic: {result.get('topic', 'N/A')}")
    print(f"   Found {len(result['nodes'])} context nodes")
    
    concepts = [n for n in result['nodes'] if n.label == "CONCEPT"]
    print(f"   Concepts included: {[c.get('name') for c in concepts[:5]]}")
    
    print("\n📝 Generated Prompt Preview:")
    print("-" * 40)
    print(result["prompt"][:500] + "..." if len(result["prompt"]) > 500 else result["prompt"])


def demonstrate_dependency_chain(assembler: PromptAssembler):
    """Demonstrate dependency chain assembly."""
    print("\n" + "=" * 60)
    print("[5] Dependency Chain Assembly")
    print("=" * 60)
    print("\nQuery: Explain authorization and its prerequisites")
    
    result = assembler.assemble_dependency_chain(
        concept_name="authorization",
        query="Explain authorization and its prerequisites"
    )
    
    print(f"   Found {len(result['nodes'])} nodes")
    if "dependency_order" in result:
        print(f"   Dependency order: {' -> '.join(result['dependency_order'])}")
    
    print("\n📝 Generated Prompt Preview:")
    print("-" * 40)
    print(result["prompt"][:600] + "..." if len(result["prompt"]) > 600 else result["prompt"])


def show_graph_stats():
    """Display current graph statistics."""
    print("\n" + "=" * 60)
    print("[Graph Statistics]")
    print("=" * 60)
    
    # Get record counts by label
    labels = db.labels.find({})
    
    print("\nRecord counts by label:")
    for label in labels:
        print(f"   {label.name}: {label.count}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("   SUBGRAPH-AWARE PROMPT ASSEMBLY SYSTEM")
    print("   Building Contextual Prompts with RushDB")
    print("=" * 60)
    
    # Initialize assembler
    assembler = PromptAssembler(db)
    
    # Show current graph stats
    show_graph_stats()
    
    # Run all demonstrations
    demonstrate_bfs_assembly(assembler)
    demonstrate_dfs_assembly(assembler)
    demonstrate_relevance_assembly(assembler)
    demonstrate_topic_assembly(assembler)
    demonstrate_dependency_chain(assembler)
    
    print("\n" + "=" * 60)
    print("   Demo Complete!")
    print("=" * 60)
    print("\n📚 Key Takeaways:")
    print("""
   1. BFS Strategy: Best for broad overview of related concepts
   2. DFS Strategy: Best for deep dives into specific topics
   3. Relevance-Weighted: Best for precision-focused queries
   4. Topic-Based: Best for comprehensive subject coverage
   5. Dependency Chain: Best for learning paths and prerequisites

   The graph structure in RushDB enables natural relationship
   traversal, making it ideal for building context-aware prompts.
""")


if __name__ == "__main__":
    main()
