# Dependency Tracking for AI Pipeline Reproducibility

A comprehensive tutorial demonstrating how to use RushDB's property graph model to track dependencies across AI/ML pipelines, ensuring full reproducibility of machine learning experiments.

## What This Demonstrates

- **Pipeline Run Tracking**: Record every experiment execution with its parameters, duration, and outcomes
- **Data Lineage**: Track which datasets were used in which runs, including version information
- **Model Artifact Dependencies**: Connect models to the exact data, preprocessing, and hyperparameters that produced them
- **Configuration Management**: Store and version configuration snapshots linked to pipeline executions
- **Graph-Based Lineage Queries**: Use RushDB's relationship traversal to trace dependencies backward and forward
- **Reproducibility Auditing**: Query exact dependencies for any model to reproduce results

## Why RushDB for This Use Case?

RushDB's property graph architecture maps naturally to dependency tracking:

| AI Pipeline Concept | RushDB Representation |
|---------------------|----------------------|
| Experiment Run | `RUN` record with timestamp, status, metrics |
| Dataset | `DATASET` record with version, schema hash |
| Model Artifact | `MODEL` record linked to training run |
| Configuration | `CONFIG` record snapshot |
| Preprocessing | `TRANSFORM` record with parameters |
| Dependencies | Typed relationships (`USED`, `PRODUCED`, `DEPENDS_ON`) |

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier at https://rushdb.com)

## Setup

```bash
# Clone the repository
git clone https://github.com/rush-db/examples
cd dependency-tracking-for-ai-pipeline-reproducibilit-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

## Getting Your RushDB API Token

1. Sign up at https://rushdb.com
2. Create a new project
3. Navigate to Settings > API Tokens
4. Copy your token to `.env` as `RUSHDB_API_TOKEN`

## Running the Example

### Step 1: Seed Mock Data

This creates a realistic AI pipeline scenario with multiple runs, datasets, models, and configurations:

```bash
python seed.py
```

The seed script generates:
- 3 datasets (raw, processed, augmented)
- 5 pipeline run records with varying configurations
- 4 model artifacts linked to successful runs
- Configuration snapshots for each run
- Transform/preprocessing records
- Full dependency relationships between all entities

### Step 2: Run the Tutorial

```bash
python main.py
```

This demonstrates:

1. **Querying Run History** - Find all experiments
2. **Tracing Data Dependencies** - Which runs used which datasets
3. **Finding Model Lineage** - What produced a specific model
4. **Reproducibility Queries** - Get exact dependencies for any model
5. **Upstream/Downstream Analysis** - Trace full dependency trees

## Expected Output

```
========================================
AI PIPELINE DEPENDENCY TRACKING
========================================

[1] QUERYING RUN HISTORY
------------------------
Found 5 pipeline runs
  - experiment_v2.1 (2024-01-15T10:30:00) - COMPLETED
  - baseline (2024-01-15T09:00:00) - COMPLETED
  - experiment_v1.0 (2024-01-14T16:45:00) - COMPLETED
  - debug_run (2024-01-14T14:00:00) - FAILED
  - initial_test (2024-01-13T11:00:00) - COMPLETED

[2] TRACING DATA DEPENDENCIES
------------------------------
Dataset 'image_dataset_v2' used in runs:
  - experiment_v2.1
  - baseline

[3] MODEL LINEAGE FOR 'sentiment_classifier_v2'
-----------------------------------------------
Model: sentiment_classifier_v2
  Status: production
  Trained on: 2024-01-15T10:30:00
  Training data: image_dataset_v2 (10000 samples)
  Validation data: validation_set_v1 (2000 samples)
  Preprocessing: standard_scaling + augmentation
  Hyperparameters:
    - learning_rate: 0.001
    - batch_size: 32
    - epochs: 50

[4] REPRODUCIBILITY SNAPSHOT
----------------------------
Full dependency graph for 'sentiment_classifier_v2':

Model: sentiment_classifier_v2
├── Run: experiment_v2.1
│   ├── Config: {'learning_rate': 0.001, 'batch_size': 32, ...}
│   ├── Training Data: image_dataset_v2
│   │   └── Source: raw_images_v1
│   └── Validation Data: validation_set_v1
│       └── Source: raw_images_v1
└── Preprocessing Pipeline: standard_scaling + augmentation
    └── Input: raw_images_v1

[5] UPSTREAM DEPENDENCIES FOR 'raw_images_v1'
---------------------------------------------
Downstream dependency tree:

raw_images_v1 (DATASET)
├── image_dataset_v1 (PROCESSED) - used by 1 runs
│   └── experiment_v1.0 (RUN)
│       └── sentiment_classifier_v1 (MODEL)
├── image_dataset_v2 (PROCESSED) - used by 2 runs
│   ├── experiment_v2.1 (RUN)
│   │   └── sentiment_classifier_v2 (MODEL)
│   └── baseline (RUN)
│       └── baseline_model (MODEL)
└── validation_set_v1 (PROCESSED) - used by 3 runs
    ├── initial_test (RUN)
    ├── experiment_v1.0 (RUN)
    └── experiment_v2.1 (RUN)

========================================
SUCCESS: All queries completed
========================================
```

## Project Structure

```
dependency-tracking-for-ai-pipeline-reproducibilit-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py            # Mock data generation
└── main.py            # Main tutorial script
```

## Key RushDB Patterns Used

### Creating Records with Relationships

```sdk
# Create a run record
run = db.records.create(
    label="RUN",
    data={
        "name": "experiment_v2.1",
        "status": "COMPLETED",
        "duration_seconds": 3600,
        "metrics": {"accuracy": 0.94, "f1": 0.92}
    }
)

# Link dataset to run
db.records.attach(
    source=run,
    target=dataset,
    options={"type": "USED"}
)

# Link model to run
db.records.attach(
    source=model,
    target=run,
    options={"type": "PRODUCED_BY"}
)
___SPLIT___
// Create a run record
const run = await db.records.create({
    label: "RUN",
    data: {
        name: "experiment_v2.1",
        status: "COMPLETED",
        durationSeconds: 3600,
        metrics: { accuracy: 0.94, f1: 0.92 }
    }
})

// Link dataset to run
await db.records.attach({
    source: run,
    target: dataset,
    options: { type: "USED" }
})

// Link model to run
await db.records.attach({
    source: model,
    target: run,
    options: { type: "PRODUCED_BY" }
})
```

### Querying by Related Record

```sdk
# Find all runs that used a specific dataset
runs = db.records.find({
    "labels": ["RUN"],
    "where": {
        "DATASET": {"$relation": {"type": "USED", "direction": "in"}}
    }
})
___SPLIT___
// Find all runs that used a specific dataset
const runs = await db.records.find({
    labels: ["RUN"],
    where: {
        "DATASET": { "$relation": { type: "USED", direction: "in" } }
    }
})
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdk/python)
- [Graph-Based Data Modeling](https://docs.rushdb.com/concepts/property-graph)

## License

MIT
