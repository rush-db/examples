"""
Graph Serialization Formats for Agent-to-Agent Communication

This tutorial demonstrates how RushDB handles different graph serialization
formats that are commonly used in multi-agent systems for transmitting
graph data between agent processes.

Formats covered:
1. Native JSON (default RushDB record format)
2. Adjacency List format
3. Edge List format
4. Nested JSON import/export
5. Graph traversal serialization
"""

import json
import os
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


def serialize_as_native_json(records: list) -> list:
    """
    Format 1: Native JSON Serialization
    
    Each record is serialized with all system fields (__id, __label)
    and user properties. This is the default format for RushDB responses.
    
    Best for: Full fidelity data exchange, debugging, documentation.
    """
    result = []
    for record in records:
        result.append(record.data)
    return result


def serialize_as_adjacency_list(records: list, relationships: list) -> dict:
    """
    Format 2: Adjacency List Format
    
    For each node, we list its outgoing connections.
    Compact and efficient for transmission between agents.
    
    Structure: { "node_id": { "outgoing": [{"type": "REL_TYPE", "target": "id"}] }}
    
    Best for: Bandwidth-constrained environments, incremental updates.
    """
    adjacency = {}
    
    # Index records by ID
    for record in records:
        adjacency[record.id] = {
            "label": record.label,
            "outgoing": []
        }
    
    # Add relationship info (from stored attach data or implicit)
    # In production, you'd query db.records.find() with relationship traversal
    return adjacency


def serialize_as_edge_list(records: list, labels: list) -> list:
    """
    Format 3: Edge List Format
    
    Simple [source_id, target_id, relationship_type] tuples.
    Useful for graph diffs, synchronization, and simple graph protocols.
    
    Best for: Sync operations, graph comparison, simple protocols.
    """
    edges = []
    
    for label in labels:
        # Find all records of this type
        related = db.records.find({
            "labels": [label],
            "limit": 100
        }).data
        
        for record in related:
            # In a real implementation, you'd traverse relationships
            # Here we show the structure
            edges.append({
                "source_label": label,
                "source_id": record.id,
                "relationship_type": "CONNECTED",
                "direction": "out"
            })
    
    return edges


def export_subgraph_as_json(db: RushDB, root_id: str, max_depth: int = 2) -> dict:
    """
    Format 4: Subgraph Export
    
    Export a connected subgraph starting from a root node.
    Useful for sharing context between agents.
    
    Structure:
    {
        "root": {...record...},
        "nodes": [...],
        "edges": [...]
    }
    
    Best for: Context sharing, snapshotting agent state.
    """
    root = db.records.find_by_id(root_id)
    if not root:
        return {"error": "Root record not found"}
    
    nodes = [root]
    edges = []
    
    current_frontier = [root]
    visited = {root.id}
    
    for depth in range(max_depth):
        next_frontier = []
        
        for node in current_frontier:
            # Find connected records via labels
            # In production, use proper relationship traversal
            for label in ["AGENT", "MESSAGE", "INTENT", "ARTIFACT"]:
                connected = db.records.find({
                    "labels": [label],
                    "limit": 5
                }).data
                
                for conn in connected:
                    if conn.id not in visited:
                        nodes.append(conn)
                        visited.add(conn.id)
                        next_frontier.append(conn)
                        
                        edges.append({
                            "from": node.id,
                            "to": conn.id,
                            "type": "RELATED"
                        })
        
        current_frontier = next_frontier
    
    return {
        "root_id": root.id,
        "root_label": root.label,
        "depth": max_depth,
        "nodes": [{"id": n.id, "label": n.label, "data": n.fields} for n in nodes],
        "edges": edges,
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    }


def import_nested_json_structure(db: RushDB) -> dict:
    """
    Format 5: Nested JSON Import
    
    RushDB's import_json can ingest hierarchical JSON and automatically
    create linked records and relationships.
    
    This demonstrates the reverse: creating nested structure to import.
    """
    nested_data = {
        "AGENT_SESSION": {
            "session_id": "sess_abc123",
            "started_at": "2024-01-15T10:30:00Z",
            "agent_name": "Orchestrator",
            "tasks": [
                {
                    "task_id": "task_001",
                    "description": "Analyze requirements",
                    "status": "completed",
                    "subtasks": [
                        {"subtask_id": "st_001", "description": "Review docs"},
                        {"subtask_id": "st_002", "description": "Query stakeholders"}
                    ]
                },
                {
                    "task_id": "task_002",
                    "description": "Generate architecture",
                    "status": "in_progress",
                    "subtasks": [
                        {"subtask_id": "st_003", "description": "Design API layer"},
                        {"subtask_id": "st_004", "description": "Plan data model"}
                    ]
                }
            ],
            "messages": [
                {
                    "msg_id": "msg_001",
                    "content": "Starting session",
                    "recipient": "Research"
                },
                {
                    "msg_id": "msg_002",
                    "content": "Requirements ready",
                    "recipient": "Coder"
                }
            ]
        }
    }
    
    # Import the nested structure
    result = db.records.import_json(nested_data)
    
    return {
        "imported": True,
        "structure": nested_data,
        "note": "Nested objects become linked child records via import_json"
    }


def demonstrate_relationship_traversal_serialization(db: RushDB) -> list:
    """
    Format 6: Relationship Traversal Results
    
    Serialize the results of traversing relationships - essential for
    agent communication where one agent needs to understand another's
    context graph.
    
    Best for: Context propagation, workflow state sharing.
    """
    traversal_results = []
    
    # Get all agents
    agents = db.records.find({"labels": ["AGENT"], "limit": 10}).data
    
    for agent in agents:
        # Build a snapshot of each agent's graph
        agent_snapshot = {
            "agent_id": agent.id,
            "agent_name": agent.fields.get("name", "Unknown"),
            "status": agent.fields.get("status", "unknown"),
            "capabilities": agent.fields.get("capabilities", []),
            "connections": {
                "messages_sent": 0,  # Would be queried via relationship
                "intents_generated": 0,
                "artifacts_authored": 0
            }
        }
        
        # Get connected messages
        messages = db.records.find({
            "labels": ["MESSAGE"],
            "limit": 5
        }).data
        
        agent_snapshot["connections"]["sample_messages"] = [
            {
                "id": m.id,
                "type": m.fields.get("type"),
                "subject": m.fields.get("subject")
            }
            for m in messages[:3]
        ]
        
        # Get connected intents
        intents = db.records.find({
            "labels": ["INTENT"],
            "limit": 5
        }).data
        
        agent_snapshot["connections"]["active_intents"] = [
            {
                "id": i.id,
                "type": i.fields.get("type"),
                "confidence": i.fields.get("confidence")
            }
            for i in intents[:3]
        ]
        
        traversal_results.append(agent_snapshot)
    
    return traversal_results


def serialize_graph_summary(db: RushDB) -> dict:
    """
    Create a summary representation of the entire graph.
    Useful for agents to understand the current state without
    fetching all records.
    """
    labels = db.labels.find({})
    
    summary = {
        "graph_name": "agent_communication_graph",
        "statistics": {},
        "labels": []
    }
    
    for label in labels:
        summary["labels"].append({
            "name": label.name,
            "count": label.count
        })
        summary["statistics"][label.name] = {
            "record_count": label.count,
            "percentage": 0  # Will calculate below
        }
    
    total = sum(l.count for l in labels)
    for label_name, stats in summary["statistics"].items():
        if total > 0:
            stats["percentage"] = round(100 * stats["record_count"] / total, 1)
    
    return summary


def main():
    """Main demonstration function."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        return
    
    with RushDB(api_key) as db:
        print("\n" + "=" * 60)
        print(" RUSHDB GRAPH SERIALIZATION FOR AGENT COMMUNICATION")
        print("=" * 60)
        
        # ============================================================
        # FORMAT 1: Native JSON Serialization
        # ============================================================
        print_section("FORMAT 1: Native JSON Serialization")
        print("\nRetrieving all AGENT records and serializing to native JSON...")
        
        agents = db.records.find({"labels": ["AGENT"], "limit": 5}).data
        native_json = serialize_as_native_json(agents)
        
        print(f"\nSerialized {len(native_json)} agent records.")
        print("\nSample record (first agent):")
        print(json.dumps(native_json[0] if native_json else {}, indent=2, default=str)[:500] + "...")
        
        # ============================================================
        # FORMAT 2: Adjacency List Format
        # ============================================================
        print_section("FORMAT 2: Adjacency List Format")
        print("\nConverting graph to adjacency list representation...")
        
        all_records = []
        for label in ["AGENT", "MESSAGE", "INTENT", "ARTIFACT"]:
            records = db.records.find({"labels": [label], "limit": 10}).data
            all_records.extend(records)
        
        adjacency = serialize_as_adjacency_list(all_records, [])
        
        # Show sample entries
        sample_keys = list(adjacency.keys())[:3]
        sample_adj = {k: adjacency[k] for k in sample_keys if k in adjacency}
        
        print(f"\nAdjacency list contains {len(adjacency)} nodes.")
        print("\nSample adjacency entries:")
        print(json.dumps(sample_adj, indent=2)[:600] + "...")
        
        # ============================================================
        # FORMAT 3: Edge List Format
        # ============================================================
        print_section("FORMAT 3: Edge List Format")
        print("\nConverting relationships to edge list format...")
        
        edge_list = serialize_as_edge_list(all_records, ["AGENT", "MESSAGE"])
        
        print(f"\nGenerated {len(edge_list)} edge entries.")
        print("\nSample edges:")
        print(json.dumps(edge_list[:5], indent=2, default=str))
        
        # ============================================================
        # FORMAT 4: Subgraph Export
        # ============================================================
        print_section("FORMAT 4: Subgraph Export")
        print("\nExporting a subgraph starting from first agent...")
        
        if agents:
            root_id = agents[0].id
            subgraph = export_subgraph_as_json(db, root_id, max_depth=2)
            
            print(f"\nSubgraph export complete:")
            print(f"  - Root: {subgraph.get('root_id', 'N/A')}")
            print(f"  - Nodes: {subgraph.get('metadata', {}).get('node_count', 0)}")
            print(f"  - Edges: {subgraph.get('metadata', {}).get('edge_count', 0)}")
            print("\nSubgraph structure preview:")
            print(json.dumps(subgraph, indent=2, default=str)[:700] + "...")
        else:
            print("No agents found to export subgraph from.")
        
        # ============================================================
        # FORMAT 5: Nested JSON Import
        # ============================================================
        print_section("FORMAT 5: Nested JSON Import")
        print("\nDemonstrating nested JSON import structure...")
        
        nested_structure = import_nested_json_structure(db)
        
        print("\nNested structure for import:")
        print(json.dumps(nested_structure["structure"], indent=2)[:800])
        print(f"\nImport status: {nested_structure['note']}")
        
        # ============================================================
        # FORMAT 6: Relationship Traversal Serialization
        # ============================================================
        print_section("FORMAT 6: Relationship Traversal Results")
        print("\nSerializing relationship traversal results for agent context...")
        
        traversal_results = demonstrate_relationship_traversal_serialization(db)
        
        print(f"\nGenerated snapshots for {len(traversal_results)} agents.")
        print("\nSample agent snapshot:")
        print(json.dumps(traversal_results[0] if traversal_results else {}, indent=2, default=str))
        
        # ============================================================
        # FORMAT 7: Graph Summary
        # ============================================================
        print_section("FORMAT 7: Graph Summary (for agent state awareness)")
        print("\nGenerating graph summary...")
        
        summary = serialize_graph_summary(db)
        
        print(f"\nGraph: {summary['graph_name']}")
        print(f"Total records: {sum(s['record_count'] for s in summary['statistics'].values())}")
        print("\nLabel distribution:")
        for label_info in summary["labels"]:
            pct = summary["statistics"][label_info["name"]]["percentage"]
            print(f"  - {label_info['name']}: {label_info['count']} records ({pct}%)")
        
        # ============================================================
        # Summary
        # ============================================================
        print_section("SUMMARY: Serialization Formats Comparison")
        print("""
| Format              | Best For                          | Size  | Fidelity |
|---------------------|-----------------------------------|-------|----------|
| Native JSON         | Full data exchange, debugging      | Large | Complete |
| Adjacency List      | Incremental updates, traversal     | Medium| High     |
| Edge List           | Sync, comparison, simple protocols | Small | Medium   |
| Subgraph Export     | Context sharing, state snapshots   | Medium| High     |
| Nested Import       | Hierarchical data ingestion        | Varies| High     |
| Traversal Results   | Context propagation, workflow state| Medium| High     |
| Graph Summary       | State awareness, planning          | Small | Low      |

Choose the format based on your agent communication requirements:
- High bandwidth: Use Native JSON or Subgraph Export
- Low bandwidth: Use Edge List or Graph Summary
- Context transfer: Use Traversal Results or Subgraph Export
- Data ingestion: Use Nested JSON import
""")


if __name__ == "__main__":
    main()
