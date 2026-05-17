#!/usr/bin/env python3
"""
Claim extraction and validation utilities.

This module provides the claim extraction logic and validation helpers
used by the main pipeline. Can be imported and extended for production use.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Claim:
    """Represents a single claim extracted from text.
    
    Attributes:
        subject: The entity making a claim
        predicate: The action or state being claimed
        obj: The object or measurement being claimed
        full_text: Original sentence containing the claim
        claim_id: Unique identifier for the claim
    """
    subject: str
    predicate: str
    obj: str
    full_text: str
    claim_id: int


@dataclass
class ValidationResult:
    """Result of validating a claim against the knowledge base.
    
    Attributes:
        claim: The original claim that was validated
        verified: True if the claim is verified against sources
        best_similarity: Similarity score of the best-matching chunk (0.0-1.0)
        best_match_chunk: The chunk record that best supports the claim
        best_match_source: The source document that provided the chunk
        failure_reason: Why verification failed (if applicable)
    """
    claim: Claim
    verified: bool
    best_similarity: float
    best_match_chunk: Optional[dict] = None
    best_match_source: Optional[dict] = None
    failure_reason: Optional[str] = None


class ClaimExtractor:
    """Extracts structured claims from unstructured text.
    
    Uses pattern matching to identify subject-predicate-object structures
    commonly found in factual claims. Designed to be extended with additional
    patterns for domain-specific use cases.
    
    Example:
        extractor = ClaimExtractor()
        claims = extractor.extract("Solar panels can increase crop yields by 30%.")
        # Returns: [Claim(subject="solar panels", predicate="can increase crop yields", 
        #                   obj="by 30%", ...)] 
    """
    
    # Subject patterns - common entities in factual claims
    SUBJECT_PATTERNS = [
        r'(solar panels?[\w\s]*)',
        r'(agrivoltaics?)',
        r'(the technology)',
        r'(this approach)',
        r'(dual-use approach)',
        r'(farms?)',
        r'(land equivalent efficiency)',
        r'(sheep)',
        r'(solar installations)',
        r'(energy yields?)',
        r'(bifacial solar panels?)',
        r'(the shading)',
    ]
    
    # Predicate-object patterns with capture groups
    # Format: (regex, predicate_template, object_template)
    CLAIM_PATTERNS = [
        (r'can boost crop yields by up to (\d+%)',
         'can boost crop yields',
         'by up to \1'),
        
        (r'increase yields by (\d+-\d+%)',
         'increases yields',
         'by \1'),
        
        (r'reducing water consumption by (\d+%)',
         'reduces water consumption',
         'by \1'),
        
        (r'water (?:requirements |needs )?drop by (\d+-\d+%)',
         'reduces water requirements',
         'by \1'),
        
        (r'first commercial installations appeared in (\w+) in (\d+)',
         'first appeared',
         'in \1 in \2'),
        
        (r'first developed in (\w+) (?:in |around )?(20\d{2})',
         'was first developed',
         'in \1 in \2'),
        
        (r'generates?\s+(\d+-\d+\s+kWh)',
         'generates energy',
         '\1 per kilowatt annually'),
        
        (r'land equivalent efficiency can reach (\d+%)',
         'can reach land equivalent efficiency',
         'of \1'),
        
        (r'land equivalent efficiency (?:to |of )?(\d+%)',
         'achieves land equivalent efficiency',
         'of \1'),
        
        (r'installed capacity (?:of )?(\d+\s+kW)',
         'installed capacity',
         'of \1'),
        
        (r'energy yields (?:of )?(\d+-\d+\s+kWh)',
         'achieves energy yields',
         'of \1'),
    ]
    
    @classmethod
    def extract(cls, text: str) -> list[Claim]:
        """Extract claims from text.
        
        Args:
            text: The source text to extract claims from
            
        Returns:
            List of Claim objects representing each extracted claim
        """
        claims = []
        
        # Normalize whitespace and split into sentences
        text = re.sub(r'\s+', ' ', text)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 20]
        
        claim_id = 0
        
        for sentence in sentences:
            # Try to extract a subject
            subject = cls._extract_subject(sentence)
            if not subject:
                continue
            
            # Try to extract a predicate-object pair
            for pattern, predicate, obj_template in cls.CLAIM_PATTERNS:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    # Build object from template and captured groups
                    obj = obj_template
                    for i, group in enumerate(match.groups(), 1):
                        obj = obj.replace(f'\\{i}', group or '')
                    obj = re.sub(r'\\\d+', '', obj)  # Clean up
                    obj = obj.strip()
                    
                    claim = Claim(
                        subject=subject.strip(),
                        predicate=predicate.strip(),
                        obj=obj.strip(),
                        full_text=sentence.strip(),
                        claim_id=claim_id
                    )
                    claims.append(claim)
                    claim_id += 1
                    break  # One claim per sentence
        
        return claims
    
    @classmethod
    def _extract_subject(cls, sentence: str) -> Optional[str]:
        """Extract the subject from a sentence."""
        for pattern in cls.SUBJECT_PATTERNS:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None


class ProvenanceTracer:
    """Traces provenance through the RushDB graph.
    
    Used to find the source document that provided evidence for a claim,
    enabling targeted diagnosis of hallucination sources.
    """
    
    @staticmethod
    def trace_source_chunk(db, chunk_id: str) -> Optional[dict]:
        """Find the source document for a given chunk.
        
        Args:
            db: RushDB client instance
            chunk_id: ID of the chunk to trace
            
        Returns:
            Source document record if found, None otherwise
        """
        result = db.records.find({
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
    
    @staticmethod
    def get_all_sources_for_claim(db, claim_text: str, limit: int = 5) -> list[dict]:
        """Get all source documents that could support a claim.
        
        Args:
            db: RushDB client instance
            claim_text: The claim text to search for
            limit: Maximum number of results
            
        Returns:
            List of source document records with their supporting chunks
        """
        # Search for relevant chunks
        results = db.ai.search({
            "propertyName": "text",
            "query": claim_text,
            "labels": ["CHUNK"],
            "limit": limit
        })
        
        sources = []
        for chunk in results.data:
            source = ProvenanceTracer.trace_source_chunk(db, chunk.id)
            if source:
                sources.append({
                    "source": source.data,
                    "chunk": chunk.data,
                    "score": chunk.score
                })
        
        return sources


def format_claim(claim: Claim) -> str:
    """Format a claim for display."""
    return f"[{claim.subject}] {claim.predicate} [{claim.obj}]"


def format_validation_result(result: ValidationResult) -> str:
    """Format a validation result for display."""
    status = "✅ VERIFIED" if result.verified else "❌ FAILED"
    lines = [
        f"{status} (similarity: {result.best_similarity:.3f})",
        f"  Claim: {format_claim(result.claim)}",
        f"  Text: \"{result.claim.full_text}\"",
    ]
    
    if result.verified:
        if result.best_match_source:
            lines.append(f"  Source: {result.best_match_source.get('title', 'Unknown')}")
        if result.best_match_chunk:
            chunk_text = result.best_match_chunk.get('text', '')[:100]
            lines.append(f"  Evidence: \"{chunk_text}...\"")
    else:
        lines.append(f"  Reason: {result.failure_reason}")
    
    return "\n".join(lines)


# CLI for testing
if __name__ == "__main__":
    # Test claim extraction
    test_text = """
    Solar panels installed on agricultural land can boost crop yields by up to 30%.
    This dual-use approach has been shown to reduce water consumption by 40%.
    The technology was first developed in Japan in 2004.
    Energy yields can reach 800-1200 kWh per kilowatt annually.
    """
    
    print("Testing claim extraction...\n")
    claims = ClaimExtractor.extract(test_text)
    
    for claim in claims:
        print(f"  {claim.claim_id + 1}. {format_claim(claim)}")
        print(f"     Full: \"{claim.full_text}\"\n")
    
    print(f"\nExtracted {len(claims)} claims from test text.")
