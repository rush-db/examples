"""
Federated Learning Simulation Across Graph-Structured Data

This tutorial demonstrates how to use RushDB as the data layer for
federated learning on graph-structured data. It simulates:

1. Graph Structure Retrieval: Query RushDB to get client topology
2. Local Training: Simulate gradient updates on each federated client
3. Weight Aggregation: FedAvg-style model parameter aggregation
4. Federated Inference: Run predictions using the aggregated model

In production, local training would use PyTorch/TensorFlow with actual
gradient computation. Here we simulate the workflow with synthetic metrics.
"""

import os
import random
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB


@dataclass
class ClientState:
    """Represents the state of a federated client."""
    client_id: str
    region: str
    node_count: int
    nodes: list = field(default_factory=list)
    local_model_weights: Optional[np.ndarray] = None
    local_accuracy: float = 0.0
    training_samples: int = 0


@dataclass
class FederatedRound:
    """Results from a single federated learning round."""
    round_number: int
    clients: list[ClientState]
    aggregated_accuracy: float
    cross_client_edges: int
    aggregation_method: str = "FedAvg"


class FederatedLearningSimulator:
    """
    Simulates federated learning across graph-structured data stored in RushDB.
    
    In a real implementation, local training would use actual ML frameworks
    (PyTorch/TensorFlow) with proper gradient computation. This simulation
    demonstrates the workflow and RushDB integration patterns.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.clients: dict[str, ClientState] = {}
        self.global_model: Optional[np.ndarray] = None
        self.feature_dim: int = 16
        
    def fetch_graph_structure(self) -> None:
        """
        Step 1: Query RushDB to retrieve the federated client topology.
        
        This demonstrates how RushDB's graph traversal works to discover
        the structure of distributed data across federated clients.
        """
        print("[Step 1] Fetching graph structure from RushDB...\n")
        
        # Get all federated clients
        client_records = self.db.records.find({
            "labels": ["CLIENT"],
            "where": {"isActive": True}
        })
        
        print(f"    Discovered {client_records.total} federated clients:")
        
        for client in client_records.data:
            client_id = client["clientId"]
            region = client["region"]
            expected_count = client["nodeCount"]
            
            # Query graph nodes belonging to this client
            # Uses RushDB's relationship traversal in where clause
            node_records = self.db.records.find({
                "labels": ["GRAPH_NODE"],
                "where": {
                    "CLIENT": {
                        "$relation": {"type": "PART_OF", "direction": "in"},
                        "clientId": client_id
                    }
                }
            })
            
            # Calculate total training samples
            total_samples = sum(
                n.get("trainingSamples", 0) 
                for n in node_records.data
            )
            
            state = ClientState(
                client_id=client_id,
                region=region,
                node_count=node_records.total,
                nodes=node_records.data,
                training_samples=total_samples
            )
            self.clients[client_id] = state
            
            print(f"    ├─ {client_id} ({region}): {node_records.total} nodes")
        
        print()
    
    def discover_cross_client_edges(self) -> int:
        """
        Discover edges connecting nodes across different federated clients.
        
        This demonstrates RushDB's ability to traverse relationships and
        find cross-client graph structure, which is important for
        graph neural network (GNN) based federated learning.
        """
        print("[Step 2] Discovering cross-client edges...")
        
        cross_client_count = 0
        
        for client_id, state in self.clients.items():
            # Find nodes that have CONNECTED_TO relationships
            connected_nodes = self.db.records.find({
                "labels": ["GRAPH_NODE"],
                "where": {
                    "CLIENT": {
                        "$relation": {"type": "PART_OF", "direction": "in"},
                        "clientId": client_id
                    },
                    "CONNECTED_TO": {"$exists": True}
                }
            })
            cross_client_count += connected_nodes.total
        
        print(f"    Found {cross_client_count} cross-client edges\n")
        return cross_client_count
    
    def simulate_local_training(self) -> None:
        """
        Step 2: Simulate local training on each federated client.
        
        In production, this would:
        1. Load the global model weights
        2. Fine-tune on local graph nodes
        3. Compute gradients and update weights
        
        Here we simulate the workflow with synthetic accuracy metrics.
        """
        print("[Step 3] Simulating local training on federated clients...\n")
        
        # Initialize global model if not exists
        if self.global_model is None:
            self.global_model = np.random.randn(self.feature_dim)
        
        for client_id, state in self.clients.items():
            # Simulate local training (in reality: gradient descent on local data)
            # The more training samples, the better the local accuracy
            base_accuracy = 0.75 + (state.training_samples / 5000) * 0.15
            noise = np.random.normal(0, 0.02)
            state.local_accuracy = min(0.95, base_accuracy + noise)
            
            # Simulate updated model weights (in reality: computed via backprop)
            # Local update = global model + random gradient (simulated)
            gradient = np.random.randn(self.feature_dim) * 0.01
            state.local_model_weights = self.global_model + gradient
            
            print(f"    {client_id}: {state.node_count} nodes, "
                  f"{state.training_samples} samples, "
                  f"local accuracy: {state.local_accuracy:.3f}")
        
        print()
    
    def aggregate_weights_fedavg(self) -> np.ndarray:
        """
        Step 3: Aggregate local model weights using FedAvg.
        
        FedAvg (Federated Averaging) weights each client's contribution
        by their number of training samples (or nodes).
        
        Formula: global_model = sum(client_weight * client_nodes / total_nodes)
        """
        print("[Step 4] Aggregating model weights (FedAvg)...")
        
        total_nodes = sum(state.node_count for state in self.clients.values())
        aggregated = np.zeros(self.feature_dim)
        
        for state in self.clients.values():
            weight = state.node_count / total_nodes
            aggregated += weight * state.local_model_weights
            print(f"    {state.client_id}: weight={weight:.3f} "
                  f"(nodes={state.node_count})")
        
        self.global_model = aggregated
        print(f"    → Global model updated with {len(self.clients)} clients\n")
        
        return aggregated
    
    def run_federated_inference(self) -> dict:
        """
        Step 4: Run inference using the aggregated global model.
        
        Simulates running predictions on each client's graph data using
        the aggregated model. In production, this would be actual inference.
        """
        print("[Step 5] Running federated inference...\n")
        
        results = {
            "client_accuracies": {},
            "aggregated_accuracy": 0.0,
            "total_nodes": 0
        }
        
        weighted_accuracy_sum = 0.0
        total_weight = 0
        
        for client_id, state in self.clients.items():
            # Simulate inference accuracy (global model performs well across clients)
            # Real GNN-based FL would have this property due to graph structure sharing
            inference_accuracy = state.local_accuracy * 0.98  # Slight drop from local
            
            results["client_accuracies"][client_id] = {
                "accuracy": inference_accuracy,
                "nodes": state.node_count
            }
            
            weight = state.node_count
            weighted_accuracy_sum += inference_accuracy * weight
            total_weight += weight
            
            print(f"    {client_id}: inference accuracy = {inference_accuracy:.3f}")
        
        results["aggregated_accuracy"] = weighted_accuracy_sum / total_weight
        results["total_nodes"] = total_weight
        
        return results
    
    def run_federated_round(self, round_number: int = 1) -> FederatedRound:
        """
        Execute a complete federated learning round.
        
        Workflow:
        1. Fetch graph structure from RushDB
        2. Simulate local training on each client
        3. Aggregate weights (FedAvg)
        4. Run federated inference
        """
        print(f"\n{'='*60}")
        print(f"Federated Learning Round {round_number}")
        print(f"{'='*60}\n")
        
        # Step 1: Graph structure
        self.fetch_graph_structure()
        
        # Step 2: Cross-client edges
        cross_client_edges = self.discover_cross_client_edges()
        
        # Step 3: Local training
        self.simulate_local_training()
        
        # Step 4: Aggregation
        self.aggregate_weights_fedavg()
        
        # Step 5: Inference
        inference_results = self.run_federated_inference()
        
        return FederatedRound(
            round_number=round_number,
            clients=list(self.clients.values()),
            aggregated_accuracy=inference_results["aggregated_accuracy"],
            cross_client_edges=cross_client_edges
        )
    
    def print_summary(self, round_result: FederatedRound) -> None:
        """Print a formatted summary of the federated learning round."""
        print("\n" + "=" * 60)
        print("Results")
        print("=" * 60)
        
        for state in round_result.clients:
            accuracy_pct = state.local_accuracy * 100
            print(f"  ├─ {state.client_id}: {state.node_count} nodes, "
                  f"local accuracy: {accuracy_pct:.1f}%")
        
        agg_pct = round_result.aggregated_accuracy * 100
        print(f"  └─ Aggregated Model Accuracy: {agg_pct:.1f}%\n")
        
        print("Federated Round Summary:")
        print(f"  - Total clients: {len(round_result.clients)}")
        nodes_per_client = [c.node_count for c in round_result.clients]
        print(f"  - Nodes per client: {nodes_per_client}")
        print(f"  - Cross-client edges discovered: {round_result.cross_client_edges}")
        print(f"  - Aggregation method: {round_result.aggregation_method}")
        print()


def main():
    """Run the federated learning simulation."""
    print("\n" + "=" * 60)
    print("Federated Learning Across Graph-Structured Data")
    print("Using RushDB as the Graph Data Layer")
    print("=" * 60 + "\n")
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found in environment. "
            "Run `python seed.py` first to populate the graph data, "
            "then copy .env.example to .env and add your API key."
        )
    
    db = RushDB(api_key)
    print(f"[+] Connected to RushDB\n")
    
    # Create simulator
    simulator = FederatedLearningSimulator(db)
    
    # Run one federated learning round
    # (In production, multiple rounds would be executed for convergence)
    round_result = simulator.run_federated_round(round_number=1)
    
    # Print summary
    simulator.print_summary(round_result)
    
    print("\n[✓] Federated learning simulation completed!")
    print("    In production, this would:")
    print("    1. Use PyTorch/TensorFlow for actual gradient computation")
    print("    2. Run multiple rounds until convergence")
    print("    3. Apply differential privacy or secure aggregation")
    print("    4. Use Graph Neural Networks for graph-aware training\n")


if __name__ == "__main__":
    main()
