#!/usr/bin/env python3
"""
Graph-backed Prompt Chaining: Multi-step reasoning using RushDB subgraphs.

This script demonstrates composing RushDB subgraphs for a multi-step reasoning 
pipeline. Each stage:
1. Queries a specific subgraph (CONCEPT → DECISION → TRADEOFF)
2. Passes results to the LLM for conclusion generation
3. Stores the conclusion as a new node
4. Uses the conclusion to scope the next query

The chain demonstrates: question → subgraph query → conclusion → 
next subgraph → final synthesized answer.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
db = RushDB(token=os.getenv("RUSHDB_TOKEN"))


class MockLLM:
    """
    Mock LLM for demonstration purposes.
    In production, replace with OpenAI/Anthropic API calls.
    
    This mock:
    - Analyzes the subgraph content
    - Generates contextually relevant conclusions
    - Determines which subgraph to query next
    """
    
    STAGE_PROGRESSION = {
        "concept": "decision",
        "decision": "tradeoff",
        "tradeoff": None  # Final stage
    }
    
    def generate_conclusion(self, stage: str, nodes: list, question: str) -> tuple[str, str]:
        """
        Generate a conclusion based on subgraph nodes.
        
        Returns:
            tuple: (conclusion_text, next_stage or None)
        """
        if not nodes:
            return "No relevant information found in this subgraph.", None
        
        # Extract node names/titles for the summary
        node_names = []
        for node in nodes:
            if "name" in node.data:
                node_names.append(node.data["name"])
            elif "title" in node.data:
                node_names.append(node.data["title"])
            elif "dimension" in node.data:
                node_names.append(node.data["dimension"])
        
        node_list = ", ".join(node_names) if node_names else "none"
        
        # Generate stage-specific conclusions
        if stage == "concept":
            conclusion = (
                f"Based on concepts: {node_list}. "
                f"Key insight: Implementing distributed caching requires careful "
                f"consideration of consistency models. The choice between strong "
                f"coherency and eventual consistency fundamentally impacts system "
                f"behavior and complexity."
            )
            next_stage = "decision"
            
        elif stage == "decision":
            conclusion = (
                f"Architecture decisions identified: {node_list}. "
                f"Key guidance: The cache placement and invalidation strategy "
                f"form a configuration matrix that determines cache hit rates, "
                f"latency, and consistency guarantees. A tiered approach with "
                f"event-driven invalidation provides the best balance for most systems."
            )
            next_stage = "tradeoff"
            
        elif stage == "tradeoff":
            conclusion = (
                f"Critical tradeoffs: {node_list}. "
                f"Synthesis: The latency vs consistency tradeoff is primary. "
                f"Strong consistency adds 10-50ms overhead. Eventual consistency "
                f"risks stale reads but improves availability. The availability vs "
                f"consistency tradeoff determines partition tolerance behavior."
            )
            next_stage = None  # Final stage
        else:
            conclusion = f"Processed {len(nodes)} nodes at stage: {stage}"
            next_stage = None
        
        return conclusion, next_stage
    
    def synthesize_final_answer(self, conclusions: list[str]) -> str:
        """
        Synthesize a final answer from all stage conclusions.
        """
        answer = """
For implementing caching in a distributed system, follow this structured approach:

1. CONCEPTUAL FOUNDATION
   - Understand the distinction between cache coherency (strong consistency) 
     and eventual consistency
   - Cache coherency requires coordination overhead but guarantees fresh reads
   - Eventual consistency allows stale reads but improves performance and availability

2. ARCHITECTURE DECISIONS
   - Use a tiered caching approach:
     • Client-side cache: frequently read, rarely updated data
     • Server-side cache: shared application state
     • CDN cache: static assets and media
   - Implement hybrid invalidation:
     • TTL-based expiration for general caching
     • Event-driven invalidation for critical data changes
     • Manual purging for administrative operations

3. KEY TRADE-OFFS TO CONSIDER
   - Latency vs Consistency: Strong consistency adds 10-50ms per operation
   - Availability vs Consistency: Choose eventual consistency for high-availability systems
   - Cache Memory vs Accuracy: Larger caches reduce misses but increase stale-read risk
   - Complexity vs Flexibility: Start simple, add sophistication only when needed

4. RECOMMENDED IMPLEMENTATION PATH
   - Begin with TTL-based cache invalidation (simplest)
   - Add event-driven invalidation when consistency requirements are stricter
   - Monitor hit ratios and staleness metrics to tune cache sizes
   - Implement circuit breakers for cache failures to prevent cascading issues
"""
        return answer.strip()


class PromptChain:
    """
    Orchestrates the multi-step reasoning pipeline using RushDB subgraphs.
    """
    
    def __init__(self):
        self.llm = MockLLM()
        self.conclusions = []
        self.stage_history = []
    
    def query_subgraph(self, stage: str, context: str = "") -> list:
        """
        Query the RushDB subgraph for the current stage.
        
        Args:
            stage: Current reasoning stage (concept, decision, tradeoff)
            context: Additional context from previous stages
            
        Returns:
            List of matching nodes from the subgraph
        """
        label_map = {
            "concept": "CONCEPT",
            "decision": "DECISION",
            "tradeoff": "TRADEOFF"
        }
        label = label_map.get(stage, "CONCEPT")
        
        # Base query for the label
        query_params = {
            "labels": [label],
            "limit": 5
        }
        
        # Add domain-specific filtering based on the question context
        if context:
            if "caching" in context.lower():
                query_params["where"] = {
                    "domain": {"$in": ["caching", "distributed-systems"]}
                }
            elif "consistency" in context.lower():
                query_params["where"] = {
                    "domain": {"$in": ["consistency", "distributed-systems"]}
                }
        
        results = db.records.find(query_params)
        
        return results.data if results.data else []
    
    def store_conclusion(self, stage: str, content: str, source_nodes: list, question: str) -> dict:
        """
        Store the LLM conclusion as a CONCLUSION node in RushDB.
        
        Args:
            stage: Current reasoning stage
            content: The conclusion text from LLM
            source_nodes: Nodes that informed this conclusion
            question: The original user question
            
        Returns:
            The created conclusion record
        """
        # Create the conclusion node
        conclusion = db.records.create(
            label="CONCLUSION",
            data={
                "stage": stage,
                "content": content,
                "source_question": question,
                "source_node_count": len(source_nodes),
                "sequence": len(self.conclusions) + 1
            }
        )
        
        # Attach to source nodes for traceability
        for node in source_nodes:
            db.records.attach(
                source=conclusion,
                target=node,
                options={"type": "BASED_ON", "direction": "out"}
            )
        
        return conclusion
    
    def run_chain(self, question: str) -> dict:
        """
        Execute the full prompt chain for a question.
        
        Args:
            question: The user's natural language question
            
        Returns:
            Dict containing all stage results and final answer
        """
        print(f"Question: {question}\n")
        print(f"{'='*60}")
        
        # Stage 1: Query CONCEPT subgraph
        print(f"\n--- Stage 1: Query CONCEPT subgraph ---")
        concept_nodes = self.query_subgraph("concept", question)
        print(f"Found {len(concept_nodes)} related concepts")
        
        for node in concept_nodes:
            print(f"  • {node.data.get('name', 'Unknown')}")
        
        # Generate conclusion for concepts
        conclusion_text, next_stage = self.llm.generate_conclusion(
            "concept", concept_nodes, question
        )
        print(f"\nLLM Conclusion: {conclusion_text}")
        
        # Store conclusion
        conclusion_1 = self.store_conclusion("concept", conclusion_text, concept_nodes, question)
        print(f"Created conclusion node: {conclusion_1.id}")
        self.conclusions.append(conclusion_1)
        
        if next_stage == "decision":
            # Stage 2: Query DECISION subgraph
            print(f"\n--- Stage 2: Query DECISION subgraph ---")
            decision_nodes = self.query_subgraph("decision", conclusion_text)
            print(f"Found {len(decision_nodes)} related decisions")
            
            for node in decision_nodes:
                print(f"  • {node.data.get('title', 'Unknown')}")
            
            # Generate conclusion for decisions
            conclusion_text, next_stage = self.llm.generate_conclusion(
                "decision", decision_nodes, question
            )
            print(f"\nLLM Conclusion: {conclusion_text}")
            
            # Store conclusion
            conclusion_2 = self.store_conclusion("decision", conclusion_text, decision_nodes, question)
            print(f"Created conclusion node: {conclusion_2.id}")
            self.conclusions.append(conclusion_2)
        
        if next_stage == "tradeoff":
            # Stage 3: Query TRADEOFF subgraph
            print(f"\n--- Stage 3: Query TRADEOFF subgraph ---")
            tradeoff_nodes = self.query_subgraph("tradeoff", conclusion_text)
            print(f"Found {len(tradeoff_nodes)} related tradeoffs")
            
            for node in tradeoff_nodes:
                print(f"  • {node.data.get('dimension', 'Unknown')}")
            
            # Generate conclusion for tradeoffs
            conclusion_text, next_stage = self.llm.generate_conclusion(
                "tradeoff", tradeoff_nodes, question
            )
            print(f"\nLLM Conclusion: {conclusion_text}")
            
            # Store conclusion
            conclusion_3 = self.store_conclusion("tradeoff", conclusion_text, tradeoff_nodes, question)
            print(f"Created conclusion node: {conclusion_3.id}")
            self.conclusions.append(conclusion_3)
        
        # Final synthesis
        print(f"\n{'='*60}")
        print(f"--- Final Answer ---\n")
        
        conclusion_texts = [c.data["content"] for c in self.conclusions]
        final_answer = self.llm.synthesize_final_answer(conclusion_texts)
        print(final_answer)
        
        return {
            "question": question,
            "stages": self.conclusions,
            "final_answer": final_answer
        }


def verify_conclusions_in_db():
    """Demonstrate that conclusions are stored and queryable in RushDB."""
    print(f"\n{'='*60}")
    print(f"--- Verifying Conclusions in RushDB ---\n")
    
    # Query all conclusion nodes
    results = db.records.find({
        "labels": ["CONCLUSION"],
        "orderBy": {"field": "sequence", "direction": "asc"}
    })
    
    print(f"Found {len(results.data)} conclusion nodes in the database:\n")
    for conclusion in results.data:
        print(f"  [{conclusion.data['stage'].upper()}] Stage {conclusion.data['sequence']}")
        print(f"    Content: {conclusion.data['content'][:80]}...")
        print(f"    Based on: {conclusion.data['source_node_count']} nodes")
        print()


def main():
    print("=== Graph-Backed Prompt Chaining Demo ===\n")
    
    # Create and run the prompt chain
    chain = PromptChain()
    result = chain.run_chain(
        question="How should I implement caching in a distributed system?"
    )
    
    # Verify conclusions are stored in RushDB
    verify_conclusions_in_db()
    
    print(f"\n{'='*60}")
    print("Prompt chain complete! Conclusions are persisted in RushDB.")
    print("Run again with a different question to see different subgraph traversal.\n")


if __name__ == "__main__":
    main()
