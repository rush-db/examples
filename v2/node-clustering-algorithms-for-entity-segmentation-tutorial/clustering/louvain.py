"""
Louvain Algorithm for Community Detection

The Louvain method is a greedy optimization algorithm that maximizes
modularity to find community structure in networks.

Algorithm phases:
1. Modularity Optimization: Move nodes between communities to maximize ΔQ
2. Community Aggregation: Build new network where nodes = communities
3. Repeat until convergence

Key features:
- Produces hierarchical community structure
- Unsupervised (no need to specify number of communities)
- Good balance between quality and speed
- O(V log V) typical complexity

Modularity formula:
Q = (1/2m) * Σ_ij [A_ij - k_i * k_j / 2m] * δ(c_i, c_j)

where:
- A_ij = edge weight between i and j
- k_i = sum of weights of edges incident to i
- m = total sum of edge weights
- c_i = community of node i
- δ(c_i, c_j) = 1 if i and j are in same community
"""

import random
from collections import defaultdict
from typing import Dict, Tuple

from .utils import Graph, compute_modularity



def louvain_community_detection(
    graph: Graph,
    seed: int = 42,
    resolution: float = 1.0
) -> Tuple[Dict[str, int], float]:
    """
    Detect communities using the Louvain algorithm.
    
    Args:
        graph: The input graph.
        seed: Random seed for reproducibility.
        resolution: Resolution parameter (higher = more smaller communities).
    
    Returns:
        Tuple of (node-to-community mapping, final modularity score).
    """
    random.seed(seed)
    
    if not graph.nodes:
        return {}, 0.0
    
    nodes = list(graph.nodes)
    total_weight = graph.edge_count * 2
    
    community_of = {node: i for i, node in enumerate(nodes)}
    community_members = defaultdict(set)
    for node in nodes:
        community_members[community_of[node]].add(node)
    
    community_weight = defaultdict(int)
    for node in nodes:
        community_weight[community_of[node]] += len(graph.get_neighbors(node))
    
    def compute_modularity_change(
        node: str,
        current_comm: int,
        target_comm: int
    ) -> float:
        """
        Compute ΔQ for moving node from current_comm to target_comm.
        
        Simplified modularity gain formula.
        """
        if current_comm == target_comm:
            return 0.0
        
        m = total_weight / 2.0
        if m == 0:
            return 0.0
        
        neighbors = graph.get_neighbors(node)
        ki = len(neighbors)
        
        current_neighbors = sum(1 for n in neighbors 
                                if community_of[n] == current_comm)
        target_neighbors = sum(1 for n in neighbors 
                               if community_of[n] == target_comm)
        
        sigma_in = target_neighbors
        sigma_tot = community_weight[target_comm]
        
        delta_q = (sigma_in / m) - (resolution * ki * sigma_tot) / (2 * m * m)
        
        return delta_q
    
    def optimize_phase() -> bool:
        """Run one optimization phase. Returns True if any node moved."""
        changed = False
        nodes_shuffled = list(nodes)
        random.shuffle(nodes_shuffled)
        
        for node in nodes_shuffled:
            current_comm = community_of[node]
            neighbors = graph.get_neighbors(node)
            
            if not neighbors:
                continue
            
            neighbor_communities = set(community_of[n] for n in neighbors)
            
            best_comm = current_comm
            best_delta = 0.0
            
            for comm in neighbor_communities:
                delta = compute_modularity_change(node, current_comm, comm)
                if delta > best_delta:
                    best_delta = delta
                    best_comm = comm
            
            if best_comm != current_comm:
                community_members[current_comm].discard(node)
                community_members[best_comm].add(node)
                community_of[node] = best_comm
                changed = True
        
        for comm in list(community_members.keys()):
            if not community_members[comm]:
                del community_members[comm]
        
        return changed
    
    for iteration in range(10):
        if not optimize_phase():
            break
    
    final_partition = community_of.copy()
    final_modularity = compute_modularity(graph, final_partition)
    
    return final_partition, final_modularity



def build_dendrogram(graph: Graph, seed: int = 42) -> list:
    """
    Build hierarchical community structure (dendrogram).
    
    Each level in the dendrogram represents a different granularity
    of community structure, from individual nodes to single community.
    
    Args:
        graph: The input graph.
        seed: Random seed.
    
    Returns:
        List of partitions at each level.
    """
    partition, _ = louvain_community_detection(graph, seed=seed)
    return [partition]


def get_inter_community_edges(
    graph: Graph,
    partition: Dict[str, int]
) -> list:
    """
    Find edges that connect different communities.
    
    Args:
        graph: The input graph.
        partition: Node-to-community mapping.
    
    Returns:
        List of tuples (node_a, node_b) for inter-community edges.
    """
    inter_edges = []
    
    for node in graph.nodes:
        for neighbor in graph.get_neighbors(node):
            if partition.get(node) != partition.get(neighbor):
                edge = (min(node, neighbor), max(node, neighbor))
                if edge not in inter_edges:
                    inter_edges.append(edge)
    
    return inter_edges


def get_intra_community_edges(
    graph: Graph,
    partition: Dict[str, int]
) -> Dict[int, int]:
    """
    Count edges within each community.
    
    Args:
        graph: The input graph.
        partition: Node-to-community mapping.
    
    Returns:
        Dictionary mapping community IDs to internal edge counts.
    """
    intra_edges = defaultdict(int)
    counted = set()
    
    for node in graph.nodes:
        node_comm = partition[node]
        for neighbor in graph.get_neighbors(node):
            edge = (min(node, neighbor), max(node, neighbor))
            if edge in counted:
                continue
            if partition.get(neighbor) == node_comm:
                intra_edges[node_comm] += 1
                counted.add(edge)
    
    return dict(intra_edges)


def compute_community_metrics(
    graph: Graph,
    partition: Dict[str, int]
) -> dict:
    """
    Compute comprehensive metrics for community structure.
    
    Args:
        graph: The input graph.
        partition: Node-to-community mapping.
    
    Returns:
        Dictionary with various community metrics.
    """
    modularity = compute_modularity(graph, partition)
    
    communities = defaultdict(list)
    for node, comm in partition.items():
        communities[comm].append(node)
    
    sizes = [len(members) for members in communities.values()]
    
    inter_edges = get_inter_community_edges(graph, partition)
    intra_edges = get_intra_community_edges(graph, partition)
    
    return {
        "num_communities": len(communities),
        "modularity": modularity,
        "largest_community": max(sizes),
        "smallest_community": min(sizes),
        "average_size": sum(sizes) / len(sizes),
        "inter_community_edges": len(inter_edges),
        "total_edges": graph.edge_count,
        "coverage": len(inter_edges) / graph.edge_count if graph.edge_count else 0
    }
