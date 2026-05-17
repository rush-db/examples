#!/usr/bin/env python3
"""
Seed script for the Source Attribution Demo.

Creates a realistic set of AI research paper summaries with:
- Document nodes (research papers)
- Passage nodes (chunked text with vectors)
- Claim nodes (extracted factual claims)
- Graph relationships (CONTAINS, SUPPORTS, CITES)

This demonstrates RushDB's graph + vector dual-layer architecture
for source attribution and grounded generation.
"""

import os
import sys
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# =============================================================================
# MOCK RESEARCH DATA
# =============================================================================

RESEARCH_PAPERS = [
    {
        "id": "paper-001",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani, A.", "Shazeer, N.", "Parmar, N."],
        "year": 2017,
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
        "passages": [
            {
                "text": "The Transformer architecture relies entirely on self-attention mechanisms to compute representations of its input and output without using sequence-aligned recurrent architecture.",
                "chunk_index": 0
            },
            {
                "text": "Self-attention allows each position in the model to attend to all positions in the previous layer, enabling direct dependency modeling between distant positions.",
                "chunk_index": 1
            },
            {
                "text": "Parallelization across training examples enables significant computational efficiency, making transformers scalable to larger datasets and model sizes.",
                "chunk_index": 2
            }
        ],
        "claims": [
            "Transformers eliminate the need for recurrence by using pure attention mechanisms",
            "Self-attention enables direct modeling of dependencies between any positions"
        ]
    },
    {
        "id": "paper-002",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": ["Devlin, J.", "Chang, M.", "Lee, K.", "Toutanova, K."],
        "year": 2018,
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
        "passages": [
            {
                "text": "BERT uses bidirectional self-attention by conditioning on both left and right context in all layers, unlike previous models that read the sequence either left-to-right or combined left-to-right with right-to-left.",
                "chunk_index": 0
            },
            {
                "text": "The pre-training task uses masked language modeling where random tokens are replaced with a [MASK] token and the model learns to predict the original token from context.",
                "chunk_index": 1
            },
            {
                "text": "Fine-tuning BERT on downstream tasks requires minimal architecture changes, with only an additional output layer added to the pre-trained model.",
                "chunk_index": 2
            }
        ],
        "claims": [
            "Bidirectional conditioning allows BERT to capture context from both directions simultaneously",
            "Masked language modeling enables self-supervised pre-training on large unlabeled corpora"
        ]
    },
    {
        "id": "paper-003",
        "title": "Language Models are Few-Shot Learners",
        "authors": ["Brown, T.", "Mann, B.", "Ryder, N."],
        "year": 2020,
        "abstract": "Recent work has demonstrated substantial gains on many NLP tasks by pre-training on a large corpus of text followed by fine-tuning on a specific task.",
        "passages": [
            {
                "text": "GPT-3 with 175 billion parameters can perform diverse tasks through in-context learning without gradient updates, using few-shot, one-shot, or zero-shot prompting.",
                "chunk_index": 0
            },
            {
                "text": "Scaling model size and training data volume correlates strongly with model capabilities, with performance improving predictably across orders of magnitude.",
                "chunk_index": 1
            },
            {
                "text": "Few-shot performance scales as a power law with model size, suggesting that larger models become more efficient learners.",
                "chunk_index": 2
            }
        ],
        "claims": [
            "Model scale is a key factor in emergent few-shot capabilities",
            "In-context learning enables task adaptation without gradient-based fine-tuning"
        ]
    },
    {
        "id": "paper-004",
        "title": "Chain-of-Thought Prompting Elicits Reasoning",
        "authors": ["Wei, J.", "Wang, X.", "Schuurmans, D."],
        "year": 2022,
        "abstract": "We explore how generating a chain of thought—a series of intermediate reasoning steps—significantly improves the ability of large language models to perform complex reasoning.",
        "passages": [
            {
                "text": "Chain-of-thought prompting improves performance on arithmetic, commonsense, and symbolic reasoning tasks by making the model's reasoning process explicit.",
                "chunk_index": 0
            },
            {
                "text": "The intermediate reasoning steps serve as soft constraints that guide the model toward correct solutions, similar to how human experts work through problems step-by-step.",
                "chunk_index": 1
            },
            {
                "text": "Scaling model size alone does not reliably improve reasoning; chain-of-thought prompting provides an alternative path to better reasoning for smaller models.",
                "chunk_index": 2
            }
        ],
        "claims": [
            "Explicit reasoning chains improve complex task performance across domains",
            "Chain-of-thought enables smaller models to achieve reasoning previously requiring larger models"
        ]
    },
    {
        "id": "paper-005",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP",
        "authors": ["Lewis, P.", "Perez, E.", "Piktus, A."],
        "year": 2020,
        "abstract": "We demonstrate general-purpose language model fine-tuning using retrieval-augmented generation (RAG), which combines pre-trained parametric and non-parametric memory.",
        "passages": [
            {
                "text": "RAG combines the power of pre-trained language models with external knowledge retrieval, allowing models to access up-to-date information beyond their training data.",
                "chunk_index": 0
            },
            {
                "text": "The retriever finds relevant passages from a large corpus, and the generator produces answers conditioned on both the input and the retrieved content.",
                "chunk_index": 1
            },
            {
                "text": "RAG models can be updated simply by changing the retrieval index without requiring re-training, making them adaptable to evolving knowledge bases.",
                "chunk_index": 2
            }
        ],
        "claims": [
            "Retrieval augments language models with access to external, dynamic knowledge",
            "Separating retrieval and generation enables modular updates to either component"
        ]
    }
]

# Example questions for the demo
DEMO_QUESTIONS = [
    "How does retrieval improve language model performance?",
    "What role does model scale play in AI capabilities?",
    "How do transformers enable parallel processing?"
]


# =============================================================================
# SEEDING LOGIC
# =============================================================================

def get_embedding_model():
    """Load the sentence transformer model (cached after first call)."""
    print("   Loading embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def seed_database():
    """
    Seed RushDB with research documents, passages, and claims.
    
    Creates a graph structure:
    - Document nodes (research papers)
    - Passage nodes (chunked text with vectors)
    - Claim nodes (extracted factual claims)
    - Relationships: CONTAINS (Doc->Passage), CITES (Claim->Passage)
    """
    api_key = os.environ.get('RUSHDB_API_KEY')
    if not api_key:
        print("❌ Error: RUSHDB_API_KEY not found in environment")
        print("   Please copy .env.example to .env and add your API key")
        sys.exit(1)
    
    print("\n🌱 Seeding RushDB with research documents...\n")
    
    db = RushDB(api_key)
    model = get_embedding_model()
    
    # --- Clean up existing demo data (idempotent) ---
    print("   Cleaning up existing demo records...")
    for label in ["Question", "Answer", "Claim", "Passage", "Document"]:
        try:
            db.records.delete({"labels": [label], "where": {}})
        except Exception:
            pass  # Ignore if no records exist
    
    # --- Create vector index for passages ---
    print("   Setting up vector index...")
    try:
        existing_indexes = db.ai.indexes.find()
        for idx in existing_indexes.data:
            if idx.get('label') == 'Passage' and idx.get('propertyName') == 'content':
                print(f"   Vector index already exists: Passage.content")
                index_id = idx.get('__id')
                break
        else:
            response = db.ai.indexes.create({
                "label": "Passage",
                "propertyName": "content",
                "sourceType": "external",
                "dimensions": 384  # all-MiniLM-L6-v2 outputs 384 dimensions
            })
            index_id = response.data.get('__id')
            print(f"   Created vector index: Passage.content (id: {index_id})")
    except Exception as e:
        print(f"   Warning: Could not create vector index: {e}")
        index_id = None
    
    # --- Process each research paper ---
    total_passages = 0
    total_claims = 0
    passage_vectors = []  # Collect for batch upsert
    
    for paper_idx, paper in enumerate(RESEARCH_PAPERS):
        print(f"\n✅ Created Document: '{paper['title']}'")
        
        # Create Document node
        document = db.records.create(
            label="Document",
            data={
                "title": paper["title"],
                "authors": paper["authors"],
                "year": paper["year"],
                "paper_id": paper["id"],
                "abstract": paper["abstract"]
            }
        )
        
        passages_in_paper = []
        
        # Create Passage nodes with embeddings
        for passage_data in paper["passages"]:
            passage_text = passage_data["text"]
            
            # Generate embedding
            embedding = model.encode(passage_text).tolist()
            
            # Create passage record (will add vectors after)
            with db.transactions.begin() as tx:
                passage = db.records.create(
                    label="Passage",
                    data={
                        "text": passage_text,
                        "chunk_index": passage_data["chunk_index"],
                        "source_document": paper["title"]
                    },
                    transaction=tx
                )
                
                # Link passage to document
                db.records.attach(
                    source=document,
                    target=passage,
                    options={"type": "CONTAINS", "direction": "out"},
                    transaction=tx
                )
            
            passages_in_paper.append(passage)
            
            # Collect vector for batch upsert
            if index_id:
                passage_vectors.append({
                    "recordId": passage.id,
                    "vector": embedding
                })
            
            total_passages += 1
            
            if total_passages % 5 == 0:
                print(f"   📄 {total_passages} passages created...")
        
        print(f"   └─ {len(passages_in_paper)} passages chunked")
        
        # Create Claim nodes linked to passages
        claims_in_paper = []
        for claim_text in paper["claims"]:
            with db.transactions.begin() as tx:
                claim = db.records.create(
                    label="Claim",
                    data={
                        "text": claim_text,
                        "extracted_from": paper["title"]
                    },
                    transaction=tx
                )
                
                # Link claim to the first passage (simplified - in production,
                # would use NLP to determine which passage supports which claim)
                db.records.attach(
                    source=claim,
                    target=passages_in_paper[0],
                    options={"type": "CITES", "direction": "out"},
                    transaction=tx
                )
            
            claims_in_paper.append(claim)
            total_claims += 1
        
        print(f"   └─ {len(claims_in_paper)} claims extracted")
    
    # --- Upsert all vectors to the index ---
    if index_id and passage_vectors:
        print(f"\n   💾 Upserting {len(passage_vectors)} passage vectors to index...")
        db.ai.indexes.upsert_vectors(index_id, {"items": passage_vectors})
        print("   ✅ All vectors indexed")
    
    # --- Store demo questions ---
    print("\n   📝 Creating demo questions...")
    for q_idx, question_text in enumerate(DEMO_QUESTIONS):
        db.records.create(
            label="Question",
            data={
                "text": question_text,
                "order": q_idx
            }
        )
    
    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"✅ Seeded successfully!")
    print(f"   • Documents: {len(RESEARCH_PAPERS)}")
    print(f"   • Passages: {total_passages} (all vectorized)")
    print(f"   • Claims: {total_claims}")
    if index_id:
        print(f"   • Vector Index: Passage.content (active)")
    print(f"{'='*60}\n")
    
    return {
        "documents": len(RESEARCH_PAPERS),
        "passages": total_passages,
        "claims": total_claims,
        "index_id": index_id
    }


if __name__ == "__main__":
    seed_database()
