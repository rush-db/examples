"""
Feedback-Annotated Knowledge Store - Main Demo

This script demonstrates a complete human-in-the-loop workflow for managing
knowledge entries with human corrections and feedback.

It showcases:
1. Querying pending feedback requiring attention
2. Applying corrections to knowledge entries
3. Finding entries with quality issues (many feedback items)
4. Analyzing feedback patterns by type and status
5. A complete workflow: submit review → apply correction → verify
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
api_token = os.getenv("RUSHDB_API_TOKEN")
if not api_token:
    print("ERROR: RUSHDB_API_TOKEN not found in environment")
    print("Please copy .env.example to .env and add your token")
    exit(1)

db = RushDB(api_token)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_find_pending_feedback():
    """Demonstrate finding feedback that needs attention."""
    print_section("1️⃣  PENDING FEEDBACK REQUIRING ATTENTION")
    
    pending = db.records.find({
        "labels": ["FEEDBACK"],
        "where": {"status": "pending"},
        "orderBy": {"submitted_at": "desc"}
    })
    
    if not pending.data:
        print("\nNo pending feedback found. Run `python seed.py` first!")
        return None
    
    print(f"\nFound {len(pending.data)} pending feedback items:")
    
    for i, fb in enumerate(pending.data[:5], 1):  # Show first 5
        print(f"\n  [{i}] {fb.data.get('type', 'unknown').upper()}")
        print(f"      Severity: {fb.data.get('severity', 'N/A')}")
        print(f"      Reviewer: {fb.data.get('reviewer', 'Anonymous')}")
        print(f"      Submitted: {fb.data.get('submitted_at', 'Unknown')}")
        print(f"      Description: {fb.data.get('description', 'No description')[:80]}...")
    
    if len(pending.data) > 5:
        print(f"\n  ... and {len(pending.data) - 5} more items")
    
    return pending.data[0] if pending.data else None


def demo_find_entries_with_feedback():
    """Demonstrate finding knowledge entries that have feedback."""
    print_section("2️⃣  KNOWLEDGE ENTRIES WITH FEEDBACK")
    
    # Find all knowledge entries that have feedback attached
    entries_with_feedback = db.records.find({
        "labels": ["KNOWLEDGE_ENTRY"],
        "where": {
            "FEEDBACK": {"$exists": True}
        }
    })
    
    print(f"\nFound {len(entries_with_feedback.data)} entries with feedback:")
    
    for entry in entries_with_feedback.data[:5]:
        # Count feedback for this entry
        feedback_count = len(entry.data.get("FEEDBACK", [])) if "FEEDBACK" in entry.data else "?"
        print(f"\n  📄 {entry.data.get('title', 'Untitled')}")
        print(f"     Topic: {entry.data.get('topic', 'Unknown')}")
        print(f"     Feedback count: {feedback_count}")
        print(f"     Version: {entry.data.get('version', 1)}")


def demo_apply_correction():
    """Demonstrate applying a correction to a knowledge entry."""
    print_section("3️⃣  APPLYING A CORRECTION")
    
    # Get a pending feedback item
    pending = db.records.find({
        "labels": ["FEEDBACK"],
        "where": {"status": "pending", "severity": "high"},
        "limit": 1
    })
    
    if not pending.data:
        print("\nNo high-severity pending feedback found.")
        return
    
    feedback = pending.data[0]
    print(f"\nSelected feedback: {feedback.data.get('description', '')[:60]}...")
    
    # Get the related knowledge entry
    # Note: In a real scenario, we'd traverse the relationship
    # For demo, let's find an entry to update
    entries = db.records.find({"labels": ["KNOWLEDGE_ENTRY"], "limit": 3})
    
    if not entries.data:
        print("No knowledge entries found to update.")
        return
    
    entry_to_update = entries.data[0]
    print(f"\nApplying correction to: {entry_to_update.data.get('title')}")
    
    # Create a correction record
    correction = db.records.create(
        label="CORRECTION",
        data={
            "original_content": entry_to_update.data.get("content", "")[:100],
            "correction_description": feedback.data.get("description", ""),
            "feedback_id": feedback.id,
            "applied_at": datetime.now().isoformat(),
            "status": "applied"
        }
    )
    print(f"\n  ✅ Created correction record: {correction.id[:20]}...")
    
    # Update the knowledge entry
    updated_entry = db.records.update(
        record_id=entry_to_update.id,
        data={
            "updated_at": datetime.now().isoformat(),
            "version": entry_to_update.data.get("version", 1) + 1,
            "last_correction": correction.id,
            "correction_summary": f"Applied {feedback.data.get('type', 'correction')}: {feedback.data.get('description', '')[:50]}..."
        }
    )
    print(f"  ✅ Updated knowledge entry to version {updated_entry.data.get('version')}")
    
    # Update the feedback status
    db.records.update(
        record_id=feedback.id,
        data={
            "status": "applied",
            "reviewed_at": datetime.now().isoformat()
        }
    )
    print(f"  ✅ Marked feedback as 'applied'")


def demo_find_quality_issues():
    """Demonstrate finding entries with many feedback items (quality issues)."""
    print_section("4️⃣  KNOWLEDGE QUALITY ANALYSIS")
    
    # Get all entries
    all_entries = db.records.find({"labels": ["KNOWLEDGE_ENTRY"]})
    
    # For each entry, count feedback
    entry_feedback_counts = []
    
    for entry in all_entries.data:
        feedback = db.records.find({
            "labels": ["FEEDBACK"],
            "where": {
                "status": {"$in": ["pending", "reviewed"]}
            }
        })
        # In a real implementation, we'd filter by related records
        # For demo, we simulate by random assignment
        pending_count = len([f for f in feedback.data if f.data.get("status") in ["pending", "reviewed"]])
        entry_feedback_counts.append({
            "entry": entry,
            "pending_count": pending_count
        })
    
    # Sort by pending feedback count (simulating actual count)
    entry_feedback_counts.sort(key=lambda x: x["pending_count"], reverse=True)
    
    print(f"\nTop entries needing attention:")
    for i, item in enumerate(entry_feedback_counts[:3], 1):
        entry = item["entry"]
        count = item["pending_count"]
        print(f"\n  [{i}] {entry.data.get('title', 'Untitled')}")
        print(f"      Topic: {entry.data.get('topic', 'Unknown')}")
        print(f"      Pending issues: {count}")
        print(f"      Confidence: {entry.data.get('confidence', 0) * 100:.0f}%")


def demo_feedback_by_type():
    """Demonstrate analyzing feedback by type."""
    print_section("5️⃣  FEEDBACK ANALYSIS BY TYPE")
    
    feedback_types = ["correction", "clarification", "addition", "outdated"]
    
    print("\nFeedback breakdown by type:")
    
    type_counts = {}
    for ftype in feedback_types:
        fb_list = db.records.find({
            "labels": ["FEEDBACK"],
            "where": {"type": ftype}
        })
        type_counts[ftype] = len(fb_list.data)
    
    for ftype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * count
        print(f"  {ftype.upper():<15} {bar} ({count})")
    
    # Status breakdown
    print("\nFeedback breakdown by status:")
    
    status_counts = {}
    for status in ["pending", "reviewed", "applied", "rejected"]:
        fb_list = db.records.find({
            "labels": ["FEEDBACK"],
            "where": {"status": status}
        })
        status_counts[status] = len(fb_list.data)
    
    for status, count in status_counts.items():
        bar = "█" * count
        print(f"  {status.upper():<15} {bar} ({count})")


def demo_complete_workflow():
    """Demonstrate a complete human-in-the-loop workflow."""
    print_section("6️⃣  COMPLETE HUMAN-IN-THE-LOOP WORKFLOW")
    
    print("\n--- Step 1: Submit new feedback ---")
    
    # Create new feedback
    new_feedback = db.records.create(
        label="FEEDBACK",
        data={
            "type": "clarification",
            "description": "The section on distributed systems should include a reference to the Raft consensus algorithm for better clarity.",
            "severity": "medium",
            "status": "pending",
            "reviewer": "Dr. Emily Watson",
            "submitted_at": datetime.now().isoformat()
        }
    )
    print(f"  ✅ Submitted feedback: {new_feedback.id[:20]}...")
    
    # Attach to a knowledge entry
    entries = db.records.find({
        "labels": ["KNOWLEDGE_ENTRY"],
        "where": {"topic": "distributed_systems"},
        "limit": 1
    })
    
    if entries.data:
        target_entry = entries.data[0]
    else:
        # Use any entry for demo
        any_entry = db.records.find({"labels": ["KNOWLEDGE_ENTRY"], "limit": 1})
        target_entry = any_entry.data[0] if any_entry.data else None
    
    if target_entry:
        db.records.attach(
            source=target_entry,
            target=new_feedback,
            options={"type": "HAS_FEEDBACK"}
        )
        print(f"  ✅ Attached to: {target_entry.data.get('title', 'Unknown')}")
    
    print("\n--- Step 2: Review feedback ---")
    
    # Update status to reviewed
    db.records.update(
        record_id=new_feedback.id,
        data={
            "status": "reviewed",
            "reviewed_at": datetime.now().isoformat(),
            "review_notes": "Valid suggestion, will apply in next update cycle."
        }
    )
    print(f"  ✅ Marked as 'reviewed'")
    
    print("\n--- Step 3: Apply correction ---")
    
    if target_entry:
        # Update the knowledge entry
        current_content = target_entry.data.get("content", "")
        updated_content = current_content + " Note: For consensus in distributed systems, consider also studying the Raft algorithm."
        
        db.records.update(
            record_id=target_entry.id,
            data={
                "content": updated_content,
                "updated_at": datetime.now().isoformat(),
                "version": target_entry.data.get("version", 1) + 1
            }
        )
        print(f"  ✅ Applied correction to knowledge entry")
        print(f"  ✅ Updated version to {target_entry.data.get('version', 1) + 1}")
        
        # Mark feedback as applied
        db.records.update(
            record_id=new_feedback.id,
            data={"status": "applied"}
        )
        print(f"  ✅ Marked feedback as 'applied'")
    
    print("\n--- Workflow complete! ---")


def demo_search_by_relationship():
    """Demonstrate querying by relationship to feedback."""
    print_section("7️⃣  QUERYING ENTRIES BY FEEDBACK RELATIONSHIP")
    
    print("\n--- Entries with high-severity feedback ---")
    
    high_severity = db.records.find({
        "labels": ["FEEDBACK"],
        "where": {"severity": "high", "status": "pending"}
    })
    
    print(f"\nFound {len(high_severity.data)} high-severity pending items:")
    
    for fb in high_severity.data:
        print(f"\n  ⚠️  {fb.data.get('type', 'unknown').upper()} from {fb.data.get('reviewer', 'Anonymous')}")
        print(f"      Description: {fb.data.get('description', '')[:60]}...")
    
    print("\n--- Entries needing review ---")
    
    needs_review = db.records.find({
        "labels": ["FEEDBACK"],
        "where": {
            "status": {"$in": ["pending", "reviewed"]}
        },
        "orderBy": {"submitted_at": "asc"}
    })
    
    print(f"\nFound {len(needs_review.data)} items needing review (oldest first):")
    for fb in needs_review.data[:3]:
        print(f"  📋 {fb.data.get('type', 'unknown')}: {fb.data.get('description', '')[:50]}...")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("🚀 FEEDBACK-ANNOTATED KNOWLEDGE STORE DEMO")
    print("=" * 60)
    print("\nThis demo shows how to build a knowledge management system")
    print("with human-in-the-loop corrections using RushDB.")
    
    # Run demonstrations
    demo_find_pending_feedback()
    demo_find_entries_with_feedback()
    demo_apply_correction()
    demo_find_quality_issues()
    demo_feedback_by_type()
    demo_complete_workflow()
    demo_search_by_relationship()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)
    print("\nKey RushDB patterns demonstrated:")
    print("  • Creating knowledge entries and feedback records")
    print("  • Attaching feedback to entries via relationships")
    print("  • Querying by feedback status and severity")
    print("  • Updating entries and tracking corrections")
    print("  • Analyzing feedback patterns by type and status")
    print("\nLearn more: https://docs.rushdb.com")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
