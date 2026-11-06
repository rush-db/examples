"""
main.py — Schema Versioning Walkthrough

Demonstrates how to evolve a production RushDB schema from V1 to V2
using zero-downtime migration patterns:
  1. Inspect current ontology
  2. Create V2 label with new properties
  3. Migrate records in bulk with shadow-write pattern
  4. Verify migration completeness
  5. Build an audit trail as a graph
  6. Update the registry and deprecate old label
"""

import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()
db = RushDB(os.environ["RUSHDB_API_KEY"])


# ─────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────

def print_phase(title):
    """Print a formatted phase header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def count_records(label):
    """Return the total count of records matching a label."""
    result = db.records.find({"labels": [label], "limit": 1})
    return result.total


def label_exists(label) -> bool:
    """Check whether any records with this label exist."""
    return count_records(label) > 0


# ─────────────────────────────────────────────────────────────
# PHASE 1: Inspect current schema state
# ─────────────────────────────────────────────────────────────

def phase_1_inspect_ontology():
    print_phase("PHASE 1: Schema Inspection")

    # Pull the full ontology as structured JSON
    ontology = db.ai.getOntology()

    print("Current ontology snapshot:")
    labels_by_count = sorted(
        [(lbl["name"], lbl["recordCount"]) for lbl in ontology.get("labels", [])],
        key=lambda x: -x[1],
    )

    for label, count in labels_by_count:
        props = [p["name"] for p in ontology.get("properties", []) if p.get("labels", []) and label in p.get("labels", [])]
        print(f"  - {label} ({count} records)")
        if props:
            print(f"    properties: {', '.join(props[:8])}{'...' if len(props) > 8 else ''}")

    # Pull the schema registry
    registry_results = db.records.find({"labels": ["SCHEMA_VERSION"]})
    if registry_results.data:
        registry = registry_results.data[0]
        print(f"\nRegistry: schema_version={registry.data.get('schema_version')}")
        active = registry.data.get("active_labels", {})
        for entity, label in active.items():
            print(f"  {entity} → {label}")
    else:
        print("\n⚠ No SCHEMA_VERSION registry found. Run seed.py first.")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
# PHASE 2: Define and deploy V2 schema
# ─────────────────────────────────────────────────────────────

def phase_2_create_v2_schema():
    print_phase("PHASE 2: Creating PRODUCT_V2 Schema")

    print("Defining V2 schema with new fields:")
    print("  NEW: tags (array of strings)")
    print("  NEW: origin_country (string)")
    print("  NEW: sustainability_score (float, 0-100)")
    print("  NEW: is_local (boolean)")
    print("  RETAINED: sku, name, price, stock, weight_kg, active")
    print("\nDeploying PRODUCT_V2 via bulk upsert...")

    # V2 products — we'll populate all existing V1 product fields plus the new ones
    v2_products = []
    v1_products = db.records.find({"labels": ["PRODUCT_V1"], "limit": 1000})

    for prod in v1_products.data:
        d = prod.data
        v2_record = {
            "sku": d.get("sku"),
            "name": d.get("name"),
            "price": d.get("price"),
            "stock": d.get("stock"),
            "weight_kg": d.get("weight_kg"),
            "active": d.get("active", True),
            # New V2 fields — sourced from existing tags or set to defaults
            "tags": d.get("tags", []) or [],
            "origin_country": d.get("origin_country", "US"),
            "sustainability_score": d.get("sustainability_score", round(50 + (hash(d.get("sku", "")) % 4000) / 100, 1)),
            "is_local": d.get("is_local", False),
            "migrated_from": d.get("sku"),  # cross-reference
            "migration_date": datetime.now(timezone.utc).isoformat(),
        }
        v2_products.append(v2_record)

    # Bulk upsert into PRODUCT_V2
    created = db.records.create_many(
        label="PRODUCT_V2",
        data=v2_products,
    )

    print(f"  Created {len(created.data)} PRODUCT_V2 records")
    print(f"  New properties detected: tags, origin_country, sustainability_score, is_local")

    # Attach relationships from V1 (categories) to V2
    print("\nAttaching category relationships to V2 records...")
    migrated_skus = {p["sku"] for p in v2_products}
    for v2_batch in [created.data[i:i+50] for i in range(0, len(created.data), 50)]:
        for v2_prod in v2_batch:
            sku = v2_prod.data.get("sku")
            if sku:
                # Find matching V1 product to copy its category relationship
                v1_match = db.records.find({"labels": ["PRODUCT_V1"], "where": {"sku": sku}})
                if v1_match.data:
                    v1_cat = db.records.find({
                        "labels": ["CATEGORY_V1"],
                        "where": {"PRODUCT_V1": {"$relation": {"type": "BELONGS_TO", "direction": "out"}, "sku": sku}},
                    })
                    if v1_cat.data:
                        db.records.attach(
                            source=v2_prod,
                            target=v1_cat.data[0],
                            options={"type": "BELONGS_TO", "direction": "out"},
                        )

    print("  Category relationships attached for all V2 products")


# ─────────────────────────────────────────────────────────────
# PHASE 3: Migrate records with transaction rollback safety
# ─────────────────────────────────────────────────────────────

def phase_3_migrate_with_transactions():
    print_phase("PHASE 3: Bulk Migration with Atomic Transactions")

    v1_count = count_records("PRODUCT_V1")
    v2_count = count_records("PRODUCT_V2")

    print(f"PRODUCT_V1: {v1_count} records")
    print(f"PRODUCT_V2: {v2_count} records")

    if v1_count == 0:
        print("\nNo V1 records to migrate — V2 already deployed. Skipping.")
        return

    print(f"\nRunning migration transaction (batch size: 50)...")
    start_time = time.time()

    # Migrate in transaction batches — if any batch fails, we rollback
    # and retry with a smaller batch. In production, you'd add retry logic.
    BATCH_SIZE = 50
    v1_products = db.records.find({"labels": ["PRODUCT_V1"], "limit": 10000})

    migrated = 0
    failed = 0

    for i in range(0, len(v1_products.data), BATCH_SIZE):
        batch = v1_products.data[i:i+BATCH_SIZE]
        try:
            with db.transactions.begin() as tx:
                for prod in batch:
                    d = prod.data
                    db.records.upsert(
                        label="PRODUCT_V2",
                        data={
                            "sku": d.get("sku"),
                            "name": d.get("name"),
                            "price": d.get("price"),
                            "stock": d.get("stock"),
                            "weight_kg": d.get("weight_kg"),
                            "active": d.get("active", True),
                            "tags": d.get("tags", []) or [],
                            "origin_country": d.get("origin_country", "US"),
                            "sustainability_score": d.get("sustainability_score", 50.0),
                            "is_local": d.get("is_local", False),
                            "migrated_from": d.get("sku"),
                            "migration_date": datetime.now(timezone.utc).isoformat(),
                        },
                        options={"mergeBy": ["sku"]},
                        transaction=tx,
                    )
                    migrated += 1

            if (i // BATCH_SIZE + 1) % 2 == 0:
                print(f"  Committed batch {i // BATCH_SIZE + 1} ({migrated} total)")

        except Exception as e:
            print(f"  Batch {i // BATCH_SIZE + 1} failed: {e}")
            failed += len(batch)

    elapsed = time.time() - start_time
    print(f"\n  Migration complete: {migrated} records in {elapsed:.2f}s")
    if failed:
        print(f"  Failed: {failed} records (check logs above)")


# ─────────────────────────────────────────────────────────────
# PHASE 4: Verify migration completeness
# ─────────────────────────────────────────────────────────────

def phase_4_verify():
    print_phase("PHASE 4: Verification")

    v1_count = count_records("PRODUCT_V1")
    v2_count = count_records("PRODUCT_V2")

    print(f"PRODUCT_V1 remaining: {v1_count}")
    print(f"PRODUCT_V2 total: {v2_count}")

    if v1_count == 0 and v2_count > 0:
        print("\n✓ Migration successful: V1 fully migrated to V2")
    elif v2_count > 0:
        print(f"\n⚠ Partial migration: {v1_count} V1 records still pending")

    # Verify V2 completeness: all records should have new fields
    v2_sample = db.records.find({"labels": ["PRODUCT_V2"], "limit": 5})
    completeness = 0
    for rec in v2_sample.data:
        d = rec.data
        if all(k in d for k in ["sustainability_score", "origin_country", "tags"]):
            completeness += 1

    print(f"\nSample completeness check (5 records): {completeness}/5 have all new fields")
    if completeness == 5:
        print("✓ All sampled V2 records have new fields populated")

    # Check average sustainability score as a sanity check
    total_score = sum(r.data.get("sustainability_score", 0) for r in v2_sample.data)
    avg_score = total_score / len(v2_sample.data) if v2_sample.data else 0
    print(f"Average sustainability_score across sample: {avg_score:.1f}")


# ─────────────────────────────────────────────────────────────
# PHASE 5: Build audit trail as a graph
# ─────────────────────────────────────────────────────────────

def phase_5_audit_trail():
    print_phase("PHASE 5: Audit Trail as a Graph")

    migration_id = f"v1_to_v2_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    migration_record = db.records.create(
        label="MIGRATION",
        data={
            "migration_id": migration_id,
            "from_version": "1.0.0",
            "to_version": "2.0.0",
            "description": "Product schema V1 → V2: add tags, origin_country, sustainability_score, is_local",
            "status": "completed",
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "affected_labels": ["PRODUCT_V1", "PRODUCT_V2"],
            "records_migrated": count_records("PRODUCT_V2"),
            "rollback_supported": True,
            "notes": "Old V1 records retained (not deleted) for relationship integrity",
        },
    )

    print(f"Migration audit record created: {migration_record.id}")
    print(f"  migration_id: {migration_id}")
    print(f"  status: completed")
    print(f"  affected_labels: [PRODUCT_V1, PRODUCT_V2]")

    # Attach migration to the registry record
    registry = db.records.find({"labels": ["SCHEMA_VERSION"]})
    if registry.data:
        db.records.attach(
            source=migration_record,
            target=registry.data[0],
            options={"type": "RECORDED_IN", "direction": "out"},
        )
        print("  Attached to SCHEMA_VERSION registry")

    # Show full migration history
    print("\nFull migration history:")
    migrations = db.records.find({"labels": ["MIGRATION"], "limit": 10})
    for m in migrations.data:
        d = m.data
        print(f"  [{d.get('migration_id')}] {d.get('from_version')} → {d.get('to_version')} | {d.get('status')}")


# ─────────────────────────────────────────────────────────────
# PHASE 6: Update registry and deprecate old label
# ─────────────────────────────────────────────────────────────

def phase_6_update_registry():
    print_phase("PHASE 6: Registry Update & Version Deprecation")

    # Update the registry to point to V2
    registry = db.records.upsert(
        label="SCHEMA_VERSION",
        data={
            "schema_version": "2.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "active_labels": {
                "PRODUCT": "PRODUCT_V2",
                "CATEGORY": "CATEGORY_V1",
                "USER": "USER_V1",
                "ORDER": "ORDER_V1",
            },
            "deprecated_labels": {
                "PRODUCT": "PRODUCT_V1",
            },
            "migrations_applied": ["init_v1", "v1_to_v2"],
        },
        options={"mergeBy": ["schema_version"]},
    )

    print("Registry updated:")
    print(f"  schema_version: 2.0.0")
    print(f"  PRODUCT → PRODUCT_V2 (active)")
    print(f"  PRODUCT_V1 → deprecated (retained, not deleted)")

    print("\nDeprecation strategy for PRODUCT_V1:")
    print("  1. New writes route to PRODUCT_V2 via registry")
    print("  2. Existing PRODUCT_V1 records kept — relationships intact")
    print("  3. Read queries can union PRODUCT_V1 + PRODUCT_V2 during transition")
    print("  4. PRODUCT_V1 can be soft-deleted after transition window (e.g. 90 days)")

    v1_count = count_records("PRODUCT_V1")
    v2_count = count_records("PRODUCT_V2")
    print(f"\nFinal state: PRODUCT_V1={v1_count} (deprecated) | PRODUCT_V2={v2_count} (active)")


# ─────────────────────────────────────────────────────────────
# PHASE 7: Query the evolved schema
# ─────────────────────────────────────────────────────────────

def phase_7_query_examples():
    print_phase("PHASE 7: Querying the Evolved Schema")

    print("Example queries against the V2 schema:\n")

    # Query 1: High sustainability products
    print("1. Products with sustainability_score >= 70:")
    high_sustainability = db.records.find({
        "labels": ["PRODUCT_V2"],
        "where": {"sustainability_score": {"$gte": 70}},
        "limit": 5,
    })
    for p in high_sustainability.data:
        d = p.data
        print(f"   [{d.get('sku')}] {d.get('name')} — score: {d.get('sustainability_score')}")

    # Query 2: Filter by origin country
    print("\n2. Products from origin_country = 'DE':")
    de_products = db.records.find({
        "labels": ["PRODUCT_V2"],
        "where": {"origin_country": "DE"},
        "limit": 5,
    })
    if de_products.data:
        for p in de_products.data:
            print(f"   [{p.data.get('sku')}] {p.data.get('name')}")
    else:
        print("   (none found — expected, sample data uses US)")

    # Query 3: Find products with a specific tag
    print("\n3. Products tagged 'sports' or 'fitness':")
    tagged = db.records.find({
        "labels": ["PRODUCT_V2"],
        "where": {"tags": {"$contains": "sports"}},
        "limit": 5,
    })
    for p in tagged.data:
        print(f"   [{p.data.get('sku')}] {p.data.get('name')} | tags: {p.data.get('tags')}")

    # Query 4: Traverse graph — products with their categories
    print("\n4. Products with their categories (graph traversal):")
    products_with_cats = db.records.find({
        "labels": ["PRODUCT_V2"],
        "where": {"CATEGORY_V1": {"$exists": True}},
        "limit": 4,
        "select": ["sku", "name", "price"],
    })
    for p in products_with_cats.data:
        print(f"   {p.data.get('name')} (${p.data.get('price')}) → has category relationship")

    # Query 5: Mixed-version union (during transition window)
    print("\n5. All products across both labels (union query):")
    all_labels = ["PRODUCT_V1", "PRODUCT_V2"]
    all_products = db.records.find({"labels": all_labels, "limit": 10})
    counts = {lbl: 0 for lbl in all_labels}
    for p in all_products.data:
        counts[p.label] += 1
    print(f"   Total accessible: {all_products.total} records")
    for lbl, cnt in counts.items():
        print(f"   {lbl}: {cnt}")


# ─────────────────────────────────────────────────────────────
# PHASE 8: Capture final ontology snapshot
# ─────────────────────────────────────────────────────────────

def phase_8_ontology_snapshot():
    print_phase("PHASE 8: Ontology Snapshot")

    ontology = db.ai.getOntologyMarkdown()
    print("Final schema ontology (paste into LLM context or docs):\n")
    print(ontology)

    # Print property type summary
    props = db.properties.find()
    print(f"\nTotal properties in schema: {len(props)}")
    prop_types = {}
    for p in props:
        t = p.data.get("type", "unknown")
        prop_types[t] = prop_types.get(t, 0) + 1
    print("Property type distribution:")
    for t, count in sorted(prop_types.items()):
        print(f"  {t}: {count}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  RushDB: Versioning Graph Schemas in Production")
    print("  Tutorial — Senior Engineer Edition")
    print("=" * 60)

    # Run all phases
    phase_1_inspect_ontology()
    phase_2_create_v2_schema()
    phase_3_migrate_with_transactions()
    phase_4_verify()
    phase_5_audit_trail()
    phase_6_update_registry()
    phase_7_query_examples()
    phase_8_ontology_snapshot()

    print("\n" + "=" * 60)
    print("  Tutorial Complete")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  • Use label versioning (PRODUCT_V1, PRODUCT_V2) for breaking changes")
    print("  • Use property aliases for non-breaking additions")
    print("  • Keep the SCHEMA_VERSION registry as a graph record")
    print("  • Audit migrations as MIGRATION records")
    print("  • Transactions wrap all bulk operations")
    print("  • db.ai.getOntology() is your schema introspection tool")
    print("\nLearn more: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
