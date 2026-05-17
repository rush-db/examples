"""
Graph Seeding Script for Federated Learning Tutorial

Creates a synthetic property graph in RushDB representing distributed
graph data across multiple federated clients. Each client owns a subset
of graph nodes with cross-client edges for realistic topology.

This script is idempotent - run it multiple times safely.
"""

import os
import random
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Configuration
FEDERATED_CLIENTS = {
    "CLIENT_A": {"count": 10, "region": "us-east", "node_features": 16},
    "CLIENT_B": {"count": 12, "region": "us-west", "node_features": 16},
    "CLIENT_C": {"count": 8, "region": "eu-central", "node_features": 16},
    "CLIENT_D": {"count": 15, "region": "ap-south", "node_features": 16},
}

# Labels used in the graph
LABELS = {
    "CLIENT": "CLIENT",
    "GRAPH_NODE": "GRAPH_NODE",
}


def clear_existing_data(db: RushDB) -> None:
    """Remove all records from previous runs."""
    print("[*] Clearing existing graph data...")
    
    for label in ["GRAPH_NODE", "CLIENT"]:
        result = db.records.delete({"labels": [label], "where": {}})
        print(f"    Cleared {result.get('deleted', 0)} {label} records")


def create_federated_clients(db: RushDB) -> dict:
    """Create CLIENT nodes representing federated parties."""
    clients = {}
    
    for client_id, config in FEDERATED_CLIENTS.items():
        print(f"[+] Creating {client_id} ({config['region']})...")
        
        client = db.records.create(
            label=LABELS["CLIENT"],
            data={
                "clientId": client_id,
                "region": config["region"],
                "nodeCount": config["count"],
                "isActive": True,
            }
        )
        clients[client_id] = client
    
    return clients


def create_graph_nodes(
    db: RushDB, 
    clients: dict, 
    client_id: str, 
    config: dict
) -> list:
    """Create GRAPH_NODE records for a federated client."""
    nodes = []
    client = clients[client_id]
    
    for i in range(config["count"]):
        # Generate synthetic node features (embedding-like vectors)
        features = np.random.randn(config["node_features"]).tolist()
        
        # Assign a label (for node classification task)
        label = random.choice(["CLASS_A", "CLASS_B", "CLASS_C", "CLASS_D"])
        
        node = db.records.create(
            label=LABELS["GRAPH_NODE"],
            data={
                "nodeId": f"{client_id}_node_{i}",
                "features": features,
                "label": label,
                "trainingSamples": random.randint(50, 500),
            },
            vectors=[{"propertyName": "features", "vector": features}]
        )
        nodes.append(node)
        
        # Link to owning client
        db.records.attach(
            source=node,
            target=client,
            options={"type": "PART_OF"}
        )
    
    return nodes


def create_cross_client_edges(
    db: RushDB, 
    all_nodes: dict
) -> None:
    """Create edges between nodes of different clients (cross-client topology)."""
    client_ids = list(all_nodes.keys())
    
    # Create some cross-client edges to simulate realistic graph structure
    edge_count = 0
    
    for i, client_a in enumerate(client_ids):
        for client_b in client_ids[i + 1:]:
            # Create 1-3 edges between each pair of clients
            num_edges = random.randint(1, 3)
            
            for _ in range(num_edges):
                node_a = random.choice(all_nodes[client_a])
                node_b = random.choice(all_nodes[client_b])
                
                # Use direction: out from client_a to client_b
                db.records.attach(
                    source=node_a,
                    target=node_b,
                    options={"type": "CONNECTED_TO", "direction": "out"}
                )
                edge_count += 1
    
    print(f"[+] Created {edge_count} cross-client edges")


def verify_graph(db: RushDB, clients: dict) -> dict:
    """Verify the graph structure and return statistics."""
    stats = {"total_nodes": 0, "total_clients": 0, "cross_client_edges": 0}
    
    # Count clients
    result = db.records.find({"labels": [LABELS["CLIENT"]], "where": {}})
    stats["total_clients"] = result.total
    
    # Count graph nodes
    result = db.records.find({"labels": [LABELS["GRAPH_NODE"]], "where": {}})
    stats["total_nodes"] = result.total
    
    # Count cross-client edges
    for client_id in clients:
        edges = db.records.find({
            "labels": [LABELS["GRAPH_NODE"]],
            "where": {
                "CLIENT": {
                    "$relation": {"type": "PART_OF", "direction": "in"},
                    "clientId": client_id
                },
                "CONNECTED_TO": {"$exists": True}
            }
        })
        stats["cross_client_edges"] += edges.total
    
    return stats


def main():
    """Seed the graph with federated learning topology."""
    print("\n" + "=" * 60)
    print("Federated Learning Graph Seeding")
    print("=" * 60 + "\n")
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found in environment. "
            "Copy .env.example to .env and add your API key."
        )
    
    db = RushDB(api_key)
    print(f"[+] Connected to RushDB\n")
    
    # Clear existing data for clean seeding
    clear_existing_data(db)
    print()
    
    # Step 1: Create federated client nodes
    print("[1/4] Creating federated clients...")
    clients = create_federated_clients(db)
    print(f"    Created {len(clients)} clients\n")
    
    # Step 2: Create graph nodes for each client
    print("[2/4] Creating graph nodes...")
    all_nodes = {}
    
    for client_id, config in FEDERATED_CLIENTS.items():
        print(f"    {client_id}: {config['count']} nodes... ", end="", flush=True)
        nodes = create_graph_nodes(db, clients, client_id, config)
        all_nodes[client_id] = nodes
        print("done")
    
    print()
    
    # Step 3: Create cross-client edges
    print("[3/4] Creating cross-client edges...")
    create_cross_client_edges(db, all_nodes)
    print()
    
    # Step 4: Verify graph structure
    print("[4/4] Verifying graph structure...")
    stats = verify_graph(db, clients)
    
    print("\n" + "-" * 40)
    print("Graph Statistics:")
    print(f"  ├─ Federated clients: {stats['total_clients']}")
    print(f"  ├─ Total graph nodes: {stats['total_nodes']}")
    print(f"  └─ Cross-client edges: {stats['cross_client_edges']}")
    print("-" * 40)
    
    print("\n[✓] Graph seeding completed successfully!")
    print("    Run `python main.py` to execute the federated learning simulation.\n")


if __name__ == "__main__":
    main()
