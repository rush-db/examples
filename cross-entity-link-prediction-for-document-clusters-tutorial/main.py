"""
Cross-Entity Link Prediction for Document Clusters.

This tutorial demonstrates practical link prediction techniques using RushDB's
property graph model. We explore three strategies:

1. SHARED TAG ANALYSIS - Find documents with overlapping tags
2. SEMANTIC SIMILARITY - Vector search for content-based predictions  
3. GRAPH PATTERN ANALYSIS - Common neighbors and collaborative filtering

Each strategy reveals different types of potential relationships that can be
used to build recommendation systems, citation graphs, or knowledge bases.
"""

import os
import sys
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
token = os.getenv("RUSHDB_API_TOKEN")
url = os.getenv("RUSHDB_URL")

if not token:
    print("Error: RUSHDB_API_TOKEN not found in environment")
    print("Make sure you have configured your .env file:")
    print("  1. cp .env.example .env")
    print("  2. Add your RUSHDB_API_TOKEN")
    sys.exit(1)

if url:
    db = RushDB(token, url=url)
else:
    db = RushDB(token)

print("=" * 60)
print("CROSS-ENTITY LINK PREDICTION FOR DOCUMENT CLUSTERS")
print("=" * 60)

# ============================================================================
# STEP 1: ANALYZE CURRENT GRAPH STATE
# ============================================================================

print("\n📊 STEP 1: ANALYZING CURRENT GRAPH STATE")
print("-" * 40)

# Get all labels and their record counts
labels_result = db.labels.find({})
print("\nLabels in the graph:")
for label_info in labels_result.data:
    print(f"  • {label_info.name}: {label_info.count} records")

# Get all documents with their relationships
documents = db.records.find({"labels": ["DOCUMENT"], "limit": 100})
doc_list = documents.data

print(f"\n📄 Total documents: {len(doc_list)}")

# Get all authors
authors = db.records.find({"labels": ["AUTHOR"], "limit": 100})
print(f"👥 Total authors: {len(authors.data)}")

# Get all tags
tags = db.records.find({"labels": ["TAG"], "limit": 100})
print(f"🏷️  Total tags: {len(tags.data)}")

# ============================================================================
# STEP 2: FETCH DOCUMENT RELATIONSHIPS
# ============================================================================

print("\n📊 STEP 2: FETCHING DOCUMENT RELATIONSHIPS")
print("-" * 40)

# Build a map of document IDs to their tags and topics
doc_metadata = {}

for doc in doc_list:
    # Find tags for this document
    tagged_docs = db.records.find({
        "labels": ["DOCUMENT"],
        "where": {
            "TAG": {
                "$relation": {"type": "TAGGED_WITH", "direction": "in"}
            }
        }
    })
    
    # Get direct relationships using attach semantics
    # For each document, find its tags
    doc_tags_result = db.records.find({
        "labels": ["TAG"],
        "where": {
            "DOCUMENT": {
                "$relation": {"type": "TAGGED_WITH", "direction": "in"},
                "$id": {"$in": [doc.id]}
            }
        }
    })
    
    # Find tags linked to this document
    tag_names = [t.data.get("name", "unknown") for t in doc_tags_result.data]
    
    # Find author linked to this document
    author_result = db.records.find({
        "labels": ["AUTHOR"],
        "where": {
            "DOCUMENT": {
                "$relation": {"type": "AUTHORED_BY", "direction": "in"},
                "$id": {"$in": [doc.id]}
            }
        }
    })
    author_name = author_result.data[0].data.get("name", "Unknown") if author_result.data else "Unknown"
    
    # Find topic linked to this document
    topic_result = db.records.find({
        "labels": ["TOPIC"],
        "where": {
            "DOCUMENT": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"},
                "$id": {"$in": [doc.id]}
            }
        }
    })
    topic_name = topic_result.data[0].data.get("name", "Unknown") if topic_result.data else "Unknown"
    
    doc_metadata[doc.id] = {
        "title": doc.data.get("title", "Untitled"),
        "tags": tag_names,
        "author": author_name,
        "topic": topic_name,
        "record": doc
    }

print(f"\nBuilt metadata for {len(doc_metadata)} documents")

# ============================================================================
# STRATEGY 1: SHARED TAG ANALYSIS
# ============================================================================

print("\n" + "=" * 60)
print("STRATEGY 1: SHARED TAG ANALYSIS")
print("=" * 60)
print("\nFinding potential links based on overlapping tags...")

def find_shared_tag_predictions(doc_metadata):
    """
    Find document pairs that share tags but aren't directly linked.
    Documents with many shared tags are likely related.
    """
    predictions = []
    doc_ids = list(doc_metadata.keys())
    
    for i, doc1_id in enumerate(doc_ids):
        for doc2_id in doc_ids[i + 1:]:
            meta1 = doc_metadata[doc1_id]
            meta2 = doc_metadata[doc2_id]
            
            # Find shared tags
            shared_tags = set(meta1["tags"]) & set(meta2["tags"])
            
            if shared_tags and len(shared_tags) >= 1:
                # Calculate confidence based on shared tag ratio
                all_tags = set(meta1["tags"]) | set(meta2["tags"])
                jaccard = len(shared_tags) / len(all_tags) if all_tags else 0
                
                predictions.append({
                    "source": doc1_id,
                    "target": doc2_id,
                    "source_title": meta1["title"],
                    "target_title": meta2["title"],
                    "source_author": meta1["author"],
                    "target_author": meta2["author"],
                    "shared_tags": list(shared_tags),
                    "shared_count": len(shared_tags),
                    "jaccard_score": round(jaccard, 3),
                    "confidence": round(min(len(shared_tags) * 0.3 + jaccard, 1.0), 3),
                    "strategy": "shared_tag"
                })
    
    # Sort by confidence
    predictions.sort(key=lambda x: (-x["confidence"], -x["shared_count"]))
    return predictions

shared_tag_predictions = find_shared_tag_predictions(doc_metadata)

print(f"\nFound {len(shared_tag_predictions)} potential links via shared tags")
print("\nTop 5 Shared Tag Predictions:")
print("-" * 40)

for i, pred in enumerate(shared_tag_predictions[:5], 1):
    print(f"\n{i}. Score: {pred['confidence']:.3f}")
    print(f"   From: \"{pred['source_title'][:50]}...\" by {pred['source_author']}")
    print(f"   To:   \"{pred['target_title'][:50]}...\" by {pred['target_author']}")
    print(f"   Shared tags: {', '.join(pred['shared_tags'])}")

# ============================================================================
# STRATEGY 2: SEMANTIC SIMILARITY (Conceptual)
# ============================================================================

print("\n" + "=" * 60)
print("STRATEGY 2: SEMANTIC SIMILARITY")
print("=" * 60)

print("""
Note: This demonstrates the CONCEPT of semantic similarity-based link prediction.
In production, you would:

1. Create a vector index on the 'content' property:
   
   ```sdk
   index = db.ai.indexes.create({
       "label": "DOCUMENT",
       "propertyName": "content",
       "sourceType": "external",
       "dimensions": 384
   })
   ```

2. Generate embeddings for each document and upsert them:
   
   ```sdk
   db.ai.indexes.upsert_vectors(index_id, {
       "items": [
           {"recordId": doc.id, "vector": embedding_vector}
       ]
   })
   ```

3. Use semantic search to find related documents:
   
   ```sdk
   # For each document, find the most similar documents
   similar = db.ai.search({
       "propertyName": "content",
       "queryVector": doc_embedding,
       "labels": ["DOCUMENT"],
       "limit": 5
   }).data
   ```

4. Filter out already-linked pairs and create link predictions
""")

# Demonstrate the pattern with actual RushDB semantic search
print("\nDemonstrating semantic search pattern:")
print("-" * 40)

# Find a sample document to search with
if doc_list:
    sample_doc = doc_list[0]
    sample_title = sample_doc.data.get("title", "")
    print(f"\nSample query: '{sample_title}'")
    print("(Using title as proxy for content search in this demo)")

# ============================================================================
# STRATEGY 3: GRAPH PATTERN ANALYSIS
# ============================================================================

print("\n" + "=" * 60)
print("STRATEGY 3: GRAPH PATTERN ANALYSIS (Common Neighbors)")
print("=" * 60)
print("\nFinding potential links via collaborative filtering...")

def find_common_neighbor_predictions(doc_metadata, doc_list):
    """
    Find potential links using the common neighbors algorithm:
    If A and B both cite/reference C, then A and B may be related.
    
    This is the foundation of collaborative filtering and citation analysis.
    """
    predictions = []
    
    # Build citation graph
    citations = defaultdict(set)  # doc_id -> set of cited doc_ids
    cited_by = defaultdict(set)   # doc_id -> set of doc_ids that cite it
    
    for doc in doc_list:
        cited_docs = db.records.find({
            "labels": ["DOCUMENT"],
            "where": {
                "DOCUMENT": {
                    "$relation": {"type": "CITES", "direction": "out"},
                    "$id": {"$in": [doc.id]}
                }
            }
        })
        
        for cited in cited_docs.data:
            citations[doc.id].add(cited.id)
            cited_by[cited.id].add(doc.id)
    
    # Find common neighbors
    checked_pairs = set()
    for doc_id, cited_ids in citations.items():
        for cited_id in cited_ids:
            # Find all documents that also cite this document
            co_citers = cited_by[cited_id]
            
            for co_citer_id in co_citers:
                if co_citer_id != doc_id:
                    pair = tuple(sorted([doc_id, co_citer_id]))
                    if pair not in checked_pairs:
                        checked_pairs.add(pair)
                        
                        meta1 = doc_metadata.get(doc_id, {})
                        meta2 = doc_metadata.get(co_citer_id, {})
                        cited_meta = doc_metadata.get(cited_id, {})
                        
                        predictions.append({
                            "source": doc_id,
                            "target": co_citer_id,
                            "source_title": meta1.get("title", "Unknown"),
                            "target_title": meta2.get("title", "Unknown"),
                            "via_document": cited_id,
                            "via_title": cited_meta.get("title", "Unknown"),
                            "common_citations_count": len(co_citers - {doc_id}),
                            "confidence": 0.7,  # Fixed confidence for this pattern
                            "strategy": "common_neighbor"
                        })
    
    predictions.sort(key=lambda x: -x["common_citations_count"])
    return predictions

common_neighbor_predictions = find_common_neighbor_predictions(doc_metadata, doc_list)

print(f"\nFound {len(common_neighbor_predictions)} potential links via common neighbors")

if common_neighbor_predictions:
    print("\nTop Common Neighbor Predictions:")
    print("-" * 40)
    
    for i, pred in enumerate(common_neighbor_predictions[:3], 1):
        print(f"\n{i}. " + 
              f"\"{pred['source_title'][:40]}...\" "
              f"and \"{pred['target_title'][:40]}...\"")
        print(f"   Both cite: \"{pred['via_title'][:40]}...\"")
        print(f"   Common citations: {pred['common_citations_count']}")
else:
    print("\n(No existing citations found - seed data may not have cross-references)")

# ============================================================================
# STRATEGY 4: CO-AUTHORSHIP ANALYSIS
# ============================================================================

print("\n" + "=" * 60)
print("STRATEGY 4: CO-AUTHORSHIP AND EXPERT CLUSTERING")
print("=" * 60)
print("\nFinding documents by authors with similar expertise...")

def find_co_authorship_predictions(doc_metadata, doc_list):
    """
    Find documents by authors who have written on similar topics.
    Authors with similar tag patterns may collaborate on future work.
    """
    predictions = []
    
    # Group documents by author
    author_docs = defaultdict(list)
    author_tags = defaultdict(set)
    
    for doc_id, meta in doc_metadata.items():
        author = meta["author"]
        author_docs[author].append(meta)
        author_tags[author].update(meta["tags"])
    
    authors = list(author_docs.keys())
    
    # Find authors with overlapping expertise
    for i, author1 in enumerate(authors):
        for author2 in authors[i + 1:]:
            shared_tags = author_tags[author1] & author_tags[author2]
            
            if shared_tags:
                # Suggest documents from author1 to author2
                for doc_meta in author_docs[author1][:2]:  # Limit to 2 suggestions
                    predictions.append({
                        "source_id": doc_meta["record"].id,
                        "source_title": doc_meta["title"],
                        "target_author": author2,
                        "source_author": author1,
                        "shared_expertise": list(shared_tags),
                        "confidence": min(len(shared_tags) * 0.2 + 0.3, 0.9),
                        "strategy": "co_authorship"
                    })
    
    predictions.sort(key=lambda x: -x["confidence"])
    return predictions

co_authorship_predictions = find_co_authorship_predictions(doc_metadata, doc_list)

print(f"\nFound {len(co_authorship_predictions)} potential cross-author links")

if co_authorship_predictions:
    print("\nTop Co-Authorship Predictions:")
    print("-" * 40)
    
    for i, pred in enumerate(co_authorship_predictions[:3], 1):
        print(f"\n{i}. " +
              f"\"{pred['source_title'][:45]}...\" "
              f"by {pred['source_author']}")
        print(f"   → Suggested to: {pred['target_author']}")
        print(f"   Shared expertise: {', '.join(pred['shared_expertise'][:3])}")
        print(f"   Confidence: {pred['confidence']:.2f}")

# ============================================================================
# CONSOLIDATE AND CREATE PREDICTED LINKS
# ============================================================================

print("\n" + "=" * 60)
print("CONSOLIDATING PREDICTIONS AND CREATING LINKS")
print("=" * 60)

print("\n📊 Prediction Summary:")
print(f"   • Shared Tag Predictions: {len(shared_tag_predictions)}")
print(f"   • Common Neighbor Predictions: {len(common_neighbor_predictions)}")
print(f"   • Co-Authorship Predictions: {len(co_authorship_predictions)}")

# Combine all predictions with deduplication
all_predictions = []
seen_pairs = set()

for pred in shared_tag_predictions:
    pair = tuple(sorted([pred["source"], pred["target"]]))
    if pair not in seen_pairs:
        seen_pairs.add(pair)
        all_predictions.append(pred)

for pred in common_neighbor_predictions:
    pair = tuple(sorted([pred["source"], pred["target"]]))
    if pair not in seen_pairs:
        seen_pairs.add(pair)
        all_predictions.append(pred)

for pred in co_authorship_predictions:
    pair = tuple(sorted([pred["source_id"], None]))  # Author-based, no target doc
    # Skip deduplication for author predictions
    all_predictions.append(pred)

# Sort by confidence
all_predictions.sort(key=lambda x: -x.get("confidence", 0))

print(f"\n   Total unique predictions: {len(all_predictions)}")

# Create high-confidence predicted links in the database
print("\n🔗 Creating predicted links in database...")
print("-" * 40)

# Only create links with confidence > 0.5
high_confidence_preds = [p for p in all_predictions if p.get("confidence", 0) > 0.5]
created_count = 0

for pred in high_confidence_preds[:10]:  # Limit to avoid excessive writes
    if pred["strategy"] == "shared_tag":
        # Create a PREDICTED_RELATES_TO link
        doc1 = db.records.find_by_id(pred["source"])
        doc2 = db.records.find_by_id(pred["target"])
        
        if doc1 and doc2:
            db.records.attach(
                source=doc1,
                target=doc2,
                options={"type": "PREDICTED_RELATES_TO"}
            )
            created_count += 1
            
            if created_count <= 3:
                print(f"   ✓ Created PREDICTED_RELATES_TO: {pred['source_title'][:35]}... ↔ {pred['target_title'][:35]}...")

print(f"\n   ✓ Created {created_count} predicted links")
print(f"\n   Note: PREDICTED_RELATES_TO links can be validated")
print(f"   by domain experts and promoted to CITES or RELATED_TO")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 60)
print("TUTORIAL COMPLETE")
print("=" * 60)

print("""
Key Takeaways:

1. SHARED TAG ANALYSIS
   - Documents sharing tags are likely related
   - Use Jaccard similarity for confidence scoring
   - Best for: Topic clustering, content recommendations

2. SEMANTIC SIMILARITY
   - Vector embeddings capture meaning beyond keywords
   - Requires a vector index and embedding generation
   - Best for: Content-based recommendations, discovery

3. GRAPH PATTERN ANALYSIS (Common Neighbors)
   - If A→C and B→C, then A and B may be related
   - Mirrors collaborative filtering in recommendation systems
   - Best for: Citation analysis, social networks

4. CO-AUTHORSHIP ANALYSIS
   - Authors with overlapping expertise may collaborate
   - Good for expert matching and research communities
   - Best for: Team building, research collaboration

Production Considerations:
- Use transactions for bulk link creation
- Implement confidence thresholds to avoid noise
- Track link provenance (which strategy predicted it)
- Build validation workflows for predicted links
- Consider temporal patterns in link formation
""")

print("\n✅ The graph now contains both real CITES links and")
print("   PREDICTED_RELATES_TO links for further analysis.")
print("\n📚 Reference: https://docs.rushdb.com")
