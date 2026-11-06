"""
Seed script for streaming token generation tutorial.

Creates a knowledge graph with research documents and their citation relationships.
Safe to run multiple times - uses upsert to prevent duplicates.
"""

import os
import json
from pathlib import Path
from rushdb import RushDB

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Sample documents - research papers on AI/ML topics
DOCUMENTS = [
    {
        "id": "paper-001",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani", "Shazeer", "Parmar", "et al."],
        "year": 2017,
        "venue": "NeurIPS",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
        "key_claims": [
            "Self-attention mechanism eliminates recurrence",
            "Multi-head attention enables parallel processing",
            "Positional encoding preserves sequence order"
        ],
        "citation_count": 89234
    },
    {
        "id": "paper-002",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": ["Devlin", "Chang", "Lee", "Toutanova"],
        "year": 2018,
        "venue": "NAACL",
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
        "key_claims": [
            "Bidirectional pre-training captures context from both directions",
            "Masked language model enables deep context understanding",
            "Fine-tuning achieves state-of-the-art on 11 NLP tasks"
        ],
        "citation_count": 72341
    },
    {
        "id": "paper-003",
        "title": "GPT-3: Language Models are Few-Shot Learners",
        "authors": ["Brown", "Mann", "Ryder", "et al."],
        "year": 2020,
        "venue": "NeurIPS",
        "abstract": "Recent work has demonstrated substantial gains on many NLP tasks by pre-training on a large corpus of text followed by fine-tuning. We show that scaling up language models greatly improves task-agnostic, few-shot performance.",
        "key_claims": [
            "175B parameters enables few-shot learning",
            "In-context learning eliminates gradient updates",
            "Scales predictably with model size"
        ],
        "citation_count": 15678
    },
    {
        "id": "paper-004",
        "title": "The Illustrated Transformer",
        "authors": ["Alammar"],
        "year": 2018,
        "venue": "Blog",
        "abstract": "A visual and intuitive guide to the Transformer architecture introduced in 'Attention Is All You Need'.",
        "key_claims": [
            "Visual explanation of attention mechanisms",
            "Step-by-step transformation walkthrough",
            "Makes transformer accessible to beginners"
        ],
        "citation_count": 8923
    },
    {
        "id": "paper-005",
        "title": "Layer Normalization",
        "authors": ["Ba", "Kiros", "Hinton"],
        "year": 2016,
        "venue": "arXiv",
        "abstract": "We propose layer normalization, a simple method for training deep neural networks.",
        "key_claims": [
            "Stabilizes hidden state dynamics in deep networks",
            "Works well with recurrent architectures",
            "Reduces training time significantly"
        ],
        "citation_count": 12345
    },
    {
        "id": "paper-006",
        "title": "Adam: A Method for Stochastic Optimization",
        "authors": ["Kingma", "Ba"],
        "year": 2015,
        "venue": "ICLR",
        "abstract": "We introduce Adam, an algorithm for first-order gradient-based optimization of stochastic objective functions.",
        "key_claims": [
            "Adaptive learning rates per-parameter",
            "Combines momentum and RMSprop",
            "Simple implementation, efficient memory"
        ],
        "citation_count": 156789
    },
    {
        "id": "paper-007",
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["He", "Zhang", "Ren", "Sun"],
        "year": 2016,
        "venue": "CVPR",
        "abstract": "We present a residual learning framework to ease the training of networks that are substantially deeper.",
        "key_claims": [
            "Skip connections enable deeper networks",
            "Identity mapping solves degradation problem",
            "Won ImageNet 2015 with 152 layers"
        ],
        "citation_count": 145678
    },
    {
        "id": "paper-008",
        "title": "Generative Adversarial Networks",
        "authors": ["Goodfellow", "Pouget-Abadie", "Mirza", "et al."],
        "year": 2014,
        "venue": "NeurIPS",
        "abstract": "We propose a new framework for estimating generative models via an adversarial process.",
        "key_claims": [
            "Adversarial training enables realistic generation",
            "Generator-discriminator game theoretic framework",
            "No need for Markov chains or approximate inference"
        ],
        "citation_count": 67890
    },
    {
        "id": "paper-009",
        "title": "ImageNet Classification with Deep Convolutional Neural Networks",
        "authors": ["Krizhevsky", "Sutskever", "Hinton"],
        "year": 2012,
        "venue": "NeurIPS",
        "abstract": "We trained a large, deep convolutional neural network to classify the 1.2 million high-resolution images.",
        "key_claims": [
            "GPU training enables large model performance",
            "ReLU activation accelerates convergence",
            "Data augmentation prevents overfitting"
        ],
        "citation_count": 234567
    },
    {
        "id": "paper-010",
        "title": "Scaling Laws for Neural Language Models",
        "authors": ["Kaplan", "McCandlish", "Henighan", "et al."],
        "year": 2020,
        "venue": "arXiv",
        "abstract": "We study empirical scaling laws for language model performance on the cross-entropy loss.",
        "key_claims": [
            "Power-law scaling with model size",
            "Compute, data, and model size interact predictably",
            "Optimal batch size scales with model size"
        ],
        "citation_count": 5678
    }
]

# Citation relationships (who cites whom)
CITATIONS = [
    # BERT cites Attention Is All You Need
    ("paper-002", "paper-001"),
    # GPT-3 cites BERT and Attention Is All You Need
    ("paper-003", "paper-002"),
    ("paper-003", "paper-001"),
    # The Illustrated Transformer cites Attention Is All You Need
    ("paper-004", "paper-001"),
    # BERT cites Layer Normalization
    ("paper-002", "paper-005"),
    # Various papers cite Adam
    ("paper-001", "paper-006"),
    ("paper-002", "paper-006"),
    ("paper-003", "paper-006"),
    # Deep Residual cites earlier work
    ("paper-007", "paper-009"),
    # Scaling Laws cites GPT-3 and BERT
    ("paper-010", "paper-003"),
    ("paper-010", "paper-002"),
    ("paper-010", "paper-001"),
    # GANs cite various foundational work
    ("paper-008", "paper-009"),
]


def get_db():
    """Initialize RushDB connection."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found. "
            "Please add it to your .env file or set the environment variable."
        )
    return RushDB(api_key)


def clear_existing_data(db: RushDB):
    """Remove existing documents to allow clean reseeding."""
    print("Clearing existing data...")
    
    # Find and delete all DOCUMENT records
    result = db.records.find({"labels": ["DOCUMENT"]})
    if result.data:
        record_ids = [r.id for r in result.data]
        for record_id in record_ids:
            db.records.delete(record_id=record_id)
    
    # Find and delete all AUTHOR records
    result = db.records.find({"labels": ["AUTHOR"]})
    if result.data:
        record_ids = [r.id for r in result.data]
        for record_id in record_ids:
            db.records.delete(record_id=record_id)
    
    print(f"Cleared existing records.")


def seed_documents(db: RushDB):
    """Create document records in RushDB."""
    print(f"\nSeeding {len(DOCUMENTS)} documents...")
    
    document_records = {}
    
    for i, doc in enumerate(DOCUMENTS):
        # Use upsert with external_id for idempotency
        record = db.records.upsert(
            label="DOCUMENT",
            data={
                "external_id": doc["id"],
                "title": doc["title"],
                "authors": doc["authors"],
                "year": doc["year"],
                "venue": doc["venue"],
                "abstract": doc["abstract"],
                "key_claims": doc["key_claims"],
                "citation_count": doc["citation_count"]
            },
            options={"mergeBy": ["external_id"]}
        )
        document_records[doc["id"]] = record
        
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} documents...")
    
    print(f"Created {len(document_records)} documents.")
    return document_records


def seed_citations(db: RushDB, document_records: dict):
    """Create citation relationships between documents."""
    print(f"\nSeeding {len(CITATIONS)} citation relationships...")
    
    for i, (citing_id, cited_id) in enumerate(CITATIONS):
        citing_record = document_records.get(citing_id)
        cited_record = document_records.get(cited_id)
        
        if citing_record and cited_record:
            db.records.attach(
                source=citing_record,
                target=cited_record,
                options={"type": "CITES", "direction": "out"}
            )
            
            if (i + 1) % 100 == 0:
                print(f"  Created {i + 1} citations...")
    
    print(f"Created {len(CITATIONS)} citation relationships.")


def verify_graph(db: RushDB):
    """Verify the graph structure was created correctly."""
    print("\n" + "=" * 50)
    print("Verifying knowledge graph...")
    print("=" * 50)
    
    # Count documents
    docs = db.records.find({"labels": ["DOCUMENT"]})
    print(f"\nDocuments: {len(docs.data)}")
    
    # Show a sample document
    if docs.data:
        sample = docs.data[0]
        print(f"\nSample document:")
        print(f"  Title: {sample.data.get('title')}")
        print(f"  Authors: {sample.data.get('authors')}")
        print(f"  Year: {sample.data.get('year')}")
        print(f"  Key Claims: {sample.data.get('key_claims')}")
    
    # Count citations by querying relationships
    print("\nCitation structure:")
    for doc in docs.data[:3]:
        # Find documents this one cites
        citing = db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "CITES": {
                    "$relation": {"type": "CITES", "direction": "in"},
                    "id": doc.id
                }
            }
        })
        if citing.data:
            titles = [d.data.get('title', 'Unknown')[:40] for d in citing.data]
            print(f"  '{doc.data.get('title', 'Unknown')[:40]}...' is cited by {len(citing.data)} document(s)")
    
    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("=" * 50)


def main():
    """Main seeding function."""
    print("=" * 50)
    print("RushDB Knowledge Graph Seeder")
    print("Streaming Token Generation Tutorial")
    print("=" * 50)
    
    db = get_db()
    
    # Check if data already exists
    existing = db.records.find({"labels": ["DOCUMENT"]})
    if existing.data:
        response = input(f"\nFound {len(existing.data)} existing documents. Clear and reseed? (y/N): ")
        if response.lower() == 'y':
            clear_existing_data(db)
        else:
            print("Skipping seed - existing data preserved.")
            verify_graph(db)
            return
    
    # Seed the data
    document_records = seed_documents(db)
    seed_citations(db, document_records)
    verify_graph(db)


if __name__ == "__main__":
    main()
