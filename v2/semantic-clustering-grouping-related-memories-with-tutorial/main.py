"""
Semantic Clustering: Grouping Related Memories with Vector Proximity

This tutorial demonstrates how to build a semantic memory clustering pipeline
using RushDB's vector search capabilities combined with graph traversal.

Key concepts:
1. Generate embeddings for memory content
2. Store vectors alongside graph properties
3. Query for semantically similar memories
4. Perform cluster analysis (neighborhoods, groups, outliers)
5. Compose graph + vector search for richer queries
"""

import os
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
import numpy as np

from rushdb import RushDB

# Load environment variables
load_dotenv()


def setup_db():
    """Initialize RushDB client."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError("RUSHDB_API_KEY not found. Please create a .env file.")
    return RushDB(api_key, url=os.getenv("RUSHDB_URL"))


def ensure_vector_index(db):
    """Ensure a vector index exists for MEMORY.content."""
    indexes = db.ai.indexes.find()
    
    for idx in indexes.data:
        if idx["label"] == "MEMORY" and idx["propertyName"] == "content":
            print(f"✓ Using existing vector index: {idx['__id']}")
            return idx["__id"]
    
    # Create new index
    print("Creating new vector index for MEMORY.content...")
    index = db.ai.indexes.create({
        "label": "MEMORY",
        "propertyName": "content",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine",
    })
    index_id = index.data["__id"]
    print(f"✓ Vector index created: {index_id}")
    return index_id


def demo_semantic_search(db):
    """
    Demo 1: Semantic Similarity Search
    
    Use db.ai.search() to find memories semantically related to a query.
    This uses cosine similarity between the query embedding and stored vectors.
    """
    print("\n" + "="*60)
    print("1. SEMANTIC SIMILARITY SEARCH")
    print("="*60)
    
    queries = [
        "planning a trip to Japan",
        "family gatherings and traditions",
        "learning new skills and growth",
    ]
    
    for query in queries:
        print(f"\nQuery: \"{query}\"")
        results = db.ai.search({
            "propertyName": "content",
            "query": query,
            "labels": ["MEMORY"],
            "limit": 5
        })
        
        for i, memory in enumerate(results.data[:5], 1):
            score = memory.score
            title = memory.data.get("title", "Untitled")
            theme = memory.data.get("theme", "unknown")
            print(f"  [{score:.3f}] {title} ({theme})")


def demo_memory_neighborhoods(db):
    """
    Demo 2: Memory Neighborhoods
    
    Find the k-nearest neighbors of a specific memory to discover local clusters.
    This reveals which memories are most semantically related to a given memory.
    """
    print("\n" + "="*60)
    print("2. MEMORY NEIGHBORHOODS (K-Nearest Neighbors)")
    print("="*60)
    
    # Get a sample memory to explore
    all_memories = db.records.find({"labels": ["MEMORY"], "limit": 1})
    if not all_memories.data:
        print("No memories found. Run seed.py first!")
        return
    
    # Pick a travel-themed memory as our anchor
    travel_memories = db.records.find({
        "labels": ["MEMORY"],
        "where": {"theme": "travel"},
        "limit": 10
    })
    
    if not travel_memories.data:
        print("No travel memories found.")
        return
    
    anchor = travel_memories.data[0]
    anchor_title = anchor.data.get("title", "Untitled")
    
    print(f"\nAnchor Memory: \"{anchor_title}\"")
    print("Finding 5 nearest neighbors...")
    
    # Use the anchor's content as the query vector source
    # (In practice, you'd use the stored vector directly)
    neighbors = db.ai.search({
        "propertyName": "content",
        "query": anchor.data.get("content", ""),
        "labels": ["MEMORY"],
        "limit": 6  # Include anchor itself
    })
    
    print("\n  Semantically Similar Memories:")
    for i, memory in enumerate(neighbors.data[1:], 1):  # Skip anchor
        score = memory.score
        title = memory.data.get("title", "Untitled")
        theme = memory.data.get("theme", "unknown")
        print(f"  {i}. [{score:.3f}] {title}")
        print(f"     Theme: {theme}, Tags: {memory.data.get('tags', [])}")


def demo_cluster_analysis(db):
    """
    Demo 3: Cluster Analysis
    
    Identify memory groups by analyzing semantic similarity patterns.
    This shows how to find:
    - Related memory groups
    - Core themes/topics
    - Semantic outliers
    """
    print("\n" + "="*60)
    print("3. CLUSTER ANALYSIS")
    print("="*60)
    
    # Get all memories for clustering
    all_memories = db.records.find({"labels": ["MEMORY"], "limit": 100})
    memory_list = all_memories.data
    
    if not memory_list:
        print("No memories found.")
        return
    
    print(f"\nAnalyzing {len(memory_list)} memories...")
    
    # Group memories by theme
    theme_groups = defaultdict(list)
    for memory in memory_list:
        theme = memory.data.get("theme", "unknown")
        theme_groups[theme].append(memory)
    
    print("\n  Memories by Theme:")
    for theme, memories in sorted(theme_groups.items(), key=lambda x: -len(x[1])):
        print(f"    {theme}: {len(memories)} memories")
    
    # Find semantically representative memory for each theme
    print("\n  Theme Centroids (most representative memories):")
    for theme in list(theme_groups.keys())[:5]:
        theme_memories = theme_groups[theme]
        if not theme_memories:
            continue
        
        # Find the memory closest to the theme center
        centroid = db.ai.search({
            "propertyName": "content",
            "query": f"typical {theme} experience",
            "labels": ["MEMORY"],
            "where": {"theme": theme},
            "limit": 1
        })
        
        if centroid.data:
            best = centroid.data[0]
            print(f"    {theme}: \"{best.data.get('title', 'Untitled')}\"")


def demo_outlier_detection(db):
    """
    Demo 4: Outlier Detection
    
    Find memories that are semantically distant from all other memories.
    These outliers represent unique or unusual experiences.
    """
    print("\n" + "="*60)
    print("4. OUTLIER DETECTION")
    print("="*60)
    
    # Get a sample of memories
    all_memories = db.records.find({"labels": ["MEMORY"], "limit": 50})
    memory_list = all_memories.data
    
    if len(memory_list) < 10:
        print("Not enough memories for outlier detection.")
        return
    
    print("\nFinding semantically isolated memories...")
    
    outlier_scores = []
    
    for memory in memory_list:
        # Find its most similar memories
        similar = db.ai.search({
            "propertyName": "content",
            "query": memory.data.get("content", ""),
            "labels": ["MEMORY"],
            "limit": 6
        })
        
        # Calculate average similarity to others (excluding self)
        if similar.data:
            scores = [m.score for m in similar.data[1:]]  # Skip self
            if scores:
                avg_score = sum(scores) / len(scores)
                outlier_scores.append((memory, avg_score))
    
    # Sort by lowest average similarity (most isolated)
    outlier_scores.sort(key=lambda x: x[1])
    
    print("\n  Top 5 Semantic Outliers (lowest avg similarity):")
    for memory, score in outlier_scores[:5]:
        title = memory.data.get("title", "Untitled")
        theme = memory.data.get("theme", "unknown")
        print(f"    [{score:.3f}] \"{title}\"")
        print(f"           Theme: {theme}, Mood: {memory.data.get('mood', 'unknown')}")


def demo_graph_vector_composition(db):
    """
    Demo 5: Graph + Vector Search Composition
    
    Combine RushDB's graph traversal with vector search for richer queries.
    This demonstrates the power of RushDB's dual-layer architecture.
    """
    print("\n" + "="*60)
    print("5. GRAPH + VECTOR SEARCH COMPOSITION")
    print("="*60)
    
    # Get memories with relationships
    connected = db.records.find({
        "labels": ["MEMORY"],
        "where": {
            "MEMORY": {"$relation": {"type": "CONNECTED_TO", "direction": "out"}}
        },
        "limit": 10
    })
    
    if not connected.data:
        print("\nNo connected memories found. Run seed.py to create relationships.")
        return
    
    print("\n--- Query: Memories semantically related to travel that are also connected ---")
    
    # First, find travel-related memories via vector search
    travel_results = db.ai.search({
        "propertyName": "content",
        "query": "travel vacation adventure exploration",
        "labels": ["MEMORY"],
        "limit": 10
    })
    
    travel_ids = {m.id for m in travel_results.data}
    print(f"\n  Found {len(travel_ids)} travel-related memories via vector search")
    
    # Then, filter by those with CONNECTED_TO relationships
    print("\n  Travel memories with connections:")
    for memory in travel_results.data[:5]:
        title = memory.data.get("title", "Untitled")
        
        # Check if this memory has CONNECTED_TO relationships
        related = db.records.find({
            "labels": ["MEMORY"],
            "where": {
                "MEMORY": {
                    "$relation": {"type": "CONNECTED_TO", "direction": "out"},
                    "$id": memory.id
                }
            },
            "limit": 3
        })
        
        if related.data:
            print(f"\n  \"{title}\"")
            print(f"    Connected to:")
            for rel in related.data[:3]:
                rel_title = rel.data.get("title", "Untitled")
                print(f"      → \"{rel_title}\"")
    
    # Demo: Find chains of semantically connected memories
    print("\n--- Query: Semantic chains (memories connected to memories similar to X) ---")
    
    # Start with a theme centroid
    start_results = db.ai.search({
        "propertyName": "content",
        "query": "family home gathering",
        "labels": ["MEMORY"],
        "limit": 1
    })
    
    if start_results.data:
        start = start_results.data[0]
        start_title = start.data.get("title", "Untitled")
        print(f"\n  Starting memory: \"{start_title}\"")
        
        # Find directly connected memories
        connected_to_start = db.records.find({
            "labels": ["MEMORY"],
            "where": {
                "MEMORY": {
                    "$relation": {"type": "CONNECTED_TO", "direction": "out"},
                    "$id": start.id
                }
            },
            "limit": 5
        })
        
        if connected_to_start.data:
            print(f"  Directly connected ({len(connected_to_start.data)} memories):")
            for mem in connected_to_start.data[:3]:
                mem_title = mem.data.get("title", "Untitled")
                print(f"    → \"{mem_title}\"")
                
                # Find memories connected to this one (2nd degree)
                second_degree = db.records.find({
                    "labels": ["MEMORY"],
                    "where": {
                        "MEMORY": {
                            "$relation": {"type": "CONNECTED_TO", "direction": "out"},
                            "$id": mem.id
                        }
                    },
                    "limit": 2
                })
                
                for sd in second_degree.data[:2]:
                    sd_title = sd.data.get("title", "Untitled")
                    print(f"      → → \"{sd_title}\"")


def demo_tag_based_clustering(db):
    """
    Demo 6: Tag-Based Clustering with Vector Refinement
    
    Use graph properties (tags) to create initial clusters,
    then use vector search to find the best representative.
    """
    print("\n" + "="*60)
    print("6. TAG-BASED CLUSTERING WITH VECTOR REFINEMENT")
    print("="*60)
    
    # Get all unique tags
    all_memories = db.records.find({"labels": ["MEMORY"], "limit": 100})
    
    tag_clusters = defaultdict(list)
    for memory in all_memories.data:
        tags = memory.data.get("tags", [])
        for tag in tags:
            tag_clusters[tag].append(memory)
    
    print("\n  Tag Clusters (with vector-selected centroids):")
    
    for tag in sorted(tag_clusters.keys())[:8]:
        memories = tag_clusters[tag]
        if len(memories) < 2:
            continue
        
        # Find the most representative memory for this tag
        centroid = db.ai.search({
            "propertyName": "content",
            "query": f"{tag} experience memory",
            "labels": ["MEMORY"],
            "limit": 1
        })
        
        centroid_title = centroid.data[0].data.get("title", "Unknown") if centroid.data else "N/A"
        
        print(f"\n  Tag: #{tag} ({len(memories)} memories)")
        print(f"    Centroid: \"{centroid_title}\"")
        print(f"    Sample memories:")
        
        for mem in memories[:3]:
            title = mem.data.get("title", "Untitled")
            print(f"      • \"{title}\"")


def demo_index_stats(db, index_id):
    """Display vector index statistics."""
    print("\n" + "="*60)
    print("VECTOR INDEX STATUS")
    print("="*60)
    
    stats = db.ai.indexes.stats(index_id)
    stats_data = stats.data
    
    total = stats_data.get('totalRecords', 0)
    indexed = stats_data.get('indexedRecords', 0)
    coverage = (indexed / total * 100) if total > 0 else 0
    
    print(f"\n  Total records: {total}")
    print(f"  Indexed records: {indexed}")
    print(f"  Coverage: {coverage:.1f}%")


def main():
    """Run the semantic clustering demonstration."""
    print("\n" + "="*60)
    print("SEMANTIC CLUSTERING: GROUPING RELATED MEMORIES")
    print("="*60)
    print("\nThis demo shows how to use RushDB for semantic memory clustering.")
    print("Concepts: vector search, neighborhoods, clusters, outliers, graph+vector composition.")
    
    try:
        db = setup_db()
        print("✓ Connected to RushDB")
        
        # Ensure vector index exists
        index_id = ensure_vector_index(db)
        
        # Run all demonstrations
        demo_index_stats(db, index_id)
        demo_semantic_search(db)
        demo_memory_neighborhoods(db)
        demo_cluster_analysis(db)
        demo_outlier_detection(db)
        demo_graph_vector_composition(db)
        demo_tag_based_clustering(db)
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("\nKey Takeaways:")
        print("  • Vector search finds semantically similar memories")
        print("  • Neighborhoods reveal local clusters of related memories")
        print("  • Cluster analysis groups memories by theme/topic")
        print("  • Outlier detection finds unique, isolated memories")
        print("  • Graph + vector composition enables rich, multi-dimensional queries")
        print("\nLearn more: https://docs.rushdb.com")
        
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("Please ensure you have:")
        print("  1. Created a .env file with your RUSHDB_API_KEY")
        print("  2. Run 'python seed.py' to populate memories")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
