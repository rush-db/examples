#!/usr/bin/env python3
"""
Main script: Demonstrates cross-modal query and retrieval.

This script shows how to:
1. Perform semantic search for text chunks
2. Traverse graph edges to find related tables and images
3. Display cross-modal results as a unified response
"""

import os
from typing import Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError(
        "RUSHDB_API_KEY not found in environment. "
        "Copy .env.example to .env and add your API key."
    )

db = RushDB(API_KEY)

# Load the sentence transformer model
MODEL_NAME = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
embedder = SentenceTransformer(MODEL_NAME)


def find_supporting_tables(text_chunk_id: str) -> list:
    """
    Find tables that support the given text chunk.
    
    Traverses: TextChunk <- SUPPORTS <- TableChunk
    """
    tables = db.records.find({
        "labels": ["TableChunk"],
        "where": {
            "TextChunk": {
                "$relation": {"type": "SUPPORTS", "direction": "in"},
                "$id": text_chunk_id
            }
        }
    })
    return tables.data


def find_illustrating_images(text_chunk_id: str) -> list:
    """
    Find images that illustrate the given text chunk.
    
    Traverses: TextChunk <- ILLUSTRATES <- ImageReference
    """
    images = db.records.find({
        "labels": ["ImageReference"],
        "where": {
            "TextChunk": {
                "$relation": {"type": "ILLUSTRATES", "direction": "in"},
                "$id": text_chunk_id
            }
        }
    })
    return images.data


def find_source_tables(image_id: str) -> list:
    """
    Find tables that are the source of the given image.
    
    Traverses: TableChunk -> SOURCE_OF -> ImageReference
    """
    tables = db.records.find({
        "labels": ["TableChunk"],
        "where": {
            "ImageReference": {
                "$relation": {"type": "SOURCE_OF", "direction": "in"},
                "$id": image_id
            }
        }
    })
    return tables.data


def cross_modal_query(query: str, limit: int = 3) -> dict:
    """
    Perform cross-modal query: find text chunks by semantic similarity,
    then traverse to related tables and images.
    
    Args:
        query: Natural language query
        limit: Maximum number of text chunks to retrieve
        
    Returns:
        Dictionary with results organized by modality
    """
    print(f"\n>>> Query: \"{query}\"")
    print("=" * 60)
    
    # 1. Embed the query
    query_vector = embedder.encode([query])[0].tolist()
    
    # 2. Semantic search for text chunks
    print("\n[1] Searching for relevant text chunks...")
    search_results = db.ai.search({
        "propertyName": "content",
        "queryVector": query_vector,
        "labels": ["TextChunk"],
        "limit": limit
    })
    
    if not search_results.data:
        print("  No text chunks found matching the query.")
        return {"text_chunks": [], "tables": [], "images": []}
    
    print(f"  Found {len(search_results.data)} text chunks")
    
    # 3. For each text chunk, find related tables and images
    results = {
        "query": query,
        "text_chunks": [],
        "tables": [],
        "images": []
    }
    
    for chunk in search_results.data:
        text_result = {
            "id": chunk.id,
            "heading": chunk.get("heading", ""),
            "section_id": chunk.get("section_id", ""),
            "content": chunk.get("content", "")[:200] + "...",  # Truncate for display
            "score": chunk.score,
            "related_tables": [],
            "related_images": []
        }
        
        # Find supporting tables
        tables = find_supporting_tables(chunk.id)
        for table in tables:
            text_result["related_tables"].append({
                "id": table.id,
                "title": table.get("title", ""),
                "caption": table.get("caption", ""),
                "rows_count": len(table.get("rows", [])),
                "columns": table.get("headers", [])
            })
            # Add to results if not already present
            if not any(t["id"] == table.id for t in results["tables"]):
                results["tables"].append({
                    "id": table.id,
                    "title": table.get("title", ""),
                    "caption": table.get("caption", ""),
                    "headers": table.get("headers", []),
                    "rows": table.get("rows", [])
                })
        
        # Find illustrating images
        images = find_illustrating_images(chunk.id)
        for image in images:
            text_result["related_images"].append({
                "id": image.id,
                "filename": image.get("filename", ""),
                "caption": image.get("caption", "")
            })
            # Add to results if not already present
            if not any(i["id"] == image.id for i in results["images"]):
                results["images"].append({
                    "id": image.id,
                    "filename": image.get("filename", ""),
                    "caption": image.get("caption", ""),
                    "bounding_box": image.get("bounding_box", {})
                })
        
        results["text_chunks"].append(text_result)
    
    return results


def display_results(results: dict):
    """Display cross-modal results in a readable format."""
    print("\n" + "=" * 60)
    print("CROSS-MODAL RETRIEVAL RESULTS")
    print("=" * 60)
    
    # Display text chunks
    for i, chunk in enumerate(results["text_chunks"], 1):
        print(f"\n--- Top Text Chunk #{i} (relevance: {chunk['score']:.3f}) ---")
        print(f"Section: {chunk['section_id']} | Heading: {chunk['heading']}")
        print(f"Content: \"{chunk['content'][:150]}...\"")
        
        if chunk["related_tables"]:
            print(f"\n  [RELATED] Tables: {len(chunk['related_tables'])} found")
            for table in chunk["related_tables"]:
                print(f"    - \"{table['title']}\" ({table['rows_count']} rows, {len(table['columns'])} columns)")
                print(f"      Related to chunk via: SUPPORTS")
        
        if chunk["related_images"]:
            print(f"\n  [RELATED] Images: {len(chunk['related_images'])} found")
            for image in chunk["related_images"]:
                print(f"    - \"{image['filename']}\" - {image['caption'][:60]}...")
                print(f"      Related to chunk via: ILLUSTRATES")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Text chunks retrieved: {len(results['text_chunks'])}")
    print(f"  Unique tables found: {len(results['tables'])}")
    print(f"  Unique images found: {len(results['images'])}")


def display_table_details(results: dict):
    """Display detailed table information."""
    if not results["tables"]:
        return
    
    print("\n" + "=" * 60)
    print("RELATED TABLE DETAILS")
    print("=" * 60)
    
    for table in results["tables"]:
        print(f"\n  Table: {table['title']}")
        print(f"  Headers: {table['headers']}")
        print(f"  Rows:")
        for row in table["rows"][:5]:  # Show first 5 rows
            print(f"    {row}")
        if len(table["rows"]) > 5:
            print(f"    ... and {len(table['rows']) - 5} more rows")


def demonstrate_graph_traversal():
    """Additional demonstration of graph traversal patterns."""
    print("\n" + "=" * 60)
    print("GRAPH TRAVERSAL DEMONSTRATION")
    print("=" * 60)
    
    # Find all documents
    docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if not docs.data:
        print("No document found. Run seed.py first.")
        return
    
    doc = docs.data[0]
    print(f"\nDocument: {doc.get('title')}")
    
    # Find all text chunks linked to this document
    text_chunks = db.records.find({
        "labels": ["TextChunk"],
        "where": {
            "DOCUMENT": {
                "$relation": {"type": "SUPPORTS", "direction": "in"},
                "$id": doc.id
            }
        }
    })
    print(f"  Text sections: {len(text_chunks.data)}")
    
    # Find all table chunks
    tables = db.records.find({
        "labels": ["TableChunk"],
        "where": {
            "DOCUMENT": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "$id": doc.id
            }
        }
    })
    print(f"  Tables: {len(tables.data)}")
    
    # Find all images
    images = db.records.find({
        "labels": ["ImageReference"],
        "where": {
            "DOCUMENT": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "$id": doc.id
            }
        }
    })
    print(f"  Images: {len(images.data)}")
    
    # Demonstrate relationship type counts
    print("\n  Relationship counts:")
    for rel_type in ["SUPPORTS", "CONTAINS", "ILLUSTRATES", "SOURCE_OF"]:
        rels = db.relationships.find({"where": {"type": rel_type}, "limit": 100})
        print(f"    - {rel_type}: {len(rels.data)}")


def check_data_exists() -> bool:
    """Check if document data exists in RushDB."""
    existing = db.records.find({
        "labels": ["DOCUMENT"],
        "limit": 1
    })
    return existing.total > 0


def main():
    """Main entry point."""
    print("=" * 60)
    print("Cross-Modal Document Retrieval - Main Query Script")
    print("=" * 60)
    
    # Check for existing data
    if not check_data_exists():
        print("\n⚠️  No document found in RushDB!")
        print("   Run 'python seed.py' first to ingest the sample document.")
        return
    
    # Demonstrate graph traversal
    demonstrate_graph_traversal()
    
    # Sample queries to demonstrate cross-modal retrieval
    queries = [
        "neural network training improvements",
        "optimizer performance comparison",
        "experimental results CIFAR",
        "learning rate optimization"
    ]
    
    print("\n" + "=" * 60)
    print("CROSS-MODAL QUERY DEMONSTRATIONS")
    print("=" * 60)
    
    for query in queries:
        results = cross_modal_query(query, limit=2)
        display_results(results)
        display_table_details(results)
    
    print("\n" + "=" * 60)
    print("TUTORIAL COMPLETE")
    print("=" * 60)
    print("\nTo build on this tutorial:")
    print("  1. Modify data/document.json with your own document structure")
    print("  2. Adjust chunking logic in seed.py for your format")
    print("  3. Update relationship types to match your domain")
    print("  4. Query different aspects of your multimodal data")
    print("\nSee README.md for more patterns and best practices.")


if __name__ == "__main__":
    main()
