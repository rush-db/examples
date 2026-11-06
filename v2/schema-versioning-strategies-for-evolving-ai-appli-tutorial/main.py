"""
Schema Versioning Strategies for Evolving AI Applications

This tutorial demonstrates comprehensive schema versioning patterns using RushDB's
flexible, zero-schema architecture. AI applications frequently evolve: models change,
new fields are introduced, legacy properties are deprecated, and data structures need
to migrate while preserving history.

Key Patterns Covered:
1. Version Tagging - Attach semantic version metadata to records
2. Migration Records - Track schema changes as first-class records
3. Rolling Upgrades - Handle mixed-version data during transitions
4. Rollback Patterns - Revert to previous schema states
5. Property Lineage - Track field evolution across versions

Usage:
    python main.py [--verbose]
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Parse arguments
parser = argparse.ArgumentParser(description="Schema Versioning Tutorial")
parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
args = parser.parse_args()

VERBOSE = args.verbose


def log(section: str, message: str):
    """Print log message if verbose mode enabled."""
    if VERBOSE:
        print(f"  [{section}] {message}")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_step(step: str, message: str):
    """Print a step header."""
    print(f"\n▶ {step}: {message}")


def print_result(success: bool, message: str):
    """Print a result indicator."""
    symbol = "✓" if success else "✗"
    print(f"   {symbol} {message}")


# ============================================================================
# SECTION 1: VERSION TAGGING PATTERN
# ============================================================================

def demonstrate_version_tagging(db: RushDB) -> list:
    """
    Pattern 1: Version Tagging
    
    Attach semantic version metadata to records. This is the foundation
    of schema versioning - each record carries information about which
    schema version it conforms to.
    """
    print_section("PATTERN 1: Version Tagging")
    
    print("""
    Version tagging is the foundation of schema versioning. Each record
    carries metadata indicating which schema version it conforms to.
    This allows querying and filtering records by their schema version.
    """)
    
    created_records = []
    
    print_step("1.1", "Creating AI model with version metadata")
    
    model = db.records.create(
        label="MODEL",
        data={
            "name": "sentiment-analyzer-v3",
            "baseName": "sentiment-analyzer",
            "version": "3.0.0",
            "schemaVersion": "2024.1",
            "inputFields": ["text"],
            "outputFields": ["sentiment", "confidence", "emotions"],
            "tutorial": True,
            "createdAt": datetime.utcnow().isoformat(),
        }
    )
    created_records.append(model)
    log("MODEL", f"Created model: {model.id}")
    print(f"   Model ID: {model.id}")
    print(f"   Schema Version: {model['schemaVersion']}")
    print_result(True, "Model created with version metadata")
    
    print_step("1.2", "Creating prediction with embedded version")
    
    prediction = db.records.create(
        label="PREDICTION",
        data={
            "input": "The AI model demonstrates impressive accuracy.",
            "output": {
                "sentiment": "positive",
                "confidence": 0.94,
                "emotions": ["satisfaction", "approval"]
            },
            "modelName": model.data.get("name"),
            "modelVersion": model.data.get("version"),
            "schemaVersion": "2024.1",
            "tutorial": True,
        }
    )
    created_records.append(prediction)
    log("PREDICTION", f"Created prediction: {prediction.id}")
    print(f"   Prediction ID: {prediction.id}")
    print_result(True, "Prediction created with version metadata")
    
    print_step("1.3", "Querying records by schema version")
    
    current_schema = db.records.find({
        "labels": ["MODEL"],
        "where": {
            "schemaVersion": "2024.1",
            "tutorial": True
        }
    })
    print(f"   Found {current_schema.total} models with schema version 2024.1")
    print_result(True, f"Version query returned {current_schema.total} records")
    
    # Show a record's version info
    if current_schema.data:
        record = current_schema.data[0]
        print(f"   Sample: {record.data.get('name')} (v{record.data.get('version')})")
    
    return created_records


# ============================================================================
# SECTION 2: MIGRATION RECORD PATTERN
# ============================================================================

def demonstrate_migration_records(db: RushDB) -> list:
    """
    Pattern 2: Migration Records
    
    Track schema changes as first-class records. Migration records capture
    what changed, when, and what records were affected. This creates an
    auditable history of schema evolution.
    """
    print_section("PATTERN 2: Migration Records")
    
    print("""
    Migration records track schema changes as first-class citizens in the graph.
    Each migration captures what changed, when, and what records were affected.
    This creates an auditable history of schema evolution.
    """)
    
    created_records = []
    
    print_step("2.1", "Creating a schema migration record")
    
    migration = db.records.create(
        label="SCHEMA_MIGRATION",
        data={
            "migrationId": "MIGR-2024-001",
            "fromVersion": "2023.3",
            "toVersion": "2024.1",
            "appliedAt": datetime.utcnow().isoformat(),
            "appliedBy": "migration-bot@v2.1",
            "affectedLabels": ["MODEL", "PREDICTION"],
            "changes": {
                "added": ["confidence", "emotions", "topK"],
                "deprecated": ["score"],
                "modified": [
                    {"field": "outputFormat", "from": "json", "to": "structured"}
                ]
            },
            "rollbackAvailable": True,
            "migrationType": "breaking",
            "tutorial": True,
        }
    )
    created_records.append(migration)
    log("MIGRATION", f"Created migration record: {migration.id}")
    print(f"   Migration ID: {migration.id}")
    print(f"   Type: {migration['migrationType']}")
    print_result(True, "Migration record created")
    
    print_step("2.2", "Creating a rollback checkpoint")
    
    checkpoint = db.records.create(
        label="MIGRATION_LOG",
        data={
            "checkpointId": "CP-2024-001",
            "migrationId": migration['migrationId'],
            "createdAt": datetime.utcnow().isoformat(),
            "status": "ready",
            "affectedRecordsCount": 150,
            "schemaSnapshot": {
                "MODEL": ["name", "version", "inputFields", "outputFields"],
                "PREDICTION": ["input", "output", "confidence"]
            },
            "tutorial": True,
        }
    )
    created_records.append(checkpoint)
    log("CHECKPOINT", f"Created checkpoint: {checkpoint.id}")
    print(f"   Checkpoint ID: {checkpoint.id}")
    print_result(True, "Rollback checkpoint created")
    
    print_step("2.3", "Querying migration history")
    
    migrations = db.records.find({
        "labels": ["SCHEMA_MIGRATION"],
        "orderBy": {"appliedAt": "desc"}
    })
    print(f"   Found {migrations.total} schema migrations")
    
    if migrations.data:
        latest = migrations.data[0]
        print(f"   Latest: {latest.data.get('migrationId')} ({latest.data.get('fromVersion')} → {latest.data.get('toVersion')})")
    
    print_result(True, f"Migration history contains {migrations.total} records")
    
    return created_records


# ============================================================================
# SECTION 3: ROLLING UPGRADE PATTERN
# ============================================================================

def demonstrate_rolling_upgrades(db: RushDB, existing_models: list) -> list:
    """
    Pattern 3: Rolling Upgrades
    
    Handle mixed-version data during transitions. This pattern allows
    querying and operating on records with different schema versions
    simultaneously, which is critical during migration periods.
    """
    print_section("PATTERN 3: Rolling Upgrades")
    
    print("""
    Rolling upgrades handle mixed-version data during transitions. This pattern
    allows querying and operating on records with different schema versions
    simultaneously, which is critical during migration periods.
    """)
    
    created_records = []
    
    print_step("3.1", "Creating records with different schema versions")
    
    # Create legacy record (old schema)
    legacy_model = db.records.create(
        label="MODEL",
        data={
            "name": "legacy-classifier-v1",
            "version": "1.0.0",
            "schemaVersion": "2023.1",
            "inputFields": ["text"],
            "outputFields": ["category", "score"],  # Old fields
            "tutorial": True,
        }
    )
    created_records.append(legacy_model)
    print(f"   Legacy model: {legacy_model.id} (schema: {legacy_model['schemaVersion']})")
    
    # Create current record (new schema)
    current_model = db.records.create(
        label="MODEL",
        data={
            "name": "current-classifier-v2",
            "version": "2.0.0",
            "schemaVersion": "2024.1",
            "inputFields": ["text"],
            "outputFields": ["category", "confidence", "topK"],  # New fields
            "tutorial": True,
        }
    )
    created_records.append(current_model)
    print(f"   Current model: {current_model.id} (schema: {current_model['schemaVersion']})")
    print_result(True, "Created mixed-version records")
    
    print_step("3.2", "Querying records requiring migration")
    
    # Find legacy records (schema version < current)
    legacy_records = db.records.find({
        "labels": ["MODEL"],
        "where": {
            "schemaVersion": {"$lt": "2024.1"},
            "tutorial": True
        }
    })
    print(f"   Found {legacy_records.total} records needing migration")
    
    for record in legacy_records.data:
        print(f"     - {record.data.get('name')} (v{record.data.get('schemaVersion')})")
    
    print_result(True, f"Identified {legacy_records.total} records for migration")
    
    print_step("3.3", "Creating upgrade task for pending migrations")
    
    if legacy_records.total > 0:
        upgrade_task = db.records.create(
            label="MIGRATION_LOG",
            data={
                "taskId": "UPGRADE-001",
                "taskType": "rolling_upgrade",
                "sourceVersion": "2023.1",
                "targetVersion": "2024.1",
                "recordsToMigrate": legacy_records.total,
                "status": "pending",
                "createdAt": datetime.utcnow().isoformat(),
                "tutorial": True,
            }
        )
        created_records.append(upgrade_task)
        print(f"   Upgrade task: {upgrade_task.id}")
        print_result(True, "Upgrade task created")
    
    return created_records


# ============================================================================
# SECTION 4: ROLLBACK PATTERN
# ============================================================================

def demonstrate_rollback_pattern(db: RushDB) -> list:
    """
    Pattern 4: Rollback Pattern
    
    Revert to previous schema states when migrations fail. This uses
    transactions to ensure atomic rollback operations.
    """
    print_section("PATTERN 4: Rollback Pattern")
    
    print("""
    The rollback pattern ensures migrations can be safely reverted.
    Using transactions guarantees atomic operations - either all changes
    apply, or none do.
    """)
    
    created_records = []
    
    print_step("4.1", "Creating a rollback-enabled migration")
    
    # Use transaction for atomic migration setup
    with db.transactions.begin() as tx:
        # Create the rollback migration record
        rollback_migration = db.records.create(
            label="SCHEMA_MIGRATION",
            data={
                "migrationId": "MIGR-ROLLBACK-001",
                "fromVersion": "2024.1",
                "toVersion": "2023.3",
                "migrationType": "rollback",
                "status": "prepared",
                "canRollback": True,
                "createdAt": datetime.utcnow().isoformat(),
                "tutorial": True,
            },
            transaction=tx
        )
        
        # Create associated rollback checkpoint
        rollback_checkpoint = db.records.create(
            label="MIGRATION_LOG",
            data={
                "checkpointId": "ROLLBACK-CP-001",
                "migrationId": rollback_migration['migrationId'],
                "type": "rollback",
                "status": "prepared",
                "createdAt": datetime.utcnow().isoformat(),
                "tutorial": True,
            },
            transaction=tx
        )
        
        created_records.append(rollback_migration)
        created_records.append(rollback_checkpoint)
    
    print(f"   Migration: {rollback_migration.id}")
    print(f"   Checkpoint: {rollback_checkpoint.id}")
    print_result(True, "Rollback-enabled migration created")
    
    print_step("4.2", "Simulating rollback operation")
    
    # Find records affected by the rollback
    affected = db.records.find({
        "labels": ["MODEL"],
        "where": {
            "schemaVersion": "2024.1",
            "tutorial": True
        }
    })
    print(f"   Records to revert: {affected.total}")
    
    # Simulate rollback: update schema version
    with db.transactions.begin() as tx:
        for record in affected.data:
            db.records.update(
                record_id=record.id,
                data={
                    "schemaVersion": "2023.3",
                    "revertedAt": datetime.utcnow().isoformat(),
                    "revertedBy": "ROLLBACK-001"
                },
                transaction=tx
            )
    
    print_result(True, "Rollback operation completed")
    
    # Verify rollback
    reverted = db.records.find({
        "labels": ["MODEL"],
        "where": {
            "schemaVersion": "2023.3",
            "tutorial": True
        }
    })
    print(f"   Verified: {reverted.total} records now at version 2023.3")
    
    return created_records


# ============================================================================
# SECTION 5: PROPERTY LINEAGE PATTERN
# ============================================================================

def demonstrate_property_lineage(db: RushDB) -> list:
    """
    Pattern 5: Property Lineage
    
    Track how fields evolved across versions. Each property in RushDB
    is a first-class entity, allowing us to track field evolution
    as relationships between property records.
    """
    print_section("PATTERN 5: Property Lineage")
    
    print("""
    Property lineage tracks how fields evolved across versions. In RushDB,
    properties are first-class entities, allowing us to model field
    evolution as relationships.
    """)
    
    created_records = []
    
    print_step("5.1", "Creating property version records")
    
    # Create property lineage chain
    property_definitions = [
        {
            "name": "score",
            "version": "2023.1",
            "type": "float",
            "description": "Model confidence score (deprecated)"
        },
        {
            "name": "confidence",
            "version": "2023.3",
            "type": "float",
            "description": "Model confidence score (replaces score)"
        },
        {
            "name": "confidence",
            "version": "2024.1",
            "type": "float",
            "range": {"min": 0.0, "max": 1.0},
            "description": "Normalized confidence score"
        }
    ]
    
    previous_prop = None
    for prop_def in property_definitions:
        prop_record = db.records.create(
            label="PROPERTY_VERSION",
            data={
                **prop_def,
                "tutorial": True,
            }
        )
        created_records.append(prop_record)
        
        # Link to previous version if exists
        if previous_prop:
            db.records.attach(
                source=prop_record,
                target=previous_prop,
                options={"type": "REPLACES", "direction": "out"}
            )
        
        print(f"   {prop_record.data.get('name')} (v{prop_record.data.get('version')})")
        previous_prop = prop_record
    
    print_result(True, "Property lineage chain created")
    
    print_step("5.2", "Creating field dependency graph")
    
    # Create a field dependency record
    dependency = db.records.create(
        label="FIELD_DEPENDENCY",
        data={
            "dependencyId": "DEP-001",
            "fieldName": "confidence",
            "introducedVersion": "2023.3",
            "requiredBy": ["PREDICTION", "MODEL_EVALUATION"],
            "replaces": ["score"],
            "migrationStrategy": "automatic",
            "tutorial": True,
        }
    )
    created_records.append(dependency)
    print(f"   Dependency: {dependency.id}")
    print_result(True, "Field dependency created")
    
    print_step("5.3", "Querying property history")
    
    # Find all versions of a property
    prop_history = db.records.find({
        "labels": ["PROPERTY_VERSION"],
        "where": {
            "name": "confidence"
        },
        "orderBy": {"version": "asc"}
    })
    print(f"   Found {prop_history.total} versions of 'confidence' property")
    
    for prop in prop_history.data:
        print(f"     - v{prop.data.get('version')}: {prop.data.get('description')}")
    
    print_result(True, "Property history retrieved")
    
    return created_records


# ============================================================================
# SECTION 6: SCHEMA EVOLUTION DEMO
# ============================================================================

def demonstrate_schema_evolution(db: RushDB) -> list:
    """
    Pattern 6: Schema Evolution
    
    A complete example showing schema evolution from v1 to v2,
    including data migration and validation.
    """
    print_section("PATTERN 6: Complete Schema Evolution Demo")
    
    print("""
    This demo shows a complete schema evolution lifecycle:
    1. Create initial schema (v1)
    2. Introduce new schema (v2)
    3. Migrate data
    4. Validate migration
    5. Deprecate old schema
    """)
    
    created_records = []
    
    print_step("6.1", "Creating initial schema (v1)")
    
    v1_model = db.records.create(
        label="MODEL",
        data={
            "name": "text-analyzer-v1",
            "version": "1.0.0",
            "schemaVersion": "v1",
            "schemaDefinition": {
                "input": {"type": "string", "required": True},
                "output": {
                    "category": {"type": "string"},
                    "score": {"type": "float", "min": 0, "max": 1}
                }
            },
            "tutorial": True,
            "createdAt": datetime.utcnow().isoformat(),
        }
    )
    created_records.append(v1_model)
    print(f"   v1 Model: {v1_model.id}")
    print_result(True, "Initial schema created")
    
    print_step("6.2", "Creating v2 schema with enhanced fields")
    
    v2_model = db.records.create(
        label="MODEL",
        data={
            "name": "text-analyzer-v2",
            "version": "2.0.0",
            "schemaVersion": "v2",
            "schemaDefinition": {
                "input": {"type": "string", "required": True},
                "output": {
                    "category": {"type": "string"},
                    "confidence": {"type": "float", "min": 0, "max": 1},
                    "topK": {"type": "array", "items": {"type": "string"}},
                    "metadata": {"type": "object"}
                }
            },
            "migrationFrom": "v1",
            "breaking": False,
            "tutorial": True,
            "createdAt": datetime.utcnow().isoformat(),
        }
    )
    created_records.append(v2_model)
    print(f"   v2 Model: {v2_model.id}")
    print_result(True, "New schema created")
    
    print_step("6.3", "Creating migration plan")
    
    migration_plan = db.records.create(
        label="SCHEMA_MIGRATION",
        data={
            "planId": "PLAN-001",
            "fromSchema": "v1",
            "toSchema": "v2",
            "fieldMappings": [
                {"from": "score", "to": "confidence", "transform": "identity"}
            ],
            "additions": ["topK", "metadata"],
            "status": "planned",
            "estimatedRecords": 42,
            "tutorial": True,
        }
    )
    created_records.append(migration_plan)
    print(f"   Migration plan: {migration_plan.id}")
    print_result(True, "Migration plan created")
    
    print_step("6.4", "Executing migration with validation")
    
    # Create sample v1 data
    sample_v1_data = []
    for i in range(3):
        record = db.records.create(
            label="ANALYSIS",
            data={
                "text": f"Sample text {i+1}",
                "category": f"category_{i}",
                "score": 0.75 + (i * 0.05),
                "schemaVersion": "v1",
                "tutorial": True,
            }
        )
        sample_v1_data.append(record)
        created_records.append(record)
    
    print(f"   Created {len(sample_v1_data)} v1 records for migration")
    
    # Migrate records
    migrated_count = 0
    with db.transactions.begin() as tx:
        for record in sample_v1_data:
            # Transform data to v2 schema
            new_data = {
                "text": record.data.get("text"),
                "category": record.data.get("category"),
                "confidence": record.data.get("score"),  # Map score to confidence
                "topK": [record.data.get("category")],    # Add new field
                "metadata": {"migratedFrom": "v1"},
                "schemaVersion": "v2",
                "migratedAt": datetime.utcnow().isoformat(),
                "tutorial": True,
            }
            
            db.records.set(
                target=record,
                label="ANALYSIS",
                data=new_data,
                transaction=tx
            )
            migrated_count += 1
    
    print(f"   Migrated {migrated_count} records")
    print_result(True, "Migration completed with transaction")
    
    print_step("6.5", "Validating migrated data")
    
    v2_records = db.records.find({
        "labels": ["ANALYSIS"],
        "where": {
            "schemaVersion": "v2",
            "tutorial": True
        }
    })
    
    print(f"   Validated {v2_records.total} v2 records")
    for record in v2_records.data:
        has_confidence = "confidence" in record.data
        has_topk = "topK" in record.data
        print(f"     - {record.id}: confidence={has_confidence}, topK={has_topk}")
    
    print_result(True, f"Validation passed for {v2_records.total} records")
    
    return created_records


# ============================================================================
# SECTION 7: CLEANUP
# ============================================================================

def cleanup_tutorial_data(db: RushDB):
    """Remove all tutorial-created records."""
    print_section("CLEANUP")
    
    print("Removing tutorial records...")
    
    # Delete in order of dependencies
    db.records.delete({"labels": ["ANALYSIS"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["FIELD_DEPENDENCY"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["PROPERTY_VERSION"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["MIGRATION_LOG"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["SCHEMA_MIGRATION"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["PREDICTION"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["MODEL"], "where": {"tutorial": True}})
    
    print("   ✓ All tutorial records removed")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the complete schema versioning tutorial."""
    
    print("\n" + "=" * 60)
    print(" SCHEMA VERSIONING STRATEGIES FOR EVOLVING AI APPLICATIONS")
    print(" RushDB Tutorial")
    print("=" * 60)
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\nERROR: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)
    
    db = RushDB(api_key)
    print("\n✓ RushDB client initialized")
    
    all_created = []
    
    try:
        # Run all demonstrations
        created = demonstrate_version_tagging(db)
        all_created.extend(created)
        
        created = demonstrate_migration_records(db)
        all_created.extend(created)
        
        created = demonstrate_rolling_upgrades(db, all_created)
        all_created.extend(created)
        
        created = demonstrate_rollback_pattern(db)
        all_created.extend(created)
        
        created = demonstrate_property_lineage(db)
        all_created.extend(created)
        
        created = demonstrate_schema_evolution(db)
        all_created.extend(created)
        
        # Cleanup
        cleanup_tutorial_data(db)
        
        # Summary
        print_section("SUMMARY")
        print(f"""
        ✓ Tutorial completed successfully!
        
        Patterns demonstrated:
        1. Version Tagging - Attach semantic version metadata to records
        2. Migration Records - Track schema changes as first-class records
        3. Rolling Upgrades - Handle mixed-version data during transitions
        4. Rollback Pattern - Revert to previous schema states
        5. Property Lineage - Track field evolution across versions
        6. Schema Evolution - Complete migration lifecycle
        
        Key concepts:
        - RushDB's zero-schema model enables flexible schema versioning
        - Version metadata allows querying by schema version
        - Transactions ensure atomic migration operations
        - Property relationships track field evolution
        """)
        
    except Exception as e:
        print(f"\n✗ Error during tutorial: {e}")
        if VERBOSE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
