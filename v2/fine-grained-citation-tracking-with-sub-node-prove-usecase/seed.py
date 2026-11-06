"""
Seed script for Fine-Grained Citation Tracking demo.

Creates a mock research corpus with:
- 5 research papers
- Multiple sections per paper
- Inter-section citations with provenance sub-nodes
- Sample insights with full provenance tracking

The script is idempotent: safe to run multiple times.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)

# Initialize embedding model
print("Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Mock data: Research papers
PAPERS_DATA = [
    {
        "title": "Attention Is All You Need",
        "year": 2017,
        "doi": "10.48550/arXiv.1706.03762",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        "abstract": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        "sections": [
            {
                "title": "Model Architecture",
                "type": "body",
                "content": "The Transformer uses multi-head self-attention to compute representations. The encoder maps an input sequence of symbol representations to a sequence of continuous representations. The decoder generates the output sequence one symbol at a time."
            },
            {
                "title": "Attention Mechanism",
                "type": "method",
                "content": "Scaled dot-product attention takes three inputs: queries Q, keys K, and values V. The output is computed as a weighted sum of values, where the weight assigned to each value is computed by a compatibility function of the query with the corresponding key."
            },
            {
                "title": "Training Results",
                "type": "result",
                "content": "The Transformer achieves better results than previous models on WMT 2014 English-to-German translation with a BLEU score of 28.4. On WMT 2014 English-to-French translation, the model achieves 41.8 BLEU score."
            }
        ]
    },
    {
        "title": "Neural Machine Translation by Jointly Learning to Align and Translate",
        "year": 2014,
        "doi": "10.48550/arXiv.1409.0473",
        "authors": ["Dzmitry Bahdanau", "Kyunghyun Cho", "Yoshua Bengio"],
        "abstract": "We propose a neural network model that learns to jointly align and translate, allowing for better translation of longer sentences.",
        "sections": [
            {
                "title": "Encoder",
                "type": "method",
                "content": "The encoder reads the source sequence X = (x1, ..., xn) and encodes it into a sequence of hidden states. We use a bidirectional RNN where the forward hidden state captures forward dependencies and the backward hidden state captures backward dependencies."
            },
            {
                "title": "Alignment Model",
                "type": "method",
                "content": "The decoder defines the conditional probability as P(yi|y1,...,yi-1,X) = g(yi-1, si, ci) where si is the hidden state at time i, and ci is the context vector computed as a weighted sum of the encoder hidden states."
            },
            {
                "title": "Long Sentence Performance",
                "type": "result",
                "content": "Our model shows improved performance on longer sentences. On sentences with less than 20 words, the attention model achieves similar performance to basic encoder-decoder. On sentences with 40+ words, the attention model significantly outperforms the basic model."
            }
        ]
    },
    {
        "title": "Improving Neural Sequence Labeling Using Attention Mechanisms",
        "year": 2018,
        "doi": "10.48550/arXiv.1804.08242",
        "authors": ["Wei Liu", "Yao Chen", "Jian Zhang"],
        "abstract": "We present an approach to neural sequence labeling that incorporates attention mechanisms to capture long-range dependencies in input sequences.",
        "sections": [
            {
                "title": "Attention-based Tagging",
                "type": "method",
                "content": "We propose an attention-based tagging mechanism that allows the model to focus on relevant parts of the input sequence when predicting each output tag. The attention weights are computed based on the current hidden state and all encoder states."
            },
            {
                "title": "Label Dependencies",
                "type": "method",
                "content": "To capture label sequence dependencies, we incorporate a CRF layer on top of the attention-based encoder. The CRF layer considers the transition probabilities between consecutive labels, improving the overall tagging accuracy."
            },
            {
                "title": "Benchmark Results",
                "type": "result",
                "content": "Our model achieves state-of-the-art results on CoNLL-2003 NER task with F1 score of 91.2 and on Penn Treebank POS tagging with accuracy of 97.5."
            }
        ]
    },
    {
        "title": "Sequence to Sequence Learning with Neural Networks",
        "year": 2014,
        "doi": "10.48550/arXiv.1409.3215",
        "authors": ["Ilya Sutskever", "Oriol Vinyals", "Quoc V. Le"],
        "abstract": "We present a general end-to-end approach to sequence learning that uses a multilayer Long Short-Term Memory (LSTM) to map an input sequence to an output sequence.",
        "sections": [
            {
                "title": "LSTM Architecture",
                "type": "method",
                "content": "The LSTM architecture consists of an encoder LSTM that reads the input sequence and a decoder LSTM that outputs the target sequence. We reverse the order of the input sequence to introduce short-term dependencies."
            },
            {
                "title": "Training Procedure",
                "type": "method",
                "content": "We train the LSTM to maximize the probability of the target sequence given the input sequence. The LSTM is trained to handle variable-length input sequences by representing each sentence as a sequence of features."
            },
            {
                "title": "WMT Results",
                "type": "result",
                "content": "On WMT'14 English-to-French translation, the LSTM achieves a BLEU score of 34.8, which is close to the state-of-the-art at that time. The LSTM captures long-range dependencies effectively."
            }
        ]
    },
    {
        "title": "Cross-lingual Transfer Learning for Named Entity Recognition",
        "year": 2019,
        "doi": "10.48550/arXiv.1905.02092",
        "authors": ["Ming Chen", "Jian Zhang", "Wei Wang"],
        "abstract": "We propose a cross-lingual transfer learning approach for NER that leverages attention mechanisms to transfer knowledge from high-resource to low-resource languages.",
        "sections": [
            {
                "title": "Cross-lingual Attention",
                "type": "method",
                "content": "Our model uses cross-lingual attention to align representations across languages. The attention mechanism learns to map entities in different languages to a shared representation space."
            },
            {
                "title": "Transfer Strategy",
                "type": "method",
                "content": "We pre-train the model on labeled data from source languages and fine-tune on target languages. The attention-based alignment helps bridge the gap between languages with different entity naming conventions."
            },
            {
                "title": "Multi-language Results",
                "type": "result",
                "content": "Our approach achieves F1 scores of 76.3 on Spanish NER and 71.8 on Chinese NER when transferring from English. This demonstrates effective cross-lingual transfer for named entity recognition."
            }
        ]
    }
]

# Citation contexts and types
CITATION_CONTEXTS = [
    "supported by empirical results",
    "building upon",
    "extend the approach",
    "contrasted with",
    "alternative to"
]
CITATION_TYPES = ["support", "extend", "contrast", "alternative"]

# Sample insights to generate
SAMPLE_INSIGHTS = [
    "Transformer architectures excel at capturing long-range dependencies through self-attention mechanisms.",
    "Attention-based models significantly outperform traditional sequence-to-sequence approaches on longer sequences.",
    "Cross-lingual transfer learning with attention achieves competitive NER performance across diverse languages."
]


def clear_existing_data():
    """Remove existing demo data to make seeding idempotent."""
    print("Clearing existing demo data...")
    for label in ["INSIGHT", "CITATION", "SECTION", "PAPER", "AUTHOR"]:
        db.records.delete({"labels": [label], "where": {}})


def create_papers_with_sections():
    """Create papers, sections, and authors."""
    print("\n[1/5] Creating papers and sections...")
    
    all_sections = []
    all_papers = []
    
    for i, paper_data in enumerate(PAPERS_DATA):
        # Create author records
        author_records = []
        for author_name in paper_data["authors"]:
            author = db.records.create(
                label="AUTHOR",
                data={"name": author_name, "affiliation": "Research Institution"}
            )
            author_records.append(author)
        
        # Create paper
        paper = db.records.create(
            label="PAPER",
            data={
                "title": paper_data["title"],
                "year": paper_data["year"],
                "doi": paper_data["doi"],
                "abstract": paper_data["abstract"]
            }
        )
        all_papers.append(paper)
        
        # Attach authors
        for author in author_records:
            db.records.attach(source=paper, target=author, options={"type": "AUTHORED_BY"})
        
        # Create sections with embeddings
        sections_for_paper = []
        for j, section_data in enumerate(paper_data["sections"]):
            # Generate embedding for section content
            embedding = embedder.encode(section_data["content"]).tolist()
            
            section = db.records.create(
                label="SECTION",
                data={
                    "title": section_data["title"],
                    "content": section_data["content"],
                    "type": section_data["type"],
                    "paper_title": paper_data["title"]
                },
                vectors=[{"propertyName": "content", "vector": embedding}]
            )
            sections_for_paper.append(section)
            all_sections.append(section)
            
            # Link section to paper
            db.records.attach(source=paper, target=section, options={"type": "CONTAINS"})
        
        print(f"  Created: {paper_data['title']} ({len(sections_for_paper)} sections)")
    
    return all_papers, all_sections


def create_citations(all_sections):
    """Create citation relationships with provenance sub-nodes."""
    print("\n[2/5] Creating citation relationships...")
    
    # Define citation relationships between sections
    citation_definitions = [
        # (citing_section_idx, cited_section_idx, context, type)
        (0, 5, "building upon", "extend"),      # Transformer -> LSTM
        (1, 6, "extend the approach", "extend"),  # Attention mechanism -> Alignment model
        (3, 7, "supported by results", "support"), # Training results -> LSTM
        (5, 1, "contrasted with", "contrast"),   # LSTM -> Attention mechanism
        (7, 9, "building upon", "extend"),      # LSTM results -> Attention results
        (9, 2, "extend the approach", "extend"),  # Alignment -> Attention mechanism
        (10, 1, "alternative to", "alternative"), # CRF -> Standard attention
        (12, 9, "supported by empirical results", "support"), # Cross-lingual attention -> LSTM
    ]
    
    citation_count = 0
    for citing_idx, cited_idx, context, cit_type in citation_definitions:
        if citing_idx < len(all_sections) and cited_idx < len(all_sections):
            citing_section = all_sections[citing_idx]
            cited_section = all_sections[cited_idx]
            
            # Create provenance sub-node for the citation
            citation_node = db.records.create(
                label="CITATION",
                data={
                    "context": context,
                    "type": cit_type,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            # Link: citing section -> citation -> cited section
            db.records.attach(source=citing_section, target=citation_node, options={"type": "CITES"})
            db.records.attach(source=citation_node, target=cited_section, options={"type": "TARGETS"})
            
            citation_count += 1
    
    print(f"  Created {citation_count} citation relationships with provenance")
    return citation_count


def create_vector_index():
    """Create vector index on section content for similarity search."""
    print("\n[3/5] Creating vector index on sections...")
    
    try:
        # Check if index already exists
        existing = db.ai.indexes.find()
        for idx in existing.data:
            if idx.get("label") == "SECTION" and idx.get("propertyName") == "content":
                print("  Vector index already exists, skipping creation")
                return
    except Exception:
        pass
    
    try:
        index = db.ai.indexes.create({
            "label": "SECTION",
            "propertyName": "content",
            "sourceType": "external",
            "dimensions": 384,  # all-MiniLM-L6-v2 output dimension
            "similarityFunction": "cosine"
        })
        print("  Created vector index for SECTION.content")
    except Exception as e:
        print(f"  Note: Vector index creation may require existing records: {e}")


def create_insights_with_provenance(all_sections):
    """Create sample insights with full citation provenance."""
    print("\n[4/5] Creating insights with provenance...")
    
    # Find citations to use for insight provenance
    citations = db.records.find({
        "labels": ["CITATION"],
        "where": {},
        "limit": 5
    })
    
    insights = []
    for i, insight_text in enumerate(SAMPLE_INSIGHTS):
        # Create insight
        insight = db.records.create(
            label="INSIGHT",
            data={
                "text": insight_text,
                "generated_at": datetime.now().isoformat(),
                "model": "synthesis-v1"
            }
        )
        insights.append(insight)
        
        # Link to citation provenance if available
        if i < len(citations.data):
            citation = citations.data[i]
            db.records.attach(source=insight, target=citation, options={"type": "SOURCED_FROM"})
    
    print(f"  Created {len(insights)} insights with citation provenance")
    return insights


def verify_data():
    """Verify seeded data counts."""
    print("\n[5/5] Verifying data...")
    
    for label in ["PAPER", "SECTION", "CITATION", "INSIGHT", "AUTHOR"]:
        result = db.records.find({"labels": [label], "where": {}})
        print(f"  {label}: {result.total} records")


def main():
    print("=" * 60)
    print("FINE-GRAINED CITATION TRACKING - DATA SEEDING")
    print("=" * 60)
    
    # Clear existing data for fresh seeding
    clear_existing_data()
    
    # Create all data
    all_papers, all_sections = create_papers_with_sections()
    citation_count = create_citations(all_sections)
    create_vector_index()
    insights = create_insights_with_provenance(all_sections)
    verify_data()
    
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - {len(PAPERS_DATA)} papers")
    print(f"  - {sum(len(p['sections']) for p in PAPERS_DATA)} sections")
    print(f"  - {citation_count} citations with provenance")
    print(f"  - {len(SAMPLE_INSIGHTS)} insights")
    print(f"\nRun 'python main.py' to explore the data")


if __name__ == "__main__":
    main()
