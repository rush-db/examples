"""
Seed script for Graph-Based Prompt Compression Demo

Creates synthetic research paper data with:
- DOCUMENT records (research papers)
- CHUNK records (semantic sections)
- CONCEPT records (extracted terms)
- Relationships for graph traversal

Run: python seed.py
Idempotent: safe to run multiple times (checks for existing data)
"""

import os
import sys
import random
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# Research paper content for seeding
RESEARCH_PAPERS = [
    {
        "title": "Attention Is All You Need",
        "authors": ["Vaswani", "Shazeer", "Parmar"],
        "year": 2017,
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
        "chunks": [
            {"title": "Introduction", "body": "Neural network architectures have historically relied on recurrence and convolution. The Transformer introduces a novel approach using multi-head self-attention to model dependencies without sequential processing. This allows for parallel training and improved long-range dependency handling. The attention mechanism computes a weighted sum of values based on query-key compatibility."},
            {"title": "Background", "body": "Reducing sequential computation has been a long-standing goal. Extended neural GPU, ByteNet, and ConvS2S used convolutional neural networks as building blocks. However, the computational complexity to relate positions in these models grows with distance. The Transformer reduces this to constant-time operations through self-attention."},
            {"title": "Model Architecture", "body": "The Transformer follows an encoder-decoder structure. The encoder maps input sequences to continuous representations. The decoder generates output sequences auto-regressively. Each layer contains sub-layers: multi-head self-attention and position-wise fully connected feed-forward network. Residual connections around each sub-layer are used."},
            {"title": "Multi-Head Attention", "body": "Multi-head attention allows the model to jointly attend to information from different representation subspaces. Instead of performing a single attention function, we linearly project queries, keys, and values h times. Each head operates on reduced dimensions, reducing computational cost while maintaining representation power."},
            {"title": "Positional Encoding", "body": "Since the Transformer contains no recurrence or convolution, positional encodings are added to input embeddings to incorporate sequence order. These encodings use sine and cosine functions of different frequencies. The resulting pattern is relative position information usable by attention heads."},
        ]
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": ["Devlin", "Chang", "Lee", "Toutanova"],
        "year": 2018,
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language models, BERT is designed to pre-train deep bidirectional representations.",
        "chunks": [
            {"title": "Overview", "body": "BERT uses a masked language model pre-training objective inspired by the Cloze task. This allows the representation to fuse context from both directions. Unlike left-to-right language models, the bidirectional context captures full semantics. The architecture is a multi-layer Transformer encoder."},
            {"title": "Input Representation", "body": "BERT input representation combines token embeddings, segment embeddings, and positional embeddings. A [CLS] token is added at the beginning for classification tasks. Sentence pairs are distinguished using segment embeddings and a [SEP] separator token. WordPiece tokenization handles out-of-vocabulary words."},
            {"title": "Pre-training Objectives", "body": "Two objectives are used: Masked Language Model (MLM) and Next Sentence Prediction (NSP). MLM randomly masks 15% of tokens and predicts the original vocabulary. NSP trains understanding of sentence relationships, important for question answering and natural language inference tasks."},
            {"title": "Fine-tuning", "body": "After pre-training, BERT can be fine-tuned with additional output layers for specific tasks. The entire model is fine-tuned using task-specific data. This approach achieves state-of-the-art results on eleven natural language processing tasks including question answering and textual entailment."},
        ]
    },
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors": ["Lewis", "Perez", "Lv"],
        "year": 2020,
        "abstract": "We demonstrate general-purpose fine-tuning of a language model on information extraction, question answering, and fact verification tasks by augmenting the model with a retrieval component trained on a large corpus.",
        "chunks": [
            {"title": "Motivation", "body": "Large language models store knowledge implicitly during pre-training. However, accessing and manipulating this knowledge is difficult. Retrieval-augmented generation provides explicit access to knowledge. This approach improves interpretability and allows updating knowledge without retraining."},
            {"title": "Architecture", "body": "RAG models combine a retriever and a sequence-to-sequence generator. The retriever uses dense passage retrieval with BERT-based encoder. Documents are indexed and retrieved using maximum inner product search. The generator is a BART seq2seq model that conditions on both the input and retrieved content."},
            {"title": "Training", "body": "The retriever and generator are trained jointly end-to-end. The retriever learns to find relevant documents through backpropagation. This differs from frozen retrieval in that both components adapt to the target task. The joint training leads to better retrieval for specific domains."},
            {"title": "Knowledge Updates", "body": "A key advantage of RAG is the ability to update knowledge. Simply update the document index without retraining the entire model. This enables real-time knowledge updates for changing information. Fine-tuning can also focus on the generator when knowledge is already indexed."},
            {"title": "Applications", "body": "RAG excels at knowledge-intensive tasks like open-domain question answering. It reduces hallucinations by grounding responses in retrieved facts. The approach also improves on tasks requiring precise citation of sources. Multiple retrieved passages can be combined for complex reasoning."},
        ]
    },
    {
        "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "authors": ["Wei", "Wang", "Schuurmans"],
        "year": 2022,
        "abstract": "We explore how generating a chain of thought, a series of intermediate reasoning steps, significantly improves the ability of large language models to perform complex reasoning tasks.",
        "chunks": [
            {"title": "Core Insight", "body": "Standard prompting provides input-output examples. Chain-of-thought prompting includes reasoning steps in the examples. This allows models to generate intermediate reasoning before final answers. The approach requires no gradient updates or task-specific engineering."},
            {"title": "Arithmetic Reasoning", "body": "Chain-of-thought prompting improves performance on arithmetic tasks like GSM8K. The model learns to break down multi-step problems. Each step involves simple calculations that combine to solve complex problems. Performance scales with model size."},
            {"title": "Common Sense Reasoning", "body": "Beyond mathematics, chain-of-thought improves reasoning on commonsense problems. The approach helps models explicitly reason about physical and social interactions. Generated reasoning often resembles human problem-solving strategies. The method works across diverse domains including object tracking and temporal reasoning."},
            {"title": "Prompting Strategies", "body": "Few-shot chain-of-thought requires diverse reasoning examples in the prompt. Adding simple phrases like 'let's think step by step' triggers zero-shot reasoning. Ensemble methods can combine multiple reasoning paths. Self-consistency sampling further improves results by selecting the most common answer."},
        ]
    },
    {
        "title": "Graph Neural Networks: A Survey",
        "authors": ["Wu", "Zhang", "Southerland"],
        "year": 2021,
        "abstract": "Graph neural networks have become powerful tools for graph representation learning. This survey provides a comprehensive overview of graph neural networks for researchers and practitioners.",
        "chunks": [
            {"title": "Introduction to Graphs", "body": "Graphs naturally represent relationships in many domains: social networks, molecular structures, knowledge graphs. Traditional machine learning struggled with graph-structured data. Graph neural networks provide an end-to-end framework for graph representation learning. The key challenge is defining operations that respect graph structure."},
            {"title": "Message Passing Framework", "body": "Most GNN architectures follow a message passing framework. Each node aggregates information from its neighbors. The aggregation function can be mean, sum, or attention-based. Multiple rounds of message passing let nodes collect information from distant parts of the graph. This produces increasingly contextualized representations."},
            {"title": "Graph Attention Networks", "body": "Graph Attention Networks (GATs) use masked self-attention to weight neighbor contributions. Unlike convolutions with fixed kernels, attention learns dynamic weights. Multi-head attention provides ensemble benefits. GATs have achieved state-of-the-art on many node classification benchmarks."},
            {"title": "Knowledge Graph Applications", "body": "Knowledge graphs benefit from GNN reasoning. Entities and relations form a graph structure. Link prediction tasks predict missing relationships. Query answering uses graph traversal to find answer entities. Combining GNNs with knowledge graph embeddings enhances reasoning capabilities."},
            {"title": "Scalability Challenges", "body": "GNNs face scalability issues on large graphs. Full-batch training on massive graphs is memory-prohibitive. Mini-batch approaches sample local neighborhoods. Graph sampling methods balance efficiency and accuracy. Distributed training enables very large-scale applications."},
        ]
    },
    {
        "title": "Efficient Transformers: A Survey",
        "authors": ["Tay", "Dehghani", "Bahri"],
        "year": 2022,
        "abstract": "We provide a comprehensive survey of efficient transformer models, covering techniques to reduce the quadratic complexity of self-attention.",
        "chunks": [
            {"title": "The Attention Bottleneck", "body": "Standard self-attention has quadratic complexity O(n^2) in sequence length. This limits application to sequences of a few thousand tokens. Many approaches have been proposed to make attention linear or near-linear. These include sparse, linear, and low-rank approximations."},
            {"title": "Sparse Attention Patterns", "body": "Sparse attention computes attention only on selected positions. Patterns include local windows, global tokens, and random connections. BigBird and Longformer use combinations of these patterns. The choice of pattern depends on the task and data characteristics."},
            {"title": "Linear Attention", "body": "Linear attention rewrites attention to avoid the softmax bottleneck. Kernel methods approximate the exponential similarity. Performer uses random feature maps for unbiased estimation. These methods achieve constant memory and linear time complexity."},
            {"title": "Memory Compressed Attention", "body": "Memory-compressed attention reduces the number of keys and values. Stride-based compression aggregates information across positions. This reduces computation while maintaining global context. The compression ratio is a hyperparameter to tune."},
        ]
    },
    {
        "title": "Prompt Engineering Guide",
        "authors": ["Arthropromeda Team"],
        "year": 2023,
        "abstract": "A comprehensive guide to prompt engineering techniques for large language models, covering patterns, strategies, and best practices.",
        "chunks": [
            {"title": "Fundamentals", "body": "Prompts are inputs that guide language model behavior. Well-designed prompts reduce ambiguity and improve outputs. Key elements include context, instructions, and examples. The way information is structured affects model performance significantly."},
            {"title": "Context Window Management", "body": "Context windows have finite capacity. Effective prompts maximize relevant information density. Irrelevant context can confuse models or dilute important details. Prompt compression techniques help fit more useful information. Prioritizing recent and relevant context improves results."},
            {"title": "Few-Shot Learning", "body": "Providing examples in the prompt enables few-shot learning. Examples should be diverse and representative. The format matters: consistent input-output structure helps. Too many examples can exceed context limits. Balance between coverage and context length."},
            {"title": "Chain-of-Thought Integration", "body": "Combining prompt engineering with chain-of-thought reasoning improves complex task performance. Explicit reasoning steps help models organize their thinking. This technique is especially valuable for multi-step problems. The reasoning chain itself can be compressed when context is limited."},
            {"title": "Retrieval Augmentation", "body": "Retrieval-augmented prompts combine parametric and non-parametric knowledge. Relevant documents are fetched and included in context. The retrieval quality directly impacts prompt effectiveness. Hybrid approaches use both dense and sparse retrieval for better coverage."},
        ]
    },
    {
        "title": "RAG vs Fine-tuning: A Comparative Study",
        "authors": ["AI Research Collective"],
        "year": 2024,
        "abstract": "We compare retrieval-augmented generation and fine-tuning approaches for customizing language models, analyzing trade-offs in knowledge retention, adaptability, and deployment complexity.",
        "chunks": [
            {"title": "Overview", "body": "RAG and fine-tuning are complementary approaches to model customization. RAG excels at knowledge lookup and can be updated dynamically. Fine-tuning adapts model behavior and style more deeply. Hybrid approaches combine both for optimal results."},
            {"title": "Knowledge Access", "body": "RAG provides explicit access to knowledge through retrieval. This makes it suitable for frequently changing information. Fine-tuned models store knowledge implicitly in weights. Updating knowledge requires expensive retraining. RAG enables fine-grained control over which knowledge is accessed."},
            {"title": "Context Sensitivity", "body": "RAG can include user-provided context dynamically. This allows queries to be answered with document-specific information. Fine-tuned models rely solely on training data. RAG excels at one-shot learning on new domains. The choice depends on whether context can be retrieved."},
            {"title": "Training Costs", "body": "Fine-tuning requires significant compute and labeled data. RAG only requires building an index, which is simpler. Index updates are cheap compared to model retraining. However, RAG incurs retrieval latency at inference time. Fine-tuned models may be faster but less adaptable."},
            {"title": "Hallucination Trade-offs", "body": "Both approaches can hallucinate incorrect information. RAG hallucinations can be traced to retrieved documents. Fine-tuning hallucinations emerge from learned patterns. Grounding RAG responses with citations reduces hallucination risk. Combining retrieval with confidence scoring helps identify unreliable outputs."},
        ]
    },
    {
        "title": "Context Compression in Long-Context Models",
        "authors": ["Mueller", "Chen", "Park"],
        "year": 2024,
        "abstract": "We present techniques for compressing long contexts while preserving critical information, addressing the challenge of processing documents that exceed model context limits.",
        "chunks": [
            {"title": "Problem Statement", "body": "Long documents exceed model context windows regularly. Truncation loses information. Naive chunking ignores semantic coherence. Context compression must identify and preserve essential information. This requires understanding document structure and key concepts."},
            {"title": "Semantic Chunking", "body": "Semantic chunking groups related content together. Sentences discussing similar topics are grouped. This preserves discourse coherence better than fixed-size chunks. Overlap between chunks maintains cross-chunk dependencies. Semantic boundaries often align with document structure."},
            {"title": "Hierarchical Summarization", "body": "Hierarchical summarization compresses at multiple levels. Documents are summarized, then chunk summaries are summarized. This creates a hierarchy of abstractions. Query-relevant summaries can be retrieved at appropriate granularity. The approach trades accuracy for compression ratio."},
            {"title": "Selective Context", "body": "Selective context identifies and keeps only relevant parts. Redundant, trivial, and irrelevant content is removed. Important entities and relations are preserved. The remaining context is maximally informative. This approach requires understanding what information is task-relevant."},
            {"title": "Attention-Based Selection", "body": "Attention patterns reveal which context influences outputs. We can identify high-attention context and prune others. This preserves information the model actually uses. Query-dependent attention highlights relevant parts. The selection can be made more efficient with learned filters."},
        ]
    },
    {
        "title": "Knowledge Graphs for Enterprise AI",
        "authors": ["Enterprise AI Institute"],
        "year": 2024,
        "abstract": "Knowledge graphs provide structured representations of enterprise data, enabling sophisticated querying and reasoning capabilities for AI systems.",
        "chunks": [
            {"title": "Enterprise Data Challenges", "body": "Enterprise data is often siloed and inconsistent. Knowledge graphs unify diverse data sources through shared semantics. Entities are normalized across systems. Relationships capture business context. This structured view enables better AI applications."},
            {"title": "Graph Construction", "body": "Knowledge graphs are built through entity extraction and relationship detection. Named entity recognition identifies key entities. Coreference resolution links entity mentions. Relation extraction finds connections between entities. Human curation ensures quality and coverage."},
            {"title": "Query Processing", "body": "Graph queries traverse relationships to find answers. Path queries follow chains of relationships. Pattern matching finds subgraph structures. Ranking algorithms prioritize answer candidates. Graph query optimization ensures responsive performance."},
            {"title": "Integration with LLMs", "body": "Knowledge graphs complement large language models. Graphs provide reliable structured knowledge. LLMs generate natural language from graph queries. The combination enables both precision and fluency. Context can be enriched with graph-derived information."},
            {"title": "Maintenance and Evolution", "body": "Knowledge graphs require ongoing maintenance. New data must be integrated consistently. Schema changes need careful migration. Stale knowledge should be identified and updated. Automated pipelines help maintain graph quality at scale."},
        ]
    },
]

# Pre-defined concepts to extract from chunks
CONCEPT_TEMPLATES = [
    "self-attention",
    "transformer",
    "multi-head attention",
    "positional encoding",
    "BERT",
    "bidirectional",
    "masked language model",
    "pre-training",
    "fine-tuning",
    "retrieval-augmented generation",
    "RAG",
    "knowledge graph",
    "graph neural network",
    "attention mechanism",
    "token",
    "embedding",
    "context window",
    "prompt engineering",
    "chain-of-thought",
    "few-shot learning",
    "information retrieval",
    "semantic search",
    "vector database",
    "neural network",
    "encoder-decoder",
    "feed-forward",
    "layer normalization",
    "residual connection",
    "question answering",
    "natural language inference",
    "text summarization",
    "named entity recognition",
    "coreference",
    "relation extraction",
    "link prediction",
    "hallucination",
    "context compression",
    "semantic chunking",
    "hierarchical summarization",
    "sparse attention",
    "linear attention",
    "message passing",
    "node classification",
    "knowledge base",
]


def extract_concepts(text: str) -> list[str]:
    """Extract relevant concepts from text based on predefined templates."""
    text_lower = text.lower()
    found = []
    for concept in CONCEPT_TEMPLATES:
        if concept.lower() in text_lower:
            found.append(concept)
    # Also extract capitalized phrases as potential concepts
    import re
    capitalized = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', text)
    found.extend(capitalized[:3])  # Limit additional concepts
    return list(set(found))


def check_existing_data(db: RushDB) -> bool:
    """Check if database already has seed data."""
    existing = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    return existing.total > 0


def main():
    print("Checking for existing data...")
    db = RushDB(os.environ.get("RUSHDB_API_KEY"))
    
    if check_existing_data(db):
        print("Database already contains data. Skipping seed.")
        print("To reseed, clear the database first.")
        return
    
    print("Seeding database with research paper data...\n")
    
    created_documents = []
    created_chunks = []
    created_concepts = []
    
    for doc_idx, paper in enumerate(RESEARCH_PAPERS):
        print(f"[DOC] Creating document: {paper['title']}")
        
        # Create document record
        doc_record = db.records.create(
            label="DOCUMENT",
            data={
                "title": paper["title"],
                "authors": paper["authors"],
                "year": paper["year"],
                "abstract": paper["abstract"]
            }
        )
        created_documents.append(doc_record)
        
        for chunk_idx, chunk_data in enumerate(paper["chunks"]):
            chunk_num = chunk_idx + 1
            total_chunks = len(paper["chunks"])
            
            if (doc_idx * len(paper["chunks"]) + chunk_idx + 1) % 10 == 0:
                progress = doc_idx * len(paper["chunks"]) + chunk_idx + 1
                print(f"[{progress}/~{len(RESEARCH_PAPERS) * 5}] Created chunk: {paper['title']} (chunk {chunk_num}/{total_chunks})")
            
            # Create chunk record
            chunk_record = db.records.create(
                label="CHUNK",
                data={
                    "title": chunk_data["title"],
                    "body": chunk_data["body"],
                    "position": chunk_idx,
                    "parent_document": paper["title"]
                }
            )
            created_chunks.append(chunk_record)
            
            # Link chunk to document
            db.records.attach(
                source=doc_record,
                target=chunk_record,
                options={"type": "HAS_CHUNK", "direction": "out"}
            )
            
            # Extract and create concepts
            concepts = extract_concepts(chunk_data["body"])
            
            for concept_text in concepts:
                # Check if concept already exists
                existing = db.records.find({
                    "labels": ["CONCEPT"],
                    "where": {"name": concept_text},
                    "limit": 1
                })
                
                if existing.total > 0:
                    concept_record = existing.data[0]
                else:
                    # Create new concept
                    concept_record = db.records.create(
                        label="CONCEPT",
                        data={
                            "name": concept_text,
                            "category": "technical_term"
                        }
                    )
                    if concept_record not in created_concepts:
                        created_concepts.append(concept_record)
                
                # Link chunk to concept
                db.records.attach(
                    source=chunk_record,
                    target=concept_record,
                    options={"type": "MENTIONS", "direction": "out"}
                )
    
    # Create concept relationships (RELATED_TO)
    print("\nCreating concept cross-references...")
    
    # Define concept relationships based on domain knowledge
    concept_relationships = [
        ("self-attention", "attention mechanism"),
        ("self-attention", "multi-head attention"),
        ("transformer", "self-attention"),
        ("transformer", "positional encoding"),
        ("transformer", "encoder-decoder"),
        ("BERT", "transformer"),
        ("BERT", "pre-training"),
        ("BERT", "fine-tuning"),
        ("BERT", "bidirectional"),
        ("retrieval-augmented generation", "RAG"),
        ("retrieval-augmented generation", "information retrieval"),
        ("retrieval-augmented generation", "knowledge graph"),
        ("graph neural network", "message passing"),
        ("graph neural network", "knowledge graph"),
        ("chain-of-thought", "few-shot learning"),
        ("chain-of-thought", "prompt engineering"),
        ("context window", "prompt engineering"),
        ("semantic chunking", "context compression"),
        ("hierarchical summarization", "context compression"),
        ("sparse attention", "linear attention"),
        ("multi-head attention", "sparse attention"),
        ("vector database", "semantic search"),
        ("RAG", "vector database"),
        ("knowledge graph", "entity extraction"),
        ("knowledge graph", "relation extraction"),
    ]
    
    created_rel_count = 0
    for concept_a, concept_b in concept_relationships:
        result_a = db.records.find({
            "labels": ["CONCEPT"],
            "where": {"name": concept_a},
            "limit": 1
        })
        result_b = db.records.find({
            "labels": ["CONCEPT"],
            "where": {"name": concept_b},
            "limit": 1
        })
        
        if result_a.total > 0 and result_b.total > 0:
            record_a = result_a.data[0]
            record_b = result_b.data[0]
            
            # Create bidirectional relationship
            db.records.attach(
                source=record_a,
                target=record_b,
                options={"type": "RELATED_TO", "direction": "out"}
            )
            db.records.attach(
                source=record_b,
                target=record_a,
                options={"type": "RELATED_TO", "direction": "out"}
            )
            created_rel_count += 2
    
    print(f"\n✓ Seeding complete!")
    print(f"  Documents: {len(created_documents)}")
    print(f"  Chunks: {len(created_chunks)}")
    print(f"  Concepts: {len(created_concepts)}")
    print(f"  Concept relationships: {created_rel_count}")
    
    # Create vector index for semantic search
    print("\nCreating vector index for semantic search...")
    try:
        existing_indexes = db.ai.indexes.find()
        index_exists = any(
            idx.get('label') == 'CHUNK' and idx.get('propertyName') == 'body'
            for idx in (existing_indexes.data if hasattr(existing_indexes, 'data') else [])
        )
        
        if not index_exists:
            index = db.ai.indexes.create({
                "label": "CHUNK",
                "propertyName": "body",
                "sourceType": "managed"
            })
            print("  Vector index created (managed - RushDB will handle embeddings)")
        else:
            print("  Vector index already exists")
    except Exception as e:
        print(f"  Note: Could not create vector index: {e}")
        print("  Semantic search will use text matching instead")


if __name__ == "__main__":
    main()
