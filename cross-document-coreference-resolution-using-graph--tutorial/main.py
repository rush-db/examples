#!/usr/bin/env python3
"""
Cross-Document Coreference Resolution using Graph-Structured Context.

This example demonstrates how to use RushDB's property graph model to:
1. Model documents, mentions, and entities as interconnected nodes
2. Store coreference relationships as directed edges
3. Traverse the graph to resolve entity identity across documents
4. Query coreference chains and entity clusters
"""

import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()


@dataclass
class ResolvedEntity:
    """A canonical entity with all its related mentions."""
    id: str
    entity_key: str
    canonical_name: str
    entity_type: str
    description: str
    mentions: list
    documents: set


def init_rushdb() -> RushDB:
    """Initialize RushDB connection."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError("RUSHDB_API_KEY environment variable is required")
    
    url = os.getenv("RUSHDB_URL")
    return RushDB(api_key, url=url) if url else RushDB(api_key)


def demo_basic_graph_structure(db: RushDB):
    """Show the basic graph structure: documents and mentions."""
    print("\n" + "=" * 60)
    print("1. Basic Graph Structure")
    print("=" * 60)
    
    # Get all documents
    documents = db.records.find({"labels": ["DOCUMENT"], "limit": 10})
    print(f"\nDocuments in graph: {len(documents.data)}")
    
    for doc in documents.data:
        print(f"  - {doc['title']}")
    
    # Count mentions
    all_mentions = db.records.find({"labels": ["MENTION"], "limit": 1000})
    print(f"\nTotal mentions: {len(all_mentions.data)}")
    
    # Show mention distribution by type
    mention_types = defaultdict(int)
    for m in all_mentions.data:
        mention_types[m.data.get("mentionType", "unknown")] += 1
    
    print("Mention type distribution:")
    for mtype, count in sorted(mention_types.items()):
        print(f"  - {mtype}: {count}")


def demo_entity_resolution(db: RushDB):
    """Demonstrate entity resolution through graph traversal."""
    print("\n" + "=" * 60)
    print("2. Entity Resolution via Graph Traversal")
    print("=" * 60)
    
    # Get all entities
    entities = db.records.find({"labels": ["ENTITY"], "limit": 100})
    
    resolved_entities = []
    
    for entity in entities.data:
        entity_key = entity.data.get("entityKey", "")
        
        # Find all mentions that refer to this entity
        # Using the relationship query pattern
        mentions = db.records.find({
            "labels": ["MENTION"],
            "where": {
                "entityKey": entity_key
            },
            "limit": 100
        })
        
        # Get documents for these mentions
        documents = set()
        for m in mentions.data:
            doc_id = m.data.get("documentId")
            if doc_id:
                documents.add(doc_id)
        
        resolved = ResolvedEntity(
            id=entity.id,
            entity_key=entity_key,
            canonical_name=entity.data.get("canonicalName", ""),
            entity_type=entity.data.get("entityType", ""),
            description=entity.data.get("description", ""),
            mentions=[m.data for m in mentions.data],
            documents=documents
        )
        resolved_entities.append(resolved)
    
    print(f"\nResolved {len(resolved_entities)} entities:")
    print("-" * 50)
    
    for entity in resolved_entities:
        print(f"\n  {entity.canonical_name} ({entity.entity_type})")
        print(f"    ID: {entity.id[:20]}...")
        print(f"    Mentions: {len(entity.mentions)}")
        print(f"    Documents: {len(entity.documents)}")
        print(f"    Canonical mentions:")
        
        # Show a few example mentions
        for m in entity.mentions[:3]:
            mention_text = m.get("text", "")
            mention_type = m.get("mentionType", "")
            print(f"      - \"{mention_text}\" ({mention_type})")
        
        if len(entity.mentions) > 3:
            print(f"      ... and {len(entity.mentions) - 3} more")
    
    return resolved_entities


def demo_coreference_chains(db: RushDB):
    """Demonstrate coreference chain traversal."""
    print("\n" + "=" * 60)
    print("3. Coreference Chain Traversal")
    print("=" * 60)
    
    # Find a mention that is part of a coreference chain
    # Start with a pronoun or description mention
    coref_mentions = db.records.find({
        "labels": ["MENTION"],
        "where": {
            "mentionType": "description"
        },
        "limit": 5
    })
    
    print("\nCoreference chains starting from description mentions:")
    print("-" * 50)
    
    for mention in coref_mentions.data[:3]:
        mention_text = mention.data.get("text", "")
        entity_key = mention.data.get("entityKey", "")
        doc_id = mention.data.get("documentId", "")
        
        # Get the entity this mentions refers to
        entity = db.records.find({
            "labels": ["ENTITY"],
            "where": {
                "entityKey": entity_key
            },
            "limit": 1
        })
        
        # Find all mentions for this entity
        same_entity_mentions = db.records.find({
            "labels": ["MENTION"],
            "where": {
                "entityKey": entity_key
            },
            "limit": 100
        })
        
        if entity.data:
            canonical = entity.data[0].data.get("canonicalName", "Unknown")
            print(f"\n  \"{mention_text}\" refers to: {canonical}")
            print(f"    Chain size: {len(same_entity_mentions.data)} mentions")
            
            # Show the chain
            chain = [m.data.get("text", "") for m in same_entity_mentions.data[:5]]
            print(f"    Chain sample: {' -> '.join(chain)}")


def demo_cross_document_resolution(db: RushDB):
    """Show how entities are resolved across multiple documents."""
    print("\n" + "=" * 60)
    print("4. Cross-Document Entity Resolution")
    print("=" * 60)
    
    # Get all entities
    entities = db.records.find({"labels": ["ENTITY"], "limit": 100})
    
    print("\nEntities mentioned across multiple documents:")
    print("-" * 50)
    
    cross_doc_entities = []
    
    for entity in entities.data:
        entity_key = entity.data.get("entityKey", "")
        
        # Find all mentions
        mentions = db.records.find({
            "labels": ["MENTION"],
            "where": {"entityKey": entity_key},
            "limit": 100
        })
        
        # Group by document
        docs_with_mentions = defaultdict(list)
        for m in mentions.data:
            doc_id = m.data.get("documentId", "")
            docs_with_mentions[doc_id].append(m.data.get("text", ""))
        
        if len(docs_with_mentions) > 1:
            canonical_name = entity.data.get("canonicalName", "Unknown")
            cross_doc_entities.append({
                "entity": entity,
                "canonical_name": canonical_name,
                "docs_with_mentions": dict(docs_with_mentions),
                "doc_count": len(docs_with_mentions),
                "total_mentions": len(mentions.data)
            })
    
    # Sort by document count (most cross-document first)
    cross_doc_entities.sort(key=lambda x: x["doc_count"], reverse=True)
    
    for item in cross_doc_entities:
        print(f"\n  {item['canonical_name']}")
        print(f"    Found in {item['doc_count']} documents with {item['total_mentions']} total mentions")
        print(f"    Mentions by document:")
        
        for doc_id, mentions in list(item["docs_with_mentions"].items())[:3]:
            # Get document title
            doc = db.records.find_by_id(doc_id)
            title = doc.data.get("title", "Unknown")[:40] if doc else "Unknown"
            print(f"      [{title}...]:")
            for m in mentions[:2]:
                print(f"        - \"{m}\"")


def demo_graph_relationships(db: RushDB):
    """Query the graph relationships directly."""
    print("\n" + "=" * 60)
    print("5. Graph Relationship Analysis")
    print("=" * 60)
    
    # Count relationship types
    documents = db.records.find({"labels": ["DOCUMENT"], "limit": 100})
    
    total_mentions_in = 0
    total_refers_to = 0
    total_same_as = 0
    
    for doc in documents.data:
        # Count MENTIONS_IN relationships (document -> mention)
        mentions = db.records.find({
            "labels": ["MENTION"],
            "where": {
                "DOCUMENT": {
                    "$relation": {"type": "MENTIONS_IN", "direction": "in"}
                },
                "documentId": doc.data.get("docId")
            },
            "limit": 100
        })
        total_mentions_in += len(mentions.data)
    
    # Count REFERS_TO relationships
    refers_to = db.records.find({
        "labels": ["MENTION"],
        "where": {
            "ENTITY": {
                "$relation": {"type": "REFERS_TO", "direction": "out"}
            }
        },
        "limit": 1000
    })
    total_refers_to = len Refers_to.data)
    
    # Count SAME_AS relationships (approximate via mentions with same entity)
    same_as = db.records.find({
        "labels": ["MENTION"],
        "where": {
            "MENTION": {
                "$relation": {"type": "SAME_AS", "direction": "out"}
            }
        },
        "limit": 1000
    })
    total_same_as = len(same_as.data)
    
    print("\nRelationship counts:")
    print(f"  - MENTIONS_IN (document -> mention): {total_mentions_in}")
    print(f"  - REFERS_TO (mention -> entity): {total_refers_to}")
    print(f"  - SAME_AS (mention -> mention): {total_same_as}")
    
    print("\nGraph structure summary:")
    print(f"  Documents: {len(documents.data)}")
    
    mentions = db.records.find({"labels": ["MENTION"], "limit": 1000})
    entities = db.records.find({"labels": ["ENTITY"], "limit": 100})
    
    print(f"  Mentions: {len(mentions.data)}")
    print(f"  Entities: {len(entities.data)}")
    print(f"  Total edges: {total_mentions_in + total_refers_to + total_same_as}")


def demo_advanced_queries(db: RushDB):
    """Show advanced graph traversal patterns."""
    print("\n" + "=" * 60)
    print("6. Advanced Graph Traversal Patterns")
    print("=" * 60)
    
    # Find entities mentioned in specific document contexts
    print("\n--- Entities mentioned together in documents ---")
    
    # Get first document
    docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if docs.data:
        doc = docs.data[0]
        doc_id = doc.data.get("docId", "")
        
        print(f"\nDocument: {doc.data.get('title', '')[:50]}...")
        
        # Find mentions in this document
        mentions = db.records.find({
            "labels": ["MENTION"],
            "where": {
                "documentId": doc_id
            },
            "limit": 100
        })
        
        # Group by entity
        entity_mentions = defaultdict(list)
        for m in mentions.data:
            entity_key = m.data.get("entityKey", "")
            entity_mentions[entity_key].append(m.data.get("text", ""))
        
        print("\nEntities mentioned in this document:")
        for entity_key, texts in entity_mentions.items():
            # Get entity details
            entity = db.records.find({
                "labels": ["ENTITY"],
                "where": {"entityKey": entity_key},
                "limit": 1
            })
            
            if entity.data:
                name = entity.data[0].data.get("canonicalName", "Unknown")
                print(f"  - {name}: {', '.join(texts)}")
    
    # Find documents where specific entity appears
    print("\n--- Document co-occurrence for entities ---")
    
    # Get an entity
    entities = db.records.find({"labels": ["ENTITY"], "limit": 1})
    if entities.data:
        entity = entities.data[0]
        entity_key = entity.data.get("entityKey", "")
        name = entity.data.get("canonicalName", "")
        
        # Find mentions of this entity
        mentions = db.records.find({
            "labels": ["MENTION"],
            "where": {
                "entityKey": entity_key
            },
            "limit": 100
        })
        
        # Find which documents contain mentions of related entities
        related_entities = set()
        for m in mentions.data:
            doc_id = m.data.get("documentId", "")
            # Get other mentions in same document
            other_mentions = db.records.find({
                "labels": ["MENTION"],
                "where": {
                    "documentId": doc_id
                },
                "limit": 100
            })
            for om in other_mentions.data:
                related_key = om.data.get("entityKey", "")
                if related_key and related_key != entity_key:
                    related_entities.add(related_key)
        
        print(f"\nEntities mentioned in same documents as '{name}':")
        for rel_key in list(related_entities)[:5]:
            rel_entity = db.records.find({
                "labels": ["ENTITY"],
                "where": {"entityKey": rel_key},
                "limit": 1
            })
            if rel_entity.data:
                print(f"  - {rel_entity.data[0].data.get('canonicalName', 'Unknown')}")


def main():
    """Main demonstration function."""
    print("=" * 60)
    print("Cross-Document Coreference Resolution")
    print("Using Graph-Structured Context with RushDB")
    print("=" * 60)
    
    db = init_rushdb()
    
    # Check if data exists
    docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if not docs.data:
        print("\nNo data found. Run 'python seed.py' first to load sample data.")
        return
    
    print(f"\nConnected to RushDB. Found {len(docs.data) if docs.data else 0} documents.")
    
    # Run demonstrations
    demo_basic_graph_structure(db)
    demo_entity_resolution(db)
    demo_coreference_chains(db)
    demo_cross_document_resolution(db)
    demo_graph_relationships(db)
    demo_advanced_queries(db)
    
    print("\n" + "=" * 60)
    print("Demonstration Complete")
    print("=" * 60)
    
    print("\nKey takeaways:")
    print("  1. Documents, mentions, and entities are modeled as graph nodes")
    print("  2. Coreference relationships are stored as directed edges")
    print("  3. RushDB's relationship queries enable efficient graph traversal")
    print("  4. Cross-document resolution leverages the connected graph structure")
    print("\nFor more advanced coreference, consider:")
    print("  - Adding mention context (surrounding text)")
    print("  - Implementing entity linking with vector similarity")
    print("  - Building hierarchical entity clusters")
    print("  - Adding temporal/dynamic entity properties")


if __name__ == "__main__":
    main()
