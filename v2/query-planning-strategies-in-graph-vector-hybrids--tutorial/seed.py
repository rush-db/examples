"""
Database seeding script for Query Planning Strategies tutorial.
Creates a knowledge graph with concepts, documents, and hierarchical relationships.
"""
import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)

# Knowledge base data
CONCEPTS = [
    {"name": "machine learning", "description": "Field of study that gives computers the ability to learn from data without being explicitly programmed"},
    {"name": "neural networks", "description": "Computing systems inspired by biological neural networks that consist of interconnected nodes"},
    {"name": "deep learning", "description": "Subset of machine learning using artificial neural networks with multiple layers"},
    {"name": "gradient descent", "description": "Optimization algorithm used to minimize loss functions by iteratively moving towards the steepest descent"},
    {"name": "backpropagation", "description": "Algorithm for training neural networks by computing gradients of the loss function"},
    {"name": "convolutional neural networks", "description": "Deep learning architecture particularly effective for image recognition tasks"},
    {"name": "recurrent neural networks", "description": "Neural network architecture designed for sequential data processing"},
    {"name": "transformers", "description": "Architecture using self-attention mechanisms that revolutionized natural language processing"},
    {"name": "attention mechanism", "description": "Technique allowing neural networks to focus on relevant parts of the input"},
    {"name": "reinforcement learning", "description": "Machine learning paradigm where agents learn by interacting with an environment"},
    {"name": "natural language processing", "description": "Branch of AI dealing with understanding and generating human language"},
    {"name": "computer vision", "description": "Field enabling computers to derive meaningful information from visual inputs"},
    {"name": "optimization", "description": "Mathematical process of finding the best solution from all feasible solutions"},
    {"name": "regularization", "description": "Techniques to prevent overfitting by adding penalties to the loss function"},
    {"name": "transfer learning", "description": "Approach where knowledge from one task is applied to improve performance on another"},
    {"name": "generative models", "description": "Models that learn to generate new data similar to training distribution"},
    {"name": "transformer architecture", "description": "Modern neural network design using self-attention and positional encoding"},
    {"name": "bert", "description": "Bidirectional encoder representations from transformers, revolutionizing NLP tasks"},
    {"name": "gpt", "description": "Generative pre-trained transformer models for natural language generation"},
    {"name": "embedding vectors", "description": "Dense vector representations of discrete variables in continuous space"},
]

DOCUMENTS = [
    {"title": "Introduction to Machine Learning Fundamentals", "type": "article", "level": "beginner"},
    {"title": "Understanding Neural Network Architectures", "type": "tutorial", "level": "intermediate"},
    {"title": "Deep Learning: A Comprehensive Guide", "type": "article", "level": "advanced"},
    {"title": "Implementing Gradient Descent from Scratch", "type": "tutorial", "level": "intermediate"},
    {"title": "Backpropagation Explained with Math", "type": "article", "level": "advanced"},
    {"title": "CNNs for Image Classification", "type": "tutorial", "level": "intermediate"},
    {"title": "Sequence Modeling with RNNs", "type": "article", "level": "advanced"},
    {"title": "Attention Is All You Need: Paper Review", "type": "article", "level": "advanced"},
    {"title": "Building Transformers in Python", "type": "tutorial", "level": "advanced"},
    {"title": "Q-Learning: A Practical Introduction", "type": "tutorial", "level": "intermediate"},
    {"title": "NLP Pipeline Architecture", "type": "article", "level": "intermediate"},
    {"title": "Object Detection with CNNs", "type": "tutorial", "level": "advanced"},
    {"title": "Stochastic vs Batch Gradient Descent", "type": "article", "level": "intermediate"},
    {"title": "L1 and L2 Regularization Explained", "type": "article", "level": "intermediate"},
    {"title": "Fine-tuning Pre-trained Models", "type": "tutorial", "level": "intermediate"},
    {"title": "GANs: Generative Adversarial Networks", "type": "article", "level": "advanced"},
    {"title": "Positional Encoding in Transformers", "type": "tutorial", "level": "advanced"},
    {"title": "BERT Model Architecture Deep Dive", "type": "article", "level": "advanced"},
    {"title": "GPT-3 and Language Modeling", "type": "article", "level": "advanced"},
    {"title": "Vector Embeddings for Semantic Search", "type": "tutorial", "level": "intermediate"},
    {"title": "Understanding Activation Functions", "type": "article", "level": "beginner"},
    {"title": "Vanishing Gradient Problem", "type": "article", "level": "intermediate"},
    {"title": "Optimizer Algorithms Comparison", "type": "article", "level": "intermediate"},
    {"title": "Dropout: A Simple Regularization Technique", "type": "tutorial", "level": "beginner"},
    {"title": "Cross-Entropy Loss Explained", "type": "article", "level": "intermediate"},
    {"title": "Word2Vec and Embedding Techniques", "type": "article", "level": "intermediate"},
    {"title": "Seq2Seq Models Explained", "type": "article", "level": "advanced"},
    {"title": "Graph Neural Networks Overview", "type": "article", "level": "advanced"},
    {"title": "Few-shot Learning Techniques", "type": "article", "level": "advanced"},
    {"title": "Model Evaluation Metrics", "type": "article", "level": "beginner"},
]

# Define hierarchical relationships between concepts
HIERARCHY = [
    ("machine learning", "neural networks", "parent_of", 0.9),
    ("machine learning", "reinforcement learning", "parent_of", 0.85),
    ("machine learning", "natural language processing", "parent_of", 0.88),
    ("machine learning", "computer vision", "parent_of", 0.86),
    ("neural networks", "deep learning", "parent_of", 0.92),
    ("neural networks", "convolutional neural networks", "parent_of", 0.89),
    ("neural networks", "recurrent neural networks", "parent_of", 0.88),
    ("deep learning", "transformers", "parent_of", 0.94),
    ("deep learning", "backpropagation", "includes", 0.91),
    ("deep learning", "convolutional neural networks", "includes", 0.87),
    ("deep learning", "recurrent neural networks", "includes", 0.86),
    ("transformers", "attention mechanism", "includes", 0.93),
    ("transformers", "positional encoding", "includes", 0.88),
    ("attention mechanism", "transformer architecture", "leads_to", 0.90),
    ("natural language processing", "transformers", "enabled_by", 0.91),
    ("natural language processing", "bert", "enabled_by", 0.89),
    ("natural language processing", "gpt", "enabled_by", 0.88),
    ("computer vision", "convolutional neural networks", "enabled_by", 0.90),
    ("gradient descent", "optimization", "related_to", 0.85),
    ("optimization", "gradient descent", "related_to", 0.85),
    ("backpropagation", "gradient descent", "uses", 0.92),
    ("reinforcement learning", "q-learning", "includes", 0.87),
    ("deep learning", "generative models", "enables", 0.88),
    ("generative models", "gan", "enables", 0.91),
    ("transfer learning", "bert", "applied_to", 0.89),
    ("transfer learning", "gpt", "applied_to", 0.88),
    ("embedding vectors", "transformers", "used_in", 0.92),
    ("embedding vectors", "bert", "used_in", 0.90),
    ("regularization", "dropout", "implements", 0.88),
    ("neural networks", "embedding vectors", "uses", 0.87),
]

# Concept to documents mapping (which concepts a document covers)
DOCUMENT_CONCEPTS = {
    0: ["machine learning"],
    1: ["neural networks"],
    2: ["deep learning", "neural networks"],
    3: ["gradient descent", "optimization"],
    4: ["backpropagation", "gradient descent", "deep learning"],
    5: ["convolutional neural networks", "computer vision"],
    6: ["recurrent neural networks", "deep learning"],
    7: ["attention mechanism", "transformers"],
    8: ["transformers", "attention mechanism"],
    9: ["reinforcement learning"],
    10: ["natural language processing", "transformers"],
    11: ["computer vision", "convolutional neural networks"],
    12: ["gradient descent", "optimization"],
    13: ["regularization", "neural networks"],
    14: ["transfer learning", "deep learning"],
    15: ["generative models", "deep learning"],
    16: ["transformers", "positional encoding"],
    17: ["bert", "natural language processing", "transformers"],
    18: ["gpt", "natural language processing", "transformers"],
    19: ["embedding vectors", "machine learning"],
    20: ["neural networks", "activation functions"],
    21: ["backpropagation", "deep learning", "gradient descent"],
    22: ["gradient descent", "optimization", "machine learning"],
    23: ["regularization", "neural networks", "dropout"],
    24: ["machine learning", "loss functions"],
    25: ["embedding vectors", "natural language processing"],
    26: ["recurrent neural networks", "natural language processing"],
    27: ["neural networks", "graph neural networks"],
    28: ["transfer learning", "machine learning", "few-shot learning"],
    29: ["machine learning", "evaluation metrics"],
}


def check_and_cleanup():
    """Check if data exists and clean up for fresh seed."""
    existing_labels = db.labels.find({})
    label_names = [l.name for l in existing_labels]
    
    if "CONCEPT" in label_names or "DOCUMENT" in label_names:
        print("Cleaning up existing data...")
        db.records.delete_many({"labels": ["CONCEPT"], "where": {}})
        db.records.delete_many({"labels": ["DOCUMENT"], "where": {}})
        return False
    return True


def create_concepts(concepts_data):
    """Create concept records with descriptions."""
    print("\nCreating concepts...")
    created_concepts = []
    
    for i, concept in enumerate(concepts_data):
        record = db.records.create(
            label="CONCEPT",
            data={
                "name": concept["name"],
                "description": concept["description"],
                "domain": "machine learning",
            }
        )
        created_concepts.append(record)
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(concepts_data)} concepts")
    
    print(f"  Created {len(concepts_data)} concepts total")
    return created_concepts


def create_documents(documents_data):
    """Create document records."""
    print("\nCreating documents...")
    created_documents = []
    
    for i, doc in enumerate(documents_data):
        record = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc["title"],
                "type": doc["type"],
                "level": doc["level"],
                "content": f"Content for {doc['title']}...",
            }
        )
        created_documents.append(record)
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{len(documents_data)} documents")
    
    print(f"  Created {len(documents_data)} documents total")
    return created_documents


def create_index_and_vectors(concepts):
    """Create vector index and add embeddings to concepts."""
    print("\nSetting up vector index...")
    
    # Create external index (we'll supply our own vectors)
    # Using a simple 384-dimension space (sentence-transformers default)
    index = db.ai.indexes.create({
        "label": "CONCEPT",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine",
    })
    
    index_id = index.data["__id"]
    print(f"  Created index: {index_id}")
    
    # Generate pseudo-embeddings for each concept
    # In production, you'd use sentence-transformers or OpenAI
    import hashlib
    
    vectors_to_upsert = []
    for concept in concepts:
        # Create deterministic "embedding" based on concept name
        # This simulates having real embeddings
        seed = int(hashlib.md5(concept["name"].encode()).hexdigest(), 16)
        random.seed(seed)
        vector = [random.uniform(-1, 1) for _ in range(384)]
        # Normalize
        magnitude = sum(v**2 for v in vector) ** 0.5
        vector = [v / magnitude for v in vector]
        
        vectors_to_upsert.append({
            "recordId": concept.id,
            "vector": vector,
        })
    
    # Upsert vectors in batches
    batch_size = 10
    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i + batch_size]
        db.ai.indexes.upsert_vectors(index_id, {"items": batch})
    
    print(f"  Indexed {len(concepts)} concept descriptions")
    return index_id


def create_relationships(concepts, documents):
    """Create hierarchical relationships between concepts and documents."""
    print("\nCreating relationships...")
    
    # Build name-to-record lookup
    concept_lookup = {c["name"]: c for c in concepts}
    
    # Create concept hierarchy relationships
    created_rels = 0
    for source_name, target_name, rel_type, strength in HIERARCHY:
        source = concept_lookup.get(source_name)
        target = concept_lookup.get(target_name)
        
        if source and target:
            db.records.attach(
                source=source,
                target=target,
                options={
                    "type": rel_type.upper().replace(" ", "_"),
                    "direction": "out",
                }
            )
            # Attach strength metadata
            db.records.find_by_id(target.id).update({"edge_strength": strength})
            created_rels += 1
    
    print(f"  Created {created_rels} concept relationships")
    
    # Link documents to concepts
    doc_rels = 0
    for doc_idx, concept_names in DOCUMENT_CONCEPTS.items():
        doc = documents[doc_idx]
        for concept_name in concept_names:
            concept = concept_lookup.get(concept_name)
            if concept:
                db.records.attach(
                    source=doc,
                    target=concept,
                    options={
                        "type": "COVERS",
                        "direction": "out",
                    }
                )
                doc_rels += 1
    
    print(f"  Created {doc_rels} document-concept relationships")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RushDB Query Planning Tutorial - Database Seeding")
    print("=" * 60)
    
    is_fresh = check_and_cleanup()
    
    # Create concepts
    concepts = create_concepts(CONCEPTS)
    
    # Create documents
    documents = create_documents(DOCUMENTS)
    
    # Create vector index and add embeddings
    index_id = create_index_and_vectors(concepts)
    
    # Create relationships
    create_relationships(concepts, documents)
    
    print("\n" + "=" * 60)
    print("Seeding complete!")
    print(f"  - {len(CONCEPTS)} concepts (with vector embeddings)")
    print(f"  - {len(DOCUMENTS)} documents")
    print(f"  - {len(HIERARCHY)} hierarchy relationships")
    print(f"  - {sum(len(v) for v in DOCUMENT_CONCEPTS.values())} doc-concept links")
    print("=" * 60)
    print("\nRun `python main.py` to execute the query planning demo.")


if __name__ == "__main__":
    main()
