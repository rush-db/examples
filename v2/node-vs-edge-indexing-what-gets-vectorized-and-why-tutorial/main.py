"""
Node vs Edge Indexing Tutorial: What Gets Vectorized and Why It Matters

This tutorial demonstrates the fundamental difference between:
- Node vectorization: indexing properties ON nodes (documents, authors)
- Edge vectorization: indexing properties ON relationships (citations, hierarchies)

You'll learn:
1. How to create vector indexes on node properties
2. How to create vector indexes on edge properties  
3. How to perform semantic search on both
4. When to use node vs edge indexing for different use cases

Key insight: Vectorizing edges captures the "semantic relationship" between entities,
not just the entities themselves.
"""

import os
import time
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
RUSHDB_URL = os.getenv("RUSHDB_URL")

if not API_KEY:
    raise ValueError("API_KEY not found in environment. Copy .env.example to .env and add your key.")

# Initialize RushDB client
db = RushDB(API_KEY, url=RUSHDB_URL) if RUSHDB_URL else RushDB(API_KEY)


def print_section(title):
    """Pretty print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_subsection(title):
    """Pretty print a subsection header."""
    print(f"\n{'─' * 40}")
    print(f"  {title}")
    print(f"{'─' * 40}")


def cleanup_indexes():
    """Remove any existing vector indexes to start fresh."""
    print("\n🧹 Cleaning up existing vector indexes...")
    
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        print(f"  Removing index: {idx['label']}.{idx['propertyName']}")
        db.ai.indexes.delete(idx['__id'])
    
    print("  ✓ Cleanup complete")


def demonstrate_node_indexing():
    """
    SECTION 1: Node Indexing
    
    Node properties contain the primary content of your graph entities.
    When you vectorize node properties, you're enabling semantic search
    across the content of those entities.
    
    Example: Document.content stores the paper's abstract/main text.
    Vectorizing it lets you find semantically similar documents.
    """
    print_section("SECTION 1: Node Indexing")
    
    print("""
    What gets vectorized:
    → Each Document node's 'content' property becomes a vector
    
    What you can search:
    → "Find papers that discuss attention mechanisms"
    → "Find documents about molecular property prediction"
    
    Storage model:
    → Each document has one vector embedding its full content
    """)
    
    print_subsection("Creating node vector index on Document.content")
    
    # Create a vector index on the node property
    node_index = db.ai.indexes.create({
        "label": "Document",
        "propertyName": "content"
    })
    
    print(f"  Index created: {node_index.data.get('__id')}")
    print(f"  Label: Document")
    print(f"  Property: content")
    print(f"  Status: {node_index.data.get('status')}")
    
    # Wait for indexing to complete
    print("\n  ⏳ Waiting for indexing to complete...")
    max_wait = 30
    waited = 0
    while waited < max_wait:
        time.sleep(2)
        waited += 2
        stats = db.ai.indexes.stats(node_index.data.get('__id'))
        indexed = stats.data.get('indexedRecords', 0)
        total = stats.data.get('totalRecords', 0)
        
        print(f"  Progress: {indexed}/{total} records indexed")
        
        if indexed >= total and total > 0:
            break
    
    print("\n✅ Node index ready!")
    return node_index.data.get('__id')


def demonstrate_edge_indexing():
    """
    SECTION 2: Edge Indexing
    
    Edge properties contain metadata ABOUT the relationship between entities.
    When you vectorize edge properties, you're enabling semantic search
    across the semantics of HOW entities relate to each other.
    
    Example: CITES.excerpt stores WHY one paper cites another.
    Vectorizing it lets you find citation relationships by semantic relevance.
    
    Key insight: The excerpt explains THE RELATIONSHIP, not the documents themselves.
    """
    print_section("SECTION 2: Edge Indexing")
    
    print("""
    What gets vectorized:
    → Each CITES edge's 'excerpt' property becomes a vector
    
    What you can search:
    → "Find citations that discuss bidirectional attention"
    → "Find edges where the citation reason relates to transformers"
    
    Storage model:
    → Each citation relationship has its own vector embedding its excerpt
    
    Why this matters:
    → Two papers might both be about "transformers"
    → But their CITES.excerpt might capture DIFFERENT reasons for citing
    → Edge vectorization captures the semantic context of the relationship
    """)
    
    print_subsection("Creating edge vector index on CITES.excerpt")
    
    # Create a vector index on the edge property
    edge_index = db.ai.indexes.create({
        "label": "CITES",
        "propertyName": "excerpt"
    })
    
    print(f"  Index created: {edge_index.data.get('__id')}")
    print(f"  Label: CITES")
    print(f"  Property: excerpt")
    print(f"  Status: {edge_index.data.get('status')}")
    
    # Wait for indexing to complete
    print("\n  ⏳ Waiting for indexing to complete...")
    max_wait = 30
    waited = 0
    while waited < max_wait:
        time.sleep(2)
        waited += 2
        stats = db.ai.indexes.stats(edge_index.data.get('__id'))
        indexed = stats.data.get('indexedRecords', 0)
        total = stats.data.get('totalRecords', 0)
        
        print(f"  Progress: {indexed}/{total} edge records indexed")
        
        if indexed >= total and total > 0:
            break
    
    print("\n✅ Edge index ready!")
    return edge_index.data.get('__id')


def demonstrate_node_search(node_index_id):
    """
    SECTION 3: Semantic Search on Nodes
    
    Use node search when you want to find entities based on their content.
    Example: "Find documents similar to this query about attention mechanisms"
    """
    print_section("SECTION 3: Node Search - Finding Similar Documents")
    
    queries = [
        "attention mechanisms and transformer architectures",
        "molecular graphs and chemical properties"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: \"{query}\"")
        print("-" * 50)
        
        results = db.ai.search({
            "propertyName": "content",
            "query": query,
            "labels": ["Document"],
            "limit": 3
        })
        
        for i, result in enumerate(results.data, 1):
            title = result.get("title", "Unknown")
            score = result.score
            print(f"\n  {i}. {title}")
            print(f"     Score: {score:.4f}")
            # Truncate content for display
            content = result.get("content", "")[:100] + "..."
            print(f"     Content preview: {content}")
    
    return results.data


def demonstrate_edge_search(edge_index_id):
    """
    SECTION 4: Semantic Search on Edges
    
    Use edge search when you want to find relationships based on their
    semantic context. Example: "Find citations where the excerpt discusses
    bidirectional attention"
    
    Important: When searching edges, RushDB returns the edge itself.
    You can traverse to connected nodes to get full context.
    """
    print_section("SECTION 4: Edge Search - Finding Semantic Relationships")
    
    queries = [
        "bidirectional self-attention mechanism",
        "message passing graph neural networks"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: \"{query}\"")
        print("-" * 50)
        
        # Search the edge index
        results = db.ai.search({
            "propertyName": "excerpt",
            "query": query,
            "labels": ["CITES"],
            "limit": 3
        })
        
        for i, result in enumerate(results.data, 1):
            excerpt = result.get("excerpt", "")
            score = result.score
            print(f"\n  {i}. Citation excerpt (score: {score:.4f})")
            print(f"     \"{excerpt[:150]}...\"")
            
            # Note: The result contains the edge, we could traverse to source/target nodes
            # by finding the records connected via CITES relationship
            record_id = result.id
            print(f"     Edge ID: {record_id}")
    
    return results.data


def demonstrate_hybrid_search():
    """
    SECTION 5: Hybrid Search - Combining Node and Edge Context
    
    Real-world applications often need both:
    1. Find relevant documents (node search)
    2. Understand HOW those documents relate (edge search)
    
    This demonstrates the power of having both indexed.
    """
    print_section("SECTION 5: Hybrid Search Pattern")
    
    print("""
    Use case: Research paper discovery
    
    Step 1: Find papers about "language model scaling"
    Step 2: Explore WHY they cite other papers (edge excerpts)
    Step 3: Build a citation graph with semantic context
    """)
    
    # Step 1: Find relevant papers
    print_subsection("Step 1: Find relevant papers")
    
    node_results = db.ai.search({
        "propertyName": "content",
        "query": "language model scaling and few-shot learning",
        "labels": ["Document"],
        "limit": 5
    })
    
    papers_by_id = {r.id: r for r in node_results.data}
    
    print(f"Found {len(node_results.data)} relevant papers:\n")
    for paper in node_results.data:
        print(f"  • {paper.get('title')} (score: {paper.score:.3f})")
    
    # Step 2: Find citation excerpts related to those papers
    print_subsection("Step 2: Find citation context for those papers")
    
    for paper in node_results.data[:3]:
        paper_id = paper.id
        paper_title = paper.get('title', '')
        
        # Find papers that cite THIS paper
        citing_papers = db.records.find({
            "labels": ["Document"],
            "where": {
                "CITES": {
                    "$relation": {"type": "CITES", "direction": "out"},
                    "$targetId": paper_id
                }
            }
        })
        
        # Find papers that THIS paper cites
        cited_papers = db.records.find({
            "labels": ["Document"],
            "where": {
                "CITES": {
                    "$relation": {"type": "CITES", "direction": "in"},
                    "$targetId": paper_id
                }
            }
        })
        
        print(f"\n  📄 {paper_title}")
        print(f"     Cited by: {len(citing_papers.data)} papers")
        print(f"     Cites: {len(cited_papers.data)} papers")
        
        # Step 3: Get edge excerpts for semantic understanding
        if citing_papers.data or cited_papers.data:
            edge_results = db.ai.search({
                "propertyName": "excerpt",
                "query": "transformer architecture extension",
                "labels": ["CITES"],
                "limit": 3
            })
            
            if edge_results.data:
                print(f"     Top citation excerpts about transformers:")
                for edge in edge_results.data[:2]:
                    excerpt = edge.get("excerpt", "")[:100]
                    print(f"       → \"{excerpt}...\"")


def show_index_statistics(node_index_id, edge_index_id):
    """Display statistics for both indexes."""
    print_section("INDEX STATISTICS")
    
    print("\nNode Index (Document.content):")
    node_stats = db.ai.indexes.stats(node_index_id)
    print(f"  Indexed Records: {node_stats.data.get('indexedRecords', 0)}")
    print(f"  Total Records: {node_stats.data.get('totalRecords', 0)}")
    
    print("\nEdge Index (CITES.excerpt):")
    edge_stats = db.ai.indexes.stats(edge_index_id)
    print(f"  Indexed Edge Records: {edge_stats.data.get('indexedRecords', 0)}")
    print(f"  Total Edge Records: {edge_stats.data.get('totalRecords', 0)}")


def main():
    """Run the complete tutorial."""
    print("\n" + "=" * 60)
    print("  NODE VS EDGE INDEXING: WHAT GETS VECTORIZED AND WHY")
    print("  RushDB Tutorial")
    print("=" * 60)
    
    print("""
    Welcome! This tutorial demonstrates the fundamental difference
    between vectorizing node properties vs edge properties in RushDB.
    
    We'll build a research paper knowledge graph and show you how to
    enable semantic search on both documents AND citation relationships.
    
    Prerequisites:
    - Run `python seed.py` first to create the sample data
    - Ensure your API key has vector indexing enabled
    """)
    
    # Check data exists
    docs = db.records.find({"labels": ["Document"], "limit": 1})
    if not docs.data:
        print("⚠️  No Document nodes found. Please run `python seed.py` first!\n")
        return
    
    print("✅ Found Document nodes, ready to begin tutorial...\n")
    input("Press Enter to continue (or Ctrl+C to exit)...")
    
    # Clean up existing indexes
    cleanup_indexes()
    
    # Run tutorial sections
    node_index_id = demonstrate_node_indexing()
    edge_index_id = demonstrate_edge_indexing()
    
    # Show index statistics
    show_index_statistics(node_index_id, edge_index_id)
    
    # Demonstrate search capabilities
    demonstrate_node_search(node_index_id)
    demonstrate_edge_search(edge_index_id)
    
    # Show hybrid search pattern
    demonstrate_hybrid_search()
    
    # Final summary
    print_section("SUMMARY: When to Use Node vs Edge Indexing")
    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │  NODE INDEXING (e.g., Document.content)                     │
    ├─────────────────────────────────────────────────────────────┤
    │  Use when you want to find ENTITIES based on their content  │
    │  Examples:                                                  │
    │    • Find documents similar to a query                     │
    │    • Search product descriptions                            │
    │    • Match user profiles by interests                       │
    │                                                             │
    │  Best for: Entity-centric search                            │
    └─────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────┐
    │  EDGE INDEXING (e.g., CITES.excerpt)                        │
    ├─────────────────────────────────────────────────────────────┤
    │  Use when you want to find RELATIONSHIPS by their context  │
    │  Examples:                                                  │
    │    • Find citations with specific reasoning                 │
    │    • Search comments by sentiment/topic                    │
    │    • Find hierarchies by semantic meaning                   │
    │                                                             │
    │  Best for: Relationship-centric search                      │
    └─────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────┐
    │  HYBRID APPROACH (use both)                                 │
    ├─────────────────────────────────────────────────────────────┤
    │  Use when you need both entity AND relationship context     │
    │  Examples:                                                  │
    │    • Academic literature discovery                          │
    │    • Recommendation systems with explanation                │
    │    • Knowledge graph with semantic edges                    │
    │                                                             │
    │  Best for: Complex knowledge applications                    │
    └─────────────────────────────────────────────────────────────┘
    
    Key insight: Vectorizing edges captures the "semantic relationship"
    between entities, not just the entities themselves. This enables
    powerful graph-aware semantic search patterns.
    
    📚 Learn more: https://docs.rushdb.com/features/vector-search
    """)
    
    print("\n✅ Tutorial complete!\n")


if __name__ == "__main__":
    main()
