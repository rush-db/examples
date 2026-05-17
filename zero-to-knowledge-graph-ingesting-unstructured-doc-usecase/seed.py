#!/usr/bin/env python3
"""
Seed script: Generates a realistic messy document corpus and ingests it into RushDB.

This creates documents across three types:
- Technical articles (simulating PDF content with mixed formatting)
- Meeting notes (unstructured text with action items)
- Data specifications (nested JSON-like structures)

The seed is idempotent: it checks for existing data before creating anything.
"""

import os
import sys
import time
import random
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)

# =============================================================================
# DOCUMENT CORPUS: Raw data that simulates messy real-world documents
# =============================================================================

SOURCES = [
    {
        "id": "source-001",
        "label": "SOURCE",
        "data": {
            "name": "research-papers-2024",
            "type": "research_archive",
            "description": "Archive of ML and distributed systems research papers"
        }
    },
    {
        "id": "source-002",
        "label": "SOURCE",
        "data": {
            "name": "team-meetings",
            "type": "meeting_notes",
            "description": "Engineering team meeting notes and decisions"
        }
    },
    {
        "id": "source-003",
        "label": "SOURCE",
        "data": {
            "name": "data-specs",
            "type": "technical_specs",
            "description": "Data models and API specifications"
        }
    }
]

# Technical articles (simulating PDF extracts with mixed formatting)
ARTICLES = [
    {
        "id": "article-001",
        "label": "DOCUMENT",
        "data": {
            "title": "Scaling Neural Networks for Production: Lessons from 100M Users",
            "type": "research_paper",
            "source": "research-papers-2024",
            "authors": ["Dr. Sarah Chen", "Prof. Michael Torres"],
            "year": 2024,
            "tags": ["machine-learning", "scaling", "production"],
            "chunks": [
                "This paper presents our experience scaling transformer-based models to handle 100 million daily active users. We describe the infrastructure challenges we faced, including GPU memory constraints, latency requirements, and cost optimization strategies that reduced our serving costs by 60%.",
                "Our architecture leverages a hierarchical caching strategy that pre-computes attention patterns for common queries. We found that 80% of user requests could be served from cache, dramatically reducing compute requirements during peak hours.",
                "We evaluate three model distillation approaches: task-specific, multi-task, and curriculum learning. Task-specific distillation proved most effective for our use case, achieving 94% of full-model accuracy with only 30% of the parameters."
            ]
        }
    },
    {
        "id": "article-002",
        "label": "DOCUMENT",
        "data": {
            "title": "Real-Time Fraud Detection Using Graph Neural Networks",
            "type": "research_paper",
            "source": "research-papers-2024",
            "authors": ["Dr. Emily Watson", "James Liu"],
            "year": 2024,
            "tags": ["fraud-detection", "graph-neural-networks", "real-time"],
            "chunks": [
                "We present a novel graph neural network architecture for real-time fraud detection in payment systems. Our approach models transaction relationships as a dynamic graph, capturing both sequential and structural patterns in fraudulent behavior.",
                "The key innovation is our temporal attention mechanism that weights recent transactions more heavily while still incorporating historical patterns. This allows us to detect novel fraud patterns within 50ms of a transaction occurring.",
                "Our system processes 50,000 transactions per second with a false positive rate below 0.1%. We achieve this through a combination of model quantization, batching strategies, and strategic caching of intermediate representations."
            ]
        }
    },
    {
        "id": "article-003",
        "label": "DOCUMENT",
        "data": {
            "title": "The Raft Consensus Algorithm: A More Understandable Approach",
            "type": "research_paper",
            "source": "research-papers-2024",
            "authors": ["Diego Ongaro", "John Ousterhout"],
            "year": 2014,
            "tags": ["distributed-systems", "consensus", "raft"],
            "chunks": [
                "Raft was designed as a more understandable alternative to Paxos. It decomposes consensus into three relatively independent subproblems: leader election, log replication, and safety. This separation makes it easier to reason about the algorithm and implement it correctly.",
                "The leader election mechanism uses a randomized timer approach to avoid split-brain scenarios. Each server candidates for leadership after a random timeout, and the first to collect majority votes wins. This simple mechanism is both correct and efficient.",
                "We conducted user studies comparing Raft with Paxos and found that participants were able to understand Raft significantly faster and implement correct solutions more often. This validated our hypothesis that understandability is crucial for practical consensus algorithms."
            ]
        }
    },
    {
        "id": "article-004",
        "label": "DOCUMENT",
        "data": {
            "title": "Attention Is All You Need: Transformers Explained",
            "type": "research_paper",
            "source": "research-papers-2024",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            "year": 2017,
            "tags": ["transformers", "attention", "nlp"],
            "chunks": [
                "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
                "Self-attention, sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. We show that self-attention can yield better results than recurrent layers on tasks requiring long-range dependencies.",
                "Our experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. The Transformer achieves 28.4 BLEU on WMT En-De, improving over existing best results."
            ]
        }
    }
]

# Meeting notes (unstructured text with mixed content)
MEETING_NOTES = [
    {
        "id": "note-001",
        "label": "DOCUMENT",
        "data": {
            "title": "ML Infrastructure Q1 Planning - 2024-01-15",
            "type": "meeting_notes",
            "source": "team-meetings",
            "date": "2024-01-15",
            "attendees": ["Dr. Sarah Chen", "James Liu", "Maria Garcia", "Alex Kim"],
            "chunks": [
                "Sarah presented the Q4 metrics showing 40% improvement in inference latency after implementing the caching layer. Action item: James to document the caching strategy for the engineering wiki.",
                "Discussion about GPU capacity for Q1. Current utilization is at 85% during peak hours. Maria proposed adding 20 more A100s to handle expected growth. Budget approved for Q2 if metrics support it.",
                "Alex raised concerns about model drift in production. Agreed to implement automated retraining pipeline by end of Q1. This will reduce manual intervention and ensure models stay current."
            ]
        }
    },
    {
        "id": "note-002",
        "label": "DOCUMENT",
        "data": {
            "title": "Distributed Systems Architecture Review - 2024-02-20",
            "type": "meeting_notes",
            "source": "team-meetings",
            "date": "2024-02-20",
            "attendees": ["Prof. Michael Torres", "Sarah Chen", "David Park"],
            "chunks": [
                "Michael led the architecture review for our new distributed training platform. Key decisions: adopting Raft for configuration consensus, using etcd for service discovery, and implementing custom load balancing.",
                "David demonstrated the prototype showing sub-100ms failover times with zero data loss. The team approved moving to production by March 15. Sarah will own the deployment runbook.",
                "Follow-up meeting scheduled for March 1 to review stress test results. Michael to prepare the capacity planning document with projected growth scenarios."
            ]
        }
    },
    {
        "id": "note-003",
        "label": "DOCUMENT",
        "data": {
            "title": "Fraud Detection Model Review - 2024-03-05",
            "type": "meeting_notes",
            "source": "team-meetings",
            "date": "2024-03-05",
            "attendees": ["Dr. Emily Watson", "James Liu", "Sarah Chen"],
            "chunks": [
                "Emily presented the GNN fraud detection results: 99.2% detection rate with 0.08% false positives. This exceeds our 98% target significantly. The model is ready for A/B testing in production.",
                "James raised a latency concern: current p99 is 45ms, but our SLA requires 50ms. Emily confirmed further optimization is possible through model pruning. She estimates we can get to 35ms p99.",
                "Decision: Deploy to 5% of traffic next week, expand to 50% if p99 stays under 45ms. Sarah will coordinate with the platform team for the canary deployment infrastructure."
            ]
        }
    },
    {
        "id": "note-004",
        "label": "DOCUMENT",
        "data": {
            "title": "NLP Team Sync - Transformer Roadmap - 2024-03-18",
            "type": "meeting_notes",
            "source": "team-meetings",
            "date": "2024-03-18",
            "attendees": ["Sarah Chen", "Dr. Emily Watson", "Lisa Wang", "Tom Chen"],
            "chunks": [
                "Lisa presented the transformer architecture evolution: from original 2017 paper to modern variants like BERT, GPT, and T5. Discussion about which architectures best fit our product needs.",
                "Decision: Invest in fine-tuning a 7B parameter model for our specific domain. This balances capability with serving cost. Tom will lead the fine-tuning experiments.",
                "Emily proposed exploring attention mechanism optimizations to reduce memory footprint. Action item: Emily to write a research brief on linear attention variants by end of March."
            ]
        }
    }
]

# Data specifications (nested JSON-like structures)
DATA_SPECS = [
    {
        "id": "spec-001",
        "label": "DOCUMENT",
        "data": {
            "title": "User Event Schema v2.1",
            "type": "data_spec",
            "source": "data-specs",
            "version": "2.1",
            "chunks": [
                "User events follow a nested structure with top-level fields: user_id, session_id, timestamp, event_type, and properties. The properties field is a flexible map supporting arbitrary key-value pairs for event-specific data.",
                "Example event: {user_id: 'u123', session_id: 's456', event_type: 'purchase', properties: {item_id: 'i789', amount: 99.99, currency: 'USD'}}. All timestamps are UTC ISO-8601 strings.",
                "Schema evolution strategy: We use schema versioning with backward compatibility. Breaking changes require a major version bump. Consumers should handle unknown fields gracefully."
            ]
        }
    },
    {
        "id": "spec-002",
        "label": "DOCUMENT",
        "data": {
            "title": "Transaction Graph Schema",
            "type": "data_spec",
            "source": "data-specs",
            "version": "1.0",
            "chunks": [
                "Transaction entities: Account (id, user_id, type, balance, created_at), Transaction (id, from_account, to_account, amount, currency, status, created_at), Merchant (id, name, category, risk_score).",
                "Relationships: Account HAS_TRANSACTION → Transaction, Merchant PROCESSED_TRANSACTION → Transaction, Account CONNECTED_TO → Account (for fraud graph). All relationships have temporal properties.",
                "Indexing strategy: We maintain vector embeddings of transaction patterns for similarity search, and graph indexes on key relationships for traversal queries. This hybrid approach supports both semantic and structural analysis."
            ]
        }
    },
    {
        "id": "spec-003",
        "label": "DOCUMENT",
        "data": {
            "title": "Model Serving API Specification",
            "type": "data_spec",
            "source": "data-specs",
            "version": "3.0",
            "chunks": [
                "REST API for model inference: POST /v1/predict with JSON body containing model_id, inputs (array of prompts), and options (temperature, max_tokens, streaming). Response includes predictions, latency_ms, and model_version.",
                "Batch inference: POST /v1/batch with same inputs as array. Optimized for throughput over latency. Response includes per-item predictions and aggregate statistics.",
                "Health and metrics: GET /health returns status and version. GET /metrics returns Prometheus-format metrics including request count, latency percentiles, and error rates by type."
            ]
        }
    },
    {
        "id": "spec-004",
        "label": "DOCUMENT",
        "data": {
            "title": "Configuration Store Schema",
            "type": "data_spec",
            "source": "data-specs",
            "version": "1.2",
            "chunks": [
                "Configuration entries have: key (namespaced dot notation), value (JSON), version (monotonic counter), created_at, updated_at, and metadata (owner, description, tags). Keys use hierarchical naming: service.feature.setting.",
                "Consensus protocol: All writes go through Raft leader. Followers proxy reads locally for low latency. Leader election uses randomized timeouts with 150-300ms range.",
                "Change tracking: Every modification creates a new version. History is immutable and queryable. We support atomic multi-key transactions for related configurations."
            ]
        }
    }
]

# Entity definitions (extracted from documents)
ENTITIES = [
    {
        "id": "entity-001",
        "label": "ENTITY",
        "data": {
            "name": "Dr. Sarah Chen",
            "type": "person",
            "role": "ML Infrastructure Lead",
            "affiliation": "Acme AI Labs"
        }
    },
    {
        "id": "entity-002",
        "label": "ENTITY",
        "data": {
            "name": "Prof. Michael Torres",
            "type": "person",
            "role": "Distributed Systems Researcher",
            "affiliation": "Stanford University"
        }
    },
    {
        "id": "entity-003",
        "label": "ENTITY",
        "data": {
            "name": "Dr. Emily Watson",
            "type": "person",
            "role": "Principal ML Researcher",
            "affiliation": "Acme AI Labs"
        }
    },
    {
        "id": "entity-004",
        "label": "ENTITY",
        "data": {
            "name": "Acme AI Labs",
            "type": "company",
            "sector": "Artificial Intelligence"
        }
    },
    {
        "id": "entity-005",
        "label": "ENTITY",
        "data": {
            "name": "Stanford University",
            "type": "company",
            "sector": "Education"
        }
    },
    {
        "id": "entity-006",
        "label": "ENTITY",
        "data": {
            "name": "Raft consensus algorithm",
            "type": "concept",
            "category": "distributed-systems"
        }
    },
    {
        "id": "entity-007",
        "label": "ENTITY",
        "data": {
            "name": "transformer architectures",
            "type": "concept",
            "category": "machine-learning"
        }
    },
    {
        "id": "entity-008",
        "label": "ENTITY",
        "data": {
            "name": "graph neural networks",
            "type": "concept",
            "category": "machine-learning"
        }
    },
    {
        "id": "entity-009",
        "label": "ENTITY",
        "data": {
            "name": "attention mechanisms",
            "type": "concept",
            "category": "deep-learning"
        }
    }
]

# =============================================================================
# INGESTION LOGIC
# =============================================================================

def check_existing_data():
    """Check if we've already seeded this workspace."""
    sources = db.records.find({"labels": ["SOURCE"],
                               "where": {"name": "research-papers-2024"}})
    return sources.total > 0


def ingest_sources():
    """Create SOURCE records."""
    created = []
    for source in SOURCES:
        existing = db.records.find({
            "labels": ["SOURCE"],
            "where": {"name": source["data"]["name"]}
        })
        if existing.total == 0:
            record = db.records.create(
                label=source["label"],
                data=source["data"]
            )
            created.append(record)
    return created


def ingest_documents():
    """Create DOCUMENT records from the corpus."""
    created = []
    
    for doc_data in ARTICLES + MEETING_NOTES + DATA_SPECS:
        source_name = doc_data["data"]["source"]
        
        # Find the source record
        source_result = db.records.find({
            "labels": ["SOURCE"],
            "where": {"name": source_name}
        })
        source_record = source_result.data[0] if source_result.total > 0 else None
        
        # Create document records (one per chunk for semantic search)
        chunks = doc_data["data"].pop("chunks")
        
        for i, chunk in enumerate(chunks):
            chunk_data = {
                **doc_data["data"],
                "content": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            record = db.records.create(
                label="DOCUMENT",
                data=chunk_data
            )
            created.append(record)
            
            # Attach to source
            if source_record:
                db.records.attach(
                    source=record,
                    target=source_record,
                    options={"type": "FROM_SOURCE", "direction": "out"}
                )
    
    return created


def ingest_entities():
    """Create ENTITY records."""
    created = []
    for entity in ENTITIES:
        existing = db.records.find({
            "labels": ["ENTITY"],
            "where": {"name": entity["data"]["name"]}
        })
        if existing.total == 0:
            record = db.records.create(
                label=entity["label"],
                data=entity["data"]
            )
            created.append(record)
    return created


def link_documents_to_entities(doc_records, entity_records):
    """Create MENTIONS relationships between documents and entities."""
    
    # Build entity lookup by name
    entity_by_name = {e.data["name"]: e for e in entity_records}
    
    # Map document content to entities mentioned
    entity_mentions = {
        "article-001": ["Dr. Sarah Chen", "Prof. Michael Torres", "transformer architectures"],
        "article-002": ["Dr. Emily Watson", "graph neural networks"],
        "article-003": ["Raft consensus algorithm"],
        "article-004": ["transformer architectures", "attention mechanisms"],
        "note-001": ["Dr. Sarah Chen", "Acme AI Labs"],
        "note-002": ["Prof. Michael Torres", "Raft consensus algorithm"],
        "note-003": ["Dr. Emily Watson"],
        "note-004": ["Dr. Emily Watson", "transformer architectures", "attention mechanisms"],
        "spec-001": [],
        "spec-002": ["graph neural networks"],
        "spec-003": [],
        "spec-004": ["Raft consensus algorithm"]
    }
    
    for doc in doc_records:
        doc_id_base = doc.data.get("id", "")
        # Extract base ID from chunk docs
        base_id = None
        for key in entity_mentions:
            if key in doc_id_base:
                base_id = key
                break
        
        if base_id and base_id in entity_mentions:
            for entity_name in entity_mentions[base_id]:
                if entity_name in entity_by_name:
                    db.records.attach(
                        source=doc,
                        target=entity_by_name[entity_name],
                        options={"type": "MENTIONS", "direction": "out"}
                    )


def link_authors_to_documents(doc_records, entity_records):
    """Create AUTHORED relationships between people and documents."""
    
    author_map = {
        "Dr. Sarah Chen": ["article-001"],
        "Prof. Michael Torres": ["article-001"],
        "Dr. Emily Watson": ["article-002"],
    }
    
    # Build entity lookup
    entity_by_name = {e.data["name"]: e for e in entity_records}
    
    for doc in doc_records:
        doc_id = doc.data.get("id", "")
        for author_name, article_ids in author_map.items():
            if any(aid in doc_id for aid in article_ids):
                if author_name in entity_by_name:
                    db.records.attach(
                        source=entity_by_name[author_name],
                        target=doc,
                        options={"type": "AUTHORED", "direction": "out"}
                    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=== SEED: Ingesting Document Corpus ===\n")
    
    # Check for existing data
    if check_existing_data():
        print("✓ Data already exists in workspace. Skipping seed.")
        print("  To reseed, delete the existing records first.")
        return
    
    # Ingest in order
    print("Phase 1: Creating sources...")
    sources = ingest_sources()
    print(f"  ✓ Created {len(sources)} SOURCE records")
    
    print("\nPhase 2: Creating documents...")
    docs = ingest_documents()
    print(f"  ✓ Created {len(docs)} DOCUMENT records")
    
    print("\nPhase 3: Creating entities...")
    entities = ingest_entities()
    print(f"  ✓ Created {len(entities)} ENTITY records")
    
    print("\nPhase 4: Creating relationships...")
    link_documents_to_entities(docs, entities)
    link_authors_to_documents(docs, entities)
    print("  ✓ Created MENTIONS and AUTHORED relationships")
    
    print("\n=== SEED COMPLETE ===")
    print(f"Total records created: {len(sources)} sources + {len(docs)} docs + {len(entities)} entities")


if __name__ == "__main__":
    main()
