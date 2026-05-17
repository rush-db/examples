"""
Label Propagation Algorithm for Community Detection

Semi-supervised learning algorithm for detecting communities in graphs.
Each node starts with a unique label and iteratively updates its label
based on the majority label among its neighbors.

Key properties:
- No need to pre-specify number of communities
- Linear time complexity O(V + E) per iteration
- May not converge in some graphs (uses random tie-breaking)
- Produces different results on different runs

This implementation includes:
- Asynchronous label updates for stability
- Convergence detection
- Tie-breaking with random selection
- Maximum iteration limit for termination
"""

import random
from typing import Dict, Tuple
from collections import Counter

from .utils import Graph


def label_propagation_communities(
    graph: Graph,
    max_iterations: int = 50,
    seed: int = 42
) -> Tuple[Dict[str, int], int]:
    """
    Detect communities using label propagation algorithm.
    
    Args:
        graph: The input graph.
        max_iterations: Maximum number of iterations before stopping.
        seed: Random seed for reproducible results.
    
    Returns:
        Tuple of (node-to-community mapping, iteration count).
    """
    random.seed(seed)
    
    if not graph.nodes:
        return {}, 0
    
    labels = {node: i for i, node in enumerate(graph.nodes)}
    
    def get_label_score(node: str, target_label: int) -> Tuple[int, float]:
        """
        Calculate a score for the label based on weighted neighbors.
        Returns (count, random_bonus) tuple for comparison.
        """
        count = sum(1 for neighbor in graph.get_neighbors(node) 
                   if labels[neighbor] == target_label)
        return (count, random.random())
    
    def update_labels() -> bool:
        """Update all labels synchronously. Returns True if any changes occurred."""
        new_labels = labels.copy()
        changed = False
        
        nodes = list(graph.nodes)
        random.shuffle(nodes)
        
        for node in nodes:
            neighbors = graph.get_neighbors(node)
            if not neighbors:
                continue
            
            neighbor_labels = [labels[n] for n in neighbors]
            label_counts = Counter(neighbor_labels)
            
            max_count = label_counts.most_common(1)[0][1]
            candidates = [label for label, count in label_counts.items() 
                        if count == max_count]
            
            new_label = random.choice(candidates)
            if new_label != labels[node]:
                new_labels[node] = new_label
                changed = True
        
        labels.update(new_labels)
        return changed
    
    iterations = 0
    for i in range(max_iterations):
        iterations = i + 1
        if not update_labels():
            break
    
    return dict(labels), iterations


def synchronous_label_propagation(
    graph: Graph,
    max_iterations: int = 50,
    seed: int = 42
) -> Dict[str, int]:
    """
    Synchronous label propagation (all nodes update simultaneously).
    
    May produce oscillating behavior in bipartite-like graphs.
    
    Args:
        graph: The input graph.
        max_iterations: Maximum iterations.
        seed: Random seed.
    
    Returns:
        Dictionary mapping nodes to community IDs.
    """
    random.seed(seed)
    
    if not graph.nodes:
        return {}
    
    labels = {node: i for i, node in enumerate(graph.nodes)}
    
    for _ in range(max_iterations):
        new_labels = {}
        
        for node in graph.nodes:
            neighbors = graph.get_neighbors(node)
            if not neighbors:
                new_labels[node] = labels[node]
                continue
            
            neighbor_labels = [labels[n] for n in neighbors]
            label_counts = Counter(neighbor_labels)
            max_count = label_counts.most_common(1)[0][1]
            candidates = [label for label, count in label_counts.items() 
                        if count == max_count]
            new_labels[node] = random.choice(candidates)
        
        labels = new_labels
    
    return labels


def get_community_members(communities: Dict[str, int], community_id: int) -> list:
    """
    Get all members of a specific community.
    
    Args:
        communities: Node-to-community mapping.
        community_id: The community ID to query.
    
    Returns:
        List of node IDs in the community.
    """
    return [node for node, cid in communities.items() if cid == community_id]



def get_community_size_distribution(communities: Dict[str, int]) -> Dict[int, int]:
    """
    Get the distribution of community sizes.
    
    Args:
        communities: Node-to-community mapping.
    
    Returns:
        Dictionary mapping community IDs to sizes.
    """
    size_distribution = {}
    for node, community in communities.items():
        size_distribution[community] = size_distribution.get(community, 0) + 1
    return size_distribution


def merge_small_communities(
    communities: Dict[str, int],
    min_size: int = 3
) -> Dict[str, int]:
    """
    Merge communities smaller than min_size into the nearest larger community.
    
    Args:
        communities: Node-to-community mapping.
        min_size: Minimum community size threshold.
    
    Returns:
        Updated communities mapping.
    """
    size_dist = get_community_size_distribution(communities)
    small_communities = {cid for cid, size in size_dist.items() if size < min_size}
    large_communities = {cid for cid, size in size_dist.items() if size >= min_size}
    
    if not small_communities:
        return communities
    
    merged = communities.copy()
    
    for node, cid in merged.items():
        if cid in small_communities:
            merged[node] = list(large_communities)[0]
    
    return merged
