"""
Seed script for Schema Versioning Tutorial

Generates sample AI model metadata with versioned schemas.
Run this before main.py if you want pre-populated data.

Usage:
    python seed.py
"""

import os
import sys
from datetime import datetime, timedelta
import random

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)

# Sample data configurations
MODELS = [
    {
        "name": "sentiment-analyzer",
        "versions": ["1.0.0", "1.1.0", "2.0.0"],
        "inputFields": ["text"],
        "outputFields_v1": ["sentiment"],
        "outputFields_v2": ["sentiment", "confidence"],
    },
    {
        "name": "entity-extractor",
        "versions": ["1.0.0", "1.2.0", "2.0.0", "2.1.0"],
        "inputFields": ["text", "language"],
        "outputFields_v1": ["entities"],
        "outputFields_v2": ["entities", "confidence", "positions"],
    },
    {
        "name": "text-classifier",
        "versions": ["1.0.0", "2.0.0"],
        "inputFields": ["text", "categories"],
        "outputFields_v1": ["category", "score"],
        "outputFields_v2": ["category", "score", "topK"]],
    },
]

SCHEMA_VERSIONS = ["2023.1", "2023.3", "2024.1"]


def seed_models():
    """Create versioned model records with schema metadata."""
    print("\n[1/4] Seeding AI models with versioned schemas...")
    
    created_models = []
    for i, model_config in enumerate(MODELS):
        for version in model_config["versions"]:
            # Determine schema version based on model version
            if version.startswith("1."):
                schema_version = SCHEMA_VERSIONS[0]
                output_fields = model_config["outputFields_v1"]
            else:
                schema_version = SCHEMA_VERSIONS[-1]
                output_fields = model_config["outputFields_v2"]
            
            created = db.records.create(
                label="MODEL",
                data={
                    "name": f"{model_config['name']}-{version}",
                    "baseName": model_config["name"],
                    "version": version,
                    "schemaVersion": schema_version,
                    "inputFields": model_config["inputFields"],
                    "outputFields": output_fields,
                    "tutorial": True,
                    "seededAt": datetime.utcnow().isoformat(),
                }
            )
            created_models.append(created)
            
            if (len(created_models) % 5) == 0:
                print(f"  Created {len(created_models)} models...")
    
    print(f"  ✓ Created {len(created_models)} model records")
    return created_models


def seed_migrations():
    """Create schema migration records tracking evolution."""
    print("\n[2/4] Seeding schema migration records...")
    
    migrations = [
        {
            "fromVersion": "2023.1",
            "toVersion": "2023.3",
            "description": "Added confidence scores to model outputs",
            "affectedLabels": ["MODEL", "PREDICTION"],
            "addedFields": ["confidence"],
            "deprecatedFields": [],
            "migrationType": "additive",
        },
        {
            "fromVersion": "2023.3",
            "toVersion": "2024.1",
            "description": "Enhanced entity extraction with position tracking",
            "affectedLabels": ["MODEL", "PREDICTION", "ENTITY"],
            "addedFields": ["positions", "topK"],
            "deprecatedFields": ["score"],
            "migrationType": "breaking",
        },
    ]
    
    created_migrations = []
    for i, migration in enumerate(migrations):
        created = db.records.create(
            label="SCHEMA_MIGRATION",
            data={
                **migration,
                "tutorial": True,
                "appliedAt": (datetime.utcnow() - timedelta(days=30 - i * 15)).isoformat(),
                "appliedBy": "migration-bot",
            }
        )
        created_migrations.append(created)
    
    print(f"  ✓ Created {len(created_migrations)} migration records")
    return created_migrations


def seed_predictions(models):
    """Create sample predictions with mixed schema versions."""
    print("\n[3/4] Seeding prediction records (mixed versions)...")
    
    predictions = []
    sample_texts = [
        "The new AI model shows promising results in natural language understanding.",
        "Recent advances in transformer architecture have improved translation quality.",
        "Machine learning models continue to evolve with better efficiency.",
    ]
    
    for i, model in enumerate(models[:6]):  # Use first 6 models
        for text in sample_texts:
            # Mix old and new schema fields based on model version
            schema_v = model.data.get("schemaVersion")
            
            prediction_data = {
                "input": text,
                "modelName": model.data.get("name"),
                "modelVersion": model.data.get("version"),
                "schemaVersion": schema_v,
                "tutorial": True,
            }
            
            # Add version-specific output fields
            if schema_v == "2024.1":
                prediction_data["sentiment"] = random.choice(["positive", "negative", "neutral"])
                prediction_data["confidence"] = round(random.uniform(0.7, 0.99), 3)
            else:
                prediction_data["sentiment"] = random.choice(["positive", "negative", "neutral"])
                prediction_data["score"] = round(random.uniform(0.5, 0.95), 3)
            
            created = db.records.create(label="PREDICTION", data=prediction_data)
            predictions.append(created)
            
            if (len(predictions) % 10) == 0:
                print(f"  Created {len(predictions)} predictions...")
    
    print(f"  ✓ Created {len(predictions)} prediction records")
    return predictions


def cleanup():
    """Remove seeded records (for re-runs)."""
    print("\n[0/4] Cleaning up existing tutorial records...")
    
    db.records.delete({"labels": ["PREDICTION"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["MODEL"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["SCHEMA_MIGRATION"], "where": {"tutorial": True}})
    db.records.delete({"labels": ["MIGRATION_LOG"], "where": {"tutorial": True}})
    
    print("  ✓ Cleanup complete")


def main():
    print("=" * 60)
    print("Schema Versioning Tutorial - Data Seeder")
    print("=" * 60)
    
    # Check if data already exists
    existing = db.records.find({"labels": ["MODEL"], "where": {"tutorial": True}})
    if existing.total > 0:
        print(f"\n⚠ Found {existing.total} existing tutorial records")
        response = input("Clean and re-seed? (y/N): ").strip().lower()
        if response == 'y':
            cleanup()
        else:
            print("Skipping seed - using existing data")
            return
    
    # Run seeding
    models = seed_models()
    migrations = seed_migrations()
    predictions = seed_predictions(models)
    
    print("\n" + "=" * 60)
    print("Seeding complete! Run 'python main.py' to see tutorials.")
    print("=" * 60)


if __name__ == "__main__":
    main()
