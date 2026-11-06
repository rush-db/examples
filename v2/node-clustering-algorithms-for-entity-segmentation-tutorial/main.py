#!/usr/bin/env python3
"""
Node Clustering Algorithms for Entity Segmentation in Large Graphs

This tutorial demonstrates three clustering algorithms implemented on RushDB graph data:
1. Connected Components - Find isolated entity groups
2. Label Propagation - Community detection via iterative label spreading
3. Louvain Partitioning - Modularity-optimized community structure
"""

import os
from collections import defaultdict
from dotenv import load_dotenv

from rushdb import RushDB

from clustering.utils import GraphBuilder
from clustering.connected_components import find_connected_components
from clustering.label_propagation import label_propagation_communities
from clustering.louvain import louvain_community_detection

load_dotenv()


def main():
    print("=" * 60)
    print("  Node Clustering Algorithms for Entity Segmentation")
    print("=" * 60)
    print()
    
    db = RushDB(os.getenv("RUSHDB_API_KEY"))
    
    print("[Step 0] Building graph from RushDB...")
    graph_builder = GraphBuilder(db)
    graph = graph_builder.build_graph()
    
    print(f"  ✓ Loaded {graph.node_count} nodes and {graph.edge_count} edges")
    print()
    
    print("-" * 60)
    print("[1] Connected Components Analysis")
    print("-" * 60)
    components = find_connected_components(graph)
    
    print(f"  Found {len(components)} connected components")
    
    component_sizes = [len(c) for c in components]
    component_sizes.sort(reverse=True)
    
    print(f"  Largest component: {component_sizes[0]} nodes")
    print(f"  Smallest component: {component_sizes[-1]} nodes")
    print(f"  Isolated nodes (no edges): {sum(1 for s in component_sizes if s == 1)}")
    
    singleton_clusters = [c for c in components if len(c) == 1]
    if singleton_clusters:
        print(f"  Singleton clusters: {len(singleton_clusters)} isolated nodes")
    print()
    
    print("-" * 60)
    print("[2] Label Propagation Communities")
    print("-" * 60)
    communities, iterations = label_propagation_communities(graph, max_iterations=50)
    
    print(f"  Converged after {iterations} iterations")
    print(f"  Detected {len(communities)} communities")
    
    community_sizes = sorted([len(c) for c in communities.values()], reverse=True)
    print(f"  Largest community: {community_sizes[0]} members")
    print(f"  Average community size: {sum(community_sizes) / len(community_sizes):.1f}")
    
    label_counts = defaultdict(int)
    for node, label in communities.items():
        label_counts[label] += 1
    
    top_labels = sorted(label_counts.items(), key=lambda x: -x[1])[:3]
    print(f"  Top 3 largest communities by label:")
    for label, count in top_labels:
        print(f"    - Community {label}: {count} members")
    print()
    
    print("-" * 60)
    print("[3] Louvain Partitioning")
    print("-" * 60)
    partition, modularity = louvain_community_detection(graph)
    
    print(f"  Modularity score: {modularity:.3f}")
    
    partition_sizes = defaultdict(int)
    for node, community in partition.items():
        partition_sizes[community] += 1
    
    num_communities = len(set(partition.values()))
    print(f"  Number of communities: {num_communities}")
    
    sizes = sorted(partition_sizes.values(), reverse=True)
    print(f"  Largest partition: {sizes[0]} members")
    print(f"  Partition size distribution: {sizes[:5]}...")
    print()
    
    print("-" * 60)
    print("[4] Entity Segmentation Summary")
    print("-" * 60)
    
    print(f"  Total entities analyzed: {graph.node_count}")
    print(f"  Total edges: {graph.edge_count}")
    print()
    
    print("  Clustering Results Comparison:")
    print(f"  {'Algorithm':<25} {'Communities':<15} {'Largest':<10}")
    print(f"  {'-'*50}")
    print(f"  {'Connected Components':<25} {len(components):<15} {max(component_sizes):<10}")
    print(f"  {'Label Propagation':<25} {len(communities):<15} {community_sizes[0]:<10}")
    print(f"  {'Louvain':<25} {num_communities:<15} {sizes[0]:<10}")
    print()
    
    print("  Sample Cluster Membership (Louvain):")
    sample_communities = list(set(partition.values()))[:3]
    for comm_id in sample_communities:
        members = [n for n, c in partition.items() if c == comm_id][:5]
        print(f"    Community {comm_id}: {members}")
    
    print()
    print("=" * 60)
    print("  Clustering analysis complete.")
    print("=" * 60)
    
    del db


if __name__ == "__main__":
    main()
