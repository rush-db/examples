"""
Seed script for the Graph-Backed Research Assistant tutorial.

Generates realistic mock research data and loads it into RushDB.
Creates a citation graph with papers, claims, findings, and relationships.

Run: python seed.py
"""
import os
import sys
import random
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rushdb import RushDB


# Sample research data
RESEARCH_TOPICS = [
    "transformer architectures",
    "attention mechanisms",
    "neural network optimization",
    "knowledge distillation",
    "few-shot learning",
    "self-supervised learning",
    "graph neural networks",
    "natural language understanding"
]

PAPERS = [
    {
        "title": "Attention Is All You Need",
        "abstract": "We propose a new simple network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
        "authors": ["Vaswani", "Shazeer", "Parmar"],
        "year": 2017,
        "citations": 85000
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text.",
        "authors": ["Devlin", "Chang", "Liu"],
        "year": 2018,
        "citations": 72000
    },
    {
        "title": "GPT-3: Language Models are Few-Shot Learners",
        "abstract": "We demonstrate that scaling up language models greatly improves task-agnostic, few-shot performance. GPT-3, an autoregressive language model with 175 billion parameters, achieves strong performance on many NLP datasets.",
        "authors": ["Brown", "Mann", "Ryder"],
        "year": 2020,
        "citations": 35000
    },
    {
        "title": "Residual Learning for Image Recognition",
        "abstract": "We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs.",
        "authors": ["He", "Zhang", "Ren"],
        "year": 2015,
        "citations": 180000
    },
    {
        "title": "ImageNet Classification with Deep CNNs",
        "abstract": "We train a large, deep convolutional neural network to classify the 1.2 million high-resolution images in the ImageNet LSVRC-2010 contest into the 1000 different classes.",
        "authors": ["Krizhevsky", "Sutskever", "Hinton"],
        "year": 2012,
        "citations": 120000
    },
    {
        "title": "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
        "abstract": "Deep neural networks with large numbers of parameters are very powerful machine learning systems. However, overfitting is a serious problem in such networks. We introduce dropout, a technique for addressing this problem.",
        "authors": ["Srivastava", "Hinton"],
        "year": 2014,
        "citations": 45000
    },
    {
        "title": "Adam: A Method for Stochastic Optimization",
        "abstract": "We introduce Adam, an algorithm for first-order gradient-based optimization of stochastic objective functions, based on adaptive estimates of lower-order moments.",
        "authors": ["Kingma", "Ba"],
        "year": 2014,
        "citations": 150000
    },
    {
        "title": "Batch Normalization: Accelerating Deep Network Training",
        "abstract": "Training deep neural networks is complicated by the fact that the distribution of each layer's inputs changes during training. We refer to this phenomenon as internal covariate shift.",
        "authors": ["Ioffe", "Szegedy"],
        "year": 2015,
        "citations": 65000
    },
    {
        "title": "Layer Normalization",
        "abstract": "Training state-of-the-art, deep neural networks is computationally expensive. We propose layer normalization, a simple technique to improve training speed for a variety of neural network models.",
        "authors": ["Ba", "Hinton"],
        "year": 2016,
        "citations": 12000
    },
    {
        "title": "Knowledge Distillation: The Teacher-Student Model",
        "abstract": "We consider the problem of training a student network to mimic a teacher network. Knowledge distillation transfers the knowledge from an ensemble or a large well-taught model to a small student model.",
        "authors": ["Hinton", "Vinyals", "Dean"],
        "year": 2015,
        "citations": 8000
    }
]

CLAIMS = [
    {
        "text": "Attention mechanisms enable direct modeling of long-range dependencies",
        "confidence": 0.95,
        "supporting_papers": ["Attention Is All You Need"]
    },
    {
        "text": "Transformers achieve superior parallelization compared to RNNs",
        "confidence": 0.92,
        "supporting_papers": ["Attention Is All You Need"]
    },
    {
        "text": "Bidirectional pre-training captures richer context than unidirectional",
        "confidence": 0.88,
        "supporting_papers": ["BERT: Pre-training of Deep Bidirectional Transformers"]
    },
    {
        "text": "Scaling model size improves few-shot generalization",
        "confidence": 0.90,
        "supporting_papers": ["GPT-3: Language Models are Few-Shot Learners"]
    },
    {
        "text": "Residual connections enable training of much deeper networks",
        "confidence": 0.97,
        "supporting_papers": ["Residual Learning for Image Recognition"]
    },
    {
        "text": "Dropout provides a inexpensive and effective regularization method",
        "confidence": 0.94,
        "supporting_papers": ["Dropout: A Simple Way to Prevent Neural Networks from Overfitting"]
    },
    {
        "text": "Adam converges faster than SGD in most deep learning scenarios",
        "confidence": 0.85,
        "supporting_papers": ["Adam: A Method for Stochastic Optimization"]
    },
    {
        "text": "Batch normalization reduces internal covariate shift",
        "confidence": 0.82,
        "supporting_papers": ["Batch Normalization: Accelerating Deep Network Training"]
    }
]

RESEARCH_QUERIES = [
    "How do attention mechanisms improve long-range dependency modeling?",
    "What are the advantages of transformer architectures over RNNs?",
    "How does knowledge distillation work in practice?",
    "What regularization techniques work best for deep networks?",
    "How does model scaling affect few-shot learning capabilities?"
]


def seed_research_data(db: RushDB) -> dict:
    """Seed the database with research entities and relationships."""
    print("\n=== Seeding Research Data ===\n")
    
    # Check if data already exists
    existing = db.records.find({"labels": ["PAPER"], "limit": 1})
    if existing.data:
        print("✓ Research data already exists, skipping seed.")
        return {"status": "skipped", "reason": "Data already exists"}
    
    # Create papers
    print("[1/5] Creating papers...")
    papers = []
    for i, paper_data in enumerate(PAPERS):
        paper = db.records.create(
            label="PAPER",
            data={
                "title": paper_data["title"],
                "abstract": paper_data["abstract"],
                "authors": paper_data["authors"],
                "year": paper_data["year"],
                "citations": paper_data["citations"],
                "topic": random.choice(RESEARCH_TOPICS)
            }
        )
        papers.append(paper)
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} papers...")
    print(f"  ✓ Created {len(papers)} papers")
    
    # Create citation relationships
    print("\n[2/5] Creating citation relationships...")
    citation_count = 0
    for i, paper in enumerate(papers):
        # Each paper cites 1-3 random earlier papers
        earlier_papers = [p for p in papers if p.data["year"] < paper.data["year"]]
        if earlier_papers:
            cited = random.sample(earlier_papers, min(random.randint(1, 3), len(earlier_papers)))
            for cited_paper in cited:
                db.records.attach(
                    source=paper,
                    target=cited_paper,
                    options={"type": "CITES"}
                )
                citation_count += 1
    print(f"  ✓ Created {citation_count} citation relationships")
    
    # Create claims
    print("\n[3/5] Creating claims...")
    claims = []
    for i, claim_data in enumerate(CLAIMS):
        claim = db.records.create(
            label="CLAIM",
            data={
                "text": claim_data["text"],
                "confidence": claim_data["confidence"]
            }
        )
        claims.append(claim)
        
        # Link claim to supporting papers
        for paper_title in claim_data["supporting_papers"]:
            supporting_paper = next((p for p in papers if p.data["title"] == paper_title), None)
            if supporting_paper:
                db.records.attach(
                    source=claim,
                    target=supporting_paper,
                    options={"type": "SUPPORTED_BY"}
                )
    print(f"  ✓ Created {len(claims)} claims with supporting references")
    
    # Create research queries
    print("\n[4/5] Creating research queries...")
    queries = []
    for query_text in RESEARCH_QUERIES:
        query = db.records.create(
            label="QUERY",
            data={
                "text": query_text,
                "intent": random.choice(["exploration", "verification", "comparison", "synthesis"]),
                "status": "pending"
            }
        )
        queries.append(query)
    print(f"  ✓ Created {len(queries)} research queries")
    
    # Create hypothesis and link claims
    print("\n[5/5] Creating hypotheses and linking claims...")
    hypothesis = db.records.create(
        label="HYPOTHESIS",
        data={
            "statement": "Attention mechanisms are fundamental to achieving state-of-the-art results in NLP",
            "verified": True
        }
    )
    
    # Link first 3 claims to hypothesis
    for claim in claims[:3]:
        db.records.attach(
            source=claim,
            target=hypothesis,
            options={"type": "SUPPORTS"}
        )
    print(f"  ✓ Created hypothesis with {len(claims[:3])} supporting claims")
    
    print("\n=== Seed Complete ===")
    print(f"  Papers: {len(papers)}")
    print(f"  Claims: {len(claims)}")
    print(f"  Queries: {len(queries)}")
    print(f"  Citations: {citation_count}")
    
    return {
        "status": "complete",
        "papers": len(papers),
        "claims": len(claims),
        "queries": len(queries),
        "citations": citation_count
    }


def main():
    """Main entry point for the seed script."""
    # Verify API token
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        print("ERROR: RUSHDB_API_TOKEN not found in environment")
        print("Please copy .env.example to .env and add your API key")
        sys.exit(1)
    
    # Initialize RushDB client
    db = RushDB(api_token)
    
    # Run seed
    result = seed_research_data(db)
    print(f"\nSeed result: {result}")


if __name__ == "__main__":
    main()
