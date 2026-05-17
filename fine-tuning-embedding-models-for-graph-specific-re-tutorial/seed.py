#!/usr/bin/env python3
"""
Seed script for the fine-tuning tutorial.

Generates a sample academic knowledge graph and imports it into RushDB.
The graph contains:
- Research papers with titles and abstracts
- Authors with names and affiliations
- Topics/subjects
- Citation relationships between papers
- Authorship relationships between authors and papers
- Topic assignments for papers

This script is idempotent - running it multiple times won't create duplicates.
"""

import random
import sys
from datetime import datetime, timedelta
from typing import Any

from tqdm import tqdm

from config import (
    RUSHDB_API_KEY,
    RUSHDB_URL,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    GRAPH_DATA,
)
from rushdb import RushDB

# Initialize RushDB client
db = RushDB(RUSHDB_API_KEY, url=RUSHDB_URL)

# Sample data for generating the academic graph
TOPICS = [
    "Machine Learning",
    "Natural Language Processing",
    "Computer Vision",
    "Reinforcement Learning",
    "Graph Neural Networks",
    "Distributed Systems",
    "Computer Graphics",
    "Robotics",
    "Bioinformatics",
    "Quantum Computing",
]

PAPER_TITLES = [
    "Attention Is All You Need",
    "BERT: Pre-training of Deep Bidirectional Transformers",
    "GPT-3: Language Models are Few-Shot Learners",
    "ImageNet Classification with Deep Convolutional Neural Networks",
    "Generative Adversarial Networks",
    "Deep Residual Learning for Image Recognition",
    "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
    "Batch Normalization: Accelerating Deep Network Training",
    "Adam: A Method for Stochastic Optimization",
    "Playing Atari with Deep Reinforcement Learning",
    "Mastering the Game of Go with Deep Neural Networks",
    "Neural Machine Translation by Jointly Learning to Align",
    "Neural Machine Translation by Jointly Learning to Align and Translate",
    "Sequence to Sequence Learning with Neural Networks",
    "Word2Vec: Distributed Representations of Words",
    "GloVe: Global Vectors for Word Representation",
    "ELMo: Deep Contextualized Word Representations",
    "U-Net: Convolutional Networks for Biomedical Image Segmentation",
    "Faster R-CNN: Towards Real-Time Object Detection",
    "You Only Look Once: Unified Real-Time Object Detection",
    "Mask R-CNN",
    "Graph Attention Networks",
    "Semi-Supervised Classification with Graph Convolutional Networks",
    "Node2Vec: Scalable Feature Learning for Networks",
    "LINE: Large-scale Information Network Embedding",
    "DeepWalk: Online Learning of Social Representations",
    "Variational Autoencoders for Learning Deep Generative Models",
    "PixelCNN and PixelRNN: Generative Models for Images",
    "WaveNet: A Generative Model for Raw Audio",
    "Transformer-XL: Attentive Language Models Beyond Fixed-Length Context",
    "XLNet: Generalized Autoregressive Pretraining",
    "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
    "ALBERT: A Lite BERT for Self-supervised Learning",
    "ELECTRA: Pre-training Text Encoders as Discriminators",
    "CLIP: Learning Transferable Visual Models From Natural Language",
    "DALL-E: Creating Images from Text",
    "T5: Text-to-Text Transfer Transformer",
    "BART: Denoising Sequence-to-Sequence Pre-training",
    "Diffusion Models Beat GANs on Image Synthesis",
    "Stable Diffusion: High-Resolution Image Synthesis",
    "Chain of Thought Prompting Elicits Reasoning in Large Language Models",
    "Self-Consistency Improves Chain of Thought Reasoning",
    "Tree of Thoughts: Deliberate Problem Solving",
    "ReAct: Synergizing Reasoning and Acting in Language Models",
    "Toolformer: Language Models Can Teach Themselves to Use Tools",
    "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
    "In-Context Learning: Concepts and Applications",
    "Codex: Evaluating Large Language Models Trained on Code",
    "InstructGPT: Training Language Models to Follow Instructions",
    "RLHF: Learning to summarize from human feedback",
    "Constitutional AI: Harmlessness from AI Feedback",
    "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
    "QLoRA: Efficient Finetuning of Quantized LLMs",
    "LoRA: Low-Rank Adaptation of Large Language Models",
]

PAPER_ABSTRACTS = [
    "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
    "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
    "Recent work has demonstrated strong performance on many language modeling and machine translation benchmarks.",
    "We trained a large, deep convolutional neural network to classify the 1.2 million high-resolution images in the ImageNet LSVRC-2010 contest.",
    "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models.",
    "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks.",
    "Deep neural networks with many layers are capable of learning highly complex and intricate functions.",
    "Training Deep Neural Networks is complicated by the fact that the distribution of each layer's inputs changes during training.",
    "We introduce Adam, an algorithm for first-order gradient-based optimization of stochastic objective functions.",
    "We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input.",
    "The game of Go has long been viewed as the most challenging of classic games for artificial intelligence.",
    "RNN encoders-decoders are capable of learning sensible sequence-to-sequence mappings for short phrases or sentences.",
    "We propose a novel neural network architecture that eliminates the sequential computation of RNNs and allows parallel computation.",
    "Neural networks are powerful function approximators, and the skip-gram model is an efficient method for learning high-quality vector representations.",
    "We present GloVe, an unsupervised learning algorithm for obtaining vector representations for words.",
    "We introduce a new type of deep contextualized word representation that models both complex characteristics of word usage.",
    "There is large consent that successful training of deep networks requires many thousand annotated training samples.",
    "State-of-the-art object detection networks depend on region proposal algorithms to hypothesize object locations.",
    "We present YOLO, a unified approach to real-time object detection that is extremely fast and accurate.",
    "We propose a conceptually simple, flexible, and general framework for object instance segmentation.",
    "We present graph attention networks (GATs), novel neural network architectures that operate on graph-structured data.",
    "We present a scalable approach for semi-supervised learning on graph-structured data using graph convolutional networks.",
    "We study the problem of learning feature representations for nodes in a graph, with a focus on embedding nodes.",
    "We present a novel embedding method which can learn from arbitrary sampling neighborhood in graphs.",
    "We propose a new embedding method for vertices of large networks based on large-scale network embedding.",
    "We present DeepWalk, an online learning approach that generates social representations from truncated random walks.",
    "We introduce a new framework for learning deep generative models based on variational autoencoders.",
    "We generalize autoregressive models and jointly learn a conditional distribution over the pixels of an image.",
    "We introduce WaveNet, a deep generative model for raw audio waveforms that achieves state-of-the-art performance.",
    "Transformers have proven to achieve superior results in sequence modeling and transduction tasks.",
    "With the breakout success of BERT, natural language processing research has seen an influx of pretrained models.",
    "We present a robustly optimized method for pretraining self-supervised NLP models that better tunes the original BERT.",
    "Due to the capacity limitations of model parallelism, existing approaches to training deeper networks face challenges.",
    "Unsupervised pretraining using replaced token detection achieves excellent performance on various language understanding tasks.",
    "We study the problem of learning transferable visual representations from natural language supervision.",
    "We explore autoregressive, decoders-only models that can generate images from textual descriptions.",
    "Transfer learning, where a model is first pre-trained on a data-rich task, has become a dominant paradigm.",
    "We present a denoising sequence-to-sequence pre-training approach for natural language understanding.",
    "Modern diffusion models achieve outstanding quality for image synthesis but are computationally expensive.",
    "We present Stable Diffusion, a latent text-to-image diffusion model capable of generating photo-realistic images.",
    "Language models can perform new tasks by inferring from a few demonstrations, a paradigm known as in-context learning.",
    "We propose a new decoding strategy that samples from the human-written chains of thought to improve reasoning.",
    "We propose a new problem-solving framework that models the thought process as a tree rather than a chain.",
    "We explore large language models that can use external tools to generalize their reasoning capabilities.",
    "We propose Toolformer, a model that learns to use external tools by self-supervised training.",
    "We demonstrate that retrieval-augmented generation improves performance on knowledge-intensive NLP tasks.",
    "In-context learning allows language models to perform new tasks using only a few demonstrations.",
    "We study the ability of large language models to write computer programs from natural language descriptions.",
    "We train instruction-following models using a combination of supervised learning and reinforcement learning.",
    "We study the use of reinforcement learning from human feedback to train a neural network to summarize text.",
    "We explore an approach for training AI systems that are helpful, harmless, and honest using AI feedback.",
    "Direct preference optimization directly aligns language models with human preferences without reinforcement learning.",
    "We present QLoRA, an efficient fine-tuning method that reduces memory requirements while preserving performance.",
    "We propose LoRA, a method that adapts large language models by learning pairs of rank-decomposition matrices.",
]

AUTHORS = [
    {"name": "Ashish Vaswani", "affiliation": "Google Brain"},
    {"name": "Noam Shazeer", "affiliation": "Google Brain"},
    {"name": "Niki Parmar", "affiliation": "Google Research"},
    {"name": "Jacob Devlin", "affiliation": "Google AI Language"},
    {"name": "Wei Liu", "affiliation": "Microsoft Research"},
    {"name": "Ian Goodfellow", "affiliation": "Google Brain"},
    {"name": "Kaiming He", "affiliation": "Facebook AI Research"},
    {"name": "Sergey Ioffe", "affiliation": "Google Research"},
    {"name": "Christian Szegedy", "affiliation": "Google"},
    {"name": "Volodymyr Mnih", "affiliation": "DeepMind"},
    {"name": "David Silver", "affiliation": "DeepMind"},
    {"name": "Yoshua Bengio", "affiliation": "MILA"},
    {"name": "Ian Goodfellow", "affiliation": "OpenAI"},
    {"name": "Jian Song", "affiliation": "Tsinghua University"},
    {"name": "Andrew Ng", "affiliation": "Stanford University"},
    {"name": "Yann LeCun", "affiliation": "NYU"},
    {"name": "Geoffrey Hinton", "affiliation": "University of Toronto"},
    {"name": "Tomas Mikolov", "affiliation": "CERN"},
    {"name": "Jeffrey H. Moore", "affiliation": "MIT"},
    {"name": "Christopher D. Manning", "affiliation": "Stanford University"},
    {"name": "Richard Socher", "affiliation": "Salesforce Research"},
    {"name": "Ilya Sutskever", "affiliation": "OpenAI"},
    {"name": "John Hopfield", "affiliation": "Princeton"},
    {"name": "Demis Hassabis", "affiliation": "DeepMind"},
    {"name": "Oriol Vinyals", "affiliation": "DeepMind"},
]


def check_data_exists() -> bool:
    """Check if the database has already been seeded."""
    try:
        result = db.records.find({"labels": ["PAPER"], "limit": 1})
        return result.total > 0
    except Exception:
        return False


def clear_existing_data():
    """Clear existing nodes to allow clean re-seeding."""
    print("Clearing existing data...")
    for label in ["PAPER", "AUTHOR", "TOPIC"]:
        try:
            db.records.delete({"labels": [label]})
        except Exception:
            pass


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for texts using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Installing sentence-transformers...")
        import subprocess
        subprocess.check_call(["pip", "install", "sentence-transformers"])
        from sentence_transformers import SentenceTransformer

    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Generating embeddings for {len(texts)} texts...")
    embeddings = model.encode(texts, show_progress_bar=True)

    return embeddings.tolist()


def seed_topics() -> dict[str, Any]:
    """Create topic nodes in RushDB."""
    print("\nCreating topics...")
    topics = {}

    for topic_name in tqdm(TOPICS, desc="Topics"):
        topic = db.records.create(
            label="TOPIC",
            data={"name": topic_name, "field": topic_name.split()[0].lower()},
        )
        topics[topic_name] = topic

    return topics


def seed_authors() -> list[Any]:
    """Create author nodes in RushDB."""
    print("\nCreating authors...")
    authors = []

    for author_data in tqdm(AUTHORS, desc="Authors"):
        author = db.records.create(
            label="AUTHOR",
            data={"name": author_data["name"], "affiliation": author_data["affiliation"]},
        )
        authors.append(author)

    return authors


def seed_papers(
    topics: dict[str, Any],
    authors: list[Any],
) -> tuple[list[Any], dict[str, list[float]], dict[int, Any]]:
    """Create paper nodes with embeddings."""
    print("\nCreating papers with embeddings...")

    papers = []
    paper_embeddings: dict[str, list[float]] = {}
    paper_index: dict[int, Any] = {}

    # Generate abstracts - extend if needed
    abstracts = PAPERS_ABSTRACTS * (len(PAPER_TITLES) // len(PAPER_ABSTRACTS) + 1)
    abstracts = abstracts[: len(PAPER_TITLES)]

    texts_to_embed = [f"{title}. {abstract}" for title, abstract in zip(PAPER_TITLES, abstracts)]
    embeddings = generate_embeddings(texts_to_embed)

    for i, (title, abstract) in tqdm(
        enumerate(zip(PAPER_TITLES, abstracts)),
        total=len(PAPER_TITLES),
        desc="Papers",
    ):
        # Assign random topic
        topic = random.choice(list(topics.values()))

        # Generate random publication date
        days_ago = random.randint(30, 2000)
        pub_date = (datetime.now() - timedelta(days=days_ago)).isoformat()

        paper = db.records.create(
            label="PAPER",
            data={
                "title": title,
                "abstract": abstract,
                "publicationDate": pub_date,
                "citations": 0,
            },
            vectors=[{"propertyName": "abstract", "vector": embeddings[i]}],
        )

        papers.append(paper)
        paper_embeddings[paper.id] = embeddings[i]
        paper_index[i] = paper

        # Attach to topic
        db.records.attach(source=paper, target=topic, options={"type": "ABOUT"})

    return papers, paper_embeddings, paper_index


def seed_citations(papers: list[Any]) -> list[tuple[Any, Any]]:
    """Create citation relationships between papers."""
    print("\nCreating citation relationships...")

    citations = []
    paper_indices = list(range(len(papers)))

    # Each paper cites 1-5 other papers (but not itself)
    for i, paper in tqdm(enumerate(papers), total=len(papers), desc="Citations"):
        num_citations = random.randint(1, 5)

        # Pick random other papers to cite
        available = [p for p in paper_indices if p != i]
        cited_indices = random.sample(available, min(num_citations, len(available)))

        for cited_idx in cited_indices:
            cited_paper = papers[cited_idx]
            db.records.attach(source=paper, target=cited_paper, options={"type": "CITES"})
            citations.append((paper, cited_paper))

            # Update citation count
            current_citations = cited_paper.data.get("citations", 0)
            db.records.update(record_id=cited_paper.id, data={"citations": current_citations + 1})

    return citations


def seed_authorships(papers: list[Any], authors: list[Any]) -> list[tuple[Any, Any]]:
    """Create authorship relationships."""
    print("\nCreating authorship relationships...")

    authorships = []

    for paper in tqdm(papers, desc="Authorships"):
        # Assign 1-3 authors per paper
        num_authors = random.randint(1, 3)
        paper_authors = random.sample(authors, num_authors)

        for author in paper_authors:
            db.records.attach(source=paper, target=author, options={"type": "WRITTEN_BY"})
            authorships.append((paper, author))

    return authorships


def create_vector_index():
    """Create the vector index for paper abstracts."""
    print("\nCreating vector index...")

    try:
        # Check if index already exists
        existing = db.ai.indexes.find()
        for idx in existing.data:
            if idx.get("label") == "PAPER" and idx.get("propertyName") == "abstract":
                print("Vector index already exists, skipping...")
                return
    except Exception:
        pass

    try:
        index = db.ai.indexes.create(
            {
                "label": "PAPER",
                "propertyName": "abstract",
                "sourceType": "external",
                "dimensions": EMBEDDING_DIMENSIONS,
                "similarityFunction": "cosine",
            }
        )
        print(f"Created vector index: {index.data.get('__id', 'unknown')}")
    except Exception as e:
        print(f"Note: Could not create vector index: {e}")
        print("Vector search may not be available until the index is created manually.")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RushDB Fine-tuning Tutorial - Data Seeding")
    print("=" * 60)

    # Check if already seeded
    if check_data_exists():
        print("\nDatabase already contains data. Skipping seed.")
        print("To re-seed, either clear the database first or delete all records.")
        return

    print(f"\nGenerating academic graph with:")
    print(f"  - {len(TOPICS)} topics")
    print(f"  - {len(AUTHORS)} authors")
    print(f"  - {len(PAPER_TITLES)} papers")
    print(f"  - Citation and authorship relationships")

    # Create nodes
    topics = seed_topics()
    authors = seed_authors()
    papers, paper_embeddings, paper_index = seed_papers(topics, authors)

    # Create relationships
    citations = seed_citations(papers)
    authorships = seed_authorships(papers, authors)

    # Create vector index
    create_vector_index()

    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"  - {len(topics)} topic nodes")
    print(f"  - {len(authors)} author nodes")
    print(f"  - {len(papers)} paper nodes with embeddings")
    print(f"  - {len(citations)} citation relationships")
    print(f"  - {len(authorships)} authorship relationships")


if __name__ == "__main__":
    main()
