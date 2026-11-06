#!/usr/bin/env python3
"""
Self-Improving Knowledge Bases with RushDB Feedback Loops

This demonstration shows how RushDB's graph+vector architecture enables
knowledge bases that learn from user corrections.

Key concepts demonstrated:
1. Storing corrections as graph edges with full metadata
2. Propagating corrections through RELATED_TO relationships
3. Computing trust scores from correction history
4. Hybrid ranking (semantic similarity × trust score)
5. Building provenance chains for result explanation
"""

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import dotenv
from rushdb import RushDB

# Load environment variables
dotenv.load_dotenv()

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Correction:
    """Represents a user-submitted correction to an article."""
    user_email: str
    user_reputation: float
    article_title: str
    correction_type: str  # factual, clarity, style, accuracy
    old_text: str
    new_text: str
    context: str


@dataclass
class TrustScoreResult:
    """Result of trust score computation for an article."""
    article_id: str
    article_title: str
    base_score: float
    correction_bonus: float
    user_reputation_factor: float
    correction_decay: float
    final_score: float
    factors: dict = field(default_factory=dict)


@dataclass
class ProvenanceEntry:
    """An entry in a result's provenance chain."""
    article_id: str
    article_title: str
    vector_score: float
    trust_score: float
    hybrid_score: float
    corrections_applied: list = field(default_factory=list)
    related_to: list = field(default_factory=list)



# ============================================================================
# FEEDBACK LOOP COMPONENTS
# ============================================================================

class KnowledgeBase:
    """
    Self-improving knowledge base built on RushDB.
    
    Demonstrates the feedback loop:
    1. Users submit corrections as graph edges
    2. Corrections propagate to related articles
    3. Trust scores recalculate based on correction history
    4. Search results improve with hybrid ranking
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.base_trust_score = 0.7  # Starting trust for new articles
        self.max_trust_score = 1.0
        self.min_trust_score = 0.3
        self.correction_weight = 0.05  # Trust increase per verified correction
        self.decay_half_life_days = 90  # Corrections half-value after 90 days
    
    def find_article_by_title(self, title: str) -> Optional[dict]:
        """Find an article by its title."""
        result = self.db.records.find({
            "labels": ["Article"],
            "where": {"title": title}
        })
        if result.data:
            return result.data[0]
        return None
    
    def find_or_create_user(self, email: str, reputation: float = 0.8) -> dict:
        """
        Find or create a user record.
        
        Users track who made corrections for provenance and reputation weighting.
        """
        result = self.db.records.find({
            "labels": ["User"],
            "where": {"email": email}
        })
        
        if result.data:
            return result.data[0]
        
        return self.db.records.create(
            label="User",
            data={
                "email": email,
                "reputation": reputation,
                "corrections_submitted": 0,
                "created_at": datetime.now().isoformat()
            }
        )
    
    def submit_correction(self, correction: Correction) -> dict:
        """
        Submit a user correction to an article.
        
        This creates:
        - A Correction record with full metadata
        - CORRECTED edge from Correction to Article
        - AUTHORED edge from User to Correction
        - CORRECTION_RECEIVED edge from Article to Correction
        
        Returns the created correction record.
        """
        print(f"\n{'='*60}")
        print(f"SUBMITTING CORRECTION")
        print(f"{'='*60}")
        print(f"User: {correction.user_email}")
        print(f"Article: {correction.article_title}")
        print(f"Type: {correction.correction_type}")
        print(f"---")
        print(f"Old: {correction.old_text[:60]}...")
        print(f"New: {correction.new_text[:60]}...")
        
        # Find the article
        article = self.find_article_by_title(correction.article_title)
        if not article:
            print(f"Warning: Article '{correction.article_title}' not found")
            return None
        
        # Find or create the user
        user = self.find_or_create_user(
            correction.user_email,
            correction.user_reputation
        )
        
        # Create correction record with all metadata
        correction_record = self.db.records.create(
            label="Correction",
            data={
                "old_text": correction.old_text,
                "new_text": correction.new_text,
                "type": correction.correction_type,
                "context": correction.context,
                "user_email": correction.user_email,
                "user_reputation": correction.user_reputation,
                "submitted_at": datetime.now().isoformat(),
                "status": "pending",  # pending, approved, rejected
                "verified": True  # In production, this would be a review process
            }
        )
        
        # Create graph relationships
        with self.db.transactions.begin() as tx:
            # Who authored this correction
            self.db.records.attach(
                source=user,
                target=correction_record,
                options={"type": "AUTHORED", "direction": "out"},
                transaction=tx
            )
            
            # What does this correction fix
            self.db.records.attach(
                source=correction_record,
                target=article,
                options={"type": "CORRECTED", "direction": "out"},
                transaction=tx
            )
            
            # What corrections has this article received
            self.db.records.attach(
                source=article,
                target=correction_record,
                options={"type": "CORRECTION_RECEIVED", "direction": "out"},
                transaction=tx
            )
        
        # Update article with corrected content
        current_body = article["body"]
        updated_body = current_body.replace(
            correction.old_text,
            correction.new_text
        )
        
        self.db.records.update(
            record_id=article.id,
            data={
                "body": updated_body,
                "version": article.get("version", 1) + 1,
                "last_verified_at": datetime.now().isoformat(),
                "correction_count": article.get("correction_count", 0) + 1
            }
        )
        
        print(f"\n✓ Correction recorded and article updated")
        print(f"  Correction ID: {correction_record.id}")
        print(f"  Article updated to version {article.get('version', 1) + 1}")
        
        return correction_record
    
    def propagate_correction(self, article_id: str, source_article_id: str) -> list:
        """
        Propagate a correction from one article to related articles.
        
        When an article receives a correction, we find its RELATED_TO neighbors
        and apply the correction to them if the content is relevant.
        
        Returns list of articles that received the propagation.
        """
        print(f"\n{'='*60}")
        print(f"PROPAGATING CORRECTION")
        print(f"{'='*60}")
        
        # Find all related articles via graph traversal
        related = self.db.records.find({
            "labels": ["Article"],
            "where": {
                "Article": {
                    "$relation": {
                        "type": "RELATED_TO",
                        "direction": "in"
                    },
                    "$id": article_id
                }
            },
            "limit": 20
        })
        
        print(f"Found {related.total} related articles")
        
        propagated_to = []
        
        for related_article in related.data:
            # Skip the source article
            if related_article.id == source_article_id:
                continue
            
            # Get the corrections received by the source article
            corrections = self.db.records.find({
                "labels": ["Correction"],
                "where": {
                    "Article": {
                        "$relation": {
                            "type": "CORRECTED",
                            "direction": "in"
                        },
                        "$id": source_article_id
                    }
                },
                "limit": 10,
                "orderBy": {"submitted_at": "desc"}
            })
            
            for correction in corrections.data:
                old_text = correction.get("old_text", "")
                new_text = correction.get("new_text", "")
                
                # Only propagate if the content exists in the related article
                if old_text and old_text in related_article.get("body", ""):
                    # Create propagation record
                    propagation = self.db.records.create(
                        label="Propagation",
                        data={
                            "source_article_id": source_article_id,
                            "target_article_id": related_article.id,
                            "correction_id": correction.id,
                            "old_text": old_text,
                            "new_text": new_text,
                            "propagated_at": datetime.now().isoformat()
                        }
                    )
                    
                    # Update the related article's body
                    new_body = related_article["body"].replace(old_text, new_text)
                    
                    self.db.records.update(
                        record_id=related_article.id,
                        data={
                            "body": new_body,
                            "version": related_article.get("version", 1) + 1,
                            "propagated_from": source_article_id,
                            "last_verified_at": datetime.now().isoformat()
                        }
                    )
                    
                    propagated_to.append({
                        "title": related_article["title"],
                        "id": related_article.id,
                        "correction": correction.get("new_text", "")[:50]
                    })
                    
                    print(f"  ✓ {related_article['title']}")
        
        return propagated_to
    
    def compute_trust_score(self, article: dict) -> TrustScoreResult:
        """
        Compute trust score for an article based on its correction history.
        
        Algorithm:
        1. Start with base trust score
        2. Add bonus for verified corrections (up to max)
        3. Weight by user reputation of correctors
        4. Apply time decay to old corrections
        
        Returns TrustScoreResult with breakdown.
        """
        base_score = self.base_trust_score
        factors = {}
        
        # Get all corrections for this article
        corrections = self.db.records.find({
            "labels": ["Correction"],
            "where": {
                "Article": {
                    "$relation": {
                        "type": "CORRECTED",
                        "direction": "in"
                    },
                    "$id": article.id
                }
            }
        })
        
        correction_bonus = 0.0
        user_reputation_factor = 1.0
        total_reputation = 0.0
        
        if corrections.data:
            now = datetime.now()
            total_reputation = sum(
                c.get("user_reputation", 0.8) for c in corrections.data
            )
            avg_reputation = total_reputation / len(corrections.data)
            
            # Each verified correction adds trust, weighted by user reputation
            for correction in corrections.data:
                rep = correction.get("user_reputation", 0.8)
                
                # Time decay
                submitted_at = datetime.fromisoformat(
                    correction["submitted_at"].replace("Z", "+00:00")
                )
                days_old = (now - submitted_at).days
                decay = 0.5 ** (days_old / self.decay_half_life_days)
                
                weighted_bonus = self.correction_weight * rep * decay
                correction_bonus += weighted_bonus
            
            # User reputation affects how much corrections matter
            # High-reputation users' corrections have more impact
            user_reputation_factor = 0.5 + (avg_reputation * 0.5)
        
        # Apply factors
        correction_decay = 0.0  # Could subtract for articles with many old corrections
        
        final_score = min(
            self.max_trust_score,
            max(
                self.min_trust_score,
                base_score + (correction_bonus * user_reputation_factor) - correction_decay
            )
        )
        
        factors["correction_count"] = len(corrections.data)
        factors["avg_user_reputation"] = total_reputation / len(corrections.data) if corrections.data else 0.8
        factors["user_reputation_factor"] = user_reputation_factor
        factors["correction_bonus"] = correction_bonus
        
        return TrustScoreResult(
            article_id=article.id,
            article_title=article["title"],
            base_score=base_score,
            correction_bonus=correction_bonus,
            user_reputation_factor=user_reputation_factor,
            correction_decay=correction_decay,
            final_score=final_score,
            factors=factors
        )
    
    def update_all_trust_scores(self) -> list:
        """
        Recalculate trust scores for all articles.
        
        Returns list of updated trust scores.
        """
        print(f"\n{'='*60}")
        print(f"UPDATING ALL TRUST SCORES")
        print(f"{'='*60}")
        
        all_articles = self.db.records.find({
            "labels": ["Article"],
            "limit": 100
        })
        
        results = []
        
        for article in all_articles.data:
            trust_result = self.compute_trust_score(article)
            
            # Update the article's stored trust score
            self.db.records.update(
                record_id=article.id,
                data={"trust_score": trust_result.final_score}
            )
            
            results.append(trust_result)
            
            print(f"  {article['title'][:40]:<40} | Trust: {trust_result.final_score:.3f}")
        
        print(f"\n✓ Updated trust scores for {len(results)} articles")
        return results
    
    def hybrid_search(self, query: str, limit: int = 5) -> list[ProvenanceEntry]:
        """
        Perform hybrid search combining semantic similarity with trust scores.
        
        1. Run semantic search to get vector similarity scores
        2. Fetch trust scores from graph
        3. Combine: hybrid_score = similarity * (0.5 + trust_score * 0.5)
        4. Build provenance chain for each result
        
        Returns ranked results with provenance information.
        """
        print(f"\n{'='*60}")
        print(f"HYBRID SEARCH: {query}")
        print(f"{'='*60}")
        
        # Step 1: Semantic search
        semantic_results = self.db.ai.search({
            "propertyName": "body",
            "query": query,
            "labels": ["Article"],
            "limit": limit * 2  # Fetch extra in case some are filtered
        })
        
        if not semantic_results.data:
            print("No results found")
            return []
        
        print(f"\nSemantic search returned {len(semantic_results.data)} candidates")
        
        # Step 2: Build provenance and combine with trust scores
        provenance_entries = []
        
        for result in semantic_results.data:
            # Get trust score
            trust_result = self.compute_trust_score(result)
            
            # Calculate hybrid score
            # Weight: 50% similarity, 50% trust (can be tuned)
            vector_score = result.score if result.score else 0.0
            trust_weight = 0.5 + (trust_result.final_score * 0.5)
            hybrid_score = vector_score * trust_weight
            
            # Get corrections that affected this article
            corrections = self.db.records.find({
                "labels": ["Correction"],
                "where": {
                    "Article": {
                        "$relation": {
                            "type": "CORRECTED",
                            "direction": "in"
                        },
                        "$id": result.id
                    }
                },
                "limit": 5
            })
            
            corrections_info = [
                {
                    "id": c.id,
                    "type": c.get("type", "unknown"),
                    "user": c.get("user_email", "anonymous"),
                    "new_text": c.get("new_text", "")[:50]
                }
                for c in corrections.data
            ]
            
            # Get related articles
            related = self.db.records.find({
                "labels": ["Article"],
                "where": {
                    "Article": {
                        "$relation": {
                            "type": "RELATED_TO",
                            "direction": "in"
                        },
                        "$id": result.id
                    }
                },
                "limit": 5
            })
            
            related_info = [
                {"id": r.id, "title": r["title"]}
                for r in related.data
            ]
            
            entry = ProvenanceEntry(
                article_id=result.id,
                article_title=result["title"],
                vector_score=vector_score,
                trust_score=trust_result.final_score,
                hybrid_score=hybrid_score,
                corrections_applied=corrections_info,
                related_to=related_info
            )
            
            provenance_entries.append(entry)
        
        # Step 3: Sort by hybrid score and return top results
        provenance_entries.sort(key=lambda x: x.hybrid_score, reverse=True)
        return provenance_entries[:limit]
    
    def print_provenance_report(self, results: list[ProvenanceEntry]):
        """
        Print a detailed provenance report for search results.
        """
        print(f"\n{'='*60}")
        print(f"PROVENANCE REPORT")
        print(f"{'='*60}")
        
        for rank, entry in enumerate(results, 1):
            print(f"\n{'─'*60}")
            print(f"RANK #{rank}: {entry.article_title}")
            print(f"{'─'*60}")
            print(f"  Scores:")
            print(f"    Vector similarity: {entry.vector_score:.4f}")
            print(f"    Trust score:       {entry.trust_score:.4f}")
            print(f"    Hybrid score:      {entry.hybrid_score:.4f}")
            
            if entry.corrections_applied:
                print(f"  Corrections applied ({len(entry.corrections_applied)}):")
                for corr in entry.corrections_applied:
                    print(f"    • [{corr['type']}] by {corr['user']}")
                    print(f"      → {corr['new_text']}...")
            else:
                print(f"  Corrections: None (base article)")
            
            if entry.related_to:
                print(f"  Related articles ({len(entry.related_to)}):")
                for rel in entry.related_to[:3]:
                    print(f"    ↔ {rel['title']}")


# ============================================================================
# DEMONSTRATION
# ============================================================================

def load_corrections() -> list[Correction]:
    """Load sample corrections from data file."""
    data_path = Path(__file__).parent / "data" / "corrections.json"
    with open(data_path) as f:
        data = json.load(f)
    
    return [
        Correction(
            user_email=c["user_email"],
            user_reputation=c["user_reputation"],
            article_title=c["article_title"],
            correction_type=c["correction_type"],
            old_text=c["old_text"],
            new_text=c["new_text"],
            context=c["context"]
        )
        for c in data
    ]


def run_demonstration():
    """
    Run the complete feedback loop demonstration.
    """
    print("\n" + "="*60)
    print("SELF-IMPROVING KNOWLEDGE BASE WITH RUSHDB FEEDBACK LOOPS")
    print("="*60)
    
    # Initialize client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY environment variable not set")
        print("Copy .env.example to .env and fill in your API key")
        sys.exit(1)
    
    db = RushDB(api_key)
    kb = KnowledgeBase(db)
    
    # Check if data is seeded
    articles = db.records.find({"labels": ["Article"], "limit": 1})
    if articles.total == 0:
        print("\nNo articles found. Run 'python seed.py' first to populate the knowledge base.")
        sys.exit(1)
    
    print(f"\nFound {articles.total} articles in the knowledge base")
    
    # ========================================================================
    # PHASE 1: BASELINE SEARCH (before corrections)
    # ========================================================================
    print("\n" + "="*60)
    print("PHASE 1: BASELINE SEARCH (before corrections)")
    print("="*60)
    
    query = "how does Python handle memory management with garbage collection"
    baseline_results = kb.hybrid_search(query, limit=3)
    kb.print_provenance_report(baseline_results)
    
    # ========================================================================
    # PHASE 2: SUBMIT CORRECTIONS
    # ========================================================================
    print("\n\n" + "="*60)
    print("PHASE 2: USER SUBMITS CORRECTIONS")
    print("="*60)
    
    corrections = load_corrections()
    
    # Submit first correction (the most impactful one)
    primary_correction = corrections[0]
    correction_record = kb.submit_correction(primary_correction)
    
    if correction_record:
        # Find the article to propagate to
        article = kb.find_article_by_title(primary_correction.article_title)
        if article:
            kb.propagate_correction(article.id, article.id)
    
    # ========================================================================
    # PHASE 3: UPDATE TRUST SCORES
    # ========================================================================
    trust_results = kb.update_all_trust_scores()
    
    # ========================================================================
    # PHASE 4: IMPROVED SEARCH (after corrections)
    # ========================================================================
    print("\n\n" + "="*60)
    print("PHASE 4: IMPROVED SEARCH (after corrections)")
    print("="*60)
    
    improved_results = kb.hybrid_search(query, limit=3)
    kb.print_provenance_report(improved_results)
    
    # ========================================================================
    # PHASE 5: COMPARISON SUMMARY
    # ========================================================================
    print("\n\n" + "="*60)
    print("COMPARISON: BEFORE vs AFTER CORRECTIONS")
    print("="*60)
    
    print(f"\n{'Rank':<6} {'Before':<30} {'After':<30}")
    print("-"*66)
    
    for i, (before, after) in enumerate(zip(baseline_results, improved_results), 1):
        before_title = before.article_title[:28]
        after_title = after.article_title[:28]
        print(f"{i:<6} {before_title:<30} {after_title:<30}")
    
    # ========================================================================
    # PHASE 6: EXPLORE THE GRAPH
    # ========================================================================
    print("\n\n" + "="*60)
    print("PHASE 6: EXPLORING THE GRAPH STRUCTURE")
    print("="*60)
    
    # Count corrections
    all_corrections = db.records.find({"labels": ["Correction"], "limit": 100})
    print(f"\nTotal corrections in system: {all_corrections.total}")
    
    # Count relationships
    all_articles = db.records.find({"labels": ["Article"], "limit": 100})
    print(f"Total articles in system: {all_articles.total}")
    
    # Show articles with corrections
    articles_with_corrections = [
        a for a in all_articles.data
        if a.get("correction_count", 0) > 0
    ]
    print(f"Articles with corrections: {len(articles_with_corrections)}")
    
    for article in articles_with_corrections:
        trust = kb.compute_trust_score(article)
        print(f"\n  {article['title']}")
        print(f"    Trust: {trust.final_score:.3f} | Corrections: {article.get('correction_count', 0)}")
        print(f"    Version: {article.get('version', 1)}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n\n" + "="*60)
    print("FEEDBACK LOOP SUMMARY")
    print("="*60)
    print("""
This demonstration showed how RushDB's dual graph+vector architecture
creates a self-improving knowledge base:

1. CORRECTION AS EDGE
   User corrections are stored as graph edges with full metadata:
   - Who made the correction (User.AUTHORED Correction)
   - What was corrected (Correction.CORRECTED Article)
   - Why it was corrected (context field)

2. AUTOMATIC PROPAGATION
   Corrections flow through RELATED_TO edges:
   - Correcting one Python article updates related Python articles
   - Propagation records track the chain of influence

3. TRUST SCORE COMPUTATION
   Graph traversal determines article reliability:
   - High-reputation users' corrections weigh more
   - Recent corrections decay slower than old ones
   - Corrections from multiple sources increase trust

4. HYBRID RANKING
   Search results combine:
   - Vector similarity (semantic matching)
   - Trust scores (reliability from graph)
   - Provenance (explanation of ranking factors)

5. PROVENANCE CHAINS
   Every result explains its ranking:
   - Which corrections affected it
   - Which related articles influenced it
   - Who verified the content
""")
    
    print("\nThis is what distinguishes RushDB from plain vector stores!")


if __name__ == "__main__":
    run_demonstration()
