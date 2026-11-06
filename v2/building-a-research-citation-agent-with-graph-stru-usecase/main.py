#!/usr/bin/env python3
"""
Research Citation Agent Demo

Demonstrates RushDB's dual-layer architecture for research paper discovery:
1. Graph traversal for citation relationships
2. Vector similarity for semantic discovery
3. Combined graph + vector queries

Run 'python seed.py' first to load the data.
"""

import os
from collections import defaultdict

from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
token = os.getenv("RUSHDB_TOKEN")
or url = os.getenv("RUSHDB_URL")

if not token:
    raise ValueError(
        "RUSHDB_TOKEN not found. Please create a .env file with your token.\n"
        "Get your token at: https://app.rushdb.com/settings/api-tokens"
    )

db = RushDB(token, url=url) if url else RushDB(token)


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f" {title}")
    print(f"{'=' * 70}\n")


def print_result(label, value=None):
    """Print a result with optional value."""
    if value is not None:
        print(f"  {label}: {value}")
    else:
        print(f"  {label}")


# ============================================================================
# SECTION 1: Basic Graph Traversal - Find Cited and Citing Papers
# ============================================================================

def demo_citation_relationships():
    """Demonstrate basic citation graph traversal."""
    print_header("1. CITATION RELATIONSHIPS (Graph Traversal)")

    # Find the "Attention Is All You Need" paper
    attention = db.records.find({
        "labels": ["PAPER"],
        "where": {"title": {"$contains": "Attention Is All You Need"}},
        "limit": 1
    }).data

    if not attention:
        print("Paper 'Attention Is All You Need' not found. Run seed.py first.")
        return

    attention = attention[0]
    print(f"Starting paper: {attention['title']}")
    print(f"  Authors: {', '.join(attention['authors'])}")
    print(f"  Year: {attention['year']}")

    # Find papers that THIS paper cites (outgoing CITES edges)
    papers_cited = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "in"},
                "paperId": attention['paperId']
            }
        }
    })

    print(f"\nPapers cited by '{attention['title']}':")
    if papers_cited.data:
        for paper in papers_cited.data:
            print_result(paper['title'], f"({paper['year']})")
    else:
        print_result("(none)")

    # Find papers that cite THIS paper (incoming CITES edges)
    papers_that_cite = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "out"},
                "paperId": attention['paperId']
            }
        }
    })

    print(f"\nPapers that cite '{attention['title']}':")
    if papers_that_cite.data:
        for paper in papers_that_cite.data:
            print_result(paper['title'], f"({paper['year']})")
    else:
        print_result("(none)")


# ============================================================================
# SECTION 2: Semantic Search - Find Similar Papers by Abstract
# ============================================================================

def demo_semantic_search():
    """Demonstrate vector similarity search on paper abstracts."""
    print_header("2. SEMANTIC SEARCH (Vector Similarity)")

    queries = [
        "attention mechanisms in transformer neural networks",
        "generative models and adversarial training",
        "unsupervised learning with contrastive methods"
    ]

    for query in queries:
        print(f"Query: \"{query}\"")
        print("-" * 60)

        results = db.ai.search({
            "propertyName": "abstract",
            "query": query,
            "labels": ["PAPER"],
            "limit": 3
        })

        for paper in results.data:
            print_result(
                f"[{paper.score:.3f}]",
                f"{paper['title']} ({paper['year']})"
            )

        print()


# ============================================================================
# SECTION 3: Graph Traversal with Multiple Hops
# ============================================================================

def demo_multi_hop_traversal():
    """Demonstrate traversing citation chains multiple hops away."""
    print_header("3. CITATION CHAIN TRAVERSAL (Multi-hop Graph)")

    # Start from "Attention Is All You Need"
    start_paper = db.records.find({
        "labels": ["PAPER"],
        "where": {"paperId": "paper_001"},
        "limit": 1
    }).data[0]

    def find_papers_cited_by(paper_id):
        """Find papers directly cited by the given paper."""
        return db.records.find({
            "labels": ["PAPER"],
            "where": {
                "PAPER": {
                    "$relation": {"type": "CITES", "direction": "in"},
                    "paperId": paper_id
                }
            }
        }).data

    def find_papers_that_cite(paper_id):
        """Find papers that directly cite the given paper."""
        return db.records.find({
            "labels": ["PAPER"],
            "where": {
                "PAPER": {
                    "$relation": {"type": "CITES", "direction": "out"},
                    "paperId": paper_id
                }
            }
        }).data

    # Collect papers at each hop
    visited = {start_paper['paperId']}
    current_hop = [start_paper]

    for hop in [1, 2]:
        print(f"\n--- Papers {hop} hop(s) away from '{start_paper['title']}' ---")

        next_hop = []
        for paper in current_hop:
            # Papers this paper cites
            cited = find_papers_cited_by(paper['paperId'])
            for p in cited:
                if p['paperId'] not in visited:
                    print_result(p['title'], f"cited by {paper['title']}")
                    next_hop.append(p)
                    visited.add(p['paperId'])

            # Papers that cite this paper
            citing = find_papers_that_cite(paper['paperId'])
            for p in citing:
                if p['paperId'] not in visited:
                    print_result(p['title'], f"citing {paper['title']}")
                    next_hop.append(p)
                    visited.add(p['paperId'])

        if not next_hop:
            print_result("(no new papers found)")

        current_hop = next_hop


# ============================================================================
# SECTION 4: Hybrid Search - Graph + Vector Combined
# ============================================================================

def demo_hybrid_search():
    """Demonstrate combining graph filtering with vector similarity."""
    print_header("4. HYBRID SEARCH (Graph Filter + Vector Similarity)")

    # Start with a semantically similar query
    query = "attention mechanisms and transformers"

    print(f"Query: \"{query}\"")
    print("\nFinding papers similar to this query, then filtering by citation relationship to BERT...")

    # First, find BERT
    bert = db.records.find({
        "labels": ["PAPER"],
        "where": {"paperId": "paper_002"},
        "limit": 1
    }).data[0]

    # Search for semantically similar papers
    similar = db.ai.search({
        "propertyName": "abstract",
        "query": query,
        "labels": ["PAPER"],
        "limit": 10
    }).data

    # Filter: which of these papers BERT cites?
    bert_cites = find_papers_cited_by_bert = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {
                "$relation": {"type": "CITES", "direction": "in"},
                "paperId": bert['paperId']
            }
        }
    }).data
    bert_cites_ids = {p['paperId'] for p in bert_cites}

    print(f"\nResults for '{query}' that are cited by BERT:")
    found = False
    for paper in similar:
        if paper['paperId'] in bert_cites_ids:
            print_result(
                f"[{paper.score:.3f}]",
                f"{paper['title']}"
            )
            found = True

    if not found:
        print_result("(none)")

    # Also show: papers cited by BERT sorted by semantic similarity to our query
    print(f"\nAll papers cited by BERT, ranked by similarity to '{query}':")
    bert_cites_sorted = sorted(
        [(p['paperId'], p['title']) for p in bert_cites],
        key=lambda x: next(
            (s for s in similar if s['paperId'] == x[0]),
            type('obj', (object,), {'score': 0})()
        ).score,
        reverse=True
    )

    for paper_id, title in bert_cites_sorted:
        sim_score = next((s.score for s in similar if s['paperId'] == paper_id), 0)
        print_result(f"[{sim_score:.3f}]", title)


# ============================================================================
# SECTION 5: Co-Citation Analysis
# ============================================================================

def demo_cocitation_analysis():
    """Demonstrate co-citation analysis to discover paper clusters."""
    print_header("5. CO-CITATION ANALYSIS (Paper Clusters)")

    # Get all papers
    all_papers = db.records.find({"labels": ["PAPER"]}).data
    print(f"Analyzing {len(all_papers)} papers for co-citation patterns...\n")

    # Build citation map: paper_id -> set of papers it cites
    def find_papers_cited_by(paper_id):
        return db.records.find({
            "labels": ["PAPER"],
            "where": {
                "PAPER": {
                    "$relation": {"type": "CITES", "direction": "in"},
                    "paperId": paper_id
                }
            }
        }).data

    # Count how often each pair of papers is cited together
    cocitation_counts = defaultdict(int)
    papers_citing_map = {}  # paper_id -> list of papers that cite it

    for paper in all_papers:
        paper_id = paper['paperId']
        citing = find_papers_cited_by(paper_id)
        if citing:
            papers_citing_map[paper_id] = [p['paperId'] for p in citing]

    # Find pairs cited together
    for cited_id, citing_ids in papers_citing_map.items():
        for i, citing_a in enumerate(citing_ids):
            for citing_b in citing_ids[i+1:]:
                pair = tuple(sorted([citing_a, citing_b]))
                cocitation_counts[pair] += 1

    # Get papers that frequently appear together
    print("Papers frequently cited together (co-citation clusters):")
    print("-" * 60)

    # Find high co-citation pairs
    strong_pairs = [(pair, count) for pair, count in cocitation_counts.items() if count >= 1]
    strong_pairs.sort(key=lambda x: x[1], reverse=True)

    paper_titles = {p['paperId']: p['title'] for p in all_papers}

    clusters = defaultdict(set)
    for (a, b), count in strong_pairs[:10]:
        print_result(
            f"Co-cited {count} time(s):",
            f"{paper_titles.get(a, a)} <-> {paper_titles.get(b, b)}"
        )
        clusters[a].add(b)
        clusters[b].add(a)

    # Identify cluster topics by checking semantic similarity
    print("\n--- Detected Clusters ---")
    connected = set()
    cluster_id = 0

    for paper_id in paper_titles:
        if paper_id not in connected:
            cluster_id += 1
            cluster = set()
            queue = [paper_id]

            while queue:
                current = queue.pop()
                if current not in cluster:
                    cluster.add(current)
                    connected.add(current)
                    if current in clusters:
                        queue.extend(clusters[current] - cluster)

            if len(cluster) > 1:
                cluster_papers = [(pid, paper_titles[pid]) for pid in cluster]
                print(f"\nCluster {cluster_id} ({len(cluster)} papers):")
                for pid, title in sorted(cluster_papers, key=lambda x: x[1]):
                    print_result(title)


# ============================================================================
# SECTION 6: Finding Papers by Author Through Graph Traversal
# ============================================================================

def demo_author_citation_network():
    """Demonstrate finding papers by authors and their citation network."""
    print_header("6. AUTHOR CITATION NETWORK")

    # Find all papers by Vaswani (first author of Attention)
    vaswani_papers = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "authors": {"$contains": "Vaswani"}
        }
    }).data

    print("Papers by Vaswani:")
    for paper in vaswani_papers:
        print_result(paper['title'], f"({paper['year']})")

    if vaswani_papers:
        # Find what other authors Vaswani's papers cite (collaborator discovery)
        paper_ids = [p['paperId'] for p in vaswani_papers]

        # Collect all cited papers
        all_cited = set()
        for pid in paper_ids:
            cited = db.records.find({
                "labels": ["PAPER"],
                "where": {
                    "PAPER": {
                        "$relation": {"type": "CITES", "direction": "in"},
                        "paperId": pid
                    }
                }
            }).data
            all_cited.update(p['paperId'] for p in cited)

        print(f"\nPapers cited by Vaswani's work: {len(all_cited)}")
        print_result("(showing first 5)")

        for pid in list(all_cited)[:5]:
            paper = db.records.find({
                "labels": ["PAPER"],
                "where": {"paperId": pid},
                "limit": 1
            }).data[0]
            print_result(paper['title'])


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" RESEARCH CITATION AGENT WITH GRAPH + VECTOR SEARCH")
    print(" RushDB Demo - rushdb.com")
    print("=" * 70)

    # Check if data exists
    count = db.records.find({"labels": ["PAPER"], "limit": 1})
    if not count.data:
        print("\nNo PAPER records found!")
        print("Please run 'python seed.py' first to load the research papers.")
        return

    print(f"\nConnected to RushDB. Found {count.total} paper records.")

    # Run all demos
    demo_citation_relationships()
    demo_semantic_search()
    demo_multi_hop_traversal()
    demo_hybrid_search()
    demo_cocitation_analysis()
    demo_author_citation_network()

    print("\n" + "=" * 70)
    print(" DEMO COMPLETE")
    print("=" * 70)
    print("\nExplore more:")
    print("  - Try different semantic search queries")
    print("  - Experiment with graph traversal depth")
    print("  - Build recommendation systems using co-citation")
    print("\nDocumentation: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
