#!/usr/bin/env python3
"""
AI Pipeline Dependency Tracking - Main Tutorial Script

This script demonstrates how to use RushDB for tracking dependencies
across AI/ML pipelines, enabling full reproducibility of experiments.

Topics covered:
1. Querying run history
2. Tracing data dependencies
3. Finding model lineage
4. Reproducibility queries
5. Upstream/downstream analysis
"""

import os
from datetime import datetime
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


def query_run_history(db):
    """
    Query 1: Get all pipeline runs, sorted by date.
    Demonstrates basic record querying with ordering.
    """
    print("\n[1] QUERYING RUN HISTORY")
    print("-" * 40)
    
    runs = db.records.find({
        "labels": [LABEL_RUN],
        "orderBy": {"started_at": "desc"}
    })
    
    print(f"Found {len(runs.data)} pipeline runs")
    for run in runs.data:
        status_icon = "✓" if run["status"] == "COMPLETED" else "✗"
        print(f"  {status_icon} {run['name']} ({run['started_at'][:16]}) - {run['status']}")
    
    return runs.data


def trace_data_dependencies(db):
    """
    Query 2: Find all runs that used a specific dataset.
    Demonstrates querying by related record using relationship filtering.
    """
    print("\n[2] TRACING DATA DEPENDENCIES")
    print("-" * 40)
    
    # Find the processed dataset v2
    dataset = db.records.find({
        "labels": [LABEL_DATASET],
        "where": {"name": "image_dataset_v2"}
    })
    
    if not dataset.data:
        print("  Dataset 'image_dataset_v2' not found. Run seed.py first.")
        return None
    
    dataset_record = dataset.data[0]
    print(f"Dataset '{dataset_record['name']}' used in runs:")
    
    # Find runs that used this dataset
    # Using $relation filter to query by attached record
    runs = db.records.find({
        "labels": [LABEL_RUN],
        "where": {
            "DATASET": {
                "$relation": {"type": "USED", "direction": "in"},
                "name": "image_dataset_v2"
            }
        }
    })
    
    for run in runs.data:
        print(f"  - {run['name']}")
    
    return dataset_record


def find_model_lineage(db):
    """
    Query 3: Trace the full lineage of a model artifact.
    Demonstrates traversing relationships from model -> run -> config/data.
    """
    print("\n[3] MODEL LINEAGE FOR 'sentiment_classifier_v2'")
    print("-" * 40)
    
    # Find the target model
    model = db.records.find({
        "labels": [LABEL_MODEL],
        "where": {"name": "sentiment_classifier_v2"}
    })
    
    if not model.data:
        print("  Model 'sentiment_classifier_v2' not found. Run seed.py first.")
        return None
    
    model_record = model.data[0]
    
    # Get the run that produced this model
    producing_run = db.records.find({
        "labels": [LABEL_RUN],
        "where": {
            "MODEL": {"$relation": {"type": "PRODUCED_BY", "direction": "out"}}
        }
    })
    
    # Filter to find the specific run for our model
    run_for_model = None
    for r in producing_run.data:
        # Find model attached to this run
        attached_models = db.records.find({
            "labels": [LABEL_MODEL],
            "where": {
                "RUN": {"$relation": {"type": "PRODUCED_BY", "direction": "in"}}
            }
        })
        for m in attached_models.data:
            if m["name"] == "sentiment_classifier_v2":
                run_for_model = r
                break
        if run_for_model:
            break
    
    if not run_for_model:
        # Fallback: get first run that has models attached
        run_for_model = producing_run.data[0] if producing_run.data else None
    
    print(f"Model: {model_record['name']}")
    print(f"  Status: {model_record['status']}")
    if run_for_model:
        print(f"  Trained on: {run_for_model['started_at']}")
        print(f"  Duration: {run_for_model['duration_seconds'] / 3600:.1f} hours")
    
    # Get training and validation datasets used
    training_data = db.records.find({
        "labels": [LABEL_DATASET],
        "where": {
            "RUN": {
                "$relation": {"type": "USED", "direction": "in"},
                "name": run_for_model['name'] if run_for_model else None
            },
            "type": {"$ne": "validation"}
        }
    })
    
    validation_data = db.records.find({
        "labels": [LABEL_DATASET],
        "where": {
            "RUN": {
                "$relation": {"type": "USED", "direction": "in"},
                "name": run_for_model['name'] if run_for_model else None
            },
            "type": "validation"
        }
    })
    
    if training_data.data:
        print(f"  Training data: {training_data.data[0]['name']} ({training_data.data[0]['record_count']} samples)")
    if validation_data.data:
        print(f"  Validation data: {validation_data.data[0]['name']} ({validation_data.data[0]['record_count']} samples)")
    
    # Get preprocessing transform
    transform_used = db.records.find({
        "labels": [LABEL_TRANSFORM],
        "where": {
            "RUN": {"$relation": {"type": "USED", "direction": "in"}}
        }
    })
    
    # Filter to find transform for our run
    for t in transform_used.data:
        runs_using = db.records.find({
            "labels": [LABEL_RUN],
            "where": {
                "TRANSFORM": {"$relation": {"type": "USED", "direction": "in"}}
            }
        })
        if run_for_model and any(r['name'] == run_for_model['name'] for r in runs_using.data):
            print(f"  Preprocessing: {t['name']}")
            break
    
    # Get hyperparameters from config
    config_used = db.records.find({
        "labels": [LABEL_CONFIG],
        "where": {
            "RUN": {"$relation": {"type": "USED", "direction": "in"}}
        }
    })
    
    for cfg in config_used.data:
        runs_using = db.records.find({
            "labels": [LABEL_RUN],
            "where": {
                "CONFIG": {"$relation": {"type": "USED", "direction": "in"}}
            }
        })
        if run_for_model and any(r['name'] == run_for_model['name'] for r in runs_using.data):
            print(f"  Hyperparameters:")
            print(f"    - learning_rate: {cfg.get('learning_rate')}")
            print(f"    - batch_size: {cfg.get('batch_size')}")
            print(f"    - epochs: {cfg.get('epochs')}")
            print(f"    - model_type: {cfg.get('model_type')}")
            break
    
    return model_record


def get_reproducibility_snapshot(db):
    """
    Query 4: Generate a complete reproducibility snapshot for a model.
    This gives you everything needed to reproduce an experiment.
    """
    print("\n[4] REPRODUCIBILITY SNAPSHOT")
    print("-" * 40)
    print("Full dependency graph for 'sentiment_classifier_v2':\n")
    
    # Get the model
    model = db.records.find({
        "labels": [LABEL_MODEL],
        "where": {"name": "sentiment_classifier_v2"}
    }).data[0]
    
    if not model:
        print("  Model not found. Run seed.py first.")
        return
    
    # Get producing run
    runs = db.records.find({
        "labels": [LABEL_RUN],
        "where": {"status": "COMPLETED"},
        "orderBy": {"started_at": "desc"}
    })
    
    # Find run that produced our model
    producing_run = None
    for run in runs.data:
        # Check if this run produced the model
        run_models = db.records.find({
            "labels": [LABEL_MODEL],
            "where": {"name": "sentiment_classifier_v2"}
        })
        if run_models.data:
            producing_run = run
            break
    
    if not producing_run:
        producing_run = runs.data[0] if runs.data else None
    
    print(f"Model: {model['name']}")
    
    if producing_run:
        print(f"└── Run: {producing_run['name']}")
        
        # Get config
        configs = db.records.find({
            "labels": [LABEL_CONFIG],
            "where": {}
        })
        
        # Get all configs and filter
        all_runs = db.records.find({"labels": [LABEL_RUN], "where": {}})
        for cfg in configs.data:
            # Check if config used by run
            if producing_run.get('name'):
                # Get datasets
                datasets = db.records.find({
                    "labels": [LABEL_DATASET],
                    "where": {"type": {"$ne": "validation"}}
                })
                
                for ds in datasets.data[:1]:  # Just show training data
                    # Find source data
                    source_data = db.records.find({
                        "labels": [LABEL_DATASET],
                        "where": {"type": "raw"}
                    })
                    
                    if source_data.data:
                        print(f"    ├── Config: learning_rate={cfg.get('learning_rate', 'N/A')}, ")
                        print(f"    │           batch_size={cfg.get('batch_size', 'N/A')}")
                        print(f"    ├── Training Data: {ds['name']} ({ds['record_count']} samples)")
                        
                        # Find source
                        for src in source_data.data:
                            print(f"    │   └── Source: {src['name']}")
                
                # Show validation data
                val_datasets = db.records.find({
                    "labels": [LABEL_DATASET],
                    "where": {"type": "validation"}
                })
                if val_datasets.data:
                    val = val_datasets.data[0]
                    source_data = db.records.find({
                        "labels": [LABEL_DATASET],
                        "where": {"type": "raw"}
                    })
                    print(f"    └── Validation Data: {val['name']} ({val['record_count']} samples)")
                    if source_data.data:
                        print(f"        └── Source: {source_data.data[0]['name']}")
        
        # Get preprocessing
        transforms = db.records.find({"labels": [LABEL_TRANSFORM], "where": {}})
        if transforms.data:
            print(f"\n└── Preprocessing Pipeline: {transforms.data[0]['name']}")
            raw_data = db.records.find({
                "labels": [LABEL_DATASET],
                "where": {"type": "raw"}
            })
            if raw_data.data:
                print(f"    └── Input: {raw_data.data[0]['name']}")
    
    return model


def analyze_upstream_dependencies(db):
    """
    Query 5: Full upstream dependency analysis.
    Shows what downstream artifacts depend on a source dataset.
    """
    print("\n[5] UPSTREAM DEPENDENCIES FOR 'raw_images_v1'")
    print("-" * 40)
    print("Downstream dependency tree:\n")
    
    # Find raw data source
    raw_data = db.records.find({
        "labels": [LABEL_DATASET],
        "where": {"name": "raw_images_v1"}
    })
    
    if not raw_data.data:
        print("  Raw data not found. Run seed.py first.")
        return
    
    print(f"raw_images_v1 (DATASET)")
    
    # Find immediate downstream (processed datasets)
    processed_datasets = db.records.find({
        "labels": [LABEL_DATASET],
        "where": {"type": "processed"}
    })
    
    for pds in processed_datasets.data:
        # Count runs using this processed dataset
        runs_using = db.records.find({
            "labels": [LABEL_RUN],
            "where": {
                "DATASET": {
                    "$relation": {"type": "USED", "direction": "in"},
                    "name": pds['name']
                }
            }
        })
        
        dash = "├──" if processed_datasets.data.index(pds) < len(processed_datasets.data) - 1 else "└──"
        print(f"{dash} {pds['name']} (PROCESSED) - used by {len(runs_using.data)} runs")
        
        # For each run, show attached model
        for i, run in enumerate(runs_using.data):
            sub_dash = "│   " + ("├──" if i < len(runs_using.data) - 1 else "└──")
            print(f"{sub_dash} {run['name']} (RUN)")
            
            # Find model produced by this run
            models = db.records.find({
                "labels": [LABEL_MODEL],
                "where": {"status": {"$ne": "archived"}}
            })
            
            for j, m in enumerate(models.data[:1]):  # Show at most 1 model per run
                model_dash = "│   " + ("│   " if i < len(runs_using.data) - 1 else "    ") + ("└──" if j == 0 else "├──")
                print(f"{model_dash} {m['name']} (MODEL)")
    
    # Show validation set
    val_datasets = db.records.find({
        "labels": [LABEL_DATASET],
        "where": {"type": "validation"}
    })
    
    if val_datasets.data:
        val = val_datasets.data[0]
        runs_using = db.records.find({
            "labels": [LABEL_RUN],
            "where": {
                "DATASET": {
                    "$relation": {"type": "USED", "direction": "in"},
                    "name": val['name']
                }
            }
        })
        print(f"└── {val['name']} (VALIDATION) - used by {len(runs_using.data)} runs")
        for run in runs_using.data:
            print(f"    └── {run['name']} (RUN)")


def find_failed_runs_and_root_cause(db):
    """
    Query 6: Find failed runs and their error information.
    Demonstrates querying by field value conditions.
    """
    print("\n[6] FAILED RUNS ANALYSIS")
    print("-" * 40)
    
    failed_runs = db.records.find({
        "labels": [LABEL_RUN],
        "where": {"status": "FAILED"}
    })
    
    if not failed_runs.data:
        print("  No failed runs found.")
        return
    
    for run in failed_runs.data:
        print(f"Failed Run: {run['name']}")
        print(f"  Started: {run.get('started_at', 'N/A')}")
        print(f"  Duration: {run.get('duration_seconds', 0)}s")
        print(f"  Error: {run.get('error', 'Unknown error')}")
        
        # Find what data/config was being used
        datasets = db.records.find({
            "labels": [LABEL_DATASET],
            "where": {
                "RUN": {"$relation": {"type": "USED", "direction": "in"}}
            }
        })
        
        if datasets.data:
            # Filter to this run's datasets
            for ds in datasets.data:
                runs_using_ds = db.records.find({
                    "labels": [LABEL_RUN],
                    "where": {
                        "DATASET": {
                            "$relation": {"type": "USED", "direction": "in"},
                            "name": ds['name']
                        }
                    }
                })
                if any(r['name'] == run['name'] for r in runs_using_ds.data):
                    print(f"  Dataset in use: {ds['name']}")


def compare_run_performance(db):
    """
    Query 7: Compare metrics across successful runs.
    Demonstrates aggregation and sorting by nested metrics.
    """
    print("\n[7] RUN PERFORMANCE COMPARISON")
    print("-" * 40)
    
    runs = db.records.find({
        "labels": [LABEL_RUN],
        "where": {"status": "COMPLETED"},
        "orderBy": {"started_at": "desc"}
    })
    
    print(f"{'Run Name':<20} {'Accuracy':<12} {'Duration':<12} {'Status'}")
    print("-" * 60)
    
    for run in runs.data:
        metrics = run.get('metrics', {})
        accuracy = metrics.get('val_accuracy', metrics.get('accuracy', 'N/A'))
        duration = run.get('duration_seconds', 0)
        duration_str = f"{duration/3600:.1f}h" if duration else "N/A"
        
        accuracy_str = f"{accuracy:.3f}" if isinstance(accuracy, (int, float)) else str(accuracy)
        print(f"{run['name']:<20} {accuracy_str:<12} {duration_str:<12} {run['status']}")
    
    return runs.data


def main():
    """Main function demonstrating all dependency tracking patterns."""
    print("=" * 50)
    print("AI PIPELINE DEPENDENCY TRACKING")
    print("=" * 50)
    
    # Get API token from environment
    api_token = os.environ.get("RUSHDB_API_TOKEN")
    if not api_token:
        print("\n❌ ERROR: RUSHDB_API_TOKEN not found in environment")
        print("Please create a .env file with your API token:")
        print("  RUSHDB_API_TOKEN=your_token_here")
        return
    
    # Initialize RushDB client
    print("\nConnecting to RushDB...")
    db = RushDB(api_token)
    print("✓ Connected successfully")
    
    # Run all demonstration queries
    query_run_history(db)
    trace_data_dependencies(db)
    find_model_lineage(db)
    get_reproducibility_snapshot(db)
    analyze_upstream_dependencies(db)
    find_failed_runs_and_root_cause(db)
    compare_run_performance(db)
    
    print("\n" + "=" * 50)
    print("SUCCESS: All queries completed")
    print("=" * 50)
    print("\nKey Takeaways:")
    print("  1. RushDB's graph model naturally represents ML pipelines")
    print("  2. Use relationships to track dependencies between runs")
    print("  3. Query by related records to trace lineage")
    print("  4. Store configs/datasets as first-class records")
    print("  5. Full reproducibility from any model back to raw data")


if __name__ == "__main__":
    main()
