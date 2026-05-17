#!/usr/bin/env python3
"""
RushDB Property Types Tutorial: Modeling Agent Belief States

This script demonstrates how to use RushDB's property type system
to model agent belief states in AI systems.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError(
        "RUSHDB_API_KEY not found in environment. "
        "Copy .env.example to .env and add your API key."
    )

db = RushDB(api_key)


def section_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def demo_create_belief():
    """Demonstrate creating a belief record with all property types."""
    section_header("1. Creating Belief Records with All Property Types")
    
    # String property - semantic content
    content = "Agent should prioritize security review"
    
    # Number property - confidence score (0.0 to 1.0)
    confidence = 0.78
    
    # String property - categorical status
    status = "hypothesis"
    
    # Boolean property - binary state
    is_active = True
    
    # Array property - multi-valued tags
    tags = ["security", "priority", "review", "agent_task"]
    
    # Object property - structured metadata
    metadata = {
        "source": "security_scanner",
        "timestamp": "2024-01-25T09:15:00Z",
        "evidence_count": 7,
        "origin_agent": "security_analyzer",
        "risk_level": "high",
        "related_issues": ["CVE-2024-1234", "CVE-2024-5678"]
    }
    
    # Create the belief record with all property types
    belief = db.records.create(
        label="BELIEF",
        data={
            "content": content,
            "confidence": confidence,
            "status": status,
            "is_active": is_active,
            "tags": tags,
            "metadata": metadata
        }
    )
    
    print(f"\n✓ Created BELIEF record")
    print(f"  ID: {belief.id}")
    print(f"  content: {belief['content']}")
    print(f"  confidence: {belief['confidence']}")
    print(f"  status: {belief['status']}")
    print(f"  is_active: {belief['is_active']}")
    print(f"  tags: {belief['tags']}")
    print(f"  metadata: {belief['metadata']}")
    
    return belief


def demo_query_by_number():
    """Demonstrate querying beliefs by number properties."""
    section_header("2. Querying by Number Property (Confidence Threshold)")
    
    # Find all beliefs with confidence >= 0.8
    high_confidence = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "confidence": {"$gte": 0.8}
        }
    })
    
    print(f"\nFound {high_confidence.total} beliefs with confidence >= 0.8:")
    for belief in high_confidence.data[:5]:  # Show first 5
        print(f"  • {belief['content'][:50]}... (confidence: {belief['confidence']})")
    
    # Find beliefs with confidence in a specific range
    medium_confidence = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "confidence": {"$gte": 0.5, "$lte": 0.75}
        }
    })
    
    print(f"\nFound {medium_confidence.total} beliefs with confidence between 0.5 and 0.75:")
    for belief in medium_confidence.data[:5]:
        print(f"  • {belief['content'][:50]}... (confidence: {belief['confidence']})")


def demo_query_by_boolean():
    """Demonstrate querying beliefs by boolean properties."""
    section_header("3. Querying by Boolean Property (Active/Inactive)")
    
    # Find all active beliefs
    active_beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "is_active": True
        }
    })
    
    print(f"\nFound {active_beliefs.total} active beliefs:")
    for belief in active_beliefs.data[:5]:
        print(f"  • {belief['content'][:50]}... (status: {belief['status']})")
    
    # Find all inactive beliefs
    inactive_beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "is_active": False
        }
    })
    
    print(f"\nFound {inactive_beliefs.total} inactive beliefs:")
    for belief in inactive_beliefs.data:
        print(f"  • {belief['content'][:50]}... (status: {belief['status']})")


def demo_query_by_string():
    """Demonstrate querying beliefs by string properties."""
    section_header("4. Querying by String Property (Status Filter)")
    
    # Find beliefs by status
    for status in ["confirmed", "hypothesis", "doubt"]:
        beliefs = db.records.find({
            "labels": ["BELIEF"],
            "where": {
                "status": status
            }
        })
        print(f"\nStatus '{status}': {beliefs.total} belief(s)")
        for belief in beliefs.data[:3]:
            print(f"  • {belief['content'][:50]}... (confidence: {belief['confidence']})")
    
    # Find beliefs by partial string match
    security_beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "content": {"$contains": "security"}
        }
    })
    
    print(f"\nContent containing 'security': {security_beliefs.total} belief(s)")
    for belief in security_beliefs.data:
        print(f"  • {belief['content'][:60]}...")


def demo_query_by_array():
    """Demonstrate querying beliefs by array properties."""
    section_header("5. Querying by Array Property (Tag Filtering)")
    
    # Find beliefs containing a specific tag
    performance_beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "tags": {"$contains": "performance"}
        }
    })
    
    print(f"\nBeliefs tagged with 'performance': {performance_beliefs.total}")
    for belief in performance_beliefs.data:
        print(f"  • {belief['content'][:50]}...")
        print(f"    Tags: {belief['tags']}")
    
    # Find beliefs containing multiple tags (AND logic)
    important_beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "tags": {"$contains": "priority"},
            "confidence": {"$gte": 0.7}
        }
    })
    
    print(f"\nBeliefs with 'priority' tag AND confidence >= 0.7: {important_beliefs.total}")
    for belief in important_beliefs.data:
        print(f"  • {belief['content'][:50]}... (confidence: {belief['confidence']})")


def demo_query_by_object():
    """Demonstrate querying by object property metadata."""
    section_header("6. Querying by Object Property (Nested Metadata)")
    
    # We can query object properties directly
    high_evidence = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "metadata": {
                "evidence_count": {"$gte": 5}
            }
        }
    })
    
    print(f"\nBeliefs with evidence_count >= 5: {high_evidence.total}")
    for belief in high_evidence.data:
        meta = belief.get("metadata", {})
        print(f"  • {belief['content'][:50]}...")
        print(f"    Evidence count: {meta.get('evidence_count', 'N/A')}")
        print(f"    Source: {meta.get('source', 'N/A')}")


def demo_update_with_transaction():
    """Demonstrate updating beliefs atomically using transactions."""
    section_header("7. Atomic Updates with Transactions")
    
    # Find a belief to update
    beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "status": "hypothesis",
            "is_active": True
        },
        "limit": 1
    })
    
    if beliefs.total == 0:
        print("\nNo hypothesis beliefs found to update.")
        return
    
    belief = beliefs.data[0]
    old_confidence = belief['confidence']
    
    print(f"\nUpdating belief: {belief['content'][:50]}...")
    print(f"  Current confidence: {old_confidence}")
    
    # Use transaction for atomic update
    with db.transactions.begin() as tx:
        # Update confidence based on new evidence
        new_confidence = min(1.0, old_confidence + 0.1)
        belief.update({
            "confidence": new_confidence,
            "status": "confirmed" if new_confidence >= 0.9 else "hypothesis"
        }, transaction=tx)
        
        # Add verification metadata
        current_meta = belief.get("metadata", {})
        current_meta["last_verified"] = "2024-01-25T12:00:00Z"
        current_meta["verification_count"] = current_meta.get("evidence_count", 0) + 1
        belief.update({"metadata": current_meta}, transaction=tx)
        # No explicit commit - context manager handles it
    
    print(f"  New confidence: {new_confidence}")
    print(f"  New status: {'confirmed' if new_confidence >= 0.9 else 'hypothesis'}")
    print("\n✓ Transaction committed successfully")
    
    # Verify the update
    updated_belief = db.records.findById(belief.id)
    print(f"\nVerified update:")
    print(f"  confidence: {updated_belief['confidence']}")
    print(f"  metadata.last_verified: {updated_belief['metadata'].get('last_verified')}")


def demo_combined_queries():
    """Demonstrate complex queries combining multiple property types."""
    section_header("8. Combined Property Type Queries")
    
    # Complex query: active confirmed beliefs with high confidence and specific tags
    complex_beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "is_active": True,
            "status": "confirmed",
            "confidence": {"$gte": 0.7},
            "tags": {"$contains": "security"}
        }
    })
    
    print(f"\nActive confirmed beliefs with confidence >= 0.7 AND 'security' tag:")
    print(f"  Found {complex_beliefs.total} matching belief(s)")
    
    for belief in complex_beliefs.data:
        print(f"\n  • {belief['content']}")
        print(f"    Confidence: {belief['confidence']}")
        print(f"    Status: {belief['status']}")
        print(f"    Tags: {belief['tags']}")
    
    # Query with OR conditions using $or
    mixed_beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "$or": [
                {"confidence": {"$gte": 0.9}},
                {"status": "confirmed", "is_active": True}
            ]
        }
    })
    
    print(f"\nBeliefs with confidence >= 0.9 OR (confirmed AND active):")
    print(f"  Found {mixed_beliefs.total} matching belief(s)")


def demo_property_inspection():
    """Demonstrate inspecting the property types in the schema."""
    section_header("9. Inspecting Property Types (Ontology)")
    
    # Get the ontology to see property types
    try:
        ontology = db.ai.getOntology()
        print("\nRushDB Schema (Property Types):")
        print(json.dumps(ontology, indent=2)[:500] + "...")
    except Exception as e:
        print(f"\nOntology inspection: {e}")
    
    # List all properties
    properties = db.properties.find({"limit": 20})
    print(f"\nFirst 20 properties in the database:")
    for prop in properties.data[:20]:
        print(f"  • {prop.name} (type: {getattr(prop, 'type', 'unknown')})")


def demo_cleanup():
    """Show how to clean up belief records."""
    section_header("10. Cleaning Up Records")
    
    # Count current beliefs
    all_beliefs = db.records.find({"labels": ["BELIEF"]})
    print(f"\nCurrent BELIEF records: {all_beliefs.total}")
    
    # Demonstrate delete by condition
    # (In production, you'd be more selective - this is for tutorial purposes)
    low_confidence = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "confidence": {"$lt": 0.3}
        }
    })
    
    print(f"Low confidence beliefs (< 0.3): {low_confidence.total}")
    
    if low_confidence.total > 0:
        print("\n  Note: Not deleting low confidence beliefs in tutorial mode.")
        print("  To delete, uncomment the following line in the code:")
        print("  db.records.delete_many({'labels': ['BELIEF'], 'where': {'confidence': {'$lt': 0.3}}})")


def main():
    """Run all demonstrations."""
    print("\n" + "="*60)
    print(" RushDB Property Types Tutorial")
    print(" Modeling Agent Belief States")
    print("="*60)
    
    # First, ensure we have data to work with
    existing = db.records.find({"labels": ["BELIEF"], "limit": 1})
    
    if existing.total == 0:
        print("\nNo belief records found. Running seed script first...")
        import subprocess
        subprocess.run(["python", "seed.py"])
        print("\nSeed complete. Running demonstrations...\n")
    
    # Run all demonstrations
    demo_create_belief()
    demo_query_by_number()
    demo_query_by_boolean()
    demo_query_by_string()
    demo_query_by_array()
    demo_query_by_object()
    demo_update_with_transaction()
    demo_combined_queries()
    demo_property_inspection()
    demo_cleanup()
    
    print("\n" + "="*60)
    print(" Tutorial Complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Experiment with different property type combinations")
    print("  2. Try the TypeScript SDK for similar patterns in JS/TS")
    print("  3. Check out docs.rushdb.com for advanced features")
    print()


if __name__ == "__main__":
    main()
