#!/usr/bin/env python3
"""
Seed script for the semantic rollback tutorial.

Creates a mock knowledge base with:
- Articles (knowledge entries)
- Concepts (topics/categories)
- Relationships between them
- Vector index for semantic search

This script is idempotent - safe to run multiple times.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Article content for the knowledge base
ARTICLES = [
    {
        "slug": "ml-intro",
        "title": "Introduction to Machine Learning",
        "body": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.",
        "tags": ["machine-learning", "ai", "fundamentals"],
        "status": "published"
    },
    {
        "slug": "ml-supervised",
        "title": "Supervised Learning Fundamentals",
        "body": "Supervised learning is a machine learning approach where the algorithm learns from labeled training data. Each example in the training set consists of an input and a desired output value. The algorithm analyzes the training data and produces an inferred function.",
        "tags": ["machine-learning", "supervised-learning", "algorithms"],
        "status": "published"
    },
    {
        "slug": "ml-unsupervised",
        "title": "Unsupervised Learning Techniques",
        "body": "Unsupervised learning is used when there are no labels in the training data. The system tries to learn without a teacher. The algorithm tries to find hidden patterns or intrinsic structures in input data.",
        "tags": ["machine-learning", "unsupervised-learning", "clustering"],
        "status": "published"
    },
    {
        "slug": "python-basics",
        "title": "Python Programming Basics",
        "body": "Python is a high-level, interpreted programming language known for its readability and simplicity. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
        "tags": ["python", "programming", "fundamentals"],
        "status": "published"
    },
    {
        "slug": "python-data-structures",
        "title": "Python Data Structures Explained",
        "body": "Python provides several built-in data structures including lists, tuples, sets, and dictionaries. Each has specific use cases and performance characteristics. Lists are ordered and mutable, tuples are ordered and immutable.",
        "tags": ["python", "data-structures", "programming"],
        "status": "published"
    },
    {
        "slug": "neural-networks-intro",
        "title": "Introduction to Neural Networks",
        "body": "A neural network is a series of algorithms that endeavors to recognize underlying relationships in a data set through a process that mimics the way the human brain operates. Neural networks can adapt to changing input.",
        "tags": ["neural-networks", "deep-learning", "ai"],
        "status": "published"
    },
    {
        "slug": "deep-learning-cnn",
        "title": "Convolutional Neural Networks for Image Processing",
        "body": "Convolutional Neural Networks are a class of deep neural networks most commonly applied to analyzing visual imagery. CNNs use a special type of linear operation called convolution instead of general matrix multiplication.",
        "tags": ["deep-learning", "cnn", "computer-vision"],
        "status": "published"
    },
    {
        "slug": "nlp-transformers",
        "title": "Transformer Architecture in NLP",
        "body": "The Transformer architecture, introduced in the 'Attention Is All You Need' paper, revolutionized natural language processing. It uses self-attention mechanisms to process sequential data without recurrence.",
        "tags": ["nlp", "transformers", "deep-learning"],
        "status": "published"
    },
    {
        "slug": "reinforcement-learning",
        "title": "Reinforcement Learning: An Overview",
        "body": "Reinforcement learning is a type of dynamic programming that trains algorithms using a system of reward and punishment. The agent learns to make decisions by interacting with an environment.",
        "tags": ["reinforcement-learning", "machine-learning", "ai"],
        "status": "published"
    },
    {
        "slug": "data-preprocessing",
        "title": "Data Preprocessing for Machine Learning",
        "body": "Data preprocessing is a crucial step in machine learning. It involves cleaning, transforming, and integrating data to make it suitable for building and training machine learning models.",
        "tags": ["machine-learning", "data-science", "preprocessing"],
        "status": "published"
    },
    {
        "slug": "model-evaluation",
        "title": "Evaluating Machine Learning Models",
        "body": "Model evaluation is essential for assessing how well a machine learning model performs. Common metrics include accuracy, precision, recall, F1-score, and AUC-ROC. Cross-validation helps ensure robust evaluation.",
        "tags": ["machine-learning", "evaluation", "metrics"],
        "status": "published"
    },
    {
        "slug": "feature-engineering",
        "title": "Feature Engineering Techniques",
        "body": "Feature engineering is the process of using domain knowledge to create features that make machine learning algorithms work better. It involves selecting, modifying, and creating new features from raw data.",
        "tags": ["machine-learning", "feature-engineering", "data-science"],
        "status": "published"
    },
    {
        "slug": "hyperparameter-tuning",
        "title": "Hyperparameter Optimization Strategies",
        "body": "Hyperparameters are parameters whose values are set before the learning process begins. Grid search, random search, and Bayesian optimization are common techniques for finding optimal hyperparameter values.",
        "tags": ["machine-learning", "optimization", "hyperparameters"],
        "status": "published"
    },
    {
        "slug": "bias-variance",
        "title": "Understanding Bias-Variance Tradeoff",
        "body": "The bias-variance tradeoff is a fundamental concept in machine learning. High bias can cause underfitting while high variance can cause overfitting. Finding the right balance is crucial for model performance.",
        "tags": ["machine-learning", "bias-variance", "theory"],
        "status": "published"
    },
    {
        "slug": "ensemble-methods",
        "title": "Ensemble Learning Methods",
        "body": "Ensemble methods combine multiple learning algorithms to obtain better predictive performance. Popular techniques include bagging, boosting, and stacking. Random forests and gradient boosting are widely used examples.",
        "tags": ["machine-learning", "ensemble", "algorithms"],
        "status": "published"
    },
    {
        "slug": "time-series-forecasting",
        "title": "Time Series Forecasting Techniques",
        "body": "Time series forecasting involves analyzing historical data to predict future values. Key methods include ARIMA, exponential smoothing, and modern deep learning approaches like LSTM and Transformer models.",
        "tags": ["time-series", "forecasting", "machine-learning"],
        "status": "published"
    },
    {
        "slug": "recommendation-systems",
        "title": "Building Recommendation Systems",
        "body": "Recommendation systems predict user preferences and suggest relevant items. Collaborative filtering uses user-item interactions while content-based filtering uses item features. Hybrid approaches combine both methods.",
        "tags": ["recommendation-systems", "machine-learning", "applications"],
        "status": "published"
    },
    {
        "slug": "anomaly-detection",
        "title": "Anomaly Detection Methods",
        "body": "Anomaly detection identifies unusual patterns that do not conform to expected behavior. Techniques include statistical methods, machine learning approaches, and deep learning autoencoders. Applications include fraud detection and system monitoring.",
        "tags": ["anomaly-detection", "machine-learning", "applications"],
        "status": "published"
    },
    {
        "slug": "mlops-intro",
        "title": "Introduction to MLops",
        "body": "MLops combines machine learning and DevOps practices to streamline the deployment and maintenance of ML models in production. It emphasizes automation, monitoring, and continuous integration for ML systems.",
        "tags": ["mlops", "machine-learning", "devops"],
        "status": "published"
    },
    {
        "slug": "ethics-ai",
        "title": "Ethics in Artificial Intelligence",
        "body": "AI ethics addresses the moral implications of AI systems including fairness, accountability, transparency, and privacy. Responsible AI development requires considering potential impacts on society and implementing safeguards.",
        "tags": ["ethics", "ai", "responsible-ai"],
        "status": "published"
    }
]

# Concept nodes for categorization
CONCEPTS = [
    {"slug": "machine-learning", "name": "Machine Learning", "description": "Core ML concepts and techniques"},
    {"slug": "deep-learning", "name": "Deep Learning", "description": "Neural networks and deep architectures"},
    {"slug": "python", "name": "Python Programming", "description": "Python language for data science"},
    {"slug": "data-science", "name": "Data Science", "description": "Data analysis and interpretation"},
    {"slug": "nlp", "name": "Natural Language Processing", "description": "Text and language processing"},
    {"slug": "computer-vision", "name": "Computer Vision", "description": "Image and video analysis"},
    {"slug": "algorithms", "name": "Algorithms", "description": "Algorithm design and analysis"},
    {"slug": "fundamentals", "name": "Fundamentals", "description": "Basic concepts and foundations"},
    {"slug": "applications", "name": "Applications", "description": "Real-world applications"},
    {"slug": "responsible-ai", "name": "Responsible AI", "description": "Ethical AI development"}
]


def get_embedding(text: str) -> list:
    """Generate embedding for text using sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text).tolist()


def check_existing_data(db: RushDB) -> bool:
    """Check if data already exists in the knowledge base."""
    result = db.records.find({"labels": ["Article"], "limit": 1})
    return len(result.data) > 0


def seed_knowledge_base():
    """Seed the knowledge base with articles, concepts, and relationships."""
    print("\n=== Seeding Knowledge Base ===\n")
    
    api_token = os.environ.get('RUSHDB_API_TOKEN')
    if not api_token:
        print("ERROR: RUSHDB_API_TOKEN environment variable is not set")
        print("Please create a .env file with your RushDB API token")
        sys.exit(1)
    
    db = RushDB(api_token)
    
    # Check for existing data
    if check_existing_data(db):
        print("Knowledge base already contains data. Skipping seed.")
        print("To reseed, delete existing records first.\n")
        
        # Still ensure vector index exists
        try:
            indexes = db.ai.indexes.find()
            index_exists = any(
                idx.get('label') == 'Article' and idx.get('propertyName') == 'body'
                for idx in indexes.data
            )
            if not index_exists:
                print("Creating vector index on Article.body...")
                db.ai.indexes.create({
                    "label": "Article",
                    "propertyName": "body",
                    "sourceType": "external",
                    "dimensions": 384,
                    "similarityFunction": "cosine"
                })
                print("Vector index created.\n")
        except Exception as e:
            print(f"Note: Could not create vector index: {e}")
        
        return
    
    print("Creating concept nodes...")
    concept_records = []
    for i, concept in enumerate(CONCEPTS):
        record = db.records.create(
            label="Concept",
            data={
                "slug": concept["slug"],
                "name": concept["name"],
                "description": concept["description"]
            }
        )
        concept_records.append(record)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(CONCEPTS)} concepts...")
    print(f"  ✓ Created {len(concept_records)} concept nodes\n")
    
    print("Creating article records with embeddings...")
    article_records = []
    slug_to_concept = {c["slug"]: c for c in CONCEPTS}
    
    for i, article in enumerate(ARTICLES):
        # Generate embedding for the article body
        embedding = get_embedding(article["body"])
        
        record = db.records.create(
            label="Article",
            data={
                "slug": article["slug"],
                "title": article["title"],
                "body": article["body"],
                "tags": article["tags"],
                "status": article["status"],
                "createdAt": datetime.now().isoformat()
            },
            vectors=[{"propertyName": "body", "vector": embedding}]
        )
        article_records.append(record)
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(ARTICLES)} articles...")
    print(f"  ✓ Created {len(article_records)} article records with embeddings\n")
    
    print("Creating relationships between articles and concepts...")
    relationship_count = 0
    for i, (article, article_record) in enumerate(zip(ARTICLES, article_records)):
        for tag in article["tags"]:
            # Find matching concept by slug
            if tag in slug_to_concept:
                concept_record = next(
                    (c for c in concept_records 
                     if c.data.get("slug") == tag), 
                    None
                )
                if concept_record:
                    db.records.attach(
                        source=article_record,
                        target=concept_record,
                        options={"type": "TAGGED_WITH", "direction": "out"}
                    )
                    relationship_count += 1
        
        if (i + 1) % 5 == 0:
            print(f"  Created {relationship_count} relationships so far...")
    print(f"  ✓ Created {relationship_count} article-concept relationships\n")
    
    # Create vector index for semantic search
    print("Creating vector index on Article.body...")
    try:
        db.ai.indexes.create({
            "label": "Article",
            "propertyName": "body",
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine"
        })
        print("  ✓ Vector index created\n")
    except Exception as e:
        print(f"  Note: Vector index creation: {e}\n")
    
    # Verify data
    article_count = len(db.records.find({"labels": ["Article"], "limit": 100}).data)
    concept_count = len(db.records.find({"labels": ["Concept"], "limit": 100}).data)
    
    print("=== Seeding Complete ===")
    print(f"  Articles: {article_count}")
    print(f"  Concepts: {concept_count}")
    print(f"  Vector Index: Created on Article.body\n")


if __name__ == "__main__":
    seed_knowledge_base()
