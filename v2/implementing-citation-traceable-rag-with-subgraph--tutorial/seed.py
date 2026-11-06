"""
Seed script for citation-traceable RAG demo.

Creates a knowledge base of AI/ML topic documents, chunks them into semantic
segments, generates embeddings, and stores everything with full provenance
relationships in RushDB.

This script is idempotent - safe to run multiple times. It checks for existing
data before seeding and skips if the knowledge base is already populated.
"""

import os
import time
from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

load_dotenv()

# Initialize RushDB client
db = RushDB(os.getenv("RUSHDB_API_KEY"))

# Initialize embedding model (all-MiniLM-L6-v2 - fast, 384 dimensions)
print("Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
EMBEDDING_DIMENSIONS = 384

# Sample knowledge base about AI/ML topics
DOCUMENTS = [
    {
        "title": "Retrieval-Augmented Generation (RAG) Architecture",
        "category": "ai-engineering",
        "content": """Retrieval-Augmented Generation (RAG) is a paradigm that enhances large language model outputs by retrieving relevant context from external knowledge sources. The architecture consists of three main components: a retriever that identifies relevant documents, a ranker that orders candidates by relevance, and a generator that synthesizes retrieved information into coherent responses.

The retriever typically uses dense vector embeddings with approximate nearest neighbor search for efficient similarity computation. Modern implementations often employ bi-encoders for embedding generation and cross-encoders for reranking, combining speed with accuracy. The generator component is usually a transformer-based language model fine-tuned for question answering tasks.

Key design decisions include chunk size selection, overlap strategies, and hybrid search combining dense and sparse retrieval. Production RAG systems often incorporate caching layers, rate limiting, and fallback mechanisms for robustness. Evaluation metrics include retrieval precision, answer faithfulness, and response relevance."""
    },
    {
        "title": "Vector Search and Embedding Strategies",
        "category": "ai-engineering",
        "content": """Vector search is the backbone of semantic retrieval in modern AI systems. Embeddings transform discrete text into dense vectors in a high-dimensional space where semantic similarity correlates with geometric distance. The choice of embedding model significantly impacts retrieval quality.

Popular models include OpenAI's text-embedding-ada-002, Cohere's embed-multilingual-v3.0, and open-source alternatives like sentence-transformers. Model selection depends on latency requirements, memory constraints, and desired accuracy. Fine-tuning embeddings on domain-specific data can dramatically improve retrieval in specialized applications.

Approximate nearest neighbor (ANN) algorithms enable sub-linear search time on billion-scale corpora. Popular libraries include FAISS, Annoy, and HNSW. Index types trade off between build time, query speed, and recall. IVF (Inverted File Index) and HNSW (Hierarchical Navigable Small World) are commonly used in production systems. Metric selection (cosine vs dot product) affects which documents are considered similar."""
    },
    {
        "title": "Provenance Tracking in AI Systems",
        "category": "ml-ops",
        "content": """Provenance tracking captures the lineage and transformation history of data through AI pipelines. In RAG systems, provenance enables debugging, compliance verification, and user trust through transparent citation of sources. Effective provenance captures both data flow and processing decisions.

Core provenance concepts include origin tracking (where did data come from), transformation tracking (how was data processed), and attribution tracking (which processes contributed to outputs). The W3C PROV model provides a standardized vocabulary for provenance representation using entities, activities, and agents.

For RAG specifically, provenance must track document ingestion, chunk extraction, embedding generation, retrieval events, and generation outputs. Each step should record timing, input/output relationships, and configuration parameters. Graph databases naturally model provenance as nodes (entities) and edges (relationships), enabling efficient traversal queries.

Implementing comprehensive provenance requires careful schema design to balance granularity with query performance. Denormalization of frequently accessed provenance paths can reduce retrieval latency. However, raw provenance should remain accessible for forensic analysis and compliance audits."""
    },
    {
        "title": "LLM Hallucination Mitigation Techniques",
        "category": "ai-safety",
        "content": """LLM hallucination occurs when models generate plausible but incorrect or ungrounded information. This poses significant challenges for production AI systems requiring factual accuracy. Multiple mitigation techniques exist, each addressing different failure modes.

Retrieval-augmented generation reduces hallucination by grounding responses in retrieved facts rather than pure parametric knowledge. The quality of retrieved context directly impacts hallucination rates - irrelevant or conflicting information can actually increase hallucination. Cross-validation with multiple retrieval passes helps identify unreliable sources.

Chain-of-thought prompting encourages explicit reasoning steps, making logical inconsistencies more visible. Self-consistency techniques generate multiple reasoning paths and select the most coherent conclusion. Constitutional AI approaches use critique-revision cycles to align outputs with defined principles.

Fact-checking mechanisms compare generated claims against trusted knowledge bases. Slot filling and named entity resolution can verify specific facts. Uncertainty quantification helps identify when models are likely hallucinating, enabling appropriate fallback behavior. Hybrid systems combining symbolic reasoning with neural components show promise for robust factual grounding."""
    },
    {
        "title": "Chunking Strategies for Document Retrieval",
        "category": "ai-engineering",
        "content": """Document chunking significantly impacts retrieval effectiveness in RAG systems. The goal is to create coherent content segments that are neither too large (losing specificity) nor too small (lacking context). Multiple strategies exist, each suited to different document types and use cases.

Fixed-size chunking divides documents at token or character boundaries, offering simplicity but potentially breaking semantic units. Semantic chunking uses sentence boundaries and paragraph structure to preserve meaning coherence. Recursive chunking hierarchically splits content, trying larger units first and recursively breaking on failure.

Overlap strategies maintain context across chunk boundaries, trading recall for increased context. Typical overlap ranges from 10-30% of chunk size. Document structure (headers, lists, tables) provides natural chunk boundaries in structured documents. Metadata preservation (section titles, page numbers) aids source attribution.

Context enrichment through preceding/following chunk references or summary generation improves retrieval quality. Query-side techniques like query expansion and HyDE (hypothetical document embeddings) can improve chunk recall. The optimal strategy depends on document characteristics, query patterns, and latency requirements."""
    },
    {
        "title": "Graph Databases for Knowledge Management",
        "category": "data-engineering",
        "content": """Graph databases excel at modeling complex relationships and hierarchies, making them ideal for knowledge management and RAG systems. Their schema-flexible nature accommodates evolving data structures without costly migrations. Relationship-first design enables efficient traversal queries.

Property graphs store entities as nodes with arbitrary attributes and relationships as typed edges with properties. This model naturally represents provenance, taxonomies, and interconnected knowledge. Cypher, Gremlin, and SPARQL provide expressive query languages for pattern matching and path finding.

Neo4j, Amazon Neptune, and Azure Cosmos DB (Gremlin API) offer cloud-native graph database solutions. Key considerations include scalability, query latency, and ecosystem integrations. Graph algorithms (PageRank, community detection) enable knowledge discovery beyond direct traversal.

Hybrid approaches combine graph databases with vector stores for RAG applications. Graphs handle relationship queries and provenance tracking while vectors enable semantic similarity search. This combination provides both retrieval power and auditability. RushDB specifically provides this hybrid capability with native graph traversal and vector search."""
    },
    {
        "title": "Evaluation Frameworks for RAG Systems",
        "category": "ml-ops",
        "content": """RAG system evaluation requires measuring both retrieval and generation quality. Retrieval metrics include precision@k, recall@k, MRR, and NDCG, computed against annotated relevance judgments. Generation metrics assess answer quality, faithfulness, and relevance independently.

RAGAS (Retrieval-Augmented Generation Assessment) provides a comprehensive framework with metrics for answer correctness, faithfulness, and context relevance. It uses LLMs for automated evaluation, reducing human annotation costs. Context precision measures whether relevant items are ranked higher than irrelevant ones.

Benchmarks like TriviaQA, Natural Questions, and HotpotQA provide standardized test sets for open-domain QA. Custom benchmarks should reflect production query distributions and expected answer formats. A/B testing with real users provides ground-truth feedback on system utility.

Continuous evaluation pipelines track quality regression over time. Canary deployments with feature flags enable safe rollouts. Synthetic test data generation using LLMs can create diverse evaluation sets at scale. Human-in-the-loop evaluation remains essential for nuanced quality assessment, particularly for sensitive applications."""
    },
    {
        "title": "Prompt Engineering for RAG Applications",
        "category": "ai-engineering",
        "content": """Effective prompting transforms retrieved context into高质量 answers. System prompts establish role, format, and behavior guidelines. User prompts combine the question with formatted retrieved context. Few-shot examples demonstrate expected response patterns.

Context window management determines how many retrieved chunks to include and how to order them. Relevance thresholding filters low-quality candidates. Page-based ordering preserves document coherence when chunks span pages. Summarization of retrieved context reduces token usage while preserving key information.

Chain-of-thought prompting encourages step-by-step reasoning over retrieved facts. This improves answer accuracy and makes reasoning transparent for debugging. Self-consistency prompting generates multiple answers and selects the most coherent, reducing random hallucinations.

Prompt templates should be version-controlled and evaluated like code. A/B testing different prompt variants identifies optimal approaches. Token tracking prevents context overflow and ensures consistent performance. Structured output formats (JSON, markdown) enable reliable downstream processing of generated content."""
    },
    {
        "title": "Scaling RAG Systems for Production",
        "category": "ml-ops",
        "content": """Production RAG systems require careful architecture to handle scale, latency, and reliability requirements. Horizontal scaling through stateless query handlers enables elastic capacity. Caching strategies reduce redundant retrieval and generation costs.

Vector index scaling involves sharding across multiple indexes or using distributed ANN algorithms. Disk-based indices (IVF, HNSW with page-based storage) extend capacity beyond memory constraints. Incremental index updates avoid full rebuild overhead.

Retrieval optimization includes query caching, result reuse across similar queries, and pre-computed candidate sets. Tiered retrieval uses fast approximate methods first, followed by slower but accurate re-ranking. Query routing directs requests to specialized indexes based on topic or query characteristics.

Monitoring and observability track retrieval latency, cache hit rates, and answer quality metrics. Alerting on retrieval failures and generation errors enables rapid response. Cost tracking by user, query type, and time period informs optimization decisions. Autoscaling based on queue depth and latency targets maintains quality of service during traffic spikes."""
    },
    {
        "title": "Ethical Considerations in AI Citation",
        "category": "ai-safety",
        "content": """Proper citation in AI systems addresses ethical, legal, and trust considerations. Attribution to source authors respects intellectual property and enables verification. Transparent sourcing allows users to evaluate information credibility independently.

Legal compliance requires understanding copyright, fair use, and data licensing. CC-licensed content may require attribution. Commercial databases may restrict usage. Privacy regulations (GDPR, CCPA) affect what information can be used and how it must be handled.

User trust depends on visible source attribution. Uncited claims appear to come from parametric knowledge, potentially misleading users about reliability. Clear confidence indicators help users calibrate trust. Explanability features show which sources influenced which parts of an answer.

Bias in source selection can propagate through retrieval. Diverse source coverage reduces systematic bias. Source credibility scoring helps prioritize authoritative sources. Regular audit of retrieval patterns identifies potential issues. Documentation of data provenance enables accountability and supports compliance requirements."""
    }
]


def check_existing_data():
    """Check if knowledge base already exists to avoid duplicate seeding."""
    result = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    return result.total > 0


def create_vector_index():
    """Create or get the vector index for chunk embeddings."""
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        if idx['label'] == 'CHUNK' and idx['propertyName'] == 'embedding':
            print(f"  Vector index exists: {idx['__id']}")
            return idx['__id']
    
    print("  Creating vector index...")
    response = db.ai.indexes.create({
        "label": "CHUNK",
        "propertyName": "embedding",
        "sourceType": "external",
        "dimensions": EMBEDDING_DIMENSIONS,
        "similarityFunction": "cosine"
    })
    index_id = response.data['__id']
    print(f"  Vector index created: {index_id}")
    return index_id


def ingest_documents():
    """Ingest all documents with full provenance chain."""
    index_id = create_vector_index()
    total_chunks = 0
    
    print("\nIngesting documents...")
    for doc_idx, doc in enumerate(DOCUMENTS):
        print(f"  [{doc_idx + 1}/{len(DOCUMENTS)}] {doc['title']}")
        
        # Create document record
        document = db.records.create(
            label="DOCUMENT",
            data={
                "title": doc['title'],
                "category": doc['category'],
                "ingested_at": time.time()
            }
        )
        
        # Chunk the content (by sentences for semantic coherence)
        sentences = doc['content'].replace('\n', ' ').split('. ')
        chunks = []
        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if len(sent) > 20:  # Skip very short segments
                chunks.append({
                    "text": sent + '.',
                    "chunk_index": i,
                    "context_before": sentences[i-1].strip() + '.' if i > 0 else None,
                    "context_after": sentences[i+1].strip() + '.' if i < len(sentences)-1 else None
                })
        
        # Generate embeddings for all chunks
        chunk_texts = [c['text'] for c in chunks]
        embeddings = model.encode(chunk_texts, show_progress_bar=False)
        
        # Create chunks with embeddings in transaction
        with db.transactions.begin() as tx:
            for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                # Create chunk record with vector
                chunk = db.records.create(
                    label="CHUNK",
                    data={
                        "text": chunk_data['text'],
                        "chunk_index": chunk_data['chunk_index'],
                        "context_before": chunk_data['context_before'],
                        "context_after": chunk_data['context_after'],
                        "embedding_model": EMBEDDING_MODEL
                    },
                    vectors=[{"propertyName": "embedding", "vector": embedding.tolist()}],
                    transaction=tx
                )
                
                # Create embedding record (reference record for provenance)
                embedding_record = db.records.create(
                    label="EMBEDDING",
                    data={
                        "model": EMBEDDING_MODEL,
                        "dimensions": EMBEDDING_DIMENSIONS,
                        "generated_at": time.time()
                    },
                    transaction=tx
                )
                
                # Link document -> chunk -> embedding
                db.records.attach(source=document, target=chunk, options={"type": "CONTAINS"}, transaction=tx)
                db.records.attach(source=chunk, target=embedding_record, options={"type": "EMBEDDING_OF"}, transaction=tx)
                
                total_chunks += 1
                
                if total_chunks % 10 == 0:
                    print(f"    Created {total_chunks} chunks so far...")
        
        print(f"    -> {len(chunks)} chunks created")
    
    return total_chunks


def print_statistics(total_chunks):
    """Print current statistics about the knowledge base."""
    print("\n" + "="*60)
    print("KNOWLEDGE BASE STATISTICS")
    print("="*60)
    
    labels = ['DOCUMENT', 'CHUNK', 'EMBEDDING', 'RETRIEVAL_EVENT', 'GENERATION']
    for label in labels:
        result = db.records.find({"labels": [label], "limit": 1})
        print(f"  {label}: {result.total} records")
    
    # Get index stats
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        if idx['label'] == 'CHUNK':
            stats = db.ai.indexes.stats(idx['__id'])
            print(f"  Vector index: {stats.data.get('indexedRecords', 0)} / {stats.data.get('totalRecords', 0)} indexed")
    
    print("="*60)


if __name__ == "__main__":
    print("="*60)
    print("CITATION-TRACEABLE RAG - KNOWLEDGE BASE SEEDING")
    print("="*60)
    
    # Check for existing data
    if check_existing_data():
        print("\nKnowledge base already exists. Skipping seeding.")
        print("To re-seed, delete existing records first.")
        print("\nRunning cleanup check...")
        
        # Count existing
        result = db.records.find({"labels": ["CHUNK"], "limit": 1})
        print(f"  Found {result.total} chunks already in database.")
        
        # Still print stats
        total = result.total
        print_statistics(total)
    else:
        # Seed the knowledge base
        print(f"\nSeeding {len(DOCUMENTS)} documents...")
        start_time = time.time()
        total_chunks = ingest_documents()
        elapsed = time.time() - start_time
        
        print(f"\nSeeding complete!")
        print(f"  Documents: {len(DOCUMENTS)}")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Time: {elapsed:.1f}s")
        
        print_statistics(total_chunks)
    
    print("\nReady to run: python main.py")
