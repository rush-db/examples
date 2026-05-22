#!/usr/bin/env python3
"""
Seed script for AI Pipeline Dependency Tracking tutorial.

This script generates realistic mock data representing an ML pipeline with:
- Datasets (raw, processed, validation)
- Pipeline runs (experiments)
- Model artifacts
- Configuration snapshots
- Preprocessing transforms
- Full dependency relationships

Run this once before main.py to populate RushDB with demo data.
Idempotent: safe to run multiple times.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Label constants
LABEL_RUN = "RUN"
LABEL_DATASET = "DATASET"
LABEL_MODEL = "MODEL"
LABEL_CONFIG = "CONFIG"
LABEL_TRANSFORM = "TRANSFORM"


def get_or_create_record(db, label, merge_by, data):
    """
    Attempt to find existing record by merge_by field.
    If found, return it; otherwise create new.
    This makes the seed script idempotent.
    """
    existing = db.records.find({
        "labels": [label],
        "where": {merge_by: data.get(merge_by)}
    })
    
    if existing.data:
        return existing.data[0]
    
    return db.records.create(label=label, data=data)


def seed_datasets(db):
    """Create dataset records representing raw and processed data."""
    print("\n[1/5] Seeding datasets...")
    
    datasets = {}
    
    # Raw data
    raw_images = get_or_create_record(db, LABEL_DATASET, "name", {
        "name": "raw_images_v1",
        "version": "1.0.0",
        "type": "raw",
        "source": "s3://ml-data/raw/images",
        "size_gb": 50.0,
        "record_count": 50000,
        "created_at": (datetime.now() - timedelta(days=30)).isoformat()
    })
    datasets["raw_images"] = raw_images
    print(f"  ✓ Created dataset: {raw_images.data['name']}")
    
    # Processed datasets
    processed_v1 = get_or_create_record(db, LABEL_DATASET, "name", {
        "name": "image_dataset_v1",
        "version": "1.0.0",
        "type": "processed",
        "source": "s3://ml-data/processed/v1",
        "size_gb": 30.0,
        "record_count": 45000,
        "schema_hash": "abc123",
        "preprocessing": "basic_cleaning",
        "created_at": (datetime.now() - timedelta(days=14)).isoformat()
    })
    datasets["processed_v1"] = processed_v1
    
    # Link processed to raw
    db.records.attach(
        source=processed_v1,
        target=raw_images,
        options={"type": "DERIVED_FROM", "direction": "out"}
    )
    print(f"  ✓ Created dataset: {processed_v1.data['name']}")
    
    # Processed v2 (current)
    processed_v2 = get_or_create_record(db, LABEL_DATASET, "name", {
        "name": "image_dataset_v2",
        "version": "2.0.0",
        "type": "processed",
        "source": "s3://ml-data/processed/v2",
        "size_gb": 35.0,
        "record_count": 10000,
        "schema_hash": "def456",
        "preprocessing": "standard_scaling + augmentation",
        "created_at": (datetime.now() - timedelta(days=2)).isoformat()
    })
    datasets["processed_v2"] = processed_v2
    
    db.records.attach(
        source=processed_v2,
        target=raw_images,
        options={"type": "DERIVED_FROM", "direction": "out"}
    )
    print(f"  ✓ Created dataset: {processed_v2.data['name']}")
    
    # Validation set
    validation = get_or_create_record(db, LABEL_DATASET, "name", {
        "name": "validation_set_v1",
        "version": "1.0.0",
        "type": "validation",
        "source": "s3://ml-data/validation/v1",
        "size_gb": 5.0,
        "record_count": 2000,
        "created_at": (datetime.now() - timedelta(days=30)).isoformat()
    })
    datasets["validation"] = validation
    
    db.records.attach(
        source=validation,
        target=raw_images,
        options={"type": "DERIVED_FROM", "direction": "out"}
    )
    print(f"  ✓ Created dataset: {validation.data['name']}")
    
    return datasets


def seed_transforms(db, datasets):
    """Create preprocessing transform records."""
    print("\n[2/5] Seeding preprocessing transforms...")
    
    transforms = {}
    
    # Basic cleaning transform
    basic_transform = get_or_create_record(db, LABEL_TRANSFORM, "name", {
        "name": "basic_cleaning",
        "type": "preprocessing",
        "parameters": {
            "remove_duplicates": True,
            "normalize_pixels": True,
            "resize_to": [224, 224]
        },
        "created_at": (datetime.now() - timedelta(days=30)).isoformat()
    })
    transforms["basic"] = basic_transform
    
    db.records.attach(
        source=basic_transform,
        target=datasets["raw_images"],
        options={"type": "INPUTS", "direction": "out"}
    )
    db.records.attach(
        source=basic_transform,
        target=datasets["processed_v1"],
        options={"type": "PRODUCES", "direction": "out"}
    )
    print(f"  ✓ Created transform: {basic_transform.data['name']}")
    
    # Advanced preprocessing transform
    advanced_transform = get_or_create_record(db, LABEL_TRANSFORM, "name", {
        "name": "standard_scaling + augmentation",
        "type": "preprocessing",
        "parameters": {
            "remove_duplicates": True,
            "normalize_pixels": True,
            "resize_to": [224, 224],
            "augmentation": {
                "rotation_range": 20,
                "horizontal_flip": True,
                "zoom_range": 0.2,
                "brightness_range": [0.8, 1.2]
            },
            "standardization": {
                "mean": [0.485, 0.456, 0.406],
                "std": [0.229, 0.224, 0.225]
            }
        },
        "created_at": (datetime.now() - timedelta(days=2)).isoformat()
    })
    transforms["advanced"] = advanced_transform
    
    db.records.attach(
        source=advanced_transform,
        target=datasets["raw_images"],
        options={"type": "INPUTS", "direction": "out"}
    )
    db.records.attach(
        source=advanced_transform,
        target=datasets["processed_v2"],
        options={"type": "PRODUCES", "direction": "out"}
    )
    print(f"  ✓ Created transform: {advanced_transform.data['name']}")
    
    return transforms


def seed_configs(db):
    """Create configuration records for different experiment settings."""
    print("\n[3/5] Seeding configurations...")
    
    configs = {}
    
    # Initial baseline config
    baseline_config = get_or_create_record(db, LABEL_CONFIG, "name", {
        "name": "baseline_config_v1",
        "model_type": "resnet50",
        "learning_rate": 0.01,
        "batch_size": 16,
        "epochs": 30,
        "optimizer": "sgd",
        "weight_decay": 0.0001,
        "momentum": 0.9,
        "created_at": (datetime.now() - timedelta(days=15)).isoformat()
    })
    configs["baseline"] = baseline_config
    print(f"  ✓ Created config: {baseline_config.data['name']}")
    
    # Experiment v1 config
    exp_v1_config = get_or_create_record(db, LABEL_CONFIG, "name", {
        "name": "experiment_v1_config",
        "model_type": "resnet50",
        "learning_rate": 0.005,
        "batch_size": 32,
        "epochs": 40,
        "optimizer": "adam",
        "weight_decay": 0.0001,
        "dropout": 0.3,
        "data_augmentation": True,
        "created_at": (datetime.now() - timedelta(days=7)).isoformat()
    })
    configs["exp_v1"] = exp_v1_config
    print(f"  ✓ Created config: {exp_v1_config.data['name']}")
    
    # Experiment v2 config (best performing)
    exp_v2_config = get_or_create_record(db, LABEL_CONFIG, "name", {
        "name": "experiment_v2_config",
        "model_type": "efficientnet_b3",
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 50,
        "optimizer": "adam",
        "weight_decay": 0.0001,
        "dropout": 0.4,
        "data_augmentation": True,
        "label_smoothing": 0.1,
        "warmup_epochs": 5,
        "created_at": (datetime.now() - timedelta(days=2)).isoformat()
    })
    configs["exp_v2"] = exp_v2_config
    print(f"  ✓ Created config: {exp_v2_config.data['name']}")
    
    return configs


def seed_runs(db, datasets, configs, transforms):
    """Create pipeline run records with all dependencies."""
    print("\n[4/5] Seeding pipeline runs...")
    
    runs = {}
    
    # Initial test run
    initial_run = get_or_create_record(db, LABEL_RUN, "name", {
        "name": "initial_test",
        "status": "COMPLETED",
        "duration_seconds": 1800,
        "started_at": (datetime.now() - timedelta(days=16)).isoformat(),
        "completed_at": (datetime.now() - timedelta(days=16, hours=-0.5)).isoformat(),
        "metrics": {
            "val_accuracy": 0.78,
            "val_loss": 0.65,
            "train_time_hours": 0.5
        },
        "git_commit": "a1b2c3d",
        "environment": {
            "python_version": "3.10",
            "cuda_version": "11.8",
            "framework": "pytorch"
        }
    })
    runs["initial"] = initial_run
    
    db.records.attach(
        source=initial_run,
        target=datasets["processed_v1"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=initial_run,
        target=datasets["validation"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=initial_run,
        target=configs["baseline"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=initial_run,
        target=transforms["basic"],
        options={"type": "USED", "direction": "out"}
    )
    print(f"  ✓ Created run: {initial_run.data['name']}")
    
    # Debug run (failed)
    debug_run = get_or_create_record(db, LABEL_RUN, "name", {
        "name": "debug_run",
        "status": "FAILED",
        "duration_seconds": 300,
        "started_at": (datetime.now() - timedelta(days=15)).isoformat(),
        "error": "OutOfMemoryError: CUDA out of memory",
        "git_commit": "e4f5g6h",
        "environment": {
            "python_version": "3.10",
            "cuda_version": "11.8",
            "framework": "pytorch"
        }
    })
    runs["debug"] = debug_run
    
    db.records.attach(
        source=debug_run,
        target=datasets["processed_v1"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=debug_run,
        target=configs["baseline"],
        options={"type": "USED", "direction": "out"}
    )
    print(f"  ✓ Created run: {debug_run.data['name']} (FAILED - expected)")
    
    # Experiment v1 run
    exp_v1_run = get_or_create_record(db, LABEL_RUN, "name", {
        "name": "experiment_v1.0",
        "status": "COMPLETED",
        "duration_seconds": 5400,
        "started_at": (datetime.now() - timedelta(days=7)).isoformat(),
        "completed_at": (datetime.now() - timedelta(days=6, hours=-1.5)).isoformat(),
        "metrics": {
            "val_accuracy": 0.89,
            "val_loss": 0.35,
            "train_time_hours": 1.5
        },
        "git_commit": "i7j8k9l",
        "environment": {
            "python_version": "3.10",
            "cuda_version": "11.8",
            "framework": "pytorch"
        }
    })
    runs["exp_v1"] = exp_v1_run
    
    db.records.attach(
        source=exp_v1_run,
        target=datasets["processed_v1"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=exp_v1_run,
        target=datasets["validation"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=exp_v1_run,
        target=configs["exp_v1"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=exp_v1_run,
        target=transforms["basic"],
        options={"type": "USED", "direction": "out"}
    )
    print(f"  ✓ Created run: {exp_v1_run.data['name']}")
    
    # Baseline run with v2 data
    baseline_run = get_or_create_record(db, LABEL_RUN, "name", {
        "name": "baseline",
        "status": "COMPLETED",
        "duration_seconds": 7200,
        "started_at": (datetime.now() - timedelta(days=2, hours=-2)).isoformat(),
        "completed_at": (datetime.now() - timedelta(days=2, hours=-0.5)).isoformat(),
        "metrics": {
            "val_accuracy": 0.91,
            "val_loss": 0.28,
            "train_time_hours": 2.0
        },
        "git_commit": "m1n2o3p",
        "environment": {
            "python_version": "3.11",
            "cuda_version": "12.1",
            "framework": "pytorch"
        }
    })
    runs["baseline"] = baseline_run
    
    db.records.attach(
        source=baseline_run,
        target=datasets["processed_v2"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=baseline_run,
        target=datasets["validation"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=baseline_run,
        target=configs["baseline"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=baseline_run,
        target=transforms["advanced"],
        options={"type": "USED", "direction": "out"}
    )
    print(f"  ✓ Created run: {baseline_run.data['name']}")
    
    # Experiment v2.1 run (best)
    exp_v2_run = get_or_create_record(db, LABEL_RUN, "name", {
        "name": "experiment_v2.1",
        "status": "COMPLETED",
        "duration_seconds": 10800,
        "started_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "completed_at": (datetime.now() - timedelta(hours=7)).isoformat(),
        "metrics": {
            "val_accuracy": 0.94,
            "val_f1": 0.92,
            "val_loss": 0.18,
            "precision": 0.93,
            "recall": 0.91,
            "train_time_hours": 3.0
        },
        "git_commit": "q4r5s6t",
        "environment": {
            "python_version": "3.11",
            "cuda_version": "12.1",
            "framework": "pytorch"
        }
    })
    runs["exp_v2"] = exp_v2_run
    
    db.records.attach(
        source=exp_v2_run,
        target=datasets["processed_v2"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=exp_v2_run,
        target=datasets["validation"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=exp_v2_run,
        target=configs["exp_v2"],
        options={"type": "USED", "direction": "out"}
    )
    db.records.attach(
        source=exp_v2_run,
        target=transforms["advanced"],
        options={"type": "USED", "direction": "out"}
    )
    print(f"  ✓ Created run: {exp_v2_run.data['name']}")
    
    return runs


def seed_models(db, runs):
    """Create model artifact records linked to their producing runs."""
    print("\n[5/5] Seeding model artifacts...")
    
    models = {}
    
    # Initial model
    initial_model = get_or_create_record(db, LABEL_MODEL, "name", {
        "name": "initial_model",
        "version": "1.0.0",
        "architecture": "resnet50",
        "status": "archived",
        "file_size_mb": 90.5,
        "storage_path": "s3://ml-models/sentiment/initial_model_v1.0.pt",
        "created_at": (datetime.now() - timedelta(days=16)).isoformat(),
        "metrics_summary": {
            "accuracy": 0.78
        }
    })
    models["initial"] = initial_model
    
    db.records.attach(
        source=initial_model,
        target=runs["initial"],
        options={"type": "PRODUCED_BY", "direction": "out"}
    )
    print(f"  ✓ Created model: {initial_model.data['name']}")
    
    # Experiment v1 model
    exp_v1_model = get_or_create_record(db, LABEL_MODEL, "name", {
        "name": "sentiment_classifier_v1",
        "version": "1.0.0",
        "architecture": "resnet50",
        "status": "archived",
        "file_size_mb": 92.3,
        "storage_path": "s3://ml-models/sentiment/classifier_v1.0.pt",
        "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
        "metrics_summary": {
            "accuracy": 0.89,
            "f1": 0.87
        }
    })
    models["exp_v1"] = exp_v1_model
    
    db.records.attach(
        source=exp_v1_model,
        target=runs["exp_v1"],
        options={"type": "PRODUCED_BY", "direction": "out"}
    )
    print(f"  ✓ Created model: {exp_v1_model.data['name']}")
    
    # Baseline v2 model
    baseline_model = get_or_create_record(db, LABEL_MODEL, "name", {
        "name": "baseline_model",
        "version": "2.0.0",
        "architecture": "efficientnet_b3",
        "status": "staging",
        "file_size_mb": 45.2,
        "storage_path": "s3://ml-models/sentiment/baseline_v2.0.pt",
        "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "metrics_summary": {
            "accuracy": 0.91
        }
    })
    models["baseline"] = baseline_model
    
    db.records.attach(
        source=baseline_model,
        target=runs["baseline"],
        options={"type": "PRODUCED_BY", "direction": "out"}
    )
    print(f"  ✓ Created model: {baseline_model.data['name']}")
    
    # Experiment v2 model (best - production)
    exp_v2_model = get_or_create_record(db, LABEL_MODEL, "name", {
        "name": "sentiment_classifier_v2",
        "version": "2.0.0",
        "architecture": "efficientnet_b3",
        "status": "production",
        "file_size_mb": 46.8,
        "storage_path": "s3://ml-models/sentiment/classifier_v2.0.pt",
        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "metrics_summary": {
            "accuracy": 0.94,
            "f1": 0.92,
            "precision": 0.93,
            "recall": 0.91
        }
    })
    models["exp_v2"] = exp_v2_model
    
    db.records.attach(
        source=exp_v2_model,
        target=runs["exp_v2"],
        options={"type": "PRODUCED_BY", "direction": "out"}
    )
    print(f"  ✓ Created model: {exp_v2_model.data['name']}")
    
    return models


def main():
    """Main seed function."""
    print("=" * 50)
    print("AI PIPELINE DEPENDENCY TRACKING - DATA SEEDING")
    print("=" * 50)
    
    # Get API token from environment
    api_token = os.environ.get("RUSHDB_API_TOKEN")
    if not api_token:
        print("\n❌ ERROR: RUSHDB_API_TOKEN not found in environment")
        print("Please create a .env file with your API token:")
        print("  RUSHDB_API_TOKEN=your_token_here")
        sys.exit(1)
    
    # Initialize RushDB client
    print("\nConnecting to RushDB...")
    db = RushDB(api_token)
    print("✓ Connected successfully")
    
    # Check if data already exists
    existing_runs = db.records.find({"labels": [LABEL_RUN], "limit": 1})
    if existing_runs.data:
        print("\n⚠ Data already exists in RushDB.")
        print("Skipping seed to avoid duplicates.")
        print("If you need to reset, clear the project data in RushDB dashboard.")
        return
    
    # Seed all data
    datasets = seed_datasets(db)
    transforms = seed_transforms(db, datasets)
    configs = seed_configs(db)
    runs = seed_runs(db, datasets, configs, transforms)
    models = seed_models(db, runs)
    
    print("\n" + "=" * 50)
    print("✓ SEEDING COMPLETE")
    print("=" * 50)
    print(f"\nCreated:")
    print(f"  - {len(datasets)} datasets")
    print(f"  - {len(transforms)} transforms")
    print(f"  - {len(configs)} configurations")
    print(f"  - {len(runs)} pipeline runs")
    print(f"  - {len(models)} model artifacts")
    print(f"\nRun 'python main.py' to explore the dependency graph!")


if __name__ == "__main__":
    main()
