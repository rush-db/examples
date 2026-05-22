"""
Research Paper Discovery Engine - Main Demo

This script demonstrates RushDB's combined graph and vector capabilities
for building a research paper discovery engine.

It showcases:
1. Graph traversal for citation network discovery
2. Vector similarity search for semantic relevance
3. Hybrid search combining both approaches
4. A "more like this" endpoint returning both citation and semantic results
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
RUSHDB_TOKEN = os.getenv("RUSHDB_TOKEN")
if not RUSHDB_TOKEN:
    raise ValueError("RUSHDB_TOKEN not found. Please set it in your .env file.")

db = RushDB(RUSHDB_TOKEN)


def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_paper(paper, show_score=False):
    """Print a paper in a formatted way."""
    score_str = f" [score: {paper.score:.4f}]" if show_score and paper.score else ""
    print(f"  📄 {paper.data['title']}{score_str}")
    print(f"     Authors: {', '.join(paper.data['authors'])}")
    print(f"     Venue: {paper.data['venue']} ({paper.data['year']})")
    print(f"     Domain: {paper.data['domain']}")


# =============================================================================
# SCENARIO 1: Citation Network Discovery (Graph Traversal)
# =============================================================================

def demonstrate_citation_network():
    """
    Use graph traversal to discover papers in the citation network.
    
    Given a paper, find:
    - Papers it CITES (outgoing edges) - foundational work
    - Papers that CITE it (incoming edges) - follow-up work
    """
    print_header("SCENARIO 1: Citation Network Discovery")
    print("""
Finding papers related through citation chains.
This is the traditional graph database use case.
""")
    
    # Find the "Attention Is All You Need" paper
    attention_papers = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "title": {"$contains": "Attention Is All You Need"}
        },
        "limit": 1
    })
    
    if not attention_papers.data:
        print("  ❌ Paper 'Attention Is All You Need' not found. Run seed.py first.")
        return
    
    attention_paper = attention_papers.data[0]
    print(f"\nStarting paper: {attention_paper.data['title']}")
    
    # Find papers that THIS paper CITES (foundational work it builds upon)
    print("\n📚 Papers that 'Attention Is All You Need' CITES:")
    papers_cited = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "in"},
                "title": attention_paper.data['title']
            }
        },
        "limit": 10
    })
    
    if papers_cited.data:
        for paper in papers_cited.data:
            print(f"  ✓ {paper.data['title']} ({paper.data['year']})")
    else:
        print("  (No outgoing citations found - edge direction may vary)")
    
    # Find papers that CITE this paper (follow-up work)
    print("\n📑 Papers that CITES 'Attention Is All You Need':")
    citing_papers = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "out"},
                "title": attention_paper.data['title']
            }
        },
        "limit": 10
    })
    
    if citing_papers.data:
        for paper in citing_papers.data:
            print(f"  ✓ {paper.data['title']} ({paper.data['year']})")
    else:
        print("  (No citing papers found)")
    
    print("""
    💡 KEY INSIGHT: Graph traversal lets you navigate the academic 
       citation network. You can trace influence chains, find 
       foundational work, or discover related research.
    """)


# =============================================================================
# SCENARIO 2: Semantic Search (Vector Similarity)
# =============================================================================

def demonstrate_semantic_search():
    """
    Use vector similarity to find conceptually related papers.
    
    Even if papers don't share citations, semantic similarity can
    surface conceptually related work.
    """
    print_header("SCENARIO 2: Semantic Search (Vector Similarity)")
    print("""
Finding papers conceptually related to a research interest.
No shared citations needed - semantic vectors capture meaning.
""")
    
    # Search for papers related to "reinforcement learning from human feedback"
    research_interest = "reinforcement learning from human feedback alignment"
    print(f"Research interest: '{research_interest}'")
    print("\n🔍 Searching for semantically similar papers...\n")
    
    results = db.ai.search({
        "propertyName": "abstract",
        "query": research_interest,
        "labels": ["PAPER"],
        "limit": 5
    })
    
    for paper in results.data:
        print_paper(paper, show_score=True)
    
    # Also show a different search angle
    research_interest2 = "image generation diffusion models"
    print(f"\n🔍 Another search: '{research_interest2}'\n")
    
    results2 = db.ai.search({
        "propertyName": "abstract",
        "query": research_interest2,
        "labels": ["PAPER"],
        "limit": 5
    })
    
    for paper in results2.data:
        print_paper(paper, show_score=True)
    
    print("""
    💡 KEY INSIGHT: Vector similarity finds conceptually related papers
       even when they don't share explicit citations. This surfaces
       research from different communities working on similar problems.
    """)


# =============================================================================
# SCENARIO 3: Combined Discovery (Graph + Vector)
# =============================================================================

def demonstrate_combined_discovery():
    """
    Combine graph and vector search for intelligent discovery.
    
    Strategy: First filter via graph (recent RL papers), then
    rerank by semantic similarity to researcher's interests.
    """
    print_header("SCENARIO 3: Combined Discovery (Graph + Vector)")
    print("""
Hybrid approach: Filter via graph, rerank via vectors.

Strategy: Find recent papers in a domain, then reorder by
how well they match the researcher's specific interest.
""")
    
    # Step 1: Graph query - find recent papers in NLP/LM domain
    print("Step 1: Graph query - Find recent NLP papers (2018+)\n")
    recent_nlp = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "domain": {"$in": ["NLP", "Deep Learning"]},
            "year": {"$gte": 2018}
        },
        "limit": 20,
        "orderBy": {"year": "desc"}
    })
    
    print(f"Found {len(recent_nlp.data)} recent NLP/Deep Learning papers")
    
    # Step 2: Semantic search - find papers matching research interest
    # We use a specific interest and get semantic scores for all candidates
    print("\nStep 2: Semantic search - Find papers matching 'language model alignment'\n")
    
    # Get semantic results (this searches across ALL papers)
    semantic_results = db.ai.search({
        "propertyName": "abstract",
        "query": "language model alignment rlhf instruction following",
        "labels": ["PAPER"],
        "limit": 20
    })
    
    # Build a map of title -> semantic score
    semantic_scores = {p.data['title']: p.score for p in semantic_results.data}
    
    # Step 3: Combine - show recent papers that also have high semantic relevance
    print("Recent NLP papers (2018+) ranked by semantic relevance to alignment:\n")
    
    # Sort recent papers by their semantic scores
    scored_papers = []
    for paper in recent_nlp.data:
        title = paper.data['title']
        score = semantic_scores.get(title, 0)
        scored_papers.append((paper, score))
    
    # Sort by semantic score (descending)
    scored_papers.sort(key=lambda x: x[1], reverse=True)
    
    for paper, score in scored_papers[:8]:
        print_paper(paper, show_score=True)
    
    print("""
    💡 KEY INSIGHT: This is where RushDB shines. You get graph traversal
       AND vector search in a single system. No need to:
       - Query Neo4j for the graph part
       - Query Pinecone for the vector part
       - Stitch results together in application code
       
       One query, one latency hit, native consistency.
    """)


# =============================================================================
# SCENARIO 4: "More Like This" Endpoint
# =============================================================================

def demonstrate_more_like_this():
    """
    Build a "more like this" endpoint that returns:
    1. Papers in the citation network (directly related through citations)
    2. Semantically similar papers (conceptually related)
    
    This provides a comprehensive view of related work.
    """
    print_header("SCENARIO 4: 'More Like This' Endpoint")
    print("""
Unified endpoint returning both:
- Citation network neighbors (explicit relationships)
- Semantically similar papers (implicit relationships)

This gives researchers a comprehensive view of related work.
""")
    
    # Find a starting paper - let's use CLIP since it bridges vision and language
    start_results = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "title": {"$contains": "CLIP"}
        },
        "limit": 1
    })
    
    if not start_results.data:
        print("  ❌ CLIP paper not found. Run seed.py first.")
        return
    
    start_paper = start_results.data[0]
    print(f"Finding papers similar to: '{start_paper.data['title']}'\n")
    
    # Part 1: Citation network
    print("=" * 50)
    print("PART 1: Citation Network (Direct Relationships)")
    print("=" * 50)
    
    # Papers that cite CLIP
    citing = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "out"},
                "title": start_paper.data['title']
            }
        },
        "limit": 10
    })
    
    # Papers cited by CLIP
    cited = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "in"},
                "title": start_paper.data['title']
            }
        },
        "limit": 10
    })
    
    print("\n📑 Papers that CITE 'CLIP':")
    if citing.data:
        for p in citing.data:
            print(f"  → {p.data['title']} ({p.data['year']})")
    else:
        print("  (None found)")
    
    print("\n📚 Papers CITED BY 'CLIP' (references):")
    if cited.data:
        for p in cited.data:
            print(f"  ← {p.data['title']} ({p.data['year']})")
    else:
        print("  (None found)")
    
    # Part 2: Semantic similarity
    print("\n" + "=" * 50)
    print("PART 2: Semantic Similarity (Implicit Relationships)")
    print("=" * 50)
    
    # Use the CLIP paper's abstract as the query
    query_text = start_paper.data['abstract']
    
    semantic_results = db.ai.search({
        "propertyName": "abstract",
        "query": query_text,
        "labels": ["PAPER"],
        "where": {
            "title": {"$ne": start_paper.data['title']}  # Exclude the query paper itself
        },
        "limit": 8
    })
    
    print("\n🔍 Conceptually similar papers (by semantic vector):")
    for paper in semantic_results.data:
        print(f"  ✓ {paper.data['title']}")
        print(f"    Score: {paper.score:.4f} | {paper.data['venue']} ({paper.data['year']})")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY: 'More Like This' Results")
    print("=" * 50)
    print(f"""
    For '{start_paper.data['title']}':
    
    📊 Citation Network: 
       - {len(citing.data)} papers cite this work
       - {len(cited.data)} papers are cited as references
    
    📊 Semantic Similarity:
       - {len(semantic_results.data)} conceptually related papers found
    
    💡 The citation network shows DIRECT academic relationships.
       Semantic similarity shows CONCEPTUAL relationships that may
       span different research communities.
    """)


# =============================================================================
# BONUS: Show the simplicity of RushDB's architecture
# =============================================================================

def demonstrate_architecture_benefits():
    """Highlight why RushDB's unified approach is beneficial."""
    print_header("ARCHITECTURE BENEFITS: Why RushDB?")
    print("""
Compare: Traditional Stack vs RushDB

TRADITIONAL STACK (requires orchestration):
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Graph DB   │────▶│   App Code  │────▶│   Vector DB     │
│  (Neo4j)    │     │  (stitching)│     │ (Pinecone/etc)  │
└─────────────┘     └─────────────┘     └─────────────────┘
     │                     │                     │
     │   latency hit       │  latency hit        │
     └─────────────────────┴─────────────────────┘
                         │
                   Consistency?
                   Data sync?
                   Extra infra?
                   Higher cost?

RUSHDB (native capabilities):
┌─────────────────────────────────┐
│           RushDB                │
│  ┌─────────────────────────┐   │
│  │  Graph: Citations        │   │
│  │  Vector: Abstracts       │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
           │
     Single query
     Single latency hit
     Native consistency
     Lower cost

KEY BENEFITS:
✅ No orchestration overhead
✅ No consistency issues between databases
✅ Single SDK, single API
✅ Lower operational complexity
✅ Cost-effective (pay for writes, reads are free)
""")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("\n" + "#" * 70)
    print("#" + " " * 68 + "#")
    print("#   RESEARCH PAPER DISCOVERY ENGINE WITH RUSHDB                      #")
    print("#   Demonstrating Graph + Vector Capabilities                        #")
    print("#" + " " * 68 + "#")
    print("#" * 70)
    
    # Run all scenarios
    demonstrate_citation_network()
    demonstrate_semantic_search()
    demonstrate_combined_discovery()
    demonstrate_more_like_this()
    demonstrate_architecture_benefits()
    
    print_header("DEMO COMPLETE")
    print("""
This demo showed RushDB's combined graph and vector capabilities:

1. ✅ Citation Network Discovery
   - Navigate citation relationships
   - Find influence chains and related work

2. ✅ Semantic Search
   - Vector similarity on paper abstracts
   - Find conceptually related papers

3. ✅ Combined Discovery
   - Filter via graph, rerank via vectors
   - Leverage both capabilities together

4. ✅ "More Like This" Endpoint
   - Return both citation and semantic results
   - Comprehensive related work discovery

📚 Learn more:
   - Docs: https://docs.rushdb.com
   - GitHub: https://github.com/rush-db/examples
   - Pricing: https://rushdb.com/pricing
""")


if __name__ == "__main__":
    main()
