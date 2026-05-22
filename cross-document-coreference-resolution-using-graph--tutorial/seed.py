#!/usr/bin/env python3
"""
Seed script for Cross-Document Coreference Resolution Example.

Generates sample documents with entity mentions and loads them into RushDB.
Uses deterministic generation for reproducibility.
"""

import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# ============================================================================
# Sample Data Generation
# ============================================================================

# Canonical entities we'll reference across documents
ENTITIES = {
    "john_smith": {
        "canonicalName": "John Smith",
        "type": "person",
        "description": "CEO of TechCorp Industries"
    },
    "sarah_chen": {
        "canonicalName": "Sarah Chen",
        "type": "person",
        "description": "Chief Technology Officer at TechCorp Industries"
    },
    "techcorp": {
        "canonicalName": "TechCorp Industries",
        "type": "organization",
        "description": "A leading technology company"
    },
    "ai_summit": {
        "canonicalName": "Global AI Summit",
        "type": "event",
        "description": "Annual artificial intelligence conference"
    }
}

# Document templates with mentions
DOCUMENTS = [
    {
        "title": "TechCorp Q4 Report: Strong Growth Driven by AI Division",
        "source": "TechCorp Investor Relations",
        "content": """TechCorp Industries reported strong fourth-quarter results, with revenue up 23% year-over-year. 
The CEO, John Smith, attributed the growth to strategic investments in artificial intelligence. 
In a statement, the CEO highlighted the company's commitment to responsible AI development.
Sarah Chen, Chief Technology Officer, emphasized that new AI products will launch in Q1.
The company's stock price rose 5% following the announcement. Analysts noted that 
the executive team has positioned TechCorp well for the coming year."""
    },
    {
        "title": "TechCorp CEO Speaks at Global AI Summit",
        "source": "TechCrunch",
        "content": """John Smith, the chief executive of TechCorp Industries, delivered the keynote at the 
Global AI Summit in San Francisco today. The CEO outlined his vision for ethical AI development.
Referring to TechCorp's latest quarterly results, Mr. Smith stated that innovation remains the company's priority.
Sarah Chen accompanied Smith at the event and presented technical insights on machine learning applications.
The summit brought together over 500 technology leaders. Industry observers praised the executive's foresight."""
    },
    {
        "title": "Industry Weekly: TechCorp's Leadership Under Scrutiny",
        "source": "Industry Weekly",
        "content": """As TechCorp Industries navigates increasing competition, observers are watching the executive team's decisions closely.
Mr. Smith has led the company through significant transformation since taking the helm.
Sources close to the company indicate that the CEO is considering strategic acquisitions.
Meanwhile, Chen continues to drive technological innovation at the Silicon Valley firm.
The technology company's board has expressed confidence in its current direction."""
    },
    {
        "title": "TechCorp Announces New AI Research Initiative",
        "source": "MIT Technology Review",
        "content": """TechCorp Industries unveiled a $500 million AI research initiative today. 
The announcement came from Sarah Chen during a press conference at company headquarters.
The CTO described the initiative as a "decade-long commitment" to advancing AI capabilities.
John Smith, who joined Chen for the announcement, called it "a defining moment" for the company.
TechCorp will partner with universities worldwide. This investment signals the executive team's ambition."""
    },
    {
        "title": "Market Analysis: TechCorp Stock Performance Review",
        "source": "Financial Times",
        "content": """TechCorp Industries shares have outperformed the sector average this quarter.
Market analysts attribute this to strong leadership from the executive team.
Smith and Chen have implemented effective strategies, according to investment research firm Goldman Sachs.
The CEO's recent public appearances have boosted investor confidence.
TechCorp continues to attract top talent. The company's headquarters remains a hub for innovation."""
    }
]

# Mentions extracted from documents with their entity mappings
# Format: (mention_text, entity_key, mention_type, document_index)
MENTION_EXTRACTIONS = [
    # Doc 0: TechCorp Q4 Report
    ("John Smith", "john_smith", "name", 0),
    ("the CEO", "john_smith", "description", 0),
    ("John Smith", "john_smith", "name", 0),
    ("the CEO", "john_smith", "description", 0),
    ("Sarah Chen", "sarah_chen", "name", 0),
    ("Chief Technology Officer", "sarah_chen", "description", 0),
    ("TechCorp", "techcorp", "name", 0),
    ("the company", "techcorp", "description", 0),
    ("the executive team", "techcorp", "description", 0),

    # Doc 1: TechCorp CEO at AI Summit
    ("John Smith", "john_smith", "name", 1),
    ("the chief executive", "john_smith", "description", 1),
    ("TechCorp Industries", "techcorp", "name", 1),
    ("the CEO", "john_smith", "description", 1),
    ("Mr. Smith", "john_smith", "name", 1),
    ("Sarah Chen", "sarah_chen", "name", 1),
    ("Smith", "john_smith", "name", 1),
    ("Global AI Summit", "ai_summit", "name", 1),

    # Doc 2: Industry Weekly
    ("Mr. Smith", "john_smith", "name", 2),
    ("the CEO", "john_smith", "description", 2),
    ("Chen", "sarah_chen", "name", 2),
    ("the company", "techcorp", "description", 2),
    ("TechCorp Industries", "techcorp", "name", 2),
    ("the technology company", "techcorp", "description", 2),
    ("the executive team", "techcorp", "description", 2),

    # Doc 3: New AI Research Initiative
    ("TechCorp Industries", "techcorp", "name", 3),
    ("Sarah Chen", "sarah_chen", "name", 3),
    ("the company", "techcorp", "description", 3),
    ("the CTO", "sarah_chen", "description", 3),
    ("a defining moment", "techcorp", "description", 3),
    ("John Smith", "john_smith", "name", 3),
    ("the executive team", "techcorp", "description", 3),

    # Doc 4: Market Analysis
    ("TechCorp Industries", "techcorp", "name", 4),
    ("the executive team", "techcorp", "description", 4),
    ("Smith", "john_smith", "name", 4),
    ("Chen", "sarah_chen", "name", 4),
    ("the CEO", "john_smith", "description", 4),
    ("TechCorp", "techcorp", "name", 4),
    ("the company", "techcorp", "description", 4),
    ("the company's headquarters", "techcorp", "description", 4),
]


def generate_sample_data():
    """Generate sample data deterministically."""
    random.seed(42)
    
    base_date = datetime(2024, 1, 15)
    
    for i, doc_template in enumerate(DOCUMENTS):
        doc_template["date"] = (base_date + timedelta(days=i * 3)).isoformat()
        doc_template["id"] = f"doc_{i:03d}"
    
    return {
        "entities": ENTITIES,
        "documents": DOCUMENTS,
        "mentions": MENTION_EXTRACTIONS
    }


def seed_database():
    """Load sample data into RushDB."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError("RUSHDB_API_KEY environment variable is required")
    
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    
    # Check if data already exists
    existing_docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if existing_docs:
        print("Data already exists in database. Skipping seed.")
        print("Run 'main.py' to demonstrate coreference resolution.")
        return False
    
    print("Generating sample data...")
    data = generate_sample_data()
    
    print("Creating entities...")
    entity_map = {}
    for key, entity_data in data["entities"].items():
        entity = db.records.create(
            label="ENTITY",
            data={
                "entityKey": key,
                "canonicalName": entity_data["canonicalName"],
                "entityType": entity_data["type"],
                "description": entity_data["description"]
            }
        )
        entity_map[key] = entity
        print(f"  Created entity: {entity_data['canonicalName']}")
    
    print("Creating documents and mentions...")
    for doc_data in data["documents"]:
        doc_id = doc_data["id"]
        
        # Create document
        document = db.records.create(
            label="DOCUMENT",
            data={
                "docId": doc_id,
                "title": doc_data["title"],
                "source": doc_data["source"],
                "date": doc_data["date"],
                "content": doc_data["content"]
            }
        )
        print(f"  Created document: {doc_data['title'][:50]}...")
        
        # Create mentions for this document
        doc_index = int(doc_id.split("_")[1])
        doc_mentions = [
            m for m in data["mentions"] 
            if m[3] == doc_index
        ]
        
        prev_mention = None
        for mention_text, entity_key, mention_type, _ in doc_mentions:
            entity = entity_map[entity_key]
            
            # Create mention
            mention = db.records.create(
                label="MENTION",
                data={
                    "text": mention_text,
                    "mentionType": mention_type,
                    "entityKey": entity_key,
                    "documentId": doc_id
                }
            )
            
            # Link document -> mention
            db.records.attach(
                source=document,
                target=mention,
                options={"type": "MENTIONS_IN", "direction": "out"}
            )
            
            # Link mention -> entity
            db.records.attach(
                source=mention,
                target=entity,
                options={"type": "REFERS_TO", "direction": "out"}
            )
            
            # Link consecutive mentions in same document (coreference chain within doc)
            if prev_mention is not None:
                prev_entity = prev_mention.data.get("entityKey")
                curr_entity = entity_key
                
                # Only link if same entity
                if prev_entity == curr_entity:
                    db.records.attach(
                        source=prev_mention,
                        target=mention,
                        options={"type": "SAME_AS", "direction": "out"}
                    )
            
            prev_mention = mention
    
    # Create cross-document coreference links
    print("Creating cross-document coreference links...")
    for entity_key in ["john_smith", "sarah_chen", "techcorp"]:
        mentions = db.records.find({
            "labels": ["MENTION"],
            "where": {"entityKey": entity_key},
            "limit": 100
        })
        
        # Get first mention from different documents
        by_doc = {}
        for m in mentions.data:
            doc_id = m.data.get("documentId")
            if doc_id and doc_id not in by_doc:
                by_doc[doc_id] = m
        
        # Link first mentions across documents
        doc_ids = list(by_doc.keys())
        for i in range(len(doc_ids) - 1):
            first = by_doc[doc_ids[i]]
            second = by_doc[doc_ids[i + 1]]
            db.records.attach(
                source=first,
                target=second,
                options={"type": "SAME_AS", "direction": "out"}
            )
    
    print(f"\nSeed complete! Created:")
    print(f"  - {len(ENTITIES)} entities")
    print(f"  - {len(DOCUMENTS)} documents")
    print(f"  - {len(MENTION_EXTRACTIONS)} mentions")
    
    # Save sample data for reference
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "sample_articles.json", "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Cross-Document Coreference Resolution - Data Seeder")
    print("=" * 60)
    
    try:
        seeded = seed_database()
        if seeded:
            print("\nTo run the main example, execute: python main.py")
    except Exception as e:
        print(f"\nError: {e}")
        raise
