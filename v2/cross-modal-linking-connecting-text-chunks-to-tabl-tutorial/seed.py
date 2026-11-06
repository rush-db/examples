#!/usr/bin/env python3
"""
Seed script: Ingests the sample research paper into RushDB.

This script:
1. Loads the sample document JSON
2. Chunks text sections into TextChunk records
3. Creates TableChunk records for each table
4. Creates ImageReference records for each image
5. Links everything with cross-modal relationships
6. Creates vector embeddings for text chunks

Run once to populate the database, then use main.py to query.
"""

import json
import os
from pathlib import Path

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

# Load the sentence transformer model for embeddings
MODEL_NAME = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
print(f"Loading embedding model: {MODEL_NAME}")
embedder = SentenceTransformer(MODEL_NAME)
EMBEDDING_DIM = embedder.get_sentence_embedding_dimension()
print(f"Embedding dimension: {EMBEDDING_DIM}")


def load_document() -> dict:
    """Load the sample research paper JSON."""
    doc_path = Path(__file__).parent / "data" / "document.json"
    with open(doc_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_vector_index():
    """Create vector index for TextChunk.content if it doesn't exist."""
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        if idx["label"] == "TextChunk" and idx["propertyName"] == "content":
            print(f"Vector index already exists: TextChunk.content")
            return idx
    
    print("Creating vector index for TextChunk.content...")
    index = db.ai.indexes.create({
        "label": "TextChunk",
        "propertyName": "content",
        "sourceType": "external",
        "dimensions": EMBEDDING_DIM,
        "similarityFunction": "cosine"
    })
    print(f"Vector index created: {index.data['__id']}")
    return index


def ingest_document(document: dict) -> dict:
    """
    Ingest the document into RushDB, creating all nodes and relationships.
    
    Returns a dict with references to created records:
    - document_record
    - text_chunks: list of TextChunk records
    - table_chunks: list of TableChunk records
    - image_refs: list of ImageReference records
    """
    print("\n=== Starting Document Ingestion ===")
    
    # Track all created records
    created = {
        "document": None,
        "text_chunks": [],
        "table_chunks": [],
        "image_refs": []
    }
    
    # ============================================
    # 1. Create the Document record
    # ============================================
    print("\n[1/5] Creating Document record...")
    document_record = db.records.create(
        label="DOCUMENT",
        data={
            "title": document["title"],
            "authors": document["authors"],
            "institution": document["institution"],
            "year": document["year"]
        }
    )
    created["document"] = document_record
    print(f"  Created: {document_record.id} - '{document['title']}'")
    
    # ============================================
    # 2. Create TextChunks with embeddings
    # ============================================
    print("\n[2/5] Creating TextChunks with embeddings...")
    
    # Collect all text content for batch embedding
    sections_to_embed = []
    for section in document["sections"]:
        # Combine heading and content for richer embedding
        full_text = f"{section['heading']}: {section['content']}"
        sections_to_embed.append({
            "section_id": section["id"],
            "heading": section["heading"],
            "content": section["content"],
            "full_text": full_text
        })
    
    # Generate embeddings in batch
    print(f"  Generating {len(sections_to_embed)} embeddings...")
    texts_for_embedding = [s["full_text"] for s in sections_to_embed]
    embeddings = embedder.encode(texts_for_embedding, show_progress_bar=True)
    
    # Ensure vector index exists
    index_info = ensure_vector_index()
    index_id = index_info.data["__id"]
    
    # Create TextChunk records within a transaction
    with db.transactions.begin() as tx:
        for section, embedding in zip(sections_to_embed, embeddings):
            text_chunk = db.records.create(
                label="TextChunk",
                data={
                    "section_id": section["section_id"],
                    "heading": section["heading"],
                    "content": section["content"]
                },
                transaction=tx
            )
            created["text_chunks"].append(text_chunk)
            
            # Link to document
            db.records.attach(
                source=document_record,
                target=text_chunk,
                options={"type": "SUPPORTS", "direction": "out"},
                transaction=tx
            )
    
    print(f"  Created {len(created['text_chunks'])} TextChunk records")
    
    # Upsert vectors to the index
    print("  Uploading vectors to index...")
    vector_items = [
        {
            "recordId": chunk.id,
            "vector": embedding.tolist()
        }
        for chunk, embedding in zip(created["text_chunks"], embeddings)
    ]
    db.ai.indexes.upsert_vectors(index_id, {"items": vector_items})
    print("  Vectors uploaded successfully")
    
    # ============================================
    # 3. Create TableChunks
    # ============================================
    print("\n[3/5] Creating TableChunks...")
    
    with db.transactions.begin() as tx:
        for table in document["tables"]:
            table_chunk = db.records.create(
                label="TableChunk",
                data={
                    "table_id": table["id"],
                    "title": table["title"],
                    "caption": table["caption"],
                    "headers": table["headers"],
                    "rows": table["rows"]
                },
                transaction=tx
            )
            created["table_chunks"].append(table_chunk)
            
            # Link table to document
            db.records.attach(
                source=document_record,
                target=table_chunk,
                options={"type": "CONTAINS", "direction": "out"},
                transaction=tx
            )
    
    print(f"  Created {len(created['table_chunks'])} TableChunk records")
    
    # ============================================
    # 4. Create ImageReferences
    # ============================================
    print("\n[4/5] Creating ImageReferences...")
    
    with db.transactions.begin() as tx:
        for image in document["images"]:
            image_ref = db.records.create(
                label="ImageReference",
                data={
                    "image_id": image["id"],
                    "filename": image["filename"],
                    "caption": image["caption"],
                    "bounding_box": image["bounding_box"],
                    "referenced_in": image["referenced_in"],
                    "derived_from": image["derived_from"]
                },
                transaction=tx
            )
            created["image_refs"].append(image_ref)
            
            # Link image to document
            db.records.attach(
                source=document_record,
                target=image_ref,
                options={"type": "CONTAINS", "direction": "out"},
                transaction=tx
            )
    
    print(f"  Created {len(created['image_refs'])} ImageReference records")
    
    # ============================================
    # 5. Create Cross-Modal Relationships
    # ============================================
    print("\n[5/5] Creating cross-modal relationships...")
    
    # Build lookup maps for linking
    text_chunk_by_section = {
        tc.get("section_id"): tc for tc in created["text_chunks"]
    }
    table_chunk_by_id = {
        tbl.get("table_id"): tbl for tbl in created["table_chunks"]
    }
    image_ref_by_id = {
        img.get("image_id"): img for img in created["image_refs"]
    }
    
    with db.transactions.begin() as tx:
        # Link tables to text chunks (SUPPORTS)
        for table in document["tables"]:
            # Tables are referenced in the experiments section
            table_chunk = table_chunk_by_id.get(table["id"])
            if table["id"] == "table_1":
                text_chunk = text_chunk_by_section.get("experiments")
                if text_chunk and table_chunk:
                    db.records.attach(
                        source=table_chunk,
                        target=text_chunk,
                        options={"type": "SUPPORTS", "direction": "out"},
                        transaction=tx
                    )
                    print(f"  Linked table '{table['title']}' -> text 'experiments' (SUPPORTS)")
        
        # Link images to text chunks (ILLUSTRATES)
        for image in document["images"]:
            image_ref = image_ref_by_id.get(image["id"])
            for section_id in image["referenced_in"]:
                text_chunk = text_chunk_by_section.get(section_id)
                if text_chunk and image_ref:
                    db.records.attach(
                        source=image_ref,
                        target=text_chunk,
                        options={"type": "ILLUSTRATES", "direction": "out"},
                        transaction=tx
                    )
                    print(f"  Linked image '{image['filename']}' -> text '{section_id}' (ILLUSTRATES)")
        
        # Link images to source tables (SOURCE_OF)
        for image in document["images"]:
            if image["derived_from"]:
                image_ref = image_ref_by_id.get(image["id"])
                table_chunk = table_chunk_by_id.get(image["derived_from"])
                if image_ref and table_chunk:
                    db.records.attach(
                        source=table_chunk,
                        target=image_ref,
                        options={"type": "SOURCE_OF", "direction": "out"},
                        transaction=tx
                    )
                    print(f"  Linked table '{image['derived_from']}' -> image '{image['filename']}' (SOURCE_OF)")
    
    print("\n=== Document Ingestion Complete ===")
    return created


def check_existing_data():
    """Check if document already exists to avoid duplicates."""
    existing = db.records.find({
        "labels": ["DOCUMENT"],
        "where": {"title": {"$contains": "Adaptive Learning Rate"}},
        "limit": 1
    })
    return existing.total > 0


def main():
    """Main entry point."""
    print("=" * 60)
    print("Cross-Modal Document Ingestion - Seed Script")
    print("=" * 60)
    
    # Check for existing data
    if check_existing_data():
        print("\n⚠️  Document already exists in RushDB!")
        print("   Skipping ingestion. Run 'python main.py' to query.")
        print("   Or delete existing data to re-ingest.")
        return
    
    # Load document
    document = load_document()
    print(f"\nLoaded document: '{document['title']}'")
    print(f"  Sections: {len(document['sections'])}")
    print(f"  Tables: {len(document['tables'])}")
    print(f"  Images: {len(document['images'])}")
    
    # Ingest document
    created = ingest_document(document)
    
    # Summary
    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    print(f"  Document: 1")
    print(f"  TextChunks: {len(created['text_chunks'])}")
    print(f"  TableChunks: {len(created['table_chunks'])}")
    print(f"  ImageReferences: {len(created['image_refs'])}")
    print("\n✓ Document ingested successfully!")
    print("\nRun 'python main.py' to query cross-modal relationships.")


if __name__ == "__main__":
    main()
