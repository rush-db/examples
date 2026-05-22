"""
Seed script for real-time vector update tutorial.

Generates sample documents about machine learning topics and creates
vector embeddings using sentence-transformers.

This demonstrates the initial seeding pattern - generating embeddings
once and storing them in RushDB with pre-computed vectors.
"""

import os
import random
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

from rushdb import RushDB

# Sample documents with machine learning topics
DOCUMENTS = [
    {
        "title": "Understanding Neural Networks in Production",
        "body": "Neural networks have become the backbone of modern AI systems. When deploying models in production, consider latency requirements, batching strategies, and model versioning. Use monitoring to track drift and retrain when necessary.",
        "category": "deep-learning"
    },
    {
        "title": "Deep Learning for Beginners",
        "body": "Deep learning is a subset of machine learning that uses neural networks with multiple layers. Key concepts include backpropagation, gradient descent, and activation functions. Start with simple architectures before moving to complex models.",
        "category": "deep-learning"
    },
    {
        "title": "Machine Learning Model Deployment",
        "body": "Deploying ML models requires careful planning. Choose between batch processing and real-time inference based on your use case. Use containers for reproducibility and implement proper CI/CD for model updates.",
        "category": "mlops"
    },
    {
        "title": "Natural Language Processing Fundamentals",
        "body": "NLP enables machines to understand human language. Key techniques include tokenization, embeddings, and attention mechanisms. Modern NLP relies on transformer architectures for state-of-the-art performance.",
        "category": "nlp"
    },
    {
        "title": "Computer Vision with Convolutional Networks",
        "body": "Convolutional neural networks excel at image tasks. Use architectures like ResNet or EfficientNet for transfer learning. Data augmentation and proper preprocessing are critical for good performance.",
        "category": "computer-vision"
    },
    {
        "title": "Reinforcement Learning Basics",
        "body": "Reinforcement learning trains agents through rewards and penalties. Key concepts include policy gradients, Q-learning, and exploration-exploitation tradeoffs. Use environments like OpenAI Gym for practice.",
        "category": "reinforcement-learning"
    },
    {
        "title": "Transformers and Attention Mechanisms",
        "body": "The transformer architecture revolutionized AI. Self-attention allows models to weigh the importance of different input parts. BERT and GPT are based on transformers and achieve remarkable results across tasks.",
        "category": "deep-learning"
    },
    {
        "title": "Attention Is All You Need - Summary",
        "body": "The original transformer paper introduced attention mechanisms that process sequences in parallel. Key innovations include positional encoding, multi-head attention, and feed-forward layers. This architecture powers modern language models.",
        "category": "nlp"
    },
    {
        "title": "Transformer Architecture Explained",
        "body": "Transformers use encoder-decoder structures with attention at their core. The encoder processes input sequences while the decoder generates outputs. Scale Transformers with more layers and heads for better performance.",
        "category": "nlp"
    },
    {
        "title": "BERT and Its Applications",
        "body": "BERT is a bidirectional transformer model that understands context from both directions. Use it for sentiment analysis, question answering, and text classification. Fine-tune on your specific dataset for best results.",
        "category": "nlp"
    },
    {
        "title": "GPT Models Explained",
        "body": "GPT is a generative pre-trained transformer that excels at producing coherent text. It uses unsupervised pre-training followed by supervised fine-tuning. Scale GPT models with more parameters for better fluency.",
        "category": "nlp"
    },
    {
        "title": "Fine-Tuning Pre-Trained Models",
        "body": "Transfer learning enables you to adapt pre-trained models to your tasks. Use techniques like layer freezing, learning rate scheduling, and data augmentation. Monitor validation metrics to avoid overfitting.",
        "category": "deep-learning"
    },
    {
        "title": "Handling Imbalanced Datasets",
        "body": "Imbalanced data harms model performance. Use oversampling, undersampling, or SMOTE. Consider class weights during training and use appropriate metrics like F1-score or AUC-ROC instead of accuracy.",
        "category": "mlops"
    },
    {
        "title": "Model Evaluation Metrics",
        "body": "Choose metrics based on your problem type. Classification uses accuracy, precision, recall, F1. Regression uses MAE, MSE, R-squared. For ranking, use NDCG or MAP. Always validate on held-out data.",
        "category": "mlops"
    },
    {
        "title": "Introduction to Generative AI",
        "body": "Generative AI creates new content from learned patterns. Models like GANs, VAEs, and diffusion models generate images, text, and audio. Applications include art, code generation, and drug discovery.",
        "category": "deep-learning"
    },
]


def seed_documents():
    """Seed the database with sample documents and pre-computed embeddings."""
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError("RUSHDB_API_KEY environment variable is required")
    
    db = RushDB(api_key)
    
    # Initialize embedding model (all-MiniLM-L6-v2 for speed and good quality)
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding_dim = 384  # all-MiniLM-L6-v2 outputs 384-dimensional vectors
    
    # Clean up existing data (optional - comment out in production)
    print("\n=== CLEANUP ===")
    try:
        # Find and delete existing index
        indexes = db.ai.indexes.find().data
        for idx in indexes:
            if idx['label'] == 'Document' and idx['propertyName'] == 'body':
                print(f"Deleting existing index: {idx['__id']}")
                db.ai.indexes.delete(idx['__id'])
    except Exception as e:
        print(f"Index cleanup skipped: {e}")
    
    # Clean up existing documents
    try:
        existing = db.records.find({"labels": ["Document"]}).data
        if existing:
            print(f"Found {len(existing)} existing documents - will update them")
    except Exception:
        pass
    
    # Create vector index
    print("\n=== INDEX CREATION ===")
    index = db.ai.indexes.create({
        "label": "Document",
        "propertyName": "body",
        "sourceType": "external",
        "dimensions": embedding_dim,
        "similarityFunction": "cosine"
    })
    index_id = index.data["__id"]
    print(f"✓ Created index: Document.body (external, {embedding_dim} dimensions)")
    
    # Generate embeddings for all documents
    print("\n=== EMBEDDING GENERATION ===")
    texts = [doc["body"] for doc in DOCUMENTS]
    embeddings = model.encode(texts, show_progress_bar=True)
    print(f"✓ Generated {len(embeddings)} embeddings")
    
    # Upsert documents with pre-computed vectors
    print("\n=== DOCUMENT SEEDING ===")
    created_count = 0
    
    for i, doc_data in enumerate(DOCUMENTS):
        embedding = embeddings[i].tolist()
        
        # Upsert by title to avoid duplicates on re-runs
        record = db.records.upsert(
            label="Document",
            data={
                "title": doc_data["title"],
                "body": doc_data["body"],
                "category": doc_data["category"]
            },
            options={
                "mergeBy": ["title"],
                "mergeStrategy": "replace"
            },
            vectors=[{"propertyName": "body", "vector": embedding}]
        )
        created_count += 1
        
        if (i + 1) % 5 == 0:
            print(f"  Seeded {i + 1}/{len(DOCUMENTS)} documents")
    
    print(f"✓ Seeded {created_count} documents with pre-computed vectors")
    
    # Verify index stats
    stats = db.ai.indexes.stats(index_id)
    print(f"\n=== INDEX STATUS ===")
    print(f"  Total records: {stats.data['totalRecords']}")
    print(f"  Indexed records: {stats.data['indexedRecords']}")
    print(f"  Status: {stats.data['status']}")
    
    print("\n✓ Seeding complete! Run main.py to see the update demo.")
    
    return index_id


if __name__ == "__main__":
    seed_documents()
