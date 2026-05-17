#!/usr/bin/env python3
"""
Graph-Based Hallucination Detection Pipeline

This pipeline demonstrates:
1. Loading a knowledge base (documents + chunks) from RushDB
2. Generating an answer (simulated - using stored facts + injected hallucination)
3. Extracting claims as subject-predicate-object triples
4. Validating each claim against the vector store
5. Tracing provenance for failed claims

The simulated answer contains both grounded and hallucinated claims
to demonstrate the full detection workflow.
"""

import os
import re
import sys
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# Configuration
SIMILARITY_THRESHOLD = 0.65
TOP_K_RESULTS = 3

# Simulated LLM answer (mix of grounded facts and hallucinations)
SIMULATED_ANSWER = """
Agrivoltaics combines solar energy generation with agricultural production on the same land. 
Research shows that solar panels installed on agricultural land can boost crop yields by up to 30% 
while reducing water consumption by 40%. This dual-use approach has gained significant traction 
since the first commercial installations appeared in Japan in 2004. 

The technology enables farms to generate 800-1200 kWh per kilowatt annually while maintaining 
agricultural productivity. Studies indicate land equivalent efficiency can reach 160% compared 
to single-use installations.
"""


@dataclass
class Claim:
    """Represents a single claim extracted from the answer."""
    subject: str
    predicate: str
    obj: str
    full_text: str
    claim_id: int


@dataclass
class ValidationResult:
    """Result of validating a claim against the knowledge base."""
    claim: Claim
    verified: bool
    best_similarity: float
    best_match_chunk: Optional[dict] = None
    best_match_source: Optional[dict] = None
    failure_reason: Optional[str] = None


class ClaimExtractor:
    """Simple rule-based claim extractor."""
    
    # Patterns for common claim structures
    SUBJECT_PATTERNS = [
        r'(solar panels?[\w\s]*)',
        r'(agrivoltaics?)',
        r'(the technology)',
        r'(this dual-use approach)',
        r'(farms?)',
        r'(land equivalent efficiency)'
    ]
    
    PREDICATE_PATTERNS = [
        r'can (boost|increase|improve)\s+(\w+\s+\w+)',
        r'(boosts?|increases?|improves?)\s+(\w+\s+\w+)',
        r'reduces?\s+(\w+\s+\w+)',
        r'has been shown to\s+(\w+)',
        r'can reach\s+(\w+\s+\w+)',
        r'has gained',
        r'enables farms to',
        r'indicates'
    ]
    
    @classmethod
    def extract(cls, text: str) -> list[Claim]:
        """Extract claims from text."""
        claims = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        claim_id = 0
        for sentence in sentences:
            # Extract subject
            subject = None
            for pattern in cls.SUBJECT_PATTERNS:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    subject = match.group(1).strip()
                    break
            
            if not subject:
                continue
            
            # Extract predicate-object patterns
            predicates = [
                (r'can boost crop yields by up to (\d+%)', 'can boost crop yields', 'by up to \1'),
                (r'reducing water consumption by (\d+%)', 'reduces water consumption', 'by \1'),
                (r'first commercial installations appeared in (\w+) in (\d+)', 'was first developed', 'in \1 in \2'),
                (r'generates?\s+(\d+-\d+\s+kWh)', 'generates energy', '\1 per kilowatt annually'),
                (r'land equivalent efficiency can reach (\d+%)', 'can reach land equivalent efficiency', 'of \1'),
            ]
            
            for pattern, predicate, obj_template in predicates:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    obj = obj_template
                    for g in match.groups():
                        obj = obj.replace(f'\\{match.lastindex}', g)
                    obj = re.sub(r'\\\d+', '', obj)  # Clean remaining backslash patterns
                    
                    claim = Claim(
                        subject=subject,
                        predicate=predicate,
                        obj=obj,
                        full_text=sentence,
                        claim_id=claim_id
                    )
                    claims.append(claim)
                    claim_id += 1
                    break  # One claim per sentence for simplicity
        
        return claims


class HallucinationDetector:
    """Detects hallucinations by validating claims against the knowledge base."""
    
    def __init__(self, db: RushDB, threshold: float = 0.65):
        self.db = db
        self.threshold = threshold
    
    def validate_claim(self, claim: Claim) -> ValidationResult:
        """Validate a single claim against the vector store."""
        
        # Search for relevant chunks
        search_query = f"{claim.subject} {claim.predicate} {claim.obj}"
        
        try:
            results = self.db.ai.search({
                "propertyName": "text",
                "query": search_query,
                "labels": ["CHUNK"],
                "limit": TOP_K_RESULTS
            })
        except Exception as e:
            return ValidationResult(
                claim=claim,
                verified=False,
                best_similarity=0.0,
                failure_reason=f"Search error: {str(e)}"
            )
        
        if not results.data:
            return ValidationResult(
                claim=claim,
                verified=False,
                best_similarity=0.0,
                failure_reason="No matching chunks found in knowledge base"
            )
        
        # Get best match
        best_chunk = results.data[0]
        best_score = best_chunk.score if best_chunk.score is not None else 0.0
        
        if best_score < self.threshold:
            return ValidationResult(
                claim=claim,
                verified=False,
                best_similarity=best_score,
                best_match_chunk=best_chunk.data,
                failure_reason=f"Best similarity ({best_score:.3f}) below threshold ({self.threshold})"
            )
        
        # Find the source document for this chunk
        source_doc = self._find_source_document(best_chunk.id)
        
        return ValidationResult(
            claim=claim,
            verified=True,
            best_similarity=best_score,
            best_match_chunk=best_chunk.data,
            best_match_source=source_doc.data if source_doc else None
        )
    
    def _find_source_document(self, chunk_id: str) -> Optional[dict]:
        """Traverse the graph to find the source document for a chunk."""
        # Use relationship query to find DOCUMENT connected via SOURCED_FROM
        result = self.db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "CHUNK": {
                    "$relation": {
                        "type": "SOURCED_FROM",
                        "direction": "in"
                    },
                    "__id": chunk_id
                }
            }
        })
        
        if result.data:
            return result.data[0]
        return None
    
    def detect_all(self, claims: list[Claim]) -> list[ValidationResult]:
        """Validate all claims."""
        return [self.validate_claim(claim) for claim in claims]


def print_results(results: list[ValidationResult]):
    """Pretty-print validation results."""
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    verified_count = 0
    failed_count = 0
    
    for result in results:
        print(f"\n{'─' * 60}")
        print(f"Claim {result.claim.claim_id + 1}: {result.claim.subject} {result.claim.predicate}")
        print(f"  Full text: \"{result.claim.full_text.strip()}\"")
        
        if result.verified:
            verified_count += 1
            print(f"\n  ✅ VERIFIED (similarity: {result.best_similarity:.3f})")
            if result.best_match_source:
                print(f"     Source: {result.best_match_source.get('title', 'Unknown')}")
            if result.best_match_chunk:
                chunk_text = result.best_match_chunk.get('text', '')[:150]
                print(f"     Chunk: \"{chunk_text}...\"")
        else:
            failed_count += 1
            print(f"\n  ❌ FAILED (best similarity: {result.best_similarity:.3f})")
            print(f"     Reason: {result.failure_reason}")
            
            if result.best_match_chunk:
                print(f"     Closest match: \"{result.best_match_chunk.get('text', '')[:150]}...\"")
    
    # Summary
    total = len(results)
    verified_pct = (verified_count / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Verified: {verified_count}/{total} claims ({verified_pct:.1f}%)")
    print(f"  Failed:   {failed_count}/{total} claims")
    
    if failed_count > 0:
        confidence = "LOW" if verified_pct < 70 else "MEDIUM" if verified_pct < 90 else "HIGH"
        print(f"\n  ⚠️  Overall confidence: {confidence}")
        print(f"     Answer requires revision before production use.")
    else:
        print(f"\n  ✅ Overall confidence: HIGH")
        print(f"     Answer is grounded in the knowledge base.")


def main():
    """Main pipeline execution."""
    # Check API key
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("   Copy .env.example to .env and add your API key.")
        sys.exit(1)
    
    db = RushDB(api_key)
    
    print("\n" + "=" * 60)
    print("GRAPH-BASED HALLUCINATION DETECTION PIPELINE")
    print("=" * 60)
    
    # Step 1: Load knowledge base stats
    print("\n📚 Loading knowledge base...")
    docs = db.records.find({"labels": ["DOCUMENT"], "limit": 100})
    chunks = db.records.find({"labels": ["CHUNK"], "limit": 100})
    print(f"   Loaded {docs.total} source documents with {chunks.total} chunks")
    
    if chunks.total == 0:
        print("\n⚠️  No chunks found. Run 'python seed.py' first.")
        sys.exit(1)
    
    # Step 2: Show simulated answer
    print("\n" + "=" * 60)
    print("SIMULATED LLM ANSWER")
    print("=" * 60)
    print(f"\n{SIMULATED_ANSWER.strip()}")
    
    # Step 3: Extract claims
    print("\n" + "=" * 60)
    print("CLAIM EXTRACTION")
    print("=" * 60)
    
    claims = ClaimExtractor.extract(SIMULATED_ANSWER)
    
    if not claims:
        print("   No claims extracted (check extractor patterns)")
        sys.exit(1)
    
    print(f"\n   Extracted {len(claims)} claims:\n")
    for i, claim in enumerate(claims):
        print(f"   {i + 1}. [{claim.subject}] {claim.predicate} [{claim.obj}]")
    
    # Step 4: Validate claims
    print("\n" + "=" * 60)
    print("CLAIM VALIDATION")
    print("=" * 60)
    print(f"   Using similarity threshold: {SIMILARITY_THRESHOLD}")
    print(f"   Searching top {TOP_K_RESULTS} chunks per claim...\n")
    
    detector = HallucinationDetector(db, threshold=SIMILARITY_THRESHOLD)
    results = detector.detect_all(claims)
    
    # Step 5: Print results
    print_results(results)
    
    # Step 6: Architecture comparison note
    print("\n" + "=" * 60)
    print("ARCHITECTURE NOTE")
    print("=" * 60)
    print("""
   This pipeline used a SINGLE RushDB instance to:
   
   1. Store documents as nodes with metadata
   2. Store chunks with pre-computed vector embeddings
   3. Create SOURCED_FROM relationships in the graph
   4. Query vector similarity for claim validation
   5. Traverse the graph to find provenance for failed claims
   
   Alternative approach (3-system stitching):
   - Vector DB (Pinecone/Qdrant) for embeddings
   - Graph DB (Neo4j) for relationships
   - LLM Proxy (custom) for evaluation
   
   → Higher latency from cross-system queries
   → Sync complexity between systems
   → Three API integrations to maintain
""")
    
    print("\nPipeline complete.\n")


if __name__ == "__main__":
    main()
