"""
Hallucination detection engine using graph inconsistency scoring.
Analyzes claim relationships to detect hallucination chains.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from rushdb import RushDB


@dataclass
class InconsistencyReport:
    """Report on hallucination detection for an entity."""
    entity_name: str
    total_claims: int
    contradiction_count: int
    support_count: int
    inconsistency_score: float
    hallucination_chains: list = field(default_factory=list)
    claims: list = field(default_factory=list)


class HallucinationDetector:
    """
    Detects hallucination chains using graph-based inconsistency scoring.
    
    Algorithm:
    1. Collect all claims mentioning a target entity
    2. Build a subgraph of relationship edges between claims
    3. Calculate inconsistency score = contradictions / (contradictions + supports)
    4. Find chains of contradictory claims (hallucination paths)
    """
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def get_entity_claims(self, entity_name: str) -> list:
        """Find all claims mentioning a specific entity."""
        claims = self.db.records.find({
            "labels": ["CLAIM"]
        })
        
        # Filter by entity field (stored in the claim data)
        entity_claims = [
            claim for claim in claims 
            if claim.data.get("entity") == entity_name
        ]
        
        return entity_claims
    
    def get_claim_relationships(self, claim_ids: list) -> dict:
        """
        Get all relationships between given claims.
        Returns dict: {(id_a, id_b): relationship_type}
        """
        relationships = {}
        
        # Find all claims and their outgoing relationships
        for claim in self.db.records.find_by_id(claim_ids):
            # Query for connected claims with CONTRADICTS or SUPPORTS relationships
            related_claims = self.db.records.find({
                "labels": ["CLAIM"],
                "where": {
                    "$or": [
                        {"CONTRADICTS_CLAIM": {"$id": claim.id}},
                        {"SUPPORTS_CLAIM": {"$id": claim.id}},
                    ]
                }
            })
            
            for related in related_claims:
                # Determine relationship type by checking the relationship direction
                rel_type = self._get_relationship_type(claim, related)
                if rel_type:
                    key = tuple(sorted([claim.id, related.id]))
                    relationships[key] = rel_type
        
        return relationships
    
    def _get_relationship_type(self, claim_a, claim_b) -> Optional[str]:
        """Determine the relationship type between two claims."""
        # Check if they were created with CONTRADICTS relationship
        # This is a simplified approach - in production you'd traverse relationships directly
        claims = self.db.records.find({
            "labels": ["CLAIM"]
        })
        
        # Look for explicit contradiction markers in the data
        for claim in claims:
            if claim.id in [claim_a.id, claim_b.id]:
                # Check if this claim has contradiction metadata
                pass
        
        return None
    
    def calculate_inconsistency_score(
        self, 
        contradictions: int, 
        supports: int
    ) -> float:
        """
        Calculate inconsistency score based on relationship counts.
        
        Score formula: contradictions / (contradictions + supports + 1)
        The +1 prevents division by zero and adds a baseline.
        
        Returns value between 0.0 (fully consistent) and 1.0 (fully inconsistent).
        """
        if contradictions == 0 and supports == 0:
            return 0.0
        
        return contradictions / (contradictions + supports + 1)
    
    def find_hallucination_chains(
        self, 
        claims: list, 
        max_chain_length: int = 4
    ) -> list:
        """
        Find chains of contradictory claims (hallucination paths).
        
        A hallucination chain is a path where each adjacent pair 
        of claims contradicts each other.
        """
        chains = []
        
        # Build adjacency map from claims
        adjacency = defaultdict(list)
        claim_map = {c.id: c for c in claims}
        
        # Query for all contradiction relationships between these claims
        for claim in claims:
            # Find claims that contradict this one
            contradicts = self.db.records.find({
                "labels": ["CLAIM"],
                "where": {
                    "CONTRADICTS_CLAIM": {"$id": claim.id}
                }
            })
            
            for other in contradicts:
                if other.id in claim_map:
                    adjacency[claim.id].append((other.id, "CONTRADICTS"))
        
        # BFS to find all contradiction chains
        for start_claim in claims:
            visited = {start_claim.id}
            queue = deque([(start_claim, [start_claim])])
            
            while queue:
                current, path = queue.popleft()
                
                if len(path) >= max_chain_length:
                    continue
                
                for neighbor_id, rel_type in adjacency[current.id]:
                    if neighbor_id not in visited:
                        new_path = path + [claim_map[neighbor_id]]
                        
                        # Only continue if relationship is CONTRADICTS
                        if rel_type == "CONTRADICTS":
                            chains.append(new_path)
                            visited.add(neighbor_id)
                            queue.append((claim_map[neighbor_id], new_path))
        
        return chains
    
    def detect_hallucination(self, entity_name: str) -> InconsistencyReport:
        """
        Main detection method - analyze an entity for hallucination indicators.
        
        Returns an InconsistencyReport with:
        - Total claims about the entity
        - Contradiction and support counts
        - Inconsistency score (0.0 to 1.0)
        - Detected hallucination chains
        """
        # Step 1: Get all claims about this entity
        claims = self.get_entity_claims(entity_name)
        
        if not claims:
            return InconsistencyReport(
                entity_name=entity_name,
                total_claims=0,
                contradiction_count=0,
                support_count=0,
                inconsistency_score=0.0,
                hallucination_chains=[]
            )
        
        # Step 2: Count relationship types
        contradiction_count = 0
        support_count = 0
        
        for claim in claims:
            # Find contradicts relationships
            contradicts = self.db.records.find({
                "labels": ["CLAIM"],
                "where": {
                    "CONTRADICTS_CLAIM": {"$id": claim.id}
                }
            })
            contradiction_count += len(contradicts)
            
            # Find supports relationships
            supports = self.db.records.find({
                "labels": ["CLAIM"],
                "where": {
                    "SUPPORTS_CLAIM": {"$id": claim.id}
                }
            })
            support_count += len(supports)
        
        # Deduplicate (each relationship counted twice from both ends)
        contradiction_count //= 2
        support_count //= 2
        
        # Step 3: Calculate inconsistency score
        inconsistency_score = self.calculate_inconsistency_score(
            contradiction_count, 
            support_count
        )
        
        # Step 4: Find hallucination chains
        hallucination_chains = self.find_hallucination_chains(claims)
        
        return InconsistencyReport(
            entity_name=entity_name,
            total_claims=len(claims),
            contradiction_count=contradiction_count,
            support_count=support_count,
            inconsistency_score=inconsistency_score,
            hallucination_chains=hallucination_chains,
            claims=claims
        )
    
    def generate_report(self, report: InconsistencyReport) -> str:
        """Format an InconsistencyReport as a readable string."""
        risk_level = self._score_to_risk_level(report.inconsistency_score)
        
        lines = [
            f"\n{'='*60}",
            f"Entity: {report.entity_name}",
            f"{'='*60}",
            f"  Total Claims: {report.total_claims}",
            f"  Contradictions: {report.contradiction_count}",
            f"  Supports: {report.support_count}",
            f"  Inconsistency Score: {report.inconsistency_score:.2f} ({risk_level})",
        ]
        
        if report.hallucination_chains:
            lines.append("\n  Hallucination Chains Detected:")
            for i, chain in enumerate(report.hallucination_chains, 1):
                chain_str = " → ".join([c.data.get("text", "")[:40] + "..." for c in chain])
                lines.append(f"    Chain {i}: {chain_str}")
        
        if report.contradiction_count > 0:
            lines.append("\n  Contradicting Claims:")
            seen_pairs = set()
            for claim in report.claims:
                contradicts = self.db.records.find({
                    "labels": ["CLAIM"],
                    "where": {
                        "CONTRADICTS_CLAIM": {"$id": claim.id}
                    }
                })
                for other in contradicts:
                    pair_key = tuple(sorted([claim.id, other.id]))
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        lines.append(f"    • \"{claim.data.get('text', '')[:50]}...\"")
                        lines.append(f"      CONTRADICTS \"{other.data.get('text', '')[:50]}...\"")
        
        lines.append("")
        return "\n".join(lines)
    
    def _score_to_risk_level(self, score: float) -> str:
        """Convert numeric score to human-readable risk level."""
        if score < 0.2:
            return "LOW"
        elif score < 0.5:
            return "MEDIUM"
        elif score < 0.7:
            return "HIGH"
        else:
            return "CRITICAL"
