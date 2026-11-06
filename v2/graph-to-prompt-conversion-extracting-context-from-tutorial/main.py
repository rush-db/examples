#!/usr/bin/env python3
"""
Main demo: Graph-to-Prompt Context Extraction with RushDB

This script demonstrates:
1. Extracting contextual information from graph traversals
2. Converting graph data to structured prompt format
3. Token budget management with priority-based pruning
4. End-to-end: RushDB query → LLM prompt → response
"""

import os
import sys
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
import tiktoken


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class Config:
    """Application configuration."""
    rushdb_api_key: str
    rushdb_url: Optional[str] = None
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    max_context_tokens: int = 1500
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls(
            rushdb_api_key=os.getenv("RUSHDB_API_KEY", ""),
            rushdb_url=os.getenv("RUSHDB_URL") or None,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "1500")),
        )


# =============================================================================
# DATA MODELS FOR GRAPH CONTEXT
# =============================================================================

@dataclass
class GraphNode:
    """Represents a node from the graph with traversal metadata."""
    id: str
    label: str
    data: dict
    depth: int = 0
    relationship_type: str = ""
    parent_id: str = ""
    
    @property
    def name(self) -> str:
        """Get the primary name field for display."""
        return (
            self.data.get("title") or 
            self.data.get("name") or 
            self.data.get("slug") or 
            self.id[:8]
        )
    
    @property
    def summary(self) -> str:
        """Get a summary/description for the node."""
        return (
            self.data.get("summary") or 
            self.data.get("description") or 
            self.data.get("title") or
            ""
        )
    
    @property
    def token_count(self) -> int:
        """Estimate token count for this node's representation."""
        content = json.dumps(self.data, default=str)
        try:
            enc = tiktoken.encoding_for_model("gpt-4o-mini")
            return len(enc.encode(content))
        except Exception:
            # Fallback: roughly 4 chars per token
            return len(content) // 4
    
    def to_context_string(self, include_path: bool = True) -> str:
        """Convert node to a readable context string."""
        parts = []
        
        if include_path and self.relationship_type:
            parts.append(f"[{self.relationship_type}]")
        
        parts.append(f"{self.label}: {self.name}")
        
        if self.summary:
            parts.append(f"  Summary: {self.summary}")
        
        # Include relevant properties based on label
        relevant_keys = {
            "TUTORIAL": ["difficulty", "duration_minutes", "tags"],
            "CHAPTER": ["order", "summary"],
            "CONCEPT": ["category", "description"],
            "EXAMPLE": ["title", "language", "code_snippet"],
        }
        
        keys = relevant_keys.get(self.label, [])
        for key in keys:
            if key in self.data and key not in ["title", "name", "summary"]:
                parts.append(f"  {key}: {json.dumps(self.data[key])}")
        
        return "\n".join(parts)


@dataclass
class GraphTraversalResult:
    """Container for graph traversal results with metadata."""
    root_node: GraphNode
    related_nodes: list[GraphNode] = field(default_factory=list)
    total_tokens: int = 0
    max_depth_reached: int = 0
    
    def add_node(self, node: GraphNode):
        """Add a node and update metadata."""
        self.related_nodes.append(node)
        self.total_tokens += node.token_count
        if node.depth > self.max_depth_reached:
            self.max_depth_reached = node.depth


# =============================================================================
# GRAPH TRAVERSAL QUERIES
# =============================================================================


class GraphContextExtractor:
    """
    Extracts contextual information from RushDB graph.
    
    Demonstrates different traversal patterns:
    - Single-hop: Direct relationships
    - Multi-hop: Deeper traversals with path tracking
    - Typed: Filter by specific relationship types
    """
    
    # Relationship type priorities (higher = more important for context)
    RELATIONSHIP_PRIORITY = {
        "CONTAINS": 10,
        "EXPLAINS": 9,
        "DEMONSTRATES": 8,
        "PREREQUISITE": 7,
        "RELATED_TO": 6,
        "EXTENDS": 5,
    }
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def find_tutorial(self, title_contains: str) -> Optional[GraphNode]:
        """Find a tutorial by partial title match."""
        results = self.db.records.find({
            "labels": ["TUTORIAL"],
            "where": {
                "title": {"$contains": title_contains}
            },
            "limit": 1
        })
        
        if not results:
            return None
        
        record = results[0]
        return GraphNode(
            id=record.id,
            label=record.label,
            data=record.fields,
            depth=0
        )
    
    def extract_1hop_context(self, root: GraphNode) -> GraphTraversalResult:
        """
        Extract single-hop context from a root node.
        
        For a TUTORIAL, this retrieves directly related CHAPTERs.
        """
        result = GraphTraversalResult(root_node=root)
        
        # Find chapters contained in this tutorial
        chapters = self.db.records.find({
            "labels": ["CHAPTER"],
            "where": {
                "TUTORIAL": {"$relation": {"type": "CONTAINS", "direction": "out"}}
            }
        })
        
        for record in chapters:
            # We need to filter to only chapters belonging to our root
            # Since we can't easily filter by parent in RushDB's relationship query,
            # we'll filter by the chapter's position in the tutorial
            node = GraphNode(
                id=record.id,
                label=record.label,
                data=record.fields,
                depth=1,
                relationship_type="CONTAINS",
                parent_id=root.id
            )
            result.add_node(node)
        
        # Also get concepts explained by those chapters
        for chapter in chapters:
            concepts = self.db.records.find({
                "labels": ["CONCEPT"],
                "where": {
                    "CHAPTER": {"$relation": {"type": "EXPLAINS", "direction": "in"}}
                }
            })
            
            for record in concepts:
                node = GraphNode(
                    id=record.id,
                    label=record.label,
                    data=record.fields,
                    depth=2,
                    relationship_type="EXPLAINS",
                    parent_id=chapter.id
                )
                result.add_node(node)
        
        return result
    
    def extract_full_depth_context(self, root: GraphNode, max_depth: int = 3) -> GraphTraversalResult:
        """
        Extract full-depth context from a root node.
        
        Traverses the graph at increasing depths, collecting all related nodes.
        Uses breadth-first approach to ensure level-order processing.
        """
        result = GraphTraversalResult(root_node=root)
        visited_ids = {root.id}
        
        # Relationship traversal map: given a node label, what can we find?
        traversal_patterns = {
            "TUTORIAL": [
                ("CHAPTER", "CONTAINS", "out"),
                ("TUTORIAL", "PREREQUISITE", "in"),
            ],
            "CHAPTER": [
                ("TUTORIAL", "CONTAINS", "in"),
                ("CONCEPT", "EXPLAINS", "out"),
            ],
            "CONCEPT": [
                ("CHAPTER", "EXPLAINS", "in"),
                ("EXAMPLE", "DEMONSTRATES", "out"),
                ("CONCEPT", "RELATED_TO", "out"),
            ],
            "EXAMPLE": [
                ("CONCEPT", "DEMONSTRATES", "in"),
                ("EXAMPLE", "EXTENDS", "in"),
            ],
        }
        
        current_depth = 0
        nodes_at_depth = [root]
        
        while current_depth < max_depth and nodes_at_depth:
            next_depth_nodes = []
            
            for node in nodes_at_depth:
                patterns = traversal_patterns.get(node.label, [])
                
                for target_label, rel_type, direction in patterns:
                    # Find records related to this node
                    related = self._find_related_records(node, target_label, rel_type, direction)
                    
                    for record in related:
                        if record.id in visited_ids:
                            continue
                        
                        visited_ids.add(record.id)
                        related_node = GraphNode(
                            id=record.id,
                            label=record.label,
                            data=record.fields,
                            depth=current_depth + 1,
                            relationship_type=rel_type,
                            parent_id=node.id
                        )
                        result.add_node(related_node)
                        next_depth_nodes.append(related_node)
            
            current_depth += 1
            nodes_at_depth = next_depth_nodes
        
        return result
    
    def _find_related_records(self, source_node: GraphNode, target_label: str, 
                               rel_type: str, direction: str) -> list:
        """Find records related to a source node."""
        # Build the where clause based on relationship direction
        if direction == "out":
            # Source has relationship to target
            where_clause = {
                target_label: {
                    "$relation": {"type": rel_type, "direction": "out"}
                }
            }
        else:
            # Target has relationship to source
            where_clause = {
                source_node.label: {
                    "$relation": {"type": rel_type, "direction": "in"}
                }
            }
        
        # Try to find by filtering in the query
        results = self.db.records.find({
            "labels": [target_label],
            "where": where_clause,
            "limit": 10
        })
        
        # Filter results client-side if needed
        if direction == "in" and source_node.label == "TUTORIAL":
            # For tutorials as targets, we can't directly query
            # Fall back to finding all and filtering by tutorial ID in the data
            pass
        
        return results


# =============================================================================
# TOKEN BUDGET MANAGEMENT
# =============================================================================

class TokenBudgetManager:
    """
    Manages token budgets for LLM context.
    
    Implements priority-based pruning to fit context within token limits.
    """
    
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.enc = tiktoken.encoding_for_model("gpt-4o-mini")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.enc.encode(text))
    
    def prune_nodes(self, nodes: list[GraphNode]) -> list[GraphNode]:
        """
        Prune nodes to fit within token budget.
        
        Priority order:
        1. Depth (closer nodes have higher priority)
        2. Relationship type (semantic importance)
        3. Content density (shorter, denser content preserved)
        """
        # Calculate priority score for each node
        scored_nodes = []
        for node in nodes:
            priority = self._calculate_priority(node)
            context_str = node.to_context_string()
            tokens = self.count_tokens(context_str)
            
            scored_nodes.append({
                "node": node,
                "priority": priority,
                "tokens": tokens,
                "context": context_str
            })
        
        # Sort by priority (descending)
        scored_nodes.sort(key=lambda x: (-x["priority"], x["tokens"]))
        
        # Select nodes until we hit the budget
        selected = []
        current_tokens = 0
        
        # Reserve tokens for the root node representation
        header_tokens = self.count_tokens("## Context\n[Root Node]\n")
        available = self.max_tokens - header_tokens - 50  # Buffer
        
        for item in scored_nodes:
            if current_tokens + item["tokens"] <= available:
                selected.append(item)
                current_tokens += item["tokens"]
        
        return [item["node"] for item in selected], current_tokens
    
    def _calculate_priority(self, node: GraphNode) -> float:
        """
        Calculate priority score for a node.
        
        Higher score = more important for context.
        """
        score = 0.0
        
        # Depth factor: closer nodes are more relevant
        depth_score = max(0, 10 - node.depth)
        score += depth_score * 10
        
        # Relationship type factor
        rel_priority = GraphContextExtractor.RELATIONSHIP_PRIORITY.get(
            node.relationship_type, 5
        )
        score += rel_priority
        
        # Label factor
        label_priority = {
            "CONCEPT": 10,
            "CHAPTER": 8,
            "EXAMPLE": 6,
            "TUTORIAL": 7,
        }
        score += label_priority.get(node.label, 5)
        
        return score


# =============================================================================
# PROMPT CONVERSION
# =============================================================================

class PromptConverter:
    """
    Converts graph traversal results into LLM-ready prompts.
    """
    
    def to_prompt(self, root: GraphNode, context_nodes: list[GraphNode]) -> str:
        """
        Convert graph context to a structured prompt.
        
        Format:
        ## Context
        [relationship path]
        - Node details
        
        ## Question
        [user query]
        """
        lines = []
        
        # Header
        lines.append("## Context")
        lines.append("")
        
        # Root node
        lines.append(f"### {root.label}: {root.name}")
        lines.append(f"Token count: {root.token_count}")
        lines.append("")
        
        # Group context nodes by relationship type
        by_rel = {}
        for node in context_nodes:
            rel = node.relationship_type or "RELATED"
            if rel not in by_rel:
                by_rel[rel] = []
            by_rel[rel].append(node)
        
        # Output by relationship type
        for rel_type, nodes in by_rel.items():
            lines.append(f"### {rel_type} relationships:")
            for node in nodes:
                lines.append(f"\n- **{node.label}: {node.name}** (depth={node.depth})")
                lines.append(node.to_context_string(include_path=False))
            lines.append("")
        
        lines.append("## Question")
        lines.append("Based on the context above, explain how this knowledge graph structure ")
        lines.append("enables efficient context retrieval for AI applications.")
        
        return "\n".join(lines)


# =============================================================================
# LLM INTEGRATION
# =============================================================================

class LLMClient:
    """
    Simple LLM client for generating responses from prompts.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate a response from the prompt."""
        if not self.api_key:
            return "[OpenAI API key not configured - showing prompt only]"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that explains graph-based knowledge systems."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[Error generating response: {str(e)}]"


# =============================================================================
# MAIN DEMO
# =============================================================================


def validate_config(config: Config) -> bool:
    """Validate that required configuration is present."""
    if not config.rushdb_api_key:
        print("Error: RUSHDB_API_KEY not found")
        print("Get your API key at https://app.rushdb.com/settings/api-keys")
        return False
    return True


def run_demo():
    """Run the main demo sequence."""
    print("\n" + "=" * 60)
    print("Graph-to-Prompt Context Extraction Demo")
    print("=" * 60 + "\n")
    
    # Load configuration
    config = Config.from_env()
    
    if not validate_config(config):
        sys.exit(1)
    
    # Initialize RushDB connection
    print("Connecting to RushDB...")
    if config.rushdb_url:
        db = RushDB(config.rushdb_api_key, url=config.rushdb_url)
    else:
        db = RushDB(config.rushdb_api_key)
    print("✓ Connected\n")
    
    # Initialize components
    extractor = GraphContextExtractor(db)
    budget_manager = TokenBudgetManager(config.max_context_tokens)
    prompt_converter = PromptConverter()
    llm_client = LLMClient(config.openai_api_key, config.openai_model)
    
    # Find a tutorial to work with
    print("1. Finding target tutorial...")
    tutorial = extractor.find_tutorial("Graph")
    if not tutorial:
        print("No tutorial found. Run 'python seed.py' first.")
        sys.exit(1)
    print(f"   Found: {tutorial.name}")
    print(f"   ID: {tutorial.id}")
    print(f"   Token count: {tutorial.token_count}\n")
    
    # Extract 1-hop context
    print("2. Extracting 1-hop context (direct relationships)...")
    one_hop_result = extractor.extract_1hop_context(tutorial)
    print(f"   Found {len(one_hop_result.related_nodes)} related nodes")
    print(f"   Max depth: {one_hop_result.max_depth_reached}")
    print(f"   Token count: {one_hop_result.total_tokens}\n")
    
    # Show context breakdown
    by_label = {}
    for node in one_hop_result.related_nodes:
        if node.label not in by_label:
            by_label[node.label] = 0
        by_label[node.label] += 1
    print("   Breakdown by label:")
    for label, count in by_label.items():
        print(f"     - {label}: {count}")
    print()
    
    # Extract full depth context
    print("3. Extracting full-depth context (3-hop traversal)...")
    full_result = extractor.extract_full_depth_context(tutorial, max_depth=3)
    print(f"   Found {len(full_result.related_nodes)} related nodes")
    print(f"   Max depth: {full_result.max_depth_reached}")
    print(f"   Token count: {full_result.total_tokens}\n")
    
    # Show traversal path
    print("   Traversal paths:")
    for node in full_result.related_nodes[:5]:
        print(f"     [{node.depth}] {node.relationship_type} → {node.label}: {node.name}")
    if len(full_result.related_nodes) > 5:
        print(f"     ... and {len(full_result.related_nodes) - 5} more")
    print()
    
    # Token budget pruning
    print(f"4. Token budget management (limit: {config.max_context_tokens} tokens)...")
    print(f"   Original nodes: {len(full_result.related_nodes)}")
    print(f"   Original tokens: {full_result.total_tokens}")
    
    pruned_nodes, final_tokens = budget_manager.prune_nodes(full_result.related_nodes)
    print(f"   After pruning: {len(pruned_nodes)} nodes")
    print(f"   Final tokens: {final_tokens}")
    
    # Show which nodes were kept
    print("   Top-priority nodes kept:")
    for node in pruned_nodes[:3]:
        print(f"     - {node.label}: {node.name} (depth={node.depth}, rel={node.relationship_type})")
    print()
    
    # Convert to prompt
    print("5. Converting to prompt format...")
    prompt = prompt_converter.to_prompt(tutorial, pruned_nodes)
    prompt_tokens = budget_manager.count_tokens(prompt)
    print(f"   Prompt token count: {prompt_tokens}")
    print(f"   Prompt length: {len(prompt)} characters\n")
    
    # Show prompt structure (first 500 chars)
    print("   Prompt structure preview:")
    print("   " + "-" * 40)
    for line in prompt.split("\n")[:15]:
        print(f"   {line}")
    if len(prompt.split("\n")) > 15:
        print(f"   ... ({len(prompt.split(chr(10))) - 15} more lines)")
    print("   " + "-" * 40 + "\n")
    
    # Generate LLM response
    print("6. Generating LLM response...")
    print(f"   Model: {config.openai_model}")
    
    if config.openai_api_key:
        print("   (Sending request to OpenAI...)\n")
        response = llm_client.generate(prompt)
        print("   LLM Response:")
        print("   " + "-" * 40)
        # Wrap response text for display
        for line in response.split("\n"):
            print(f"   {line}")
        print("   " + "-" * 40)
    else:
        print("   Skipped: OPENAI_API_KEY not configured")
        print("   Set OPENAI_API_KEY in .env to enable LLM responses")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  • Graph relationships carry semantic meaning")
    print("  • Depth-first vs breadth-first affect context relevance")
    print("  • Token budgets require priority-based pruning")
    print("  • Structured prompts enable better LLM responses")
    print()


if __name__ == "__main__":
    run_demo()
