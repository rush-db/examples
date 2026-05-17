"""
Graph construction utilities for RushDB entity data.
"""


from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from rushdb import RushDB


@dataclass
class Graph:
    """Simple graph data structure for clustering algorithms."""
    
    nodes: set = field(default_factory=set)
    neighbors: dict = field(default_factory=lambda: defaultdict(set))
    edges: set = field(default_factory=set)
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        return len(self.edges)
    
    def add_node(self, node_id: str) -> None:
        self.nodes.add(node_id)
    
    def add_edge(self, source: str, target: str) -> None:
        self.nodes.add(source)
        self.nodes.add(target)
        self.neighbors[source].add(target)
        self.neighbors[target].add(source)
        self.edges.add((min(source, target), max(source, target)))
    
    def get_neighbors(self, node_id: str) -> set:
        return self.neighbors.get(node_id, set())


class GraphBuilder:
    """
    Builds an in-memory graph from RushDB entity relationships.
    
    This class queries RushDB for records and their relationships,
    then constructs a simple adjacency-list graph for clustering algorithms.
    """
    
    ENTITY_LABELS = ["EMPLOYEE", "TEAM", "PROJECT", "SKILL"]
    RELATIONSHIP_TYPES = ["MEMBER_OF", "WORKS_ON", "HAS_SKILL"]
    
    def __init__(self, db: RushDB):
        self.db = db
        self._node_id_map: dict[str, str] = {}
    
    def _get_node_id(self, record) -> str:
        """Generate a stable node ID from a record."""
        record_id = record.id
        if record_id not in self._node_id_map:
            self._node_id_map[record_id] = f"node_{len(self._node_id_map)}"
        return self._node_id_map[record_id]
    
    def _load_all_records(self) -> dict:
        """Load all entity records from RushDB."""
        records = {}
        
        for label in self.ENTITY_LABELS:
            try:
                result = self.db.records.find({
                    "labels": [label],
                    "limit": 500
                })
                records[label] = result.data if hasattr(result, 'data') else []
            except Exception:
                records[label] = []
        
        return records
    
    def _load_relationships(self) -> list[tuple]:
        """Load relationships from RushDB using raw query."""
        relationships = []
        
        try:
            result = self.db.query.raw(
                """
                MATCH (a)-[r]->(b)
                WHERE type(r) IN ['MEMBER_OF', 'WORKS_ON', 'HAS_SKILL']
                RETURN a.__id AS source_id, b.__id AS target_id, type(r) AS rel_type
                LIMIT 500
                """
            )
            
            if hasattr(result, 'data') and result.data:
                for record in result.data:
                    if record.get('source_id') and record.get('target_id'):
                        relationships.append((
                            record['source_id'],
                            record['target_id'],
                            record.get('rel_type', 'RELATED')
                        ))
        except Exception as e:
            print(f"  Warning: Could not load relationships via raw query: {e}")
            relationships = self._load_relationships_fallback()
        
        return relationships
    
    def _load_relationships_fallback(self) -> list[tuple]:
        """Fallback method to load relationships by querying entity pairs."""
        relationships = []
        
        for label in self.ENTITY_LABELS:
            try:
                records = self.db.records.find({"labels": [label], "limit": 200})
                data = records.data if hasattr(records, 'data') else []
                
                for record in data:
                    record_id = self._get_node_id(record)
                    
                    for rel_type in self.RELATIONSHIP_TYPES:
                        related = self.db.records.find({
                            "labels": self.ENTITY_LABELS,
                            "where": {
                                label: {
                                    "$relation": {
                                        "type": rel_type,
                                        "direction": "in"
                                    }
                                }
                            },
                            "limit": 50
                        })
                        
                        if hasattr(related, 'data'):
                            for rel_record in related.data:
                                rel_id = self._get_node_id(rel_record)
                                relationships.append((rel_id, record_id, rel_type))
            except Exception:
                pass
        
        return relationships
    
    def build_graph(self) -> Graph:
        """
        Build an in-memory graph from RushDB entity data.
        
        Returns:
            Graph: A Graph object containing nodes and edges.
        """
        graph = Graph()
        
        records = self._load_all_records()
        
        for label, record_list in records.items():
            for record in record_list:
                node_id = self._get_node_id(record)
                graph.add_node(node_id)
        
        relationships = self._load_relationships()
        
        for source_id, target_id, rel_type in relationships:
            source_node = self._node_id_map.get(source_id)
            target_node = self._node_id_map.get(target_id)
            
            if source_node and target_node:
                graph.add_edge(source_node, target_node)
        
        for node in graph.nodes:
            if not graph.get_neighbors(node):
                pass
        
        return graph


def compute_modularity(graph: Graph, partition: dict) -> float:
    """
    Compute the modularity score for a graph partition.
    
    Modularity measures the quality of a community partition, with higher
    values (closer to 1) indicating better community structure.
    
    Args:
        graph: The input graph.
        partition: Dictionary mapping node IDs to community IDs.
    
    Returns:
        float: Modularity score between -0.5 and 1.
    """
    if not graph.nodes:
        return 0.0
    
    m = graph.edge_count
    if m == 0:
        return 0.0
    
    degrees = defaultdict(int)
    for node in graph.nodes:
        degrees[node] = len(graph.get_neighbors(node))
    
    community_nodes = defaultdict(list)
    for node, community in partition.items():
        community_nodes[community].append(node)
    
    modularity_sum = 0.0
    
    for comm_id, nodes in community_nodes.items():
        for i, node_i in enumerate(nodes):
            for node_j in nodes[i + 1:]:
                adj_ij = 1 if node_j in graph.get_neighbors(node_i) else 0
                ki = degrees[node_i]
                kj = degrees[node_j]
                
                modularity_sum += adj_ij - (ki * kj) / (2 * m)
    
    return modularity_sum / m
