# Query Routing Patterns: Graph-Based LLM Request Distribution

**Use Case**: AI engineers building multi-LLM pipelines who are currently hand-rolling routing logic.

This project demonstrates how RushDB's property graph stores users, queries, and model performance metrics as a heterogeneous graph, enabling graph traversal queries that select the optimal LLM for each request based on real historical performance — without hand-rolled routing logic.

## The Problem with Hand-Rolled Routing

Building a multi-LLM pipeline typically means:
- Multiple custom tables to track query history
- A separate service to manage model performance
- Hand-coded if/else logic to select models
- No ability to learn from past routing decisions

## The RushDB Solution

RushDB models the routing domain as a property graph:

```
User ──QUERIED──▶ Query ──ROUTED_TO──▶ Model
                                       │
                              (performance metadata)
```

Key advantages:
1. **Graph-native routing**: User → Query → Model traversal finds historical context
2. **Embedded performance**: Model success rates stored as node properties
3. **Vector similarity**: Query embeddings enable finding similar past queries
4. **Dynamic updates**: Performance metrics update after each request

## Prerequisites

- Python 3.10+
- RushDB account and API key ([get one here](https://app.rushdb.com))

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

## Running the Example

### 1. Seed the Database (creates mock data)

```bash
python seed.py
```

This creates:
- 3 LLM models (GPT-4, Claude-Haiku, GPT-3.5-Turbo) with performance metrics
- 5 users with query history
- 50 historical queries with routing outcomes

### 2. Run the Router Demo

```bash
python main.py
```

The router will:
1. Analyze a user's recent query complexity
2. Find similar historical queries via vector search
3. Query model success rates for those query types
4. Select the optimal model (e.g., Claude-Haiku for simple queries, GPT-4 for complex ones)
5. Print the routing decision with full reasoning

## Expected Output

```
=== RushDB Graph-Based LLM Router ===

📊 Analyzing query: "Explain quantum entanglement"
👤 User: alice
🔍 Complexity score: 0.85 (high)
📈 Similar historical queries: 3 found

📋 Model Comparison:
  • GPT-4:       success_rate=0.92, avg_latency=4500ms, cost=$0.03
  • Claude-Haiku: success_rate=0.65, avg_latency=800ms, cost=$0.0001
  • GPT-3.5-Turbo: success_rate=0.78, avg_latency=1200ms, cost=$0.002

🎯 ROUTING DECISION: GPT-4
   Reasoning: High complexity query (0.85) + GPT-4 has 92% success on similar queries
   Estimated cost: $0.03 | Latency: ~4500ms
```

## How It Works


### Graph Model

The routing graph has three node types:

| Label | Properties | Role |
|-------|-----------|------|
| `User` | `id`, `name`, `preference` | Routes requests through this user context |
| `Query` | `text`, `embedding`, `complexity`, `success` | Tracks all queries and their outcomes |
| `Model` | `name`, `success_rate`, `avg_latency`, `cost_per_1k`, `embedding` | LLM performance metrics |

Relationships:
- `User` ─`QUERIED`─▶ `Query`
- `Query` ─`ROUTED_TO`─▶ `Model`

### Routing Algorithm

1. **Complexity Analysis**: Embed the incoming query and compare to user's recent queries
2. **Historical Lookup**: Traverse the graph to find similar successful queries
3. **Model Comparison**: Query each model's success rate for similar query types
4. **Decision**: Select model based on complexity-adjusted success rate

### Why Not Pure Vector or Timeline Systems?

| Requirement | Pure Vector DB | Timeline DB | RushDB Graph |
|------------|----------------|-------------|--------------|
| Query → Model relationship | ❌ Requires JOIN | ❌ Manual link | ✅ Native |
| Model performance per query type | ❌ Aggregations | ❌ Separate table | ✅ Node properties |
| User-specific routing context | ❌ Separate index | ✅ Possible | ✅ Traversal |
| Update model metrics | ❌ No transactions | ✅ Possible | ✅ ACID transactions |

## Project Structure

```
query-routing-patterns-graph-based-llm-request-dis-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── seed.py             # Mock data generator
└── main.py             # Router demonstration
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)
- [Property Graph Model Deep Dive](https://docs.rushdb.com/concepts/property-graph)
