"""
Seed script for Node vs Edge Indexing Tutorial.

Creates a research paper knowledge graph with:
- Document nodes (papers with title and content)
- Author nodes (researchers)
- WRITTEN_BY edges (document -> author)
- CITES edges (document -> document) with excerpt property

This demonstrates how both nodes AND edges can be vectorized for semantic search.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
RUSHDB_URL = os.getenv("RUSHDB_URL")

if not API_KEY:
    raise ValueError("API_KEY not found in environment. Copy .env.example to .env and add your key.")

# Initialize RushDB client
db = RushDB(API_KEY, url=RUSHDB_URL) if RUSHDB_URL else RushDB(API_KEY)

# Sample research papers with meaningful content
PAPERS = [
    {
        "title": "Attention Is All You Need",
        "content": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"]
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "content": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.",
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"]
    },
    {
        "title": "GPT-3: Language Models Are Few-Shot Learners",
        "content": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by task-specific fine-tuning. We demonstrate that scaling up language models significantly improves task-agnostic, few-shot performance. Here we show that scaling up LM can be done in a data-efficient manner, even in the low-resource regime. The core idea is to use language models to learn to perform tasks from very few examples by conditioning on input and output pairs.",
        "authors": ["Tom Brown", "Benjamin Mann", "Nick Ryder"]
    },
    {
        "title": "Graph Neural Networks for Molecular Property Prediction",
        "content": "Graph neural networks have emerged as a powerful tool for learning from graph-structured data. In the domain of molecular property prediction, molecules can be naturally represented as graphs, where atoms are nodes and bonds are edges. We present a message-passing neural network architecture for learning molecular fingerprints that achieves state-of-the-art performance on multiple molecular property prediction benchmarks. The key innovation is the iterative aggregation of information from neighboring atoms to build molecular representations.",
        "authors": ["Justin Gilmer", "Sanjay S. Dwivedi", "William Hamilton"]
    },
    {
        "title": "Neural Message Passing for Quantum Chemistry",
        "content": "Machine learning for quantum chemistry has emerged as a promising approach to approximate the quantum chemical calculations that underlie molecular simulations. We propose a message passing neural network architecture that learns to predict chemical properties of molecules directly from their graphical structure. The model operates on graph representations of molecules and uses a learned message function to propagate information between atoms, allowing the network to learn rich representations of the molecular graph structure.",
        "authors": ["Justin Gilmer", "Sanjay S. Dwivedi", "William Hamilton"]
    },
    {
        "title": "Deep Learning for Code Understanding",
        "content": "Understanding source code is a challenging task due to the structured nature of programming languages. We present a novel approach to learning semantic representations of code using graph neural networks. By modeling code as abstract syntax trees and data flow graphs, our model captures both syntactic and semantic information. Experiments on code summarization and code search tasks demonstrate that learned representations can capture semantic similarity between code snippets that goes beyond surface-level syntax.",
        "authors": ["Miltiadis Allamanis", "Marc Brockschmidt", "Mateusz Odstawski"]
    },
    {
        "title": "Pathformer: Graph Transformers for Molecular Property Prediction",
        "content": "Path-based molecular representations have shown promise for property prediction tasks. We introduce Pathformer, a graph transformer architecture that incorporates path information into the attention mechanism. Unlike previous approaches that treat molecules as simple graph structures, Pathformer explicitly models chemical paths and uses them to enhance molecular representations. Our experiments on benchmarks including QM9 and PCQM4M demonstrate significant improvements over existing methods.",
        "authors": ["Jiaxuan Lei", "Dian Wang", "Ming Li"]
    },
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive Tasks",
        "content": "Large language models can store vast amounts of knowledge in their parameters, but knowledge access remains limited. We propose retrieval-augmented generation (RAG) as a paradigm for knowledge-intensive tasks. RAG combines pre-trained parametric knowledge with non-parametric retrieval mechanisms. By retrieving relevant documents and conditioning the language model on them, RAG systems can access up-to-date information and can be easily updated without retraining. We evaluate RAG on open-domain question answering, conversational search, and summarization tasks.",
        "authors": ["Patrick Lewis", "Ethan Perez", "Daphne Raposo"]
    }
]

# Citation relationships with excerpts
CITATIONS = [
    ("Attention Is All You Need", "BERT: Pre-training of Deep Bidirectional Transformers",
     "BERT builds on the Transformer encoder architecture introduced in the original Transformer paper. The key innovation of using bidirectional self-attention allows BERT to learn contextual representations from both directions."),
    ("BERT: Pre-training of Deep Bidirectional Transformers", "GPT-3: Language Models Are Few-Shot Learners",
     "While BERT and GPT use different pre-training objectives (masked LM vs language modeling), GPT-3 extends the LM approach with in-context learning, demonstrating that scale alone enables few-shot capabilities."),
    ("Attention Is All You Need", "Neural Message Passing for Quantum Chemistry",
     "The message passing framework in our model extends the attention mechanism concept to graph-structured data, where each node aggregates information from its neighbors through learned message functions."),
    ("Neural Message Passing for Quantum Chemistry", "Graph Neural Networks for Molecular Property Prediction",
     "Message passing neural networks provide a unified framework for learning on graphs, which we extend with improved aggregation strategies for molecular graphs with bond information."),
    ("Graph Neural Networks for Molecular Property Prediction", "Pathformer: Graph Transformers for Molecular Property Prediction",
     "Our graph transformer architecture incorporates path information to capture long-range dependencies in molecular graphs that are missed by simple node-level aggregation approaches."),
    ("Retrieval-Augmented Generation for Knowledge-Intensive Tasks", "BERT: Pre-training of Deep Bidirectional Transformers",
     "RAG models use dense retrieval with BERT-based encoders to index and retrieve relevant documents, demonstrating the versatility of pre-trained language models for retrieval tasks."),
    ("Retrieval-Augmented Generation for Knowledge-Intensive Tasks", "GPT-3: Language Models Are Few-Shot Learners",
     "GPT-3's few-shot capabilities complement retrieval approaches, as the large LM can effectively combine retrieved information with its pre-trained knowledge for knowledge-intensive tasks."),
    ("Deep Learning for Code Understanding", "Attention Is All You Need",
     "Our graph attention mechanism builds on the Transformer architecture, adapting self-attention to capture dependencies in code syntax trees and data flow graphs.")
]


def check_existing_data():
    """Check if data already exists to avoid duplicate seeding."""
    result = db.records.find({"labels": ["Document"], "limit": 1})
    return len(result.data) > 0


def seed_data():
    """Seed the database with research paper data."""
    print("\n📚 Seeding research paper knowledge graph...\n")
    
    created_papers = {}
    created_authors = {}
    
    # Create papers and authors
    print("Creating Document nodes...")
    for i, paper in enumerate(PAPERS):
        doc = db.records.create(
            label="Document",
            data={
                "title": paper["title"],
                "content": paper["content"]
            }
        )
        created_papers[paper["title"]] = doc
        
        # Create authors
        for author_name in paper["authors"]:
            if author_name not in created_authors:
                author = db.records.create(
                    label="Author",
                    data={"name": author_name}
                )
                created_authors[author_name] = author
                print(f"  ✓ Created Author: {author_name}")
            
            # Create WRITTEN_BY relationship
            db.records.attach(
                source=doc,
                target=created_authors[author_name],
                options={"type": "WRITTEN_BY", "direction": "out"}
            )
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1} papers...")
        
        print(f"  ✓ Created Document: {paper['title']}")
    
    print(f"\n📎 Creating citation edges with excerpts...")
    # Create citation relationships
    for source_title, target_title, excerpt in CITATIONS:
        source_doc = created_papers.get(source_title)
        target_doc = created_papers.get(target_title)
        
        if source_doc and target_doc:
            db.records.attach(
                source=source_doc,
                target=target_doc,
                options={
                    "type": "CITES",
                    "direction": "out",
                    "excerpt": excerpt
                }
            )
            print(f"  ✓ {source_title} CITES {target_title} (excerpt: {len(excerpt)} chars)")
    
    # Print summary
    print("\n📊 Seeding complete! Summary:")
    docs = db.records.find({"labels": ["Document"], "limit": 1000})
    authors = db.records.find({"labels": ["Author"], "limit": 1000})
    print(f"   - {len(docs.data)} Document nodes")
    print(f"   - {len(authors.data)} Author nodes")
    print(f"   - {len(CITATIONS)} citation edges (each with excerpt property)")
    print(f"\n✅ Data seeded successfully!")


if __name__ == "__main__":
    print("=" * 60)
    print("  Node vs Edge Indexing Tutorial - Seed Script")
    print("=" * 60)
    
    if check_existing_data():
        print("\n⚠️  Data already exists (found Document nodes).")
        print("   Skipping seeding to avoid duplicates.")
        print("   To re-seed, delete existing records first.\n")
    else:
        seed_data()
