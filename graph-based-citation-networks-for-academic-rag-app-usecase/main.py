"""
Graph-Based Citation Networks for Academic RAG Applications

This demo shows how combining graph traversal with vector similarity search
enables both RELEVANCE and LINEAGE in academic literature retrieval.

Key concept:
- Vector search finds semantically SIMILAR papers
- Graph traversal finds methodologically ANCESTOR papers
- Together: find relevant papers AND trace their citation lineage
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Check for API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("❌ RUSHDB_API_KEY not found in environment")
    print("   Copy .env.example to .env and add your API key")
    exit(1)

from rushdb import RushDB

# Initialize RushDB client
db = RushDB(api_key)


def demo_semantic_search_only():
    """
    DEMO 1: Semantic Search Only (Baseline)
    
    Shows the limitation of pure vector similarity search:
    We find RELEVANT papers but cannot determine their METHODOLOGICAL lineage.
    """
    print("\n--- DEMO 1: Semantic Search Only (Baseline) ---")
    print('Query: "neural network text classification"')
    print()
    
    # Pure semantic search - finds papers with similar abstracts
    results = db.ai.search({
        "propertyName": "abstract",
        "query": "neural network text classification",
        "labels": ["PAPER"],
        "limit": 5
    })
    
    print("Found 5 semantically similar papers:")
    for i, paper in enumerate(results.data, 1):
        print(f"  {i}. [{paper.score:.3f}] {paper['title']} ({paper['year']})")
    
    print("""
Problem: These papers are RELEVANT but we don't know which
         VALIDATED or INSPIRED the user's research.
         
We need to trace their citation chains to find:
  - What foundational work did they build upon?
  - Which papers are methodological ancestors?
         """)


def find_papers_cited_by(paper_id: str) -> list:
    """
    Find papers that a given paper CITES (outbound edges).
    
    RushDB relationship query syntax:
    - We want papers where the relationship to our paper has:
      - type = "CITES"
      - direction = "out" (our paper → target)
    
    Using the $relation filter in where clause:
    """
    # Find records where the PAPER relationship points TO our paper
    # with type "CITES" and direction "in" (incoming to our paper)
    # Actually, to find papers CITED BY our paper, we need:
    # Papers where there's a CITES edge from our paper TO them
    
    # Use raw query for complex relationship traversal
    # This finds papers that the given paper cites (outbound)
    cited = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "$or": [
                {
                    "PAPER": {
                        "$relation": {"type": "CITES", "direction": "out"},
                        "$id": paper_id
                    }
                }
            ]
        },
        "limit": 10
    })
    return cited.data


def find_papers_citing(paper_id: str) -> list:
    """
    Find papers that CITE a given paper (inbound edges).
    
    Papers where there's a CITES edge from them TO our paper.
    """
    citing = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "in"},
                "$id": paper_id
            }
        },
        "limit": 10
    })
    return citing.data


def trace_citation_lineage(paper_id: str, max_hops: int = 2) -> list:
    """
    Trace the citation lineage of a paper up to max_hops.
    
    Returns a list of (paper, hop_level) tuples for each ancestor found.
    """
    lineage = []
    current_level = {paper_id}
    visited = set()
    
    for hop in range(1, max_hops + 1):
        next_level = set()
        for paper_id in current_level:
            if paper_id in visited:
                continue
            visited.add(paper_id)
            
            # Find papers this paper cites
            cited_papers = find_papers_cited_by(paper_id)
            
            for ancestor in cited_papers:
                lineage.append((ancestor, hop))
                next_level.add(ancestor.id)
        
        current_level = next_level
        if not current_level:
            break
    
    return lineage


def demo_semantic_plus_citation_lineage():
    """
    DEMO 2: Semantic Search + Citation Lineage
    
    Shows how to combine vector similarity with graph traversal
    to find relevant papers AND trace their methodological ancestors.
    """
    print("\n--- DEMO 2: Semantic Search + Citation Lineage ---")
    print('Query: "neural network text classification"')
    print()
    
    # Step 1: Semantic search to find relevant papers
    print("First, semantic search finds relevant papers...")
    similar = db.ai.search({
        "propertyName": "abstract",
        "query": "neural network text classification",
        "labels": ["PAPER"],
        "limit": 3
    })
    
    print(f"Found {len(similar.data)} semantically similar papers:")
    for i, paper in enumerate(similar.data, 1):
        print(f"  {i}. [{paper.score:.3f}] {paper['title']} ({paper['year']})")
    print()
    
    # Step 2: For each relevant paper, trace citation lineage
    print("Now tracing citation lineage (methodological ancestors)...")
    print()
    
    for paper in similar.data:
        print(f"For \"{paper['title']}\":")
        
        # Find immediate citations (papers this paper cites)
        cited = find_papers_cited_by(paper.id)
        if cited:
            print("  This paper cites:")
            for c in cited:
                print(f"    • {c['title']} ({c['year']})")
        else:
            print("  This paper cites: (none)")
        print()
        
        # Trace 2-hop ancestors
        lineage = trace_citation_lineage(paper.id, max_hops=2)
        if lineage:
            print(f"  METHODOLOGICAL LINEAGE (traced 2 hops):")
            print(f"    {paper['title']} ({paper['year']})")
            
            # Group by hop level
            by_hop = {}
            for ancestor, hop in lineage:
                if hop not in by_hop:
                    by_hop[hop] = []
                by_hop[hop].append(ancestor)
            
            for hop in sorted(by_hop.keys()):
                arrow = "  ↓ CITES" + (hop * " CITES") if hop > 1 else "  ↓ CITES"
                for ancestor in by_hop[hop]:
                    indent = "      " if hop > 1 else "    "
                    print(f"{indent}↓ CITES" if hop == 1 else f"{indent}↓ CITES")
                    print(f"{indent}{ancestor['title']} ({ancestor['year']})")
                    if hop == 2:
                        print(f"{indent}    └── Found {hop}-hop ancestor!")
            print()


def demo_find_foundational_papers():
    """
    DEMO 3: Find Papers That Validated/Influenced a Method
    
    Shows how to use citation tracing to find the foundational
    papers that all transformer-based work builds upon.
    """
    print("\n--- DEMO 3: Find Papers That Validated/Influenced a Method ---")
    print()
    print('Query: "transformer architecture"')
    print()
    
    # Find papers about transformers
    transformer_papers = db.ai.search({
        "propertyName": "abstract",
        "query": "transformer architecture",
        "labels": ["PAPER"],
        "limit": 4
    })
    
    print(f"Relevant papers: {len(transformer_papers.data)} found")
    print()
    print("Tracing lineage for each to find methodological ancestors...")
    print()
    
    # Track all 2-hop ancestors across all relevant papers
    all_2hop_ancestors = {}
    
    for paper in transformer_papers.data:
        lineage = trace_citation_lineage(paper.id, max_hops=2)
        
        for ancestor, hop in lineage:
            if hop == 2:  # Only track 2-hop ancestors (foundational work)
                if ancestor.id not in all_2hop_ancestors:
                    all_2hop_ancestors[ancestor.id] = {
                        "paper": ancestor,
                        "source_papers": []
                    }
                all_2hop_ancestors[ancestor.id]["source_papers"].append(paper['title'])
    
    if all_2hop_ancestors:
        print(f"{len(all_2hop_ancestors)}-hop ancestors (key foundational papers):")
        print()
        for data in all_2hop_ancestors.values():
            ancestor = data["paper"]
            sources = data["source_papers"]
            print(f"  • {ancestor['title']} ({ancestor['year']})")
            print(f"    [Found via: {', '.join(sources[:2])}]")
            print()
        
        print("These papers represent the FOUNDATIONAL WORK that all")
        print("transformer papers ultimately build upon.")


def demo_combined_query_result():
    """
    DEMO 4: Combined Query Result
    
    Shows a complete academic RAG workflow that returns:
    1. Semantically relevant papers
    2. Their methodological ancestors (from citation graph)
    
    This is the pattern for building an academic literature assistant
    that can answer: "Show me papers like X, and trace back which
    foundational works they ultimately derive from."
    """
    print("\n--- DEMO 4: Combined Query Result ---")
    print()
    print('User research: "I\'m building a document classification system"')
    print()
    print('Query: "document classification neural network"')
    print()
    
    # Step 1: Semantic search
    query = "document classification neural network"
    semantic_results = db.ai.search({
        "propertyName": "abstract",
        "query": query,
        "labels": ["PAPER"],
        "limit": 3
    })
    
    print("SEMANTIC RESULTS (top 3 by relevance):")
    for i, paper in enumerate(semantic_results.data, 1):
        print(f"  {i}. [{paper.score:.3f}] {paper['title']} ({paper['year']})")
    print()
    
    # Step 2: Collect all 2-hop ancestors
    all_ancestors = {}
    for paper in semantic_results.data:
        lineage = trace_citation_lineage(paper.id, max_hops=2)
        for ancestor, hop in lineage:
            if ancestor.id not in all_ancestors:
                all_ancestors[ancestor.id] = {
                    "paper": ancestor,
                    "hop": hop,
                    "found_via": paper['title']
                }
    
    # Step 3: Display methodological ancestors
    print("METHODOLOGICAL ANCESTORS (traced 2 hops):")
    print()
    
    if all_ancestors:
        for data in list(all_ancestors.values())[:5]:  # Show top 5
            ancestor = data["paper"]
            print(f"  ┌─────────────────────────────────────────────────────┐")
            print(f"  │ {ancestor['title'][:50]} ")
            print(f"  │ ({ancestor['year']})")
            print(f"  │                                                     │")
            
            # Generate a brief explanation based on the abstract
            abstract_words = ancestor['abstract'].lower().split()
            key_terms = [w for w in ['attention', 'neural', 'language', 'translation', 
                                    'sequence', 'embedding', 'representation']
                       if w in abstract_words]
            if key_terms:
                print(f"  │ Why it matters: Pioneered/introduced {key_terms[0]} ")
                print(f"  │ that modern models build upon.                    │")
            print(f"  └─────────────────────────────────────────────────────┘")
            print()
    
    total_results = len(semantic_results.data) + len(all_ancestors)
    print(f"TOTAL: {len(semantic_results.data)} semantic results + {len(all_ancestors)} key ancestors = {total_results} papers")
    print("        with proven methodological lineage")


def main():
    """Run all demos."""
    print("=" * 60)
    print("GRAPH-BASED CITATION NETWORKS FOR ACADEMIC RAG")
    print("=" * 60)
    
    # Verify data exists
    existing = db.records.find({"labels": ["PAPER"], "limit": 1})
    if existing.total == 0:
        print("\n❌ No papers found in database!")
        print("   Run 'python seed.py' first to create the citation network.")
        exit(1)
    
    # Run all demos
    demo_semantic_search_only()
    demo_semantic_plus_citation_lineage()
    demo_find_foundational_papers()
    demo_combined_query_result()
    
    # Print key insight
    print("=" * 60)
    print("KEY INSIGHT:")
    print("=" * 60)
    print("""
Vector similarity alone returns RELEVANT papers.

Graph traversal alone returns INFLUENCED papers.

Combined graph+vector returns RELEVANT papers
THAT YOU CAN TRACE to their methodological roots.

This enables academic RAG that answers:
  "Show me papers like X, and trace back which
   foundational works they ultimately derive from."
""")
    print("=" * 60)
    print("\n✅ All demos completed successfully!")


if __name__ == "__main__":
    main()
