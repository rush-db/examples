"""
Database Seeder for Citation Verification Chain

Creates sample source documents and claims to demonstrate the verification chain.
This script is idempotent - safe to run multiple times.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Verify environment setup
api_key = os.environ.get("RUSHDB_API_KEY")
if not api_key:
    print("❌ Error: RUSHDB_API_KEY not found in environment")
    print("   Copy .env.example to .env and add your API key")
    sys.exit(1)

# Initialize clients
db = RushDB(api_key)
embedder = SentenceTransformer('all-MiniLM-L6-v2')


def get_embedding(text: str) -> list[float]:
    """Generate embedding for text using sentence-transformers."""
    return embedder.encode(text, normalize_embeddings=True).tolist()


def seed_sources() -> list:
    """Create source document records in RushDB."""
    print("\n📚 Seeding source documents...")
    
    sources_data = [
        {
            "title": "Artificial Intelligence Market Report 2024",
            "authors": ["Market Research Institute"],
            "publication_year": 2024,
            "abstract": "This comprehensive report analyzes global AI spending trends and projects market growth through 2028.",
            "content": """
Global AI spending is projected to reach $500 billion by 2027, driven by enterprise adoption and government initiatives.
The compound annual growth rate (CAGR) for AI infrastructure spending is expected to be 24% over the next five years.
Major growth areas include generative AI, computer vision, and natural language processing applications.
Enterprise spending on AI has increased by 65% year-over-year, with cloud-based AI services leading adoption.
            """
        },
        {
            "title": "Attention Is All You Need",
            "authors": ["Vaswani, A.", "Shazeer, N.", "Parmar, N."],
            "publication_year": 2017,
            "abstract": "The dominant sequence transduction models are based on complex RNNs or CNNs. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
            "content": """
The Transformer architecture was introduced in 2017 by researchers at Google Brain.
This paper introduced the self-attention mechanism that has become fundamental to modern large language models.
The architecture replaced recurrence with parallel attention, enabling faster training on GPUs.
Key innovations include multi-head attention, positional encoding, and encoder-decoder structure.
            """
        },
        {
            "title": "Enterprise Technology Forecast 2024",
            "authors": ["Gartner Research"],
            "publication_year": 2024,
            "abstract": "Annual forecast of enterprise technology spending across major categories.",
            "content": """
Enterprise technology spending is expected to exceed $4.5 trillion globally in 2024.
AI and machine learning investments represent the fastest-growing segment at 28% YoY growth.
Cloud infrastructure spending continues to dominate IT budgets, comprising 35% of total tech spend.
Digital transformation initiatives are driving 40% of new technology investments.
            """
        },
        {
            "title": "Stack Overflow Developer Survey 2024",
            "authors": ["Stack Overflow"],
            "publication_year": 2024,
            "abstract": "Annual survey of developer demographics, tools, and trends.",
            "content": """
Python remains the most popular programming language among developers for the second consecutive year.
JavaScript continues to be the most widely used language for web development.
Rust has been voted the most admired language for eight years running.
Developer satisfaction with Python is at 87%, reflecting its ease of use and ecosystem.
            """
        },
        {
            "title": "Climate Change Impact on Agriculture 2024",
            "authors": ["FAO", "World Bank"],
            "publication_year": 2024,
            "abstract": "Analysis of climate change effects on global food production systems.",
            "content": """
Climate change is affecting agricultural yields globally, with developing regions experiencing the most severe impacts.
Average crop yields have decreased by 2.5% per decade due to changing precipitation patterns.
Adoption of climate-resilient crop varieties has increased by 15% in the past five years.
Precision agriculture technologies are being deployed on 25% of arable land globally.
            """
        }
    ]
    
    created_sources = []
    
    for i, source in enumerate(sources_data, 1):
        # Check if source already exists
        existing = db.records.find({
            "labels": ["SOURCE"],
            "where": {"title": source["title"]}
        })
        
        if existing.data:
            print(f"  ✓ Source '{source['title']}' already exists, skipping")
            created_sources.append(existing.data[0])
            continue
        
        # Create source record with embedding
        content = source["content"].strip()
        vector = get_embedding(content)
        
        record = db.records.create(
            label="SOURCE",
            data={
                "title": source["title"],
                "authors": source["authors"],
                "publication_year": source["publication_year"],
                "abstract": source["abstract"],
                "body": content
            },
            vectors=[{"propertyName": "body", "vector": vector}]
        )
        
        created_sources.append(record)
        print(f"  ✓ Created source: {source['title']}")
    
    return created_sources


def seed_claims(sources: list) -> list:
    """Create claim records and link to potential sources."""
    print("\n📝 Seeding LLM-generated claims...")
    
    claims_data = [
        {
            "text": "Global AI spending will reach $500B by 2027",
            "verification_status": "PENDING",
            "generated_by": "GPT-4",
            "generated_at": "2024-01-15T10:30:00Z",
            "context": "While discussing market trends in enterprise AI adoption"
        },
        {
            "text": "Transformer architecture was introduced in 2017",
            "verification_status": "PENDING",
            "generated_by": "Claude-3",
            "generated_at": "2024-01-16T14:20:00Z",
            "context": "When explaining the history of neural network architectures"
        },
        {
            "text": "Python is the most popular programming language",
            "verification_status": "PENDING",
            "generated_by": "GPT-4",
            "generated_at": "2024-01-17T09:15:00Z",
            "context": "While recommending a first programming language for beginners"
        }
    ]
    
    created_claims = []
    
    for i, claim in enumerate(claims_data, 1):
        # Check if claim already exists
        existing = db.records.find({
            "labels": ["CLAIM"],
            "where": {"text": claim["text"]}
        })
        
        if existing.data:
            print(f"  ✓ Claim already exists, skipping")
            created_claims.append(existing.data[0])
            continue
        
        # Create claim record with embedding
        vector = get_embedding(claim["text"])
        
        record = db.records.create(
            label="CLAIM",
            data={
                "text": claim["text"],
                "verification_status": claim["verification_status"],
                "generated_by": claim["generated_by"],
                "generated_at": claim["generated_at"],
                "context": claim["context"]
            },
            vectors=[{"propertyName": "text", "vector": vector}]
        )
        
        created_claims.append(record)
        print(f"  ✓ Created claim: {claim['text'][:50]}...")
    
    return created_claims


def link_claims_to_sources(claims: list, sources: list):
    """Create CITES relationships between claims and sources."""
    print("\n🔗 Creating citation relationships...")
    
    # Predefined mappings based on semantic similarity
    citation_mappings = {
        # Claim about AI spending
        0: [0, 2],  # "Global AI spending will reach $500B by 2027" -> AI Market Report, Enterprise Tech Forecast
        # Claim about Transformers
        1: [1],     # "Transformer architecture was introduced in 2017" -> Attention Is All You Need
        # Claim about Python
        2: [3],     # "Python is the most popular programming language" -> Stack Overflow Survey
    }
    
    for claim_idx, source_indices in citation_mappings.items():
        claim = claims[claim_idx]
        
        for source_idx in source_indices:
            source = sources[source_idx]
            
            # Check if relationship already exists
            existing = db.records.find({
                "labels": ["SOURCE"],
                "where": {
                    "CLAIM": {"$id": claim.id}
                }
            })
            
            if existing.data and any(s.id == source.id for s in existing.data):
                print(f"  ✓ Citation link already exists")
                continue
            
            # Create CITES relationship
            db.records.attach(
                source=claim,
                target=source,
                options={"type": "CITES", "direction": "out"}
            )
            print(f"  ✓ Linked claim to: {source.data.get('title', 'Unknown')}")


def create_vector_index():
    """Create a vector index for claims for semantic search."""
    print("\n🔍 Setting up vector index for claims...")
    
    # Check for existing index
    existing_indexes = db.ai.indexes.find()
    for idx in existing_indexes.data:
        if idx.get('label') == 'CLAIM' and idx.get('propertyName') == 'text':
            print(f"  ✓ Vector index already exists")
            return
    
    # Create new index
    index = db.ai.indexes.create({
        "label": "CLAIM",
        "propertyName": "text",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine"
    })
    
    print(f"  ✓ Created vector index: {index.data.get('__id')}")


def main():
    print("=" * 50)
    print("📦 Citation Verification Chain - Database Seeder")
    print("=" * 50)
    
    # Seed data
    sources = seed_sources()
    claims = seed_claims(sources)
    link_claims_to_sources(claims, sources)
    create_vector_index()
    
    print("\n" + "=" * 50)
    print("✅ Database seeding complete!")
    print("=" * 50)
    print(f"\n📊 Summary:")
    print(f"   • Sources created: {len(sources)}")
    print(f"   • Claims created: {len(claims)}")
    print("\nRun 'python main.py' to execute the verification chain.")


if __name__ == "__main__":
    main()
