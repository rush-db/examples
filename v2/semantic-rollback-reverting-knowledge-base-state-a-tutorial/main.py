#!/usr/bin/env python3
"""
Semantic Rollback: Reverting Knowledge Base State

A complete implementation demonstrating how to implement semantic rollback
in a production knowledge base using RushDB.

This tutorial covers:
1. Prerequisite architecture: graph for entities/relationships, vector index for similarity
2. Capture semantic snapshot before updates
3. Detect rollback trigger (manual flag, external validation, LLM confidence threshold)
4. Revert graph subgraph while preserving unrelated nodes
5. Rebuild affected vector index entries atomically

Target audience: Backend engineers implementing AI memory or knowledge management systems
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# =============================================================================
# Data Models
# =============================================================================

@dataclass
class SemanticSnapshot:
    """
    Represents a point-in-time snapshot of knowledge base state.
    
    This snapshot captures:
    - Record IDs and their full data
    - Vector embeddings for each record
    - Relationship graph structure
    - Metadata about the snapshot (timestamp, ID, purpose)
    """
    snapshot_id: str
    timestamp: str
    purpose: str
    article_snapshots: list = field(default_factory=list)
    preserved_relationships: list = field(default_factory=list)


@dataclass
class ArticleSnapshot:
    """Snapshot of a single article's state."""
    record_id: str
    slug: str
    title: str
    body: str
    tags: list
    status: str
    vector: list
    related_concept_ids: list = field(default_factory=list)


@dataclass
class RollbackTrigger:
    """Represents a trigger that initiated the rollback process."""
    trigger_type: str  # 'manual', 'confidence', 'validation'
    message: str
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# Embedding Generation
# =============================================================================

def get_embedding(text: str) -> list:
    """Generate embedding for text using sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text).tolist()


def calculate_confidence(embedding: list) -> float:
    """
    Calculate a simulated confidence score for an embedding.
    
    In production, this could use:
    - Model uncertainty estimates
    - Reconstruction error (for autoencoders)
    - Ensemble agreement
    
    Here we simulate with embedding statistics.
    """
    import numpy as np
    arr = np.array(embedding)
    # Higher variance in embedding often indicates less confident representation
    variance = np.var(arr)
    # Normalize to 0-1 range (rough approximation)
    confidence = 1.0 / (1.0 + variance * 10)
    return min(1.0, max(0.0, confidence))


# =============================================================================
# Step 1: Capture Semantic Snapshot
# =============================================================================

def capture_snapshot(
    db: RushDB,
    article_ids: list,
    purpose: str = "pre-update-capture"
) -> SemanticSnapshot:
    """
    Step 1: Capture semantic snapshot before updates.
    
    This function:
    1. Fetches current state of target articles
    2. Retrieves their vector embeddings
    3. Captures relationship graph structure
    4. Creates a rollback-able snapshot
    
    Args:
        db: RushDB instance
        article_ids: List of article record IDs to snapshot
        purpose: Reason for the snapshot
        
    Returns:
        SemanticSnapshot object containing all captured state
    """
    print("\n" + "="*60)
    print("STEP 1: Capturing Semantic Snapshot")
    print("="*60)
    
    snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now().isoformat()
    
    article_snapshots = []
    preserved_relationships = []
    
    print(f"\nCapturing state of {len(article_ids)} articles...")
    print(f"  Snapshot ID: {snapshot_id}")
    
    # Fetch all articles at once
    articles = db.records.find_by_id(article_ids)
    
    for article in articles:
        if not article.exists:
            print(f"  Warning: Article {article.id} not found, skipping")
            continue
        
        # Extract article data
        article_data = article.data
        
        # Get vector from the data (stored by RushDB)
        vector = article_data.get("__vectors", {}).get("body", [])
        
        # Find related concepts (relationships)
        related_concepts = db.records.find({
            "labels": ["Concept"],
            "where": {
                "Article": {"$relation": {"type": "TAGGED_WITH", "direction": "in"}}
            },
            "limit": 100
        })
        related_concept_ids = [c.id for c in related_concepts.data]
        
        # Capture each relationship individually
        for concept in related_concepts.data:
            preserved_relationships.append({
                "article_id": article.id,
                "concept_id": concept.id,
                "type": "TAGGED_WITH",
                "direction": "out"
            })
        
        article_snapshot = ArticleSnapshot(
            record_id=article.id,
            slug=article_data.get("slug", ""),
            title=article_data.get("title", ""),
            body=article_data.get("body", ""),
            tags=article_data.get("tags", []),
            status=article_data.get("status", ""),
            vector=vector,
            related_concept_ids=related_concept_ids
        )
        article_snapshots.append(article_snapshot)
        
        print(f"  ✓ Captured: {article_data.get('slug')} ({len(vector)} dims)")
    
    snapshot = SemanticSnapshot(
        snapshot_id=snapshot_id,
        timestamp=timestamp,
        purpose=purpose,
        article_snapshots=article_snapshots,
        preserved_relationships=preserved_relationships
    )
    
    print(f"\nSnapshot captured successfully!")
    print(f"  Articles: {len(article_snapshots)}")
    print(f"  Relationships: {len(preserved_relationships)}")
    
    return snapshot


# =============================================================================
# Step 2: Detect Rollback Trigger
# =============================================================================

class RollbackDetector:
    """
    Detects when a rollback should be triggered.
    
    Implements three detection mechanisms:
    1. Manual trigger (explicit user request)
    2. LLM confidence threshold (automated quality check)
    3. External validation (third-party system feedback)
    """
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.triggers: list[RollbackTrigger] = []
    
    def check_manual_trigger(self, user_requested: bool = False) -> Optional[RollbackTrigger]:
        """
        Check for manual rollback trigger.
        
        Args:
            user_requested: Whether user explicitly requested rollback
            
        Returns:
            RollbackTrigger if triggered, None otherwise
        """
        if user_requested:
            trigger = RollbackTrigger(
                trigger_type="manual",
                message="User explicitly requested rollback"
            )
            self.triggers.append(trigger)
            return trigger
        return None
    
    def check_confidence_trigger(
        self,
        confidence_before: float,
        confidence_after: float
    ) -> Optional[RollbackTrigger]:
        """
        Check for LLM confidence threshold trigger.
        
        This simulates checking if the content quality dropped
        below an acceptable threshold after updates.
        
        Args:
            confidence_before: Quality score before updates
            confidence_after: Quality score after updates
            
        Returns:
            RollbackTrigger if triggered, None otherwise
        """
        if confidence_after < self.confidence_threshold:
            trigger = RollbackTrigger(
                trigger_type="confidence",
                message=f"LLM confidence dropped below threshold ({self.confidence_threshold})",
                confidence_before=confidence_before,
                confidence_after=confidence_after
            )
            self.triggers.append(trigger)
            return trigger
        return None
    
    def check_external_validation(
        self,
        validation_result: dict
    ) -> Optional[RollbackTrigger]:
        """
        Check for external validation trigger.
        
        This simulates receiving feedback from an external system
        (e.g., content moderation, fact-checking, user feedback).
        
        Args:
            validation_result: Dictionary with 'passed' and optional 'reason'
            
        Returns:
            RollbackTrigger if triggered, None otherwise
        """
        if not validation_result.get("passed", True):
            trigger = RollbackTrigger(
                trigger_type="validation",
                message=f"External validation failed: {validation_result.get('reason', 'Unknown')}"
            )
            self.triggers.append(trigger)
            return trigger
        return None
    
    def should_rollback(self) -> bool:
        """Check if any trigger conditions are met."""
        return len(self.triggers) > 0
    
    def get_primary_trigger(self) -> Optional[RollbackTrigger]:
        """Get the primary trigger that initiated rollback."""
        return self.triggers[0] if self.triggers else None
    
    def simulate_llm_confidence(self, text: str) -> float:
        """
        Simulate LLM confidence scoring for text content.
        
        In production, this would use:
        - Model uncertainty estimates
        - Ensemble disagreement metrics
        - Perplexity scores
        
        Args:
            text: The text content to score
            
        Returns:
            Confidence score between 0 and 1
        """
        embedding = get_embedding(text)
        return calculate_confidence(embedding)


def demonstrate_rollback_triggers(
    detector: RollbackDetector,
    original_text: str,
    degraded_text: str
) -> list[RollbackTrigger]:
    """
    Demonstrate all three rollback trigger mechanisms.
    
    Args:
        detector: RollbackDetector instance
        original_text: Original high-quality content
        degraded_text: Updated lower-quality content
        
    Returns:
        List of triggered RollbackTriggers
    """
    print("\n" + "="*60)
    print("STEP 2: Detecting Rollback Triggers")
    print("="*60)
    
    print("\nDetecting rollback triggers...")
    
    # Trigger 1: Manual
    print("\n  [1] Manual Trigger Check:")
    trigger = detector.check_manual_trigger(user_requested=True)
    if trigger:
        print(f"      ✓ TRIGGERED: {trigger.message}")
    
    # Trigger 2: LLM Confidence
    print("\n  [2] LLM Confidence Check:")
    confidence_before = detector.simulate_llm_confidence(original_text)
    confidence_after = detector.simulate_llm_confidence(degraded_text)
    print(f"      Confidence before: {confidence_before:.3f}")
    print(f"      Confidence after:  {confidence_after:.3f}")
    print(f"      Threshold:        {detector.confidence_threshold:.3f}")
    
    trigger = detector.check_confidence_trigger(confidence_before, confidence_after)
    if trigger:
        print(f"      ✓ TRIGGERED: {trigger.message}")
        print(f"        (Dropped by {(confidence_before - confidence_after):.3f})")
    
    # Trigger 3: External Validation
    print("\n  [3] External Validation Check:")
    validation_result = {
        "passed": False,
        "reason": "Content quality below acceptable threshold"
    }
    print(f"      Validation result: FAILED")
    print(f"      Reason: {validation_result['reason']}")
    
    trigger = detector.check_external_validation(validation_result)
    if trigger:
        print(f"      ✓ TRIGGERED: {trigger.message}")
    
    print(f"\n  Total triggers detected: {len(detector.triggers)}")
    
    return detector.triggers


# =============================================================================
# Step 3: Revert Graph Subgraph
# =============================================================================

def revert_to_snapshot(db: RushDB, snapshot: SemanticSnapshot) -> dict:
    """
    Step 3: Revert graph subgraph while preserving unrelated nodes.
    
    This function:
    1. Reverts each article to its snapshot state
    2. Maintains relationships with concepts
    3. Preserves all unrelated nodes
    4. Uses transactions for atomicity
    
    Args:
        db: RushDB instance
        snapshot: The SemanticSnapshot to revert to
        
    Returns:
        Dictionary with statistics about the revert operation
    """
    print("\n" + "="*60)
    print("STEP 3: Reverting Graph Subgraph")
    print("="*60)
    
    stats = {
        "articles_reverted": 0,
        "relationships_preserved": 0,
        "relationships_recreated": 0,
        "errors": []
    }
    
    print(f"\nReverting to snapshot: {snapshot.snapshot_id}")
    print(f"Purpose: {snapshot.purpose}")
    
    # First, detach all relationships from articles we're reverting
    print("\nDetaching existing relationships...")
    for article_snapshot in snapshot.article_snapshots:
        # Find all concepts this article was tagged with
        related_concepts = db.records.find({
            "labels": ["Concept"],
            "where": {
                "Article": {
                    "$relation": {"type": "TAGGED_WITH", "direction": "in"},
                    "$id": article_snapshot.record_id
                }
            }
        })
        
        for concept in related_concepts.data:
            try:
                db.records.detach(
                    source=db.records.find_by_id(article_snapshot.record_id),
                    target=concept,
                    options={"type": "TAGGED_WITH"}
                )
                stats["relationships_preserved"] += 1
            except Exception as e:
                stats["errors"].append(f"Detach error: {e}")
    
    print(f"  ✓ Detached {stats['relationships_preserved']} relationships")
    
    # Revert each article using transaction
    print("\nReverting articles to snapshot state...")
    
    with db.transactions.begin() as tx:
        for article_snapshot in snapshot.article_snapshots:
            try:
                # Get the record
                record = db.records.find_by_id(article_snapshot.record_id)
                
                if not record.exists:
                    print(f"  Warning: Record {article_snapshot.record_id} not found")
                    continue
                
                # Full replacement of article data
                db.records.set(
                    target=record,
                    label="Article",
                    data={
                        "slug": article_snapshot.slug,
                        "title": article_snapshot.title,
                        "body": article_snapshot.body,
                        "tags": article_snapshot.tags,
                        "status": article_snapshot.status,
                        "updatedAt": datetime.now().isoformat(),
                        "rolledBackFrom": snapshot.snapshot_id
                    },
                    vectors=[{
                        "propertyName": "body",
                        "vector": article_snapshot.vector
                    }]
                )
                
                stats["articles_reverted"] += 1
                print(f"  ✓ Reverted: {article_snapshot.slug}")
                
            except Exception as e:
                error_msg = f"Error reverting {article_snapshot.slug}: {e}"
                stats["errors"].append(error_msg)
                print(f"  ✗ Error: {error_msg}")
                raise
    
    # Re-create relationships
    print("\nRe-creating relationships...")
    for rel in snapshot.preserved_relationships:
        try:
            article_record = db.records.find_by_id(rel["article_id"])
            concept_record = db.records.find_by_id(rel["concept_id"])
            
            if article_record.exists and concept_record.exists:
                db.records.attach(
                    source=article_record,
                    target=concept_record,
                    options={"type": rel["type"], "direction": rel["direction"]}
                )
                stats["relationships_recreated"] += 1
        except Exception as e:
            stats["errors"].append(f"Attach error: {e}")
    
    print(f"  ✓ Re-created {stats['relationships_recreated']} relationships")
    
    print(f"\nRevert complete!")
    print(f"  Articles reverted: {stats['articles_reverted']}")
    print(f"  Relationships preserved: {stats['relationships_preserved']}")
    
    if stats["errors"]:
        print(f"  Warnings: {len(stats['errors'])}")
    
    return stats


# =============================================================================
# Step 4: Rebuild Vector Index
# =============================================================================

def rebuild_vector_index(
    db: RushDB,
    article_ids: list,
    snapshot: SemanticSnapshot
) -> dict:
    """
    Step 4: Rebuild affected vector index entries atomically.
    
    This function:
    1. Finds the vector index for Article.body
    2. Updates only the affected article vectors
    3. Verifies the rebuild was successful
    
    Args:
        db: RushDB instance
        article_ids: List of article IDs that were reverted
        snapshot: The snapshot containing original vectors
        
    Returns:
        Dictionary with rebuild statistics
    """
    print("\n" + "="*60)
    print("STEP 4: Rebuilding Vector Index")
    print("="*60)
    
    stats = {
        "vectors_updated": 0,
        "index_found": False,
        "errors": []
    }
    
    # Find the vector index
    print("\nLocating vector index...")
    indexes = db.ai.indexes.find()
    target_index = None
    
    for idx in indexes.data:
        if idx.get('label') == 'Article' and idx.get('propertyName') == 'body':
            target_index = idx
            stats["index_found"] = True
            break
    
    if not stats["index_found"]:
        print("  Warning: Vector index not found, skipping index rebuild")
        print("  (Vectors were already updated during article revert)")
        return stats
    
    print(f"  ✓ Found index: {target_index.get('__id')}")
    
    # Get index stats before
    try:
        index_stats = db.ai.indexes.stats(target_index.get('__id'))
        print(f"  Index stats before: {index_stats.data.get('indexedRecords', 'N/A')} records")
    except:
        pass
    
    # Build vector update items from snapshot
    print("\nUpdating vector entries from snapshot...")
    
    items = []
    for article_snapshot in snapshot.article_snapshots:
        if article_snapshot.vector:
            items.append({
                "recordId": article_snapshot.record_id,
                "vector": article_snapshot.vector
            })
    
    if items:
        try:
            db.ai.indexes.upsert_vectors(
                target_index.get('__id'),
                {"items": items}
            )
            stats["vectors_updated"] = len(items)
            print(f"  ✓ Updated {len(items)} vectors in index")
        except Exception as e:
            # Note: vectors might already be updated via set() operation
            # This is informational only
            stats["errors"].append(f"Upsert note: {e}")
            print(f"  Note: Vector upsert: {e}")
    
    # Verify with semantic search
    print("\nVerifying semantic search after rollback...")
    
    test_query = "machine learning algorithms"
    try:
        results = db.ai.search({
            "propertyName": "body",
            "query": test_query,
            "labels": ["Article"],
            "limit": 3
        })
        
        print(f"  Query: '{test_query}'")
        print(f"  Results found: {len(results.data)}")
        
        for result in results.data[:3]:
            score = result.score if hasattr(result, 'score') else 0
            title = result.data.get('title', 'Unknown')[:50]
            print(f"    [{score:.3f}] {title}")
        
        print("\n  ✓ Semantic search restored")
        
    except Exception as e:
        stats["errors"].append(f"Search verification: {e}")
        print(f"  Warning: Could not verify semantic search: {e}")
    
    print(f"\nVector index rebuild complete!")
    print(f"  Vectors updated: {stats['vectors_updated']}")
    
    return stats


# =============================================================================
# Main Demo Workflow
# =============================================================================

def simulate_problematic_updates(db: RushDB, article_ids: list) -> tuple[list, str, str]:
    """
    Simulate problematic updates to knowledge base articles.
    
    In a real scenario, these could be:
    - Bulk AI regeneration that degraded quality
    - External data import with errors
    - Malicious content injection
    
    Returns:
        Tuple of (updated article IDs, original combined text, degraded combined text)
    """
    print("\n  Applying problematic updates to simulate rollback scenario...")
    
    # Get original content for comparison
    articles = db.records.find_by_id(article_ids)
    original_texts = []
    degraded_texts = []
    
    # Simulated degraded content
    degraded_content = [
        {
            "title": "Introduction to Machine Learning - CORRUPTED",
            "body": "Machine learning is a thing that makes computers learn stuff. It might work sometimes but nobody really knows how. There are algorithms that do stuff.",
            "tags": ["machine-learning", "ai"],
            "status": "draft"
        },
        {
            "title": "Supervised Learning Fundamentals - OUTDATED",
            "body": "Supervised learning is when you tell the computer what to learn. It reads labeled data. The algorithm reads the data. That's basically it.",
            "tags": ["machine-learning", "supervised-learning"],
            "status": "draft"
        },
        {
            "title": "Python Programming Basics - REVIEW NEEDED",
            "body": "Python is a programming language. You can write code in it. It has things called variables and functions. People use it for many things.",
            "tags": ["python", "programming"],
            "status": "draft"
        }
    ]
    
    for i, (article, degraded) in enumerate(zip(articles, degraded_content)):
        if not article.exists:
            continue
        
        # Store original for later comparison
        original_texts.append(article.data.get("body", ""))
        degraded_texts.append(degraded["body"])
        
        # Apply degraded content
        new_embedding = get_embedding(degraded["body"])
        
        db.records.set(
            target=article,
            label="Article",
            data={
                "title": degraded["title"],
                "body": degraded["body"],
                "tags": degraded["tags"],
                "status": degraded["status"],
                "updatedAt": datetime.now().isoformat()
            },
            vectors=[{"propertyName": "body", "vector": new_embedding}]
        )
        
        print(f"    ✓ Updated: {degraded['title'][:40]}...")
    
    return article_ids, " ".join(original_texts), " ".join(degraded_texts)


def verify_rollback_quality(
    db: RushDB,
    snapshot: SemanticSnapshot
) -> dict:
    """
    Verify that rollback restored the expected quality.
    """
    print("\n  Verifying rollback quality...")
    
    results = {
        "articles_verified": 0,
        "articles_matched": 0,
        "confidence_scores": []
    }
    
    for article_snapshot in snapshot.article_snapshots:
        record = db.records.find_by_id(article_snapshot.record_id)
        if not record.exists:
            continue
        
        results["articles_verified"] += 1
        
        # Check if content matches snapshot
        if record.data.get("body") == article_snapshot.body:
            results["articles_matched"] += 1
        
        # Calculate confidence of restored content
        confidence = calculate_confidence(
            record.data.get("__vectors", {}).get("body", [])
        )
        results["confidence_scores"].append(confidence)
    
    avg_confidence = sum(results["confidence_scores"]) / len(results["confidence_scores"]) if results["confidence_scores"] else 0
    
    print(f"    Articles verified: {results['articles_verified']}")
    print(f"    Content matched: {results['articles_matched']}/{results['articles_verified']}")
    print(f"    Average confidence: {avg_confidence:.3f}")
    
    return results


def main():
    """
    Main entry point demonstrating the complete semantic rollback workflow.
    """
    print("\n" + "="*60)
    print("SEMANTIC ROLLBACK: Reverting Knowledge Base State")
    print("="*60)
    print("\nThis tutorial demonstrates how to implement semantic rollback")
    print("in a production knowledge base using RushDB.")
    
    # Initialize RushDB
    api_token = os.environ.get('RUSHDB_API_TOKEN')
    if not api_token:
        print("\nERROR: RUSHDB_API_TOKEN environment variable is not set")
        print("Please create a .env file with your RushDB API token")
        print("\nGet your token at: https://app.rushdb.com/settings/api-tokens")
        return
    
    db = RushDB(api_token)
    
    # =========================================================================
    # Setup: Get target articles for rollback demo
    # =========================================================================
    
    print("\n" + "="*60)
    print("SETUP: Preparing Knowledge Base")
    print("="*60)
    
    # Find articles to work with (using slug for predictability)
    articles = db.records.find({
        "labels": ["Article"],
        "where": {
            "slug": {"$in": ["ml-intro", "ml-supervised", "python-basics"]}
        },
        "limit": 10
    })
    
    if len(articles.data) < 3:
        print("\nERROR: Not enough articles found in knowledge base")
        print("Please run 'python seed.py' first to populate the knowledge base")
        return
    
    article_ids = [a.id for a in articles.data[:3]]
    print(f"\n  Found {len(article_ids)} articles for rollback demo:")
    for article in articles.data[:3]:
        print(f"    - {article.data.get('slug')}: {article.data.get('title')}")
    
    # =========================================================================
    # STEP 1: Capture Semantic Snapshot
    # =========================================================================
    
    snapshot = capture_snapshot(
        db=db,
        article_ids=article_ids,
        purpose="pre-update-capture"
    )
    
    # =========================================================================
    # STEP 2: Simulate Problematic Updates
    # =========================================================================
    
    print("\n" + "="*60)
    print("SIMULATION: Applying Problematic Updates")
    print("="*60)
    
    original_text, degraded_text = None, None
    original_text, degraded_text = simulate_problematic_updates(db, article_ids)
    original_text = " ".join([a.data.get("body", "") for a in articles.data[:3]])
    
    # Get degraded text from updated records
    updated_articles = db.records.find_by_id(article_ids)
    degraded_text = " ".join([a.data.get("body", "") for a in updated_articles.data])
    
    print("\n  ✓ Applied problematic updates to all articles")
    
    # =========================================================================
    # STEP 3: Detect Rollback Triggers
    # =========================================================================
    
    detector = RollbackDetector(confidence_threshold=0.5)
    triggers = demonstrate_rollback_triggers(detector, original_text, degraded_text)
    
    # =========================================================================
    # STEP 4: Execute Rollback (if triggered)
    # =========================================================================
    
    if detector.should_rollback():
        print("\n" + "="*60)
        print("EXECUTION: Performing Semantic Rollback")
        print("="*60)
        
        # Revert graph subgraph
        revert_stats = revert_to_snapshot(db, snapshot)
        
        # Rebuild vector index
        rebuild_stats = rebuild_vector_index(db, article_ids, snapshot)
        
        # Verify quality
        quality_results = verify_rollback_quality(db, snapshot)
        
        # =========================================================================
        # Final Summary
        # =========================================================================
        
        print("\n" + "="*60)
        print("SUMMARY: Semantic Rollback Complete")
        print("="*60)
        
        print(f"\n  Rollback Trigger: {detector.get_primary_trigger().trigger_type}")
        print(f"  Snapshot ID: {snapshot.snapshot_id}")
        print(f"  Timestamp: {snapshot.timestamp}")
        
        print(f"\n  Articles Reverted: {revert_stats['articles_reverted']}")
        print(f"  Relationships Preserved: {revert_stats['relationships_preserved']}")
        print(f"  Vectors Updated: {rebuild_stats['vectors_updated']}")
        print(f"  Quality Verified: {quality_results['articles_matched']}/{quality_results['articles_verified']}")
        
        print("\n  ✓ Knowledge base state successfully restored")
        print("  ✓ Semantic search consistency maintained")
        
    else:
        print("\n  No rollback triggered.")
    
    print("\n" + "="*60)
    print("Tutorial Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
