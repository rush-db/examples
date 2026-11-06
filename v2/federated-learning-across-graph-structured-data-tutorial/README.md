# Federated Learning Across Graph-Structured Data

A tutorial demonstrating how to use RushDB as the data layer for federated learning on graph-structured data.

## What This Tutorial Demonstrates

- **Graph-structured federated learning**: Training ML models across distributed graph nodes
- **RushDB graph traversal**: Using RushDB's property graph API to navigate relationships between federated clients
- **Privacy-preserving aggregation**: Simulating FedAvg-style model aggregation across graph partitions
- **Node classification**: Running predictions on graph data spanning multiple federated nodes

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      RushDB Graph Store                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ CLIENT_A │──│ CLIENT_B │──│ CLIENT_C │──│ CLIENT_D │        │
│  │ (Region) │  │ (Region) │  │ (Region) │  │ (Region) │        │
│  │ 10 nodes │  │ 12 nodes │  │  8 nodes │  │ 15 nodes │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│        │            │            │            │                  │
│        └────────────┴────────────┴────────────┘                  │
│                      (cross-client edges)                       │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- RushDB account (free tier works)
- `rushdb>=2.0.0` Python package

## Setup

1. **Clone and install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

3. **Get your API key**:
   - Sign up at https://rushdb.com
   - Create a new project
   - Copy the API key to `.env`

## Running the Tutorial

### Step 1: Seed the Graph Data

This creates a synthetic graph with:
- 4 federated clients (representing different regions/parties)
- Node embeddings stored as vectors
- Cross-client relationships for graph connectivity

```bash
python seed.py
```

Expected output:
```
[1/4] Seeding CLIENT_A: 10 nodes... done
[2/4] Seeding CLIENT_B: 12 nodes... done
[3/4] Seeding CLIENT_C: 8 nodes... done
[4/4] Seeding CLIENT_D: 15 nodes... done
[+] Graph seeded successfully: 45 nodes across 4 clients
```

### Step 2: Run the Federated Learning Simulation

```bash
python main.py
```

Expected output:
```
[Step 1] Fetching graph structure from RushDB...
[Step 2] Simulating local training on 4 federated clients...
[Step 3] Aggregating model weights (FedAvg)...
[Step 4] Running federated inference...

Results:
  ├─ CLIENT_A: 10 nodes, local accuracy: 0.873
  ├─ CLIENT_B: 12 nodes, local accuracy: 0.891
  ├─ CLIENT_C: 8 nodes, local accuracy: 0.845
  ├─ CLIENT_D: 15 nodes, local accuracy: 0.882
  └─ Aggregated Model Accuracy: 0.873

Federated Round Summary:
  - Total clients: 4
  - Nodes per client: [10, 12, 8, 15]
  - Cross-client edges discovered: 7
  - Aggregation method: FedAvg (weighted by node count)
```

## Project Structure

```
federated-learning-across-graph-structured-data-tutorial/
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── seed.py                # Graph data generation script
└── main.py                # Main federated learning simulation
```

## How It Works

### 1. Graph Seeding

`seed.py` creates a property graph in RushDB representing distributed graph data:

- **CLIENT nodes**: Represent federated parties (each owns local data)
- **GRAPH_NODE nodes**: Individual data points with features and labels
- **PART_OF relationships**: Connect graph nodes to their owner client
- **CONNECTED_TO relationships**: Cross-client edges for graph structure

### 2. Federated Learning Pipeline

`main.py` implements a simplified federated learning cycle:

1. **Graph Fetch**: Query RushDB to retrieve client topology and node data
2. **Local Training**: Simulate gradient updates on each client (in reality, this would use PyTorch/TensorFlow on local data)
3. **Weight Aggregation**: FedAvg-style weighted averaging of model parameters
4. **Inference**: Run predictions using the aggregated global model

### 3. Why RushDB?

- **Zero-schema flexibility**: Store heterogeneous graph data without upfront schema design
- **Relationship traversal**: Native graph queries for discovering cross-client edges
- **Vector support**: Store node embeddings directly in RushDB for similarity search
- **Free reads**: Query graph structure without per-call costs during training

## Key RushDB Operations Used

```sdk
# Find all nodes belonging to a client
db.records.find({
    "labels": ["GRAPH_NODE"],
    "where": {
        "CLIENT": {
            "$relation": {"type": "PART_OF", "direction": "in"},
            "clientId": "CLIENT_A"
        }
    }
})

# Traverse cross-client relationships
db.records.find({
    "labels": ["GRAPH_NODE"],
    "where": {
        "CONNECTED_TO": {"$exists": true}
    }
})
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Find all nodes belonging to a client
const nodes = await db.records.find({
    labels: ['GRAPH_NODE'],
    where: {
        CLIENT: {
            $relation: { type: 'PART_OF', direction: 'in' },
            clientId: 'CLIENT_A'
        }
    }
})

// Traverse cross-client relationships
const crossClientNodes = await db.records.find({
    labels: ['GRAPH_NODE'],
    where: {
        CONNECTED_TO: { $exists: true }
    }
})
```

## Extending This Tutorial

To adapt this for production federated learning:

1. **Replace simulated training** with actual PyTorch/TensorFlow local training loops
2. **Add differential privacy** by computing noise additions on aggregated gradients
3. **Implement secure aggregation** using cryptographic protocols
4. **Scale to more clients** by seeding additional CLIENT partitions
5. **Use semantic search** for node similarity: `db.ai.search()` on graph node features

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [Federated Learning: Strategy for Privacy-Preserving Machine Learning](https://arxiv.org/abs/1602.05629)
- [Graph Neural Networks for Federated Learning](https://arxiv.org/abs/2106.12643)
