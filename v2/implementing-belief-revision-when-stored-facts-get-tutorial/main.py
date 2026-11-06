"""
Belief Revision Tutorial — Main Demonstration

This script demonstrates how to implement belief revision patterns using RushDB.
When stored facts get contradicted by incoming data, we need to:

1. Detect the contradiction
2. Mark the old belief as retracted
3. Create a new belief with the corrected value
4. Link them together for audit trails
5. Handle cascading revisions for dependent beliefs

Run with: python main.py
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# =============================================================================
# DATA: Incoming data that contradicts our stored beliefs
# =============================================================================

INCOMING_CORRECTIONS = {
    "TechCorp": {
        "founding_date": "2000-01-01",  # Old: "1999-03-15"
        "ceo": "Jane Doe",              # Old: "John Smith"
    },
    "DataInc": {
        "headquarters": "Boston",       # Old: "New York"
    },
}


# =============================================================================
# PATTERN 1: Load Knowledge Base and Detect Contradictions
# =============================================================================

def load_knowledge_base(db: RushDB) -> list:
    """
    Load all active (non-retracted) beliefs from the knowledge base.
    Returns a list of belief records with their entity information.
    """
    beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": {"retracted": False},
    })

    # For each belief, find its related entity
    enriched_beliefs = []
    for belief in beliefs:
        entity = db.records.find({
            "labels": ["ENTITY"],
            "where": {"BELIEF": {"$relation": {"type": "BELIEF_ABOUT", "direction": "in"}}},
        })

        belief_data = {
            "id": belief.id,
            "entity_name": entity[0].data.get("name") if entity else None,
            "property_name": belief.data.get("property_name"),
            "value": belief.data.get("value"),
            "confidence": belief.data.get("confidence"),
            "source": belief.data.get("source"),
            "created_at": belief.data.get("created_at"),
        }
        enriched_beliefs.append(belief_data)

    return enriched_beliefs


def detect_contradictions(
    current_beliefs: list,
    incoming_data: dict
) -> list:
    """
    Compare current beliefs against incoming data to find contradictions.

    A contradiction occurs when:
    - We have an active belief for a property/entity
    - The incoming data provides a different value for that same property

    Returns a list of contradiction details.
    """
    contradictions = []

    for belief in current_beliefs:
        entity_name = belief["entity_name"]
        property_name = belief["property_name"]
        current_value = belief["value"]

        # Check if we have incoming data for this entity
        if entity_name in incoming_data:
            corrections = incoming_data[entity_name]

            # Check if the incoming data contradicts this property
            if property_name in corrections:
                incoming_value = str(corrections[property_name])


                if current_value != incoming_value:
                    contradictions.append({
                        "entity_name": entity_name,
                        "property_name": property_name,
                        "belief_id": belief["id"],
                        "current_value": current_value,
                        "incoming_value": incoming_value,
                        "current_confidence": belief["confidence"],
                        "current_source": belief["source"],
                    })

    return contradictions


# =============================================================================
# PATTERN 2: Simple Revision (Overwrite)
# =============================================================================

def simple_revision(db: RushDB, contradiction: dict) -> str:
    """
    Simple revision: Just update the belief value directly.

    Use case: When you don't care about preserving history and just
    need the current state to be correct.

    Note: This pattern loses the old value. See Pattern 3 for history preservation.
    """
    belief_id = contradiction["belief_id"]
    new_value = contradiction["incoming_value"]

    db.records.update(
        record_id=belief_id,
        data={"value": new_value}
    )

    return belief_id


# =============================================================================
# PATTERN 3: Full Revision with History (Preserve Audit Trail)
# =============================================================================

def full_revision_with_history(
    db: RushDB,
    contradiction: dict,
    revision_reason: str = "Source verification failed"
) -> tuple:
    """
    Full belief revision that preserves an audit trail:

    1. Mark the old belief as retracted
    2. Create a new belief with the corrected value
    3. Link them together with RETRACTED and CORRECTED_BY relationships


    This is the recommended pattern for production systems where
    you need to maintain a complete history of belief changes.
    """
    old_belief_id = contradiction["belief_id"]
    entity_name = contradiction["entity_name"]
    property_name = contradiction["property_name"]
    new_value = contradiction["incoming_value"]
    current_source = contradiction["current_source"]

    with db.transactions.begin() as tx:
        # Step 1: Retract the old belief
        db.records.update(
            record_id=old_belief_id,
            data={
                "retracted": True,
                "revised_at": datetime.utcnow().isoformat(),
                "revision_note": f"{revision_reason}. Previous value: {contradiction['current_value']}",
            }
        )

        # Step 2: Create the new belief
        new_belief = db.records.create(
            label="BELIEF",
            data={
                "property_name": property_name,
                "value": new_value,
                "source": "correction_service",
                "confidence": 0.95,  # Higher confidence for verified data
                "retracted": False,
                "created_at": datetime.utcnow().isoformat(),
                "revised_at": None,
                "revision_note": f"Correction of previously retracted belief",
                "supersedes": old_belief_id,
            },
            transaction=tx
        )

        # Step 3: Find the entity to link the new belief
        entity = db.records.find({
            "labels": ["ENTITY"],
            "where": {"name": entity_name}
        })

        if entity:
            db.records.attach(
                source=new_belief,
                target=entity[0],
                options={"type": "BELIEF_ABOUT", "direction": "out"},
                transaction=tx
            )

        # Step 4: Link old belief to new belief
        db.records.attach(
            source=new_belief,
            target=db.records.find_by_id(old_belief_id),
            options={"type": "CORRECTED_BY", "direction": "out"},
            transaction=tx
        )

    return old_belief_id, new_belief.id



# =============================================================================
# PATTERN 4: Cascading Revision (Dependent Beliefs)
# =============================================================================

def find_dependent_beliefs(db: RushDB, belief_id: str) -> list:
    """
    Find beliefs that depend on the given belief.

    In a graph, beliefs can reference other beliefs through relationships.
    When a belief is retracted, all beliefs that depend on it may need
    cascading revision.

    For this tutorial, we simulate dependencies by finding beliefs
    that reference the same entity with lower confidence.
    """
    # Get the entity this belief is about
    entity = db.records.find({
        "labels": ["ENTITY"],
        "where": {"BELIEF": {"$relation": {"type": "BELIEF_ABOUT", "direction": "in"}}},
    })

    if not entity:
        return []

    entity_id = entity[0].id

    # Find beliefs with lower confidence that might need revision
    dependent = db.records.find({
        "labels": ["BELIEF"],
        "where": {
            "retracted": False,
            "confidence": {"$lt": 0.8},
            "ENTITY": {"$id": entity_id},
        },
    })

    return [b for b in dependent if b.id != belief_id]


def cascading_revision(
    db: RushDB,
    contradiction: dict,
    revision_reason: str
) -> dict:
    """
    Handle belief revision that may cascade to dependent beliefs.


    Process:
    1. Perform the main revision
    2. Find any beliefs that depend on the revised belief
    3. Optionally revise those beliefs (often just re-evaluating confidence)
    """
    # Step 1: Perform the main revision
    old_id, new_id = full_revision_with_history(db, contradiction, revision_reason)


    # Step 2: Find dependents
    dependents = find_dependent_beliefs(db, old_id)

    revision_result = {
        "main_revision": {"old_id": old_id, "new_id": new_id},
        "dependents_found": len(dependents),
        "dependent_revisions": [],
    }

    # Step 3: Revise dependent beliefs (simple re-validation)
    for dep in dependents:
        # In a real system, you might:
        # - Recalculate confidence based on the correction
        # - Flag for manual review
        # - Trigger downstream system updates

        db.records.update(
            record_id=dep.id,
            data={
                "revision_note": "Re-evaluated after upstream correction",
                "revised_at": datetime.utcnow().isoformat(),
            }
        )

        revision_result["dependent_revisions"].append({
            "id": dep.id,
            "property": dep.data.get("property_name"),
            "action": "re-validated",
        })

    return revision_result


# =============================================================================
# PATTERN 5: Querying Revised Knowledge
# =============================================================================

def query_belief_state(
    db: RushDB,
    entity_name: str = None,
    include_retracted: bool = False
) -> dict:
    """
    Query beliefs with optional filtering.

    Returns counts and optionally the belief details.
    """
    where_clause = {"retracted": False}

    if not include_retracted:
        where_clause = {"retracted": False}

    beliefs = db.records.find({
        "labels": ["BELIEF"],
        "where": where_clause,
    })

    # Filter by entity if specified
    if entity_name:
        beliefs = [b for b in beliefs if b.data.get("property_name")]

    active = [b for b in beliefs if not b.data.get("retracted", False)]
    retracted = [b for b in beliefs if b.data.get("retracted", False)]

    return {
        "total": len(beliefs),
        "active_count": len(active),
        "retracted_count": len(retracted),
        "active": active,
        "retracted": retracted,
    }


def get_belief_history(db: RushDB, belief_id: str) -> list:
    """
    Trace the complete history of a belief through its corrections.

    Follows CORRECTED_BY relationships to build a chain of revisions.
    """
    history = []
    current_id = belief_id
    visited = set()

    while current_id and current_id not in visited:
        visited.add(current_id)
        belief = db.records.find_by_id(current_id)

        if not belief:
            break

        history.append({
            "id": belief.id,
            "value": belief.data.get("value"),
            "retracted": belief.data.get("retracted", False),
            "created_at": belief.data.get("created_at"),
            "revised_at": belief.data.get("revised_at"),
            "revision_note": belief.data.get("revision_note"),
        })

        # Follow the correction chain
        corrections = db.records.find({
            "labels": ["BELIEF"],
            "where": {"BELIEF": {"$relation": {"type": "CORRECTED_BY", "direction": "in"}}},
        })

        if corrections and corrections[0].id != current_id:
            current_id = corrections[0].id
        else:
            break

    return history


# =============================================================================
# MAIN TUTORIAL EXECUTION
# =============================================================================

def main():
    """Run the complete belief revision tutorial demonstration."""
    print("=" * 60)
    print("BELIEF REVISION TUTORIAL")
    print("=" * 60)
    print()

    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY environment variable not set")
        print("Copy .env.example to .env and add your API key")
        return

    db = RushDB(api_key)

    # -----------------------------------------------------------------------------
    # STEP 1: Load Knowledge Base
    # -----------------------------------------------------------------------------
    print("[1] Loading Knowledge Base...")
    beliefs = load_knowledge_base(db)
    print(f"      Found {len(beliefs)} active beliefs")

    # Display beliefs grouped by entity
    entities = {}
    for belief in beliefs:
        entity = belief["entity_name"]
        if entity not in entities:
            entities[entity] = []
        entities[entity].append(belief)

    for entity, entity_beliefs in entities.items():
        print(f"      - {entity}: {len(entity_beliefs)} beliefs")
    print()

    # -----------------------------------------------------------------------------
    # STEP 2: Detect Contradictions
    # -----------------------------------------------------------------------------
    print("[2] Detecting Contradictions...")
    contradictions = detect_contradictions(beliefs, INCOMING_CORRECTIONS)
    print(f"      Found {len(contradictions)} contradictions:")

    for c in contradictions:
        print(f"      - {c['entity_name']}.{c['property_name']}")
        print(f"        Current: '{c['current_value']}' vs Incoming: '{c['incoming_value']}'")
        print(f"        Belief ID: {c['belief_id'][:20]}...")
    print()

    # -----------------------------------------------------------------------------
    # STEP 3: Simple Revision (for demonstration only)
    # -----------------------------------------------------------------------------
    print("[3] Simple Revision...")
    print("      (Directly updating without preserving history)")

    if contradictions:
        # Use the first contradiction for simple revision demo
        first_contraction = contradictions[0]
        old_id = simple_revision(db, first_contraction)
        print(f"      Updated {first_contraction['entity_name']}.{first_contraction['property_name']}")
        print(f"      Old belief ID: {old_id[:20]}...")
        print("      WARNING: Original value is lost!")
    print()

    # Reload beliefs after simple revision
    beliefs = load_knowledge_base(db)

    # -----------------------------------------------------------------------------
    # STEP 4: Full Revision with History
    # -----------------------------------------------------------------------------
    print("[4] Full Revision with History...")
    print("      (Preserving audit trail via retraction records)")

    # Skip the first contradiction (already revised simply)
    remaining = detect_contradictions(beliefs, INCOMING_CORRECTIONS)

    for c in remaining[:2]:  # Revise up to 2 more
        print(f"\n      Revising {c['entity_name']}.{c['property_name']}...")
        old_id, new_id = full_revision_with_history(
            db, c, revision_reason="Official correction received"
        )
        print(f"      - Retracted belief ID: {old_id[:20]}...")
        print(f"      - Created new belief ID: {new_id[:20]}...")

        # Show the history trace
        history = get_belief_history(db, new_id)
        print(f"      - History trace: {len(history)} belief(s) in chain")

        # Reload for next iteration
        beliefs = load_knowledge_base(db)
    print()

    # -----------------------------------------------------------------------------
    # STEP 5: Cascading Revision
    # -----------------------------------------------------------------------------
    print("[5] Cascading Revision...")

    remaining = detect_contradictions(beliefs, INCOMING_CORRECTIONS)
    if remaining:
        c = remaining[0]
        print(f"      Processing {c['entity_name']}.{c['property_name']}...")
        result = cascading_revision(db, c, "Cascade from primary correction")

        print(f"      - Main revision complete")
        print(f"      - Dependent beliefs found: {result['dependents_found']}")

        for dep in result["dependent_revisions"]:
            print(f"        - {dep['property']}: {dep['action']}")
    else:
        print("      No remaining contradictions to process")
    print()

    # -----------------------------------------------------------------------------
    # STEP 6: Query Revised Knowledge
    # -----------------------------------------------------------------------------
    print("[6] Querying Revised Knowledge...")

    state = query_belief_state(db, include_retracted=True)
    print(f"      Total beliefs: {state['total']}")
    print(f"      Active beliefs: {state['active_count']}")
    print(f"      Retracted beliefs: {state['retracted_count']}")
    print()

    # Show detailed state for a specific entity
    print("      Active beliefs by entity:")
    for entity, entity_beliefs in entities.items():
        print(f"      - {entity}:")
        for b in entity_beliefs[:3]:  # Show first 3
            status = "✓" if not b.get("retracted") else "✗"
            print(f"        {status} {b['property_name']}: {b['value']}")

    print()
    print("=" * 60)
    print("TUTORIAL COMPLETE")
    print("=" * 60)
    print()
    print("Key patterns demonstrated:")
    print("  1. Detection: Comparing current beliefs vs incoming data")
    print("  2. Simple Revision: Direct update (lossy)")
    print("  3. Full Revision: Retraction + new belief + linking")
    print("  4. Cascading: Revising dependent beliefs")
    print("  5. Querying: Filtering active vs retracted beliefs")
    print()
    print("For production use, prefer Pattern 3 (Full Revision) to")
    print("maintain complete audit trails and enable rollback if needed.")



if __name__ == "__main__":
    main()
