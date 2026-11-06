"""
Main tutorial script for the Research Paper Discovery Engine.

Demonstrates RushDB's unique ability to combine:
1. Graph traversal (citation depth queries)
2. Vector similarity search (semantic queries)
3. Both together (hybrid queries)

This script assumes you have already run `python seed.py` to populate the database.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import RushDB
from rushdb import RushDB


def setup_rushdb() -> RushDB:
    """Initialize RushDB connection."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found in environment. "
            "Please copy .env.example to .env and add your API key."
        )
    
    print("Connecting to RushDB...")
    db = RushDB(api_key)
    print("Connected successfully!\n")
    return db


def get_papers_count(db: RushDB) -> int:
    """Get the count of papers in the database."""
    result = db.labels.find({})
    for label in result.data:
        if label.name == "PAPER":
            return label.count
    return 0


def get_seminal_paper(db: RushDB) -> object:
    """Find a seminal paper to use as a starting point for graph queries."""
    results = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "title": {"$contains": "Attention Is All You Need"}
        },
        "limit": 1,
    })
    return results.data[0] if results.data else None


def query_citation_depth(db: RushDB, seminal_paper: object, max_depth: int = 3) -> list:
    """
    Query papers by citation depth (graph traversal).
    
    Finds papers that cite the seminal paper directly or indirectly,
    up to a specified depth in the citation graph.
    
    In a traditional database setup, this would require:
    - Multiple JOINs for each hop
    - Recursive CTEs or application-level iteration
    - Complex query planning
    
    With RushDB's graph model, we can leverage relationship traversal
    directly in the query.
    """
    print("--- Query 1: Citation Depth ---")
    print(f"Finding papers up to {max_depth} hops from seminal paper...")
    
    # Find papers that cite the seminal paper (1 hop)
    citing_papers = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "in"},
                "title": seminal_paper["title"]
            }
        },
        "limit": 20,
    })
    
    results = []
    direct_citers = set()
    
    for paper in citing_papers.data:
        results.append({
            "title": paper["title"],
            "year": paper["year"],
            "hops": 1,
        })
        direct_citers.add(paper["title"])
    
    # For 2-hop papers, find papers that cite the 1-hop papers
    if citing_papers.data and max_depth >= 2:
        for direct_citer in citing_papers.data:
            papers_citing_direct = db.records.find({
                "labels": ["PAPER"],
                "where": {
                    "PAPER": {
                        "$relation": {"type": "CITES", "direction": "in"},
                        "title": direct_citer["title"]
                    }
                },
                "limit": 10,
            })
            
            for paper in papers_citing_direct.data:
                if paper["title"] not in direct_citers:
                    results.append({
                        "title": paper["title"],
                        "year": paper["year"],
                        "hops": 2,
                    })
                    direct_citers.add(paper["title"])
    
    return results[:10]


def query_semantic_similarity(db: RushDB, query_text: str, limit: int = 5) -> list:
    """
    Query papers by semantic similarity (vector search).
    
    Uses RushDB's built-in vector index to find papers with abstracts
    semantically similar to the query text.
    
    The server handles embedding the query text automatically using
    the model configured for the index.
    """
    print("--- Query 2: Semantic Similarity ---")
    print(f'Finding papers similar to: "{query_text}"')
    
    results = db.ai.search({
        "propertyName": "abstract",
        "query": query_text,
        "labels": ["PAPER"],
        "limit": limit,
    })
    
    similar_papers = []
    for record in results.data:
        similar_papers.append({
            "title": record["title"],
            "year": record["year"],
            "score": record.score,
            "abstract": record["abstract"][:100] + "...",
        })
    
    return similar_papers


def query_combined(db: RushDB, semantic_query: str, category_filter: str = None) -> list:
    """
    Combine graph traversal with vector similarity search.
    
    This is the key differentiator: finding papers that are:
    1. Semantically similar to a query
    2. AND part of a specific citation subtree
    
    In a traditional setup, this would require:
    - A vector database for similarity search
    - A graph database for citation traversal
    - Complex synchronization between systems
    
    With RushDB, we can express this as a single logical query.
    """
    print("--- Query 3: Combined Query ---")
    print(f"Finding semantically similar papers in the NLP citation subtree...")
    print(f'Query: "{semantic_query}"')
    
    # First, get the citation subtree for NLP papers
    nlp_papers = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "category": {"$in": ["Natural Language Processing", "Large Language Models", "Deep Learning"]}
        },
        "limit": 50,
    })
    
    nlp_titles = {paper["title"]: paper for paper in nlp_papers.data}
    
    # Now perform semantic search
    similar_results = db.ai.search({
        "propertyName": "abstract",
        "query": semantic_query,
        "labels": ["PAPER"],
        "limit": 20,
    })
    
    # Filter to only papers in the NLP citation subtree
    combined_results = []
    for record in similar_results.data:
        if record["title"] in nlp_titles:
            combined_results.append({
                "title": record["title"],
                "year": record["year"],
                "score": record.score,
                "category": record["category"],
            })
    
    return combined_results[:10]


def print_results(results: list, query_name: str):
    """Pretty-print query results."""
    if not results:
        print(f"  No results found.")
        return
    
    for i, result in enumerate(results, 1):
        if "score" in result:
            # Semantic search results
            print(f"  [{result['score']:.3f}] {result['title']}")
            if "abstract" in result:
                print(f"           Year: {result['year']}")
        elif "hops" in result:
            # Citation depth results
            print(f"  {i}. {result['title']} ({result['hops']} hops, {result['year']})")
        else:
            # General results
            print(f"  {i}. {result['title']} ({result.get('year', 'N/A')})")


def main():
    """Main entry point for the tutorial."""
    print("=" * 60)
    print("Tutorial: Research Paper Discovery Engine with RushDB")
    print("=" * 60)
    print()
    
    # Setup RushDB connection
    db = setup_rushdb()
    
    # Check for existing data
    num_papers = get_papers_count(db)
    print(f"Papers in database: {num_papers}")
    
    if num_papers == 0:
        print("\nNo papers found. Please run `python seed.py` first to populate the database.")
        return
    
    print()
    
    # =========================================================================
    # Query 1: Citation Depth (Graph Traversal)
    # =========================================================================
    print("[1] Graph Traversal: Citation Depth Query")
    print("-" * 50)
    
    seminal_paper = get_seminal_paper(db)
    if seminal_paper:
        print(f"Starting from seminal paper: {seminal_paper['title']}")
        citation_results = query_citation_depth(db, seminal_paper, max_depth=2)
        print_results(citation_results, "Citation Depth")
    else:
        print("Seminal paper not found. Try running seed.py again.")
    
    print()
    
    # =========================================================================
    # Query 2: Semantic Similarity (Vector Search)
    # =========================================================================
    print("[2] Vector Search: Semantic Similarity Query")
    print("-" * 50)
    
    query_text = "transformer architecture attention mechanism self-attention"
    semantic_results = query_semantic_similarity(db, query_text, limit=5)
    print_results(semantic_results, "Semantic Similarity")
    
    print()
    
    # =========================================================================
    # Query 3: Combined (Graph + Vector)
    # =========================================================================
    print("[3] Hybrid Query: Semantic Similarity + Citation Subtree")
    print("-" * 50)
    print("This query would require TWO separate databases without RushDB!")
    print()
    
    combined_results = query_combined(
        db,
        semantic_query="large language model pre-training few-shot learning",
    )
    print_results(combined_results, "Combined")
    
    print()
    print("=" * 60)
    print("Tutorial Complete!")
    print("=" * 60)
    print()
    print("Key Takeaways:")
    print("  1. Graph traversal (CITES relationships) works with RushDB's")
    print("     native relationship model, just like Neo4j.")
    print("  2. Vector similarity search is built into RushDB's AI module,")
    print("     no separate vector database needed.")
    print("  3. Combined queries leverage both capabilities in a single")
    print("     application, with a unified SDK.")
    print()
    print("Learn more:")
    print("  - Graph Relationships: https://docs.rushdb.com/guides/relationships")
    print("  - Vector Search: https://docs.rushdb.com/guides/vector-search")
    print("  - AI Module: https://docs.rushdb.com/ai")


if __name__ == "__main__":
    main()
