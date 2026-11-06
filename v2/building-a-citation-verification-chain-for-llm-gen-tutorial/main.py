"""
Citation Verification Chain for LLM-Generated Content

This example demonstrates how to build a citation verification chain using RushDB.
The chain verifies that LLM-generated claims are properly supported by source documents
through semantic similarity search and citation graph traversal.
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Verify environment setup
api_key = os.environ.get("RUSHDB_API_KEY")
if not api_key:
    print("❌ Error: RUSHDB_API_KEY not found in environment")
    print("   Copy .env.example to .env and add your API key")
    sys.exit(1)


# Initialize clients
db = RushDB(api_key)
embedder = SentenceTransformer('all-MiniLM-L6-v2')


@dataclass
class VerificationResult:
    """Result of verifying a single claim against sources."""
    claim: dict
    status: str
    citations: list[dict]
    verification_score: float
    evidence_snippets: list[str]


def get_embedding(text: str) -> list[float]:
    """Generate embedding for text using sentence-transformers."""
    return embedder.encode(text, normalize_embeddings=True).tolist()



def load_source_documents() -> list:
    """Load all source documents from RushDB."""
    result = db.records.find({"labels": ["SOURCE"]})
    return result.data


def load_claims() -> list:
    """Load all claims from RushDB."""
    result = db.records.find({"labels": ["CLAIM"]})
    return result.data


def find_supporting_sources(claim_text: str, sources: list) -> list[dict]:
    """
    Use semantic search to find sources that may support a claim.
    Returns top matching sources with similarity scores.
    """
    claim_embedding = get_embedding(claim_text)
    
    matching_sources = []
    
    for source in sources:
        # Get source content embedding
        source_content = source.data.get('body', source.data.get('abstract', ''))
        if not source_content:
            continue
            
        source_embedding = get_embedding(source_content)
        
        # Calculate cosine similarity
        similarity = sum(a * b for a, b in zip(claim_embedding, source_embedding))
        
        if similarity > 0.3:  # Threshold for relevance
            matching_sources.append({
                'source': source,
                'similarity': float(similarity),
                'title': source.data.get('title', 'Unknown'),
                'content_preview': source_content[:200] + '...'
            })
    
    # Sort by similarity descending
    matching_sources.sort(key=lambda x: x['similarity'], reverse=True)
    return matching_sources[:5]


def get_cited_sources(claim_id: str) -> list:
    """
    Get all sources cited by a specific claim using relationship traversal.
    """
    result = db.records.find({
        "labels": ["SOURCE"],
        "where": {
            "CLAIM": {"$id": claim_id}
        }
    })
    return result.data


def calculate_verification_score(claim_text: str, cited_sources: list) -> float:
    """
    Calculate a verification score based on how well cited sources
    support the claim (0.0 to 1.0).
    """
    if not cited_sources:
        return 0.0
    
    claim_embedding = get_embedding(claim_text)
    total_similarity = 0.0
    
    for source in cited_sources:
        source_content = source.data.get('body', source.data.get('abstract', ''))
        if source_content:
            source_embedding = get_embedding(source_content)
            similarity = sum(a * b for a, b in zip(claim_embedding, source_embedding))
            total_similarity += similarity
    
    # Average similarity across cited sources
    avg_similarity = total_similarity / len(cited_sources)
    return min(1.0, max(0.0, avg_similarity))


def verify_claim(claim: dict, sources: list) -> VerificationResult:
    """
    Verify a single claim against the source document database.
    
    Steps:
    1. Find cited sources via relationships
    2. Search for additional supporting evidence
    3. Calculate verification score
    4. Determine verification status
    """
    claim_id = claim.id
    claim_text = claim.data.get('text', '')
    
    # Get explicitly cited sources
    cited_sources = get_cited_sources(claim_id)
    
    # If no explicit citations, search for supporting sources
    if not cited_sources:
        supporting = find_supporting_sources(claim_text, sources)
        cited_sources = [s['source'] for s in supporting]
    
    # Calculate verification score
    verification_score = calculate_verification_score(claim_text, cited_sources)
    
    # Determine status based on score
    if verification_score >= 0.8:
        status = "VERIFIED"
    elif verification_score >= 0.5:
        status = "PARTIALLY_SUPPORTED"
    else:
        status = "UNVERIFIED"
    
    # Build citation information
    citations = []
    for source in cited_sources:
        citations.append({
            'title': source.data.get('title', 'Unknown'),
            'authors': source.data.get('authors', []),
            'year': source.data.get('publication_year', 'N/A'),
            'abstract': source.data.get('abstract', '')[:100] + '...'
        })
    
    # Extract evidence snippets
    evidence_snippets = []
    for source in cited_sources:
        content = source.data.get('body', source.data.get('abstract', ''))
        evidence_snippets.append(content[:150] + '...')
    
    return VerificationResult(
        claim=claim.data,
        status=status,
        citations=citations,
        verification_score=verification_score,
        evidence_snippets=evidence_snippets
    )


def run_verification_chain() -> list[VerificationResult]:
    """
    Run the complete citation verification chain.
    
    1. Load all source documents and claims from RushDB
    2. Verify each claim against sources
    3. Return verification results
    """
    print("\n🔄 Running Citation Verification Chain...")
    
    # Load data from RushDB
    sources = load_source_documents()
    claims = load_claims()
    
    print(f"📚 Loaded {len(sources)} source documents")
    print(f"📝 Loaded {len(claims)} LLM-generated claims")
    
    # Verify each claim
    results = []
    for claim in claims:
        result = verify_claim(claim, sources)
        results.append(result)
        
        # Update claim status in RushDB
        db.records.update(
            record_id=claim.id,
            data={"verification_status": result.status}
        )
    
    return results


def print_results(results: list[VerificationResult]):
    """Print verification results in a formatted output."""
    print("\n" + "=" * 60)
    print("📋 VERIFICATION RESULTS")
    print("=" * 60)
    
    status_counts = {"VERIFIED": 0, "PARTIALLY_SUPPORTED": 0, "UNVERIFIED": 0}
    
    for i, result in enumerate(results, 1):
        print(f"\n{'─' * 60}")
        print(f"📌 Claim {i}: \"{result.claim.get('text', '')[:60]}...\"")
        print(f"   Generated by: {result.claim.get('generated_by', 'Unknown')}")
        print(f"   Context: {result.claim.get('context', 'N/A')}")
        
        print(f"\n   Status: ", end="")
        if result.status == "VERIFIED":
            print(f"✅ VERIFIED")
            status_counts["VERIFIED"] += 1
        elif result.status == "PARTIALLY_SUPPORTED":
            print(f"⚠️  PARTIALLY_SUPPORTED")
            status_counts["PARTIALLY_SUPPORTED"] += 1
        else:
            print(f"❌ UNVERIFIED")
            status_counts["UNVERIFIED"] += 1
        
        print(f"   Citations ({len(result.citations)}):")
        for citation in result.citations:
            print(f"     • \"{citation['title']}\"")
            print(f"       Authors: {', '.join(citation['authors'])}")
            print(f"       Year: {citation['year']}")
        
        print(f"\n   Verification Score: {result.verification_score:.2f}")
    
    # Summary
    print(f"\n{'═' * 60}")
    print("📊 SUMMARY")
    print(f"{'═' * 60}")
    print(f"Total Claims: {len(results)}")
    print(f"Verified: {status_counts['VERIFIED']}")
    print(f"Partially Supported: {status_counts['PARTIALLY_SUPPORTED']}")
    print(f"Unverified: {status_counts['UNVERIFIED']}")
    print(f"{'═' * 60}\n")


def demonstrate_citation_graph():
    """
    Demonstrate traversing the citation graph.
    Shows how claims are connected to their source documents.
    """
    print("\n🌐 Citation Graph Traversal Demo")
    print("-" * 40)
    
    # Find all claims
    claims = db.records.find({"labels": ["CLAIM"]})
    
    for claim in claims:
        claim_text = claim.data.get('text', '')[:50]
        print(f"\n📌 Claim: {claim_text}...")
        
        # Find connected sources
        cited_sources = db.records.find({
            "labels": ["SOURCE"],
            "where": {
                "CLAIM": {"$id": claim.id}
            }
        })
        
        for source in cited_sources:
            print(f"   → CITES → \"{source.data.get('title', '')}\"")
    
    print()

def main():
    """Main entry point for the citation verification chain."""
    print("=" * 60)
    print("🔍 CITATION VERIFICATION CHAIN FOR LLM-GENERATED CONTENT")
    print("=" * 60)
    
    # Check if data exists
    sources = load_source_documents()
    claims = load_claims()
    
    if not sources or not claims:
        print("⚠️  No data found in RushDB.")
        print("   Run 'python seed.py' first to seed the database with sample data.")
        sys.exit(1)
    
    # Run verification chain
    results = run_verification_chain()
    
    # Display results
    print_results(results)
    
    # Demonstrate graph traversal
    demonstrate_citation_graph()
    
    print("✅ Verification complete!")



if __name__ == "__main__":
    main()
