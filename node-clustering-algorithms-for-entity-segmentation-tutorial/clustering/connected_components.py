"""
Connected Components Algorithm

Finds all connected components in an undirected graph. A connected component
is a maximal set of nodes where every pair of nodes is connected by a path.


This algorithm is fundamental for entity segmentation as it identifies:
- Isolated entity groups that should be treated together
- Orphan records with no connections
- Data silos that may need integration

Time Complexity: O(V + E) using BFS/DFS
Space Complexity: O(V) for visited tracking
"""


from typing import List
from collections import deque

from .utils import Graph


def find_connected_components(graph: Graph) -> List[List[str]]:
    """
    Find all connected components in an undirected graph.
    
    Uses BFS to explore the graph and identify all nodes that belong
    to the same connected component.
    
    Args:
        graph: The input graph.
    
    Returns:
        List of connected components, where each component is a list of node IDs.
    """
    if not graph.nodes:
        return []
    
    visited = set()
    components = []
    
    def bfs(start_node: str) -> List[str]:
        """Breadth-first search to find all nodes in a component."""
        component = []
        queue = deque([start_node])
        visited.add(start_node)
        
        while queue:
            node = queue.popleft()
            component.append(node)
            
            for neighbor in graph.get_neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return component
    
    for node in graph.nodes:
        if node not in visited:
            component = bfs(node)
            components.append(component)
    
    components.sort(key=len, reverse=True)
    
    return components


def filter_singleton_components(components: List[List[str]]) -> List[List[str]]:
    """
    Filter out singleton components (isolated nodes with no edges).
    
    Args:
        components: List of connected components.
    
    Returns:
        List of non-singleton components.
    """
    return [c for c in components if len(c) > 1]



def get_component_statistics(components: List[List[str]]) -> dict:
    """
    Compute statistics about connected components.
    
    Args:
        components: List of connected components.
    
    Returns:
        Dictionary with component statistics.
    """
    if not components:
        return {
            "total_components": 0,
            "total_nodes": 0,
            "largest_size": 0,
            "smallest_size": 0,
            "singleton_count": 0,
            "average_size": 0.0
        }
    
    sizes = [len(c) for c in components]
    
    return {
        "total_components": len(components),
        "total_nodes": sum(sizes),
        "largest_size": max(sizes),
        "smallest_size": min(sizes),
        "singleton_count": sum(1 for s in sizes if s == 1),
        "average_size": sum(sizes) / len(sizes),
        "component_sizes": sorted(sizes, reverse=True)
    }


def find_bridges(graph: Graph) -> List[tuple]:
    """
    Find all bridge edges in the graph.
    
    A bridge is an edge whose removal disconnects the graph.
    These are critical connections in the entity network.
    
    Uses Tarjan's algorithm for O(V + E) complexity.
    
    Args:
        graph: The input graph.
    
    Returns:
        List of bridge edges as tuples (node_a, node_b).
    """
    if not graph.nodes:
        return []
    
    discovery_time = {}
    low = {}
    parent = {}
    bridges = []
    time = [0]
    
    def dfs_bridge(node: str):
        discovery_time[node] = low[node] = time[0]
        time[0] += 1
        
        for neighbor in graph.get_neighbors(node):
            if neighbor not in discovery_time:
                parent[neighbor] = node
                dfs_bridge(neighbor)
                
                low[node] = min(low[node], low[neighbor])
                
                if low[neighbor] > discovery_time[node]:
                    bridges.append((min(node, neighbor), max(node, neighbor)))
            elif neighbor != parent.get(node):
                low[node] = min(low[node], discovery_time[neighbor])
    
    for node in graph.nodes:
        if node not in discovery_time:
            parent[node] = None
            dfs_bridge(node)
    
    return bridges
