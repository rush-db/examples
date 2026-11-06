"""
Seed script for the Research Paper Discovery Engine tutorial.

Generates 50 mock research papers with:
- Realistic ML/AI titles and abstracts
- Citation relationships (forming a graph structure)
- Pre-computed embeddings for semantic search

This script is idempotent: it checks for existing data and skips re-ingestion.
"""

import os
import json
import random
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import RushDB
from rushdb import RushDB

# ============================================================================
# MOCK DATA GENERATION
# ============================================================================

PAPER_TITLES = [
    "Attention Is All You Need",
    "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
    "GPT-3: Language Models are Few-Shot Learners",
    "Language Models are Few-Shot Learners",
    "T5: Text-to-Text Transfer Transformer",
    "Scaling Laws for Neural Language Models",
    "An Empirical Investigation of Catastrophic Forgetting in Large Language Models",
    "On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?",
    "Fundamental Limitations of Language Models",
    "Emergent Abilities of Large Language Models",
    "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
    "Self-Consistency Improves Chain of Thought Reasoning",
    "Tree of Thoughts: Deliberate Problem Solving with Large Language Models",
    "Reasoning with Language Model Prompting: A Survey",
    "In-context Learning and Induction Heads",
    "What Makes Chain-of-Thought Prompting Work?",
    "Large Language Models and Human Values",
    "Constitutional AI: Harmlessness from AI Feedback",
    "RLHF: Learning to summarize from human feedback",
    "Deep Reinforcement Learning from Human Preferences",
    "Learning to summarize through human feedback",
    "WebGPT: Browser-assisted question answering with human feedback",
    "InstructGPT: Training language models to follow instructions with human feedback",
    "ChatGPT is a knowledge worker, but what about the rest of us?",
    "Sparks of Artificial General Intelligence: Early experiments with GPT-4",
    "Theory of Mind May Have Spontaneously Emerged in Large Language Models",
    "LaMDA: Language Models for Dialog Applications",
    "PaLM: Scaling Language Modeling with Pathways",
    "PaLM 2 Technical Report",
    "Exploring the Limits of Transfer Learning with T5",
    "mT5: A Massively Multilingual Pre-trained Text-to-Text Transformer",
    "ByT5: Towards a token-free future with pre-trained byte-to-byte models",
    "UL2: Unifying Language Learning Paradigms",
    "Switch Transformers: Scaling to Trillion Parameter Models",
    "ST-MoE: Stable and Transferable Mixture of Experts",
    "GShard: Scaling Giant Models with Conditional Computation",
    "GLaM: Efficient Scaling of Language Models with Mixture-of-Experts",
    "Training Compute-Optimal Large Language Models",
    "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
    "FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning",
    "Efficient Memory Management for Transformer-based Models",
    "LoRA: Low-Rank Adaptation of Large Language Models",
    "QLoRA: Efficient Finetuning of Quantized Language Models",
    "AdapterHub: A Framework for Adapting Transformers",
    "Prefix-Tuning: Optimizing Continuous Prompts for Generation",
    "P-Tuning v2: Prompt Tuning Can Be Comparable to Fine-tuning",
    "The Power of Scale: Parameter-Efficient Self-Attentive Models",
    "ReAct: Synergizing Reasoning and Acting in Language Models",
    "Toolformer: Language Models Can Teach Themselves to Use Tools",
    "Generative Agents: Interactive Simulacra of Human Behavior",
]

CATEGORIES = [
    "Natural Language Processing",
    "Machine Learning",
    "Deep Learning",
    "Computer Vision",
    "Reinforcement Learning",
    "AI Safety",
    "Large Language Models",
]

AUTHORS = [
    "Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit",
    "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin",
    "Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova",
    "Tom Brown", "Benjamin Mann", "Nick Ryder", "Melanie Subbiah",
    "Jerry Zhuravlev", "Aditya Prmadha", "Prafulla Dhariwal", "David Luan",
    "Yi Tay", "Mostafa A. H AbdElrahman", "Yinhan Liu", "Myle Ott",
    "Colin Raffel", "Noam Shazeer", "Adam Roberts", "Catherine Olson",
    "Sharan Narang", "Michael Matena", "Yanqi Zhou", "Wei Li", "Peter J. Liu",
    "Jeff Dean", "Slav Petrov", "Noam Shazeer", "Aravindh Mahendran",
    "Peter J. Liu", "Andrew Dai", "Sebastian Borgeaud", "Andy Jones",
]

# Abstract templates for different categories
ABSTRACT_TEMPLATES = [
    "We present a new approach to {topic} that achieves state-of-the-art results on multiple benchmarks. Our method builds on transformer architecture and introduces novel techniques for {aspect}. Experiments on {domain} tasks show significant improvements over previous methods.",
    "This paper investigates the application of {topic} to {domain}. We propose a novel framework that combines the strengths of {aspect} with scalable training procedures. Our approach demonstrates improved generalization and sample efficiency compared to existing methods.",
    "We study the properties of {topic} in large-scale settings. Through extensive experiments on {domain}, we discover unexpected behaviors and propose practical improvements. Our findings suggest that {aspect} plays a crucial role in achieving better performance.",
    "Large-scale {topic} has emerged as a promising direction for AI research. In this work, we explore {aspect} and its impact on {domain}. We introduce new training techniques that enable more efficient learning and better final performance.",
    "We introduce a new method for {topic} that addresses limitations of previous approaches. Our key insight is that {aspect} can be leveraged to improve {domain}. Experimental results validate the effectiveness of our proposed approach.",
]

TOPICS = [
    "language model pre-training",
    "attention mechanisms",
    "neural network architectures",
    "few-shot learning",
    "transfer learning",
    "model scaling",
    "efficient transformers",
    "prompt engineering",
    "in-context learning",
    "reinforcement learning from human feedback",
    "constitutional AI",
    "mixture of experts",
    "parameter-efficient fine-tuning",
    "chain-of-thought reasoning",
]

ASPECTS = [
    "attention computation",
    "gradient flow optimization",
    "representation learning",
    "computational efficiency",
    "task generalization",
    "sample efficiency",
    "model compression",
    "knowledge transfer",
    "multi-task learning",
    "adversarial robustness",
]

DOMAINS = [
    "natural language understanding",
    "text generation",
    "question answering",
    "machine translation",
    "text classification",
    "summarization",
    "dialogue systems",
    "code generation",
]


def generate_abstract() -> str:
    """Generate a realistic abstract for a research paper."""
    template = random.choice(ABSTRACT_TEMPLATES)
    return template.format(
        topic=random.choice(TOPICS),
        aspect=random.choice(ASPECTS),
        domain=random.choice(DOMAINS),
    )


def generate_papers(num_papers: int = 50) -> List[Dict[str, Any]]:
    """Generate mock research papers with metadata."""
    papers = []
    
    # Use predefined titles for the first set (seminal works)
    num_predefined = min(num_papers, len(PAPER_TITLES))
    
    for i in range(num_papers):
        if i < num_predefined:
            title = PAPER_TITLES[i]
        else:
            # Generate additional papers with variations
            title = f"{random.choice(TOPICS).title()}: {random.choice(ASPECTS).title()} Approach"
        
        paper = {
            "title": title,
            "abstract": generate_abstract(),
            "authors": random.sample(AUTHORS, k=random.randint(1, 4)),
            "year": random.randint(2017, 2024),
            "category": random.choice(CATEGORIES),
            "citation_count": random.randint(0, 500),
        }
        papers.append(paper)
    
    return papers


def create_citation_graph(papers: List[Dict], max_citations: int = 5) -> Dict[str, List[str]]:
    """Create a citation graph where each paper cites 2-5 other papers."""
    citations = {}
    num_papers = len(papers)
    
    for i in range(num_papers):
        # Papers cite earlier papers (realistic citation order)
        max_cite = min(i, max_citations) if i > 0 else 0
        num_citations = random.randint(0, max_cite)
        
        if num_citations > 0:
            cited_indices = random.sample(range(i), num_citations)
            citations[papers[i]["title"]] = [papers[j]["title"] for j in cited_indices]
    
    return citations


def compute_embeddings(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    """Compute embeddings for a list of texts using sentence-transformers."""
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"Computing embeddings for {len(texts)} papers...")
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


# ============================================================================
# RUSHDB OPERATIONS
# ============================================================================

def check_existing_data(db: RushDB) -> bool:
    """Check if data has already been seeded."""
    result = db.labels.find({})
    for label in result.data:
        if label.name == "PAPER":
            return label.count > 0
    return False


def seed_papers(db: RushDB) -> int:
    """Seed the database with research papers."""
    print("\n=== Seeding Research Papers ===\n")
    
    # Check for existing data
    if check_existing_data(db):
        result = db.labels.find({})
        for label in result.data:
            if label.name == "PAPER":
                print(f"Data already exists ({label.count} papers). Skipping seed.")
                return label.count
    
    # Generate mock papers
    print("Generating 50 mock research papers...")
    papers = generate_papers(50)
    
    # Create citation graph
    print("Creating citation graph...")
    citations = create_citation_graph(papers)
    
    # Compute embeddings for abstracts
    print("Computing embeddings for abstracts...")
    abstracts = [p["abstract"] for p in papers]
    embeddings = compute_embeddings(abstracts)
    
    # Create vector index first (external index for pre-computed vectors)
    print("\nCreating vector index for abstracts...")
    index = db.ai.indexes.create({
        "label": "PAPER",
        "propertyName": "abstract",
        "sourceType": "external",
        "dimensions": 384,  # all-MiniLM-L6-v2 outputs 384-dim vectors
        "similarityFunction": "cosine",
    })
    index_id = index.data["__id"]
    print(f"Vector index created: {index_id}")
    
    # Create papers with inline vectors using transaction
    print("\nIngesting papers into RushDB...")
    created_papers = []
    
    with db.transactions.begin() as tx:
        for i, paper in enumerate(papers):
            if i % 10 == 0:
                print(f"  Creating paper {i+1}/{len(papers)}...")
            
            # Create paper with inline vector embedding
            record = db.records.create(
                label="PAPER",
                data={
                    "title": paper["title"],
                    "abstract": paper["abstract"],
                    "authors": paper["authors"],
                    "year": paper["year"],
                    "category": paper["category"],
                    "citation_count": paper["citation_count"],
                },
                vectors=[{"propertyName": "abstract", "vector": embeddings[i]}],
                transaction=tx,
            )
            created_papers.append(record)
    
    print(f"\nCreated {len(created_papers)} papers.")
    
    # Create citation relationships
    print("\nCreating citation relationships...")
    title_to_record = {record["title"]: record for record in created_papers}
    citation_count = 0
    
    with db.transactions.begin() as tx:
        for citing_title, cited_titles in citations.items():
            citing_record = title_to_record.get(citing_title)
            if citing_record:
                for cited_title in cited_titles:
                    cited_record = title_to_record.get(cited_title)
                    if cited_record:
                        db.records.attach(
                            source=citing_record,
                            target=cited_record,
                            options={"type": "CITES", "direction": "out"},
                            transaction=tx,
                        )
                        citation_count += 1
    
    print(f"Created {citation_count} citation relationships.")
    
    # Verify index stats
    stats = db.ai.indexes.stats(index_id)
    print(f"\nVector index stats: {stats.data['indexedRecords']}/{stats.data['totalRecords']} records indexed")
    
    return len(created_papers)


def main():
    """Main entry point for the seed script."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment.")
        print("Please copy .env.example to .env and add your API key.")
        return
    
    print("Connecting to RushDB...")
    db = RushDB(api_key)
    print("Connected successfully!\n")
    
    num_papers = seed_papers(db)
    print(f"\n=== Seed Complete ===")
    print(f"Total papers: {num_papers}")
    print("\nYou can now run `python main.py` to explore the data.")


if __name__ == "__main__":
    main()
