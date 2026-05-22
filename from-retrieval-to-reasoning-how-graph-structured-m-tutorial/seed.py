"""
Seed script: Creates the AI agent memory graph with realistic demo data.

This script populates RushDB with:
- CONTEXT records (documents, knowledge base entries)
- OBSERVATION records (agent's perceptions)
- THOUGHT records (reasoning steps)
- ACTION records (decisions made)

All linked via typed relationships for multi-hop traversal.
"""

import os
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Check for API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    exit(1)

db = RushDB(api_key)

# Domain knowledge for AI/ML concepts
ML_TOPICS = [
    "neural network optimization",
    "transformer architecture",
    "backpropagation mechanics",
    "gradient descent variants",
    "regularization techniques",
    "attention mechanism explained",
]

CONTEXT_DOCUMENTS = [
    {
        "title": "Dropout as Regularization",
        "content": "Dropout is a technique where neurons are randomly dropped during training to prevent co-adaptation. This effectively trains an ensemble of sub-networks and improves generalization.",
        "tags": ["regularization", "neural-networks", "training"],
    },
    {
        "title": "Learning Rate Scheduling",
        "content": "Adaptive learning rate methods like Adam combine momentum with RMSprop. Learning rate warmup helps early training stability by gradually increasing the learning rate.",
        "tags": ["optimization", "training", "hyperparameters"],
    },
    {
        "title": "Transformer Self-Attention",
        "content": "Self-attention computes pairwise relevance between all positions in a sequence. The scaled dot-product attention formula: softmax(QK^T / sqrt(d_k)) V enables parallel computation.",
        "tags": ["transformers", "attention", "architecture"],
    },
    {
        "title": "Batch Normalization Benefits",
        "content": "BatchNorm normalizes layer inputs to have zero mean and unit variance. This reduces internal covariate shift, allows higher learning rates, and has a mild regularization effect.",
        "tags": ["normalization", "training", "architecture"],
    },
    {
        "title": "Gradient Clipping Strategies",
        "content": "Gradient clipping prevents exploding gradients by capping their norm. Typical thresholds are 1.0 or 5.0. Essential for RNNs and very deep networks.",
        "tags": ["optimization", "gradients", "stability"],
    },
    {
        "title": "Weight Initialization Methods",
        "content": "Xavier/Glorot initialization sets weights based on fan-in and fan-out. He initialization is better for ReLU networks. Proper initialization prevents vanishing/exploding gradients.",
        "tags": ["initialization", "neural-networks", "architecture"],
    },
    {
        "title": "Early Stopping Criterion",
        "content": "Monitor validation loss and stop when no improvement for N epochs (patience). This prevents overfitting and reduces training time. Often combined with model checkpointing.",
        "tags": ["regularization", "training", "validation"],
    },
    {
        "title": "Cross-Entropy Loss Properties",
        "content": "Cross-entropy measures difference between predicted and true distributions. For classification, it penalizes confident wrong predictions more than log loss from uncertain ones.",
        "tags": ["loss-functions", "classification", "training"],
    },
]

OBSERVATIONS = [
    {"content": "Training loss decreasing slowly after epoch 10", "priority": "medium", "source": "metrics"},
    {"content": "Validation accuracy plateauing at 87%", "priority": "high", "source": "metrics"},
    {"content": "GPU utilization at 45% during training", "priority": "low", "source": "system"},
    {"content": "Gradient norm spike detected in layer 3", "priority": "high", "source": "metrics"},
    {"content": "Model predictions uncertain for minority class", "priority": "medium", "source": "evaluation"},
    {"content": "Learning rate decay not applied correctly", "priority": "high", "source": "config"},
    {"content": "Current batch_size=16, memory usage normal", "priority": "low", "source": "system"},
    {"content": "Feature importance: encoder layers most impactful", "priority": "medium", "source": "analysis"},
]

THOUGHTS = [
    {"content": "Slow loss decrease indicates possible learning rate too low", "type": "diagnostic", "confidence": 0.7},
    {"content": "Plateau suggests model approaching capacity limit", "type": "diagnostic", "confidence": 0.6},
    {"content": "Low GPU utilization suggests batch size could increase", "type": "optimization", "confidence": 0.8},
    {"content": "Gradient spikes may indicate exploding gradient problem", "type": "diagnostic", "confidence": 0.85},
    {"content": "Class imbalance affecting prediction confidence", "type": "diagnostic", "confidence": 0.75},
    {"content": "Learning rate schedule needs adjustment", "type": "remediation", "confidence": 0.9},
    {"content": "Increasing batch size to 32 may improve GPU utilization", "type": "optimization", "confidence": 0.85},
    {"content": "Add dropout to prevent overfitting on encoder layers", "type": "remediation", "confidence": 0.8},
]

ACTIONS = [
    {"content": "Increase learning rate from 0.001 to 0.003", "tool": "hyperparameter_update", "status": "applied"},
    {"content": "Apply cosine annealing learning rate schedule", "tool": "scheduler_update", "status": "applied"},
    {"content": "Set batch_size=32, monitor GPU utilization", "tool": "batch_size_change", "status": "applied"},
    {"content": "Add gradient clipping with threshold 1.0", "tool": "gradient_clipping", "status": "applied"},
    {"content": "Apply class weights to loss function", "tool": "loss_modification", "status": "pending"},
    {"content": "Add 0.2 dropout after encoder layers", "tool": "architecture_change", "status": "planned"},
]


def clear_existing_data():
    """Remove all existing records of these labels."""
    labels = ["CONTEXT", "OBSERVATION", "THOUGHT", "ACTION"]
    for label in labels:
        result = db.records.find({"labels": [label], "limit": 1000})
        if result.data:
            ids = [r.id for r in result.data]
            for record_id in ids:
                db.records.delete(record_id=record_id)
    print("  Cleared existing records")


def create_vector_index():
    """Create vector index for semantic search on context documents."""
    try:
        # Check if index already exists
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            if idx["label"] == "CONTEXT" and idx["propertyName"] == "content":
                print("  Vector index already exists")
                return
        
        # Create managed index (server embeds)
        result = db.ai.indexes.create({
            "label": "CONTEXT",
            "propertyName": "content",
            "sourceType": "managed"
        })
        print("  Created vector index for CONTEXT.content")
    except Exception as e:
        print(f"  Index creation note: {e}")


def seed_context_records():
    """Create CONTEXT records with embedded vectors."""
    print("  Creating CONTEXT records...")
    records = []
    for i, doc in enumerate(CONTEXT_DOCUMENTS):
        record = db.records.create(
            label="CONTEXT",
            data={
                "title": doc["title"],
                "content": doc["content"],
                "tags": doc["tags"],
                "indexed_at": "2024-01-15T10:00:00Z"
            }
        )
        records.append(record)
        if (i + 1) % 100 == 0:
            print(f"    Created {i + 1} context records...")
    print(f"  Created {len(records)} CONTEXT records")
    return records


def seed_observation_records():
    """Create OBSERVATION records."""
    print("  Creating OBSERVATION records...")
    records = []
    for obs in OBSERVATIONS:
        record = db.records.create(
            label="OBSERVATION",
            data={
                "content": obs["content"],
                "priority": obs["priority"],
                "source": obs["source"],
                "observed_at": "2024-01-15T12:00:00Z"
            }
        )
        records.append(record)
    print(f"  Created {len(records)} OBSERVATION records")
    return records


def seed_thought_records():
    """Create THOUGHT records."""
    print("  Creating THOUGHT records...")
    records = []
    for thought in THOUGHTS:
        record = db.records.create(
            label="THOUGHT",
            data={
                "content": thought["content"],
                "type": thought["type"],
                "confidence": thought["confidence"],
                "reasoned_at": "2024-01-15T13:00:00Z"
            }
        )
        records.append(record)
    print(f"  Created {len(records)} THOUGHT records")
    return records


def seed_action_records():
    """Create ACTION records."""
    print("  Creating ACTION records...")
    records = []
    for action in ACTIONS:
        record = db.records.create(
            label="ACTION",
            data={
                "content": action["content"],
                "tool": action["tool"],
                "status": action["status"],
                "decided_at": "2024-01-15T14:00:00Z"
            }
        )
        records.append(record)
    print(f"  Created {len(records)} ACTION records")
    return records


def create_reasoning_graph(observations, thoughts, actions, contexts):
    """
    Create the reasoning graph with typed relationships.
    
    Relationships:
    - OBSERVATION --[DERIVED_FROM]--> CONTEXT
    - THOUGHT --[REASONED_ABOUT]--> OBSERVATION
    - THOUGHT --[BASED_ON]--> CONTEXT
    - ACTION --[CAUSED_BY]--> THOUGHT
    - ACTION --[ADDRESSES]--> OBSERVATION
    """
    print("  Creating reasoning graph relationships...")
    
    # Link observations to relevant context
    for obs in observations:
        # Find related context by tags/keywords
        obs_content = obs.data.get("content", "").lower()
        for ctx in contexts:
            ctx_content = ctx.data.get("content", "").lower()
            if any(word in ctx_content for word in obs_content.split() if len(word) > 4):
                db.records.attach(
                    source=obs,
                    target=ctx,
                    options={"type": "DERIVED_FROM", "direction": "out"}
                )
    
    # Link thoughts to observations (reasoning chain)
    for i, thought in enumerate(thoughts):
        # Match by type and confidence
        for obs in observations:
            if obs.data.get("priority") == "high":
                db.records.attach(
                    source=thought,
                    target=obs,
                    options={"type": "REASONED_ABOUT", "direction": "out"}
                )
                break
        
        # Link to relevant context
        for ctx in contexts:
            if i % 2 == 0 and i // 2 < len(contexts):
                db.records.attach(
                    source=thought,
                    target=contexts[i // 2],
                    options={"type": "BASED_ON", "direction": "out"}
                )
                break
    
    # Link actions to thoughts
    for action in actions:
        for thought in thoughts:
            if thought.data.get("type") == "remediation":
                db.records.attach(
                    source=action,
                    target=thought,
                    options={"type": "CAUSED_BY", "direction": "out"}
                )
                break
        
        # Link actions to observations they address
        for obs in observations:
            if obs.data.get("priority") == "high":
                db.records.attach(
                    source=action,
                    target=obs,
                    options={"type": "ADDRESSES", "direction": "out"}
                )
                break
    
    print("  Created reasoning graph")


def main():
    print("\n=== Seeding AI Agent Memory Graph ===\n")
    
    # Check if already seeded
    existing = db.records.find({"labels": ["CONTEXT"], "limit": 1})
    if existing.data:
        response = input("Memory already contains records. Re-seed? (y/N): ")
        if response.lower() != 'y':
            print("Seeding cancelled")
            return
        clear_existing_data()
    
    print("\n[1/5] Setting up vector index...")
    create_vector_index()
    
    print("\n[2/5] Creating CONTEXT records...")
    contexts = seed_context_records()
    
    print("\n[3/5] Creating OBSERVATION records...")
    observations = seed_observation_records()
    
    print("\n[4/5] Creating THOUGHT records...")
    thoughts = seed_thought_records()
    
    print("\n[5/5] Creating ACTION records and graph...")
    actions = seed_action_records()
    create_reasoning_graph(observations, thoughts, actions, contexts)
    
    print("\n=== Seeding Complete ===\n")
    print(f"Created {len(contexts)} CONTEXT, {len(observations)} OBSERVATION,")
    print(f"             {len(thoughts)} THOUGHT, {len(actions)} ACTION records")
    print("\nRun 'python main.py' to explore the graph\n")


if __name__ == "__main__":
    main()
