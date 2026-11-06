"""
Graph-Backed Autonomous Research Assistant Tutorial

This tutorial demonstrates using RushDB as a memory layer for autonomous research.
It shows five key patterns:
1. Research entity modeling with typed records
2. Building citation and support graphs with relationships
3. Graph traversal for context building
4. Semantic search on research content
5. Transactions for atomic research workflows

Run: python main.py
"""
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rushdb import RushDB


def print_header(text: str):
    """Print a section header."""
    print(f"\n=== {text} ===\n")


def print_success(text: str):
    """Print a success message."""
    print(f"  \u2713 {text}")


def demo_entity_modeling(db: RushDB):
    """Demonstrate creating research entity records."""
    print_header("1. Research Entity Modeling")
    
    # Create a research paper
    paper = db.records.create(
        label="PAPER",
        data={
            "title": "Emerging Patterns in Neural Architecture Search",
            "abstract": "We survey recent advances in neural architecture search (NAS), focusing on reinforcement learning and evolutionary approaches.",
            "authors": ["Smith", "Jones"],
            "year": 2023,
            "citations": 450
        }
    )
    print_success(f"Created PAPER: {paper.data['title']}")
    
    # Create a research claim
    claim = db.records.create(
        label="CLAIM",
        data={
            "text": "RL-based NAS methods achieve state-of-the-art performance on benchmark tasks",
            "confidence": 0.87,
            "source": "Empirical analysis across 15 NAS benchmarks"
        }
    )
    print_success(f"Created CLAIM: {claim.data['text'][:50]}...")
    
    # Create a research hypothesis
    hypothesis = db.records.create(
        label="HYPOTHESIS",
        data={
            "statement": "Evolutionary NAS will outperform RL-based NAS on tasks requiring diverse model architectures",
            "status": "testable"
        }
    )
    print_success(f"Created HYPOTHESIS: {hypothesis.data['statement'][:50]}...")
    
    return {"paper": paper, "claim": claim, "hypothesis": hypothesis}


def demo_graph_building(db: RushDB, entities: dict):
    """Demonstrate creating graph relationships between research entities."""
    print_header("2. Building the Citation Graph")
    
    paper = entities["paper"]
    claim = entities["claim"]
    hypothesis = entities["hypothesis"]
    
    # Find an existing paper to cite
    existing_papers = db.records.find({"labels": ["PAPER"], "limit": 5, "orderBy": {"citations": "desc"}})
    if existing_papers.data:
        referenced_paper = existing_papers.data[0]
        db.records.attach(
            source=paper,
            target=referenced_paper,
            options={"type": "CITES"}
        )
        print_success(f"Paper '{paper.data['title']}' cites '{referenced_paper.data['title']}'")
    
    # Link claim to supporting evidence
    evidence = db.records.create(
        label="EVIDENCE",
        data={
            "type": "benchmark_result",
            "dataset": "NAS-Bench-201",
            "accuracy": 0.923,
            "method": "Reinforcement Learning Controller"
        }
    )
    db.records.attach(
        source=claim,
        target=evidence,
        options={"type": "SUPPORTED_BY"}
    )
    print_success(f"Claim SUPPORTED_BY Evidence: {evidence.data['type']}")
    
    # Link claim to hypothesis
    db.records.attach(
        source=claim,
        target=hypothesis,
        options={"type": "SUPPORTS"}
    )
    print_success(f"Claim SUPPORTS Hypothesis")
    
    # Create a contradicting claim
    contradicting_claim = db.records.create(
        label="CLAIM",
        data={
            "text": "Evolutionary algorithms provide better architectural diversity",
            "confidence": 0.82
        }
    )
    db.records.attach(
        source=contradicting_claim,
        target=claim,
        options={"type": "CONTRADICTS"}
    )
    print_success(f"Created CONTRADICTS relationship between claims")
    
    return {"evidence": evidence, "contradicting_claim": contradicting_claim}


def demo_graph_traversal(db: RushDB, entities: dict, new_entities: dict):
    """Demonstrate traversing the research graph to build context."""
    print_header("3. Graph Traversal for Context Building")
    
    hypothesis = entities["hypothesis"]
    
    # Pattern 1: Find claims that support a specific hypothesis
    print("\n  [Traverse 1] Finding claims supporting the hypothesis...")
    supporting_claims = db.records.find({
        "labels": ["CLAIM"],
        "where": {
            "HYPOTHESIS": {
                "$relation": {"type": "SUPPORTS", "direction": "in"},
                "$id": hypothesis.id
            }
        }
    })
    print_success(f"Found {len(supporting_claims.data)} claims supporting the hypothesis")
    for claim in supporting_claims.data[:2]:
        print(f"    - {claim.data.get('text', '')[:60]}...")
    
    # Pattern 2: Find evidence supporting the claims
    print("\n  [Traverse 2] Finding evidence for claims...")
    evidence_list = db.records.find({
        "labels": ["EVIDENCE"],
        "where": {
            "CLAIM": {"$relation": {"type": "SUPPORTED_BY", "direction": "in"}}
        },
        "limit": 5
    })
    print_success(f"Found {len(evidence_list.data)} evidence items")
    
    # Pattern 3: Find related papers via citation chains
    print("\n  [Traverse 3] Finding papers citing the same sources...")
    recent_papers = db.records.find({"labels": ["PAPER"], "where": {"year": {"$gte": 2015}}, "limit": 3})
    if recent_papers.data:
        # Find papers that cite similar sources (bibliographic coupling)
        sample_paper = recent_papers.data[0]
        cited_sources = db.records.find({
            "labels": ["PAPER"],
            "where": {
                "PAPER": {
                    "$relation": {"type": "CITES", "direction": "in"},
                    "$id": sample_paper.id
                }
            }
        })
        print_success(f"Found {len(cited_sources.data)} papers citing similar sources")
    
    # Pattern 4: Build a context tree for LLM prompts
    print("\n  [Traverse 4] Building context tree for research query...")
    
    def build_context_tree(record, depth=0, visited=None):
        """"Recursively build context from graph traversal."""
        if visited is None:
            visited = set()
        
        if record.id in visited or depth > 3:
            return []
        visited.add(record.id)
        
        context = [{
            "label": record.label,
            "depth": depth,
            "data": record.fields
        }]
        
        # Find related records (outgoing relationships)
        related = db.records.find({
            "labels": [record.label],
            "where": {
                record.label: {
                    "$relation": {"direction": "out"}
                }
            },
            "limit": 3
        })
        
        for rel in related.data[:2]:
            context.extend(build_context_tree(rel, depth + 1, visited))
        
        return context
    
    context_tree = build_context_tree(hypothesis)
    print_success(f"Built context tree with {len(context_tree)} nodes")
    
    return {"context_tree": context_tree}



def demo_semantic_search(db: RushDB, entities: dict):
    """Demonstrate semantic search on research content."""
    print_header("4. Semantic Search on Research")
    
    # Check if vector index exists, create if not
    indexes = db.ai.indexes.find()
    abstract_index = None
    
    for idx in indexes.data:
        if idx.get("label") == "PAPER" and idx.get("propertyName") == "abstract":
            abstract_index = idx
            break
    
    if not abstract_index:
        print("  Creating vector index for PAPER.abstract...")
        abstract_index = db.ai.indexes.create({
            "label": "PAPER",
            "propertyName": "abstract",
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine"
        })
        print_success(f"Created index: {abstract_index.data.get('__id')}")
        
        # Note: In production, you would compute and upsert vectors here
        # using sentence-transformers or OpenAI embeddings
        print("  (Vector upsert would happen here with pre-computed embeddings)")
    else:
        print_success(f"Using existing index for PAPER.abstract")
    
    # Semantic search
    print("\n  Performing semantic search...")
    results = db.ai.search({
        "propertyName": "abstract",
        "query": "architecture search optimization methods",
        "labels": ["PAPER"],
        "limit": 3
    })
    
    print_success(f"Semantic search returned {len(results.data)} results")
    for i, result in enumerate(results.data[:3]):
        score = result.score if hasattr(result, 'score') else result.data.get('__score', 0)
        title = result.data.get('title', 'Unknown')
        print(f"    [{i+1}] Score: {score:.3f} - {title}")
    
    # Filtered semantic search
    print("\n  Performing filtered semantic search...")
    filtered_results = db.ai.search({
        "propertyName": "abstract",
        "query": "neural network training optimization",
        "labels": ["PAPER"],
        "where": {"year": {"$gte": 2015}},
        "limit": 2
    })
    print_success(f"Filtered search returned {len(filtered_results.data)} recent papers")
    
    return {"index": abstract_index, "results": results}


def demo_transactions(db: RushDB, entities: dict):
    """Demonstrate using transactions for atomic research operations."""
    print_header("5. Transactions for Research Workflows")
    
    # Create a new research finding with atomic operations
    with db.transactions.begin() as tx:
        # Create the main finding
        finding = db.records.create(
            label="FINDING",
            data={
                "text": "RL-based NAS achieves 2.3% higher accuracy than evolutionary methods on NLP tasks",
                "metric": "accuracy_improvement",
                "value": 2.3,
                "confidence": 0.91,
                "status": "preliminary"
            },
            transaction=tx
        )
        print_success(f"Created FINDING: {finding.data['text'][:50]}...")
        
        # Create supporting evidence
        evidence_1 = db.records.create(
            label="EVIDENCE",
            data={
                "type": "quantitative",
                "dataset": "GLUE Benchmark",
                "baseline_accuracy": 0.842,
                "rl_nas_accuracy": 0.865,
                "improvement": 2.3
            },
            transaction=tx
        )
        print_success(f"Created EVIDENCE: GLUE benchmark results")
        
        # Create additional evidence
        evidence_2 = db.records.create(
            label="EVIDENCE",
            data={
                "type": "quantitative",
                "dataset": "SST-2",
                "baseline_accuracy": 0.912,
                "rl_nas_accuracy": 0.928,
                "improvement": 1.6
            },
            transaction=tx
        )
        print_success(f"Created EVIDENCE: SST-2 benchmark results")
        
        # Link evidence to finding
        db.records.attach(
            source=finding,
            target=evidence_1,
            options={"type": "EXTRACTED_FROM"}
        )
        db.records.attach(
            source=finding,
            target=evidence_2,
            options={"type": "EXTRACTED_FROM"}
        )
        print_success("Linked evidence to finding")
        
        # Link finding to hypothesis
        hypothesis = entities["hypothesis"]
        db.records.attach(
            source=finding,
            target=hypothesis,
            options={"type": "SUPPORTS"}
        )
        print_success("Linked finding to hypothesis")
    
    # Verify the transaction was successful
    verification = db.records.find_by_id(finding.id)
    if verification.exists:
        print_success("Transaction verified: all entities created with relationships")
        
        # Verify relationships
        related_evidence = db.records.find({
            "labels": ["EVIDENCE"],
            "where": {
                "FINDING": {
                    "$relation": {"type": "EXTRACTED_FROM", "direction": "in"},
                    "$id": finding.id
                }
            }
        })
        print_success(f"Verified {len(related_evidence.data)} evidence relationships")
    
    # Demonstrate rollback scenario
    print("\n  Demonstrating transaction rollback...")
    try:
        with db.transactions.begin() as tx:
            # Create a record that we'll use to test rollback
            test_record = db.records.create(
                label="TEST",
                data={"description": "This should be rolled back"},
                transaction=tx
            )
            # Simulate an error condition
            raise ValueError("Simulated research workflow error")
    except ValueError as e:
        print_success(f"Transaction rolled back due to: {e}")
        
        # Verify test record was not created
        test_result = db.records.find({"labels": ["TEST"], "where": {"description": "This should be rolled back"}})
        if not test_result.data:
            print_success("Rollback verified: test record not created")
        else:
            print("  WARNING: Record may have been created despite error")
    
    return {"finding": finding}


def demo_context_builder(db: RushDB):
    """Demonstrate building rich context for LLM prompts."""
    print_header("6. Context Builder for LLM Prompts")
    
    # Get a research query
    queries = db.records.find({"labels": ["QUERY"], "limit": 1})
    if queries.data:
        query = queries.data[0]
        print(f"  Research query: {query.data.get('text', 'N/A')}")
        
        # Build context by traversing the graph
        # 1. Find relevant papers via semantic search
        search_results = db.ai.search({
            "propertyName": "abstract",
            "query": query.data.get('text', ''),
            "labels": ["PAPER"],
            "limit": 3
        })
        
        context = {
            "query": query.data,
            "relevant_papers": [],
            "supporting_claims": [],
            "related_evidence": []
        }
        
        for paper in search_results.data:
            paper_context = {
                "title": paper.data.get('title', ''),
                "authors": paper.data.get('authors', []),
                "year": paper.data.get('year', 0),
                "abstract": paper.data.get('abstract', '')[:200] + "..."
            }
            
            # Find claims supported by this paper
            claims = db.records.find({
                "labels": ["CLAIM"],
                "where": {
                    "PAPER": {
                        "$relation": {"type": "SUPPORTED_BY", "direction": "in"},
                        "$id": paper.id
                    }
                }
            })
            paper_context["claims"] = [c.data.get('text', '') for c in claims.data]
            
            context["relevant_papers"].append(paper_context)
        
        # Find supporting evidence
        evidence = db.records.find({"labels": ["EVIDENCE"], "limit": 5})
        context["related_evidence"] = [
            {"type": e.data.get('type', ''), "dataset": e.data.get('dataset', 'N/A')}
            for e in evidence.data
        ]
        
        print_success(f"Built context with {len(context['relevant_papers'])} papers")
        print(f"  Context preview: {len(str(context))} characters")
        
        return context
    else:
        print("  No queries found, skipping context builder demo")
        return None


def main():
    """Main entry point for the tutorial."""
    print("\n" + "=" * 60)
    print("Graph-Backed Autonomous Research Assistant Tutorial")
    print("=" * 60)
    
    # Verify API token
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("\nERROR: RUSHDB_API_TOKEN not found in environment")
        print("Please copy .env.example to .env and add your API key")
        print("Get your API key at: https://app.rushdb.com")
        sys.exit(1)
    
    # Initialize RushDB client
    db = RushDB(api_token)
    print(f"\nConnected to RushDB")
    
    # Run demos
    try:
        # 1. Entity modeling
        entities = demo_entity_modeling(db)
        
        # 2. Graph building
        new_entities = demo_graph_building(db, entities)
        
        # 3. Graph traversal
        traversal = demo_graph_traversal(db, entities, new_entities)
        
        # 4. Semantic search
        semantic = demo_semantic_search(db, entities)
        
        # 5. Transactions
        transaction = demo_transactions(db, entities)
        
        # 6. Context builder
        context = demo_context_builder(db)
        
        print("\n" + "=" * 60)
        print("Tutorial Complete!")
        print("=" * 60)
        print("\nAll RushDB operations shown above use the Python SDK.")
        print("See the README for the full tutorial walkthrough.")
        print(f"\nGitHub: https://github.com/rush-db/examples/tree/main/building-a-graph-backed-autonomous-research-assist-tutorial")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Make sure you've run 'python seed.py' first to populate the database.")
        sys.exit(1)


if __name__ == "__main__":
    main()
